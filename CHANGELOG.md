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

## 2026-04-14-01

### 这版一句话
Web 端补齐账本（Ledger）功能，支持账本切换、新增、重命名、删除、排序，与 App 端对齐。

### 主要变化
- **账本选择器**：投资页顶部新增账本切换下拉菜单，显示所有账本、默认标记、当前选中
- **切换账本刷新数据**：选择账本后自动刷新持仓、实时盈亏、趋势等数据
- **账本管理弹窗**：支持新增账本、重命名、删除（默认账本不可删）、上下移排序
- **添加资产关联账本**：通过 InvestTradeModal 添加资产时自动传入当前账本 ID
- **登录/启动自动加载**：session bootstrap 和 login 后自动加载账本列表

### 涉及文件
| 文件 | 改动 |
|------|------|
| `web/src/stores/ledgerScope.ts` | 扩展为完整 CRUD store |
| `web/src/stores/sessionCoordinator.ts` | bootstrap/login 后加载账本 |
| `web/src/components/business/LedgerManageModal.vue` | 新增账本管理弹窗 |
| `web/src/components/index.ts` | 注册新组件 |
| `web/src/components/business/InvestTradeModal.vue` | 添加资产时传 ledger_id |
| `web/src/pages/app/AppInvestPage.vue` | 账本选择器 UI + 切换刷新逻辑 |

### 影响范围
- Web：投资页、分析页（已有 ledger_id 透传，无需额外改动）
- 不改后端，不改数据库

### 验收重点
- 投资页顶部显示当前账本名，点击可切换
- 切换账本后持仓列表和盈亏数据刷新
- "管理账本"弹窗中可新增、重命名、删除、排序
- 默认账本不可删除
- 添加新资产归属当前选中账本

## 2026-04-12-02

### 这版一句话
Web 端持仓卡片的当日盈亏和累计盈亏改为显示原始币种整数金额，与 App 端对齐。

### 主要变化
- **金额改为正整数显示**：持仓卡片中的当日盈亏和累计盈亏不再显示小数，统一取整
- **显示原始币种**：美股显示 `$`、港股显示 `HK$`、A股/基金显示 `¥`，不再强制转换为人民币
- **与 App 端保持一致**：格式对齐 App 的 `_fmtPnl` 逻辑（正负号 + 币种符号 + 整数金额）
- **汇总区域不受影响**：页面顶部的汇总盈亏仍以全局显示币种展示

### 影响范围
- Web：投资页持仓卡片的"当日盈亏"和"累计盈亏"金额展示
- 不改后端，不改数据

### 验收重点
- 持有美股资产时，持仓卡片的盈亏应显示 `+$123` 或 `-$45`，不显示小数
- 持有港股资产时，应显示 `+HK$123`
- A 股/基金应显示 `+¥123`
- 盈亏为 0 时显示 `--`
- 页面顶部的汇总数字仍正常显示

## 2026-04-12-01

### 这版一句话
支持做空记账：通过"外部资金"添加负数量的持仓，系统自动反转盈亏方向。

### 主要变化
- **添加资产支持负数量**：选择"外部资金/初始转入"时，数量可以填负数，表示空头持仓（如 -100 股）
- **盈亏自动反转**：空头持仓的浮动盈亏、日收益方向自动反转——标的下跌时显示赚钱，上涨时显示亏钱
- **调整数量支持负数**：可以通过"调整数量"将持仓改为负数（转空头），或从负数调回正数（平仓翻多）
- **现金账户不受影响**：选择现金账户买入时，仍要求数量和价格大于 0，避免现金余额异常
- **快照和分析页正确处理空头**：空头持仓的日收益正常写入快照，分析页能正确展示

### 影响范围
- App + Web：添加资产弹窗、调整数量操作
- 后端：`/api/portfolio/add`、`/api/portfolio/modify`、`/api/portfolio/update` 接口
- 快照计算：`snapshot.py`、`portfolio_metrics.py`
- 数据库查询：持仓列表不再过滤负数量记录
- 不改数据库结构

### 验收重点
- 选"外部资金"添加一个数量为 -100、成本价为 50 的资产，应能正常保存和显示
- 该空头持仓在标的下跌时应显示正收益，上涨时显示负收益
- 选现金账户时输入负数量，应被拦截提示
- 已有的多头持仓功能完全不受影响
- 对已有多头持仓的资产，不能直接添加负数量（会提示"已有多头持仓"）
- 空头持仓可以正常调整成本价和数量

## 2026-04-10-02

### 这版一句话
添加资产和调整成本价现在支持负数，适用于已回本或分红超过本金的持仓场景。

### 主要变化
- **添加资产支持负成本和零成本**：之前添加资产时成本价必须大于 0，现在允许输入负数或零
- **调整成本价支持负数**：之前调整成本价也必须大于 0，现在放开限制
- **买入和卖出不受影响**：交易价格仍然要求大于 0，符合实际交易逻辑
- App 端和 Web 端同步修改，行为一致
- **修复输入框限制**：Web 端价格输入框移除 `min=0` 限制，App 端调整成本价键盘改为允许负号输入
- **现金账户买入仍要求正成本**：从现金账户买入时需要扣款，负成本会导致现金反增，因此保持 price > 0 限制。只有选择"外部资金/初始转入"时才允许负成本

### 影响范围
- App：投资交易弹窗的"添加资产"和"调整成本价"操作
- Web：投资交易弹窗的"添加资产"和"调整成本价"操作
- 后端：`/api/portfolio/add` 接口放开 price 正数限制
- 不改数据库结构，不影响快照、分析等下游计算

### 验收重点
- 添加一个成本为负数的资产（如 -5），应能正常保存并显示
- 调整已有资产的成本价为负数，应能正常保存
- 买入和卖出时输入负数价格，应仍然被拦截提示错误
- 总收益率在总成本为负或零时显示 0%，属于正常退化

## 2026-04-10-01

### 这版一句话
根治分析页"未归因收益"反复出现的问题，从写入、计算、展示三个层面彻底修复数据不一致。

### 主要变化
- **分析页不再频繁出现"未归因收益"**：之前多账本架构下，逐资产明细没有汇总到全局表，导致分析页读不到个股数据，整天收益都变成"未归因"。现在写入快照时会自动聚合各账本的逐资产数据到全局表
- **盘前时段个股明细和市场总额对齐了**：之前盘前调整只挪了市场维度的日期，没挪个股维度，导致同一天的市场总额和个股明细对不上。现在两边同步调整
- **消除了四舍五入导致的几分钱偏差**：20只股票各自四舍五入后求和，可能和总额差几分钱。现在写入时会自动分摊尾差，确保个股之和等于市场总额
- **即使写入侧有残余偏差，分析页也不会再暴露给用户**：读取时如果个股之和与总额有微小差异，不再生成"未归因收益"条目，改为后台记录日志供排查。只有完全没有个股数据时才显示"未归因"（代表真正的系统故障）
- **历史数据已修复**：线上 3/30 至 4/9 的全局逐资产数据已从账本表回填

### 影响范围
- 分析页：逐资产收益明细展示（日历点击详情、区间汇总）
- 后端快照写入逻辑（`snapshot.py`）
- 后端分析数据读取逻辑（`analysis_asset_breakdown_service.py`）
- 不改数据库结构，不改 API 响应格式

### 验收重点
- 分析页日历点进去，每天的逐资产明细之和应等于当日总收益，不应再出现"未归因收益"
- 盘前时段（A股/港股/基金开盘前）查看分析页，数据应正常，不出现日期错位
- 历史日期（如2月份）的分析数据应正常显示，总收益金额不应为零
- 部署后连续观察 3 天，确认不再出现"未归因收益"

## 2026-04-09-01

### 这版一句话
修复 App 删除基金资产时黑屏、且重新添加后旧交易记录还在的问题。

### 主要变化
- **删除改为彻底清理**：删除投资资产时改用 corrective 模式，同时清理持仓记录、交易记录、调整记录和受影响的每日快照，不再只删持仓而留下孤立数据
- **修复删除黑屏**：增加删除进行中标志位，防止乐观更新触发的自动返回和手动返回冲突导致双重 pop 黑屏
- **删除失败不再误跳转**：原来删除失败也会跳走，现在只有成功才返回列表页

### 影响范围
- App：投资持仓详情页的"删除资产"操作
- 后端接口从 `/api/portfolio/delete` 改走 `/api/portfolio/delete_corrective`，会额外清理 transactions、adjustment_ledger、correction_logs 和受影响的 daily_snapshots
- 不改后端代码，不改数据库结构

### 验收重点
- 删除一个基金资产，页面应正常返回列表页，不应黑屏
- 删除后重新添加同一个基金，不应看到以前的交易记录
- 删除失败时应留在详情页，不应跳走

## 2026-04-01-01

### 这版一句话
修复了“场内 ETF 被误标为基金”时，App 投资卡片不显示当日涨幅/当日盈亏（显示 `--`）的问题。

### 主要变化
- **后端：补齐场内基金识别**：更新 `kona_tool/core/price.py` 的 `is_exchange_fund_code`，让 `512890/159201/513530` 这类纯数字场内 ETF 号段也能被识别为“场内可交易基金”，交易日/开市状态改按 A 股口径走。
- **行为更符合直觉**：当这些资产被旧数据误标为 `fund` 时，后端不再把它们当成“场外基金（非交易日）”，从而恢复当日盈亏与百分比展示。

### 影响范围
- App/Web：投资页持仓卡片的“当日盈亏/百分比”展示门禁（仅影响场内 ETF 号段且被标为 `fund` 的旧数据）
- 不改数据库、不改持仓成本价/数量，不会写任何线上数据

### 验收重点
- `kona` 用户的 `红利低波ETF(512890)`、`港股通红利ETF(513530)` 等场内 ETF，在交易日时应恢复显示当日盈亏和百分比，不再是 `--`。
- 场外基金（`f_` / `ft_`）仍应维持“净值未更新时不展示当日盈亏”的原有规则。

## 2026-04-01-02

### 这版一句话
Web 端对齐 App：场内 ETF（统计归基金但可交易）不再显示“最新净值(日期)”的误导文案，统一按“价格口径”展示。

### 主要变化
- **Web：净值提示只对场外基金显示**：更新 [web/src/pages/app/AppInvestPage.vue](/Users/kona/Desktop/kaka/kona_repo/web/src/pages/app/AppInvestPage.vue) 和 [web/src/pages/app/AppHomePage.vue](/Users/kona/Desktop/kaka/kona_repo/web/src/pages/app/AppHomePage.vue)，只有 `navUpdatePending=true` 才显示“最新净值(日期)”；场内 ETF 不再显示该提示。
- **Web：资产详情页同步对齐**：更新 [web/src/pages/app/AppAssetDetailPage.vue](/Users/kona/Desktop/kaka/kona_repo/web/src/pages/app/AppAssetDetailPage.vue)，最新价格/净值标题与净值日期提示同样改为只在 `navUpdatePending=true` 时出现。

### 影响范围
- Web：首页、投资页、资产详情页
- 不改后端，不改数据库，不会写任何线上数据

### 验收重点
- `kona` 用户的 `自由现金流ETF(159201)`、`标普ETF(159655)`、`红利低波ETF(512890)`、`港股通红利ETF(513530)`：Web 卡片不再出现“最新净值(日期)”提示，展示与 App 一致。
- 场外基金（`f_` / `ft_`）仍应维持“净值未更新时不展示当日盈亏，并显示净值日期提示”的原有规则。

## 2026-04-01-03

### 这版一句话
Web 端对齐 App：场内 ETF（`navUpdatePending=false`）不再因为缺少 `latest_nav_date` 就被当成“净值过期”，当日涨幅/当日盈亏恢复展示。

### 主要变化
- **Web：stale 判断加门禁**：更新 [web/src/pages/app/AppInvestPage.vue](/Users/kona/Desktop/kaka/kona_repo/web/src/pages/app/AppInvestPage.vue)、[web/src/pages/app/AppHomePage.vue](/Users/kona/Desktop/kaka/kona_repo/web/src/pages/app/AppHomePage.vue) 和 [web/src/pages/app/AppAssetDetailPage.vue](/Users/kona/Desktop/kaka/kona_repo/web/src/pages/app/AppAssetDetailPage.vue)，`isStaleFund()` 只在 `navUpdatePending=true` 时才要求 `latest_nav_date`，否则直接视为非 stale。

### 影响范围
- Web：首页、投资页、资产详情页
- 不改后端，不改数据库，不会写任何线上数据

### 验收重点
- `kona` 用户的 `自由现金流ETF(159201)`、`标普ETF(159655)`、`红利低波ETF(512890)`、`港股通红利ETF(513530)`：Web 端应恢复显示当日涨幅/当日盈亏，不再是 `--`。
- 场外基金（`navUpdatePending=true`）仍维持保守策略：无净值日期或非当日净值时，当日盈亏显示 `--`。

## 2026-04-01-04

### 这版一句话
Web 端兜底对齐后端：当持仓被标成 `fund` 但代码属于“场内 ETF/LOF”等可交易号段时，Web 侧交易日/开市状态按 A 股口径推断，避免因为 bootstrap/缓存缺字段导致当日盈亏被误隐藏。

### 主要变化
- **Web：补一份场内基金号段识别（仅用于市场状态推断）**：更新 [web/src/stores/portfolio.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/stores/portfolio.ts)，新增 `isExchangeFundCode()`，当 `market === 'fund'` 且代码命中场内号段时，把内部 `market` 视为 `a` 来读取市场开休市状态与交易日，从而恢复 `dayPnlAggregateEnabled` 推断。

### 影响范围
- Web：状态层（影响“当日盈亏开关推断/汇总口径”）
- 不改后端、不改数据库，不会写任何线上数据

### 验收重点
- `kona` 用户场内 ETF：Web 端应稳定显示当日盈亏/百分比（只要行情正常返回），不再被“基金市场未开盘/非交易日”误判挡住。
- 场外基金（`f_` / `ft_` 且 `navUpdatePending=true`）仍维持净值口径与保守门禁不变。

## 2026-04-01-05

### 这版一句话
Web 端对齐 App：场内 ETF 即使历史上用 `f_` 前缀入库，也不再被当成“净值待更新的场外基金”，当日涨幅/当日盈亏不再被门禁挡成 `--`。

### 主要变化
- **Web：场内 ETF 强制 `navUpdatePending=false`**：更新 [web/src/stores/portfolio.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/stores/portfolio.ts)，当代码命中“场内 ETF/LOF”号段时，直接关掉 `navUpdatePending`，避免前端误走“净值待更新”分支。

### 影响范围
- Web：首页、投资页、资产详情页（仅影响“场内 ETF 号段但被旧数据用 `f_` 前缀误标”的资产）
- 不改后端、不改数据库，不会写任何线上数据

### 验收重点
- `kona` 用户的 `红利低波ETF(512890)`、`港股通红利ETF(513530)`、`自由现金流ETF(159201)`、`标普ETF(159655)`：Web 端应恢复显示当日涨幅 badge 和当日盈亏，不再是 `--`。
- 场外基金仍维持“净值待更新时不展示当日盈亏”的规则。

## 2026-04-03-01

### 这版一句话
修复 Web 首页顶部“指数卡片一直加载中”问题：`/api/market/indices` 兼容价格接口 5 元组返回，不再 500。

### 主要变化
- **后端：指数接口解包兼容 4/5 元组**：更新 [kona_tool/market_handlers.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/market_handlers.py)，只取 `(price, yclose, amt, pct)` 前 4 个字段，忽略 `nav_date` 等尾部字段，避免 ValueError 导致接口报错。
- **测试：锁住 5 元组回归**：更新 [kona_tool/tests/test_market_api.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_market_api.py)，mock 改为 5 元组，确保后续不会再回退到错误解包。

### 影响范围
- Web：首页顶部指数条（依赖 `/api/market/indices`）
- 不改数据库、不改持仓口径，不会写任何线上数据

### 验收重点
- Web 首页顶部应能正常显示上证/深成/创业板/恒生科技/纳指和 USD/CNY，不再一直显示“加载中.../--%”。

## 2026-03-31-01

### 这版一句话
把仓库里确认不再使用的图片资源和本地产物彻底清掉，并补齐忽略规则，避免后续继续污染仓库。

### 主要变化
- **清理：删除不再使用的图片资源**：移除 Flutter `assets/images/` 下的旧 logo 与登录相关资源，以及 Web 端 `public/assets/`、`web/screenshots/` 里不再需要的图片和截图文件。
- **清理：删除历史备份文件**：移除 `web/package-lock.json.old.*` 这类历史备份文件，减少误提交噪音。
- **规则：补齐 .gitignore**：新增忽略 `web/screenshots/`、`web/modal_test.png`、`web/package-lock.json.old.*`，避免本地截图/测试产物反复进入 Git。

### 影响范围
- Flutter/Web：不改业务逻辑，仅删除已确认不再引用的资源文件
- 工程：仓库体积与 Git 变更噪音显著下降

### 验收重点
- Web/Flutter 的构建与运行不应出现“找不到资源文件”的报错（如果出现，说明仍存在引用残留，需要补一次引用清理）。
- GitHub Actions 的 `CHANGELOG guard` 应恢复绿色。

## 2026-03-30-02

### 这版一句话
修掉了 Web 投资页在美股休市时仍继续显示“当日盈亏”的口径漏保护问题，让 Web 和 App 在场外时段的展示规则重新对齐。

### 主要变化
- **Web：汇总口径补齐开关保护**：更新 `web/src/stores/portfolioMetrics.ts`，投资总览和市场卡片在累计“当日盈亏 / 当日收益率”时，开始尊重 `dayPnlAggregateEnabled`；不再把后端明确标记为“当前不该参与今日汇总”的资产继续加进来。
- **Web：单只资产卡片改成看 aggregate 开关**：更新 `web/src/pages/app/AppInvestPage.vue`，持仓卡片和列表行里的“当日盈亏金额 / 百分比”不再继续看 `dayPnlDisplayEnabled`，而是改成和市场汇总一致，统一尊重 `dayPnlAggregateEnabled`、基金净值延迟、`quotePending`、`navUpdatePending` 等条件；这样美股休市时不会再显示 `+¥0 / +0.00%`。
- **Web：布尔字段解析对齐 App**：更新 `web/src/stores/portfolio.ts`，`day_pnl_display_enabled / day_pnl_aggregate_enabled / market_open / market_trading_day` 等字段的解析逻辑改成和 Flutter 一致，避免后端如果返回字符串 `0/1/true/false` 时，Web 误把 `'0'` 当成 `true`。
- **Web：状态层不再覆盖后端开关**：继续更新 `web/src/stores/portfolio.ts`，当后端已经明确把 `day_pnl_display_enabled / day_pnl_aggregate_enabled` 置为 `false` 时，Web 不会再因为拿到了最新 quote 和昨收，就擅自把开关改回 `true` 并重新算出“今日盈亏”；这次修的是导致美股休市时仍然显示真实盈亏的根因。
- **Web：今日盈亏兜底规则正式对齐 App**：继续收 `web/src/stores/portfolio.ts`，当后端没显式给 `day_pnl_*_enabled` 时，Web 不再“只要有 quote 就算今日盈亏”，而是改成和 App 一样：先看 `nav_update_pending`、A/HK/Fund 盘前抑制，再看是否有有效昨收；聚合口径下，美股只有在交易日或扩展时段（盘前/盘后）才允许启用今日盈亏。
- **Web：状态层补齐 quote session / 美股扩展时段**：Web 的 `rows` 现在会落 `session`、`usExtendedActive`，后续页面和汇总层不需要再自己猜“美股现在是不是可展示今日盈亏”，统一只读状态层结果。
- **Web：持仓卡片数量样式收口**：修复 `美股 284 股` 这类元信息被 `space-between` 硬拉开的样式问题，数量和单位现在会作为一组正常排布，不再“数量飘左、股字飘右”。
- **展示收口**：当单只资产当前不应展示今日盈亏时，Web 现在显示 `--`，不再出现“百分比已经隐藏，但金额还在跳”或“显示成 0”的口径分裂。

### 影响范围
- Web：投资页顶部市场卡片、投资页持仓卡片、投资页列表行、投资页状态层布尔解析
- 口径：仅影响 Web 端“今日盈亏”的展示与汇总，不改后端数据，不改 App 逻辑

### 验收重点
- 周一白天美股未开盘时，Web 投资页“美股”市场卡片不应再显示非零当日盈亏。
- Web 投资页里美股单只资产卡片和列表行，不应再继续显示 `+¥0 / +0.00%` 这种伪“今日盈亏”；应与 App 的休市展示口径一致。
- Web 状态层在拿到最新 quote 后，不应再把后端已判定为 `false` 的今日盈亏开关改回 `true`；美股休市时不应继续出现 `-¥117.63 / +¥78.61 / -¥482.99` 这类真实今日盈亏数值。
- 当后端没有显式给今日盈亏开关时，Web 应和 App 一样：美股只有在交易日或扩展时段才显示当日盈亏；周一白天这类美股未开盘场景，不应再因为拿到了 quote 就继续显示今日盈亏。
- 持仓卡片头部的 `284 股` 这类数量文案，不应再出现数字和单位被横向拉开的漂移现象。

## 2026-03-30-01

### 这版一句话
把 GitHub Actions 的生产部署链路改成“部署抖动只给 warning，不再把前后端门禁全绿的 run 打成红叉或取消”。

### 主要变化
- **CI：部署 job 超时上调**：把 `.github/workflows/deploy.yml` 里的 `Deploy to Production` job 超时从 `20` 分钟提高到 `30` 分钟，避免上传重试阶段还没跑完就被 GitHub 直接 cancel。
- **CI：上传和远程部署改成非阻断**：`Upload Web artifact to server (with retries)` 和 `SSH and deploy` 两个步骤都改成 `continue-on-error`，并分别加了步骤级 `timeout-minutes`，避免网络抖动把整条 workflow 结论打红。
- **CI：补部署结果总结**：新增 `Deploy result summary` 步骤；如果上传或远程部署失败，会在 Actions 里明确给出 warning，提示“代码门禁已通过，可稍后重试部署 workflow”，不再只留下一个不清楚的红叉或 cancel 结果。

### 影响范围
- GitHub Actions：`.github/workflows/deploy.yml`
- 生产部署：仅影响 Actions 展示方式和部署失败时的结论，不改线上应用逻辑

### 验收重点
- 当前后端、前端门禁都通过时，workflow 不应再因为上传 Web 制品超时而整条显示红叉或 cancelled。
- 如果服务器 SSH / SCP 抖动，Actions 应出现明确 warning，并指出失败发生在“上传阶段”还是“远程部署阶段”。

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
