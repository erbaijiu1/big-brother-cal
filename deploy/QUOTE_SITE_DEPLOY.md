# 报价官网部署说明

## 静态包

在 `uniapp-cal-price` 目录执行：

```bash
npm run build:h5:public
```

输出目录为 `uniapp-cal-price/dist/build/h5-public/`。把该目录内的全部文件上传到线上
`/var/www/hk-logistics-quote/`，不要额外套一层 `h5` 目录。

官网构建和本地管理端构建使用不同输出目录，不会覆盖本地 Nginx 使用的
`uniapp-cal-price/dist/build/h5/`。

该构建按域名根目录 `/` 生成资源地址，页面会调用同域的 `/cal_price/...` 接口，
因此不需要在前端写死服务器 IP 或域名，也不会产生跨域问题。

## Nginx

复制 `deploy/nginx/quote-site.conf.example` 到线上 Nginx 配置目录并修改：

1. `server_name` 改成实际报价域名。
2. `root` 改成实际静态文件目录。
3. 后端在宿主机监听 8088 时保留 `127.0.0.1:8088`；Nginx 和后端在同一 Docker
   网络时改成 `cal_price_server:8088`。
4. 配好 HTTPS 证书后，将 HTTP 请求 301 跳转到 HTTPS。

配置仅公开报价页使用的三个接口：

- `POST /cal_price/classify/classify_list`
- `GET /cal_price/districts/`
- `POST /cal_price/pricing_rule/min_pricing`

其他 `/cal_price/` 管理接口会返回 404。

## 上线检查

```bash
nginx -t
systemctl reload nginx
curl -I https://实际域名/
curl -sS https://实际域名/cal_price/districts/
```

浏览器打开报价域名后，检查分类、地区可以加载，并完成一次实际报价。
