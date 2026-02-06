# 咔咔记账（Kona）

个人资产与投资管理系统。

- 前端：Flutter（Android / iOS / macOS / Web）
- 后端：Python Flask
- 数据库：SQLite（`portfolio.db`）
- 部署：GitHub Actions + AWS EC2

本 README 目标：让你或新同事在新电脑上，按文档即可完整接手开发、部署和运维。

---

## 1. 当前状态（重要）

- 代码主分支：`main`
- 仓库根目录：`/Users/kona/Desktop/ko/kona_repo`
- 后端目录：`/Users/kona/Desktop/ko/kona_repo/kona_tool`
- 前端目录：`/Users/kona/Desktop/ko/kona_repo/flutter`
- 线上后端（AWS）：通过 `systemd` 管理主服务，支持异常自动重启
- 每日快照：使用 `systemd timer` 定时触发（北京 07:00）
- 旧版前端 `HI`：已归档到 `archive/HI`，不参与运行

---

## 2. 项目结构与每个目录用途

```text
kona_repo/
├─ .github/workflows/            # GitHub Actions 自动部署工作流
├─ archive/                      # 已归档历史代码（当前不运行）
│  └─ HI/
├─ docs/                         # 项目文档（接口、部署、运行、维护）
├─ flutter/                      # Flutter 前端
│  ├─ lib/
│  │  ├─ config/                 # API 地址、主题、常量配置
│  │  ├─ models/                 # 数据模型
│  │  ├─ pages/                  # 页面（首页/投资/分析/快讯/我的/登录）
│  │  ├─ providers/              # 状态管理（缓存 + SWR + 用户信息）
│  │  ├─ services/               # API 调用层
│  │  └─ widgets/                # 弹窗、复用组件
│  └─ android/ios/macos/web/...  # 多端工程
├─ kona_tool/                    # Flask 后端
│  ├─ app.py                     # API 入口
│  ├─ config.py                  # 后端配置
│  ├─ core/                      # 业务模块（认证、价格、新闻、快照、DB）
│  ├─ migrations/                # 数据迁移脚本
│  ├─ scripts/                   # 运维脚本（每日快照）
│  ├─ tests/                     # 基础测试
│  ├─ templates/                 # Web 页模板（后端自带页面）
│  ├─ .env.example               # 环境变量模板
│  └─ requirements.txt
├─ scripts/                      # 文档自动生成脚本
└─ README.md
```

---

## 3. 已完成改动总览（按模块）

以下是近阶段核心改动（已在代码中）：

### 3.1 数据加载与体验

- 前端实现 SWR（先显示缓存，再后台刷新）
- 页面切换不再反复清空、重载
- 下拉刷新替代手动刷新
- 实时价格自动轮询（30s）

### 3.2 投资页（持仓）

- 列布局与小屏适配优化
- 分类标签布局、间距和字号优化
- 持仓列表文本字号整体调优
- 资产名称截断策略优化（中英文处理）
- 当日盈亏列展示优化（人民币归一显示）

### 3.3 分析页

- 日历、排行、摘要卡样式升级
- 当日盈亏与实时价格逻辑打通
- 隐藏金额模式支持到分析页关键金额区域（收益率保留）
- 月/年/全部改为快照口径，避免实时跳动误导

### 3.4 主题系统

- 新增浅色/暗黑主题切换（在“我的页面”）
- 修复切换主题后底部栏与快讯卡片不同步问题
- 各页面主题跟随统一修复

### 3.5 快讯页

- 重要快讯筛选开关
- 单条快讯折叠/展开
- 分页加载（每页 30 条，滚动加载更多）

### 3.6 认证与用户资料

- 邮箱验证码登录（SMTP）
- 支持测试账号免验证码白名单（`LOGIN_BYPASS_EMAILS`）
- 用户资料接口扩展：昵称、手机号、注册方式、头像
- 头像上传/存储修复
- 登录响应去除头像大字段，改为登录后单独拉取 `me/profile`

### 3.7 快照与统计口径

- 支持按用户写入每日快照
- 关闭后端“启动即快照”和“后台循环快照”开关（避免重复）
- 改为定时任务固定时间打点（更稳定）

### 3.8 运维稳定性

- 后端服务改为 `systemd` 托管（自动拉起）
- 每日快照改为 `systemd timer`
- 继续保留 GitHub Actions 自动部署

---

## 4. 前端说明（Flutter）

### 4.1 前端是什么

- 一个统一 App，包含：首页、投资、分析、快讯、我的、登录
- 支持深色/浅色主题
- 支持头像与昵称修改

### 4.2 本地运行

```bash
cd /Users/kona/Desktop/ko/kona_repo/flutter
flutter pub get
flutter run
```

### 4.3 常用构建与安装

```bash
# 生成 Android debug 包
flutter build apk --debug

# 生成 Android release 包
flutter build apk --release

# USB 安装到指定设备
flutter install -d <device_id> --debug
```

### 4.4 API 地址配置

文件：`/Users/kona/Desktop/ko/kona_repo/flutter/lib/config/api_config.dart`

- 本地调试：`http://127.0.0.1:5003`
- 线上联调：`http://<EC2公网IP>:5003`

---

## 5. 后端说明（Flask）

### 5.1 后端是什么

- 提供资产、交易、分析、新闻、认证、快照等 API
- 当前以 SQLite 为主存储

### 5.2 本地运行

```bash
cd /Users/kona/Desktop/ko/kona_repo/kona_tool
pip3 install -r requirements.txt
python3 app.py
```

默认端口：`5003`

### 5.3 关键环境变量

参考模板：`/Users/kona/Desktop/ko/kona_repo/kona_tool/.env.example`

当前代码支持（重要项）：

- `JWT_SECRET`
- `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASS`
- `SMTP_FROM` / `SMTP_FROM_NAME` / `SMTP_USE_TLS`
- `LOGIN_BYPASS_EMAILS`
- `ENABLE_BACKGROUND_SNAPSHOT`（建议 `false`）
- `ENABLE_STARTUP_SNAPSHOT`（建议 `false`）
- `KONA_DATABASE_PATH`（可选）

---

## 6. 数据库结构（当前核心表）

数据库文件：`/home/ec2-user/portfolio/kona_tool/portfolio.db`（线上）

### 6.1 users

- `id`（用户 UUID）
- `email`
- `nickname`
- `register_method`
- `phone`
- `avatar`（Base64 文本）
- `user_number`
- `created_at`
- `last_login`

### 6.2 portfolio（持仓）

- `code`, `name`
- `qty`, `price`
- `currency`
- `adjustment`（手动校准项）
- `asset_type`（如 `a/us/hk/fund`）
- `user_id`

### 6.3 transactions（交易）

- 买入/卖出流水
- 价格、数量、成交金额、盈亏
- `user_id`

### 6.4 daily_snapshots（快照）

- `date`
- `total_asset`
- `day_pnl`
- `total_pnl`
- `user_id`
- `updated_at`

---

## 7. 部署说明（GitHub + AWS）

### 7.1 自动部署（代码发布）

工作流文件：`/Users/kona/Desktop/ko/kona_repo/.github/workflows/deploy.yml`

触发方式：

- push 到 `main`
- 手动触发 `workflow_dispatch`

流程：

1. SSH 登录 AWS
2. `git pull`
3. 安装依赖
4. 重启后端
5. 健康检查 `/api/rates`

### 7.2 生产运行（服务托管）

推荐用 `systemd`（已在线上启用）：

- 主服务：`kona.service`
- 每日快照：`kona-snapshot.service` + `kona-snapshot.timer`

优势：

- 服务异常自动重启
- 开机自启动
- 统一日志

---

## 8. 快照机制（必须理解）

当前推荐口径：

- 实时价格用于“当日显示”
- 月/年/全部收益主要基于 `daily_snapshots`
- 每天固定时间只生成一条当日快照（北京 07:00）

线上定时方式：

- `systemd timer` 在 UTC `23:00` 触发（等价北京 07:00）
- 脚本：`/home/ec2-user/portfolio/kona_tool/scripts/daily_snapshot.sh`

注意：

- 如果同时开启后台快照、启动快照、cron、timer，可能重复写快照
- 推荐仅保留一种“日更快照”机制（当前为 `systemd timer`）

---

## 9. 常用运维命令（AWS）

### 9.1 服务状态

```bash
sudo systemctl status kona -l
sudo journalctl -u kona -n 100
```

### 9.2 重启服务

```bash
sudo systemctl restart kona
```

### 9.3 定时器状态

```bash
sudo systemctl list-timers | grep kona-snapshot
sudo journalctl -u kona-snapshot.service -n 50
```

### 9.4 手动触发快照

```bash
curl -s -X POST http://127.0.0.1:5003/api/snapshot/trigger
```

### 9.5 健康检查

```bash
curl -s http://127.0.0.1:5003/api/rates
```

---

## 10. 登录与邮件（SMTP）

### 10.1 现状

- 已接入 SMTP 验证码发送
- 测试账号可配置免验证码

### 10.2 关键配置

`.env` 示例：

```env
SMTP_HOST=email-smtp.<region>.amazonaws.com
SMTP_PORT=587
SMTP_USER=<smtp_username>
SMTP_PASS=<smtp_password>
SMTP_FROM=<verified_sender_or_domain_mailbox>
SMTP_FROM_NAME=Kaka
SMTP_USE_TLS=true
LOGIN_BYPASS_EMAILS=konaeee@gmail.com
```

### 10.3 接口

- `POST /api/auth/send_code`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/auth/profile`

---

## 11. 文档索引（全部在 docs）

- 结构说明：`/Users/kona/Desktop/ko/kona_repo/docs/STRUCTURE.md`
- 运行手册：`/Users/kona/Desktop/ko/kona_repo/docs/RUNBOOK.md`
- 部署说明：`/Users/kona/Desktop/ko/kona_repo/docs/DEPLOYMENT.md`
- 前端环境：`/Users/kona/Desktop/ko/kona_repo/docs/FRONTEND_SETUP.md`
- API 列表：`/Users/kona/Desktop/ko/kona_repo/docs/API.md`
- API 参数：`/Users/kona/Desktop/ko/kona_repo/docs/API_DETAILS.md`
- OpenAPI：`/Users/kona/Desktop/ko/kona_repo/docs/openapi.yaml`
- Swagger：`/Users/kona/Desktop/ko/kona_repo/docs/swagger-ui.html`
- 导入 Postman/Apifox：`/Users/kona/Desktop/ko/kona_repo/docs/API_IMPORT.md`
- 后端模块说明：`/Users/kona/Desktop/ko/kona_repo/docs/CORE_MODULES.md`
- 运维维护：`/Users/kona/Desktop/ko/kona_repo/docs/MAINTENANCE.md`

---

## 12. 新电脑 15 分钟接手流程

1. 克隆仓库并进入根目录
2. 后端：安装依赖、准备 `.env`、启动
3. 前端：`flutter pub get`、确认 API 地址、运行
4. 打开 App 验证：登录 -> 首页 -> 投资 -> 分析 -> 快讯
5. 如需上线：push 到 `main`，看 Actions 是否绿灯
6. 上 AWS 检查 `kona.service` 与 `kona-snapshot.timer`

---

## 13. 开发与发布建议（团队规范）

- 本地改完先 `flutter run` / API 自测
- 满意后再 `git add -A && git commit && git push`
- 不要把 `.env`、数据库、私钥提交到仓库
- 每次改 API，更新 `docs/API.md` 与 `docs/API_DETAILS.md`
- 涉及统计口径改动，必须记录“实时/快照”来源

---

## 14. 当前已知限制

- 后端仍是 Flask 开发服务器方式启动（非 gunicorn/nginx），适合现阶段、后续可升级
- SQLite 适合当前单机部署，未来多实例需迁移数据库
- 外部行情源会偶发超时（代码已做 fallback）

---

## 15. 结论

当前项目已经具备：

- 可持续开发（前后端分离、文档齐全）
- 可自动部署（GitHub Actions）
- 可稳定运行（systemd 自动重启）
- 可稳定产出统计（定时快照）

如果你后续换电脑或让新成员接手，按本 README + `docs/` 可以完整恢复上下文并继续开发。
