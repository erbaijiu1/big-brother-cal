ALTER TABLE t_channel_config
    ADD COLUMN customer_quote_config TEXT NULL COMMENT '对客报价展示配置 JSON' AFTER receiving_address,
    ADD COLUMN config_updated_at DATETIME NULL DEFAULT CURRENT_TIMESTAMP COMMENT '对客配置更新时间' AFTER customer_quote_config;

CREATE TABLE t_channel_quote_config_history (
    id INT NOT NULL AUTO_INCREMENT COMMENT '主键',
    channel_id INT NOT NULL COMMENT '渠道ID',
    channel_code VARCHAR(20) NOT NULL COMMENT '渠道编码快照',
    config_snapshot TEXT NOT NULL COMMENT '对客报价配置快照 JSON',
    changed_by_id INT NULL COMMENT '操作管理员ID',
    changed_by_name VARCHAR(50) NULL COMMENT '操作管理员账号',
    changed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '变更时间',
    PRIMARY KEY (id),
    KEY idx_channel_quote_config_history_channel_id (channel_id),
    CONSTRAINT fk_channel_quote_config_history_channel
        FOREIGN KEY (channel_id) REFERENCES t_channel_config(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='渠道对客报价配置历史';
