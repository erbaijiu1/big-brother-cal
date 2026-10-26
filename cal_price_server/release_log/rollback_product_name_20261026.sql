-- 回滚未知产品首批稳妥回填
-- 只恢复 product_name 和原 updated_at，不覆盖其他业务字段。

SET NAMES utf8mb4;
USE `db_prize_cal`;

DELIMITER $$
DROP PROCEDURE IF EXISTS `rollback_product_backfill_20261026`$$
CREATE PROCEDURE `rollback_product_backfill_20261026`()
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    IF (SELECT COUNT(*) FROM `z_plan_product_name_20261026`) <> 1940 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = '回滚终止：计划表行数不符合预期';
    END IF;
    IF (SELECT COUNT(*) FROM `z_bak_t_performance_product_20261026`) <> 1940 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = '回滚终止：备份表行数不符合预期';
    END IF;

    START TRANSACTION;
    UPDATE `t_performance_statement` performance
    JOIN `z_bak_t_performance_product_20261026` backup_row ON backup_row.`id` = performance.`id`
    SET performance.`product_name` = backup_row.`product_name`,
        performance.`updated_at` = backup_row.`updated_at`;

    IF (SELECT COUNT(*)
        FROM `t_performance_statement` performance
        JOIN `z_bak_t_performance_product_20261026` backup_row ON backup_row.`id` = performance.`id`
        WHERE NOT (performance.`product_name` <=> backup_row.`product_name`)
           OR NOT (performance.`updated_at` <=> backup_row.`updated_at`)) <> 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = '回滚终止：恢复后的字段与备份不一致';
    END IF;
    COMMIT;
END$$
DELIMITER ;

CALL `rollback_product_backfill_20261026`();
DROP PROCEDURE `rollback_product_backfill_20261026`;

SELECT COUNT(*) AS `restored_blank_product_rows`
FROM `t_performance_statement` performance
JOIN `z_bak_t_performance_product_20261026` backup_row ON backup_row.`id` = performance.`id`
WHERE NULLIF(TRIM(performance.`product_name`), '') IS NULL;

-- 回滚后仍保留计划表和备份表，删除需另行审批。
