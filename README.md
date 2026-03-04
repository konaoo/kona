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
- [`docs/README_HANDOVER_2026_03_INVEST_UI_V2_AND_DILUTED_COST.md`](./docs/README_HANDOVER_2026_03_INVEST_UI_V2_AND_DILUTED_COST.md)

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

1. 对外版本号固定使用 `1.0.x`，不再使用 `+build`（示例：`1.0.22`、`1.0.23`、`1.0.24`）。
2. 安卓内部安装序号（`versionCode`）由 `versionName` 的 patch 段自动映射：
   - `1.0.22 -> 22`
   - `1.0.23 -> 23`
   - `1.0.24 -> 24`
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

- `v1.0.28`：分析页 UI 旗舰级对齐（3色深蓝渐变、18px圆角、淡蓝边框）；文案全量居中对齐；盈亏汇总栏重构为单行专业排版；修复排行榜为“累计盈亏”排序逻辑；解决 PnL 汇总数据显 0 错误。
- `v1.0.27`：分析页面 1:1 UI 复刻（纯黑背景、蓝色分段控件、7 列日历矩阵、盈亏双 KPI 汇总）；新增排行前三名金银铜勋章样式；代码洁净度优化（修复 lint 与过时 API）。
- `v1.0.26`：投资明细 UI 1:1 还原 HTML 原型（发光边框、账户列表、添加按钮）；持仓列表按当日盈亏降序排列；PnL 盈亏进度条重构（CustomPainter、1.5px 中心线、600ms 入场动画）；名称限长 20 字符；修复负号显示 Bug 与渲染崩溃；优化默认账户自动选中。
- `v1.0.25`：登录页 UI 1:1 升级还原原型（M 形 Logo、Tab 切换、聚焦发光输入框、渐变按钮、密码强度条、入场动画）；邀请码弹窗文案从后端加载 + 保存图片到相册 + 点击空白关闭；19 处 GoogleFonts 调用提取为静态缓存消除卡顿；Gradle 升级 8.13 修复 Kotlin 2.2.20 兼容。
- `v1.0.24`：投资页成本位升级为“摊薄成本”展示（Flutter + Web）；`InvestTradeDialog` 升级为 v2 居中弹窗与新交互；卖出缺同币种账户时下拉内补建现金账户；统一 `AddAssetDialog` 新 UI 并修复 other/liability 币种透传与下拉定位问题。
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

## 8. v1.0.28 详细改动说明（本次）

范围说明：

1. 本次落地 `Flutter + Docs`。
2. 目标是“分析页 UI 全面升级、盈亏汇总布局重构、核心数据排序算法修复”。

核心改动：

1. **外观旗舰化**：
   - 更新分析页大卡片至首页/投资页同级的 **3色深蓝渐变主体** + **18px 圆角**。
   - 实现卡片内容的**全量居中对齐**，重点突出盈亏金额与收益率。
2. **汇总排版专业化**：
   - 收益日历下方汇总区域重构为单行。
   - 样式：`本月盈亏：¥XXX (左对齐)  ---  盈亏率：XX% (右对齐)`。
3. **算法精密化**：
   - 修正“盈利榜”与“亏损榜”算法：从“当日变化”修正为“**累计持仓盈亏**”排序。
   - 重写数据推演逻辑：实时结合 `resolvePriceInfo` 现价与持仓均价进行二次校验。
4. **编译与部署透明化**：
   - 彻底修复 `analysis_page.dart` 的脏代码引入导致的 0 值展示和热重载失败问题。
   - 完成生产环境热重载与 Fresh Install。

版本信息：

1. Flutter 客户端版本：`1.0.28`
2. 发布状态：Released & Pushed

---

## 9. v1.0.25 详细改动说明（上次）

范围说明：

1. 本次落地 `Flutter + Docs`。
2. 目标是“登录页 UI 1:1 还原原型设计 + 邀请码弹窗功能完善 + 渲染性能优化”。

核心改动：

1. **登录页完全重写**（`login_page.dart` ~860 行）：
   - M 形渐变 Logo（`CustomPainter`）
   - 登录/注册 Tab 切换器（`AnimatedContainer` 滑块动画）
   - 自定义输入框组件 `_InputWrap`（聚焦蓝色发光描边、错误红色发光、密码可见切换、JetBrains Mono 等宽字体）
   - 渐变按钮状态机（默认 → loading → 成功打勾 → 跳转）
   - 密码强度条（弱/中/强 动态颜色）
   - 注册邀请码提示条 + 「获取邀请码」白色高亮链接
   - 底部法律声明（预留用户协议/隐私政策入口）
   - 入场 fadeUp 交错动画
2. **全局暗色主题配色更新**（`theme.dart`）：
   - `bgPrimary: #0C0D11`、`bgCard: #13151C`、`accent: #5B8DEF`、`success: #2ECC8A`、`danger: #F05A55` 等
   - 新增 `textDim` 颜色字段
3. **邀请码弹窗功能完善**：
   - 去掉标题和 X 关闭按钮，点击空白关闭
   - 文案左对齐，内容从后端 `invite_acquire_text` 动态获取
   - 按钮「保存二维码」→「保存图片」，实现下载保存到相册（`gal: ^2.3.2`）
4. **渲染性能优化**：
   - 新增 `_S` 缓存样式类（18 个 `static final` TextStyle），消除 19 处 `GoogleFonts` 每次 build 重复解析
   - `main.dart` 启动时 `GoogleFonts.pendingFonts()` 预加载字体
5. **构建环境修复**：
   - Gradle wrapper 7.3.1 → 8.13（修复 Kotlin 2.2.20 + AGP 8.11.1 编译）

版本信息：

1. Flutter 客户端版本：`1.0.25`
2. 后端默认客户端版本（`/api/app/version` 默认）：`1.0.24`（未改动后端）

验收清单（建议逐条勾选）：

1. 登录页暗色主题视觉与原型一致，M Logo + 品牌文案正常显示。
2. 登录/注册 Tab 切换流畅，滑块动画正确。
3. 输入框聚焦时蓝色发光描边、输入错误时红色描边、取消聚焦回归默认。
4. 密码输入框可切换明暗文，注册密码有强度条。
5. 邀请码弹窗文案与后端内容一致、左对齐、点击空白可关闭。
6. 保存图片按钮可下载二维码到相册。
7. 输入框聚焦 / Tab 切换无明显卡顿感。

验证命令（本次已执行）：

```bash
cd /Users/kona/Desktop/kaka/kona_repo/flutter
flutter test test/widget_test.dart
```

详细交接文档见：

- [`CHANGELOG.md`](./CHANGELOG.md)

---

## 9. 完整历史入口

历史“按日期”记录已全量迁移为版本化记录，统一维护在：

- [`CHANGELOG.md`](./CHANGELOG.md)

说明：

- 旧 README 中“今日改动（按日期）”章节（原 15~23）已并入版本历史。
- 后续新改动不再新增“日期章节”，统一走版本条目。
