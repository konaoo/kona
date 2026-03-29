## 说明

这份 [CHANGELOG.md](/Users/kona/Desktop/kaka/kona_repo/CHANGELOG.md) 以后默认只保留近期变更记录。

要点只有 3 条：

1. 这里记录的是“开发变更”，不是 Flutter 安装包真实版本号
2. 开发变更记录默认使用 `YYYY-MM-DD-序号`
3. 更早的历史记录统一归档到 [archive/changelog/2026-03.md](/Users/kona/Desktop/kaka/kona_repo/archive/changelog/2026-03.md) 这类文件里

也就是说：

- `2026-03-28-02` 这种编号，表示当天第 2 次正式变更记录
- `1.0.29` 这种编号，才是客户端正式发版版本

历史里已经出现的 `v1.0.x / v1.4.x` 条目先保留，不回头重写；但从规则上说，以后不再把 `CHANGELOG` 当客户端版本号来用。

## 2026-03-29-02

### 这版一句话
修掉了主干 CI 里分析页统一接口的时间源漂移问题，并把 Android 桌面图标正式收成自适应图标，解决手机端外层白壳。

### 主要变化
- **后端：分析页统一接口时间源对齐**：更新 `core/analysis_screen_service.py`，`today_status` 和日历 today 覆盖逻辑不再偷偷直接吃系统当前时间，而是优先跟分析链现有的时间源保持一致；这样测试里 patch 的 `_get_datetime_now` 会真正影响 `analysis/screen`，避免同一天数据被误判成 `pending`。
- **CI：后端门禁恢复**：本地按 GitHub Actions 同款命令重跑 `python -m unittest discover -s kona_tool/tests -p "test_*.py" -v`，`407` 条后端测试已全绿。
- **Android：桌面图标改成自适应图标**：新增 `mipmap-anydpi-v26/ic_launcher*.xml`、前景层 `ic_launcher_foreground.png` 和背景色配置，Manifest 同步补 `roundIcon`，让安卓桌面直接使用深色背景 + 幽灵前景，不再被系统额外套一层白底壳。

### 影响范围
- 后端：`/api/analysis/screen` 的 `today_status` 与 today 覆盖逻辑
- Android：桌面安装图标显示方式

### 验收重点
- GitHub Actions 的 `Backend Gate (Python 3.10/3.11)` 应恢复绿色，不再卡在 `test_analysis_screen_returns_unified_payload`。
- Android 手机重新安装新 APK 后，桌面图标外面不应再出现系统自动加的白色底壳。

## 2026-03-29-01

### 这版一句话
收了 App 端“检查更新”弹窗和登录页这一轮验收修改，让更新弹窗更完整、登录页更轻，同时把版本记录规则和归档入口一起理顺。

### 主要变化
- **App：检查更新弹窗重做**：新增专用更新弹窗组件，改成 H5 风格的插画布局；去掉底部“稍后再说”，改成右上角关闭按钮，并更新提示文案。
- **App：登录页减重重做**：登录页去掉中间卡片、logo 和厚胶囊切换，改成整页承载；顶部品牌区调整为“咔咔记账 + 很高兴见到你。”，并按验收反馈多次收口字号、位置、切换区对齐和顶部渐变。
- **App：登录页交互细节修复**：修复注册态内容可能顶住顶部品牌文案的问题，给品牌区预留安全空间；登录/注册切换最终恢复居中，品牌字独立放在页面左上区域。
- **App / Web：统一 logo 资源**：把 App 端和 Web 端显式使用 logo 的位置统一切到 `flutter/assets/images/logo.png`，同步替换 Web 公共资源、Flutter 页面 logo，以及 Android / iOS / macOS / Flutter Web 的安装图标与站点图标。
- **App：关于页深色模式 logo 收口**：关于页不再继续直接缩放通用透明 logo，而是改成按亮色 / 深色背景分别使用专用图；深色模式额外补一张小尺寸专用资源，解决深色底下边缘发白、锯齿明显的问题。
- **文档：版本记录规则收口**：补充并整理版本记录规范，新增 `archive/changelog/README.md` 和 `archive/changelog/2026-03.md`，把根 `CHANGELOG.md` 收成近期入口。

### 影响范围
- Flutter：`我的 -> 检查更新` 弹窗、登录页
- Flutter / Web：logo 资源与相关引用、关于页 logo 显示
- 文档：`CHANGELOG.md`、`版本记录规范.md`、`archive/changelog/`

### 验收重点
- “我的 -> 检查更新”弹窗应为新样式，只保留“立即升级”和右上角关闭按钮。
- 登录页应为轻量整页结构，顶部只有渐变和品牌字，不再出现旧 logo、旧卡片和厚胶囊切换。
- 切到注册时，顶部品牌文案不应再被挡住。
- 关于页 logo 在亮色和深色模式下都应使用新图，深色模式下不应再出现明显白边和锯齿。

## 2026-03-28-02

### 这版一句话
把后端“检查更新”返回的客户端最新版版本号提升到 `1.0.29`，让当前安装旧版客户端时能正常弹出更新提示。

### 主要变化
- **后端：客户端更新版本号上调**：更新 [kona_tool/config.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/config.py)，将 `CLIENT_APP_VERSION` 的默认值从 `1.0.24` 提升到 `1.0.29`，对应默认 `buildNumber` 也会按版本号尾段自动变为 `29`。
- **行为保持不变**：本次只改 `/api/app/version` 返回的“最新版客户端版本”，不改 Flutter 安装包本身的 `pubspec` 版本号，不改下载地址，不改强制更新开关。

### 影响范围
- 后端：`/api/app/version`
- Flutter / Web：凡是调用“检查更新”的客户端入口

### 验收重点
- 调用 `/api/app/version` 时，返回的 `version` 应为 `1.0.29`，`buildNumber` 应为 `29`。
- 已安装旧版客户端点击“检查更新”时，应能识别出有新版本并弹出更新提示。

## 2026-03-28-01

### 这版一句话
把分析页收成“后端统一单屏数据 + 前端纯展示”的主链路，并把晚到净值回填从局部补丁改成按有效日整天覆盖，减少分析页口径打架和未归因脏数据反复出现。

### 主要变化
- **后端：新增分析页统一读模型接口**：新增 `analysis_screen_service.py`，提供 `/api/analysis/screen`；后端统一产出概览、日历、排行和 `realtime_today`，不再让 Web / App 各自二次拼 today、calendar 和 summary。
- **Web / Flutter：分析页切到统一接口主链路**：Web 状态层和 Flutter 分析页改为直接消费统一 screen payload，保留旧缓存兼容读取，但不再继续各自拼装“今天这格”和底部汇总，减少切账本、切周期、自动刷新时的数据打架。
- **后端：收生产快照回填链路**：`snapshot.py` 里的 `late settlement` 不再按 market 做 partial update，而是先读出受影响日期的现有整天结果，只替换这次晚到的市场，再整天覆盖写回 market / asset breakdown，并同步主快照 `day_pnl`。
- **测试补齐**：补了统一分析页接口与快照回填的回归测试，锁住“今天格子与汇总同口径”“账本级也走整天覆盖”“生产路径不再写 partial breakdown”。

### 影响范围
- 后端：分析页读侧接口、快照落库、账本级历史回填
- Web：分析页状态层与日历展示
- Flutter：分析页数据加载、缓存兼容与实时 today 展示

### 验收重点
- 分析页同一屏里的顶部概览、日历今天这格、底部汇总应来自同一套主链路，不再前后打架。
- 场外基金 / 海外市场晚到净值回填后，历史有效日应整天更新，不再只补某个市场导致出现未归因或半新半旧。
- 切账本、切周期、重新进入分析页时，Web 和 App 都不应再出现旧请求把新状态盖回去的明显现象。

## 2026-03-27-06

### 这版一句话
收敛了 App 多处展示细节，并修复 `gb_boxx` 等美股代码误走基金链路导致累计盈亏显示异常的问题。

### 主要变化
- **App 端展示微调（Flutter）**：投资页搜索选中卡片改为两行结构并保留“分类胶囊 + 代码”；分析页日历金额字号、年月选择器、本月盈亏卡和区块间距按验收反馈收紧；快讯页分类切换改为“文字 + 下划线”样式（去胶囊），并缩小“市场快讯”标题字号。
- **App 投资页底部空白优化**：投资页底部预留由“底栏高度 + FAB 区域”改为“安全区 + 小缓冲”，减少少持仓场景下的大块空白。
- **后端美股取价链路修复**：`get_stock_price` 中 `gb_` 前缀不再误入 ISIN 基金链路；`get_us_stock_price` 在常规源失败后统一补一轮 relaxed Nasdaq 兜底，恢复 `BOXX` 等美股 ETF 取价。
- **测试与依赖补齐**：`test_stock_source_order.py` 新增 `gb_` 路由与 relaxed Nasdaq 回归用例；`requirements.txt` 增加 `akshare==1.18.47`（用于行情探索与验证）。

### 影响范围
- Flutter：投资页、分析页、快讯页
- Web：投资交易弹窗（选中资产卡片展示）
- 后端：`kona_tool/core/stock.py` 取价路由与兜底链路
- 测试/依赖：`kona_tool/tests/test_stock_source_order.py`、`kona_tool/requirements.txt`

### 验收重点
- `kona` 用户的 `gb_boxx` 在投资页应恢复有效实时价格与累计盈亏（不再显示 `--`）。
- 快讯页分类切换应为“下划线高亮”风格，且不再出现胶囊背景。
- 分析页“当日/本月/本年/全部”下方到收益日历的空白应明显收紧；投资页底部空白应明显减少。

## 2026-03-27-05 (v1.4.4)

### 这版一句话
上线了卢森堡（LU）及全球基金名称的“中文化引擎”，支持自动将英文基金名翻译为地道的简体中文。

### 主要变化
- **后端：基金名定位中文化**：新增 `localization.py` 本地化引擎。通过内置的顶级基金公司（Allianz, BlackRock 等）、投资策略（Income, Growth 等）及份额类别（Class AM, USD 等）的翻译词典，结合正向规则匹配，将原始英文名转化为用户更易理解的中文名称。
- **集成：全链路生效**：更新了 `get_ft_metadata` 和 `search_stocks` 逻辑，确保从搜索预览到持仓详情，所有 ISIN 资产均以中文名称显示。
- **优化：展示细节改进**：自动清理了名称中的冗余词汇（如 Global Investors），并统一了空格与连接符的处理。

### 影响范围
- 后端：本地化引擎 (`localization.py`)、行情元数据 (`stock.py`)、搜索接口 (`price.py`)

### 验收重点
- 搜索 `LU0820561818`，结果应显示为 **“安联收益成长AM美元”** 而非英文长名。

## 2026-03-27-04

### 这版一句话
修复了 ISIN 资产搜索预览价格缺失（显示 `--`）的问题，通过接入 BlackRock 等多源价格兜底链路提升了搜索结果的鲁棒性。

### 主要变化
- **后端：搜索预览价格补全**：在 `search_stocks` 中增加异步价格获取失败后的同步兜底方案。当 ISIN 资产的 FT 元数据抓取因环境封禁失败时，自动调用 `get_stock_price`（优先走 BlackRock 链路）补全搜索框中的价格预览。
- **稳定性：环境兼容性优化**：通过复用已标准化的行情获取链路，解决了线上服务器与本地开发环境在 ISIN 数据抓取上的表现差异。

### 影响范围
- 后端：搜索接口核心逻辑 (`price.py`)

### 验收重点
- 在“添加资产”弹窗中搜索 `LU0820561818`，应能即时显示净值（如 8.17）而非 `--`。

## 2026-03-27-03

### 这版一句话
完成了卢森堡基金（LU）及全球资产的价格接口标准化，统一返回包含“净值日期”的 5 元组格式，并修复了 CI 挂掉的遗留断言问题。

### 主要变化
- **后端：价格接口 5 元组标准化**：更新了 `get_fund_price` 及所有子源函数（天天、东财、腾讯、FT、BlackRock 等），统一返回 `(price, yclose, amt, pct, nav_date)`。
- **后端：资产类型识别修复**：修正了 `infer_asset_type` 对 `f_` 前缀的过度匹配问题，确保 `f_NUGT` 等美股标杆资产被正确识别为 US 股票而非基金。
- **后端：数据源优先级调整**：在 `get_stock_price` 中将 BlackRock（官方源）权重提升至 Financial Times（聚合源）之前，确保 LU 基金数据的权威性。
- **基础设施：API 响应升级**：`quote_handlers.py` 现在会从 5 元组中提取 `nav_date` 并通过 JSON 响应下发，支持前端显示。
- **测试：全量 CI 适配与断言修复**：修复了 10+ 个测试文件中的解包错误（IndexError/ValueError）以及 Mock 调用次数断言错误，确保 395 个测试用例全量通过。

### 影响范围
- 后端：价格抓取核心 (`fund.py`, `stock.py`)、API 处理层 (`quote_handlers.py`)、资产识别 (`asset_type.py`)
- 测试：全量后端单元测试

### 验收重点
- `pytest kona_tool/tests` 应返回全量通过（395 passed）。
- 卢森堡基金（如 LU0582531332）的 API 响应中应包含 `nav_date` 字段。
- `f_NUGT` 资产应被识别为 `us` 市场。

## 2026-03-27-02

### 这版一句话
标准化卢森堡及境外基金（LU）净值日期显示逻辑，统一 Web 投资页卡片尺寸，并优化持仓资产分布与搜索 UI 的细节表现。

### 主要变化
- **后端：贝莱德基金日期标准化与价格提取**：更新 [kona_tool/core/stock.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/stock.py)，为卢森堡系列场外基金补全“净值截至日期”解析逻辑；[kona_tool/core/fund.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/fund.py) 同步支持 `YYYY年M月D日` 中文日期格式的正则解析。
- **前端：场外基金保守显示策略**：在 [web/src/pages/app/AppInvestPage.vue](/Users/kona/Desktop/kaka/kona_repo/web/src/pages/app/AppInvestPage.vue)、[AppHomePage.vue](/Users/kona/Desktop/kaka/kona_repo/web/src/pages/app/AppHomePage.vue) 和 [AppAssetDetailPage.vue](/Users/kona/Desktop/kaka/kona_repo/web/src/pages/app/AppAssetDetailPage.vue) 中联动：若基金未抓取到有效净值日期，自动将当日盈亏置灰（显示 `--`），防止时效性误导。
- **前端：投资页样式对齐与图表修复**：
    - 将投资分析页持仓卡片布局（`min-width: 280px`、`gap: 10px`）及视觉材质同步至首页规格。
    - 修正资产分布占比分母，并彻底解决 SVG Donut 图在占比 100% 时的渲染崩溃问题。
- **前端：搜索与弹窗 UI 细节优化**：
    - 更新 [web/src/components/business/InvestTradeModal.vue](/Users/kona/Desktop/kaka/kona_repo/web/src/components/business/InvestTradeModal.vue)，对搜索结果中的资产名称进行字数限制并增加提示，修正搜索结果列表的对齐方式。
- **后端：行情抓取鲁棒性提升**：更新 [kona_tool/core/price.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/price.py)，优化了汇率缓存及行情合并逻辑，增强了外部源异常时的稳定性。

### 影响范围
- Web：首页、投资页、资产详情页、交易弹窗
- 后端：基金价格抓取管道与日期系统
- Flutter：首页及分析页收益显示逻辑对齐

### 验收重点
- 卢森堡基金（如 LU0582531332）应正确带出净值日期，无日期资产的当日盈亏应恒为 `--`。
- 只有一种资产时，投资页占比图呈现为完整的圆形。
- 投资页卡片尺寸、间距、材质感官与首页完全一致。

## 2026-03-27-01

### 这版一句话
修正了分析页收益日历“盘前把前一交易日实时值继续写进昨天格子”的口径错误，今天没开盘时现在固定显示今天 `0`，不再污染历史格子。

### 主要变化
- **today 实时归属日锁回当前自然日**：更新 [kona_tool/core/snapshot.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/snapshot.py)，实时展示口径不再取“最后一个非 0 的有效收益日”，而是固定认当前自然日；如果今天还没有有效收益，直接返回 `0`，不再拿上一交易日顶上来。
- **补回归测试**：更新 [kona_tool/tests/test_api_baseline.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_api_baseline.py)，覆盖“隔夜美股收益仍归前一交易日，但 today 展示不得继续把前一天收益冒充今天”这类场景。
- **线上已同步修复**：已将后端修复发布到腾讯云并重启 `kona` 服务，`kona` 用户在 `2026-03-27` 早上盘前的收益日历现在恢复为 `3-26 = -1006.9`、`3-27 = 0.0`。

### 影响范围
- 后端实时 today 收益口径
- Web / Flutter 分析页日历当月实时替换逻辑

### 验收重点
- 北京时间盘前，如果当天还没有新的有效收益，收益日历今天这一格应显示 `0`，不能继续改写昨天的历史格子。
- `kona` 在 `2026-03-27` 早上查看 2026 年 3 月日历时，`3-26` 应保持历史快照值，`3-27` 应为 `0`。
