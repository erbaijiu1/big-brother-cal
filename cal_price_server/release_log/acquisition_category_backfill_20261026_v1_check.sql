-- Facebook 获客分析 V1：回填后只读验收
SET NAMES utf8mb4;
USE `db_prize_cal`;

SELECT 'plan_names' AS `check_name`, COUNT(*) AS `actual_value`, 2587 AS `expected_value`
FROM `z_plan_acq_product_20261026_v1`
UNION ALL
SELECT 'backup_orders', COUNT(*), 7390 FROM `z_bak_acq_product_20261026_v1`
UNION ALL
SELECT 'normalized_orders', COUNT(*), 7390
FROM `z_bak_acq_product_20261026_v1` backup_row
JOIN `z_plan_acq_product_20261026_v1` plan
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
FROM `z_bak_acq_product_20261026_v1` backup_row
JOIN `z_plan_acq_product_20261026_v1` plan
  ON BINARY TRIM(backup_row.`product_name`) = BINARY plan.`raw_product_name`
JOIN `t_performance_statement` performance ON performance.`id` = backup_row.`id`
GROUP BY plan.`normalized_category`
ORDER BY `gross_profit` DESC;

SELECT
    ROUND(SUM(backup_row.`shipping_fee`), 2) AS `backup_revenue`,
    ROUND(SUM(performance.`shipping_fee`), 2) AS `current_revenue`,
    ROUND(SUM(backup_row.`shipping_cost`), 2) AS `backup_cost`,
    ROUND(SUM(performance.`shipping_cost`), 2) AS `current_cost`
FROM `z_bak_acq_product_20261026_v1` backup_row
JOIN `t_performance_statement` performance ON performance.`id` = backup_row.`id`;
