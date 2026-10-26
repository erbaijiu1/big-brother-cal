"""Generate reviewed, reversible SQL for product-name enrichment.

This tool only reads a dry-run CSV and writes SQL/document files. It never
connects to the database and never executes the generated statements.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


ALLOWED_CATEGORIES = {"冻品", "熟食", "水果", "酒类", "食品", "生鲜肉类", "水产海鲜", "普货"}
ALLOWED_SOURCES = {"canonical", "mapping", "rule", "llm"}


@dataclass(frozen=True)
class BackfillRow:
    performance_id: int
    product_name: str
    source: str
    confidence: float


def load_rows(preview_path: Path, min_llm_confidence: float) -> list[BackfillRow]:
    selected: dict[int, BackfillRow] = {}
    with preview_path.open(encoding="utf-8-sig", newline="") as preview_file:
        for raw in csv.DictReader(preview_file):
            row = BackfillRow(
                performance_id=int(raw["performance_id"]),
                product_name=raw["product_name"].strip(),
                source=raw["source"].strip(),
                confidence=float(raw["confidence"]),
            )
            if row.product_name not in ALLOWED_CATEGORIES:
                raise ValueError(f"不允许的产品分类: {row.product_name}")
            if row.source not in ALLOWED_SOURCES:
                raise ValueError(f"不允许的分类来源: {row.source}")
            if row.source == "llm" and row.confidence < min_llm_confidence:
                continue
            previous = selected.get(row.performance_id)
            if previous and previous != row:
                raise ValueError(f"同一绩效记录存在冲突分类: {row.performance_id}")
            selected[row.performance_id] = row
    return sorted(selected.values(), key=lambda item: item.performance_id)


def sql_values(rows: list[BackfillRow]) -> str:
    return ",\n".join(
        f"    ({row.performance_id}, '{row.product_name}', '{row.source}', {row.confidence:.4f})"
        for row in rows
    )


def generate_apply_sql(rows: list[BackfillRow], migration_key: str, digest: str) -> str:
    expected = len(rows)
    plan_table = f"z_plan_product_name_{migration_key}"
    backup_table = f"z_bak_t_performance_product_{migration_key}"
    return f"""-- 未知产品首批稳妥回填
-- 目标库：db_prize_cal
-- 计划行数：{expected}
-- 映射 SHA256：{digest}
-- 范围：规则分类全部 + LLM 置信度达到指定阈值的记录。
-- 注意：执行前仍为空的 product_name 才会更新。

SET NAMES utf8mb4;
USE `db_prize_cal`;

CREATE TEMPORARY TABLE `tmp_product_name_{migration_key}` (
    `performance_id` BIGINT UNSIGNED NOT NULL,
    `product_name` VARCHAR(255) NOT NULL,
    `source` VARCHAR(16) NOT NULL,
    `confidence` DECIMAL(6,4) NOT NULL,
    PRIMARY KEY (`performance_id`)
) ENGINE=InnoDB;

INSERT INTO `tmp_product_name_{migration_key}` (`performance_id`, `product_name`, `source`, `confidence`) VALUES
{sql_values(rows)};

DELIMITER $$
DROP PROCEDURE IF EXISTS `validate_product_backfill_{migration_key}`$$
CREATE PROCEDURE `validate_product_backfill_{migration_key}`()
BEGIN
    IF (SELECT COUNT(*) FROM `tmp_product_name_{migration_key}`) <> {expected} THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = '迁移终止：临时计划行数不符合预期';
    END IF;
    IF (SELECT COUNT(*)
        FROM `tmp_product_name_{migration_key}` plan
        JOIN `t_performance_statement` performance ON performance.`id` = plan.`performance_id`) <> {expected} THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = '迁移终止：部分目标 ID 在绩效表中不存在';
    END IF;
    IF (SELECT COUNT(*)
        FROM `tmp_product_name_{migration_key}` plan
        JOIN `t_performance_statement` performance ON performance.`id` = plan.`performance_id`
        WHERE NULLIF(TRIM(performance.`product_name`), '') IS NULL) <> {expected} THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = '迁移终止：部分目标记录的产品分类已被填写';
    END IF;
END$$
DELIMITER ;

CALL `validate_product_backfill_{migration_key}`();
DROP PROCEDURE `validate_product_backfill_{migration_key}`;

CREATE TABLE IF NOT EXISTS `{plan_table}` (
    `performance_id` BIGINT UNSIGNED NOT NULL,
    `product_name` VARCHAR(255) NOT NULL,
    `source` VARCHAR(16) NOT NULL,
    `confidence` DECIMAL(6,4) NOT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`performance_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `{backup_table}` LIKE `t_performance_statement`;

DELIMITER $$
DROP PROCEDURE IF EXISTS `assert_product_backfill_tables_{migration_key}`$$
CREATE PROCEDURE `assert_product_backfill_tables_{migration_key}`()
BEGIN
    IF (SELECT COUNT(*) FROM `{plan_table}`) <> 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = '迁移终止：计划表已有数据，请确认是否曾执行过本迁移';
    END IF;
    IF (SELECT COUNT(*) FROM `{backup_table}`) <> 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = '迁移终止：备份表已有数据，请确认是否曾执行过本迁移';
    END IF;
END$$
DELIMITER ;

CALL `assert_product_backfill_tables_{migration_key}`();
DROP PROCEDURE `assert_product_backfill_tables_{migration_key}`;

INSERT INTO `{plan_table}` (`performance_id`, `product_name`, `source`, `confidence`)
SELECT `performance_id`, `product_name`, `source`, `confidence`
FROM `tmp_product_name_{migration_key}`;

INSERT INTO `{backup_table}`
SELECT performance.*
FROM `t_performance_statement` performance
JOIN `{plan_table}` plan ON plan.`performance_id` = performance.`id`;
COMMIT;

DELIMITER $$
DROP PROCEDURE IF EXISTS `apply_product_backfill_{migration_key}`$$
CREATE PROCEDURE `apply_product_backfill_{migration_key}`()
BEGIN
    DECLARE changed_rows INT DEFAULT 0;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    IF (SELECT COUNT(*) FROM `{backup_table}`) <> {expected} THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = '迁移终止：备份行数不符合预期';
    END IF;

    START TRANSACTION;
    UPDATE `t_performance_statement` performance
    JOIN `{plan_table}` plan ON plan.`performance_id` = performance.`id`
    SET performance.`product_name` = plan.`product_name`,
        performance.`updated_at` = CURRENT_TIMESTAMP
    WHERE NULLIF(TRIM(performance.`product_name`), '') IS NULL;

    SET changed_rows = ROW_COUNT();
    IF changed_rows <> {expected} THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = '迁移终止：实际更新行数不符合预期';
    END IF;
    COMMIT;
END$$
DELIMITER ;

CALL `apply_product_backfill_{migration_key}`();
DROP PROCEDURE `apply_product_backfill_{migration_key}`;

SELECT plan.`source`, plan.`product_name`, COUNT(*) AS `updated_rows`
FROM `{plan_table}` plan
JOIN `t_performance_statement` performance ON performance.`id` = plan.`performance_id`
WHERE BINARY performance.`product_name` = BINARY plan.`product_name`
GROUP BY plan.`source`, plan.`product_name`
ORDER BY plan.`source`, plan.`product_name`;

-- 计划表和备份表在验收完成前保留，清理需另行审批。
"""


def generate_rollback_sql(rows: list[BackfillRow], migration_key: str) -> str:
    expected = len(rows)
    plan_table = f"z_plan_product_name_{migration_key}"
    backup_table = f"z_bak_t_performance_product_{migration_key}"
    return f"""-- 回滚未知产品首批稳妥回填
-- 只恢复 product_name 和原 updated_at，不覆盖其他业务字段。

SET NAMES utf8mb4;
USE `db_prize_cal`;

DELIMITER $$
DROP PROCEDURE IF EXISTS `rollback_product_backfill_{migration_key}`$$
CREATE PROCEDURE `rollback_product_backfill_{migration_key}`()
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    IF (SELECT COUNT(*) FROM `{plan_table}`) <> {expected} THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = '回滚终止：计划表行数不符合预期';
    END IF;
    IF (SELECT COUNT(*) FROM `{backup_table}`) <> {expected} THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = '回滚终止：备份表行数不符合预期';
    END IF;

    START TRANSACTION;
    UPDATE `t_performance_statement` performance
    JOIN `{backup_table}` backup_row ON backup_row.`id` = performance.`id`
    SET performance.`product_name` = backup_row.`product_name`,
        performance.`updated_at` = backup_row.`updated_at`;

    IF (SELECT COUNT(*)
        FROM `t_performance_statement` performance
        JOIN `{backup_table}` backup_row ON backup_row.`id` = performance.`id`
        WHERE NOT (performance.`product_name` <=> backup_row.`product_name`)
           OR NOT (performance.`updated_at` <=> backup_row.`updated_at`)) <> 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = '回滚终止：恢复后的字段与备份不一致';
    END IF;
    COMMIT;
END$$
DELIMITER ;

CALL `rollback_product_backfill_{migration_key}`();
DROP PROCEDURE `rollback_product_backfill_{migration_key}`;

SELECT COUNT(*) AS `restored_blank_product_rows`
FROM `t_performance_statement` performance
JOIN `{backup_table}` backup_row ON backup_row.`id` = performance.`id`
WHERE NULLIF(TRIM(performance.`product_name`), '') IS NULL;

-- 回滚后仍保留计划表和备份表，删除需另行审批。
"""


def generate_check_sql(rows: list[BackfillRow], migration_key: str) -> str:
    expected = len(rows)
    plan_table = f"z_plan_product_name_{migration_key}"
    backup_table = f"z_bak_t_performance_product_{migration_key}"
    selected_categories = ", ".join(f"'{name}'" for name in sorted({row.product_name for row in rows}))
    return f"""-- 未知产品回填只读验收
-- 可在迁移后或回滚后执行，本文件没有写操作。

SET NAMES utf8mb4;
USE `db_prize_cal`;

SELECT 'plan_rows' AS `check_name`, COUNT(*) AS `actual_value`, {expected} AS `expected_value`
FROM `{plan_table}`
UNION ALL
SELECT 'backup_rows', COUNT(*), {expected}
FROM `{backup_table}`
UNION ALL
SELECT 'matching_rows', COUNT(*), {expected}
FROM `{plan_table}` plan
JOIN `t_performance_statement` performance ON performance.`id` = plan.`performance_id`
WHERE BINARY performance.`product_name` = BINARY plan.`product_name`;

SELECT plan.`source`, plan.`product_name`, COUNT(*) AS `planned_rows`,
       SUM(BINARY performance.`product_name` = BINARY plan.`product_name`) AS `matching_rows`
FROM `{plan_table}` plan
JOIN `t_performance_statement` performance ON performance.`id` = plan.`performance_id`
GROUP BY plan.`source`, plan.`product_name`
ORDER BY plan.`source`, plan.`product_name`;

SELECT
    COUNT(*) AS `remaining_unknown_rows`,
    ROUND(COALESCE(SUM(`shipping_fee`), 0), 2) AS `remaining_unknown_revenue`,
    SUM(`shipping_fee` > 0 AND `shipping_cost` = 0) AS `remaining_missing_cost_rows`,
    ROUND(COALESCE(SUM(CASE WHEN `shipping_fee` > 0 AND `shipping_cost` = 0
        THEN NULL ELSE `shipping_fee` - `shipping_cost` END), 0), 2) AS `remaining_unknown_gross_profit`
FROM `t_performance_statement`
WHERE NULLIF(TRIM(`product_name`), '') IS NULL;

SELECT COALESCE(NULLIF(TRIM(`product_name`), ''), '未知产品') AS `product_name`,
       COUNT(*) AS `order_count`,
       ROUND(SUM(`shipping_fee`), 2) AS `revenue`,
       ROUND(COALESCE(SUM(CASE WHEN `shipping_fee` > 0 AND `shipping_cost` = 0
           THEN NULL ELSE `shipping_fee` - `shipping_cost` END), 0), 2) AS `gross_profit`
FROM `t_performance_statement`
WHERE NULLIF(TRIM(`product_name`), '') IS NULL
   OR TRIM(`product_name`) IN ({selected_categories})
GROUP BY COALESCE(NULLIF(TRIM(`product_name`), ''), '未知产品')
ORDER BY `gross_profit` DESC;
"""


def generate_runbook(rows: list[BackfillRow], migration_key: str, min_llm_confidence: float, digest: str) -> str:
    categories = Counter(row.product_name for row in rows)
    sources = Counter(row.source for row in rows)
    category_text = "、".join(f"{name} {count}" for name, count in sorted(categories.items()))
    return f"""# 未知产品首批回填操作单（{migration_key}）

本批只回填当前仍为空的 `t_performance_statement.product_name`，不改动其他业务字段。

## 执行范围

- 总行数：{len(rows)}
- 规则识别：{sources['rule']}
- LLM 识别：{sources['llm']}（置信度 ≥ {min_llm_confidence:.2f}）
- 分类分布：{category_text}
- 映射 SHA256：`{digest}`

## 执行顺序

1. 对 `db_prize_cal` 做一次完整逻辑备份并记录 SHA256。
2. 执行迁移 SQL。脚本会先在会话临时表中校验全部目标，再创建计划表和完整行备份表；任何目标记录已被填写时都会主动终止。
3. 执行只读验收 SQL，三个总数检查都应等于 {len(rows)}。
4. 打开经营分析页面，确认“未知产品”票数下降、分类排名合理、毛利润总额不变。
5. 若结果不符合预期，执行回滚 SQL，再执行只读验收 SQL确认 `matching_rows` 为 0。
6. 计划表和备份表暂不删除；稳定观察后另行审批清理。

## 待确认后执行的命令

以下命令目前仅作为操作清单，尚未执行：

```bash
mkdir -p /Users/hc/Desktop/code/data_backup/mysql/2026-10-26
docker exec mysql_db sh -c 'exec mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" --single-transaction --routines --triggers db_prize_cal' > /Users/hc/Desktop/code/data_backup/mysql/2026-10-26/db_prize_cal_before_product_backfill.sql
shasum -a 256 /Users/hc/Desktop/code/data_backup/mysql/2026-10-26/db_prize_cal_before_product_backfill.sql

docker exec -i mysql_db sh -c 'exec mysql -uroot -p"$MYSQL_ROOT_PASSWORD"' < cal_price_server/release_log/backfill_product_name_{migration_key}.sql
docker exec -i mysql_db sh -c 'exec mysql -uroot -p"$MYSQL_ROOT_PASSWORD"' < cal_price_server/release_log/check_product_name_{migration_key}.sql
```

需要回滚时：

```bash
docker exec -i mysql_db sh -c 'exec mysql -uroot -p"$MYSQL_ROOT_PASSWORD"' < cal_price_server/release_log/rollback_product_name_{migration_key}.sql
docker exec -i mysql_db sh -c 'exec mysql -uroot -p"$MYSQL_ROOT_PASSWORD"' < cal_price_server/release_log/check_product_name_{migration_key}.sql
```

## 文件

- `backfill_product_name_{migration_key}.sql`：备份、前置断言、事务更新、结果摘要。
- `check_product_name_{migration_key}.sql`：只读验收。
- `rollback_product_name_{migration_key}.sql`：恢复原产品名和原更新时间。

## 测试矩阵

| 场景 | 预期结果 |
| --- | --- |
| 正常首次执行 | 精确更新 {len(rows)} 行并提交 |
| 任一目标 ID 不存在 | 更新前终止 |
| 任一目标产品名已被人工/同步填写 | 更新前终止，避免覆盖 |
| 计划表或备份表已有数据 | 更新前终止，避免误重跑 |
| 更新行数不是 {len(rows)} | 事务回滚 |
| 同步源后续仍为空 | 保留本次回填值，不被清空 |
| 执行回滚 | 只恢复产品名和原更新时间，其他字段保持不变 |
| 经营分析复核 | 总收入、总成本、总毛利润不变，仅产品分组发生迁移 |
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="从分类预览生成产品名回填 SQL")
    parser.add_argument("preview", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--migration-key", default="20261026")
    parser.add_argument("--min-llm-confidence", type=float, default=0.9)
    args = parser.parse_args()

    rows = load_rows(args.preview, args.min_llm_confidence)
    canonical = "\n".join(
        f"{row.performance_id}|{row.product_name}|{row.source}|{row.confidence:.4f}" for row in rows
    )
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    outputs = {
        f"backfill_product_name_{args.migration_key}.sql": generate_apply_sql(rows, args.migration_key, digest),
        f"rollback_product_name_{args.migration_key}.sql": generate_rollback_sql(rows, args.migration_key),
        f"check_product_name_{args.migration_key}.sql": generate_check_sql(rows, args.migration_key),
        f"backfill_product_name_{args.migration_key}.md": generate_runbook(
            rows, args.migration_key, args.min_llm_confidence, digest
        ),
    }
    for name, content in outputs.items():
        (args.output_dir / name).write_text(content, encoding="utf-8")

    print(f"generated_rows={len(rows)}")
    print(f"mapping_sha256={digest}")
    for name in outputs:
        print(args.output_dir / name)


if __name__ == "__main__":
    main()
