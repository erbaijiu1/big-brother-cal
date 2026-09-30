SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `t_cooperation_quote_config` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `category_id` int NOT NULL COMMENT '货物分类ID',
  `enabled` tinyint(1) NOT NULL DEFAULT 1 COMMENT '是否启用',
  `currency` varchar(10) NOT NULL DEFAULT 'CNY' COMMENT '币种',
  `price_tiers` text NOT NULL COMMENT '合作阶梯价 JSON',
  `delivery_base_fee` decimal(10,2) DEFAULT NULL COMMENT '香港派送基础费用',
  `delivery_included_weight` decimal(10,2) DEFAULT NULL COMMENT '基础派送费包重 kg',
  `delivery_excess_rate` decimal(10,2) DEFAULT NULL COMMENT '超重派送费 元/kg',
  `sea_crossing_notice` varchar(255) DEFAULT '' COMMENT '港岛过海说明',
  `upstairs_notice` text COMMENT '上楼费用说明',
  `cutoff_text` varchar(255) DEFAULT '' COMMENT '入仓截单说明',
  `eta_text` varchar(255) DEFAULT '' COMMENT '运输时效说明',
  `customer_notice` text COMMENT '其他对客说明',
  `config_updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '配置更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_cooperation_quote_category` (`category_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='长期合作客户品类报价配置';

INSERT INTO `t_cooperation_quote_config`
(`category_id`, `price_tiers`, `delivery_base_fee`, `delivery_included_weight`, `delivery_excess_rate`, `sea_crossing_notice`, `upstairs_notice`, `cutoff_text`, `eta_text`, `customer_notice`)
VALUES
(1, '[{"min_quantity":1,"max_quantity":100,"min_price":12,"max_price":15,"unit":"kg"},{"min_quantity":101,"max_quantity":500,"min_price":11,"max_price":13,"unit":"kg"},{"min_quantity":501,"max_quantity":1000,"min_price":11,"max_price":12,"unit":"kg"},{"min_quantity":1001,"max_quantity":null,"min_price":10.5,"max_price":12,"unit":"kg"}]', 85, 30, 1, '港岛过海加20元/票', '上楼费用按实际地址确认', '当日中午12点前送到深圳仓', '次日香港派送上门', ''),
(2, '[{"min_quantity":1,"max_quantity":100,"min_price":7,"max_price":9,"unit":"kg"},{"min_quantity":101,"max_quantity":500,"min_price":6,"max_price":8,"unit":"kg"},{"min_quantity":501,"max_quantity":1000,"min_price":5.5,"max_price":7,"unit":"kg"},{"min_quantity":1001,"max_quantity":null,"min_price":5,"max_price":6.5,"unit":"kg"}]', 85, 30, 1, '港岛过海加20元/票', '上楼费用按实际地址确认', '当日中午12点前送到深圳仓', '次日香港派送上门', ''),
(4, '[{"min_quantity":1,"max_quantity":1000,"min_price":1.5,"max_price":2.5,"unit":"kg"},{"min_quantity":1001,"max_quantity":3000,"min_price":1.3,"max_price":2,"unit":"kg"},{"min_quantity":3001,"max_quantity":null,"min_price":1.2,"max_price":1.8,"unit":"kg"}]', 150, 300, 0.3, '港岛过海加50-400元/票（按区域）', '地面交收；工业大厦上楼加0.5元/kg；住宅、商业写字楼有电梯无台阶加1.5元/kg；有台阶需具体确认', '当日17点前送到深圳仓', '3-5日香港派送；海关查验可能延迟', ''),
(9, '[{"min_quantity":1,"max_quantity":1000,"min_price":1,"max_price":2,"unit":"kg"},{"min_quantity":1001,"max_quantity":3000,"min_price":1,"max_price":1.8,"unit":"kg"},{"min_quantity":3001,"max_quantity":null,"min_price":0.8,"max_price":1.5,"unit":"kg"}]', 150, 300, 0.3, '港岛过海加50-400元/票（按区域）', '地面交收；工业大厦上楼加0.5元/kg；住宅、商业写字楼有电梯无台阶加1.5元/kg；有台阶需具体确认', '当日17点前送到深圳仓', '次日香港派送；海关查验可能延迟', ''),
(11, '[{"min_quantity":1,"max_quantity":1000,"min_price":1.5,"max_price":2.5,"unit":"kg"},{"min_quantity":1001,"max_quantity":3000,"min_price":1.3,"max_price":2,"unit":"kg"},{"min_quantity":3001,"max_quantity":null,"min_price":1.2,"max_price":1.8,"unit":"kg"}]', 150, 300, 0.3, '港岛过海加50-400元/票（按区域）', '地面交收；工业大厦上楼加0.5元/kg；住宅、商业写字楼有电梯无台阶加1.5元/kg；有台阶需具体确认', '当日17点前送到深圳仓', '3-5日香港派送；海关查验可能延迟', ''),
(12, '[{"min_quantity":1,"max_quantity":1000,"min_price":1.5,"max_price":2.5,"unit":"kg"},{"min_quantity":1001,"max_quantity":3000,"min_price":1.3,"max_price":2,"unit":"kg"},{"min_quantity":3001,"max_quantity":null,"min_price":1.2,"max_price":1.8,"unit":"kg"}]', 150, 300, 0.3, '港岛过海加50-400元/票（按区域）', '地面交收；工业大厦上楼加0.5元/kg；住宅、商业写字楼有电梯无台阶加1.5元/kg；有台阶需具体确认', '当日17点前送到深圳仓', '3-5日香港派送；海关查验可能延迟', '液体货物需确认成分、酒精含量、防泄漏包装及申报资料'),
(18, '[{"min_quantity":1,"max_quantity":1000,"min_price":1.5,"max_price":2.5,"unit":"kg"},{"min_quantity":1001,"max_quantity":3000,"min_price":1.3,"max_price":2,"unit":"kg"},{"min_quantity":3001,"max_quantity":null,"min_price":1.2,"max_price":1.8,"unit":"kg"}]', 150, 300, 0.3, '港岛过海加50-400元/票（按区域）', '地面交收；工业大厦上楼加0.5元/kg；住宅、商业写字楼有电梯无台阶加1.5元/kg；有台阶需具体确认', '当日17点前送到深圳仓', '3-5日香港派送；海关查验可能延迟', '')
ON DUPLICATE KEY UPDATE
  `price_tiers` = VALUES(`price_tiers`),
  `delivery_base_fee` = VALUES(`delivery_base_fee`),
  `delivery_included_weight` = VALUES(`delivery_included_weight`),
  `delivery_excess_rate` = VALUES(`delivery_excess_rate`),
  `sea_crossing_notice` = VALUES(`sea_crossing_notice`),
  `upstairs_notice` = VALUES(`upstairs_notice`),
  `cutoff_text` = VALUES(`cutoff_text`),
  `eta_text` = VALUES(`eta_text`),
  `customer_notice` = VALUES(`customer_notice`);
