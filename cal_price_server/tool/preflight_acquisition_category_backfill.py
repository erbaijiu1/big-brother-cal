"""Read-only preflight for the acquisition category backfill."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from sqlalchemy import text

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from db.sqlalchemy_define import get_session_factory
from tool.generate_acquisition_category_backfill_sql import load_mappings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", type=Path, required=True)
    parser.add_argument("--migration-key", default="20261026_v1")
    parser.add_argument("--min-confidence", type=float, default=0.90)
    args = parser.parse_args()

    mappings = load_mappings(args.preview, args.min_confidence)
    mapping_by_name = {row.raw_product_name: row for row in mappings}
    session = get_session_factory()()
    try:
        rows = session.execute(text("""
            SELECT id, product_name, shipping_fee, shipping_cost
            FROM t_performance_statement
        """)).mappings().all()
        table_names = [
            f"z_plan_acq_product_{args.migration_key}",
            f"z_bak_acq_product_{args.migration_key}",
        ]
        existing_tables = {
            row["TABLE_NAME"]
            for row in session.execute(text("""
                SELECT TABLE_NAME
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME IN (:plan_table, :backup_table)
            """), {"plan_table": table_names[0], "backup_table": table_names[1]}).mappings()
        }
    finally:
        session.rollback()
        session.close()

    actual_counts = Counter()
    selected_rows = []
    for row in rows:
        raw_name = (row["product_name"] or "").strip()
        if raw_name in mapping_by_name:
            actual_counts[raw_name] += 1
            selected_rows.append(row)
    mismatches = [
        {"raw_product_name": name, "expected": mapping_by_name[name].order_count, "actual": actual_counts[name]}
        for name in mapping_by_name
        if actual_counts[name] != mapping_by_name[name].order_count
    ]
    missing_cost_rows = [
        row for row in selected_rows
        if float(row["shipping_fee"] or 0) > 0 and float(row["shipping_cost"] or 0) == 0
    ]
    report = {
        "mapping_names": len(mappings),
        "expected_orders": sum(row.order_count for row in mappings),
        "actual_orders": len(selected_rows),
        "mismatched_names": len(mismatches),
        "mismatch_examples": mismatches[:20],
        "existing_migration_tables": sorted(existing_tables),
        "selected_revenue": round(sum(float(row["shipping_fee"] or 0) for row in selected_rows), 2),
        "selected_cost": round(sum(float(row["shipping_cost"] or 0) for row in selected_rows), 2),
        "selected_reportable_gross_profit": round(sum(
            float(row["shipping_fee"] or 0) - float(row["shipping_cost"] or 0)
            for row in selected_rows if row not in missing_cost_rows
        ), 2),
        "selected_missing_cost_orders": len(missing_cost_rows),
        "ready": (
            len(selected_rows) == sum(row.order_count for row in mappings)
            and not mismatches
            and not existing_tables
        ),
        "read_only": True,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
