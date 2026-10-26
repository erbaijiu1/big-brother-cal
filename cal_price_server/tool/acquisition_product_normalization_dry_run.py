"""Dry-run normalization for historical product names used by acquisition analytics.

The script reads aggregate product-name statistics, sends only distinct product
names to the configured classifier, and writes a review CSV. It never updates
the database.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from sqlalchemy import bindparam, text

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from db.sqlalchemy_define import get_session_factory
from services.acquisition_analytics_service import CANONICAL_CATEGORIES
from tool.product_name_enrichment import LlmProductClassifier, classify_with_rules


@dataclass
class ProductImpact:
    raw_product_name: str
    order_count: int
    revenue: float
    gross_profit: float
    missing_cost_order_count: int


@dataclass
class NormalizationResult:
    raw_product_name: str
    normalized_category: str
    source: str
    confidence: float


def load_product_impacts(session) -> list[ProductImpact]:
    rows = session.execute(
        text(
            """
            SELECT
                TRIM(product_name) AS raw_product_name,
                COUNT(*) AS order_count,
                ROUND(SUM(shipping_fee), 2) AS revenue,
                ROUND(COALESCE(SUM(CASE
                    WHEN shipping_fee > 0 AND shipping_cost = 0 THEN NULL
                    ELSE shipping_fee - shipping_cost END), 0), 2) AS gross_profit,
                SUM(shipping_fee > 0 AND shipping_cost = 0) AS missing_cost_order_count
            FROM t_performance_statement
            WHERE NULLIF(TRIM(product_name), '') IS NOT NULL
              AND TRIM(product_name) NOT IN :canonical_categories
            GROUP BY TRIM(product_name)
            ORDER BY order_count DESC, ABS(gross_profit) DESC, raw_product_name
            """
        ).bindparams(bindparam("canonical_categories", expanding=True)),
        {"canonical_categories": tuple(CANONICAL_CATEGORIES)},
    ).mappings()
    return [
        ProductImpact(
            raw_product_name=row["raw_product_name"],
            order_count=int(row["order_count"]),
            revenue=float(row["revenue"] or 0),
            gross_profit=float(row["gross_profit"] or 0),
            missing_cost_order_count=int(row["missing_cost_order_count"] or 0),
        )
        for row in rows
    ]


def review_priority(rank: int, result: NormalizationResult) -> tuple[str, str]:
    if result.normalized_category == "UNKNOWN":
        return "P0", "无法明确识别，必须人工判断"
    if result.confidence < 0.9:
        return "P0", "模型置信度低于0.90"
    if rank <= 200:
        return "P0", "高订单量/高毛利影响品名，优先复核"
    if rank <= 1000:
        return "P1", "中等影响品名，第二批复核"
    return "P2", "低影响品名，可抽样复核"


def load_previous_results(path: Path | None) -> dict[str, NormalizationResult]:
    if not path or not path.exists():
        return {}
    with path.open(encoding="utf-8-sig", newline="") as input_file:
        return {
            row["raw_product_name"]: NormalizationResult(
                raw_product_name=row["raw_product_name"],
                normalized_category=row["normalized_category"],
                source=row["source"],
                confidence=float(row["confidence"]),
            )
            for row in csv.DictReader(input_file)
        }


def write_preview(
    impacts: list[ProductImpact],
    results: dict[str, NormalizationResult],
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as output_file:
        fields = [
            "priority_rank", "review_priority", "review_reason", "raw_product_name",
            "normalized_category", "source", "confidence", "order_count", "revenue",
            "gross_profit", "missing_cost_order_count",
        ]
        writer = csv.DictWriter(output_file, fieldnames=fields)
        writer.writeheader()
        for rank, impact in enumerate(impacts, 1):
            result = results.get(impact.raw_product_name)
            if result is None:
                continue
            priority, reason = review_priority(rank, result)
            writer.writerow({
                "priority_rank": rank,
                "review_priority": priority,
                "review_reason": reason,
                "raw_product_name": impact.raw_product_name,
                "normalized_category": result.normalized_category,
                "source": result.source,
                "confidence": f"{result.confidence:.4f}",
                "order_count": impact.order_count,
                "revenue": f"{impact.revenue:.2f}",
                "gross_profit": f"{impact.gross_profit:.2f}",
                "missing_cost_order_count": impact.missing_cost_order_count,
            })


def resolve_names(
    impacts: Iterable[ProductImpact],
    classifier: LlmProductClassifier,
    batch_size: int,
    existing: dict[str, NormalizationResult],
    checkpoint,
) -> dict[str, NormalizationResult]:
    impacts = list(impacts)
    results = dict(existing)
    unresolved: list[str] = []
    for impact in impacts:
        name = impact.raw_product_name
        if name in results:
            continue
        rule = classify_with_rules(name)
        if rule:
            category, confidence = rule
            results[name] = NormalizationResult(name, category, "rule", confidence)
        else:
            unresolved.append(name)

    batch_count = (len(unresolved) + batch_size - 1) // batch_size
    for start in range(0, len(unresolved), batch_size):
        batch = unresolved[start : start + batch_size]
        print(f"品名分类进度: {start // batch_size + 1}/{batch_count}（{len(batch)}个）", flush=True)
        try:
            classified = classifier.classify(batch)
        except Exception as exc:
            print(f"批次失败，保留 UNKNOWN: {exc}", flush=True)
            classified = {}
        for name in batch:
            if name in classified:
                category, confidence = classified[name]
                results[name] = NormalizationResult(name, category, "llm", confidence)
            else:
                results[name] = NormalizationResult(name, "UNKNOWN", "unknown", 0.0)
        checkpoint(results)
    return results


def summary(impacts: list[ProductImpact], results: dict[str, NormalizationResult]) -> dict:
    impacts_by_name = {impact.raw_product_name: impact for impact in impacts}
    category_names = Counter(result.normalized_category for result in results.values())
    category_orders = Counter()
    category_profit = Counter()
    for name, result in results.items():
        impact = impacts_by_name[name]
        category_orders[result.normalized_category] += impact.order_count
        category_profit[result.normalized_category] += impact.gross_profit
    return {
        "distinct_product_names": len(impacts),
        "resolved_names": sum(result.normalized_category != "UNKNOWN" for result in results.values()),
        "unknown_names": sum(result.normalized_category == "UNKNOWN" for result in results.values()),
        "source_counts": Counter(result.source for result in results.values()),
        "category_name_counts": category_names,
        "category_order_counts": category_orders,
        "category_gross_profit": {key: round(value, 2) for key, value in category_profit.items()},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="历史原始品名归一 dry-run（不会更新数据库）")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reuse-preview", type=Path)
    parser.add_argument("--llm-batch-size", type=int, default=10)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    session = get_session_factory()()
    try:
        impacts = load_product_impacts(session)
    finally:
        session.rollback()
        session.close()
    if args.limit > 0:
        impacts = impacts[: args.limit]

    existing = load_previous_results(args.reuse_preview)
    classifier = LlmProductClassifier.from_environment()

    def checkpoint(current_results):
        write_preview(impacts, current_results, args.output)

    results = resolve_names(impacts, classifier, max(1, args.llm_batch_size), existing, checkpoint)
    write_preview(impacts, results, args.output)
    print(json.dumps(summary(impacts, results), ensure_ascii=False, indent=2))
    print(f"preview_file={args.output}")
    print("apply=false")


if __name__ == "__main__":
    main()
