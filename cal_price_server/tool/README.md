# 旧系统数据导入工具

`get_all_trade_info.py` 从旧物流系统读取托运排单或业绩数据，逐页导出 CSV，并可选择写入 `db_prize_cal`。

## 安全默认值

- `DRY_RUN=1`：默认只抓取、解析和导出 CSV，不写数据库。
- `EXPORT_CSV` 默认跟随运行模式：预览时开启，正式入库时关闭。
- `ENABLE_AUTO_PAGING=0`：默认只处理一页。
- `PRINT_RESPONSE=0`：默认不在终端打印整页业务数据。
- `PHPSESSID` 必须通过环境变量提供，代码中不保存登录凭证。

CSV 和断点文件默认保存在 `tool/output/`。Docker Compose 已将该目录挂载到宿主机。
预览模式不会读取或更新正式入库 checkpoint，因此预览后切换正式入库不会跳页。

## 环境变量

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `PHPSESSID` | 无 | 必填，旧系统登录会话 Cookie |
| `LEGACY_SYSTEM_BASE_URL` | `https://gzjsjy.s1.office7x.cn` | 旧系统域名，自动用于 Origin 和 Referer |
| `LEGACY_SYSTEM_URL` | `<LEGACY_SYSTEM_BASE_URL>/SOA/WorkSpace.phtml` | 数据接口地址 |
| `LEGACY_DS_CODE` | 按数据集选择 | 可选，覆盖当前数据集的旧系统数据源编码 |
| `LEGACY_GROUP_ID` | 按数据集选择 | 可选，覆盖当前数据集的分组编码 |
| `LEGACY_VERIFY_TLS` | `1` | 是否校验 HTTPS 证书 |
| `DATASET_TYPE` | `consignment` | `consignment` 或 `performance` |
| `DRY_RUN` | `1` | `1` 只导出，`0` 写数据库 |
| `EXPORT_CSV` | 预览为 `1`，入库为 `0` | 是否导出每页 CSV，可显式覆盖 |
| `START_PAGE` | `1` | 起始页 |
| `PAGE_ROWS` | `14` | 每页条数，与当前网页请求一致 |
| `ENABLE_AUTO_PAGING` | `0` | 是否连续翻页 |
| `AUTO_MAX_PAGES` | `0` | 最大处理页数，`0` 不限制 |
| `AUTO_RESUME` | `1` | 正式入库时是否从 checkpoint 继续 |
| `AUTO_INTERVAL_SECONDS` | `0.2` | 页间等待秒数 |
| `INGEST_OUTPUT_DIR` | `tool/output` | CSV 与 checkpoint 输出目录 |
| `PRINT_RESPONSE` | `0` | 是否打印解码后的整页响应 |

数据库连接继续使用项目已有的 `DB_HOST`、`DB_PORT`、`DB_USER`、`DB_PASSWORD`、`DB_NAME`。

## 推荐执行顺序

以下命令在 `/app` 目录执行。

### 1. 单页预览

```bash
PHPSESSID='<登录 Cookie>' \
DATASET_TYPE=consignment \
DRY_RUN=1 \
python tool/get_all_trade_info.py
```

### 2. 预览两页

```bash
PHPSESSID='<登录 Cookie>' \
DATASET_TYPE=consignment \
DRY_RUN=1 \
ENABLE_AUTO_PAGING=1 \
AUTO_MAX_PAGES=2 \
AUTO_RESUME=0 \
python tool/get_all_trade_info.py
```

### 3. 确认 CSV 后正式入库

```bash
PHPSESSID='<登录 Cookie>' \
DATASET_TYPE=consignment \
DRY_RUN=0 \
ENABLE_AUTO_PAGING=1 \
AUTO_MAX_PAGES=0 \
AUTO_RESUME=1 \
python tool/get_all_trade_info.py
```

将 `DATASET_TYPE` 改成 `performance` 可导入业绩明细。

工具会按数据集自动使用网页当前的请求参数：

- `consignment`：`dsCode=T0020142`、`GroupID=`
- `performance`：`dsCode=T00200DE`、`GroupID=-1:0`

## Docker 执行

镜像重新构建后，可以在现有服务容器中执行：

```bash
docker exec \
  -e PHPSESSID='<登录 Cookie>' \
  -e DATASET_TYPE=consignment \
  -e DRY_RUN=1 \
  cal_price_server \
  python tool/get_all_trade_info.py
```

正式入库前先检查 `cal_price_server/tool/output/` 中的 CSV。正式入库默认不再生成 CSV。

自动分页默认每页请求 50 条，单次请求超时 30 秒；网络超时、HTTP 429 或服务端错误会自动重试 3 次。
可通过 `PAGE_ROWS`、`REQUEST_TIMEOUT_SECONDS`、`REQUEST_MAX_RETRIES` 和
`REQUEST_RETRY_INTERVAL_SECONDS` 调整。修改 `PAGE_ROWS` 后应从第 1 页重新抓取，不能沿用旧页大小生成的页码断点。

```angular2html
docker exec \
  -e PHPSESSID='2e2582e75253004f60151004a5a90ead' \
  -e LEGACY_VERIFY_TLS=0 \
  -e DATASET_TYPE=performance \
  -e DRY_RUN=0 \
  -e EXPORT_CSV=0 \
  -e ENABLE_AUTO_PAGING=1 \
  -e AUTO_MAX_PAGES=0 \
  -e AUTO_RESUME=0 \
  -e START_PAGE=1 \
  -e PAGE_ROWS=50 \
  -e REQUEST_TIMEOUT_SECONDS=30 \
  -e REQUEST_MAX_RETRIES=3 \
  -e REQUEST_RETRY_INTERVAL_SECONDS=1.5 \
  -e AUTO_INTERVAL_SECONDS=0.2 \
  cal_price_server \
  python tool/get_all_trade_info.py
```
DATASET_TYPE =performance | consignment