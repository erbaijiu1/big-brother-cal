-- 最新成本（2026-09-30 版）首批迁移：迁移后只读检查

SET NAMES utf8mb4;
USE `db_prize_cal`;

SELECT 'pricing_backup_rows' AS `check_name`, COUNT(*) AS `actual_value`
FROM `z_bak_t_pricing_rule_20261023`
UNION ALL
SELECT 'classification_backup_rows', COUNT(*)
FROM `z_bak_t_goods_classification_20261023`
UNION ALL
SELECT 'frozen_a_rules', COUNT(*)
FROM `t_pricing_rule`
WHERE `category_id` IN (1, 2) AND `channel` = '冻A';

SELECT `id`, `category_id`, `channel`, `transport_method`, `warehouse`,
       `unit_price_rules`, `delivery_fee_rules`, `remark`,
       JSON_VALID(`unit_price_rules`) AS `unit_json_valid`,
       JSON_VALID(`delivery_fee_rules`) AS `delivery_json_valid`
FROM `t_pricing_rule`
WHERE `id` IN (1, 37, 38, 39, 42, 43, 44)
   OR (`category_id` IN (1, 2) AND `channel` = '冻A')
ORDER BY `category_id`, `channel`, `id`;

SELECT `category_id`, `main_category`, `sub_examples`,
       (LENGTH(`sub_examples`) - LENGTH(REPLACE(`sub_examples`, '芒果', ''))) / LENGTH('芒果')
           AS `mango_occurrences`
FROM `t_goods_classification`
WHERE `category_id` = 14;

