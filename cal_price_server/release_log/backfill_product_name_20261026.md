# 未知产品首批回填操作单（20261026）

本批只回填当前仍为空的 `t_performance_statement.product_name`，不改动其他业务字段。

## 执行范围

- 总行数：1940
- 规则识别：1066
- LLM 识别：874（置信度 ≥ 0.90）
- 分类分布：冻品 47、普货 489、水产海鲜 311、水果 106、熟食 228、生鲜肉类 302、酒类 139、食品 318
- 映射 SHA256：`2040673eaaf4a70560669e468405646711e1c1c88f4f2042217a9ed8128cc3be`

## 执行顺序

1. 对 `db_prize_cal` 做一次完整逻辑备份并记录 SHA256。
2. 执行迁移 SQL。脚本会先在会话临时表中校验全部目标，再创建计划表和完整行备份表；任何目标记录已被填写时都会主动终止。
3. 执行只读验收 SQL，三个总数检查都应等于 1940。
4. 打开经营分析页面，确认“未知产品”票数下降、分类排名合理、毛利润总额不变。
5. 若结果不符合预期，执行回滚 SQL，再执行只读验收 SQL确认 `matching_rows` 为 0。
6. 计划表和备份表暂不删除；稳定观察后另行审批清理。

## 待确认后执行的命令

以下命令目前仅作为操作清单，尚未执行：

```bash
mkdir -p /Users/hc/Desktop/code/data_backup/mysql/2026-10-26
docker exec mysql_db sh -c 'exec mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" --single-transaction --routines --triggers db_prize_cal' > /Users/hc/Desktop/code/data_backup/mysql/2026-10-26/db_prize_cal_before_product_backfill.sql
shasum -a 256 /Users/hc/Desktop/code/data_backup/mysql/2026-10-26/db_prize_cal_before_product_backfill.sql

docker exec -i mysql_db sh -c 'exec mysql -uroot -p"$MYSQL_ROOT_PASSWORD"' < cal_price_server/release_log/backfill_product_name_20261026.sql
docker exec -i mysql_db sh -c 'exec mysql -uroot -p"$MYSQL_ROOT_PASSWORD"' < cal_price_server/release_log/check_product_name_20261026.sql
```

需要回滚时：

```bash
docker exec -i mysql_db sh -c 'exec mysql -uroot -p"$MYSQL_ROOT_PASSWORD"' < cal_price_server/release_log/rollback_product_name_20261026.sql
docker exec -i mysql_db sh -c 'exec mysql -uroot -p"$MYSQL_ROOT_PASSWORD"' < cal_price_server/release_log/check_product_name_20261026.sql
```

## 文件

- `backfill_product_name_20261026.sql`：备份、前置断言、事务更新、结果摘要。
- `check_product_name_20261026.sql`：只读验收。
- `rollback_product_name_20261026.sql`：恢复原产品名和原更新时间。

## 测试矩阵

| 场景 | 预期结果 |
| --- | --- |
| 正常首次执行 | 精确更新 1940 行并提交 |
| 任一目标 ID 不存在 | 更新前终止 |
| 任一目标产品名已被人工/同步填写 | 更新前终止，避免覆盖 |
| 计划表或备份表已有数据 | 更新前终止，避免误重跑 |
| 更新行数不是 1940 | 事务回滚 |
| 同步源后续仍为空 | 保留本次回填值，不被清空 |
| 执行回滚 | 只恢复产品名和原更新时间，其他字段保持不变 |
| 经营分析复核 | 总收入、总成本、总毛利润不变，仅产品分组发生迁移 |
