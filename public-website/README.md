# 大哥物流官网（本地验收）

本地启动：

```bash
docker compose -f docker-compose.local.yml up -d
```

访问地址：

- 官网首页：<http://localhost:4174/>
- 隐私政策：<http://localhost:4174/privacy/>
- 服务条款：<http://localhost:4174/terms/>
- 数据删除：<http://localhost:4174/data-deletion/>

本地 Nginx 只代理官网所需的分类、公开地区和报价接口，其他计费管理接口返回 404。
官网与 `localhost/cal_static` 管理端互不覆盖。

停止：

```bash
docker compose -f docker-compose.local.yml down
```
