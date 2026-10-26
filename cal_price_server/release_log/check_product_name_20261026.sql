-- 未知产品回填只读验收
-- 可在迁移后或回滚后执行，本文件没有写操作。

SET NAMES utf8mb4;
USE `db_prize_cal`;

SELECT 'plan_rows' AS `check_name`, COUNT(*) AS `actual_value`, 1940 AS `expected_value`
FROM `z_plan_product_name_20261026`
UNION ALL
SELECT 'backup_rows', COUNT(*), 1940
FROM `z_bak_t_performance_product_20261026`
UNION ALL
SELECT 'matching_rows', COUNT(*), 1940
FROM `z_plan_product_name_20261026` plan
JOIN `t_performance_statement` performance ON performance.`id` = plan.`performance_id`
WHERE BINARY performance.`product_name` = BINARY plan.`product_name`;

SELECT plan.`source`, plan.`product_name`, COUNT(*) AS `planned_rows`,
       SUM(BINARY performance.`product_name` = BINARY plan.`product_name`) AS `matching_rows`
FROM `z_plan_product_name_20261026` plan
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
   OR TRIM(`product_name`) IN ('冻品', '普货', '水产海鲜', '水果', '熟食', '生鲜肉类', '酒类', '食品')
GROUP BY COALESCE(NULLIF(TRIM(`product_name`), ''), '未知产品')
ORDER BY `gross_profit` DESC;
