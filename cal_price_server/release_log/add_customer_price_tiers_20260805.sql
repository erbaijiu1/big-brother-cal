ALTER TABLE t_goods_classification
    ADD COLUMN customer_price_tiers TEXT NULL COMMENT '对客阶梯价 JSON' AFTER priority,
    ADD COLUMN price_tiers_updated_at DATETIME NULL DEFAULT CURRENT_TIMESTAMP COMMENT '对客阶梯价更新时间' AFTER customer_price_tiers;

CREATE TABLE t_goods_price_tier_history (
    id INT NOT NULL AUTO_INCREMENT,
    category_id INT NOT NULL,
    main_category VARCHAR(50) NOT NULL,
    config_snapshot TEXT NOT NULL,
    changed_by_id INT NULL,
    changed_by_name VARCHAR(50) NULL,
    changed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_goods_price_tier_history_category (category_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='货物分类对客阶梯价配置历史';

UPDATE t_goods_classification
SET customer_price_tiers = '[{"min_quantity":1,"max_quantity":100,"min_price":12,"max_price":15,"unit":"kg"},{"min_quantity":101,"max_quantity":500,"min_price":11,"max_price":13,"unit":"kg"},{"min_quantity":501,"max_quantity":1000,"min_price":11,"max_price":12,"unit":"kg"},{"min_quantity":1001,"max_quantity":null,"min_price":10.5,"max_price":12,"unit":"kg"}]',
    price_tiers_updated_at = NOW()
WHERE category_id = 1;

UPDATE t_goods_classification
SET customer_price_tiers = '[{"min_quantity":1,"max_quantity":100,"min_price":7,"max_price":9,"unit":"kg"},{"min_quantity":101,"max_quantity":500,"min_price":6,"max_price":8,"unit":"kg"},{"min_quantity":501,"max_quantity":1000,"min_price":5.5,"max_price":7,"unit":"kg"},{"min_quantity":1001,"max_quantity":null,"min_price":5,"max_price":6.5,"unit":"kg"}]',
    price_tiers_updated_at = NOW()
WHERE category_id = 2;

UPDATE t_goods_classification
SET customer_price_tiers = '[{"min_quantity":1,"max_quantity":1000,"min_price":1.5,"max_price":2.5,"unit":"kg"},{"min_quantity":1001,"max_quantity":3000,"min_price":1.3,"max_price":2,"unit":"kg"},{"min_quantity":3001,"max_quantity":null,"min_price":1.2,"max_price":1.8,"unit":"kg"}]',
    price_tiers_updated_at = NOW()
WHERE category_id IN (4, 11, 12, 18);

UPDATE t_goods_classification
SET customer_price_tiers = '[{"min_quantity":1,"max_quantity":1000,"min_price":1,"max_price":2,"unit":"kg"},{"min_quantity":1001,"max_quantity":3000,"min_price":1,"max_price":1.8,"unit":"kg"},{"min_quantity":3001,"max_quantity":null,"min_price":0.8,"max_price":1.5,"unit":"kg"}]',
    price_tiers_updated_at = NOW()
WHERE category_id = 9;

INSERT INTO t_goods_price_tier_history
    (category_id, main_category, config_snapshot, changed_by_name)
SELECT category_id, main_category, customer_price_tiers, 'migration-20260805'
FROM t_goods_classification
WHERE customer_price_tiers IS NOT NULL AND customer_price_tiers <> '';
