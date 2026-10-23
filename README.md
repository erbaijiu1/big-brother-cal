# big-brother-cal

中港物流成本价、计价规则和货物分类管理服务。

## 本地管理后台

先确保 `cal_price_server` 已通过统一环境启动：

```bash
cd /Users/hc/Desktop/code/local_dev_env
docker compose up -d cal_price_server
```

管理前端是独立的 H5 开发服务，需要另外启动：

```bash
cd /Users/hc/Desktop/code/toCom/big-brother-cal/uniapp-cal-price
npm run dev:h5 -- --host 0.0.0.0
```

常用页面：

- 登录页：<http://localhost:5173/cal_static/#/pages/login/index>
- 管理首页：<http://localhost:5173/cal_static/#/pages/admin/index>
- 计价规则：<http://localhost:5173/cal_static/#/pages/admin/pricing_mgr/index>
- 分类管理：<http://localhost:5173/cal_static/#/pages/admin/classify_mgr/index>
- 渠道管理：<http://localhost:5173/cal_static/#/pages/admin/channel/index>
- 渠道成本计算：<http://localhost:5173/cal_static/#/pages/admin/pricing_cal/index>

成本报价更新后重点检查：

1. 在“计价规则”确认目标渠道和分类的 KG、CBM、派送费及阶梯边界。
2. 在“分类管理”确认分类示例；例如分类 14“蔬菜水果”应包含“芒果”。
3. 前端请求后端地址来自 `.env.h5dev`，本地默认是 `http://localhost:8088`。

管理后台需要使用已有后台账号登录。不要把账号或密码写入 README。
