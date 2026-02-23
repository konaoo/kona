# Changelog

本文件是项目版本历史的唯一标准记录。

- 版本起点：`v1.0.0`
- 默认迭代：`Patch`
- 大版本升级（`Minor`/`Major`）需你明确确认

---

## v1.0.6 - Web 页面体验收敛与个人中心入口重构
- 发布状态：Released
- 发布类型：Patch
- 范围：Web | Docs

### Summary
- Web 侧边栏移除“设置”菜单，改为左下角用户区（头像/昵称/退出）交互。
- `/app/me` 个人中心页面去掉顶部主题卡片，首屏直接展示“账号资料”。
- 市场快讯页交互对齐移动端：只看重要开关、LIVE 位置调整、重要消息标签化。
- 我的资产/我的投资/资产分析页面改为缓存优先渲染，降低 F5 后的全量请求与白屏感。
- Web 导出入口保持仅 4 类资产（现金/投资/其他/负债）能力，页面结构继续精简。

### Added
- 页面级缓存机制在 Web 资产相关页面落地（Home/Invest/Analysis/News）。
- 市场快讯项新增“重要”标识渲染样式（重要消息显示标签）。
- 侧栏资料区新增图标化退出按钮（门+箭头，纯图标）。

### Changed
- 侧栏左下角资料区改为同一行布局：左侧头像+昵称，右侧退出图标按钮。
- 市场快讯页头改为“标题+LIVE”同组展示，右侧保留“只看重要”开关。
- `我的资产` 与 `我的投资` 启动刷新策略由全量优先改为轻量优先（命中缓存时）。
- `资产分析` 页面挂载时默认先读缓存，手动点击“刷新”才执行强制全量刷新。
- `我的资产`静态轮询周期调整为 5 分钟，减少重复拉取。

### Fixed
- 修复资产分析/我的投资页面 F5 后重复全量请求的问题。
- 修复市场快讯页“只看重要”开关样式与交互不一致问题。
- 修复市场快讯页 LIVE 徽标位置与产品预期不一致问题。
- 修复侧栏“设置入口已下沉后仍保留按钮”的残留问题。

### Ops / Deployment
- Web 构建门禁持续通过，改动已按“Web 直推 main”流程发布。
- 相关改动已同步推送远端主分支，无需额外迁移步骤。

### Data / Migration
- None（无数据库迁移）

### Verification
- `cd /Users/kona/Desktop/kaka/kona_repo/web && npm run build`（通过）
- 手工验收：
  - 市场快讯：开关样式、LIVE 位置、重要标签显示
  - 侧栏：头像昵称+图标退出同一行
  - `/app/me`：去除顶部主题卡片
  - F5 后 Home/Invest/Analysis 首屏缓存渲染与轻量刷新

### Notes
- 主要来源提交：`55def90`、`2b3bbf3`、`3944ddc`、`250fcb5`、`82d44ac`、`24a6752`、`0f356e4`、`7902906`、`3f2aa73`
- 文档规范沿用：`README.md` 导航化 + `CHANGELOG.md` 版本化唯一记录

---

## v1.0.5 - Web 分析页对齐与排行口径修复
- 发布状态：Released
- 发布类型：Patch
- 范围：Web | Backend | Docs

### Summary
- Web 端分析页改为更接近 App 的结构化体验。
- 盈亏排行改为统一榜单，不再分“盈利榜/亏损榜”分类切换。
- 排行列表支持“默认 Top5 + 查看更多/收起”。
- 港股/美股（含外币基金）盈亏金额改为按汇率折算后展示人民币。
- 修复 Web 行情 `price=0` 导致持有金额和盈亏异常的问题。

### Added
- Web 分析页收益日历新增完整网格交互（`日/月/年` + 周期选择器 + 底部累计摘要）。
- Web 排行新增“查看更多/收起”交互。
- `GET /api/analysis/rank` 返回项新增 `curr` 字段，供前端做准确汇率换算。

### Changed
- Web 资产分析品牌文案与结构统一：侧栏文案更新为“咔咔记账”。
- Web 排行展示从双榜切换模式调整为单榜排序模式（结合市场筛选）。
- Web 排行金额显示统一为 CNY 口径（后台返回币种 + 前端汇率换算）。

### Fixed
- 修复 Web `BOXX` 等美股场景现价回传 `0` 时被当作有效价的问题。
- 修复 Web 排行中港股/美股金额按人民币直接显示导致的数值偏差。

### Ops / Deployment
- 完成 Web 构建验证，保证前端改造可发布。
- 相关提交均已推送到 `main`，可由现有 CI/CD 门禁流程自动发布。

### Data / Migration
- None（无数据库迁移）

### Verification
- `cd web && npm run build`（通过）
- `python3 -m py_compile kona_tool/app.py`（通过）
- 手工验收：分析页日历交互、排行 Top5/展开、港美金额折算

### Notes
- 来源提交：`d0a959b`、`7ff3dde`、`18de8cc`
- 关联文档：`docs/README_WEB_CHANGELOG_TIMELINE.md`

---

## v1.0.4 - 增量刷新与休市冻结口径统一
- 发布状态：Released
- 发布类型：Patch
- 范围：Flutter | Web | Backend | Infra

### Summary
- 引入启动阶段版本增量同步，降低重复全量请求。
- 建立“缓存先渲染 + 后台增量刷新 + 行情独立刷新”的加载链路。
- 休市场景口径统一：显示冻结值，汇总按开市市场计入。
- 混合开市日（如 A 休市 / HK 开市）“今日收益”污染问题被修复。
- Web 与 Flutter 市场状态判断逻辑统一。

### Added
- 新增接口：`POST /api/sync/bootstrap`（版本驱动增量域刷新）。
- 新增前端刷新策略：按域版本决定是否拉取数据。
- 新增休市保底价格回退策略（实时 -> 缓存 -> 快照 -> 成本）。

### Changed
- 启动时不再无条件全量刷新全部资产域。
- 行情刷新与静态资产刷新彻底分层。
- 日收益展示与汇总逻辑分离：单只可展示冻结值，汇总仅统计开市市场。

### Fixed
- 修复混合开市场景下冻结值污染“今日收益”汇总的问题。
- 修复市场状态 `trading_day` 判断在多端不一致导致的显示偏差。

### Ops / Deployment
- 调整 CI 策略：APK debug smoke 按 Android 目录变更触发。
- 减少非 Android 改动时的无效构建开销。

### Data / Migration
- None

### Verification
- 后端：`python -m unittest discover ...`（门禁覆盖）
- Flutter：真机重启、下拉刷新、休市/开市切换验收
- Web：市场状态与今日收益一致性验收

### Notes
- 来源章节：旧 README §23、§22（刷新与休市口径）
- 关联文档：`docs/README_HANDOVER_2026_02_ASSET_REFRESH_AND_PNL_LOGIC.md`

---

## v1.0.3 - 收益日历口径修复与分市场明细回填
- 发布状态：Released
- 发布类型：Patch
- 范围：Backend | Flutter | Web | Docs

### Summary
- 修复收益日历在特定日期被错误压零的问题。
- 增加分市场收益明细能力（A/HK/US/Fund/unallocated）。
- 补齐历史回填脚本，支持 dry-run/apply。
- 明确历史缺证据时归入 `unallocated`，不做伪精确分摊。
- 管理后台与 App/Web 日历口径完成对齐。

### Added
- 新表：`daily_snapshot_market_breakdowns`。
- 新接口：`GET /api/analysis/calendar/market_breakdown`。
- 新脚本：
  - `kona_tool/scripts/backfill_day_pnl_from_total_delta.py`
  - `kona_tool/scripts/backfill_market_breakdown.py`

### Changed
- 日历读取逻辑：`closed_at_snapshot` 由“直接归零条件”改为“仅阻止 backfill”。
- 快照写入逻辑：去掉“写入时全市场休市强制 day_pnl=0”的错误覆盖。
- 历史分市场回补改为“可证据优先 + 残差进 unallocated”。

### Fixed
- 修复 2026-02-17~2026-02-20 等交易日 `day_pnl=0` 错误。
- 修复“有 total_pnl 变化但日历看不到收益”的口径冲突。

### Ops / Deployment
- 生产执行回填脚本支持分批、幂等与范围控制。
- 已纳入备份/恢复流程前置校验。

### Data / Migration
- 需要执行回填脚本（先 dry-run 后 apply）。
- 历史数据回填可按用户/时间窗口分批处理。

### Verification
- 后端重点测试：
  - `test_calendar_weekend.py`
  - `test_api_baseline.py`
  - `test_market_calendar.py`
  - `test_market_breakdown.py`
- 线上验收：指定日期收益值与数据库一致。

### Notes
- 来源章节：旧 README §19、§3.13
- 关联文档：`docs/README_ANALYSIS_CALENDAR_MARKET_BREAKDOWN.md`

---

## v1.0.2 - 安全限流、监控告警与备份恢复
- 发布状态：Released
- 发布类型：Patch
- 范围：Backend | Infra | Docs

### Summary
- 认证链路加入限流与安全审计。
- 价格健康监控与告警体系上线。
- 数据库自动备份与一键恢复流程上线。
- 生产运行稳定性显著提升。

### Added
- 认证相关安全审计日志（登录、注册、改密、refresh、logout 等）。
- 价格健康接口：`GET /api/system/price_health`。
- 告警任务：服务探活、快照缺失、价格阈值异常。
- 备份脚本 + 恢复脚本 + 定时器任务。

### Changed
- 生产配置要求明确化（`JWT_SECRET`、Redis 限流存储、SMTP 告警参数等）。
- 运维流程从“人工巡检”升级为“定时巡检 + 告警”。

### Fixed
- 修复恢复脚本跨分区临时文件问题（`Errno 18`）。
- 降低服务异常后人工干预频率。

### Ops / Deployment
- `systemd` 服务 + timers 标准化上线。
- AWS 日志排障命令与恢复演练流程固化。

### Data / Migration
- None（不变更核心业务表结构）

### Verification
- 后端门禁测试通过。
- 告警任务日志检查通过。
- 备份生成/恢复演练通过。

### Notes
- 来源章节：旧 README §3.10~§3.12
- 关联文档：`docs/MAINTENANCE.md`、`docs/RUNBOOK.md`

---

## v1.0.1 - CI/CD 门禁与发布流程强化
- 发布状态：Released
- 发布类型：Patch
- 范围：Infra | Backend | Flutter | Web

### Summary
- 部署流程重构为“后端门禁 + 前端门禁 + 部署”三段式。
- `main` 分支发布前必须全门禁通过。
- PR 场景只做门禁，不自动部署。
- Web 产物发布加入 smoke 校验与失败回滚。

### Added
- GitHub Actions 分段门禁：`backend-gate`、`frontend-gate`、`deploy`。
- 前端门禁固定包含：`flutter analyze`、`flutter test`、`web build`。
- 部署后健康检查与关键路由 smoke。

### Changed
- 发布策略改为严格门禁，阻断“未通过测试直接上线”。
- APK smoke 构建按 Android 目录改动触发（默认跳过无关改动）。

### Fixed
- 修复“push 成功但门禁失败仍触发部署”的流程风险。
- 修复 Web 发布失败缺少可回退路径的问题。

### Ops / Deployment
- 明确 deploy secrets、分支策略、线上拉取约定。
- 形成“功能分支 -> main -> 自动部署”标准流程。

### Data / Migration
- None

### Verification
- GitHub Actions 全链路门禁执行通过。
- 部署阶段健康检查、路由 smoke 校验通过。

### Notes
- 来源章节：旧 README §3.9、§7.1~§7.1.3
- 关联文档：`docs/DEPLOYMENT.md`

---

## v1.0.0 - 初始稳定基线
- 发布状态：Released
- 发布类型：Major
- 范围：Flutter | Web | Backend | Infra | Docs

### Summary
- 建立完整的资产管理核心链路（资产、投资、分析、快讯、设置）。
- 建立认证体系（用户名/密码/邀请码）与会话保持能力。
- 建立快照统计口径（day/month/year/all）与多端展示能力。
- 建立后端服务托管与定时快照机制。
- 建立基础文档体系，支持新机器快速接手。

### Added
- Flutter 业务端主页面群（资产/投资/分析/快讯/设置）。
- Web 业务端、管理端、门户端基本能力。
- Flask API：资产、交易、分析、行情、新闻、认证等。
- SQLite 核心表：`users`、`portfolio`、`transactions`、`daily_snapshots`。

### Changed
- 登录与注册流程统一为用户名体系（替代邮箱验证码流程）。
- 累计收益口径固化：未实现收益 + 已实现收益（含 `adjustment` 承载）。
- 月/年/全部统计从“实时混算”过渡到“快照优先口径”。

### Fixed
- 修复主题切换、页面切换缓存、快讯加载与投资页展示等一批基础问题。
- 修复多端口径不一致导致的关键金额误读问题。

### Ops / Deployment
- 线上服务采用 `systemd + gunicorn` 托管。
- 快照定时由 `systemd timer` 固定触发。

### Data / Migration
- 初始表结构建立与历史数据承接完成。
- `portfolio` 清仓资产保留 `qty=0` 以维持累计收益口径连续性。

### Verification
- 基础 API 与前端端到端可用。
- 本地运行、部署链路、线上健康检查均可执行。

### Notes
- 来源章节：旧 README §1~§14、§3.1~§3.8、§15~§23（全量迁移归档）
- 关联文档：`README.md`、`docs/PROJECT_OVERVIEW.md`、`docs/STRUCTURE.md`
