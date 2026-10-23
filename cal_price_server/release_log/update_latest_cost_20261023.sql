-- 最新成本（2026-09-30 版）首批无歧义规则
-- 目标库：db_prize_cal
-- 来源：docs/最新成本9.30.xlsx
--
-- 本批范围：
--   1. 普A：分类 8 更新为 0.6 元/kg、120 元/cbm，二者取大。
--   2. 冻A：新增生货、熟货公斤价；派送 80 元含 30kg，续重 1 元/kg。
--   3. 冻B、冻C：更新生货、熟货公斤价和上述派送价。
--   4. 冻L：仅将运输方式修正为“海运冻柜”；成本与派送价保持现值。
--   5. 分类 14 示例补充“芒果”，使模型有明确的水果分类锚点；本批不新增箱价。
--
-- 明确不在本批：水果/青菜箱价、冻Q、冻G、冻W、普A重复规则清理。
-- 迁移前必须先完成整库 mysqldump，并执行配套 precheck。

SET NAMES utf8mb4;
USE `db_prize_cal`;

-- 持久化保存本批会触及的原始行。重复执行时 INSERT IGNORE 不覆盖第一次快照。
CREATE TABLE IF NOT EXISTS `z_bak_t_pricing_rule_20261023` LIKE `t_pricing_rule`;
INSERT IGNORE INTO `z_bak_t_pricing_rule_20261023`
SELECT *
FROM `t_pricing_rule`
WHERE `id` IN (1, 37, 38, 39, 42, 43, 44)
   OR (`category_id` IN (1, 2) AND `channel` = '冻A');

CREATE TABLE IF NOT EXISTS `z_bak_t_goods_classification_20261023` LIKE `t_goods_classification`;
INSERT IGNORE INTO `z_bak_t_goods_classification_20261023`
SELECT *
FROM `t_goods_classification`
WHERE `category_id` = 14;

DELIMITER $$
DROP PROCEDURE IF EXISTS `assert_latest_cost_20261023_preconditions`$$
CREATE PROCEDURE `assert_latest_cost_20261023_preconditions`()
BEGIN
    IF (SELECT COUNT(*) FROM `t_pricing_rule`
        WHERE (`id` = 1  AND `category_id` = 8 AND `channel` = '普A')
           OR (`id` = 37 AND `category_id` = 1 AND `channel` = '冻B')
           OR (`id` = 38 AND `category_id` = 1 AND `channel` = '冻C')
           OR (`id` = 39 AND `category_id` = 2 AND `channel` = '冻C')
           OR (`id` = 42 AND `category_id` = 1 AND `channel` = '冻L')
           OR (`id` = 43 AND `category_id` = 2 AND `channel` = '冻L')
           OR (`id` = 44 AND `category_id` = 2 AND `channel` = '冻B')) <> 7 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = '迁移终止：7 条目标计价规则与预期 ID/分类/渠道不一致';
    END IF;

    IF (SELECT COUNT(*) FROM `t_pricing_rule`
        WHERE `category_id` IN (1, 2) AND `channel` = '冻A') <> 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = '迁移终止：已存在冻A生货/熟货规则，请人工合并';
    END IF;

    IF (SELECT COUNT(*) FROM `t_goods_classification` WHERE `category_id` = 14) <> 1 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = '迁移终止：分类14不存在或不唯一';
    END IF;
END$$
DELIMITER ;

CALL `assert_latest_cost_20261023_preconditions`();
DROP PROCEDURE `assert_latest_cost_20261023_preconditions`;

START TRANSACTION;

UPDATE `t_pricing_rule`
SET `unit_price_rules` = '[{"range":"0-99999999","prize_type":"KG","unit_price":0.6},{"range":"0-99999999","prize_type":"CBM","unit_price":120}]',
    `remark` = CONCAT_WS('；', NULLIF(`remark`, ''), '最新成本9.30：0.6元/kg或120元/cbm，二者取大')
WHERE `id` = 1 AND `category_id` = 8 AND `channel` = '普A';

UPDATE `t_pricing_rule`
SET `unit_price_rules` = '[{"range":"0-99999999","prize_type":"KG","unit_price":12}]',
    `delivery_fee_rules` = '[{"range":"0-99999999","prize_type":"KG","unit_price":1,"base_fees":80,"deduction_value":30}]',
    `remark` = CONCAT_WS('；', NULLIF(`remark`, ''), '最新成本9.30：冻B生货12元/kg；派送80元含30kg，续重1元/kg')
WHERE `id` = 37 AND `category_id` = 1 AND `channel` = '冻B';

UPDATE `t_pricing_rule`
SET `unit_price_rules` = '[{"range":"0-300","prize_type":"KG","unit_price":9.5},{"range":"300-99999999","prize_type":"KG","unit_price":9}]',
    `delivery_fee_rules` = '[{"range":"0-99999999","prize_type":"KG","unit_price":1,"base_fees":80,"deduction_value":30}]',
    `remark` = CONCAT_WS('；', NULLIF(`remark`, ''), '最新成本9.30：冻C生货300kg内9.5元/kg，超过300kg为9元/kg；派送80元含30kg，续重1元/kg')
WHERE `id` = 38 AND `category_id` = 1 AND `channel` = '冻C';

UPDATE `t_pricing_rule`
SET `unit_price_rules` = '[{"range":"0-300","prize_type":"KG","unit_price":5},{"range":"300-500","prize_type":"KG","unit_price":4.5},{"range":"500-99999999","prize_type":"KG","unit_price":4}]',
    `delivery_fee_rules` = '[{"range":"0-99999999","prize_type":"KG","unit_price":1,"base_fees":80,"deduction_value":30}]',
    `remark` = CONCAT_WS('；', NULLIF(`remark`, ''), '最新成本9.30：冻C熟货300kg内5元/kg，301-500kg为4.5元/kg，超过500kg为4元/kg；派送80元含30kg，续重1元/kg')
WHERE `id` = 39 AND `category_id` = 2 AND `channel` = '冻C';

UPDATE `t_pricing_rule`
SET `transport_method` = '海运冻柜',
    `remark` = CONCAT_WS('；', NULLIF(`remark`, ''), '最新成本9.30：运输方式修正为海运冻柜')
WHERE `id` IN (42, 43) AND `channel` = '冻L';

UPDATE `t_pricing_rule`
SET `unit_price_rules` = '[{"range":"0-99999999","prize_type":"KG","unit_price":6.5}]',
    `delivery_fee_rules` = '[{"range":"0-99999999","prize_type":"KG","unit_price":1,"base_fees":80,"deduction_value":30}]',
    `remark` = CONCAT_WS('；', NULLIF(`remark`, ''), '最新成本9.30：冻B熟货6.5元/kg；派送80元含30kg，续重1元/kg')
WHERE `id` = 44 AND `category_id` = 2 AND `channel` = '冻B';

INSERT INTO `t_pricing_rule`
    (`category_id`, `channel`, `transport_method`, `warehouse`, `min_consumption`,
     `unit_price_rules`, `discount_price`, `surcharge_fee_rules`, `delivery_fee_rules`,
     `delivery_time`, `packaging_requirement`, `remark`, `compensation_policy`,
     `status`, `filter_rules`, `region_rules`)
SELECT 1, '冻A', `transport_method`, `warehouse`, `min_consumption`,
       '[{"range":"0-500","prize_type":"KG","unit_price":10.5},{"range":"500-99999999","prize_type":"KG","unit_price":10}]',
       `discount_price`, `surcharge_fee_rules`,
       '[{"range":"0-99999999","prize_type":"KG","unit_price":1,"base_fees":80,"deduction_value":30}]',
       `delivery_time`, `packaging_requirement`,
       '最新成本9.30：冻A生货500kg内10.5元/kg，超过500kg为10元/kg；派送80元含30kg，续重1元/kg',
       `compensation_policy`, `status`, `filter_rules`, `region_rules`
FROM `t_pricing_rule`
WHERE `id` = 37
UNION ALL
SELECT 2, '冻A', `transport_method`, `warehouse`, `min_consumption`,
       '[{"range":"0-500","prize_type":"KG","unit_price":6.5},{"range":"500-99999999","prize_type":"KG","unit_price":6}]',
       `discount_price`, `surcharge_fee_rules`,
       '[{"range":"0-99999999","prize_type":"KG","unit_price":1,"base_fees":80,"deduction_value":30}]',
       `delivery_time`, `packaging_requirement`,
       '最新成本9.30：冻A熟货500kg内6.5元/kg，超过500kg为6元/kg；派送80元含30kg，续重1元/kg',
       `compensation_policy`, `status`, `filter_rules`, `region_rules`
FROM `t_pricing_rule`
WHERE `id` = 44;

UPDATE `t_goods_classification`
SET `sub_examples` = CASE
        WHEN LOCATE('芒果', COALESCE(`sub_examples`, '')) > 0 THEN `sub_examples`
        WHEN TRIM(COALESCE(`sub_examples`, '')) = '' THEN '芒果'
        ELSE CONCAT(`sub_examples`, '、芒果')
    END
WHERE `category_id` = 14;

COMMIT;

-- 快照表在验收完成前保留；确认稳定后再单独审批是否删除。
