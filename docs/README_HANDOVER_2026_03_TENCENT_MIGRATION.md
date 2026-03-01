# 腾讯云迁移交接（2026-03）

本文用于新接手的 Codex/开发者快速理解当前线上形态、关键配置与排障方法。

---

## 1. 当前线上结论

- 生产公网入口：`http://114.132.238.12`
- 服务器：腾讯云轻量（广州）
- 架构：`Nginx(80) -> Gunicorn(127.0.0.1:5003) -> Flask`
- 限流存储：本机 Redis（`127.0.0.1:6379`）
- 数据库：SQLite（`/opt/kaka/portfolio/kona_tool/portfolio.db`）

---

## 2. 关键路径与文件

- 项目根目录：`/opt/kaka/portfolio`
- 后端目录：`/opt/kaka/portfolio/kona_tool`
- 环境配置：`/opt/kaka/portfolio/kona_tool/.env`
- Gunicorn 服务：`/etc/systemd/system/kona.service`
- Nginx 配置：`/etc/nginx/nginx.conf`
- 服务日志：
  - `journalctl -u kona.service`
  - `journalctl -u nginx`
  - `journalctl -u redis`

---

## 3. systemd 服务状态命令

```bash
sudo systemctl status kona.service --no-pager
sudo systemctl status nginx --no-pager
sudo systemctl status redis --no-pager
```

重启：

```bash
sudo systemctl restart kona.service
sudo systemctl restart nginx
sudo systemctl restart redis
```

开机自启：

```bash
sudo systemctl enable kona.service nginx redis
```

---

## 4. 线上健康检查

公网：

```bash
curl -i http://114.132.238.12/health
curl -i http://114.132.238.12/
```

服务器本机：

```bash
curl -i http://127.0.0.1:5003/health
curl -i http://127.0.0.1/health
redis-cli -h 127.0.0.1 -p 6379 ping
```

期望：
- `/health` 返回 `200`
- Redis 返回 `PONG`

---

## 5. 已踩坑与修复

### 5.1 登录返回 500

现象：
- `POST /api/auth/login` 返回 `500`

根因：
- `.env` 使用 `RATELIMIT_STORAGE_URL=redis://127.0.0.1:6379/0`
- 迁移后 Redis 未安装，Flask-Limiter 连接失败

修复：
- 安装并启用 Redis
- 保持 `.env` 为 `RATELIMIT_STORAGE_URL=redis://127.0.0.1:6379/0`

### 5.2 Nginx 首页显示系统 404

现象：
- 访问 80 端口出现 OpenCloudOS 默认 404 页面

根因：
- 系统默认 server 块抢占 `default_server`

修复：
- 清理冲突配置
- 在 `/etc/nginx/nginx.conf` 保留唯一默认 server，并反向代理到 `127.0.0.1:5003`

---

## 6. 安全与端口策略

- 对外仅开放：`22`（SSH）、`80`（HTTP）
- `5003` 仅本机监听，不对公网开放
- 防火墙中不应长期保留 `5003` 公网入站规则

---

## 7. Flutter 客户端基地址

- 文件：`flutter/lib/config/api_config.dart`
- 当前：`http://114.132.238.12`

对应测试：
- `flutter/test/api_service_web_test.dart`

---

## 8. 回滚预案（最小）

如果新机出现不可恢复故障：

1. 临时恢复旧 AWS 入口（若旧机仍保留且服务可启动）
2. 把客户端基地址切回旧入口并重新发包
3. 排障完成后再切回腾讯云

注意：
- 停 AWS 前需确认无新写入，避免新旧库分叉

---

## 9. 下一步建议

1. 接入域名与 HTTPS（443）
2. 客户端改用域名（避免未来换 IP 再发版）
3. 增加迁移前置检查脚本（Python/Redis/.env/DB）
4. 为 `.env` 建立模板（区分 `prod` 与 `migrate`）
