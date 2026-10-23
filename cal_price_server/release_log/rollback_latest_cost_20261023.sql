-- 回滚 update_latest_cost_20261023.sql 触及的全部行。
-- 前提：迁移创建的两个 z_bak_*_20261023 快照表仍然存在。

SET NAMES utf8mb4;
USE `db_prize_cal`;

START TRANSACTION;

DELETE FROM `t_pricing_rule`
WHERE `id` IN (1, 37, 38, 39, 42, 43, 44)
   OR (`category_id` IN (1, 2) AND `channel` = '冻A');

INSERT INTO `t_pricing_rule`
SELECT * FROM `z_bak_t_pricing_rule_20261023`;

UPDATE `t_goods_classification` AS current_row
JOIN `z_bak_t_goods_classification_20261023` AS backup_row
  ON backup_row.`category_id` = current_row.`category_id`
SET current_row.`main_category` = backup_row.`main_category`,
    current_row.`sub_examples` = backup_row.`sub_examples`,
    current_row.`description` = backup_row.`description`,
    current_row.`temperature_req` = backup_row.`temperature_req`,
    current_row.`hazard_level` = backup_row.`hazard_level`,
    current_row.`storage_level` = backup_row.`storage_level`,
    current_row.`create_time` = backup_row.`create_time`,
    current_row.`last_modified` = backup_row.`last_modified`,
    current_row.`status` = backup_row.`status`,
    current_row.`priority` = backup_row.`priority`,
    current_row.`customer_price_tiers` = backup_row.`customer_price_tiers`,
    current_row.`price_tiers_updated_at` = backup_row.`price_tiers_updated_at`,
    current_row.`warehouse_acceptance_policy` = backup_row.`warehouse_acceptance_policy`,
    current_row.`acceptance_notice` = backup_row.`acceptance_notice`
WHERE current_row.`category_id` = 14;

COMMIT;

-- 为便于复核，回滚后仍保留快照表；确认无误后再单独审批删除。

