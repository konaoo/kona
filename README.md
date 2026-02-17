# 咔咔记账（Kona）

个人资产与投资管理系统。

- 前端：Flutter（Android / iOS / macOS / Web）
- 后端：Python Flask
- 数据库：SQLite（`portfolio.db`）
- 部署：GitHub Actions + AWS EC2

本 README 目标：让你或新同事在新电脑上，按文档即可完整接手开发、部署和运维。

---

## 0. 新会话必读（Auth 改造）

- 登录体系已切换到：`用户名 + 密码`（不再依赖邮箱验证码）
- 注册体系已切换到：`用户名 + 密码 + 邀请码`
- 会话策略：`365 天滑动 refresh` + `生物识别退出后重登`
- 后台体系已升级为“全中文运营工作台”（用户/邀请码/接口策略/数据运维/审计）
- 详细设计、字段释义、验收命令请直接看：
  - `/Users/kona/Desktop/kaka/kona_repo/docs/README_AUTH_PERSISTENCE_BIOMETRIC.md`
  - `/Users/kona/Desktop/kaka/kona_repo/docs/README_ADMIN_CONSOLE_V2.md`

---

## 1. 当前状态（重要）

- 代码主分支：`main`
- 仓库根目录：`/Users/kona/Desktop/kaka/kona_repo`
- 后端目录：`/Users/kona/Desktop/kaka/kona_repo/kona_tool`
- 前端目录：`/Users/kona/Desktop/kaka/kona_repo/flutter`
- 线上后端（AWS）：`systemd + gunicorn` 管理，支持异常自动重启
- CI/CD：`main` 分支必须通过后端门禁 + 前端门禁后才允许部署
- 运营后台：已改为全中文、去技术化交互，支持风险确认与操作审计
- 每日快照：使用 `systemd timer` 定时触发（北京 07:00）
- 价格健康监控：`/api/system/price_health` 已上线（用于运维告警）
- 告警体系：服务故障、健康检查失败、快照缺失、价格健康异常均可邮件告警
- 备份恢复：SQLite 每日自动压缩备份 + 一键恢复演练脚本已上线
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

- 登录改为 `username + password`
- 注册改为 `username + password + invite_code`
- 邀请码支持前后端双校验（实时 validate + 注册时强校验）
- `POST /api/auth/send_code` 已下线，返回 `410 Gone`
- 会话采用 access + refresh，refresh 默认 365 天滑动续期
- 生物识别由客户端系统能力实现，服务端不保存生物特征
- 用户资料接口扩展：昵称、手机号、注册方式、头像
- 头像上传/存储修复
- 登录响应去除头像大字段，改为登录后单独拉取 `me/profile`

### 3.7 快照与统计口径

- 支持按用户写入每日快照
- 关闭后端“启动即快照”和“后台循环快照”开关（避免重复）
- 改为定时任务固定时间打点（更稳定）

### 3.8 运维稳定性

- 后端服务改为 `systemd + gunicorn` 托管（自动拉起）
- 每日快照改为 `systemd timer`
- CI 门禁改为“先测试、后部署”

### 3.9 CI/CD 门禁（今天新增）

- GitHub Actions 拆分为三段：`backend-gate`、`frontend-gate`、`deploy`
- `push main` 必须先通过两道门禁，部署才会执行
- `pull_request` 只跑门禁，不部署
- 前端门禁固定包含：`flutter analyze`、`flutter test`、`flutter build web --release`
- `flutter build apk --debug` 改为按路径触发：
  - 仅当本次提交包含 `flutter/android/**` 变更时执行
  - 或手动触发 `workflow_dispatch` 时执行

### 3.10 安全与限流（今天新增）

- 登录/注册/refresh 接口增加限流与安全审计
- 限流后端支持 Redis（生产可横向共享计数）
- 增加安全审计日志：登录失败、注册、邀请码使用、改密、refresh、logout 等
- 强制要求 `JWT_SECRET`（生产）

### 3.11 监控与告警（今天新增）

- 新增运行指标接口：`GET /api/system/price_health`
- 已接入 `kona` 服务失败告警
- 已接入健康检查失败告警
- 已接入快照缺失告警
- 已接入价格健康阈值告警（network_fail/stale_hits/source fail）
- 告警通道使用邮箱（`ALERT_NOTIFY_TO`）

### 3.12 备份与恢复（今天新增）

- 新增 SQLite 自动备份脚本（gzip 压缩）
- 新增每日备份 timer（北京 07:20）
- 新增一键恢复脚本（默认恢复最新备份）
- 恢复前自动生成 `pre_restore` 安全副本
- 已修复恢复脚本跨分区 `Errno 18` 问题（临时文件改为目标目录内创建）

---

## 4. 前端说明（Flutter）

### 4.1 前端是什么

- 一个统一 App，包含：首页、投资、分析、快讯、我的、登录
- 支持深色/浅色主题
- 支持头像与昵称修改

### 4.2 本地运行

```bash
cd /Users/kona/Desktop/kaka/kona_repo/flutter
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

文件：`/Users/kona/Desktop/kaka/kona_repo/flutter/lib/config/api_config.dart`

- 本地调试：`http://127.0.0.1:5003`
- 线上联调：`http://<EC2公网IP>:5003`

### 4.5 Flutter Web（`/app`）接入规则（2026-02-16）

本项目已支持把 Flutter Web 作为主项目 Web 端运行，挂载路径固定为：`/app`

- Web 访问入口：`http://<host>:<port>/app/`
- 后端托管目录：`/Users/kona/Desktop/kaka/kona_repo/kona_tool/static/app`
- Flask 路由：
  - `GET /app`、`GET /app/`
  - `GET /app/<path>`（静态资源 + SPA fallback 到 `index.html`）

API 基址策略（避免影响 App）：

- Web：同源（`Uri.base.origin + /api/...`）
- Android/iOS：继续使用 `ApiConfig.baseUrl`

本地构建与验收：

```bash
cd /Users/kona/Desktop/kaka/kona_repo/flutter
flutter build web --release --base-href /app/

mkdir -p /Users/kona/Desktop/kaka/kona_repo/kona_tool/static/app
rsync -a --delete \
  /Users/kona/Desktop/kaka/kona_repo/flutter/build/web/ \
  /Users/kona/Desktop/kaka/kona_repo/kona_tool/static/app/

cd /Users/kona/Desktop/kaka/kona_repo/kona_tool
JWT_SECRET=local_debug_secret_2026 .venv/bin/python app.py
```

然后在浏览器访问：

- `http://127.0.0.1:5003/app/`（若本机端口被占用，以启动日志端口为准）

### 4.6 Web 端近期改动（2026-02）

为保证 Web 与 App 行为一致，已落地以下修复：

1. 登录链路一致性：
   - Web 端登录改为“内存登录态优先 + 本地存储失败不阻断登录成功”。
   - 在 HTTP 场景下，secure storage 异常时会自动走 fallback 存储，避免 `Null check operator used on a null value`。
2. 前端资源缓存策略：
   - `/app/main.dart.js` 已禁用 immutable 强缓存，避免旧 bundle 导致“代码已修但页面仍是旧逻辑”。
3. 休市口径一致性：
   - Web 端当日盈亏按 `/api/market/status` 判定，仅开市市场计入当日收益。
4. 行情显示稳定性：
   - 批量行情接口增加瞬时网络错误重试。
   - 后端补齐 5 位港股代码规范化（如 `00700`），避免 Web 端出现现价回退成本价。

说明：

- Web 与 App 共用同一套业务代码（`AppState + ApiService`），核心口径一致。
- 若出现“App 正常、Web 异常”，优先排查：
  1. 是否命中旧前端缓存（强刷或清缓存）
  2. 是否部署到最新 `main`
  3. `/api/prices/batch` 返回中目标 code 是否有有效 `price`

---

## 5. 后端说明（Flask）

### 5.1 后端是什么

- 提供资产、交易、分析、新闻、认证、快照等 API
- 当前以 SQLite 为主存储

### 5.2 本地运行

```bash
cd /Users/kona/Desktop/kaka/kona_repo/kona_tool
pip3 install -r requirements.txt
python3 app.py
```

默认端口：`5003`

### 5.3 关键环境变量

参考模板：`/Users/kona/Desktop/kaka/kona_repo/kona_tool/.env.example`

当前代码支持（重要项）：

- `JWT_SECRET`
- `AUTH_REFRESH_TOKEN_DAYS`（默认 365）
- `AUTH_REFRESH_TOKEN_RETENTION_DAYS`（默认 90）
- `ENABLE_BACKGROUND_SNAPSHOT`（建议 `false`）
- `ENABLE_STARTUP_SNAPSHOT`（建议 `false`）
- `KONA_DATABASE_PATH`（可选）
- `RATELIMIT_STORAGE_URL`（建议 `redis://127.0.0.1:6379/0`）
- `ALLOW_LOCAL_ADMIN_BYPASS`（仅本机开发，生产建议 `false`）
- `ALERT_NOTIFY_TO`（告警邮箱，可多个）
- `KONA_HEALTH_URL`（健康探活 URL）
- `PRICE_HEALTH_URL`（价格健康指标 URL）
- `PRICE_HEALTH_NETWORK_FAIL_DELTA_THRESHOLD`（默认 20）
- `PRICE_HEALTH_STALE_HITS_DELTA_THRESHOLD`（默认 30）
- `PRICE_HEALTH_SOURCE_CONSEC_FAIL_THRESHOLD`（默认 5）
- `KONA_BACKUP_DIR`（备份目录）
- `KONA_BACKUP_RETENTION_DAYS`（默认 14）
- `PRICE_HEALTH_TOKEN`（可选；留空即不鉴权）
- `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASS`（仅运维告警，不用于登录）

---

## 6. 数据库结构（当前核心表）

数据库文件：`/home/ec2-user/portfolio/kona_tool/portfolio.db`（线上）

### 6.1 users

- `id`（用户 UUID）
- `username`（唯一用户名）
- `password_hash`（密码哈希，不存明文）
- `legacy_needs_password_setup`（历史账号补设密码标记）
- `password_updated_at`（最近改密时间）
- `nickname`
- `avatar`
- `register_method`
- `phone`
- `user_number`
- `is_admin`
- `status`
- `created_at`
- `last_login`

### 6.2 portfolio（持仓）

- `code`, `name`
- `qty`, `price`
- `currency`
- `adjustment`（校准项，承载“已实现收益/分红等”的累积值，影响累计收益口径）
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

### 6.5 累计收益口径（重要）

当前产品对“累计收益/累计盈亏”的最终口径定义为：

- `累计收益(total_pnl) = 持仓未实现收益 + 已实现收益（卖出落袋）`

其中：

- 未实现收益：`(现价 - 成本价) * 数量`（按汇率折算后汇总）
- 已实现收益：卖出时的成交差价收益（目前不计手续费/税费）
- `portfolio.adjustment` 用于累积承载“已实现收益（以及后续可能的分红等）”，因此它会影响 `total_pnl`

为保证“清仓后已实现收益不丢失”：

- 当某资产卖到 `qty=0` 时，后端不再删除该 `portfolio` 记录，而是保留 `qty=0`，并将本次卖出盈亏累加到 `adjustment`
- `GET /api/portfolio` 默认只返回 `qty>0` 的持仓，所以清仓资产不会在列表里出现
- 快照计算会包含 `qty=0` 的记录（只为了把已实现收益纳入累计收益），从而保证 `daily_snapshots.total_pnl` 口径稳定

---

## 7. 部署说明（GitHub + AWS）

### 7.1 自动部署（代码发布）

工作流文件：`/Users/kona/Desktop/kaka/kona_repo/.github/workflows/deploy.yml`

触发方式：

- push 到 `main`
- pull request 到 `main`（仅门禁，不部署）
- 手动触发 `workflow_dispatch`

流程：

1. 先跑 `backend-gate`（Python compile + unittest）
2. 再跑 `frontend-gate`（flutter analyze + test + web release build）
3. 仅当门禁全绿时，执行 `deploy` 到 AWS（任一门禁失败则跳过部署）
4. 打包并上传 Flutter Web 产物（`flutter-web.tar.gz`）
5. SSH 登录 AWS，`git pull/reset` + `pip install`
6. 解压 Web 产物到 `kona_tool/static/app`
7. 刷新 `kona.service` 并重启
8. 健康检查 `/health`

### 7.1 Deploy 所需 Secrets（当前工作流补充）

仓库 `Settings -> Secrets and variables -> Actions` 需配置：

- `SSH_HOST`：EC2 公网 IP / EIP
- `SSH_KEY`：可登录 `ec2-user` 的私钥
- `APP_DIR`：服务器上的后端目录（如 `/home/ec2-user/portfolio/kona_tool` 或父目录）

说明：

- 当前 workflow 中 `username` 固定为 `ec2-user`
- `deploy` 阶段会自动识别：
  - 若 `APP_DIR/app.py` 存在，则 Web 解压到 `APP_DIR/static/app`
  - 若 `APP_DIR/kona_tool` 存在，则 Web 解压到 `APP_DIR/kona_tool/static/app`

### 7.1.1 分支与 AWS 自动拉取约定（很重要）

- 当前线上自动部署/自动拉取以 `main` 为准
- 推送到 `codex/*` 或其他功能分支，不会触发线上自动更新
- 若修复先在功能分支完成，必须再合入 `main`（merge 或 cherry-pick）并 `push origin main`

推荐发布顺序：

1. 在功能分支开发与验证
2. 通过 PR 合并到 `main`（或将提交 cherry-pick 到 `main`）
3. push `main` 后等待 Actions 门禁与部署
4. 在 AWS 检查服务状态与关键页面

### 7.1.2 严格门禁策略（2026-02-13 已启用）

- 已在 `/Users/kona/Desktop/kaka/kona_repo/.github/workflows/deploy.yml` 中显式限制：
  - `needs.backend-gate.result == 'success'`
  - `needs.frontend-gate.result == 'success'`
- 满足以上条件才允许执行 `Deploy to AWS`
- 这意味着“push 成功”不等于“已上线”，必须看 Actions 三段都通过

### 7.1.3 Push 说明（APK 构建触发规则）

工作流文件：`/Users/kona/Desktop/kaka/kona_repo/.github/workflows/deploy.yml`

- 默认规则（`push main` / `pull_request`）：
  - 若未改动 `flutter/android/**`，则跳过 `Flutter build apk (debug smoke)`，其余门禁照常执行
  - 若改动了 `flutter/android/**`，才执行 APK smoke 构建
- 手动触发（`workflow_dispatch`）：
  - 强制执行 APK smoke 构建（用于发布前手动全量验收）

推荐用法：

1. 仅后端 / Web / Dart 业务逻辑改动：直接 push，CI 会自动跳过 APK 构建。
2. 涉及 Android 工程改动（`flutter/android/**`）：push 后会自动执行 APK smoke。
3. 需要人工强制全量验证时：在 Actions 页面手动触发 `Deploy to AWS` workflow。

### 7.2 生产运行（服务托管）

推荐用 `systemd`（已在线上启用）：

- 主服务：`kona.service`
- 价格健康巡检：`kona-healthcheck.timer` / `kona-healthcheck.service`
- 快照缺失巡检：`kona-snapshot-verify.timer` / `kona-snapshot-verify.service`
- 价格阈值巡检：`kona-price-health-alert.timer` / `kona-price-health-alert.service`
- 每日快照：`kona-snapshot.service` + `kona-snapshot.timer`
- 每日备份：`kona-db-backup.service` + `kona-db-backup.timer`

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
sudo systemctl list-timers | grep kona
sudo journalctl -u kona-snapshot.service -n 50
```

### 9.4 手动触发快照

```bash
curl -s -X POST http://127.0.0.1:5003/api/snapshot/trigger
```

### 9.5 健康检查

```bash
curl -s http://127.0.0.1:5003/api/rates
curl -s http://127.0.0.1:5003/health
curl -s http://127.0.0.1:5003/api/system/price_health
```

### 9.6 告警与备份巡检日志

```bash
sudo journalctl -u kona-healthcheck.service -n 80 --no-pager
sudo journalctl -u kona-snapshot-verify.service -n 80 --no-pager
sudo journalctl -u kona-price-health-alert.service -n 80 --no-pager
sudo journalctl -u kona-db-backup.service -n 80 --no-pager
```

### 9.7 手动恢复演练

```bash
sudo systemctl stop kona
python3 /home/ec2-user/portfolio/kona_tool/scripts/restore_portfolio_db.py
sudo systemctl start kona
curl -i --max-time 5 http://127.0.0.1:5003/health
```

恢复成功后会生成：
- `portfolio.db.pre_restore_<timestamp>`

---

## 10. 登录与会话（Auth V2）

### 10.1 现状

- 登录：`username + password`
- 注册：`username + password + invite_code`
- 邀请码：一次性消费，可作废，可导出 CSV 批量管理
- 改密：必须提供原密码；成功后吊销该用户所有 refresh token
- 生物识别：仅客户端本地校验（iOS/Android `local_auth`），服务端不存生物特征
- 管理后台登录：复用同一套账号密码体系，登录后再校验 `is_admin`
- 旧接口：`POST /api/auth/send_code` 已下线，返回 `410`

### 10.2 关键配置

`.env` 示例（认证相关）：

```env
JWT_SECRET=<required_secret>
AUTH_REFRESH_TOKEN_DAYS=365
AUTH_REFRESH_TOKEN_RETENTION_DAYS=90
RATELIMIT_STORAGE_URL=redis://127.0.0.1:6379/0
```

### 10.3 接口

- `POST /api/auth/login`
- `POST /api/auth/register`
- `POST /api/auth/invite/validate`
- `POST /api/auth/password/change`
- `POST /api/auth/refresh`
- `POST /api/auth/logout`
- `GET /api/auth/me`
- `POST /api/auth/profile`

管理员能力（`/api/admin/*`）：
- 邀请码生成/列表/作废/导出
- 历史数据归属迁移预览与执行

---

## 11. 文档索引（全部在 docs）

- Auth 持久化专题（必读）：`/Users/kona/Desktop/kaka/kona_repo/docs/README_AUTH_PERSISTENCE_BIOMETRIC.md`
- 后台重构专题（邀请码/用户/接口策略）：`/Users/kona/Desktop/kaka/kona_repo/docs/README_ADMIN_CONSOLE_V2.md`
- 结构说明：`/Users/kona/Desktop/kaka/kona_repo/docs/STRUCTURE.md`
- 运行手册：`/Users/kona/Desktop/kaka/kona_repo/docs/RUNBOOK.md`
- 部署说明：`/Users/kona/Desktop/kaka/kona_repo/docs/DEPLOYMENT.md`
- 前端环境：`/Users/kona/Desktop/kaka/kona_repo/docs/FRONTEND_SETUP.md`
- API 列表：`/Users/kona/Desktop/kaka/kona_repo/docs/API.md`
- API 参数：`/Users/kona/Desktop/kaka/kona_repo/docs/API_DETAILS.md`
- OpenAPI：`/Users/kona/Desktop/kaka/kona_repo/docs/openapi.yaml`
- Swagger：`/Users/kona/Desktop/kaka/kona_repo/docs/swagger-ui.html`
- 导入 Postman/Apifox：`/Users/kona/Desktop/kaka/kona_repo/docs/API_IMPORT.md`
- 后端模块说明：`/Users/kona/Desktop/kaka/kona_repo/docs/CORE_MODULES.md`
- 运维维护：`/Users/kona/Desktop/kaka/kona_repo/docs/MAINTENANCE.md`

---

## 12. 新电脑 15 分钟接手流程

1. 克隆仓库并进入根目录
2. 后端：安装依赖、准备 `.env`、启动
3. 前端：`flutter pub get`、确认 API 地址、运行
4. 打开 App 验证：登录 -> 首页 -> 投资 -> 分析 -> 快讯
5. 如需上线：push 到 `main`，看 Actions 是否绿灯
6. 上 AWS 检查 `kona.service`、`kona-snapshot.timer`、`kona-db-backup.timer`

---

## 13. 开发与发布建议（团队规范）

- 本地改完先 `flutter run` / API 自测
- 满意后再 `git add -A && git commit && git push`
- 不要把 `.env`、数据库、私钥提交到仓库
- 每次改 API，更新 `docs/API.md` 与 `docs/API_DETAILS.md`
- 涉及统计口径改动，必须记录“实时/快照”来源
- 涉及线上发布时，最终上线提交必须确认已进入 `main`

---

## 14. 当前已知限制

- 后端目前是 `gunicorn + systemd`，未接入 `nginx` 反向代理（后续可补）
- SQLite 适合当前单机部署，未来多实例需迁移数据库
- 外部行情源会偶发超时（代码已做 fallback）
- Flutter `analyze` 当前存在若干 warning/info（不阻塞 CI），建议分批清理

---

## 15. 今日改动（2026-02-06）

1. CI/CD 升级为“先测试后部署”。
2. 登录/发码接口加限流与安全审计日志，支持 Redis 存储限流状态。
3. 上线运维告警链路（服务失败、健康检查失败、快照缺失、价格阈值异常）。
4. 上线 SQLite 自动备份（每日定时 + 保留天数清理）。
5. 完成恢复演练流程，脚本支持恢复前自动备份。
6. 修复恢复脚本跨分区错误 `Invalid cross-device link (Errno 18)`。

---

## 16. 今日改动（2026-02-12）

1. 投资页与资产页的新增/编辑弹窗统一改为不可点击空白关闭（`barrierDismissible: false`），仅允许“取消/保存”关闭。
2. 投资链路改为“本地乐观更新 + 后台刷新”：保存/删除后先更新列表与提示，再异步 `refreshHomeData()`，失败自动回滚。
3. 投资写接口返回统一为可携带错误文案的结果类型（`AssetActionResult`），不再只用 `bool`。
4. 投资页价格显示优化：现价/成本价在 `< 10` 时显示 3 位小数，其他维持 2 位。
5. 投资编辑默认值优化：
   - 买入/卖出默认填充当前现价（无行情时回退成本价）
   - 调整默认留空（不预填）
6. 后端新增写操作幂等支持：`/api/portfolio/add|buy|sell|modify|delete` 接受可选 `request_id`，短窗口内去重，降低重复提交导致的“数量翻倍”风险。
7. 新增纠错删除接口：`POST /api/portfolio/delete_corrective`。
   - 删除持仓（`portfolio`）
   - 删除该资产交易记录（`transactions`）
   - 清理受影响快照区间（`daily_snapshots` 中 `date >= from_date`）
   - 成功后异步重建当日快照
8. 纠错删除做了幂等/兜底：即使记录已不存在也按成功路径处理；前端在纠错删除失败时自动回退普通删除，避免“提示成功但列表回弹”。
9. 新增“投资联动买入（现金账户扣款）”：
   - 后端接口：`POST /api/portfolio/buy_with_cash`
   - 前端买入时可选择现金账户，成交成功后对应现金资产同步减少。
10. 新增“余额校验”：
   - 买入前按币种换算校验现金余额，不足时返回明确错误（如 `INSUFFICIENT_CASH`）并阻止落库。
11. 新增“15 秒撤销”：
   - 写操作成功后返回 `undo_token`，支持 `POST /api/portfolio/undo` 在 15 秒窗口内撤销最近一次投资操作。
   - 撤销成功后同步回滚持仓/交易与关联现金变动，并触发快照更新。
12. 前后端接口与测试覆盖（`8fbb46f`）：
   - 前端：`ApiService`、`AppState`、投资弹窗链路已接入 `buy_with_cash` 与 `undo`。
   - 后端：`app.py`、`core/db.py` 增加联动买入与撤销实现。
   - 测试：`flutter/test/app_state_smoke_test.dart` 与 `kona_tool/tests/test_api_baseline.py` 已补充对应场景。

## 17. 今日改动（2026-02-13）

1. 投资页滚动性能优化（已上线）：
   - 持仓列表由 `CustomScrollView + ListView(shrinkWrap)` 改为 `SliverList`，减少滚动过程中的布局抖动与卡顿。
   - FAB 显隐监听增加最外层滚动过滤（`notification.depth == 0`），降低无效滚动通知造成的频繁回调。
2. 快照定时机制已核验（AWS）：
   - `kona-snapshot.timer` 每天 `23:00 UTC` 触发（等价北京时间次日 `07:00`）。
   - `kona-snapshot-verify.timer` 每天 `23:05 UTC` 触发（等价北京时间次日 `07:05`）。
   - 最近多日 `kona-snapshot.service` 均正常执行完成（`Finished`）。
3. 分析页收益日历新增“年月选择器”（日+月视图）：
   - 标题右侧新增周期按钮：日视图显示 `YYYY年MM月`，月视图显示 `YYYY年`。
   - 选择器仅允许选择有快照数据的周期（空周期禁用）。
   - `GET /api/analysis/calendar` 增加可选参数 `year`、`month`，并返回 `period`、`selectable` 元数据。

## 18. 今日改动（2026-02-13，后台重构）

1. 运营后台完成“全中文、去技术化、人性化”重构（保留模板方案，不新建 SPA）：
   - 全局字典映射：状态/动作/策略/错误统一中文展示
   - 全局交互组件：统一确认弹窗（普通/高风险/确认词）+ 统一详情抽屉
   - 顶部改为“当前管理员 + 右上角退出登录”
2. 信息架构重构：
   - 菜单分组统一为：运营总览 / 用户中心 / 邀请码中心 / 接口与策略 / 数据运维 / 系统配置 / 操作审计
3. 用户中心重构：
   - 支持启用/停用、管理员切换、重置临时密码、强制改密、强制下线
   - 支持批量停用/批量启用/批量强制下线
   - 支持在线会话数预估，降低误操作风险
4. 邀请码中心重构：
   - 表头与字段改为运营语义：邀请码 / 可用性 / 使用用户名 / 使用用户编号 / 使用时间 / 操作
   - 默认筛选“未使用”，分页 20 条，支持“未使用/已使用/已作废/全部”切换
   - 已使用邀请码不可作废（前端明确禁用提示）
5. 接口与策略页重构：
   - 页面定位改为“接口与策略中心”
   - 策略表改为业务语义：策略名称、分类、状态、限流、备注、影响说明
   - 健康检测与策略编辑同屏，支持快速闭环
6. 数据运维页重构：
   - 历史数据归属迁移入口迁入数据页
   - 周末收益清理支持预览影响条数
   - 备份恢复增加“最近备份信息”与确认词保护（`立即恢复`）
7. 系统配置页重构：
   - 配置名称/说明/建议范围中文化
   - 支持单项恢复默认、全部恢复默认（确认词）
   - 支持“仅保存改动项”
8. 审计页重构：
   - 查询条件中文化（操作类型/操作人/时间范围/结果）
   - 支持按当前筛选导出 CSV
9. 后端新增/增强接口（保持兼容）：
   - `GET /api/admin/meta/dictionaries`
   - `GET /api/admin/summary/todo`
   - `GET /api/admin/users/sessions/count`
   - `POST /api/admin/data/snapshot/cleanup_weekend/preview`
   - `GET /api/admin/data/backup/latest`
   - `POST /api/admin/config/reset`
   - `GET /api/admin/audit/export`
10. Auth 与策略能力（本轮配套）：
    - `must_change_password` 硬约束继续生效
    - `admin_api_policies` 运行时即时生效（开关/限流）
11. 数据迁移与编号规则：
    - `009`：用户强制改密字段
    - `010`：接口策略持久化
    - `011`：用户编号重排并从 `10000` 起递增
12. CI/CD 收敛：
    - `Deploy to AWS` 已改为显式双门禁通过才执行（后端+前端）
13. 详细交接文档：
    - `/Users/kona/Desktop/kaka/kona_repo/docs/README_ADMIN_CONSOLE_V2.md`

---

## 19. 今日改动（2026-02-13，分析口径一致性与验收修复）

本节对应你在真机验收中提出的核心问题：  
“收益日历月/年是 `2.1万`，但分析页顶部卡片切到本月/今年/全部出现 `-745`，口径对不上”。

### 19.1 已确认并落地的最终口径

1. 首页“本月收益/今年收益”唯一真值：`GET /api/analysis/overview` 的 `month.pnl` / `year.pnl`。  
2. 分析页顶部卡片（本月/今年/全部）使用同一套 `overview` 数据源。  
3. 收益日历（月/年汇总）与顶部卡片必须同口径，不能再出现同周期数值冲突。

### 19.2 初始化基线能力状态（最终）

1. “设为初始化基线 / 清除初始化基线”能力已整体下线（前后端同步）。  
2. 基线接口已移除：  
   - `GET /api/analysis/baseline`  
   - `POST /api/analysis/baseline`  
3. 旧客户端若仍调用上述接口会得到 `404`（符合预期）。

### 19.3 本次根因与修复（你本次验收对应）

#### 根因 1：当前周期统计边界不一致
- `overview` 的 month/year 原本只统计到“今天”。  
- `calendar` 的 month/year 在当前周期可能读到“今天之后”的快照（例如测试或补录产生的未来日期），导致同周期结果不一致。

修复：
- `calendar` 的当前月/当前年查询边界统一截断到 `today`。  
- `year` 视图同样限制到 `date <= today`。

#### 根因 2：月初/年初“无前置快照”时基准不一致
- `overview` 旧逻辑：无前置快照时，用当期第一条快照当基准，容易得到 `-745` 这类结果。  
- `calendar` 旧逻辑：当期按 0 基线累计，得到 `2.1万`。

修复：
- `overview` month/year 在“无前置快照”时改为 0 基线累计，与日历一致。  
- 同时保留收益率分母逻辑（优先使用当期可用 `total_invest`）。

#### 根因 3：周末快照影响不一致
- 周末快照在不同统计路径上处理不一致，会造成月/年偏差。

修复：
- `overview` month/year 与 `calendar` month/year 统一忽略周末快照影响。

#### 根因 4：分析页顶部卡片可能显示旧缓存
- 分析页使用 `IndexedStack`，切换到“本月/今年/全部”可能读到旧概览缓存。

修复：
- 切换到非“当日”周期时，强制刷新 `overview`，避免旧值滞留。

### 19.4 你关心的“月=年都 2.1万是否正确”

在当前数据下是可能正确的，常见场景：
1. 只有当年数据，没有往年快照。  
2. 今年当前只有一个有收益的月份（例如 2 月）。  

此时：
- `本年累计` = `当月累计`  
属于正常业务结果，不是 bug。

### 19.5 收益日历（年月选择器）最终交互定义

1. 选择器位置：收益日历标题下方。  
2. 维度：保留 `日 / 月 / 年`。  
3. 日期筛选：底部弹层滚轮（年/月），仅展示有快照数据的项。  
4. 空周期：不可选择。  
5. 当前周期无数据：默认跳最近有数据周期。  
6. 实时当日盈亏覆盖：仅在“日视图且所选为当前年月”时覆盖当天格子；历史月份不覆盖。

### 19.6 后端接口当前定义（分析相关）

1. `GET /api/analysis/overview?period=all|day|month|year`  
2. `GET /api/analysis/calendar?type=day|month|year&year=<int>&month=<int>`（`year/month` 为可选）  
3. `calendar` 响应新增并保留：  
   - `period`（当前实际周期）  
   - `selectable`（可选年/月集合）

### 19.7 本次验证记录（已执行）

后端：
```bash
cd /Users/kona/Desktop/kaka/kona_repo/kona_tool
.venv/bin/python -m unittest -q tests/test_api_baseline.py
.venv/bin/python -m unittest -q tests/test_calendar_weekend.py
```

前端：
```bash
cd /Users/kona/Desktop/kaka/kona_repo/flutter
flutter test test/analysis_calendar_picker_test.dart
```

以上测试均通过；新增回归用例覆盖了：
1. 当前周期存在未来日期快照时，`overview` 与 `calendar` 仍一致。  
2. 无年初前置快照时，`overview year` 与 `calendar month total` 一致。  
3. 周末快照不再污染 month/year 汇总。

### 19.8 追加修复（首屏收益纠偏 + 日历持久缓存 + all 口径修正）

你在后续验收里又反馈了三个问题：
1. 首页首开时“本月收益/今年收益”先出现 10w+，随后才回落。  
2. 分析页日历首次加载慢，偶发只看到今天有值。  
3. 分析页顶部“全部/累计盈亏”与预期不一致。  

本轮已落地修复如下（代码已合入本地）：

#### A. 首页收益首屏不再先显示错误大值

1. `AppState` 新增 `overviewMilestonesReady` 状态，月/年收益仅在拿到 `overview` 有效值后展示。  
2. `hydrateFromCache()` 增加读取 `cache_analysis_overview`，冷启动优先显示上次正确收益口径。  
3. `refreshHomeData()` 改为两阶段：
   - 核心数据（资产/持仓/历史/overview）先返回并 `notify`；
   - 行情价格改为后台刷新（不阻塞首页收益首屏）。  
4. 首页月/年里程碑显示条件从“有历史基线”改为“`overviewMilestonesReady` 为真”。  

#### B. 分析页日历增加持久缓存（历史秒开）

1. 分析页接入 `CacheService`，新增持久缓存键：
   - `analysis_calendar_v1:{userId}:day:{yyyy}-{mm}`
   - `analysis_calendar_v1:{userId}:month:{yyyy}`
   - `analysis_calendar_v1:{userId}:year`
2. 加载策略：
   - 先读内存缓存；
   - 再读本地持久缓存并立即渲染；
   - 当前月/当前年后台增量刷新；
   - 历史周期命中缓存时不阻塞页面等待网络。  
3. 修复“只显示今天”误导：只有在 `items` 非空且确为当月 `day` 视图时，才覆盖当天实时值。  

#### C. `overview all` 口径修正

1. 后端 `get_pnl_overview(period='all')` 仅统计 `date <= today` 的快照，忽略未来日期快照。  
2. `all.pnl` 改为“截至今天最后一条快照的 `total_pnl`（累计值）”，不再做首尾差值。  
3. `all.pnl_rate` 分母优先最新 `total_invest`，无则回退首条 `total_invest`，再兜底 `1`。  

#### D. 对应测试补充

后端新增/调整了 `test_api_baseline.py` 用例，覆盖：
1. `all` 忽略未来快照。  
2. `all` 返回最新 `total_pnl` 累计值而非差值。  
3. `all` 与日历累计在同数据集下保持一致。  

前端测试补充：
1. `AppState` 覆盖 `overviewMilestonesReady` 的有效/无效状态。  
2. 分析页历史周期命中持久缓存后，重建页面不再重复请求网络。  

## 20. 线上入口与快速验收（当前）

- 后端健康：`http://57.180.79.186:5003/health`
- 后台登录：`http://57.180.79.186:5003/admin/login`

一键检查（AWS）：

```bash
set -euo pipefail
sudo systemctl status kona.service --no-pager -l | sed -n '1,80p'
ss -ltnp | grep :5003 || true
curl -sS http://127.0.0.1:5003/health
```

## 21. 结论

当前项目已经具备：

- 可持续开发（前后端分离、文档齐全）
- 可自动部署（GitHub Actions + 门禁）
- 可稳定运行（gunicorn + systemd 自动重启）
- 可观测（健康接口 + 邮件告警）
- 可恢复（每日备份 + 恢复演练）
- 可稳定产出统计（定时快照 + 缺失巡检）

如果你后续换电脑或让新成员接手，按本 README + `docs/` 可以完整恢复上下文并继续开发。

---

## 22. 今日改动（2026-02-17，休市口径 + Web/App 一致性）

本节对应本轮你重点反馈的问题：

1. 分析页无数据、无法下拉刷新。  
2. 美股仅有盘中价，盘前盘后未纳入展示与当日盈亏。  
3. Web 与 App 在登录、价格、收益口径上需保持一致。  

### 22.1 分析页（Flutter）

1. 分析页已支持下拉刷新（`RefreshIndicator`）。  
2. 下拉刷新会强制重拉：
   - 分析概览（`/api/analysis/overview`）
   - 收益日历（`/api/analysis/calendar`）
3. 当分析页处于“空数据首开”时，会补触发一次首页核心数据刷新，避免“分析页无任何数据”。  

代码位置：
- `/Users/kona/Desktop/kaka/kona_repo/flutter/lib/pages/analysis_page.dart`

### 22.2 美股盘前/盘后行情（后端 + Flutter）

后端：

1. `/api/prices/batch` 增强美股扩展时段字段（盘前/盘后）：
   - `regular_price`
   - `premarket_price`
   - `after_hours_price`
   - `session`
   - `effective_session`
   - `extended_active`
2. 美股扩展时段数据源使用 Nasdaq quote info 接口，按状态计算有效价格与涨跌额。  

代码位置：
- `/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/stock.py`
- `/Users/kona/Desktop/kaka/kona_repo/kona_tool/app.py`

前端：

1. `PriceInfo` 扩展上述字段并持久化到本地缓存。  
2. 当 `US regular 休市` 但 `pre/post 活跃` 时：
   - 允许该美股参与当日盈亏计算；
   - 投资页现价旁显示 `盘前` / `盘后` 标记。  

代码位置：
- `/Users/kona/Desktop/kaka/kona_repo/flutter/lib/models/portfolio.dart`
- `/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_state.dart`
- `/Users/kona/Desktop/kaka/kona_repo/flutter/lib/pages/invest_page.dart`

### 22.3 休市口径（A/HK/US/Fund）

本轮延续并补强“统一休市口径”：

1. 非开市市场默认当日盈亏为 0。  
2. 美股扩展时段（盘前/盘后）是唯一例外：可参与当日盈亏。  
3. 目标是“现价展示 + 当日盈亏口径”在 Web / App 同步一致。  

### 22.4 Web 登录与一致性说明

1. Web 登录成功后，存储异常不再阻断登录态建立。  
2. HTTP 场景下，secure storage 异常会 fallback，避免 `Null check operator used on a null value`。  
3. Web 与 App 共用同一套 API 与核心口径：
   - `AppState`
   - `ApiService`
   - `/api/market/status`
   - `/api/prices/batch`

### 22.5 CI / Push 规则（重点）

为避免每次都慢速跑 APK：

1. 若本次提交未改动 `flutter/android/**`，CI 跳过 `Flutter build apk (debug smoke)`。  
2. 其余门禁（后端测试、Flutter analyze/test/web build）照常执行。  
3. 仅改后端/Web/Dart 业务逻辑时，可直接 push，不需要强制 APK smoke。  
4. 如需手动全量验证，可在 Actions 手动触发 `workflow_dispatch`。  

### 22.6 本轮已执行的验证（本地）

Flutter：

```bash
cd /Users/kona/Desktop/kaka/kona_repo/flutter
flutter test test/analysis_calendar_picker_test.dart test/app_state_market_day_pnl_test.dart
flutter test test/widget_test.dart
```

后端：

```bash
cd /Users/kona/Desktop/kaka/kona_repo/kona_tool
JWT_SECRET=test .venv/bin/python -m unittest -q tests/test_api_baseline.py
```

### 22.7 真机安装（推荐 USB）

```bash
cd /Users/kona/Desktop/kaka/kona_repo/flutter
flutter build apk --debug
adb devices -l
adb -s <USB_DEVICE_ID> install -r -t build/app/outputs/flutter-apk/app-debug.apk
adb -s <USB_DEVICE_ID> shell am start -n com.example.tool/com.example.tool.MainActivity
```
