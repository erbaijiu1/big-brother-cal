# 获客品类高置信回填操作单（20261026_v1）

## 执行范围

- 目标库：本地 `db_prize_cal`
- 目标表：`t_performance_statement`
- 修改字段：`product_name`、`updated_at`
- 映射品名：2587
- 预计更新：7390 行
- 最低置信度：0.90
- 映射 SHA256：`7687f071893e716f963c492b1d4a6ffc1bf61a75aca9e3674bd42396b7e1240f`
- UNKNOWN 与低置信度品名不更新

## 已完成完整备份

- 文件：`/Users/hc/Desktop/code/data_backup/mysql/2026-10-26/db_prize_cal_before_acquisition_category_backfill.sql`
- 大小：172 MB
- 完成时间：2026-10-26 13:35:16
- SHA-256：`f0ff3cb27759183a2e060e532a00e513d985db3ba3ca094a94975df8fe3021ab`
- `mysqldump` 尾部包含正常完成标志。

- 冻品：68 个品名，278 票
- 普货：1160 个品名，1941 票
- 水产海鲜：153 个品名，655 票
- 水果：91 个品名，548 票
- 熟食：223 个品名，1077 票
- 生鲜肉类：378 个品名，1639 票
- 酒类：30 个品名，188 票
- 食品：484 个品名，1064 票

## SQL 分类

- `apply`：包含 DDL、INSERT、UPDATE 和存储过程调用，会修改数据库。
- `check`：只读 SELECT，可在回填后直接执行。
- `rollback`：包含 UPDATE 和存储过程调用，仅在需要回滚且再次确认后执行。

## 执行顺序

1. 确认完整逻辑备份 SHA-256。
2. 执行 apply SQL；前置断言必须确认 2,587 个品名、7,390 票均未变化。
3. 执行 check SQL；三个计数应分别为 2,587、7,390、7,390。
4. 对账总收入、总成本和总毛利润不变。
5. 页面检查候选品类与 UNKNOWN/待归一变化。
6. 结果异常时，单独确认后执行 rollback SQL。

## 待批准执行命令

```bash
docker exec -i mysql_db sh -c 'exec mysql -uroot -p"$MYSQL_ROOT_PASSWORD"' < cal_price_server/release_log/acquisition_category_backfill_20261026_v1.sql
docker exec -i mysql_db sh -c 'exec mysql -uroot -p"$MYSQL_ROOT_PASSWORD"' < cal_price_server/release_log/acquisition_category_backfill_20261026_v1_check.sql
```

回滚 SQL 不会自动执行；若验收异常，需再次确认：

```bash
docker exec -i mysql_db sh -c 'exec mysql -uroot -p"$MYSQL_ROOT_PASSWORD"' < cal_price_server/release_log/acquisition_category_backfill_20261026_v1_rollback.sql
```

## 执行前只读预检

- 当前映射品名：2,587 / 2,587
- 当前匹配订单：7,390 / 7,390
- 品名票数不一致：0
- 同名迁移表：不存在
- 回填范围收入基线：¥8,933,898.12
- 回填范围成本基线：¥5,821,896.98
- 回填范围可报告毛利润：¥3,057,793.68
- 回填范围缺成本：86票
- 预检状态：`ready=true`

## 执行结果（2026-10-26）

- apply SQL：已执行成功
- 计划表：2,587 / 2,587
- 行级备份：7,390 / 7,390
- 已归一订单：7,390 / 7,390
- 剩余非规范品名：356 个、1,179 票
- 剩余非规范品名可报告毛利润：¥336,031.09
- 回填范围收入：备份与当前均为 ¥8,933,898.12
- 回填范围成本：备份与当前均为 ¥5,821,896.98
- 回滚 SQL：未执行，保留备用
- 计划表和行级备份表：保留，未清理

最近180天页面复核：

- 订单 4,893、收入 ¥5,447,627.49、毛利润 ¥1,739,409.63、毛利率 32.52%，与经营看板一致。
- 待归一 626 票，未知 263 票，未归一利润占比 12.65%。
- 客户识别覆盖率 97.22%，利润订单覆盖率 98.08%。
