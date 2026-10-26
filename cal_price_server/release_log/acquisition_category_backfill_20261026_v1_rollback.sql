-- Facebook 获客分析 V1：品名归一回滚
-- 只恢复 product_name 和原 updated_at，不覆盖其他业务字段。
SET NAMES utf8mb4;
USE `db_prize_cal`;

DELIMITER $$
DROP PROCEDURE IF EXISTS `rollback_acq_category_20261026_v1`$$
CREATE PROCEDURE `rollback_acq_category_20261026_v1`()
BEGIN
    DECLARE changed_rows INT DEFAULT 0;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    IF (SELECT COUNT(*) FROM `z_bak_acq_product_20261026_v1`) <> 7390 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '回滚终止：行级备份数量不符合预期';
    END IF;

    START TRANSACTION;
    UPDATE `t_performance_statement` performance
    JOIN `z_bak_acq_product_20261026_v1` backup_row ON backup_row.`id` = performance.`id`
    SET performance.`product_name` = backup_row.`product_name`,
        performance.`updated_at` = backup_row.`updated_at`;
    SET changed_rows = ROW_COUNT();
    IF changed_rows <> 7390 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '回滚终止：恢复行数不符合预期';
    END IF;
    COMMIT;
END$$
DELIMITER ;

CALL `rollback_acq_category_20261026_v1`();
DROP PROCEDURE `rollback_acq_category_20261026_v1`;

SELECT COUNT(*) AS `restored_orders`, 7390 AS `expected_orders`
FROM `t_performance_statement` performance
JOIN `z_bak_acq_product_20261026_v1` backup_row ON backup_row.`id` = performance.`id`
WHERE BINARY performance.`product_name` = BINARY backup_row.`product_name`
  AND performance.`updated_at` <=> backup_row.`updated_at`;

-- 回滚后仍保留计划表和备份表，删除需另行审批。
