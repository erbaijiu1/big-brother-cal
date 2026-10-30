# 深圳市大哥物流有限公司官网生产部署说明

本文档供线上服务器上的 Codex 或运维人员执行。部署前先检查服务器现状并备份，
不要直接覆盖未知的线上配置。

## 1. 部署目标

- 主站地址：`https://www.yjhcai.cn/`
- `https://yjhcai.cn/` 永久跳转到 `https://www.yjhcai.cn/`
- 官网首页直接部署在域名根路径 `/`
- 不部署到 `/quote/`、`/cal_static/` 等子路径
- 官网无需登录，公开展示企业资料、物流业务、联系方式、报价、隐私政策和服务条款
- 原管理端是独立系统，不得用管理端静态包覆盖官网首页

官网源文件位于 `public-website/`。这是可直接发布的静态站点，**不需要执行 npm build**。
旧的 `uniapp-cal-price/dist/...` 不是本次官网发布物。

## 2. 发布目录

建议线上目录：

```text
/var/www/yjhcai.cn/
├── index.html
├── assets/
├── privacy/
├── terms/
├── data-deletion/
├── robots.txt
└── sitemap.xml
```

从仓库同步 `public-website/` 的站点文件，排除仅供本地测试的文件：

```bash
sudo mkdir -p /var/www/yjhcai.cn
sudo rsync -av --delete \
  --exclude docker-compose.local.yml \
  --exclude nginx.local.conf \
  --exclude README.md \
  public-website/ /var/www/yjhcai.cn/
```

执行 `--delete` 前，必须确认目标路径精确为 `/var/www/yjhcai.cn/`，并已备份旧站点。

## 3. 后端要求

官网采用同域接口，不在前端写死服务器 IP：

- `POST /cal_price/classify/classify_list`：读取货物分类
- `GET /cal_price/public/districts`：读取公开地区列表
- `POST /cal_price/pricing_rule/min_pricing`：计算报价

本次代码新增了 `cal_price_server/api/public_quote_api.py`，并在
`cal_price_server/main.py` 注册公开地区接口。线上拉取新代码后，需要按现有部署方式重建或
重启 `cal_price_server`，确保新路由生效。

不要取消旧管理接口 `/cal_price/districts/` 的登录校验；官网只使用新的只读接口
`/cal_price/public/districts`。

后端位于宿主机时，Nginx upstream 通常使用 `127.0.0.1:8088`。如果 Nginx 和后端都在
Docker 中，需让两者加入同一网络，并将 upstream 改为 `cal_price_server:8088`。

## 4. Nginx 与 HTTPS

生产模板：`deploy/nginx/yjhcai.cn.conf.example`

执行前确认：

1. `yjhcai.cn` 和 `www.yjhcai.cn` 的 DNS 已指向当前服务器。
2. 静态目录确实是 `/var/www/yjhcai.cn/`。
3. 后端 upstream 地址能从 Nginx 所在环境访问。
4. HTTPS 证书覆盖 `yjhcai.cn` 和 `www.yjhcai.cn`。
5. 服务器已有其他站点时，不覆盖其配置文件。

可将模板复制成独立站点配置，再按服务器发行版启用：

```bash
sudo cp deploy/nginx/yjhcai.cn.conf.example /etc/nginx/conf.d/yjhcai.cn.conf
sudo nginx -t
sudo systemctl reload nginx
```

如果尚无证书，可先保留仅用于 ACME 验证的 HTTP 配置，再按服务器现有证书方案申请。
使用 Certbot 时可参考：

```bash
sudo certbot certonly --webroot -w /var/www/certbot \
  -d yjhcai.cn -d www.yjhcai.cn
```

证书路径与模板不一致时，以服务器实际路径为准。不得在证书未生成时直接启用 443 配置。

## 5. 上线验证

先检查配置并重新加载：

```bash
sudo nginx -t
sudo systemctl reload nginx
```

再执行接口和页面冒烟测试：

```bash
curl -I http://yjhcai.cn/
curl -I https://yjhcai.cn/
curl -I https://www.yjhcai.cn/
curl -I https://www.yjhcai.cn/privacy/
curl -fsS https://www.yjhcai.cn/cal_price/public/districts
curl -fsS -X POST https://www.yjhcai.cn/cal_price/classify/classify_list \
  -H 'Content-Type: application/json' -d '{}'
```

浏览器还需人工确认：

- 访问 `/` 直接看到官网首页，无需登录
- 公司名称、地址、电话、WhatsApp、邮箱和统一社会信用代码正确
- 分类和地区下拉框能加载，并能完成一次实际报价
- `/privacy/`、`/terms/`、`/data-deletion/` 均能访问
- 手机端布局正常，电话、WhatsApp、邮箱和二维码可用
- `yjhcai.cn` 能跳转到 `www.yjhcai.cn`
- 未列入白名单的 `/cal_price/` 管理接口不能经官网域名访问

## 6. 安全边界

官网域名只反向代理上述三个报价接口，其他 `/cal_price/` 请求统一返回 404。
管理端建议使用独立域名并增加登录、VPN 或 IP 白名单，不要挂在公开官网首页下。

## 7. 回滚

部署前保存：

- 原网站目录备份
- 原 Nginx 站点配置备份
- 当前运行的后端镜像或版本号

如页面或接口验证失败，恢复旧静态目录和旧 Nginx 配置，执行 `nginx -t` 成功后再 reload，
并按原版本恢复后端。不要在验证失败时继续修改 DNS。
