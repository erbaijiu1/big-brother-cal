"""Generate reversible SQL from the acquisition product normalization preview.

This generator never connects to MySQL and never executes the generated SQL.
Only non-UNKNOWN mappings at or above the chosen confidence are included.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


ALLOWED_CATEGORIES = {"冻品", "熟食", "水果", "酒类", "食品", "生鲜肉类", "水产海鲜", "普货"}


@dataclass(frozen=True)
class MappingRow:
    raw_product_name: str
    normalized_category: str
    source: str
    confidence: float
    order_count: int


def load_mappings(preview_path: Path, min_confidence: float) -> list[MappingRow]:
    selected: dict[str, MappingRow] = {}
    with preview_path.open(encoding="utf-8-sig", newline="") as preview_file:
        for raw in csv.DictReader(preview_file):
            category = raw["normalized_category"].strip()
            confidence = float(raw["confidence"])
            if category == "UNKNOWN" or confidence < min_confidence:
                continue
            if category not in ALLOWED_CATEGORIES:
                raise ValueError(f"不允许的分类: {category}")
            row = MappingRow(
                raw_product_name=raw["raw_product_name"].strip(),
                normalized_category=category,
                source=raw["source"].strip(),
                confidence=confidence,
                order_count=int(raw["order_count"]),
            )
            if not row.raw_product_name:
                raise ValueError("原始品名不能为空")
            previous = selected.get(row.raw_product_name)
            if previous and previous != row:
                raise ValueError(f"原始品名存在冲突映射: {row.raw_product_name}")
            selected[row.raw_product_name] = row
    return sorted(selected.values(), key=lambda item: item.raw_product_name)


def sql_text(value: str) -> str:
    return f"CONVERT(0x{value.encode('utf-8').hex()} USING utf8mb4)"


def mapping_values(rows: list[MappingRow]) -> str:
    return ",\n".join(
        "    (" + ", ".join([
            sql_text(row.raw_product_name),
            sql_text(row.normalized_category),
            sql_text(row.source),
            f"{row.confidence:.4f}",
            str(row.order_count),
        ]) + ")"
        for row in rows
    )


def export_runtime_mapping(rows: list[MappingRow], output_path: Path) -> None:
    """Write the reviewed aliases consumed by future ingestion runs."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=["raw_product_name", "normalized_category", "source", "confidence"],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "raw_product_name": row.raw_product_name,
                "normalized_category": row.normalized_category,
                "source": row.source,
                "confidence": f"{row.confidence:.4f}",
            })


def generate_apply_sql(rows: list[MappingRow], migration_key: str, digest: str) -> str:
    expected_names = len(rows)
    expected_orders = sum(row.order_count for row in rows)
    plan_table = f"z_plan_acq_product_{migration_key}"
    backup_table = f"z_bak_acq_product_{migration_key}"
    return f"""-- Facebook 获客分析 V1：高置信品名归一回填
-- 目标库：db_prize_cal
-- 映射品名：{expected_names}
-- 预计更新绩效记录：{expected_orders}
-- 映射 SHA256：{digest}
-- UNKNOWN 和置信度不足 0.90 的记录不在本次范围。

SET NAMES utf8mb4;
USE `db_prize_cal`;

CREATE TABLE IF NOT EXISTS `{plan_table}` (
    `raw_product_name` VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
    `normalized_category` VARCHAR(32) NOT NULL,
    `source` VARCHAR(16) NOT NULL,
    `confidence` DECIMAL(6,4) NOT NULL,
    `expected_order_count` INT UNSIGNED NOT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`raw_product_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `{backup_table}` LIKE `t_performance_statement`;

DELIMITER $$
DROP PROCEDURE IF EXISTS `assert_acq_category_empty_{migration_key}`$$
CREATE PROCEDURE `assert_acq_category_empty_{migration_key}`()
BEGIN
    IF (SELECT COUNT(*) FROM `{plan_table}`) <> 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '迁移终止：计划表非空，可能已执行过';
    END IF;
    IF (SELECT COUNT(*) FROM `{backup_table}`) <> 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '迁移终止：备份表非空，可能已执行过';
    END IF;
END$$
DELIMITER ;

CALL `assert_acq_category_empty_{migration_key}`();
DROP PROCEDURE `assert_acq_category_empty_{migration_key}`;

INSERT INTO `{plan_table}`
    (`raw_product_name`, `normalized_category`, `source`, `confidence`, `expected_order_count`)
VALUES
{mapping_values(rows)};

DELIMITER $$
DROP PROCEDURE IF EXISTS `validate_acq_category_plan_{migration_key}`$$
CREATE PROCEDURE `validate_acq_category_plan_{migration_key}`()
BEGIN
    IF (SELECT COUNT(*) FROM `{plan_table}`) <> {expected_names} THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '迁移终止：映射品名数不符合预期';
    END IF;
    IF (SELECT COALESCE(SUM(`expected_order_count`), 0) FROM `{plan_table}`) <> {expected_orders} THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '迁移终止：计划订单数不符合预期';
    END IF;
    IF (SELECT COUNT(*)
        FROM `t_performance_statement` performance
        JOIN `{plan_table}` plan
          ON BINARY TRIM(performance.`product_name`) = BINARY plan.`raw_product_name`) <> {expected_orders} THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '迁移终止：数据库当前匹配行数与 dry-run 不一致';
    END IF;
    IF EXISTS (
        SELECT 1
        FROM `{plan_table}` plan
        LEFT JOIN `t_performance_statement` performance
          ON BINARY TRIM(performance.`product_name`) = BINARY plan.`raw_product_name`
        GROUP BY plan.`raw_product_name`, plan.`expected_order_count`
        HAVING COUNT(performance.`id`) <> plan.`expected_order_count`
    ) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '迁移终止：至少一个品名的匹配票数已变化';
    END IF;
END$$
DELIMITER ;

CALL `validate_acq_category_plan_{migration_key}`();
DROP PROCEDURE `validate_acq_category_plan_{migration_key}`;

INSERT INTO `{backup_table}`
SELECT performance.*
FROM `t_performance_statement` performance
JOIN `{plan_table}` plan
  ON BINARY TRIM(performance.`product_name`) = BINARY plan.`raw_product_name`;
COMMIT;

DELIMITER $$
DROP PROCEDURE IF EXISTS `apply_acq_category_{migration_key}`$$
CREATE PROCEDURE `apply_acq_category_{migration_key}`()
BEGIN
    DECLARE changed_rows INT DEFAULT 0;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    IF (SELECT COUNT(*) FROM `{backup_table}`) <> {expected_orders} THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '迁移终止：行级备份数量不符合预期';
    END IF;

    START TRANSACTION;
    UPDATE `t_performance_statement` performance
    JOIN `{plan_table}` plan
      ON BINARY TRIM(performance.`product_name`) = BINARY plan.`raw_product_name`
    SET performance.`product_name` = plan.`normalized_category`,
        performance.`updated_at` = CURRENT_TIMESTAMP;

    SET changed_rows = ROW_COUNT();
    IF changed_rows <> {expected_orders} THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '迁移终止：实际更新行数不符合预期';
    END IF;
    COMMIT;
END$$
DELIMITER ;

CALL `apply_acq_category_{migration_key}`();
DROP PROCEDURE `apply_acq_category_{migration_key}`;

SELECT plan.`normalized_category`, plan.`source`, COUNT(*) AS `mapped_names`,
       SUM(plan.`expected_order_count`) AS `updated_orders`
FROM `{plan_table}` plan
GROUP BY plan.`normalized_category`, plan.`source`
ORDER BY plan.`normalized_category`, plan.`source`;

-- 计划表和行级备份表保留到人工验收完成，删除需另行审批。
"""


def generate_check_sql(rows: list[MappingRow], migration_key: str) -> str:
    expected_names = len(rows)
    expected_orders = sum(row.order_count for row in rows)
    plan_table = f"z_plan_acq_product_{migration_key}"
    backup_table = f"z_bak_acq_product_{migration_key}"
    return f"""-- Facebook 获客分析 V1：回填后只读验收
SET NAMES utf8mb4;
USE `db_prize_cal`;

SELECT 'plan_names' AS `check_name`, COUNT(*) AS `actual_value`, {expected_names} AS `expected_value`
FROM `{plan_table}`
UNION ALL
SELECT 'backup_orders', COUNT(*), {expected_orders} FROM `{backup_table}`
UNION ALL
SELECT 'normalized_orders', COUNT(*), {expected_orders}
FROM `{backup_table}` backup_row
JOIN `{plan_table}` plan
  ON BINARY TRIM(backup_row.`product_name`) = BINARY plan.`raw_product_name`
JOIN `t_performance_statement` performance ON performance.`id` = backup_row.`id`
WHERE BINARY performance.`product_name` = BINARY plan.`normalized_category`;

SELECT
    COUNT(DISTINCT TRIM(performance.`product_name`)) AS `remaining_noncanonical_names`,
    COUNT(*) AS `remaining_noncanonical_orders`,
    ROUND(COALESCE(SUM(CASE WHEN performance.`shipping_fee` > 0 AND performance.`shipping_cost` = 0
        THEN NULL ELSE performance.`shipping_fee` - performance.`shipping_cost` END), 0), 2)
        AS `remaining_noncanonical_gross_profit`
FROM `t_performance_statement` performance
WHERE NULLIF(TRIM(performance.`product_name`), '') IS NOT NULL
  AND TRIM(performance.`product_name`) NOT IN ('冻品','熟食','水果','酒类','食品','生鲜肉类','水产海鲜','普货');

SELECT plan.`normalized_category`, COUNT(*) AS `updated_orders`,
       ROUND(SUM(performance.`shipping_fee`), 2) AS `revenue`,
       ROUND(COALESCE(SUM(CASE WHEN performance.`shipping_fee` > 0 AND performance.`shipping_cost` = 0
           THEN NULL ELSE performance.`shipping_fee` - performance.`shipping_cost` END), 0), 2) AS `gross_profit`
FROM `{backup_table}` backup_row
JOIN `{plan_table}` plan
  ON BINARY TRIM(backup_row.`product_name`) = BINARY plan.`raw_product_name`
JOIN `t_performance_statement` performance ON performance.`id` = backup_row.`id`
GROUP BY plan.`normalized_category`
ORDER BY `gross_profit` DESC;

SELECT
    ROUND(SUM(backup_row.`shipping_fee`), 2) AS `backup_revenue`,
    ROUND(SUM(performance.`shipping_fee`), 2) AS `current_revenue`,
    ROUND(SUM(backup_row.`shipping_cost`), 2) AS `backup_cost`,
    ROUND(SUM(performance.`shipping_cost`), 2) AS `current_cost`
FROM `{backup_table}` backup_row
JOIN `t_performance_statement` performance ON performance.`id` = backup_row.`id`;
"""


def generate_rollback_sql(rows: list[MappingRow], migration_key: str) -> str:
    expected_orders = sum(row.order_count for row in rows)
    plan_table = f"z_plan_acq_product_{migration_key}"
    backup_table = f"z_bak_acq_product_{migration_key}"
    return f"""-- Facebook 获客分析 V1：品名归一回滚
-- 只恢复 product_name 和原 updated_at，不覆盖其他业务字段。
SET NAMES utf8mb4;
USE `db_prize_cal`;

DELIMITER $$
DROP PROCEDURE IF EXISTS `rollback_acq_category_{migration_key}`$$
CREATE PROCEDURE `rollback_acq_category_{migration_key}`()
BEGIN
    DECLARE changed_rows INT DEFAULT 0;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    IF (SELECT COUNT(*) FROM `{backup_table}`) <> {expected_orders} THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '回滚终止：行级备份数量不符合预期';
    END IF;

    START TRANSACTION;
    UPDATE `t_performance_statement` performance
    JOIN `{backup_table}` backup_row ON backup_row.`id` = performance.`id`
    SET performance.`product_name` = backup_row.`product_name`,
        performance.`updated_at` = backup_row.`updated_at`;
    SET changed_rows = ROW_COUNT();
    IF changed_rows <> {expected_orders} THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '回滚终止：恢复行数不符合预期';
    END IF;
    COMMIT;
END$$
DELIMITER ;

CALL `rollback_acq_category_{migration_key}`();
DROP PROCEDURE `rollback_acq_category_{migration_key}`;

SELECT COUNT(*) AS `restored_orders`, {expected_orders} AS `expected_orders`
FROM `t_performance_statement` performance
JOIN `{backup_table}` backup_row ON backup_row.`id` = performance.`id`
WHERE BINARY performance.`product_name` = BINARY backup_row.`product_name`
  AND performance.`updated_at` <=> backup_row.`updated_at`;

-- 回滚后仍保留计划表和备份表，删除需另行审批。
"""


def generate_runbook(rows: list[MappingRow], migration_key: str, min_confidence: float, digest: str) -> str:
    names_by_category = Counter(row.normalized_category for row in rows)
    orders_by_category = Counter()
    for row in rows:
        orders_by_category[row.normalized_category] += row.order_count
    category_lines = "\n".join(
        f"- {category}：{names_by_category[category]} 个品名，{orders_by_category[category]} 票"
        for category in sorted(names_by_category)
    )
    return f"""# 获客品类高置信回填操作单（{migration_key}）

## 执行范围

- 目标库：本地 `db_prize_cal`
- 目标表：`t_performance_statement`
- 修改字段：`product_name`、`updated_at`
- 映射品名：{len(rows)}
- 预计更新：{sum(row.order_count for row in rows)} 行
- 最低置信度：{min_confidence:.2f}
- 映射 SHA256：`{digest}`
- UNKNOWN 与低置信度品名不更新

{category_lines}

## SQL 分类

- `apply`：包含 DDL、INSERT、UPDATE 和存储过程调用，会修改数据库。
- `check`：只读 SELECT，可在回填后直接执行。
- `rollback`：包含 UPDATE 和存储过程调用，仅在需要回滚且再次确认后执行。

## 执行顺序

1. 确认完整逻辑备份 SHA-256。
2. 执行 apply SQL；前置断言必须确认 2,587 个品名、7,390 票均未变化。
3. 执行 check SQL；三个计数应分别为 2,587、7,390、7,390。
4. 对账总收入、总成本和总毛利润不变。
5. 页面检查候选品类与 UNKNOWN/待归一变化。
6. 结果异常时，单独确认后执行 rollback SQL。
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--migration-key", default="20261026_v1")
    parser.add_argument("--min-confidence", type=float, default=0.90)
    parser.add_argument("--mapping-output", type=Path)
    args = parser.parse_args()

    rows = load_mappings(args.preview, args.min_confidence)
    canonical = "\n".join(
        f"{row.raw_product_name}\t{row.normalized_category}\t{row.source}\t{row.confidence:.4f}\t{row.order_count}"
        for row in rows
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"acquisition_category_backfill_{args.migration_key}"
    (args.output_dir / f"{stem}.sql").write_text(generate_apply_sql(rows, args.migration_key, digest), encoding="utf-8")
    (args.output_dir / f"{stem}_check.sql").write_text(generate_check_sql(rows, args.migration_key), encoding="utf-8")
    (args.output_dir / f"{stem}_rollback.sql").write_text(generate_rollback_sql(rows, args.migration_key), encoding="utf-8")
    (args.output_dir / f"{stem}.md").write_text(generate_runbook(rows, args.migration_key, args.min_confidence, digest), encoding="utf-8")
    if args.mapping_output:
        export_runtime_mapping(rows, args.mapping_output)
    print(f"mapping_names={len(rows)}")
    print(f"expected_orders={sum(row.order_count for row in rows)}")
    print(f"mapping_sha256={digest}")
    if args.mapping_output:
        print(f"mapping_output={args.mapping_output}")
    print("executed=false")


if __name__ == "__main__":
    main()
