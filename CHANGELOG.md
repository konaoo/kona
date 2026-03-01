# Changelog

本文件是项目版本历史的唯一标准记录。

- 版本起点：`v1.0.0`
- 默认迭代：`Patch`
- 大版本升级（`Minor`/`Major`）需你明确确认

---

## v1.0.18 - 腾讯云迁移与公网入口收敛（Nginx + Redis）
- 发布状态：Released
- 发布类型：Patch
- 范围：Infra | Backend | Flutter | Docs

### Summary
- 生产环境从 AWS 单机迁移到腾讯云轻量服务器（广州），线上入口统一为 `http://114.132.238.12`。
- 入口架构收敛为正式形态：`Nginx(80) -> Gunicorn(127.0.0.1:5003)`，业务端口 `5003` 不再对公网暴露。
- 修复迁移后登录 `500`：补齐 Redis 并恢复限流存储到本地 Redis。
- Flutter 客户端默认 API 地址切换至新公网入口。

### Added
- 腾讯云主机新增 systemd 服务：
  - `kona.service`
  - `nginx.service`
  - `redis.service`
- 新增迁移交接文档：
  - `docs/README_HANDOVER_2026_03_TENCENT_MIGRATION.md`

### Changed
- Gunicorn 监听地址从 `0.0.0.0:5003` 调整为 `127.0.0.1:5003`。
- Nginx 主配置改为默认反向代理站点，统一转发到 `127.0.0.1:5003`。
- `.env` 中限流存储恢复为 `RATELIMIT_STORAGE_URL=redis://127.0.0.1:6379/0`。
- Flutter `ApiConfig.baseUrl` 从旧 AWS 地址切换为新腾讯云地址。
- 运维文档统一收敛到当前生产入口：`docs/MAINTENANCE.md`、`docs/RUNBOOK.md`、`docs/API_IMPORT.md`、`docs/FRONTEND_SETUP.md`、`docs/PROJECT_OVERVIEW.md`、`docs/openapi.yaml`。

### Fixed
- 修复迁移后登录接口 `POST /api/auth/login` 返回 `500`（根因：Redis 未安装导致 Flask-Limiter 连接拒绝）。
- 修复 OpenCloudOS 默认 Nginx 站点抢占导致首页显示系统 404 的问题。

### Ops / Deployment
- 新服务器：`114.132.238.12`（广州）。
- 公网验收：
  - `GET /health` -> `200`
  - `GET /` -> 前端首页正常返回
  - `GET :5003/health` -> 公网不可达（符合“仅内网监听”预期）
- 腾讯云防火墙已放通 `80/22`；`5003` 已可删除/不再需要对公网放行。

### Data / Migration
- 已从旧机同步代码、`.env` 与 `portfolio.db` 至新机目录：
  - `/opt/kaka/portfolio`
  - `/opt/kaka/portfolio/kona_tool/.env`
  - `/opt/kaka/portfolio/kona_tool/portfolio.db`
- 注意：旧 AWS 停机前应确保无新增写入，避免新旧库分叉。

### Verification
- `curl -i http://114.132.238.12/health`
- `curl -i http://114.132.238.12/`
- `curl -i -H 'Content-Type: application/json' -d '{\"username\":\"kona\",\"password\":\"x\"}' http://114.132.238.12/api/auth/login`（应返回 401/业务错误，不应 500）
- `flutter test test/api_service_web_test.dart`

### Notes
- 当前线上入口仍为 IP，建议下一步接入域名 + HTTPS（443）并将 App 基地址改为域名，彻底摆脱 IP 迁移成本。

---

## v1.0.17 - 管理后台排序分页、活跃地区与首屏体验修复
- 发布状态：Released
- 发布类型：Patch
- 范围：Web | Backend | Flutter | Infra | Docs

### Summary
- 管理后台用户页完成服务端排序 + 分页统一，支持按最近活跃、总资产、注册时间降序查看。
- 管理后台时间展示统一北京时间，地区展示统一中文 `省-市`，并补齐历史回填链路。
- Web 管理端硬刷新黑屏问题修复，首屏增加加载占位与超时保护。
- 服务器完成最小扩容（2 worker + 预取降频 + 2GB swap），提升抗压能力。

### Added
- `GET /api/admin/users` 新增排序参数：`sort_by`、`sort_dir`。
- 用户页新增排序下拉与分页条（10/20/50/100）。
- 新增活跃地区字段链路：`last_active_ip`、`last_active_region`（管理后台展示）。
- 新增并执行地区回填脚本（按历史 IP 回填规范化地区）。

### Changed
- 用户页查询从固定 `limit=100` 改为服务端分页。
- 后端用户列表查询改为排序白名单，排序键进入缓存 key，避免串缓存。
- 地区显示策略统一：有值显示中文省市，无值显示 `未知`。
- Web 首屏按路径区分 boot 背景（门户/业务端/管理端），并增加 `auth/me` 启动超时保护。
- 线上 Gunicorn 从 `workers=1` 调整为 `workers=2`（threads 维持 4）；预取间隔上调为 300 秒。

### Fixed
- 修复管理后台用户页“单页拉全量”导致的查询和交互不稳定问题。
- 修复管理后台时间非北京时间、地区中英混杂及空值展示不统一问题。
- 修复管理端硬刷新时出现大面积黑页的首屏体验问题。

### Ops / Deployment
- 已推送 `main`：`cb935ed`、`5fb4a91`、`d1a9ec0` 等。
- 已完成线上部署与服务重启，回填生效。
- 已启用 swap（2GB）并写入 `/etc/fstab` 持久化。

### Data / Migration
- 用户表地区数据执行历史回填：
  - 可回填记录已更新到 `last_active_region`。
  - 无公网 IP 或不可解析记录保持 `未知`。

### Verification
- `cd /Users/kona/Desktop/kaka/kona_repo/kona_tool && .venv/bin/python -m unittest -q tests/test_admin_api_foundation.py`
- `cd /Users/kona/Desktop/kaka/kona_repo/web && npm run build`
- 线上抽样：
  - `/api/admin/users` 排序分页返回正确
  - 活跃地区字段返回并规范化
  - `/admin/users` 强刷不再纯黑屏

### Notes
- 当前服务器为 `t3.micro`，20 人同时高频刷新行情仍会出现高延迟与部分超时；建议下一步升配 `t3.small` 或 `t3.medium`。

---

## v1.0.16 - 资产分类规则收敛与美股ETF代码链路修复
- 发布状态：Released
- 发布类型：Patch
- 范围：Backend | Docs

### Summary
- 收敛资产分类口径，前端保持四类展示不变：`A股 / 美股 / 港股 / 基金`。
- 修复 `NUGT/QQQ/BOXX` 等美股 ETF 被错误识别为基金、导致价格链路异常的问题。
- 增加入库标准化与搜索过滤，阻断 `f_` 字母代码再次落库。

### Added
- 新增持仓标准化函数：统一处理 `code/curr/asset_type`，入库前强制标准化。
- 新增回归测试：
  - `test_infer_asset_type_us_etf_remains_us`
  - `test_search_filters_letter_prefixed_fund_codes`
  - `test_portfolio_add_invalid_f_prefix_letters_normalizes_to_us`

### Changed
- 资产类型推断规则：
  - `gb_` 统一按美股；
  - `f_` 仅纯数字按基金；
  - `sh/sz/bj`（含场内 ETF）统一按 A 股。
- 搜索结果过滤字母型 `f_` 代码（例如 `f_NUGT`、`f_BOXX`）。
- `portfolio/add` 与 `buy_with_cash` 统一走标准化入库逻辑。

### Fixed
- 修复美股 ETF 误入基金链路导致的“有持仓但价格为 0”问题。
- 修复历史脏数据 `f_` 字母代码导致的分类与币种错误。

### Ops / Deployment
- 代码已推送 `main`：`449dee0`。
- 后端已部署并重启：`kona` 服务 `active`。
- 线上已执行历史数据修复：`f_` 字母代码批量转 `gb_`（并修正 `curr=USD, asset_type=us`）。

### Data / Migration
- 已生成修复前备份：
  - `archive/backups/portfolio_pre_symbol_fix_20260228_030518.db`
- 已修复记录：2 条（`f_NUGT` -> `gb_nugt`）。

### Verification
- `cd /Users/kona/Desktop/kaka/kona_repo/kona_tool && .venv/bin/python -m unittest -q tests.test_market_code_normalization tests.test_search_timeout tests.test_api_baseline`
- `cd /Users/kona/Desktop/kaka/kona_repo/kona_tool && .venv/bin/python -m unittest -q tests.test_portfolio_schema_migration tests.test_portfolio_user_scope tests.test_search_timeout tests.test_market_code_normalization`
- 线上冒烟：
  - `GET /api/search?q=nugt` 返回仅 `gb_*` 美股结果
  - `get_price('gb_nugt')` 可取价，`f_NUGT` 不再作为有效入库代码

### Notes
- 业务规则固定：
  - A股：A股股票 + 场内基金（ETF/LOF/REITs）
  - 美股：美股股票 + 美股 ETF
  - 港股：港股股票 + 港股 ETF
  - 基金：仅场外基金（`f_` 纯数字）

---

## v1.0.15 - 跨端会话稳定性与门户下载体验修复
- 发布状态：Released
- 发布类型：Patch
- 范围：Flutter | Web | Backend | Docs

### Summary
- 修复同账号跨端使用时的会话稳定性问题：避免 token 过期后 App 出现“空数据假象”与 Web 端误登出。
- 完成门户 APK 下载链路落地：支持固定下载路由与本地 APK 回退。
- 优化门户首屏体验：修复强刷时先黑屏再渲染的问题；浏览器标题统一为产品名。

### Added
- 后端新增 `/download/apk` 固定下载路由。
- 新增后端鉴权回归测试：无效 Bearer token 访问 `optional_auth` 资源时返回 `401`。

### Changed
- `optional_auth` 策略调整：当请求携带失效/非法 token 时返回 `401`，不再静默降级为游客态。
- Flutter `ApiService` 新增 401 自动刷新会话与单次重放机制，并加入 refresh 并发锁。
- Web `refreshTokenIfNeeded` 新增并发互斥，避免并发刷新导致本地登录态被清空。
- 门户首屏增加预置背景（portal boot），减少强刷闪黑。

### Fixed
- 修复 App 在 access token 失效时偶发返回空资产列表的问题（根因：后端游客态回退）。
- 修复 Web 在并发请求触发 refresh 时可能被动退出登录的问题。
- 修复门户 APK 按钮“暂无提供”与下载链路不一致问题。
- 修复门户浏览器标签页标题仍显示 `web` 的问题。

### Ops / Deployment
- 本版本已推送 `main`，并完成线上 AWS 同步（后端服务重启 + Web 静态资源更新 + APK 文件上传）。

### Data / Migration
- None

### Verification
- `cd /Users/kona/Desktop/kaka/kona_repo/kona_tool && ./.venv/bin/python -m unittest tests.test_api_baseline -v`
- `cd /Users/kona/Desktop/kaka/kona_repo/flutter && flutter test test/auth_persistence_test.dart test/profile_page_test.dart test/app_settings_page_test.dart`
- `cd /Users/kona/Desktop/kaka/kona_repo/web && npm run build`
- 线上接口验证：
  - `GET /api/portfolio` + invalid bearer token 返回 `401`
  - `GET /download/apk` 返回 `200`

### Notes
- 保持“允许多端同时在线”策略：Web 与 App 不互踢，仅失效 token 会触发各端本地续期或重新登录。

---

## v1.0.14 - Flutter 个人中心与投资交互体验优化
- 发布状态：Released
- 发布类型：Patch
- 范围：Flutter | Docs

### Summary
- 个人中心与系统设置入口重构完成：`问题反馈` 从系统设置迁移到我的页面一级入口。
- 投资页交互体验优化：修复底部大面积留空，收敛尾部安全间距。
- 下拉刷新体验统一：保留顶部小动画，去除中部大 Loading，刷新时保持已有内容不闪白。

### Added
- Flutter 新增 `AppSettingsPage` 页面与设置项结构（主题、生物识别、改密、检查更新占位、关于我们、退出登录）。
- 个人中心新增 `问题反馈` 入口并支持外部浏览器拉起。
- 新增/更新 Widget 测试覆盖设置页与个人中心关键行为。

### Changed
- 投资页“添加资产/买入”账户选择弹窗改为更清晰的排版与字号层级，适配账户较多场景。
- 投资页底部内容预留高度收缩，减少滚动到底后的空白区域。
- 个人中心顶部名称规则保持“仅显示一行主标题（昵称优先，昵称为空回退用户名）”。

### Fixed
- 修复系统设置与我的页面反馈入口层级不一致的问题。
- 修复下拉刷新时“顶部+中部双 Loading”导致的打断体验问题。

### Ops / Deployment
- Flutter 改动已安装到 Android 真机验收，并同步推送到 `main`。

### Data / Migration
- None

### Verification
- `cd /Users/kona/Desktop/kaka/kona_repo/flutter && flutter test test/profile_page_test.dart test/app_settings_page_test.dart`
- `cd /Users/kona/Desktop/kaka/kona_repo/flutter && flutter run -d 3B15B400J3F00000 --no-resident`

### Notes
- 同步更新 Flutter 模块 README 与版本号，便于后续发布管理。

---

## v1.0.13 - 后端行情预取缓存（秒回优化）
- 发布状态：Released
- 发布类型：Minor
- 范围：Backend

### Summary
- 新增后台行情预取线程，每 30 秒自动批量拉取所有持仓证券的行情并写入内存缓存。
- API 请求始终命中热缓存，响应时间从 500ms~2s 降至 <50ms。

### Changed
- `price.py` 新增 `PricePreloader` 类（后台守护线程 + SQLite 代码收集 + 定时 `batch_get_prices`）。
- `config.py` 新增 `PRELOAD_INTERVAL_SECONDS` 配置项（默认 30 秒）。
- `app.py` 和 `wsgi.py` 启动时自动启动预取线程。

### Verification
- 重启后端后日志出现 `PricePreloader started`，之后 App 刷新时日志应全部为 `Cache hit`。

### Notes
- 可通过环境变量 `PRELOAD_INTERVAL_SECONDS` 调整预取间隔。

---

## v1.0.12 - 启动即时同步与排行汇率修正
- 发布状态：Released
- 发布类型：Patch
- 范围：Flutter

### Summary
- 修复 App 冷启动后数据不自动更新、需要手动下拉刷新的问题。
- 修复盈亏排行榜未做跨币种汇率换算的问题。

### Changed
- `main.dart` 中 `_startSyncTimer` 改为 `immediate: true`，App 启动后立即执行一次后台增量同步。
- `analysis_page.dart` 中两处 `_buildRankItems` 加入 `getCurrencyRate` 汇率换算，排行榜统一归一化为人民币比较。

### Fixed
- 修复冷启动后 120 秒内数据不同步的问题（SWR 模式生效延迟）。
- 修复跨币种持仓在盈亏排行中未按统一币种比较的问题。

### Ops / Deployment
- 本次改动直接推送到 `main`。

### Data / Migration
- None

### Verification
- 冷启动 App 后无需手动操作，2-3 秒后数据自动更新。

### Notes
- None

---
- 发布状态：Released
- 发布类型：Patch
- 范围：Backend

### Summary
- 修正了收益率（pnl_rate）的计算逻辑，分母优先使用期初本金（而非期末总本金），从根本上解决了当日追加投资（入金）导致当日收益率被严重稀释的 Bug。

### Added
- None

### Changed
- `kona_tool/core/db.py` 中的收益率统计：计算分母逻辑从使用当日期末总投入，修正为了优先使用期初本金（前序快照），并配以首日入金兜底机制。

### Fixed
- 修复加仓/入金现金流作为分母导致收益率计算畸变的问题（金融算法修正）。

### Ops / Deployment
- 本次改动直接推送到 `main`。

### Data / Migration
- None

### Verification
- 经代码逻辑推演，算法更符合真实盈亏比例。

### Notes
- 核心补丁由用户直接编写并提供，质量极高。

---
- 发布状态：Released
- 发布类型：Patch
- 范围：Flutter | Backend

### Summary
- 新增“外部资金/初始转入”选项，支持无现金账户下的投资填报或划转。
- 优化 Flutter 端添加资产时的股票代码搜索：降低搜索频率、防竞态刷新，提升 UI 流畅度。
- 后端股票搜索逻辑增加精确匹配优先排序算法。
- 客户端持仓界面搜素结果的市场类型标签替换为纯中文标识（A股/美股/港股/基金）。

### Added
- Flutter 端投资界面的资金源下拉列表在非“卖出”动作下自动内置 `id: -999` 的“外部资金 / 初始转入”选项，免去强制添加现金账户限制。
- AppState 的购买/卖出操作内部适配 `-999` 的静默跳过（降级为单纯记录购买）。
- Backend（`price.py`）针对搜索关键词的完全匹配（忽略特定后缀后匹配代码及拼音前缀等）添加了置顶排序权重。

### Changed
- Flutter 投资搜索栏防抖时间从 300ms 提高到 800ms。
- 搜索防抖触发加入严格上下文守卫：若文字框已被清空，立级取消计时器并不渲染过期到达的网络层请求。
- Flutter 层面市场类型的显示标取代原英文字母缩写。

### Fixed
- 修复搜索延时回调导致的 UI（清空后依然展示幽灵搜索结果）竞态 Bug。
- 修复买入与添加记录时不规范传入 `-999` ID 导致的 Validator 验证拦截 Bug。

### Ops / Deployment
- 本次改动直接推送到 `main`。

### Data / Migration
- None

### Verification
- AAPL 精准匹配测试与 APP 搜索狂划/狂删体验验证完成。

### Notes
- None

---
- 发布状态：Released
- 发布类型：Patch
- 范围：Flutter | Docs

### Summary
- App 端实现了基于本地生物识别的锁屏保护（冷启动与后台唤醒）。
- 端侧登录页视觉重构：新增独立动画、密码明暗文切换、错误反馈动效。
- 登录页新增“记住用户名”可选能力。
- 修复并优化了生物识别按钮及其周边元素的视觉间距。
- 修改了邀请码获取引导外部跳转链接为小红书地址。

### Added
- `AppState` 配置新增了 `isAppLocked` 全局锁屏控制变量。
- 登录界面的入场、震动报错与成功提示打钩三大辅助动画体系。

### Changed
- 调整了指纹登录的大图标渲染尺寸（26px）及关联上下文间距。
- `api_config.dart` 中的 `inviteAcquireUrl` 改为小红书外链。

### Fixed
- 修复了旧版 iOS 模拟器因为 UI 空间过窄导致的生物识别不明显问题。

### Ops / Deployment
- 本次改动直接推送到 `main`。

### Data / Migration
- None

### Verification
- iOS 模拟器/真机冷启与登录页相关行为验证完毕。

### Notes
- 核心修改文件涵盖 `main.dart`（全局监听）、`login_page.dart` 和 `api_config.dart`。

---

## v1.0.8 - Web 门户/认证改版、主题体系与投资分析隐私工具统一
- 发布状态：Released
- 发布类型：Patch
- 范围：Web | Docs

### Summary
- Web 门户首页整体替换为新视觉（品牌、主标题、双按钮与产品展示区），并保持 APK 动态下载配置可用。
- 登录/注册页改为同风格单卡布局，完善返回交互、记住我、注册链接与中文错误提示。
- `/app/*` 新增深浅主题切换体系（默认深色），主题状态本地持久化并跨页面保持一致。
- 首页顶部操作区统一为图标按钮，视觉回退并还原到你确认的 1:1 版本。
- 投资页浅色主题完成统一收敛，去除当日/累计盈亏胶囊感，表格风格与浅色体系一致。
- `home/invest/analysis` 引入缓存优先 + 后台刷新（SWR）与请求去重，显著降低 F5 重复请求。
- 投资页与分析页新增顶部工具行（隐藏金额 + 拍照），并与首页共用隐私状态，支持“隐藏金额保留百分比”。

### Added
- 新增共享隐私模块：`web/src/shared/privacyMode.ts`（`privacy_mode` 持久化、跨标签同步、统一掩码函数）。
- 新增全局 store 持久化缓存结构：`web_store_cache_v1`（`portfolio/quotes/rates/marketStatus/quotePolicy` 等）。
- `/app/invest` 与 `/app/analysis` 新增页面级截图能力（仅截主内容区域，不含侧边栏）。
- 首页新增主题按钮 + 隐私按钮 + 截图按钮的固定工具行。

### Changed
- 门户页：改为新 Hero 结构与风格，Logo 资源从仓库静态资源引用。
- 认证页：拆分路由（`/app/login` + `/app/register`），移除顶部胶囊切换。
- 登录流程：去除登录成功后的阻塞式全量刷新，先进入业务页再后台刷新。
- 自动刷新策略：`startAutoRefresh` 不再 0ms 立即触发，避免首屏阶段与手动刷新并发打接口。
- 首页投资模块：移除右上角三张“今日/持仓/累计盈亏”统计小卡。
- 投资页浅色模式：整体卡片、表头、行 hover、数值层级按统一视觉规则重排。

### Fixed
- 修复 `/app/home` 在浅色主题下多轮样式尝试导致的页面错位/空白问题，并最终回退到确认版本。
- 修复 F5 后首页/投资页首屏重复触发 bootstrap 与静态请求的问题。
- 修复登录错误文案出现英文 raw message 的问题（如 `Invalid username or password`）。
- 修复注册场景缺少确认密码与邀请码必填中文提示的问题。
- 修复投资页与分析页缺少统一隐私工具入口的问题。

### Ops / Deployment
- 全部改动按 Web 直推规则发布到 `main`，无需后端迁移。
- 推送波次覆盖提交：`bc1a0a8` → `681ecbf`（含中间回退提交）。

### Data / Migration
- None（无数据库迁移）

### Verification
- `cd /Users/kona/Desktop/kaka/kona_repo/web && npm run build`（通过）
- 页面验收路径：
  - `/` 门户视觉与按钮
  - `/app/login`、`/app/register` 登录注册链路
  - `/app/home` 主题切换与顶部工具按钮
  - `/app/invest` 浅色风格与隐私/截图按钮
  - `/app/analysis` 隐私/截图按钮与金额掩码

### Notes
- 本版本为当天 Web 多轮迭代的收敛版本，文档按“上线波次”合并记录，不按单 commit 拆分。
- 关联文档：`docs/README_WEB_CHANGELOG_TIMELINE.md`

---

## v1.0.7 - Web 登录注册体验与中文错误提示完善
- 发布状态：Released
- 发布类型：Patch
- 范围：Web | Docs

### Summary
- Web 认证页拆分为独立登录/注册路由（`/app/login`、`/app/register`），去除顶部胶囊切换。
- 登录页交互改版：左上角返回箭头、顶部品牌“咔咔记账”、注册引导文案优化。
- 登录支持“记住我”本地回填（仅登录模式写入），注册流程明确不保存登录信息。
- 注册页新增“确认密码”输入与前端先验校验，减少无效请求。
- 登录和注册错误提示统一中文化，避免英文 raw 错误直接暴露给用户。
- 登录成功链路移除阻塞式全量刷新，显著缩短点击“登录”到进入首页的等待时长。

### Added
- 新增独立注册路由：`/app/register`（复用认证页组件，注册模式展示邀请码与确认密码）。
- 注册模式新增字段：`confirmPassword`（确认密码）。
- 新增注册前端校验规则：
  - 用户名格式校验（小写字母开头，4-24 位，仅小写/数字/下划线）。
  - 密码规则校验（8-64 位，且同时包含字母和数字）。
  - 两次密码一致性校验。
  - 邀请码必填校验。

### Changed
- 认证页布局由“信息区+表单区”改为单卡片聚焦表单布局。
- 登录页底部文案改为“还没有账户？立即注册”，仅“立即注册”可点击跳转。
- 认证页返回逻辑固定为：优先 `router.back()`，无历史回退时跳转 `/`。
- 登录分支错误处理改为中文映射展示；注册分支保持中文映射并补齐空邀请码文案“请填写邀请码”。
- 登录成功流程调整为直接跳转首页，不再等待 `store.refreshAll()` 完成。

### Fixed
- 修复登录失败时仍显示英文文案（如 `Invalid username or password`）的问题。
- 修复注册缺少确认密码校验导致可提交不一致密码的问题。
- 修复注册场景对“邀请码为空/无效”缺乏明确中文提示的问题。
- 修复登录按钮“提交中”等待时间过长（受同步全量刷新阻塞）的问题。

### Ops / Deployment
- 变更按 Web 直推规则发布到 `main`。
- 未引入后端接口与数据库变更，无需额外部署迁移步骤。

### Data / Migration
- None（无数据库迁移）

### Verification
- `cd /Users/kona/Desktop/kaka/kona_repo/web && npm run build`（通过）
- 手工验收：
  - `/app/login`：记住我、中文错误提示、返回箭头、注册链接
  - `/app/register`：确认密码、邀请码必填、中文错误提示
  - 已登录访问 `/app/login` 与 `/app/register` 都会跳转 `/app/home`

### Notes
- 主要来源提交：`b490a51`、`022fe2d`、`feef3ab`、`6ecdecd`
- 文档规则保持：`CHANGELOG.md` 为唯一版本历史标准，`README.md` 仅保留摘要导航

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
