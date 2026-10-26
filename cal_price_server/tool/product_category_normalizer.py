"""Shared product-category normalization for ingestion and enrichment."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


PRODUCT_CATEGORIES = (
    "冻品",
    "熟食",
    "水果",
    "酒类",
    "食品",
    "生鲜肉类",
    "水产海鲜",
    "普货",
)

PRODUCT_CATEGORY_SET = set(PRODUCT_CATEGORIES)
DEFAULT_MAPPING_PATH = Path(__file__).resolve().parent / "data" / "product_category_mapping_v1.csv"

# Earlier rules win. Specific terms precede broad terms.
PRODUCT_KEYWORD_RULES = (
    ("酒类", ("茅台", "白酒", "红酒", "葡萄酒", "啤酒", "洋酒", "酒水")),
    ("水产海鲜", ("水鱼", "大闸蟹", "螃蟹", "生蚝", "海鲜", "鱼苗", "鱼泡", "鱿鱼", "虾", "鲍鱼")),
    ("生鲜肉类", ("牛肉", "羊肉", "猪肉", "鸡肉", "生鸡", "肉丸", "鹅肠", "鹅肝", "牛杂")),
    ("熟食", ("熟冻", "熟食", "预制菜", "点心", "油条", "丸子", "饼皮", "熟的")),
    ("食品", ("月饼", "果浆", "菠萝浆", "面粉", "大米", "干货", "食品", "果汁", "酱料", "茶叶", "酸奶", "鸡蛋", "粽子")),
    ("水果", ("水果", "榴莲", "菠萝", "芒果", "柠檬", "百香果", "橙", "苹果", "梨", "西瓜")),
    ("冻品", ("冻品", "生冻", "冷冻", "冰冻", "冻货", "雪糕")),
    ("普货", ("屏幕", "家具", "沙发", "桌子", "柜子", "床垫", "电器", "冰箱", "空调", "纸巾", "包装盒", "杯子", "瓷砖", "油漆")),
)

NON_PRODUCT_DESCRIPTIONS = (
    "正报",
    "包车",
    "在仓全部出",
    "在仓的货全部出",
    "在仓的全部出",
    "到了才知道几件",
)
NON_PRODUCT_MARKERS = ("正报", "包车", "在仓")


@dataclass(frozen=True)
class CategoryResolution:
    category: str
    source: str
    confidence: float


def normalize_description(value: object) -> str | None:
    if value is None:
        return None
    normalized = re.sub(r"\s+", " ", str(value)).strip(" ,，。;；")
    return normalized or None


@lru_cache(maxsize=8)
def load_approved_mapping(mapping_path: str | Path = DEFAULT_MAPPING_PATH) -> dict[str, CategoryResolution]:
    path = Path(mapping_path)
    if not path.exists():
        raise RuntimeError(f"产品分类映射文件不存在: {path}")

    mapping: dict[str, CategoryResolution] = {}
    with path.open(encoding="utf-8-sig", newline="") as mapping_file:
        for row in csv.DictReader(mapping_file):
            raw_name = normalize_description(row.get("raw_product_name"))
            category = (row.get("normalized_category") or "").strip()
            confidence = float(row.get("confidence") or 0)
            if not raw_name or category not in PRODUCT_CATEGORY_SET or confidence < 0.90:
                raise RuntimeError(f"产品分类映射存在无效记录: {row}")
            resolution = CategoryResolution(category, "mapping", confidence)
            previous = mapping.get(raw_name)
            if previous and previous.category != category:
                raise RuntimeError(f"同一原始品名存在冲突分类: {raw_name}")
            mapping[raw_name] = resolution
    return mapping


def classify_with_rules(description: str | None) -> tuple[str, float] | None:
    normalized = normalize_description(description)
    if not normalized:
        return None
    lowered = normalized.lower()
    for category, keywords in PRODUCT_KEYWORD_RULES:
        if any(keyword.lower() in lowered for keyword in keywords):
            return category, 1.0
    return None


def resolve_product_category(
    description: object,
    mapping_path: str | Path = DEFAULT_MAPPING_PATH,
) -> CategoryResolution | None:
    normalized = normalize_description(description)
    if not normalized:
        return None
    if normalized in PRODUCT_CATEGORY_SET:
        return CategoryResolution(normalized, "canonical", 1.0)

    mapped = load_approved_mapping(mapping_path).get(normalized)
    if mapped:
        return mapped

    rule = classify_with_rules(normalized)
    if rule:
        category, confidence = rule
        return CategoryResolution(category, "rule", confidence)
    return None


def normalize_product_category(description: object) -> str | None:
    resolution = resolve_product_category(description)
    return resolution.category if resolution else None


def is_non_product_description(description: str | None) -> bool:
    normalized = normalize_description(description)
    if not normalized or normalized in NON_PRODUCT_DESCRIPTIONS:
        return True
    if resolve_product_category(normalized):
        return False
    if any(marker in normalized for marker in NON_PRODUCT_MARKERS):
        return True
    return re.fullmatch(r"[\d\s+=.,，、/箱件板拖公斤kgKG]+", normalized) is not None
