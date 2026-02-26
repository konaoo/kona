# 咔咔记账（Kona）

个人资产与投资管理系统，支持多资产类型管理、收益分析、后台运营与线上部署。

---

## 1. 项目简介

- 前端：Flutter（Android / iOS / macOS）+ Vue3（Web）
- 后端：Python Flask
- 数据库：SQLite（`portfolio.db`）
- 部署：GitHub Actions + AWS EC2（`systemd + gunicorn`）

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

---

## 3. 快速开始

### 3.1 后端本地运行

```bash
cd /Users/kona/Desktop/kaka/kona_repo/kona_tool
pip3 install -r requirements.txt
python3 app.py
```

默认端口：`5003`

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

---

## 4. 部署与运维入口

- 部署说明：[`docs/DEPLOYMENT.md`](./docs/DEPLOYMENT.md)
- 运维手册：[`docs/MAINTENANCE.md`](./docs/MAINTENANCE.md)
- Runbook：[`docs/RUNBOOK.md`](./docs/RUNBOOK.md)
- OpenAPI：[`docs/openapi.yaml`](./docs/openapi.yaml)

线上入口（当前）：

- 门户：`http://57.180.79.186:5003/`
- 业务端：`http://57.180.79.186:5003/app/login`
- 管理端：`http://57.180.79.186:5003/admin/login`

---

## 5. 文档导航

认证与后台：

- [`docs/README_AUTH_PERSISTENCE_BIOMETRIC.md`](./docs/README_AUTH_PERSISTENCE_BIOMETRIC.md)
- [`docs/README_ADMIN_CONSOLE_V2.md`](./docs/README_ADMIN_CONSOLE_V2.md)

分析与收益口径：

- [`docs/README_ANALYSIS_CALENDAR_MARKET_BREAKDOWN.md`](./docs/README_ANALYSIS_CALENDAR_MARKET_BREAKDOWN.md)
- [`docs/README_HANDOVER_2026_02_ASSET_REFRESH_AND_PNL_LOGIC.md`](./docs/README_HANDOVER_2026_02_ASSET_REFRESH_AND_PNL_LOGIC.md)

Web 专项：

- [`web/README.md`](./web/README.md)
- [`docs/README_WEB_CHANGELOG_TIMELINE.md`](./docs/README_WEB_CHANGELOG_TIMELINE.md)

项目总览：

- [`docs/PROJECT_OVERVIEW.md`](./docs/PROJECT_OVERVIEW.md)
- [`docs/STRUCTURE.md`](./docs/STRUCTURE.md)

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

- `v1.0.9`：Flutter 端 App 锁屏支持，登录页多重动画重构、间距优化、跳转链接修改。
- `v1.0.8`：Web 门户/认证视觉统一 + `/app` 深浅主题体系 + `home/invest/analysis` 缓存优先刷新（SWR）+ 投资/分析页新增隐私与截图工具行。
- `v1.0.7`：Web 登录/注册页改版（独立 `/app/register`、记住我、返回交互优化）+ 注册确认密码与中文错误文案统一 + 登录提速（去除阻塞式全量刷新）。
- `v1.0.6`：Web 页面体验收敛（快讯开关/LIVE/重要标签、侧栏个人区重构、`/app/me` 页头精简）+ 资产页缓存优先刷新。

详细内容见：[`CHANGELOG.md`](./CHANGELOG.md)

---

## 8. 完整历史入口

历史“按日期”记录已全量迁移为版本化记录，统一维护在：

- [`CHANGELOG.md`](./CHANGELOG.md)

说明：

- 旧 README 中“今日改动（按日期）”章节（原 15~23）已并入版本历史。
- 后续新改动不再新增“日期章节”，统一走版本条目。
