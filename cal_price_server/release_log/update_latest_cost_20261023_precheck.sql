-- 最新成本（2026-09-30 版）首批无歧义规则：迁移前只读检查
-- 目标库：db_prize_cal
-- 本文件只读，不会修改数据。

SET NAMES utf8mb4;
USE `db_prize_cal`;

SELECT `id`, `category_id`, `channel`, `transport_method`, `warehouse`,
       `unit_price_rules`, `delivery_fee_rules`, `delivery_time`, `remark`
FROM `t_pricing_rule`
WHERE `id` IN (1, 37, 38, 39, 42, 43, 44)
   OR (`category_id` IN (1, 2) AND `channel` = '冻A')
ORDER BY `category_id`, `channel`, `id`;

SELECT `category_id`, `main_category`, `sub_examples`
FROM `t_goods_classification`
WHERE `category_id` = 14;

SELECT `channel_code`, `channel_name`, `delete_flag`
FROM `t_channel_config`
WHERE `channel_code` IN ('普A', '冻A', '冻B', '冻C', '冻L')
ORDER BY `channel_code`;

