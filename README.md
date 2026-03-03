# 咔咔记账（Kona）

个人资产与投资管理系统，支持多资产类型管理、收益分析、后台运营与线上部署。
> 当前生产入口仅 IP：`http://114.132.238.12`；域名 `kakawallet.fun` / `www.kakawallet.fun` 已临时禁用。

---

## 1. 项目简介

- 前端：Flutter（Android / iOS / macOS）+ Vue3（Web）
- 后端：Python Flask
- 数据库：SQLite（`portfolio.db`）
- 部署：GitHub Actions + 腾讯云轻量服务器（`Caddy + systemd + gunicorn`，Nginx 已停用）

定位：在保证“日常可用 + 可持续运维”的前提下，统一管理资产、收益、快照、行情与后台运营能力。

---

## 2. 技术栈与仓库结构

```text
kona_repo/
├─ flutter/          # Flutter 客户端（业务端）
├─ web/              # Vue3 + Vite Web（门户/业务端/管理端）
├─ kona_tool/        # Flask 后端（API + 核心业务 + 定时任务）
├─ docs/             # 项目文档与交接文档
├─ scripts/          # 辅助脚本
└─ CHANGELOG.md      # 版本迭代主记录（唯一标准）
```

核心目录：

- 后端：`/Users/kona/Desktop/kaka/kona_repo/kona_tool`
- Flutter：`/Users/kona/Desktop/kaka/kona_repo/flutter`
- Web：`/Users/kona/Desktop/kaka/kona_repo/web`
- 说明：`kona_tool/templates` 仅保留管理后台模板（`admin_*`），业务端旧 Flask 模板页已废弃并删除

---

## 3. 快速开始

### 3.1 后端本地运行

```bash
cd /Users/kona/Desktop/kaka/kona_repo/kona_tool
pip3 install -r requirements.txt
export JWT_SECRET="dev_secret_key"
python3 app.py
```

默认端口：`52345`（说明：本地 Python 启动走 52345，线上部署使用 Gunicorn 跑 5003 端口）

### 3.2 Flutter 本地运行

```bash
cd /Users/kona/Desktop/kaka/kona_repo/flutter
flutter pub get
flutter run
```

### 3.3 Web 本地运行

```bash
cd /Users/kona/Desktop/kaka/kona_repo/web
npm ci
npm run dev
```

生产构建：

```bash
cd /Users/kona/Desktop/kaka/kona_repo/web
npm run build
```

### 3.4 旧 Flask 模板页下线说明（2026-03）

业务端旧模板页（Jinja）已从仓库删除，不再作为运行入口：

- 已删除：`kona_tool/templates/{index,assets,investment,analysis,news,settings,test_api,simple_home,simple_render,base}.html`
- 后端兼容路由保留为 302 跳转，不再读取模板文件：
  - `/assets -> /app/invest`
  - `/analysis -> /app/analysis`
  - `/news -> /app/news`
  - `/settings -> /app/profile`
  - `/test -> /app`
- 当前唯一业务端前端来源：`web/` 构建产物（`kona_tool/static/web`）

---

## 4. 部署与运维入口

- 部署说明：[`docs/DEPLOYMENT.md`](./docs/DEPLOYMENT.md)
- 运维手册：[`docs/MAINTENANCE.md`](./docs/MAINTENANCE.md)
- Runbook：[`docs/RUNBOOK.md`](./docs/RUNBOOK.md)
- OpenAPI：[`docs/openapi.yaml`](./docs/openapi.yaml)
- 腾讯迁移交接：[`docs/README_HANDOVER_2026_03_TENCENT_MIGRATION.md`](./docs/README_HANDOVER_2026_03_TENCENT_MIGRATION.md)
- 换电脑与后续待办总清单：[`docs/README_HANDOVER_2026_03_NEW_PC_TODO.md`](./docs/README_HANDOVER_2026_03_NEW_PC_TODO.md)

线上入口（当前）：

- IP 直连：`http://114.132.238.12/`
- 业务端：`http://114.132.238.12/app/login`
- 管理端：`http://114.132.238.12/admin/login`
- 域名：已临时禁用（备案完成后再评估恢复）

---

## 5. 文档导航

认证与后台：

- [`docs/README_AUTH_PERSISTENCE_BIOMETRIC.md`](./docs/README_AUTH_PERSISTENCE_BIOMETRIC.md)
- [`docs/README_ADMIN_CONSOLE_V2.md`](./docs/README_ADMIN_CONSOLE_V2.md)

分析与收益口径：

- [`docs/README_ANALYSIS_CALENDAR_MARKET_BREAKDOWN.md`](./docs/README_ANALYSIS_CALENDAR_MARKET_BREAKDOWN.md)
- [`docs/README_HANDOVER_2026_02_ASSET_REFRESH_AND_PNL_LOGIC.md`](./docs/README_HANDOVER_2026_02_ASSET_REFRESH_AND_PNL_LOGIC.md)
- [`docs/README_HANDOVER_2026_03_TENCENT_MIGRATION.md`](./docs/README_HANDOVER_2026_03_TENCENT_MIGRATION.md)

Web 专项：

- [`web/README.md`](./web/README.md)
- [`docs/README_WEB_CHANGELOG_TIMELINE.md`](./docs/README_WEB_CHANGELOG_TIMELINE.md)

项目总览：

- [`docs/PROJECT_OVERVIEW.md`](./docs/PROJECT_OVERVIEW.md)
- [`docs/STRUCTURE.md`](./docs/STRUCTURE.md)

管理后台当前口径（2026-03）：

- 菜单：`数据概览 / 用户管理 / 邀请码管理 / 运营配置 / 接口管理`
- 已下线：审计查询页面与导出能力（前端路由 `/admin/audit`、后端 `GET /api/admin/audit/logs`、`GET /api/admin/audit/export`）
- 审计写入仍保留（后台写操作继续落库 `admin_audit_logs`，仅不对外提供查询接口）

---

## 6. 版本与发布规范

版本策略（固定）：

- 起始版本：`v1.0.0`
- 默认迭代：`patch`（如 `v1.0.0 -> v1.0.1`）
- 仅在你明确确认时升级：
  - `minor`：`v1.1.0`
  - `major`：`v2.0.0`

记录规则（固定）：

1. 每次更新先写 `CHANGELOG.md`（唯一标准）。
2. `README.md` 只保留结构化导航 + 最近版本摘要，不写日期流水账。
3. 同一上线波次合并为一个版本条目，不按单 commit 拆分。
4. 协作执行特例（Web + 管理后台 Admin）：默认“完成即直推 `main`”，推送后由你验收；Flutter 与非 Admin 后端改动仍按常规确认流程执行。
5. APK 对外下载采用固定文件名覆盖发布，不改下载链接；固定路径：
   - 服务器：`/opt/kaka/portfolio/kona_tool/static/downloads/kaka-latest-release.apk`
   - 下载链接：`http://114.132.238.12/download/apk`

客户端版本号规范（新增）：

1. 对外版本号固定使用 `1.0.x`，不再使用 `+build`（示例：`1.0.22`、`1.0.23`）。
2. 安卓内部安装序号（`versionCode`）由 `versionName` 的 patch 段自动映射：
   - `1.0.22 -> 22`
   - `1.0.23 -> 23`
3. 后端 `/api/app/version` 继续返回 `buildNumber` 兼容旧端；默认与 `version` 的 patch 段对齐。
4. 版本展示统一为 `v1.0.x`，不再展示 `+build`。

APK 覆盖发布命令（固定）：

```bash
scp -i ~/.ssh/tencent_kona_key \
  /Users/kona/Desktop/kaka/kona_repo/flutter/build/app/outputs/flutter-apk/app-release.apk \
  root@114.132.238.12:/opt/kaka/portfolio/kona_tool/static/downloads/kaka-latest-release.apk
```

本地构建 + 上传一键命令（固定）：

```bash
cd /Users/kona/Desktop/kaka/kona_repo/flutter && flutter build apk --release && \
scp -i ~/.ssh/tencent_kona_key \
  /Users/kona/Desktop/kaka/kona_repo/flutter/build/app/outputs/flutter-apk/app-release.apk \
  root@114.132.238.12:/opt/kaka/portfolio/kona_tool/static/downloads/kaka-latest-release.apk
```

上传后快速校验（建议每次都跑）：

```bash
curl -I http://114.132.238.12/download/apk
```

`CHANGELOG.md` 条目模板：

```md
## vX.Y.Z - <版本标题>
- 发布状态：Released | In Progress
- 发布类型：Patch | Minor | Major
- 范围：Flutter | Web | Backend | Infra | Docs

### Summary
### Added
### Changed
### Fixed
### Ops / Deployment
### Data / Migration
### Verification
### Notes
```

---

## 7. 最近版本摘要

- `v1.0.23`：Flutter 现金资产弹窗新增币种选择（默认 CNY）；交易弹窗改为同币种账户过滤并支持“缺账户一键创建”；后端现金资产金额校验放宽为 `>=0`（其他资产/负债仍 `>0`），版本升级到 `1.0.23`。
- `v1.0.22`：Flutter 添加资产弹窗改为“输入后手动点搜索”并引入自定义数字键盘（数量两位小数、负号规则按字段限制）；分析页收益日历修复历史月份切换后无法回到当月问题；B股币种全端修复（`sh900* -> USD`、`sz200* -> HKD`）并增加后端历史数据自动回填。
- `v1.0.21`：登录错误提示统一为“用户名/密码错误，请重试”；邀请码页/用户群页文案默认左对齐；我的页面移除“问题反馈”；版本号规范切换为无 `+build`（安卓内部序号自动映射 patch）。
- `v1.0.19`：修复 Clash/TUN 代理导致 App 登录 TLS 握手失败；Caddy 新增 HTTP 直连入口，Flutter 端临时切换 IP 直连；构建环境升级 Gradle 8.13 + JDK 21。
- `v1.0.18`：生产环境迁移至腾讯云（广州），线上入口统一到 `http://114.132.238.12`；完成 `Nginx(80) -> Gunicorn(127.0.0.1:5003)` 正式收敛，修复迁移后登录 500（Redis 限流依赖补齐）。
- `v1.0.17`：管理后台用户页支持“最近活跃/总资产/注册时间”降序排序与服务端分页（10/20/50/100）；统一北京时间与中文省市地区展示（含历史回填）；修复 `/admin/users` 强刷黑页；线上完成最小扩容（2 workers + 预取降频 + 2GB swap）。
- `v1.0.16`：统一资产四类口径（A股/美股/港股/基金），修复 `NUGT/QQQ/BOXX` 等美股ETF误归基金问题；后端新增入库标准化与搜索过滤，并完成线上历史 `f_` 字母代码修复。
- `v1.0.15`：跨端会话稳定性修复（App 401 自动续期、Web refresh 并发互斥、后端 optional_auth 严格化）+ 门户 APK 固定下载链路 + 首屏闪黑与标题修复。
- `v1.0.14`：Flutter 个人中心与系统设置重构、问题反馈入口迁移、投资页底部留白优化、下拉刷新体验收敛（仅顶部小动画）。
- `v1.0.13`：后端行情预取缓存（秒回优化），接口读缓存优先，显著降低响应延迟。
- `v1.0.12`：App 启动即时同步 + 分析页排行跨币种汇率修正。
- `v1.0.9`：Flutter 端 App 锁屏支持，登录页多重动画重构、间距优化、跳转链接修改。

详细内容见：[`CHANGELOG.md`](./CHANGELOG.md)

---

## 8. v1.0.23 详细改动说明（本次）

范围说明：

1. 本次只落地 `Flutter + Backend + Docs`，Web 按当前决策未改动。
2. 目标是“降低多币种交易误操作”，并减少新建外币账户的操作成本。

Flutter 交互改造：

1. 现金资产弹窗（`AddAssetDialog`）新增币种下拉：
   - 可选：`CNY / USD / HKD`
   - 默认：`CNY`
   - 编辑时会回填原币种
2. 交易弹窗（`InvestTradeDialog`）资金账户选择改为“按交易目标币种过滤”：
   - 买入/卖出时只显示同币种现金账户
   - 非卖出模式仍保留“外部资金/初始转入”选项
3. 卖出/买入缺少同币种账户时，弹窗内新增“一键创建XXX账户”：
   - 卖出：创建 `资产回款账户`
   - 买入：创建 `资产资金账户`
   - 创建成功后自动选中新账户
4. 一键创建账户初始金额调整为 `0.0`（与后端新校验一致）。

AppState 行为收口：

1. `addAsset/updateAsset` 增加 `curr` 参数透传，现金资产不再丢币种。
2. 买入/卖出到现金账户时增加同币种强校验：
   - 币种不匹配直接拦截并提示
   - 防止错误走跨币种隐式换算

后端规则调整：

1. 现金资产接口（add/update）金额校验由 `> 0` 放宽为 `>= 0`。
2. 其他资产/负债保持原规则：金额必须 `> 0`。
3. 负数金额仍统一拦截（返回 `INVALID_AMOUNT` / `INVALID_VALUE`）。

版本信息：

1. Flutter 客户端版本：`1.0.23`
2. 后端默认客户端版本（`/api/app/version` 默认）：`1.0.23`

验收清单（建议逐条勾选）：

1. 添加/编辑现金资产时，币种默认 `CNY`，可切换 `USD/HKD`。
2. 添加“其他资产/负债”时，不出现币种下拉。
3. 现金资产 `amount=0` 可新增、可更新。
4. 现金资产负数金额被后端拒绝。
5. 卖出外币持仓时，若无对应币种回款账户，出现“一键创建USD/HKD账户”。
6. 一键创建后账户自动可选，交易可继续提交。
7. 买入/卖出若账户币种不匹配，前端会被拦截并显示明确错误。

验证命令（本次已执行）：

```bash
cd /Users/kona/Desktop/kaka/kona_repo/flutter
flutter test test/invest_trade_dialog_test.dart test/widget_test.dart
```

```bash
cd /Users/kona/Desktop/kaka/kona_repo/kona_tool
JWT_SECRET=dummy python3 -m unittest tests.test_api_baseline.ApiBaselineTests.test_cash_asset_amount_allows_zero
JWT_SECRET=dummy python3 -m unittest tests.test_api_baseline.ApiBaselineTests.test_cash_asset_negative_amount_rejected
JWT_SECRET=dummy python3 -m unittest tests.test_api_baseline.ApiBaselineTests.test_liability_invalid_amount_has_code
```

---

## 9. 完整历史入口

历史“按日期”记录已全量迁移为版本化记录，统一维护在：

- [`CHANGELOG.md`](./CHANGELOG.md)

说明：

- 旧 README 中“今日改动（按日期）”章节（原 15~23）已并入版本历史。
- 后续新改动不再新增“日期章节”，统一走版本条目。
