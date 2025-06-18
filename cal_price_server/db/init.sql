use db_prize_cal;
INSERT INTO t_goods_classification
(main_category, sub_examples, description, temperature_req, hazard_level, storage_level)
VALUES
( '冷冻生肉', '冷冻／冷藏生肉', '港区仓库全程 −18℃ 冷链，严格 FIFO', '冷链', '非险', '专属冷链（A）'),
( '冷链烘焙 & 豆制品', '包子（无肉）、糕点、豆腐、雪糕', '全程 0~4℃ 冷链，包装合规要求高', '冷链', '非险', '专属冷链（A）'),
('化妆品', '护肤品、日化', '常温；易碎易泄露类需二次防护；可海运／陆运', '常温', '非险', 'B（中价值）'),
('常温食品', '干货、零食、饼干、卤味、熟肉、面点', '常温；保质期长，适合 C 库（低值慢品）', '常温', '非险', 'C（低价值）'),
('高度白酒（危险品）', '≥40° 白酒（不含茅台/五粮液）', '危险品申报，需 MSDS、危包证；仅海运', '常温', '险', '危险品库（D）'),
('红酒 & 啤酒', '干红、啤酒（有商检资料可正报）', '<24° 可走一般货；≥24° 同 T5 处理；普通酒需商检／报关资料', '常温', '部分险', 'B（或 D）'),
('雪种（制冷剂）', '冷媒／制冷剂', 'IMDG Class 2.2（非易燃气体）或 Class 9；需专舱', '常温', '险', '专用危险库（E）'),
('建材 & 家具', '木柜板、瓷砖、玻璃、钢铁、轨道', '重货低值，走陆运 A 类；装卸需机械化', '常温', '非险', 'A（重货库）'),
('普货 & 日杂', '居家用品、文具、快递日杂', '常温；普通非危险，无品牌家电', '常温', '非险', 'B（中价值）'),
('高价酒类 & 高价值货物', '茅台、五粮液、品牌高端酒、珠宝等', '实时询价；精细化包装与安保；可走白手转电', '常温', '非险', 'G（精品库）'),
('粮食散装', '大米、面粉、玉米渣', '干货散装，防潮防虫；海运/陆运均可', '常温', '非险', 'F（散货库）'),
('液体食品 & 液体日化', '饮料、酱油、食用油；化妆水、洗手液', '防泄漏二次包装；需检验成分、标签；部分属危险品（酒精含量高）', '常温', '部分险', 'B / D（视风险）'),
('禁运 & 限运品', '枪弹、毒化剂、盗版货物、电池等', '系统屏蔽，不可下单；需遵守中港两地法律法规', '—', '禁运／限运', '禁运／限运');

INSERT INTO t_goods_classification
(main_category, sub_examples, description, temperature_req, hazard_level, storage_level)
VALUES
('蔬菜水果', '西红柿、黄瓜、菠菜、生菜、苹果、香蕉、草莓',
'2–8℃；85–95% 湿度；需乙烯控制；易腐品优先配送',
'冷链', '非险', '专属冷链（A）');

INSERT INTO t_goods_classification
(main_category, sub_examples, description, temperature_req, hazard_level, storage_level)
VALUES
('水生动物', '观赏鱼（龙鱼、热带鱼等）、观赏虾',
'需活水氧气包装（水桶+泡沫箱），机舱温度维持18–25℃，分规格报价（如龙鱼按cm计价）',
'常温', '非险', '生物存活库（B）'),
('其它鲜活', '昆虫（蟑螂、蜘蛛、蜗牛）、爬行类（小蛇、守宫）、小型哺乳（刺猬、松鼠）、宠物犬猫等',
'采用透气/通风包装（盒/笼），环境温度18–25℃（或常温），需提供检疫/健康证或CITES许可',
'常温', '非险', '特殊生物库（C）');

INSERT INTO t_goods_classification
(main_category, sub_examples, description, temperature_req, hazard_level, storage_level)
VALUES
('鲜活植物', '鲜花、草皮、草卷',
'全程 2–8℃ 冷链；湿度控制 85–95%；需透气包装/防压保护；出运前须备齐植物检疫证、原产地证',
'冷链', '非险', '专属冷链（A）');


-- 将 NULL 字段替换为 ''，适用于不允许 NULL 的字段情况（如 SQLite 默认不允许部分字段为 NULL）
-- 注意：JSON 字符串依然保持双引号转义格式

INSERT INTO t_pricing_rule (category_id, channel, transport_method, warehouse, min_consumption, unit_price_rules, discount_price, surcharge_fee_rules, delivery_fee_rules, delivery_time, packaging_requirement, remark, compensation_policy)VALUES

-- 建材 & 家具
(8, '普A', '陆运', '深圳仓', '', '[{"range": "0-1000", "unit_price":0.5, "prize_type":"KG"}, {"range": "1000-99999999", "unit_price":0.3, "prize_type":"KG"}, {"range": "0-99999999", "unit_price":100, "prize_type":"CBM"}]', '', '[{"range": "0-0.2", "total_prize":100, "prize_type":"CBM"}, {"range": "0.2-2", "total_prize":150, "prize_type":"CBM"}, {"range": "2-99999999", "unit_price":50, "prize_type":"CBM"}, {"range": "0-40", "total_prize":100, "prize_type":"KG"}, {"range": "40-300", "total_prize":150, "prize_type":"KG"}, {"range": "300-99999999", "unit_price":0.3, "prize_type":"KG"}]', '', '', '', '', ''),

-- 普货 & 日杂
(9, '普A', '陆运', '深圳仓', '', '[{"range": "0-1000", "unit_price": 0.6, "prize_type": "KG"}, {"range": "1000-99999999", "unit_price": 0.4, "prize_type": "KG"}, {"range": "0-99999999", "unit_price": 120, "prize_type": "CBM"}]', '', '[{"range": "0-0.2", "total_prize": 100, "prize_type": "CBM"}, {"range": "0.2-2", "total_prize": 150, "prize_type": "CBM"}, {"range": "2-99999999", "unit_price": 50, "prize_type": "CBM"}, {"range": "0-40", "total_prize": 100, "prize_type": "KG"}, {"range": "40-300", "total_prize": 150, "prize_type": "KG"}, {"range": "300-99999999", "unit_price": 0.3, "prize_type": "KG"}]', '', '', '', '', ''),

-- 危险化学品
(7, '普A', '海运', '深圳仓', '', '[{"range": "0-99999999", "unit_price": 2.5, "prize_type": "KG"}, {"range": "0-99999999", "unit_price": 500, "prize_type": "CBM"}]', '', '[{"range": "0-0.2", "total_prize": 100, "prize_type": "CBM"}, {"range": "0.2-2", "total_prize": 150, "prize_type": "CBM"}, {"range": "2-99999999", "unit_price": 50, "prize_type": "CBM"}, {"range": "0-40", "total_prize": 100, "prize_type": "KG"}, {"range": "40-300", "total_prize": 150, "prize_type": "KG"}, {"range": "300-99999999", "unit_price": 0.3, "prize_type": "KG"}]', '', '', '', '', ''),

-- 粮食散装
(11, '普A', '海运', '深圳仓', '', '[{"range": "0-99999999", "unit_price": 3.0, "prize_type": "KG"}, {"range": "0-99999999", "unit_price": 600, "prize_type": "CBM"}]', '', '[{"range": "0-0.2", "total_prize": 100, "prize_type": "CBM"}, {"range": "0.2-2", "total_prize": 150, "prize_type": "CBM"}, {"range": "2-99999999", "unit_price": 50, "prize_type": "CBM"}, {"range": "0-40", "total_prize": 100, "prize_type": "KG"}, {"range": "40-300", "total_prize": 150, "prize_type": "KG"}, {"range": "300-99999999", "unit_price": 0.3, "prize_type": "KG"}]', '', '', '', '', ''),

-- 高价酒类 & 高价值货物
(10, '普A', '海运', '深圳仓', '', '[{"range": "0-99999999", "prize_type": "negotiated"}]', '', '[{"range": "0-99999999", "prize_type": "negotiated"}]', '', '', '', '', ''),

-- 常温食品
(4, '普A', '陆运', '深圳仓', '', '[{"range": "0-99999999", "unit_price": 4.0, "prize_type": "KG"}, {"range": "0-99999999", "unit_price": 800, "prize_type": "CBM"}]', '', '[{"range": "0-0.2", "total_prize": 100, "prize_type": "CBM"}, {"range": "0.2-2", "total_prize": 150, "prize_type": "CBM"}, {"range": "2-99999999", "unit_price": 50, "prize_type": "CBM"}, {"range": "0-40", "total_prize": 100, "prize_type": "KG"}, {"range": "40-300", "total_prize": 150, "prize_type": "KG"}, {"range": "300-99999999", "unit_price": 0.3, "prize_type": "KG"}]', '', '', '', '', '');



-- 渠道附加费配置插入语句（将 NULL 改为 '' 作为默认空值）
INSERT INTO t_channel_config (channel_code, channel_name, surcharge_rules) VALUES

-- 冻品渠道
('冻A', '牛哥', ''),
('冻B', '潘潘', ''),
('冻C', '盐田', ''),
('冻G', '廖总', ''),
('冻L', '刘总', ''),

-- 普通渠道：普A含完整规则
('普A', '港利发', '{
  "surcharges": [
    {"name": "sea_crossing_fee", "description": "过海费（Van）", "condition": "volume<=0.2 CBM AND weight<=40 KG", "unit": "per_shipment", "price": 30},
    {"name": "sea_crossing_fee_truck", "description": "过海费（吨车，超标）", "condition": "NOT (volume<=0.2 CBM AND weight<=40 KG)", "unit": "per_shipment", "price": 50},
    {"name": "remote_area_fee_100", "description": "偏远费 ¥100（西贡/东涌/赤柱/…）", "condition": "destination IN [\"西贡\",\"东涌\",\"赤柱\",\"龙鼓滩\",\"半山\",\"沙头角\"]", "unit": "per_shipment", "price": 100},
    {"name": "remote_area_fee_300", "description": "偏远费 ¥300（愉景湾）", "condition": "destination == \"愉景湾\"", "unit": "per_shipment", "price": 300},
    {"name": "queue_and_docs_fee", "description": "排队交仓单费", "condition": "always", "unit": "per_shipment", "price": 200},
    {"name": "self_pickup_registration_fee", "description": "自提登记费", "condition": "volume<=3 CBM AND weight<=1 T", "unit": "per_shipment", "price": 100},
    {"name": "self_pickup_registration_fee", "description": "自提登记费", "condition": "volume<=6 CBM AND weight<=2 T", "unit": "per_shipment", "price": 200},
    {"name": "self_pickup_registration_fee", "description": "自提登记费", "condition": "volume<=9 CBM AND weight<=3 T", "unit": "per_shipment", "price": 300},
    {"name": "oversize_fee", "description": "超长费", "conditions": [
      {"length": 3, "unit": "M", "price": 50},
      {"length": 4, "unit": "M", "price": 100},
      {"length": 5, "unit": "M", "price": 150},
      {"length": 6, "unit": "M", "price": 300},
      {"length": 7, "unit": "M", "price": 600}
    ]},
    {"name": "elevator_handling_fee", "description": "电梯上楼／抛货", "condition": "elevator_required == true", "unit": "per_CBM", "price": 100, "minimum": 50}
  ]
}'),

-- 其余渠道
('普B', '港通达', ''),
('普C', '诚意', ''),
('冻K', '林总大闸蟹小龙虾', ''),
('特A', '一号线', ''),
('重货', '锦鑫', ''),
('F线', '思源', ''),
('虎门A', '何总国际集运物流', ''),
('虎门B', '波仔全志物流', ''),
('澳门A', '忠哥鸿发物流', ''),
('澳门B', '张少蔚南屏集运0731201', ''),
('宠物A', '陈橙港澳宠物托运', ''),
('水果A线', '新铭农产品', ''),
('水果B线', '旺农产品物流园', ''),
('广州A线干货', '港庆联', ''),
('广州观赏鱼', '出口观赏鱼', ''),
('广州植物', '山哥花草树木', ''),
('广州运输安装一条龙', 'Lucky长盛物流园', ''),
('香港安装A', '何总', ''),
('香港安装B', '虎门B', ''),
('香港安装C', '淘家装', ''),
('香港安装D', 'Lucky', ''),
('进口小件', '神舟，潘潘', ''),
('进口大件', '搬家群', ''),
('进口大小件', '香港进口回大陆', ''),
('平板特殊车辆包车', '旭平板，港骏', ''),
('柜车包车', '港通达，诚意，重货', '');


-- 报价
-- 广州/深圳 海运 快件报关 - 普货
INSERT INTO t_pricing_rule (
    category_id, channel, transport_method, warehouse, min_consumption,
    unit_price_rules, discount_price, surcharge_fee_rules, delivery_fee_rules,
    delivery_time, packaging_requirement, remark, compensation_policy, status
) VALUES (
    9, '普B', '海运', '广州/深圳仓', '50',
    '[{"range": "0-99999999", "unit_price": 0.6, "prize_type": "KG"}, {"range": "0-99999999", "unit_price": 120, "prize_type": "CBM"}]',
    '', '', '', '', '', '0', '', 1
);

-- 广州/深圳 陆运 快件报关 - 普货
INSERT INTO t_pricing_rule (
    category_id, channel, transport_method, warehouse, min_consumption,
    unit_price_rules, discount_price, surcharge_fee_rules, delivery_fee_rules,
    delivery_time, packaging_requirement, remark, compensation_policy, status
) VALUES (
    9, '普B', '陆运', '广州/深圳仓', '50',
    '[{"range": "0-99999999", "unit_price": 1.5, "prize_type": "KG"}, {"range": "0-99999999", "unit_price": 300, "prize_type": "CBM"}]',
    '', '', '', '', '', '0', '', 1
);

-- 广州 陆运 一般贸易 - 普货
INSERT INTO t_pricing_rule (
    category_id, channel, transport_method, warehouse, min_consumption,
    unit_price_rules, discount_price, surcharge_fee_rules, delivery_fee_rules,
    delivery_time, packaging_requirement, remark, compensation_policy, status
) VALUES (
    9, '普B', '陆运', '广州仓', '50',
    '[{"range": "0-99999999", "unit_price": 1.2, "prize_type": "KG"}, {"range": "0-99999999", "unit_price": 240, "prize_type": "CBM"}]',
    '', '', '', '', '', '大陆关200/票', '', 1
);

-- 深圳 陆运 一般贸易 - 普货
INSERT INTO t_pricing_rule (
    category_id, channel, transport_method, warehouse, min_consumption,
    unit_price_rules, discount_price, surcharge_fee_rules, delivery_fee_rules,
    delivery_time, packaging_requirement, remark, compensation_policy, status
) VALUES (
    9, '普B', '陆运', '深圳仓', '50',
    '[{"range": "0-99999999", "unit_price": 1.0, "prize_type": "KG"}, {"range": "0-99999999", "unit_price": 200, "prize_type": "CBM"}]',
    '', '', '', '', '', '大陆关200/票', '', 1
);

-- 广州/深圳 海运 快件报关 - 熟食包装食品，化妆品
INSERT INTO t_pricing_rule (
    category_id, channel, transport_method, warehouse, min_consumption,
    unit_price_rules, discount_price, surcharge_fee_rules, delivery_fee_rules,
    delivery_time, packaging_requirement, remark, compensation_policy, status
) VALUES (
    4, '普B', '海运', '广州/深圳仓', '50',
    '[{"range": "0-99999999", "unit_price": 1.5, "prize_type": "KG"}, {"range": "0-99999999", "unit_price": 300, "prize_type": "CBM"}]',
    '', '', '', '', '', '0', '', 1
);

-- 广州/深圳 海运 快件报关 - 防疫物资
INSERT INTO t_pricing_rule (
    category_id, channel, transport_method, warehouse, min_consumption,
    unit_price_rules, discount_price, surcharge_fee_rules, delivery_fee_rules,
    delivery_time, packaging_requirement, remark, compensation_policy, status
) VALUES (
    12, '普B', '海运', '广州/深圳仓', '50',
    '[{"range": "0-99999999", "unit_price": 2.0, "prize_type": "KG"}, {"range": "0-99999999", "unit_price": 400, "prize_type": "CBM"}]',
    '', '', '', '', '', '0', '', 1
);


-- 普C
INSERT INTO t_pricing_rule (
    category_id, channel, transport_method, warehouse, min_consumption,
    unit_price_rules, discount_price, surcharge_fee_rules, delivery_fee_rules,
    delivery_time, packaging_requirement, remark, compensation_policy, status
) VALUES (
    9, '普C', '陆运', '深圳/东莞仓', '80',
    '[{"range": "0-99999999", "unit_price": 0.5, "prize_type": "KG"}, {"range": "0-99999999", "unit_price": 100, "prize_type": "CBM"}]',
    '', '', '', '', '', '普货最低消费80元/票', '', 1
);

INSERT INTO t_pricing_rule (
    category_id, channel, transport_method, warehouse, min_consumption,
    unit_price_rules, discount_price, surcharge_fee_rules, delivery_fee_rules,
    delivery_time, packaging_requirement, remark, compensation_policy, status
) VALUES (
    9, '普C', '陆运', '广州仓', '80',
    '[{"range": "0-99999999", "unit_price": 2, "prize_type": "KG"}, {"range": "0-99999999", "unit_price": 350, "prize_type": "CBM"}]',
    '', '', '', '', '', '普货最低消费80元/票', '', 1
);

INSERT INTO t_pricing_rule (
    category_id, channel, transport_method, warehouse, min_consumption,
    unit_price_rules, discount_price, surcharge_fee_rules, delivery_fee_rules,
    delivery_time, packaging_requirement, remark, compensation_policy, status
) VALUES (
    8, '普C', '陆运', '深圳/东莞仓', '80',
    '[{"range": "0-99999999", "unit_price": 0.6, "prize_type": "KG"}, {"range": "0-99999999", "unit_price": 125, "prize_type": "CBM"}]',
    '', '', '', '', '', '家私或其他最低消费80元/票', '', 1
);


INSERT INTO t_pricing_rule (
    category_id, channel, transport_method, warehouse, min_consumption,
    unit_price_rules, discount_price, surcharge_fee_rules, delivery_fee_rules,
    delivery_time, packaging_requirement, remark, compensation_policy, status
) VALUES (
    4, '普C', '陆运', '深圳/东莞仓', '80',
    '[{"range": "0-99999999", "unit_price": 1.2, "prize_type": "KG"}, {"range": "0-99999999", "unit_price": 220, "prize_type": "CBM"}]',
    '', '', '', '', '', '食品最低消费80元/票', '', 1
);
