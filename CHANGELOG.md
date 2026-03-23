## 2026-03-23-02

### 这版一句话

修掉投资账本两条线上脏数据入口：首页刷新不再偷偷切回全部账本，同代码跨账本持仓的新增和撤销不再互相串改。

### 主要变化
- **首页全量刷新继续带当前账本**：Flutter [flutter/lib/providers/app_refresh_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_refresh_state.dart) / [flutter/lib/providers/app_refresh_coordinator_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_refresh_coordinator_state.dart) / [flutter/lib/providers/app_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_state.dart) 现在会把当前 `ledger_id` 贯穿到 `refreshAll / refreshByVersion`，首页下拉刷新、全量刷新、账本模式下的回退刷新不再把默认账本刷成全部账本汇总。
- **新增持仓更新语句补回账本条件**：后端 [kona_tool/core/db_portfolio.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/db_portfolio.py) 里 `add_asset()` 命中已有持仓后的 `UPDATE` 现在会带上 `ledger_id`，避免同一用户多个账本里同代码资产被一次更新一起改掉。
- **撤销投资操作改成按账本回滚**：后端 [kona_tool/portfolio_handlers.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/portfolio_handlers.py) 会把 `ledger_id` 写进 undo 记录，[kona_tool/core/db_portfolio.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/db_portfolio.py) 的 `undo_invest_operation()` 现在也按 `code + user_id + ledger_id` 回滚，不再误删或误恢复别的账本同代码持仓。
- **补了跨账本回归测试**：后端 [kona_tool/tests/test_portfolio_api.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_portfolio_api.py) 新增“同代码跨账本更新只改目标账本”和“带现金买入后的 undo 只回滚目标账本”两条测试，锁住这次修复。

### 影响范围
- Flutter：首页下拉刷新、全量刷新、账本模式下的首页数据口径
- 后端：同一用户多个账本持有同一代码资产时的新增、更新、撤销链路

### 验收重点
- 选择默认账本进入首页后，下拉刷新不应再跳成全部账本总额
- 同一用户两个账本都有同一只股票时，修改其中一个账本的持仓不应影响另一个账本
- 在某个账本里买入后点撤销，只应回滚当前账本，不应把别的账本同代码持仓一起删掉

## 2026-03-22-10

### 这版一句话

继续收口 Flutter 投资录入和详情页体验：截图录入复用的添加资产弹窗补齐草稿模式、删除确认和金额联动，mac 端详情页顶部按钮点击区域同步修正。

### 主要变化
- **添加资产弹窗支持草稿模式**：Flutter [flutter/lib/widgets/invest_trade_dialog.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/widgets/invest_trade_dialog.dart) 现在支持 `draftOnly`，截图录入进入弹窗时会先保存草稿，不直接写库，方便回到截图页统一提交。
- **截图录入弹窗交互补齐**：同一文件现在支持删除识别结果前二次确认、预填数量和成本价时自动联动金额、清空已选资产时默认保留 OCR 已识别出的数字输入。
- **弹窗关闭结果可回写上一页**：同一文件关闭时可把当前已确认的 `名称 / 代码 / 数量 / 成本价 / 金额` 带回截图录入页，避免编辑完后页面状态不同步。
- **mac 详情页顶部点击区域下移**：Flutter [flutter/lib/pages/investment_detail_page.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/pages/investment_detail_page.dart) 现在在 macOS 下把顶部导航整体下移，避免返回和更多按钮被标题栏区域挡住点不到。

### 影响范围
- Flutter：截图录入进入后的“添加资产”弹窗
- Flutter：macOS 投资详情页顶部返回和更多按钮点击区域

### 验收重点
- 截图录入点“编辑”进入添加资产弹窗后，应先保存草稿，再回到截图页统一提交，不应直接入库
- 弹窗里删除识别结果时，应先弹确认
- OCR 已识别出成本价和数量时，金额应自动算出
- macOS 投资详情页顶部返回按钮和右上角更多按钮应能正常点击

## 2026-03-22-09

### 这版一句话

截图录入页再次上传图片时不再覆盖上一批识别结果，改成继续追加，方便一轮里连续处理多张截图。

### 主要变化
- **结果列表改成追加而不是覆盖**：Flutter [flutter/lib/pages/portfolio_screenshot_import_page.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/pages/portfolio_screenshot_import_page.dart) 现在在第二次上传成功后，会把新识别结果追加到现有列表后面，不再直接把上一批结果整批替换掉。
- **补了最小去重**：如果新旧两批识别结果在 `名称 / 代码 / 数量 / 成本价` 上完全相同，当前页面不会再重复追加第二遍。
- **失败时保留旧结果**：再次上传如果识别失败，上一批已识别结果会继续保留，不会被空结果或错误状态冲掉。
- **提示文案同步改成当前真实行为**：成功后提示改成“已追加识别结果，请继续编辑后提交”，没有新增结果时会提示“这张图没有新的识别结果”。

### 影响范围
- Flutter：`截图录入` 页面多图连续导入时的结果列表行为

### 验收重点
- 先上传第一张图，再上传第二张图，结果列表应继续追加，不应覆盖第一张图的结果
- 第二次上传失败时，第一张图原来的识别结果应继续保留
- 完全相同的识别结果不应重复堆叠两遍

## 2026-03-22-08

### 这版一句话

复杂整页持仓图不再反复请求模型，改成“一次视觉转写，后端自己拆表”，减少上游限流下的超时和直接报错。

### 主要变化
- **复杂截图主流程改成单次转写**：后端 [kona_tool/core/portfolio_ocr.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/portfolio_ocr.py) 现在只请求一次视觉模型，让模型把资产列表逐行抄出来；不再让模型多轮做 JSON 结构化，也不再做区域级二次请求。
- **后端自己完成拆表**：同一文件里的本地解析器继续负责把转写文本拆成 `名称 / 代码 / 数量 / 成本价`，支持管道格式、两行一条资产、单行资产等常见持仓列表形态。
- **保留 JSON 兼容，但不再作为主路径**：如果上游模型仍然直接返回 JSON，后端还能兼容解析；但复杂图主路径已经切到“先转写，再本地拆”。
- **复杂图结果容量继续保持 12 条**：整页持仓图最多返回 12 条，避免只识别出前几条就被自己截断。
- **补齐单次转写回归测试**：后端 [kona_tool/tests/test_portfolio_api.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_portfolio_api.py) 已改成“单次转写 + 本地解析”的测试口径，避免后面又回退到多轮模型请求。

### 影响范围
- 后端：`/api/portfolio/ocr_parse_asset` 的复杂截图识别链路
- 线上识别：银河证券、富途这类整页深色持仓图的成功率、耗时和稳定性

### 验收重点
- 桌面测试图 [测试1.jpg](/Users/kona/Desktop/测试1.jpg) 这类整页深色持仓图，应至少能提取出多条资产草稿，不应再因为多轮模型重试拖死
- 桌面测试图 [测试2.jpg](/Users/kona/Desktop/测试2.jpg) 这类带代码的港股持仓列表，应至少能提取出主要资产行
- 截图里没明确出现代码时，`code` 仍然必须保持为空，不能因为复杂图兜底又开始瞎猜

## 2026-03-22-07

### 这版一句话

截图识别后端开始支持深色、多列、整页持仓表截图，第一次提取失败时会自动切到表格模式再试一遍。

### 主要变化
- **主提示词补上复杂持仓表规则**：后端 [kona_tool/core/portfolio_ocr.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/portfolio_ocr.py) 现在明确支持深色背景、整页、多行、多列的持仓列表图，不再只按“单条资产详情图”理解截图。
- **新增表格模式兜底识别**：第一次按普通模式识别如果没有提到任何候选资产，后端会自动再用“复杂表格截图”专用提示词重试一次，优先逐行提取名称、代码、数量和成本价。
- **补清复杂列的提取口径**：对 `成本/现价`、`现价/成本` 这类列头，后端提示词现在会显式区分成本价该取哪一个值，并明确禁止把市值、盈亏、涨跌幅误塞进成本价。
- **补齐回归测试**：后端 [kona_tool/tests/test_portfolio_api.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_portfolio_api.py) 新增“普通模式空结果时自动切表格模式”的测试，避免这条兜底能力以后回退。

### 影响范围
- 后端：`/api/portfolio/ocr_parse_asset` 的截图理解能力
- 线上识别：银河证券、富途这类深色整页持仓图的成功率

### 验收重点
- 深色、多列、整页列表型持仓截图，不应再因为第一轮提取为空就直接报错
- 对 `成本/现价` 或 `现价/成本` 这类列头，提取出的 `price` 应优先对应成本价
- 截图里没有明确代码时，仍然必须保持 `code` 为空，不能为了表格模式又开始瞎猜代码

## 2026-03-22-06

### 这版一句话

继续收口截图识别录入：禁止 AI 在没看到代码时瞎猜证券代码，并把统一添加资产弹窗里的删除和保留输入交互补齐。

### 主要变化
- **截图识别提示词补上“严禁猜代码”**：后端 [kona_tool/core/portfolio_ocr.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/portfolio_ocr.py) 现在明确要求只有在截图里真的看到了代码，才允许填写 `code`；如果没看到，必须留空，不能根据名称、品牌、常识、热门股票记忆、价格或市场去脑补。
- **补一条防回退测试**：后端 [kona_tool/tests/test_portfolio_api.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_portfolio_api.py) 新增回归测试，直接锁住“禁止猜代码”这条规则，避免后面改提示词时又把模型带回会臆造代码的状态。
- **统一添加资产弹窗补齐删除入口**：Flutter [flutter/lib/widgets/invest_trade_dialog.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/widgets/invest_trade_dialog.dart) 现在在截图识别进入的“添加资产”弹窗右上角显示删除按钮，允许直接删掉这条识别结果，不再回到截图页再删。
- **清空已选资产时保留 OCR 草稿数字**：Flutter [flutter/lib/widgets/invest_trade_dialog.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/widgets/invest_trade_dialog.dart) / [flutter/lib/pages/portfolio_screenshot_import_page.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/pages/portfolio_screenshot_import_page.dart) 现在在截图识别链路里，点已选资产的 `x` 只会清掉资产选择，不会把 OCR 带进来的数量和成本价一起清空。

### 影响范围
- 后端：`/api/portfolio/ocr_parse_asset` 的代码提取口径
- Flutter：截图识别进入后的“添加资产”弹窗交互

### 验收重点
- 像“小米集团”这类截图里没有明确股票代码的场景，识别结果里的 `code` 应保持为空，不应再杜撰 `000333` 之类代码
- 在截图识别进入的“添加资产”弹窗里，右上角应能直接删除当前识别结果
- 清掉已选资产后，数量和成本价应继续保留，方便换资产时直接沿用 OCR 草稿

## 2026-03-22-05

### 这版一句话

截图识别录入不再走第二套编辑弹窗，统一回到原来的“添加资产”弹窗，并把 OCR 草稿直接预填进去。

### 主要变化
- **去掉截图页自己的编辑弹窗**：截图录入页现在只负责上传图片和展示识别结果，不再自己维护一套“编辑识别结果”表单。
- **统一复用原来的添加资产弹窗**：点击识别结果里的“编辑”，会直接打开原来的“添加资产”弹窗；如果 OCR 已经识别出名称、代码、数量、买入价，就会自动预填进去，没有识别到的字段保持为空，让用户自己补。
- **添加资产弹窗补齐截图预填能力**：原有 Flutter 添加资产弹窗新增初始搜索词、初始已选资产、初始数量、初始成本价的预填能力，避免截图链路再长第二套交互。
- **OCR 接口继续收口成“只提取、不猜”**：后端不再按名称自动补股票代码，识别结果只保留 OCR 实际识别出的草稿字段，缺项留给用户在统一弹窗里手动补齐。

### 影响范围
- Flutter：截图录入页、添加资产弹窗
- 后端：`/api/portfolio/ocr_parse_asset` 的返回口径

### 验收重点
- 截图结果点“编辑”后，应直接进入原来的“添加资产”弹窗，而不是另一套编辑表单
- OCR 已识别出的名称 / 代码 / 数量 / 买入价，应自动带入添加资产弹窗
- 没识别到的字段应保持为空，用户可继续搜索资产并手动补齐

## 2026-03-22-04

### 这版一句话

管理后台截图识别模型配置支持手填，避免智谱模型列表不全时把视觉模型挡在下拉框外面。

### 主要变化
- **截图识别模型改成“下拉 + 手填”并存**：后台 AI 助手页的 OCR 模型配置，保留下拉选择，同时新增手动输入框，不再强依赖供应商返回的模型列表。
- **智谱默认给出视觉模型建议值**：当截图识别供应商选中智谱且当前模型为空时，页面会默认建议 `glm-4.6v-flash`，减少误选 `glm-4.6` 这类纯文本模型的概率。
- **页面提示补清楚**：明确说明“模型列表可能不会返回全部可用模型”，让主人知道下拉缺项不等于模型不能用。

### 影响范围
- Web 管理后台：AI 助手页里的“截图识别配置”
- 线上配置流程：截图识别模型现在可以直接手填视觉模型名

### 验收重点
- 智谱供应商下，截图识别模型既能从下拉选，也能直接手填
- 不依赖下拉列表时，`glm-4.6v-flash` 这类视觉模型也能保存
- Web 构建通过，不影响其他管理后台页面

## 2026-03-22-03

### 这版一句话

补齐截图识别这轮改动后的 CI 门禁，让 Flutter 生成物和测试口径重新和当前实现对齐。

### 主要变化
- **Flutter 生成物门禁补齐**：类型生成脚本现在会顺手清掉 `lib/generated/openapi` 里的测试目录和临时产物，`analysis_options.yaml` 也排除了生成测试目录，避免 CI 把第三方生成包的测试样板当成主工程代码继续分析。
- **测试口径同步到当前实现**：Flutter 测试补上 `day_pnl_base_aggregate_cny` 显式分母，不再回到前端自己猜收益率分母的旧逻辑。
- **后端回归测试改认当前规则**：场外基金未来归属和收益日历收益率分母的测试，改成和当前“按有效归属日记收益”“按期初本金算区间收益率”的正式口径一致。
- **交易记录测试去掉同秒排序假设**：保留“不能重复、卖出盈亏必须对”的校验，不再把跨表同秒记录顺序当成稳定规则。

### 影响范围
- Flutter：生成类型后的静态检查门禁、投资页当日收益率相关测试
- 后端：分析页收益率、场外基金归属、交易记录回归测试
- CI：`flutter analyze`、Flutter 测试、后端 Python 3.10 / 3.11 测试矩阵

### 验收重点
- GitHub Actions 不应再因为 `lib/generated/openapi/test/**` 被扫描而红叉
- Flutter 当日收益率测试应继续只认后端下发的显式分母
- 后端收益日历和场外基金相关测试应和当前正式口径一致

## 2026-03-22-02

### 这版一句话

继续收口投资收益口径，并落地客户端截图录入链路、后台 OCR 独立模型配置和接口文档生成链路。

### 主要变化
- **收益率和分析口径继续收口**：后端补齐 `day_pnl_base / total_pnl_base` 等分母字段，分析页月 / 年 / 总收益率改成按期初本金口径计算；Web / Flutter 不再自己乱猜今日收益率分母，改成优先吃后端统一字段。
- **普通调整入口继续去 legacy adjustment 化**：Web / Flutter 的持仓调整入口不再把 `adjustment` 当正常可编辑字段，分红 / 手续费改走收益事件入口，避免前端继续暗示“普通用户可以直接改老 adjustment”。
- **截图录入链路落地**：Flutter 投资页右下角新增“手动录入 / 截图识别”双入口；截图识别改成独立全屏页，支持候选卡片、编辑浮窗和确认保存，页面不再直接露出本地演示提示。
- **OCR 模型与聊天模型拆开**：后端新增截图识别专用 `ai_ocr_provider_config`，后台 AI 助手页新增“截图识别配置”区；AI 聊天继续走激活供应商，截图识别可单独指定 provider / model，不再强绑一套模型。
- **接口与文档链路补齐**：OpenAPI、接口总览 / 详情、类型生成脚本和 Web / Flutter 生成类型同步更新；后台现在能稳定生成和消费投资写链路、交易记录和 AI 配置相关接口。

### 影响范围
- 后端：AI provider 读取、截图识别路由、投资收益率分母、分析页收益口径、收益事件写入口
- Flutter：投资页悬浮录入入口、截图识别页、持仓调整弹窗、投资收益展示
- Web：分析页收益日历默认周期、后台 AI 助手配置页、投资写入口与收益率展示
- 文档与类型：OpenAPI、接口文档、类型生成脚本、生成后的 Web / Flutter 类型

### 验收重点
- Flutter 投资页右下角 `+` 能展开“手动录入 / 截图识别”，截图识别页能完成上传图片、查看识别结果、编辑浮窗和保存
- 管理后台 AI 助手页应新增“截图识别配置”，可以单独选截图识别供应商和模型，不影响聊天激活供应商
- Web 构建、后端 OCR / AI 聊天相关测试通过；真实截图识别是否可用取决于后台是否配置了支持图片的模型

## 2026-03-23-01

### 这版一句话

修掉空账本删除失败的后端判断 bug：现在非默认、无持仓的账本可以正常删除。

### 主要变化
- [kona_tool/core/db_portfolio.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/db_portfolio.py)：修正删除账本时把 `sqlite3.Row` 当 `dict` 调 `.get()` 的错误写法，避免空账本删除被误打成 `DELETE_FAILED`。
- [kona_tool/tests/test_portfolio_api.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_portfolio_api.py)：补齐“空账本可删”“有持仓账本不可删”的回归测试，防止删除规则以后再次回退。

### 影响范围
- 后端：`DELETE /api/portfolio/ledgers/<ledger_id>`
- Flutter：账本管理页删除账本

### 验收重点
- 非默认且没有持仓的账本，应能直接删除成功
- 非默认但仍有持仓的账本，应继续返回“账本下还有持仓，不能删除”

## 2026-03-22-01

### 这版一句话

投资支持多账本：每个账本独立管理持仓、交易和分析数据，总资产页汇总所有账本。

### 主要变化
- **数据库**：新增 `investment_ledgers` 和 `ledger_daily_snapshots` 表；`portfolio`、`transactions`、`portfolio_adjustment_ledger`、`portfolio_correction_logs` 加 `ledger_id` 列；portfolio 唯一约束改为 `(code, user_id, ledger_id)`。数据迁移自动为现有用户创建默认账本。
- **后端 CRUD**：`GET/POST /api/portfolio/ledgers`、`PUT/DELETE /api/portfolio/ledgers/<id>`，非默认且无持仓才允许删除。
- **后端持仓隔离**：`db_portfolio.py` 所有持仓/交易查询和写入方法加 `ledger_id` 过滤；不传时读侧返回全部，写侧用默认账本。
- **后端分析隔离**：`db_analysis.py` 的 overview/calendar/rank 加 `ledger_id`，有值时查 `ledger_daily_snapshots`；快照任务 `snapshot.py` 同时保存全局和按账本快照。
- **Flutter 状态管理**：`app_state.dart` 新增 `ledgers`、`currentLedgerId`、`switchLedger()`、`loadLedgers()`、`createLedger()`、`updateLedger()`、`deleteLedger()`；登录和恢复会话后自动加载账本；所有投资写操作默认透传 `currentLedgerId`。
- **Flutter UI**：投资页顶部常驻账本切换栏 + “+” 新建按钮；长按账本可重命名/删除；分析页 API 调用传入 `currentLedgerId`。

### 影响范围
- 后端：db_schema、db_portfolio、db_snapshots、db_analysis、snapshot、portfolio_handlers、portfolio_routes、analysis_handlers、analysis_read_service、portfolio_read_service、app_factory
- Flutter：api_config、api_service、app_state、app_investment_write_state、app_refresh_state、app_refresh_coordinator_state、invest_page、analysis_page
- 测试：5 个 Flutter 测试文件更新 fake/stub 签名

### 验收重点
- 投资页顶部出现账本切换栏和 “+” 按钮
- 创建新账本 → 切换过去 → 持仓为空
- 在新账本买入资产 → 切回默认账本 → 原持仓不变
- 删除空账本成功；删除有持仓的账本被拒绝
- 分析页按当前账本展示数据
- 不切换账本时所有功能与之前一致

## 2026-03-22-01

### 这版一句话

投资账本切换正式落地到 Flutter：投资页改成顶部账本选择器 + 独立账本管理页，并把分析页和首页的账本联动收干净。

### 主要变化
- [flutter/lib/pages/invest_page.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/pages/invest_page.dart) / [flutter/lib/pages/ledger_management_page.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/pages/ledger_management_page.dart)：投资页顶部改成账本胶囊选择器，下拉里可直接切换账本并进入独立“管理账本”页面；管理页支持新增、重命名、删除、拖动排序。
- [flutter/lib/providers/app_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_state.dart) / [flutter/lib/providers/app_refresh_coordinator_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_refresh_coordinator_state.dart) / [flutter/lib/providers/app_refresh_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_refresh_state.dart)：切换账本后改为刷新整套首页数据，首页总资产口径收正为“全局现金/其他/负债 + 当前账本投资资产”，不再出现切账本后首页整页归零。
- [flutter/lib/pages/analysis_page.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/pages/analysis_page.dart)：分析页和“全部排行”页现在会监听当前账本变化，切换账本后会清掉旧数据并按新账本重拉。
- [flutter/lib/services/api_service.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/services/api_service.dart) / [flutter/lib/config/api_config.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/config/api_config.dart)：补齐账本排序接口，修正 ledger 接口成功响应的前端识别。
- [kona_tool/portfolio_routes.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/portfolio_routes.py) / [kona_tool/portfolio_handlers.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/portfolio_handlers.py) / [kona_tool/core/db_portfolio.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/db_portfolio.py) / [kona_tool/core/db_analysis.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/db_analysis.py) / [kona_tool/core/db_schema.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/db_schema.py)：后端补齐账本排序接口、账本隔离、非法 `ledger_id` 拒绝和账本快照清理，避免同代码跨账本串盈亏、删纠错后账本历史残留脏数据。
- [flutter/test/invest_page_ledger_selector_test.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/test/invest_page_ledger_selector_test.dart) / [kona_tool/tests/test_portfolio_api.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_portfolio_api.py) / [kona_tool/tests/test_analysis_api.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_analysis_api.py)：补齐账本选择器、账本排序、账本隔离和分析页账本参数的回归测试。

### 影响范围
- Flutter：投资页、首页、分析页、账本管理页
- 后端：投资账本读写、分析读侧、账本排序、账本快照清理

### 验收重点
- 切换账本后，投资页和分析页应立即切到当前账本，不应继续显示上一个账本的数据
- 切换账本后，首页不应整页归零；首页总资产应按“全局现金/其他/负债 + 当前账本投资资产”展示
- 账本下拉里的“管理账本”页应支持新增、改名、删除、拖动排序

## 2026-03-21-01

### 这版一句话

统一分析页”当日总计盈亏”和收益日历口径，并封住自动快照反向污染历史日期的问题。

### 主要变化
- **分析页当日口径统一**：后端 [kona_tool/core/analysis_read_service.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/analysis_read_service.py) 的 `period=day` 现在在休市时仍然认实时统计层里的“最后一个有效收益日最终值”，不再退回“今天自然日快照”，避免顶部 `当日总计盈亏` 和收益日历互相打架。
- **自动快照不再顺手重写历史日**：后端 [kona_tool/core/snapshot.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/snapshot.py)、[kona_tool/snapshot_runtime.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/snapshot_runtime.py)、[kona_tool/portfolio_handlers.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/portfolio_handlers.py) 现在只允许写 `snapshot_date` 当天的市场拆分；当前实时统计里带出来的更早 `effective_date` 不再自动落库，历史修复必须单独走明确流程。
- **补齐回归测试**：新增接口保存和后台自动快照的测试，确保未来不会再把 `3/19` 这种已落地历史快照被 `3/21` 的实时统计回写覆盖。
- **线上 `kona` 数据收口**：恢复 `2026-03-19` 的原始历史拆分，保留 `2026-03-20 = -2772.45` 的最终值，同时继续保持 `2026-03-21 = 0`，让分析页顶部概览、收益日历和快照表重新一致。

### 影响范围
- 后端：分析页 `period=day` 顶部概览、自动快照写入、`/api/snapshot/save`
- 线上数据：`kona` 账号 `2026-03-19`、`2026-03-20`、`2026-03-21` 的分析快照与分市场拆分

### 验收重点
- 分析页顶部 `当日总计盈亏` 和收益日历 `3/20` 应同时显示 `-2772.45`
- `3/19` 应恢复为 `-1250.87`，`3/21` 应保持 `0`
- 后续自动快照不应再把当前实时统计顺手写回更早历史日期

## 2026-03-20-10

### 这版一句话

收口 `kona` 账号投资清账，并把分析页收益日历数字调大一档。

### 主要变化
- [flutter/lib/pages/analysis_page.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/pages/analysis_page.dart)：收益日历格子里的日盈亏数字调大，并同步放宽数字行高度，减少被压缩后看不清的问题。
- 线上 `kona` 账号按新规则完成一轮数据清账：清掉旧 `adjustment` 后，分批补录分红 / 手续费、成本价修正，并重写了 `f_511360` 的错误交易记录。
- 明确后续记账口径：分红单独记收益事件，不再为了对齐券商“摊薄后成本”去手改成本价；港股通人民币折算后的展示成本不作为系统真值。

### 影响范围
- Flutter 分析页收益日历可读性
- `kona` 账号当前持仓、持仓详情、分析页当日与后续快照口径
- 首页趋势和分析页历史快照会把 `2026-03-20` 视为本轮清账切换点

### 验收重点
- `flutter analyze lib/pages/analysis_page.dart` 通过
- mac 调试会话热重载后，收益日历数字比之前更清楚
- `kona` 账号当前持仓页、详情页和明天之后的新快照按新规则继续走

## 2026-03-20-09

### 这版一句话

把 Web 和 Flutter 的“今日盈亏”统一改成记账口径：今天新买的不参与当天盈亏。

### 主要变化
- **后端今日盈亏改成只看昨仓**：`portfolio_metrics.py` 现在计算 `day_pnl / day_pnl_rate` 时，会先扣掉今天新增买入的数量；今天新买的部分不再参与当天盈亏。
- **纯今天新建的持仓不再硬显示今日盈亏**：如果一只持仓当前全部都是今天新买的，后端会把这条持仓标成不展示今日盈亏，避免页面继续给出看起来像真实盘中收益的 `+0.xx%`。
- **补齐契约测试**：新增“今天加仓后今日盈亏应只看昨仓”和“纯今天新建仓位不展示今日盈亏”的测试，防止后面再回到交易软件口径。

### 影响范围
- 后端：`/api/portfolio?with_metrics=1`、同步返回的投资持仓今日盈亏口径
- Web / Flutter：投资首页、首页投资区、详情页里依赖 `day_pnl` 的展示

### 验收重点
- `f_159687` 这种今天加过仓的持仓，今日盈亏应只反映昨仓，不再被今天新买部分拉成正数
- 今天刚补录的新持仓，不应立刻显示一条有误导性的今日盈亏

## 2026-03-20-08

### 这版一句话

修正投资页卡片“今日盈亏金额”和百分比口径打架的问题，并补掉整数显示被浮点误差吃成 0 的问题。

### 主要变化
- **当日盈亏率改成和当日盈亏金额同口径**：`portfolio_metrics.py` 现在在“今日有加仓”时，会按“昨仓部分 + 今日买入均价部分”一起算 `day_pnl` 和 `day_pnl_rate`，不再出现金额为正、旁边百分比却跟着昨收涨跌幅显示成负数。
- **整数显示不再被浮点残差误伤**：投资页卡片和全局 `formatPnlInt` 现在都对 `0.4999999999` 这类浮点残差做归一，避免真实应显示 `+1` 的值被截成 `+0`。
- **补齐合同测试和 Flutter 冒烟测试**：后端新增“今日有加仓时 `day_pnl_rate` 必须和 `day_pnl` 同方向”的契约测试；Flutter 新增整数格式化测试，防止以后又回退成 `+0`。

### 影响范围
- Flutter：投资页持仓卡片的今日盈亏金额与百分比显示
- 后端：`/api/portfolio?with_metrics=1` 和同步返回的当日盈亏率口径

### 验收重点
- 今日有加仓的持仓，若卡片右上角“今日盈亏”是正数，现价旁边百分比也应保持正数
- 像 `0.4999999999` 这样的当日盈亏，不应再显示成 `+0`

## 2026-03-20-07

### 这版一句话

把投资详情页修正后的强制刷新、修正文案和迁移说明文档补齐。

### 主要变化
- **详情页保存/撤销后强制刷新**：投资详情页弹窗现在在加仓、减仓、修正成功后会主动刷新持仓和交易记录；点撤销成功后也会再刷新一次，尽量避免刚保存完列表还停在旧数据。
- **修正记录文案改成人话**：交易记录里的 `成本修正 / 数量修正 / 持仓修正` 现在直接展示变化前后，比如 `成本价 2 -> 2.1`、`持仓数量 100股 -> 120股`，不再只给一串干巴巴的数字。
- **补齐当前口径和线上补数说明**：新增 [投资持仓修正与收益事件迁移说明](/Users/kona/Desktop/kaka/kona_repo/docs/投资持仓修正与收益事件迁移说明.md)，把当前真实表职责、旧 `adjustment` 兼容策略、这次腾讯云发布和 `konae / f_159687` 补数记录写清楚；同时更新 docs 导航和旧收益说明的入口提示。

### 影响范围
- Flutter：投资详情页、买卖/修正弹窗、撤销后的详情页刷新
- 文档：投资持仓口径入口、旧 `adjustment` 说明、线上补数记录

### 验收重点
- 保存加仓、减仓、修正后，详情页应自动刷新，不需要手动退回再进
- 撤销成功后，详情页指标和交易记录也应一起回滚
- 文档入口优先看新的迁移说明，不再误把旧 `adjustment` 摊薄成本当成当前主口径

## 2026-03-20-06

### 这版一句话

补齐交易记录同秒排序，并把这轮投资详情改动的 CI 门禁收绿。

### 主要变化
- **交易记录同秒排序补稳**：`transactions / portfolio_adjustment_ledger / portfolio_correction_logs` 在同一秒产生多条记录时，统一按 `time DESC, id DESC` 返回，避免详情页出现“明明后记的手续费却排到分红后面”。
- **后端测试隔离补齐**：`test_portfolio_api.py` 和 `test_portfolio_metrics_contract.py` 在 `setUp` 里清掉 `market_runtime` 的市场状态缓存，避免前一条测试把 5 秒缓存带进后一条，导致场内 ETF 市场状态契约偶发误判。
- **Flutter 测试桩签名补齐**：`analysis_rank_abs_cost_test.dart` 的假 `ApiService` 现在补上 `note` 参数，和真实接口保持一致，避免 `flutter analyze` 被无效 override 拦住。

### 影响范围
- 后端：投资详情页交易记录排序稳定性
- 测试与 CI：后端单测隔离、Flutter analyze 门禁

### 验收重点
- 同一秒连续补记 `分红 / 手续费 / 修正记录` 时，详情页列表应按最新一条排在最上面
- `python3 -m unittest discover -s tests -p 'test_*.py'` 通过
- `flutter analyze --no-fatal-infos --no-fatal-warnings` 通过

## 2026-03-20-05

### 这版一句话

把 Flutter 投资持仓详情页和“修正”流程收成可验收状态，同时把线上后端切到新的修正记录口径，并补回 `konae` 缺失的修正记录。

### 主要变化
- **Flutter 持仓详情页按原型继续收口**：新增 [investment_detail_page.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/pages/investment_detail_page.dart)，投资页持仓卡片改成进入详情页；页面补了交易记录、空状态、删除确认、资产名称全局截断、代码格式转用户端习惯显示，以及市值/累计盈亏/当日盈亏整数展示。
- **买入/卖出/修正弹窗重新整理**：去掉弹窗右上角删除入口和修正页签切换；买卖表单改成“成本价/数量”一行、“金额”单独一行；修正弹窗去掉冗余预览卡，备注改成可选，保存后的撤销提示从顶部 15 秒改成弹窗附近底部 5 秒。
- **后端把交易、收益事件、修正记录拆开**：`transactions` 只记录加仓/减仓，`portfolio_adjustment_ledger` 只记录分红/手续费/税，新增 `portfolio_correction_logs` 专门记录成本价/数量/持仓修正；成本价展示不再吃 `adjustment`，分红和手续费不再改成本价。
- **交易记录读链路改成吃修正表**：详情页交易记录现在会展示 `成本修正 / 数量修正 / 持仓修正`，减仓已实现盈亏不再重复拆成第二条收益事件。
- **线上发布与补数**：腾讯云 `kona.service` 已发布新后端并补齐 `portfolio_correction_logs` 表；另外把 `konae / f_159687` 在 `2026-03-20 18:45:18` 的成本价修正补成正式修正记录，避免详情页列表继续缺一条。

### 影响范围
- Flutter：投资页、持仓详情页、买卖/修正弹窗、顶部提示条、资产名称显示
- 后端：持仓修正写入、交易记录读取、累计盈亏口径、线上 `kona.service`

### 验收重点
- 修正成本价、数量、分红、手续费时，备注留空也应能保存，且分红/手续费不应再改成本价
- 详情页保存后，撤销提示应在底部附近显示并在 5 秒内消失
- `konae / f_159687` 详情页交易记录里应能看到 `2026-03-20 18:45:18` 的 `成本修正 2.0 -> 2.1`

## 2026-03-20-04

### 这版一句话

把投资持仓里的“调整”从混合大桶拆成收益事件兼容层，并修掉 Flutter 端调整保存偶发卡很久的问题。

### 主要变化
- **后端开始把“持仓状态”和“历史收益事件”分开**：新增 `portfolio_adjustment_ledger` 收益事件流水表和迁移脚本；卖出产生的已实现盈亏改成写流水，不再继续把所有历史收益都硬塞进 `portfolio.adjustment`。
- **读侧累计盈亏改成统一总口径**：持仓指标和分析排行现在统一按“旧 `portfolio.adjustment` 兼容值 + ledger 流水汇总”计算累计盈亏，给后续把分红、手续费、手工补差独立出来留好入口。
- **Flutter 调整保存改成内存优先续签**：登录、恢复会话和刷新 token 后会把 `access token + refresh token` 一起缓存到内存；token 过期时续签优先用内存里的 refresh token，不再每次先慢读 macOS 安全存储，减少调整保存时无故转很久和偶发失败的体感。
- **回归测试补齐**：新增收益事件迁移测试和 Flutter token 缓存测试，继续覆盖修改持仓、撤销卖出、累计盈亏聚合和认证恢复链路。

### 影响范围
- 后端：投资持仓调整、卖出已实现盈亏记录、累计盈亏聚合、分析排行口径
- Flutter：投资页调整保存、token 续签与登录态恢复

### 验收重点
- 修改成本价或数量时，不应再把这类持仓修正继续混进历史收益事件
- 卖出后累计盈亏应连续，撤销卖出后对应收益事件应一起回滚
- Flutter 在 macOS 上调整保存时，不应再因为 token 续签卡出 3 到 4 秒的明显停顿

## 2026-03-20-03

### 这版一句话

统一 Web 和 Flutter 投资页顶部收益口径：持仓盈亏只看当前持仓浮动，累计盈亏继续包含 adjustment、分红和已实现盈亏。

### 主要变化
- **Flutter 顶部收益卡片改成两套真实口径**：投资页大卡片里的 `持仓盈亏` 不再直接复用累计盈亏，改成按当前持仓 `市值 - 成本` 计算；`累计盈亏` 继续走后端 `totalPnl`，把 adjustment、分红和已实现盈亏并进去。
- **Web 投资页文案与计算统一**：投资页顶部中间这列从 `持仓收益` 改成 `持仓盈亏`，继续显示当前持仓浮动盈亏，避免把浮动结果误读成累计收益。
- **累计盈亏率分母一起校正**：Web 和 Flutter 聚合口径里的累计盈亏率，统一改成按 `|成本| + max(0, adjustment)` 作为分母，避免有已实现盈亏时百分比虚高，保证金额和百分比说的是同一件事。

### 影响范围
- Flutter：投资页顶部大卡片的持仓盈亏、累计盈亏及对应收益率
- Web：投资页顶部投资汇总和分类累计盈亏率聚合展示

### 验收重点
- Flutter 投资页顶部大卡片里，`持仓盈亏` 和 `累计盈亏` 不应再显示成同一个值
- Web 投资页顶部中间这列应显示为 `持仓盈亏`，且只反映当前持仓浮动盈亏
- 当持仓存在 adjustment、分红或减仓已实现盈亏时，累计盈亏率不应再比金额口径明显偏高

## 2026-03-20-02

### 这版一句话

修复 Web 投资页数据刷新慢半拍的问题：停留页面时会定期补拉持仓指标，不再只刷行情。

### 主要变化
- **投资页刷新链路补齐**：`AppInvestPage.vue` 新增统一的 `refreshInvestReadState()`，进入页面和交易成功后都先刷新静态持仓数据，再补趋势线和行情，避免只更新 quotes 但持仓指标不动。
- **页面停留时补静态刷新**：投资页现在和首页一样，停留期间每 60 秒主动补一次 `refreshStaticOnly()`，不再只靠 `refreshQuotesOnly()`，减少“价格请求在跑，但投资页数字不跟着变”的延迟感。
- **页面卸载时清理定时器**：投资页离开时会停止自己的静态刷新定时器，避免继续占着旧页面副作用。

### 影响范围
- Web：投资页持仓卡片、顶部投资汇总、交易成功后的回显时机
- 刷新编排：投资页停留期间的数据更新节奏

### 验收重点
- 打开 Web 投资页后，停留一段时间时持仓卡片和顶部汇总应能跟随后端持仓指标更新
- 买入、卖出、调整成功后，投资页应立即重拉持仓数据，不再需要手动反复刷新
- 首页和投资页的刷新节奏应保持一致，不再出现首页更新了、投资页还慢一拍

## 2026-03-20-01

### 这版一句话

补齐基金最新净值日期透出，优化 Flutter 多个页面的展示和加载体验。

### 主要变化
- **基金净值日期透出**：后端持仓读取链路新增 `latest_nav_date`，为场外基金补充最新净值日期；投资页在“待净值更新”场景下会继续显示当前净值，并把“最新净值 MM-DD”贴在净值右侧；如果最新净值不是今天，卡片右上角仍保留“今日盈亏”，但值显示 `--`，避免误导成实时涨跌。
- **资产历史页改为先读缓存再静默刷新**：历史页现在会先读本地缓存秒开，再后台刷新最新数据，降低重复进入页面时的等待感；同时补了状态层缓存读取入口。
- **Flutter 页面细节优化**：分析页切换控件补了浅色主题边框和阴影；首页大卡片底部增加“总资产趋势”入口文案；AI 聊天页把单一“思考中”改成轮播状态文案；资产调整弹窗补了浅色主题下的选中态和输入选择样式。
- **后端测试补齐**：新增基金最新净值日期透出的读取测试，继续覆盖投资页依赖的持仓读取口径。

### 影响范围
- Flutter：投资页、分析页、首页、AI 聊天页、资产历史页、资产调整弹窗
- 后端：基金净值读取与持仓聚合字段

### 验收重点
- 场外基金卡片在净值未更新时，应显示当前净值和“最新净值 MM-DD”提示；右上角“今日盈亏”应保留但值显示 `--`
- 资产历史页再次进入时应优先展示缓存，再静默刷新
- AI 聊天页流式回复期间应看到轮播中的状态文案

## 2026-03-19-05

### 这版一句话

修复 GitHub Actions 部署红叉：前端静态包上传后先做远端校验，再进入解压和发布。

### 主要变化
- **前端部署包改成可校验上传**：部署工作流现在会先在 runner 本地做 `gzip` 自检，再计算 `sha256`，上传到服务器临时文件后先校验完整性，通过后才替换成正式部署包。
- **远端改成唯一文件名**：部署包不再总是共用 `/tmp/web-dist.tar.gz`，改成带提交号的唯一路径，避免旧文件、半上传文件和新文件互相覆盖。
- **解压前先验包**：服务器正式解压前会先跑一次 `gzip -t`，损坏包直接失败，不再带着坏包进入 `tar -xzf`。

### 影响范围
- GitHub Actions 的 `Deploy to Production`
- 前端静态资源上传、校验和解压发布流程

### 验收重点
- `Deploy to Production` 不应再因为 `invalid compressed data` 或 `Unexpected EOF in archive` 红叉
- 上传重试后，远端只应保留校验通过的部署包

## 2026-03-19-04

### 这版一句话

给 Flutter 端 AI 助手加上积分门槛：默认 0 积分，后台可按用户名发放，成功开始回答后才扣 1 分。

### 主要变化
- **后端积分模型**：`users` 表新增 `ai_credits_balance`，新增 `ai_credit_ledger` 流水表，保留余额和每次变动记录，方便后面查账、排障和审计。
- **AI 聊天扣点规则**：`/api/ai/chat` 进入时先校验积分；没有积分直接返回 `AI_CREDITS_REQUIRED`；有积分时只有在 AI 成功返回第一段内容后才原子扣减 `1` 分，失败不白扣。
- **管理后台发放积分**：用户列表和详情新增 `AI 积分` 展示；在现有用户详情里直接支持按用户名增减积分，并展示最近积分流水。
- **Flutter 无积分态**：AI 聊天页会显示剩余积分；没有积分时允许进入页面，但不允许发送，并展示“加入咔咔用户群”的引导文案和二维码。
- **聊天记录持久化**：AI 对话历史按用户本地持久化，退出页面再进会恢复，不同账号不会串记录。
- **AI 链路埋点**：AI 聊天补了上下文构建、首字返回、总耗时埋点，后面可以更快判断慢在本地上下文还是慢在模型响应。
- **部署重试修复**：GitHub Actions 的部署脚本移除了 `git fetch` 超时后的危险 `pkill -f`，避免远端 SSH 会话被误杀，导致部署在重试前直接红叉。

### 影响范围
- 后端：AI 聊天、用户表、用户读写接口、管理后台用户管理接口
- Flutter：AI 聊天页、登录资料同步、错误提示、聊天记录缓存
- Web 管理后台：用户管理页新增 AI 积分展示、发放入口和积分流水

### 验收重点
- 新用户进入 AI 页面时，应看到“无积分引导态”，不能发送消息
- 后台给某个用户名发 1 积分后，该用户重新进入 AI 页面可以发送；成功收到首字后余额应减 1
- 同一个用户退出再进入，聊天记录应恢复；换账号后不应串历史记录
- 管理后台用户列表和详情里能看到 AI 积分，发放后余额和流水应立即刷新

## 2026-03-19-03

### 这版一句话

新增"小咔"AI 投资助手：后端 SSE 流式对话 + Flutter 聊天页 + 管理后台供应商配置。

### 主要变化
- **后端 AI 聊天端点**：新增 `POST /api/ai/chat`（SSE 流式返回），支持 Anthropic Claude 和 OpenAI 兼容协议（DeepSeek/OpenAI/Gemini/智谱等）双 provider 切换
- **数据上下文注入**：新增 [ai_context_builder.py](kona_tool/ai_context_builder.py)，每次对话自动聚合用户持仓明细、资产趋势、盈亏排行、市场状态注入 system prompt
- **管理后台 AI 配置**：新增 [AdminAiPage.vue](web/src/pages/admin/AdminAiPage.vue)，支持多供应商 CRUD、测试连通性、动态拉取模型列表、一键切换激活供应商
- **后端供应商管理**：新增 [admin_routes_ai.py](kona_tool/admin_routes_ai.py)，6 种预置供应商类型（DeepSeek/OpenAI/Anthropic/Gemini/智谱/自定义），API Key 脱敏存储
- **Flutter 聊天页**：新增 [ai_chat_page.dart](flutter/lib/pages/ai_chat_page.dart)，首页入口按钮，4 个预设快捷问题，Markdown 渲染，流式逐字显示，支持取消发送
- **新增依赖**：后端 `anthropic` + `openai`；Flutter `flutter_markdown`

### 影响范围
- 后端：新增 4 个 Python 文件，修改 app_factory/admin_routes/config/requirements
- Flutter：新增 3 个文件，修改 home_page/api_config/api_service/pubspec
- Web 管理后台：新增 AdminAiPage，侧边栏增加"AI 助手"入口

### 验收重点
- 管理后台配置 AI 供应商后，测试连通性正常
- Flutter 端发送消息能收到流式回复，Markdown 渲染正常
- AI 回复中包含用户真实持仓数据（非通用回答）

## 2026-03-19-02

### 这版一句话

后端时间统一北京时间 + Flutter 多项 UI 修复 + Web 端 F5 刷新数据不更新修复。

### 主要变化
- **后端时间统一**：所有 SQLite 写入从 `CURRENT_TIMESTAMP`(UTC) 改为 `datetime('now','localtime')`(北京时间)，涉及 db_schema/db_portfolio/db_snapshots/db_users 等全部写入点；新增 [012 迁移脚本](kona_tool/migrations/012_timestamps_utc_to_local.py) 将已有数据 +8 小时；`auth_refresh_tokens` 保持 UTC
- **资产历史页**：新增 [asset_history_page.dart](flutter/lib/pages/asset_history_page.dart)，首页大卡片点击跳转，含折线图 + 饼图 + 日变动列表
- **fl_chart 桌面端修复**：macOS/Windows/Linux 禁用触摸事件，防止 setState 风暴卡死
- **饼图交互修复**：单击切换选中，中心百分比动态更新
- **输入框样式修复**：[asset_adjust_dialog.dart](flutter/lib/widgets/asset_adjust_dialog.dart) 和 [add_asset_dialog.dart](flutter/lib/widgets/add_asset_dialog.dart) 修复文字偏移和底色阴影（ClipRRect + isDense + filled transparent）
- **时间解析简化**：[asset_item_detail_page.dart](flutter/lib/pages/asset_item_detail_page.dart) 移除前端 UTC 转换逻辑（后端已统一北京时间）
- **Web 刷新修复**：[refreshCoordinator.ts](web/src/stores/refreshCoordinator.ts) 页面首次加载时清除 syncVersions 强制拉取完整数据，解决 F5 后数据不更新

### 影响范围
- 后端所有时间写入（除 JWT token 外）
- Flutter 资产历史页、资产详情页、资产编辑弹窗
- Web 端数据同步机制

### 验收重点
- 资产详情页时间显示为北京时间
- 资产历史页图表交互流畅（桌面端不卡顿）
- 编辑资产弹窗输入框无偏移和阴影
- Web 端 F5 刷新后数据正常更新（无需退出登录）

## 2026-03-19-01

### 这版一句话

资产调整弹窗改为乐观提交（即时关闭），历史列表加静态缓存（再次进入秒开）。

### 主要变化
- [asset_adjust_dialog.dart](flutter/lib/widgets/asset_adjust_dialog.dart)：`_submit` 验证通过后立即 pop 并显示成功 toast，API 在后台异步执行；失败时在 hostContext 补一条错误 toast。移除 `_saving` 等待状态。
- [asset_item_detail_page.dart](flutter/lib/pages/asset_item_detail_page.dart)：新增 `static Map<String, List<_AdjustRecord>> _cache`，`_loadHistory` 先展示缓存（有则秒开），再后台刷新并更新缓存；乐观插入新记录后同步写入缓存，下次进入可即时看到最新记录。

### 影响范围
- 资产调整弹窗的保存体验：从等待 3 秒变为即时关闭
- 资产详情页历史列表：首次进入仍需加载，再次进入秒开

### 验收重点
- 填完金额点确认，弹窗立即关闭并显示「已记录」，记录出现在列表顶部
- 退出详情页再进入，历史列表立即展示（无 loading），随后数据静默刷新
- 网络异常时保存应在后台失败后弹出错误 toast

## 2026-03-18-13

### 这版一句话

修复资产调整记录时间显示偏移 8 小时的问题。

### 主要变化
- [asset_item_detail_page.dart](flutter/lib/pages/asset_item_detail_page.dart)：解析服务端 `created_at`（UTC）后调用 `.toLocal()`，转为本地时区再显示。

### 影响范围
- 资产详情页调整记录列表的时间显示

### 验收重点
- 新增一条调整记录后，列表中显示的时间应与本地当前时间一致

## 2026-03-18-12

### 这版一句话

修复排行榜初始 loading 遮罩；新快讯提示从全宽横幅改为居中浮动胶囊。

### 主要变化
- [analysis_page.dart](flutter/lib/pages/analysis_page.dart)：`AnalysisRankAllPage` 的 `_loading` 初始值从 `true` 改为 `false`，避免首次渲染出现多余 loading 遮罩。
- [news_page.dart](flutter/lib/pages/news_page.dart)：新快讯提示改为居中浮动胶囊（`BorderRadius.circular(20)` + 蓝色阴晕），加入 `TweenAnimationBuilder` 滑入淡出动画（easeOutBack 320ms），视觉更轻量。

### 影响范围
- 分析页持仓排行全列表的初始渲染状态
- 快讯页有新快讯时的横幅样式和动画

### 验收重点
- 进入排行全列表页面，不应出现短暂 loading 遮罩
- 快讯页下滑后出现新快讯时，应看到居中胶囊从顶部滑入

## 2026-03-18-11

### 这版一句话

资产调整记录功能：支持对现金/其他资产/负债做增减操作，并持久化记录每次调整历史。

### 主要变化
- [db_asset_adjustments.py](kona_tool/core/db_asset_adjustments.py)：新增 `AssetAdjustmentDatabaseMixin`，包含 `add_asset_adjustment`（单事务更新余额 + 写记录）和 `get_asset_adjustments` 两个方法。
- [db_schema.py](kona_tool/core/db_schema.py)：新增 `asset_adjustments` 表（asset_type/asset_id/mode/delta/note/balance_after）及索引。
- [db.py](kona_tool/core/db.py)：`DatabaseManager` 继承 `AssetAdjustmentDatabaseMixin`。
- [asset_adjustment_handlers.py](kona_tool/asset_adjustment_handlers.py) + [asset_adjustment_routes.py](kona_tool/asset_adjustment_routes.py)：`POST/GET /api/assets/<type>/<id>/adjustments`，遵循已有 handler factory + Blueprint 规范。
- [app_factory.py](kona_tool/app_factory.py)：注册新 Blueprint。
- [asset_item_detail_page.dart](flutter/lib/pages/asset_item_detail_page.dart)：新增资产详情页，含余额卡片 + 调整记录列表（initState 从 API 加载历史，新增后乐观插入顶部）。
- [asset_adjust_dialog.dart](flutter/lib/widgets/asset_adjust_dialog.dart)：增加/减少弹窗，调 `adjustAsset` API，`balance_after` 取自服务端返回值。
- [asset_detail_page.dart](flutter/lib/pages/asset_detail_page.dart)：点击资产卡片跳转详情页（有 id）或原编辑弹窗（无 id 兜底）。
- [app_state.dart](flutter/lib/providers/app_state.dart) / [app_asset_write_state.dart](flutter/lib/providers/app_asset_write_state.dart) / [api_service.dart](flutter/lib/services/api_service.dart)：新增 `adjustAsset` + `getAssetAdjustments`。

### 影响范围
- 现金账户、其他资产、负债的资产卡片点击行为（从弹窗改为跳转详情页）
- 新增调整记录写入数据库并影响资产余额

### 验收重点
- 点击资产卡片 → 进入详情页，显示余额卡片和历史记录列表
- 点击编辑图标 → 弹窗选增加/减少，填金额和备注，确认后余额更新、记录出现在列表顶部
- 重启 App 后历史记录仍然存在（从服务端加载）
- 删除资产后详情页自动返回

## 2026-03-18-10

### 这版一句话

修复投资页两个计算缺陷：加仓当日 day_pnl 虚高、减仓后 total_pnl_rate 分母缩水导致收益率虚高。

### 主要变化
- [db_portfolio.py](kona_tool/core/db_portfolio.py)：新增 `get_today_buy_transactions(date_str, user_id)` 方法，按 code 聚合当日加仓的 qty 和 amount。
- [portfolio_metrics.py](kona_tool/core/portfolio_metrics.py)：
  - `build_portfolio_items_with_metrics` 新增可选参数 `today_buys`；有加仓时按"昨持仓份额用昨收价、新买入份额用实际均价"修正当日盈亏，避免今日新买入被错误地算入昨收价差。
  - `total_pnl_rate` 分母改为 `|持仓成本| + max(0, adjustment)`，减仓后持仓成本缩减时不再导致收益率虚高。
- [portfolio_read_service.py](kona_tool/core/portfolio_read_service.py)：`_enrich_items_with_metrics` 新增 `user_id` 参数，内部拉取今日加仓记录并传给 `build_portfolio_items_with_metrics`。
- [snapshot.py](kona_tool/core/snapshot.py)：`calculate_portfolio_stats` 同步应用 day_pnl 修正逻辑，与投资页口径一致。
- [test_read_services.py](kona_tool/tests/test_read_services.py)：阶段记录测试更新（新增 `portfolio.today_buys` 阶段）；`_FakeDb` 补齐 `get_today_buy_transactions` stub。

### 影响范围
- 投资页持仓列表的 `day_pnl`、`day_pnl_rate`：加仓当日更准确
- 投资页持仓列表的 `total_pnl_rate`：重仓减仓后不再虚高
- 分析页总览卡片的 `day_pnl`（通过 `calculate_portfolio_stats`）：加仓当日更准确

### 验收重点
- 加仓后当日盈亏应接近 0（若加仓时价格接近实时价）
- 重仓减仓后总收益率不应突然大幅跳升

## 2026-03-18-09

### 这版一句话

给 stats_getter 调用加计时日志，方便排查开市期间行情接口的实际响应时间。

### 主要变化
- [analysis_read_service.py](kona_tool/core/analysis_read_service.py)：记录 stats_getter 每次调用的耗时（INFO 级别）；超时时输出实际等待时长（WARNING）；异常时输出错误原因（WARNING）。

### 验收重点
- 开市期间下拉刷新后，在服务端日志中搜索 `stats_getter` 确认实际耗时
- 根据实际耗时决定是否需要调整 `stats_timeout`（当前默认 5 秒）

## 2026-03-18-08

### 这版一句话

分析页刷新不再因实时行情拉取卡住：休市直接走快照，开市加 5 秒超时兜底。

### 主要变化
- [analysis_read_service.py](kona_tool/core/analysis_read_service.py)：`AnalysisReadService` 新增 `all_markets_closed_getter` 和 `stats_timeout` 参数；`_get_day_overview` 在全市场休市时跳过 `stats_getter` 直接返回快照，开市时通过线程池加超时（默认 5 秒）调用，超时或失败均 fallback 到快照。
- [app_factory.py](kona_tool/app_factory.py)：注入 `all_markets_closed_getter`，取自 `market_runtime` 缓存状态（5 秒 TTL）。
- [test_read_services.py](kona_tool/tests/test_read_services.py)：新增三个测试，覆盖休市跳过、开市调用、超时 fallback 三个场景。

### 影响范围
- 分析页下拉刷新响应速度（A 股/港股收盘后立即生效）
- 当日盈亏大卡片的实时性（休市后显示快照值，开市期间仍实时）

### 验收重点
- A 股收盘后下拉刷新应明显变快（不再等待行情接口）
- 开市期间当日盈亏仍为实时值
- 行情接口异常时最多等待 5 秒后自动 fallback，不卡死

## 2026-03-18-07

### 这版一句话

月/年/全部收益率改用期末持仓成本做分母，反映"当前账户里这么多钱赚了多少"。

### 主要变化
- [db_analysis.py](kona_tool/core/db_analysis.py)：`get_pnl_overview` 和 `get_calendar_data` 的月/年/全部三个周期，收益率分母从期初持仓成本改为期末（最新）持仓成本；期末为零时兜底回退到期初。
- [test_calendar_weekend.py](kona_tool/tests/test_calendar_weekend.py)：同步更新三个收益率测试的名称和预期值。

### 影响范围
- 分析页大卡片月/年/全部收益率
- 收益日历底部的 total_rate 汇总数字

### 验收重点
- 加仓后月收益率会相应降低（分母变大），符合"当前账户里有多少钱赚了多少"的语义
- 无持仓数据或期末 total_invest 为零时不报错（兜底到期初）

## 2026-03-18-06

### 这版一句话

排行榜跨货币统一换算为 CNY 后排序，市场拆分日历今日 total_pnl 改为实时值。

### 主要变化
- [analysis_read_service.py](kona_tool/core/analysis_read_service.py)：`AnalysisReadService` 新增 `rates_getter` / `convert_amount` 可选参数；`build_rank_payload` 用 CNY 换算后的金额排序，返回值仍保持原始货币；`build_market_breakdown_payload` 在查询当月时把今日那条 `total_pnl` 替换为实时值（per-market 拆分仍为快照，标记 `source: partial_realtime`）。
- [app_factory.py](kona_tool/app_factory.py)：`AnalysisReadService` 注入 `rates_getter` 和 `convert_amount`。
- [test_read_services.py](kona_tool/tests/test_read_services.py)：新增四个测试，覆盖多货币排序正确性、无换算器时兼容旧行为、市场拆分日历今日实时替换、历史月份不受影响。

### 影响范围
- 分析页盈亏排行榜（跨市场排名更准确）
- 分析页市场拆分日历当月今日的 total_pnl

### 验收重点
- 美股/A股/港股混合持仓时，排行榜排名按 CNY 换算后的收益金额排序
- 市场拆分日历今日 total_pnl 与大卡片当日盈亏一致
- 历史月份市场拆分数据不受影响

### 已知限制
- 市场拆分日历今日的 per-market 拆分（a/hk/us/fund）仍为快照值，不是实时值，因 stats_getter 不返回市场维度拆分数据

## 2026-03-18-05

### 这版一句话

修复盈亏排行"查看全部"卡在加载中的 bug，同时把排行改为用昨收价计算累计盈亏。

### 主要变化
- [analysis_page.dart](flutter/lib/pages/analysis_page.dart)：修复 `_AnalysisRankAllPageState` 初始 `_loading = true` 导致进入页面就被守卫拦截、永远加载不出来的 bug，改为 `false`。
- [analysis_read_service.py](kona_tool/core/analysis_read_service.py)：排行榜盈亏计算从实时价改为昨收价，白天排名不随行情波动，与"累计收益"的语义一致。
- [test_read_services.py](kona_tool/tests/test_read_services.py)：同步更新排行测试预期值。

### 影响范围
- Flutter 分析页"查看全部"子页面
- 分析页盈亏排行榜数字（改用昨收价）

### 验收重点
- 点击"查看全部"能正常显示列表，不再卡加载
- 排行榜盈亏数字白天保持稳定，不随行情跳动
- 本次未做真机验收

## 2026-03-18-04

### 这版一句话

分析页日历今天那格改为实时盈亏，不再显示滞后的快照值。

### 主要变化
- [analysis_read_service.py](kona_tool/core/analysis_read_service.py)：`build_calendar_payload` 在查询当月日视图时，把今天那格的盈亏替换为实时计算值；今天还没有快照时自动补上该格；历史月份不受影响。底部当月累计汇总继续走快照，不变。
- [test_read_services.py](kona_tool/tests/test_read_services.py)：新增三个测试，覆盖今天格替换、无快照时补格、历史月份不受影响三种情况。

### 影响范围
- 分析页收益日历，仅影响当月视图中今天那一格

### 验收重点
- 日历今天那格和大卡片"当日盈亏"数字一致
- 历史日期格子数字不变

## 2026-03-18-03

### 这版一句话

分析页当日盈亏改为实时计算，不再依赖每 2 小时跑一次的快照。

### 主要变化
- [analysis_read_service.py](kona_tool/core/analysis_read_service.py)：新增 `stats_getter` 参数和 `_get_day_overview` 方法，day 数据走实时计算，失败时 fallback 快照。月/年/全部继续走快照不动。
- [app_factory.py](kona_tool/app_factory.py)：注入 `wiring.calculate_portfolio_stats` 作为 `stats_getter`，复用和快照任务同一套实时计算逻辑。
- [test_read_services.py](kona_tool/tests/test_read_services.py)：新增两个测试，覆盖实时路径和 fallback 路径。

### 影响范围
- 分析页大卡片"当日盈亏"显示
- 前端零改动，接口返回格式不变

### 验收重点
- 分析页"当日盈亏"和投资页"今日收益"数字基本一致（口径相同）
- 当天首次快照跑之前不再显示 0

## 2026-03-18-02

### 这版一句话

快照计算对齐投资页口径：场外基金净值未更新时不计入当日盈亏。

### 主要变化
- [snapshot.py](kona_tool/core/snapshot.py)：新增 `nav_update_pending` 判断，场外基金（f_/ft_ 开头且非场内 ETF）在净值未更新时当日收益归零，和投资页 `portfolio_metrics.py` 保持一致，避免把昨天的净值变动错算到今天。

### 影响范围
- 每 2 小时 cron 快照写入的 day_pnl
- 分析页"当日盈亏"读取快照后的显示

### 验收重点
- 分析页"当日盈亏"和投资页"今日收益"数字一致（场外基金部分归零）
- `pytest kona_tool/tests/test_snapshot_runtime.py test_contracts_analysis_snapshot_admin.py test_analysis_api.py test_calendar_weekend.py` 全通过

## 2026-03-18-01

### 这版一句话

修复快照日期错位导致三个页面"今日收益"数字对不上的问题，并加固盘前误算保护。

### 主要变化
- [snapshot.py](kona_tool/core/snapshot.py)：快照日期从 UTC 统一为北京时间，和 cron、服务器时区一致；盘前价格和昨收相同时当日收益归零，避免把昨天涨幅错算到今天。
- [db_snapshots.py](kona_tool/core/db_snapshots.py)：`save_daily_snapshot` 新增 `snapshot_date` 参数，优先用调用方传入的日期，保证快照表和分市场表写同一天。
- [snapshot_runtime.py](kona_tool/snapshot_runtime.py)：`save_snapshot_for_user` 透传 `snapshot_date`，和 `snapshot.py` 同步。
- [db_analysis.py](kona_tool/core/db_analysis.py)：分析页"当日"收益改为直接读快照里的当日收益字段，不再用"今天累计盈亏 - 昨天累计盈亏"差值算法（差值会被新加仓位的历史调整干扰）。
- [test_snapshot_runtime.py](kona_tool/tests/test_snapshot_runtime.py)：mock 签名同步更新。

### 影响范围
- 分析页"当日盈亏"大卡片
- 收益日历的分市场拆分数据
- 每 2 小时 cron 快照写入逻辑

### 验收重点
- 分析页"当日盈亏"和投资页"今日收益"数字一致
- 收益日历各天数字不变，分市场拆分加起来等于当天总收益
- `pytest kona_tool/tests/test_snapshot_runtime.py test_contracts_analysis_snapshot_admin.py test_analysis_api.py test_calendar_weekend.py` 全通过

## 2026-03-19-01

### 这版一句话

把 Flutter 端 AI 助手聊天记录做成本地按用户持久化，退出页面再回来也能继续上次对话。

### 主要变化
- [ai_chat_history_service.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/services/ai_chat_history_service.dart)：新增 AI 聊天记录存储服务，统一负责按用户读写本地历史，避免把存储细节直接塞进页面。
- [chat_message.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/models/chat_message.dart)：补了时间戳序列化和反序列化，保证聊天记录恢复后消息顺序和时间还能保住。
- [ai_chat_page.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/pages/ai_chat_page.dart)：页面进入时会自动恢复当前用户的聊天记录，发送消息、流式返回、报错结束后也会同步落本地。
- [ai_chat_history_service_test.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/test/ai_chat_history_service_test.dart)：补了按用户持久化和用户隔离测试，防止后面把不同账号的聊天记录串在一起。

### 影响范围
- Flutter 端 AI 助手聊天页
- 本地 SharedPreferences 中的 AI 聊天记录缓存

### 验收重点
- 进入 AI 助手页时能恢复上一次聊天记录
- 退出页面再进入，对话内容还在
- 切换不同用户时，不会串用对方的聊天记录

## 2026-03-17-09

### 这版一句话

把 Flutter 端常见英文后端报错统一翻成中文，避免买卖弹窗、登录提示继续把英文原文直接展示给用户。

### 主要变化
- [error_text.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/utils/error_text.dart)：新增 Flutter 端统一错误翻译入口，把 `Request failed: 500`、`Failed to fetch`、`Insufficient cash balance`、`Failed to buy asset with cash` 这类常见英文状态码和后端错误统一翻成中文。
- [api_service.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/services/api_service.dart)：把 HTTP 响应错误、网络异常和 `AssetActionResult` 失败结果统一接到错误翻译入口，后面投资弹窗、资产弹窗这类直接吃 `result.message` 的页面会一起受益，不再原样漏英文。
- [app_session_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_session_state.dart)：保留登录 401 的“用户名/密码错误”特殊提示，同时把其他英文认证异常也统一翻成中文，避免登录页继续直接显示原始英文。
- [error_text_test.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/test/error_text_test.dart) / [app_state_auth_resilience_test.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/test/app_state_auth_resilience_test.dart)：补了通用错误翻译测试和登录英文网络异常回归测试。

### 影响范围
- Flutter 端登录页错误提示
- Flutter 端投资买卖弹窗、资产弹窗的失败提示
- Flutter 端通用 `ApiService` 错误文案口径

### 验收重点
- App 端不再直接显示 `Request failed: 500`、`Failed to fetch`、`Failed to buy asset with cash` 这类英文提示
- `flutter test test/error_text_test.dart test/app_state_auth_resilience_test.dart test/invest_trade_dialog_test.dart` 继续通过
- `flutter analyze --no-fatal-infos --no-fatal-warnings` 继续全绿

## 2026-03-17-08

### 这版一句话

把 Web 端 App 登录页、App 主壳子和浏览器标签页图标统一换成了正式品牌 logo，不再继续显示默认占位图标。

### 主要变化
- [AppShell.vue](/Users/kona/Desktop/kaka/kona_repo/web/src/layouts/AppShell.vue) / [homepage-original.css](/Users/kona/Desktop/kaka/kona_repo/web/src/styles/homepage-original.css)：把 App 主壳子侧边栏顶部的手写折线图标替换成正式品牌图，并保留原有尺寸和阴影，不改周边布局。
- [AppLoginPage.vue](/Users/kona/Desktop/kaka/kona_repo/web/src/pages/app/AppLoginPage.vue)：把登录页顶部的临时折线图标替换成正式品牌图，和首页、下载页现有品牌资源统一。
- [web/index.html](/Users/kona/Desktop/kaka/kona_repo/web/index.html) / [web/app/index.html](/Users/kona/Desktop/kaka/kona_repo/web/app/index.html) / [web/admin/index.html](/Users/kona/Desktop/kaka/kona_repo/web/admin/index.html)：把浏览器标签页 favicon 从 Vite 默认的 `vite.svg` 改成项目自己的 [kaka-logo.png](/Users/kona/Desktop/kaka/kona_repo/web/public/assets/kaka-logo.png)。

### 影响范围
- App 登录页顶部品牌图
- App 主壳子侧边栏品牌图
- Portal / App / Admin 三个入口页的浏览器标签页图标

### 验收重点
- 登录页和 App 主壳子显示正式品牌图，不再出现临时折线图标
- 浏览器标签页不再显示紫黄色 Vite 默认图标
- `npm run build` 继续通过

## 2026-03-17-07

### 这版一句话

修掉了美股用人民币账户买入会报 500 的问题，并把 Web 端常见英文错误提示统一翻成了中文。

### 主要变化
- [app_factory.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/app_factory.py) / [portfolio_handlers.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/portfolio_handlers.py)：把跨币种买入卖出需要的 `rates_getter` 和 `convert_amount` 正式注入到投资处理链里，修掉了美股配人民币现金账户时会因为依赖缺失直接抛 500 的问题。
- [test_portfolio_api.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_portfolio_api.py)：补了一条“美股 + CNY 现金账户”回归测试，防止后面再把跨币种现金买入链路写坏。
- [errorText.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/shared/errorText.ts) / [http.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/shared/http.ts)：新增统一错误翻译入口，`Request failed: 500`、`Missing required fields`、`Insufficient cash balance`、`Failed to fetch` 这类后端英文和网络英文，现在会先翻成中文再给页面使用。
- [InvestTradeModal.vue](/Users/kona/Desktop/kaka/kona_repo/web/src/components/business/InvestTradeModal.vue) / [AppLoginPage.vue](/Users/kona/Desktop/kaka/kona_repo/web/src/pages/app/AppLoginPage.vue) / [AppMePage.vue](/Users/kona/Desktop/kaka/kona_repo/web/src/pages/app/AppMePage.vue) / [AppProfilePage.vue](/Users/kona/Desktop/kaka/kona_repo/web/src/pages/app/AppProfilePage.vue)：把交易弹窗、登录页、个人中心、资料页里会直接吃原始错误文案的地方切到统一中文错误解析，避免继续漏出英文提示。
- [errorText.test.ts](/Users/kona/Desktop/kaka/kona_repo/web/tests/unit/errorText.test.ts)：补了 Web 单测，保证状态码兜底和常见英文错误翻译继续有效。

### 影响范围
- Web 端跨币种现金买入链路
- Web 端通用错误提示文案
- 登录页、投资弹窗、个人中心、资料页的错误展示

### 验收重点
- 美股配人民币账户买入不再 500
- `Request failed: 500`、`Missing required fields`、`Failed to fetch` 这类提示改为中文
- `test_portfolio_api`、`errorText.test.ts`、`httpRequestTrace.test.ts` 和 `npm run build` 继续通过

## 2026-03-17-06

### 这版一句话

修掉了 Web 端“卖出到现金账户”会直接 404 的问题，现在选现金账户卖出会真的减仓并把回款加回对应现金账户。

### 主要变化
- [portfolio_routes.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/portfolio_routes.py) / [app_factory.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/app_factory.py)：补上 `/api/portfolio/sell_to_cash` 路由和注册入口，和 Web 端现有请求地址对齐，不再因为后端缺接口直接返回 404。
- [portfolio_handlers.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/portfolio_handlers.py)：新增“卖出到现金账户”处理链路，补了持仓查找、现金账户查找、跨币种回款换算、撤销 token 和快照异步刷新，错误码也统一收口。
- [db_portfolio.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/db_portfolio.py)：新增 `sell_asset_to_cash`，在原有卖出基础上追加现金账户回款写入，避免前端卖出成功但现金余额不更新。
- [test_portfolio_api.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_portfolio_api.py)：补了一条回归测试，覆盖“卖出到现金账户 -> 持仓减少 -> 现金增加 -> undo 后全部还原”。

### 影响范围
- Web 端投资页选择现金账户的卖出链路
- 后端 `/api/portfolio/sell_to_cash` 新接口
- 投资撤销时对“卖出回款到现金账户”的还原逻辑

### 验收重点
- Web 端选现金账户卖出时不再 404
- 卖出后持仓数量减少，目标现金账户金额同步增加
- `undo` 后持仓和现金都能恢复

## 2026-03-17-05

### 这版一句话

修掉了 Web 端现金买入老场内基金持仓时会拆成第二条记录的问题，避免同一只 ETF 被写成两条持仓。

### 主要变化
- [db_portfolio.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/db_portfolio.py)：给 `buy_asset_with_cash` 补了“优先并到已有 legacy 持仓代码”的兼容逻辑。现在如果线上已经有像 `159655` 这种旧基金代码持仓，现金买入时不会再被写成新的 `sz159655` 持仓，而是会继续并到原来的记录里。
- [portfolio_handlers.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/portfolio_handlers.py)：把现金买入撤销链路里的 `code` 也改成跟最终写入的真实持仓代码一致，避免后面 undo 还在拿新代码找旧持仓。
- [test_portfolio_api.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_portfolio_api.py)：补了一条回归测试，专门覆盖“已有 `159655/fund` 老持仓时，再现金买入 `159655` 应该继续并仓，而不是长出 `sz159655`”。

### 影响范围
- Web / App 的现金账户买入资产接口
- 已有 legacy 场内基金代码持仓的继续加仓行为
- 投资撤销时对这类兼容持仓的还原逻辑

### 验收重点
- 线上已有 `159655` 这类旧基金持仓时，再买入不会再长出第二条 `sz159655`
- `/api/portfolio` 返回里只保留原持仓代码，数量正确累加
- `test_portfolio_api` 继续全绿，普通现金买入和撤销不受影响

## 2026-03-17-04

### 这版一句话

把 `request_id` 排障从“能查日志”继续推进到“顺手能查”，并把关键写接口和认证链路也补上阶段追踪。

### 主要变化
- [request_id_trace.py](/Users/kona/Desktop/kaka/kona_repo/scripts/request_id_trace.py) / [scripts/README.md](/Users/kona/Desktop/kaka/kona_repo/scripts/README.md)：新增一个零依赖排障脚本，输入 `request_id` 就能直接回查本地日志或 `journalctl`，把请求摘要、阶段耗时和相关日志一起捞出来，不用再手工翻整段日志。
- [asset_account_handlers.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/asset_account_handlers.py) / [portfolio_handlers.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/portfolio_handlers.py) / [auth_routes.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/auth_routes.py)：给资产增删改、投资买卖改删、撤销、登录、注册、刷新、登出、改密码、资料更新这些关键写链路补上阶段追踪，后端现在能进一步看出是校验慢、查库慢、写库慢、发 token 慢，还是写完后的快照慢。
- [core/auth.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/auth.py) / [core/db_admin_state.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/db_admin_state.py)：把剩余 `datetime.utcnow()` 换成明确的 UTC 时间写法，减少 Python 新版本下的弃用噪音，也避免刷新令牌过期判断继续混用 naive / aware 时间。
- [test_asset_account_api.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_asset_account_api.py) / [test_portfolio_api.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_portfolio_api.py) / [test_auth_rate_limit.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_auth_rate_limit.py) / [test_admin_users_password_reset.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_admin_users_password_reset.py) / [请求追踪与排障手册.md](/Users/kona/Desktop/kaka/kona_repo/docs/请求追踪与排障手册.md)：补了关键写接口阶段追踪的回归断言，并把登录异常、投资页数据不对、分析页慢、sync 异常、用户说“刚刚不对”这些固定场景写成可直接照着查的剧本。

### 影响范围
- 后端资产 / 投资 / 认证关键写接口的响应头和请求摘要日志
- 本地和线上按 `request_id` 排障的操作方式
- 刷新令牌和认证时间处理的 UTC 口径

### 验收重点
- 关键写接口响应头里能看到 `X-Trace-Stage-Count`
- `python3 scripts/request_id_trace.py req-xxxx` 能正确输出摘要和相关日志
- 认证链路继续正常发 token，刷新令牌过期判断不受影响

## 2026-03-17-03

### 这版一句话

把已经废弃的 `docs/plans` 正式从仓库里删除，避免后面继续把历史草稿当成还在维护的正式文档。

### 主要变化
- 删除 [docs/plans/2026-02-03-baseline-tests-implementation.md](/Users/kona/Desktop/kaka/kona_repo/docs/plans/2026-02-03-baseline-tests-implementation.md) / [docs/plans/2026-02-03-performance-stability-design.md](/Users/kona/Desktop/kaka/kona_repo/docs/plans/2026-02-03-performance-stability-design.md) / [docs/plans/2026-02-03-swr-performance-implementation.md](/Users/kona/Desktop/kaka/kona_repo/docs/plans/2026-02-03-swr-performance-implementation.md) / [docs/plans/手机客户端访问改造成类似Flutter体验方案.md](/Users/kona/Desktop/kaka/kona_repo/docs/plans/手机客户端访问改造成类似Flutter体验方案.md)，把这组已经确认废弃的计划草稿正式从 Git 里移除。
- 这次没有新增功能和代码逻辑改动，只是把仓库里的废弃文档状态收口，避免它们反复出现在工作区脏改动里。

### 影响范围
- 仓库里的历史计划草稿目录
- 工作区状态判断和后续文档维护边界

### 验收重点
- `docs/plans` 不再作为 Git 跟踪目录存在
- 仓库里没有正式文档继续引用这组废弃计划文件

## 2026-03-17-02

### 这版一句话

继续把后端数据层里“数据库结构初始化”这一坨从 `db.py` 拿出去，并把阶段追踪补到更多高频 API。

### 主要变化
- [db_schema.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/db_schema.py) / [db.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/db.py)：把建表、旧库补列、基础索引这些数据库结构初始化逻辑，从 `DatabaseManager` 里收成单独结构模块，`db.py` 继续保留连接入口和 mixin 主入口，不再自己硬扛整套 schema 细节。
- [sync_handlers.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/sync_handlers.py) / [quote_handlers.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/quote_handlers.py) / [market_handlers.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/market_handlers.py)：给 `sync/bootstrap`、行情、搜索、汇率、市场状态这些高频接口补了阶段追踪，后端现在不只是能看投资页 / 分析页慢在哪，连同步和行情链路也能拆到更细阶段。
- [test_database_schema.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_database_schema.py) / [test_quote_api.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_quote_api.py) / [test_market_api.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_market_api.py) / [test_sync_bootstrap_api.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_sync_bootstrap_api.py)：补了数据库结构初始化和接口阶段追踪的回归测试，防止后面有人把这层边界又写回去。
- [README_STRUCTURE.md](/Users/kona/Desktop/kaka/kona_repo/kona_tool/README_STRUCTURE.md) / [README_结构说明.md](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/README_结构说明.md) / [请求追踪与排障手册.md](/Users/kona/Desktop/kaka/kona_repo/docs/请求追踪与排障手册.md)：同步更新目录说明和排障手册，明确 `db_schema.py` 的职责，以及现在哪些 API 已经支持阶段级排障。

### 影响范围
- 后端数据库结构初始化入口
- `sync / market / quote` 相关接口的响应头和请求摘要日志
- 后端数据库初始化和行情同步链路的后续维护方式

### 验收重点
- 数据库初始化后，核心表和索引继续正常创建
- `sync / market / quote` 相关接口响应头里能看到 `X-Trace-Stage-Count`
- 这些高频接口的日志里能看到更细的阶段摘要

## 2026-03-17-01

### 这版一句话

继续收紧后端数据层边界，并把请求追踪从“只知道整条请求多久”升级成“能看出慢在哪一段”。

### 主要变化
- [portfolio_read_service.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/portfolio_read_service.py) / [history_read_service.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/history_read_service.py) / [analysis_read_service.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/analysis_read_service.py)：把实时持仓、历史曲线、分析页概览/日历/排行这些读链路，从 handler 和 `app_factory.py` 里继续抽成明确读侧服务，减少“参数解析、查库、取价、拼结果”混在一层。
- [portfolio_metrics.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/portfolio_metrics.py) / [portfolio_handlers.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/portfolio_handlers.py) / [analysis_handlers.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/analysis_handlers.py) / [misc_handlers.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/misc_handlers.py)：把实时持仓指标统一口径从 handler 里拿出来，handler 现在主要保留参数解析和返回，后面查 bug 时更容易分清是“读模型错了”还是“路由入口错了”。
- [request_trace.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/request_trace.py) / [request_runtime.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/request_runtime.py)：新增请求级阶段耗时记录，API 响应头现在会返回 `X-Trace-Stage-Count` 和 `X-Trace-Stage-Total-Ms`，后端日志会把 `db / quotes / rates / market / assemble` 这类阶段摘要写出来，线上慢请求以后不再只能看总耗时。
- [test_request_runtime.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_request_runtime.py) / [test_read_services.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_read_services.py)：补了请求阶段追踪和读侧服务边界的单测，避免这轮治理以后被人无意写回老路。
- [请求追踪与排障手册.md](/Users/kona/Desktop/kaka/kona_repo/docs/请求追踪与排障手册.md) / [kona_tool/README_STRUCTURE.md](/Users/kona/Desktop/kaka/kona_repo/kona_tool/README_STRUCTURE.md) / [core/README_结构说明.md](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/README_结构说明.md)：把新边界和新排障方式写进目录说明和手册，后面接手的人不用再猜“读链路到底落哪、慢请求该怎么看”。

### 影响范围
- 后端实时持仓、历史曲线、分析页的读侧拼装路径
- 后端 API 响应头和请求摘要日志
- 后端排障方式与线上慢请求定位效率

### 验收重点
- `/api/portfolio`、`/api/history`、`/api/analysis/*` 继续按原口径返回
- API 响应头里继续带 `X-Request-Id`，并能看到 `X-Trace-Stage-Count` / `X-Trace-Stage-Total-Ms`
- 后端日志里能按同一个 `request_id` 看到阶段摘要，不再只剩总耗时

## 2026-03-16-20

### 这版一句话

把 Flutter 客户端历史 warning / info 清到 `flutter analyze` 全绿，减少后续维护噪音，让真问题更容易被看见。

### 主要变化
- [invest_page.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/pages/invest_page.dart) / [invest_trade_dialog.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/widgets/invest_trade_dialog.dart)：删除已经失效的样式字段、废弃 helper 和未使用弹层逻辑，保留现有行为不变，避免后面继续在遗留死代码上长新逻辑。
- [analysis_page.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/pages/analysis_page.dart) / [profile_page.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/pages/profile_page.dart) / [profile_custom_dialog.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/widgets/profile_custom_dialog.dart)：把过时的 `withOpacity`、`activeColor` 和若干旧写法替换成当前 Flutter 版本推荐写法，减少升级时的兼容噪音。
- [portfolio.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/models/portfolio.dart) / [home_page.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/pages/home_page.dart) / [asset_detail_page.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/pages/asset_detail_page.dart) / [add_funding_account_dialog.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/widgets/add_funding_account_dialog.dart)：清理无意义变量、未使用 import 和回调参数噪音，保证这些基础文件以后更适合继续维护。
- [flutter/test](/Users/kona/Desktop/kaka/kona_repo/flutter/test) 下多份测试：统一清掉旧的命名噪音和未使用测试参数，保证测试代码本身也不再持续制造 analyze 噪音。
- [请求追踪与排障手册.md](/Users/kona/Desktop/kaka/kona_repo/docs/请求追踪与排障手册.md) / [docs/README.md](/Users/kona/Desktop/kaka/kona_repo/docs/README.md) / [README.md](/Users/kona/Desktop/kaka/kona_repo/README.md)：补了一份能直接拿来排障的请求追踪手册，并把入口挂到仓库主 README 和 docs 导航，避免后面新增能力却没人知道怎么用。

### 影响范围
- Flutter 客户端静态检查结果
- Flutter 主要页面和交易弹层的遗留代码噪音
- Flutter 测试文件的可读性与后续维护成本

### 验收重点
- `flutter analyze --no-fatal-infos --no-fatal-warnings` 现在应为 `No issues found!`
- Flutter 全量测试继续通过，投资页、交易弹层、分析页、个人页相关行为不变

## 2026-03-16-19

### 这版一句话

补齐跨端请求追踪和正式 Web 烟测，把“请求出了问题到底是哪一条链路坏了”这件事从靠猜变成可查。

### 主要变化
- [request_runtime.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/request_runtime.py) / [test_request_runtime.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_request_runtime.py)：后端为所有 API 请求统一生成或透传 `X-Request-Id`，并把 `request_id / method / path / status / duration_ms / user_id / ip` 写进请求摘要日志，认证审计日志也会带上同一个 request id。
- [http.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/shared/http.ts) / [requestTrace.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/shared/requestTrace.ts) / [AppProfilePage.vue](/Users/kona/Desktop/kaka/kona_repo/web/src/pages/app/AppProfilePage.vue)：Web 端统一给请求补 `X-Request-Id`，POST JSON 会自动补 `request_id`，直接 `fetch` 的恢复数据入口也补上追踪头；请求失败时，错误对象会保留后端返回的 request id。
- [api_service.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/services/api_service.dart) / [api_service_request_trace_test.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/test/api_service_request_trace_test.dart)：Flutter 的 `ApiService` 也统一带追踪头，写请求会自动补 `request_id`，后面查 App 端接口问题时能和后端日志对上。
- [smoke.spec.ts](/Users/kona/Desktop/kaka/kona_repo/web/tests/e2e/smoke.spec.ts) / [playwright.config.ts](/Users/kona/Desktop/kaka/kona_repo/web/playwright.config.ts) / [seed_web_e2e_db.py](/Users/kona/Desktop/kaka/kona_repo/scripts/ci/seed_web_e2e_db.py) / [start_web_e2e_backend.sh](/Users/kona/Desktop/kaka/kona_repo/scripts/ci/start_web_e2e_backend.sh)：新增正式 Web smoke，自动起本地后端和前端，覆盖登录、首页、投资页、分析页主链路，并校验接口返回里确实带有 `X-Request-Id`。
- [deploy.yml](/Users/kona/Desktop/kaka/kona_repo/.github/workflows/deploy.yml) / [web/tests/README.md](/Users/kona/Desktop/kaka/kona_repo/web/tests/README.md) / [package.json](/Users/kona/Desktop/kaka/kona_repo/web/package.json)：把 Web smoke 接进前端门禁，正式 `test:e2e` 改成长期保的 smoke，全部 Playwright 用 `test:e2e:all` 单独跑。

### 影响范围
- 后端 API 日志与认证审计日志
- Web / Flutter 发起的接口请求头与写请求体
- Web 正式页面验收和 GitHub Actions 前端门禁

### 验收重点
- 后端 API 响应头里继续带 `X-Request-Id`，日志里能按同一个 request id 串起来
- Web smoke 继续能覆盖登录、首页、投资页、分析页主链路，并稳定通过

## 2026-03-16-18

### 这版一句话

继续拆 Web 首页状态：把首页的资产列表、市场卡片、历史快照、趋势线和刷新编排从页面里拆到独立 home store。

### 主要变化
- [home.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/stores/home.ts) / [AppHomePage.vue](/Users/kona/Desktop/kaka/kona_repo/web/src/pages/app/AppHomePage.vue)：把首页读侧状态、市场卡片缓存恢复、历史快照加载、趋势线加载和首页刷新编排，从页面脚本拆到独立 home store，页面主要保留展示计算、筛选和弹窗交互。
- [homeStore.test.ts](/Users/kona/Desktop/kaka/kona_repo/web/tests/unit/homeStore.test.ts) / [stores/index.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/stores/index.ts)：补首页 store 回归测试和导出，确保首页初始化、静态刷新、行情刷新和自动刷新入口继续能走通。
- [README_页面与状态地图.md](/Users/kona/Desktop/kaka/kona_repo/web/src/README_页面与状态地图.md)：更新 Web 状态地图，明确首页读侧状态现在不再由页面自己扛。

### 影响范围
- Web 首页首次加载
- Web 首页的资产列表、市场卡片和历史快照刷新
- Web 首页持仓卡片趋势线的加载与刷新

### 验收重点
- 首页继续能正常显示现金、其他、负债、市场卡片和资产趋势图
- 首页进入后仍会自动刷新行情，投资交易成功后首页数据继续能同步更新

## 2026-03-16-17

### 这版一句话

继续拆 Web 页面状态：把分析页的缓存、周期选择和数据加载编排从页面里拆到独立 analysis store。

### 主要变化
- [analysis.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/stores/analysis.ts) / [AppAnalysisPage.vue](/Users/kona/Desktop/kaka/kona_repo/web/src/pages/app/AppAnalysisPage.vue)：把盈亏概览、收益日历、排行榜的缓存恢复、接口加载、周期选择和刷新编排，从页面脚本拆到独立 analysis store，页面主要保留展示格式化和少量 UI 状态。
- [stores/index.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/stores/index.ts) / [README_页面与状态地图.md](/Users/kona/Desktop/kaka/kona_repo/web/src/README_页面与状态地图.md)：补导出和状态地图，明确分析页现在不再自己扛整套数据状态。

### 影响范围
- Web 分析页的首次加载
- Web 分析页的本地缓存恢复
- Web 分析页的日 / 月 / 年周期切换

### 验收重点
- 分析页继续能正常显示盈亏概览、收益日历和排行榜
- 切换日 / 月 / 年周期后，选择器和列表仍按原来口径更新

## 2026-03-16-16

### 这版一句话

继续拆 Web 状态总入口：把登录恢复、认证入口和路由初始化判断收成独立会话协调层。

### 主要变化
- [sessionCoordinator.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/stores/sessionCoordinator.ts) / [composables.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/stores/composables.ts)：把 `bootstrap / login / register / logout` 从统一入口里进一步下沉到独立会话协调层，`composables` 继续保留对外兼容接口不变。
- [router.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/router.ts) / [router_admin.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/router_admin.ts)：路由守卫不再通过 `useKonaStore()` 间接走认证恢复，改成直接走 `sessionCoordinator` 做登录恢复和权限判断。
- [composablesSessionCoordinator.test.ts](/Users/kona/Desktop/kaka/kona_repo/web/tests/unit/composablesSessionCoordinator.test.ts) / [README_页面与状态地图.md](/Users/kona/Desktop/kaka/kona_repo/web/src/README_页面与状态地图.md)：补回归测试和状态地图，明确 Web 初始化职责的新落点。

### 影响范围
- Web 登录页 / 注册页的认证入口
- App 与 Admin 路由守卫的登录恢复
- 首次进入页面时的会话恢复与缓存恢复顺序

### 验收重点
- 登录页、注册页、管理后台登录继续能正常进入目标页面
- App / Admin 路由守卫继续按登录态和管理员权限正确跳转

## 2026-03-16-15

### 这版一句话

继续拆 Web 状态总入口：把 `composables.ts` 里的刷新编排、缓存恢复和页面恢复副作用拆到独立刷新协调层。

### 主要变化
- [refreshCoordinator.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/stores/refreshCoordinator.ts) / [composables.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/stores/composables.ts)：把 `refreshAll / refreshStaticOnly / refreshQuotesOnly / startAutoRefresh / stopAutoRefresh`、按用户缓存恢复，以及页面回到前台后的自动刷新恢复，从统一入口拆到独立 `refreshCoordinator`。
- [composablesRefreshCoordinator.test.ts](/Users/kona/Desktop/kaka/kona_repo/web/tests/unit/composablesRefreshCoordinator.test.ts)：补一条回归测试，确保页面继续从 `useKonaStore()` 拿刷新能力，外部调用方式不变。
- [README_页面与状态地图.md](/Users/kona/Desktop/kaka/kona_repo/web/src/README_页面与状态地图.md)：补充 Web 状态地图，明确 `composables` 现在主要负责组合入口，刷新总控已经独立。

### 影响范围
- Web 登录后首次缓存恢复
- Web 首页 / 投资页的静态刷新与行情刷新
- Web 页面切回前台后的自动刷新恢复

### 验收重点
- `useKonaStore()` 对外公开的刷新方法保持不变
- 首页、投资页继续能正常触发静态刷新、行情刷新和自动刷新

## 2026-03-16-14

### 这版一句话

把部署链路里的 artifact 上传下载也去掉，彻底清掉最后一条 Node 20 提醒。

### 主要变化
- [.github/workflows/deploy.yml](/Users/kona/Desktop/kaka/kona_repo/.github/workflows/deploy.yml)：删除前端门禁里的 `Package Web artifact / Upload Web artifact`，不再走 GitHub artifact 中转。
- [.github/workflows/deploy.yml](/Users/kona/Desktop/kaka/kona_repo/.github/workflows/deploy.yml)：`Deploy to Production` 改成自己 `checkout`、安装 Web 依赖、重新构建 `web/dist`，再直接打包上传服务器。
- [.github/workflows/deploy.yml](/Users/kona/Desktop/kaka/kona_repo/.github/workflows/deploy.yml)：这样可以彻底移除 `actions/download-artifact` 的 Node 20 运行时提醒，代价是部署阶段会比之前慢一点。

### 影响范围
- GitHub Actions 部署阶段
- Web 构建产物的生成方式
- 工作流整体耗时

### 验收重点
- `Deploy to Production` 继续能完整通过
- 工作流 annotation 里不再出现 Node 20 弃用提醒

## 2026-03-16-13

### 这版一句话

清理 GitHub Actions 里的 Node 20 弃用提醒，把还能升级的官方 action 全部升到 Node 24 版本。

### 主要变化
- [.github/workflows/deploy.yml](/Users/kona/Desktop/kaka/kona_repo/.github/workflows/deploy.yml)：把 `actions/setup-java` 从 `v4` 升到 `v5`，改用 Node 24 运行时。
- [.github/workflows/deploy.yml](/Users/kona/Desktop/kaka/kona_repo/.github/workflows/deploy.yml)：把 `dorny/paths-filter` 从 `v3` 升到 `v4`，改用 Node 24 运行时。
- [.github/workflows/deploy.yml](/Users/kona/Desktop/kaka/kona_repo/.github/workflows/deploy.yml)：把 `actions/upload-artifact`、`actions/download-artifact` 从 `v4` 升到 `v6`，清掉产物上传下载链路里的 Node 20 提醒。

### 影响范围
- GitHub Actions 前端门禁
- GitHub Actions 生产部署链路
- 工作流运行时兼容性

### 验收重点
- `Deploy to Production` 继续能完整通过
- 这次工作流里不再出现 `setup-java`、`paths-filter`、`upload-artifact`、`download-artifact` 的 Node 20 弃用提醒

### 补充说明
- 这轮继续把前端门禁里的内置缓存先关掉，直接清掉最后剩下的 `actions/cache@v4` 提醒；代价是 CI 速度会比之前慢一点，但发布链路会更干净。

## 2026-03-16-12

### 这版一句话

把 GitHub Actions 的生产部署链路补稳，重点处理服务器端 `git fetch` 偶发挂住的问题。

### 主要变化
- [.github/workflows/deploy.yml](/Users/kona/Desktop/kaka/kona_repo/.github/workflows/deploy.yml)：给服务器端 `git fetch --depth=1 origin main` 增加 `45` 秒超时、5 次重试、失败日志输出和卡死进程清理，不再无限挂在 `SSH and deploy`。
- [.github/workflows/deploy.yml](/Users/kona/Desktop/kaka/kona_repo/.github/workflows/deploy.yml)：部署时显式记录 `target sha / current sha / fetched sha`，并在成功后优先 `reset --hard` 到本次工作流的目标提交，不再只靠远端分支名隐式推进。
- [.github/workflows/deploy.yml](/Users/kona/Desktop/kaka/kona_repo/.github/workflows/deploy.yml)：当远端拉取仍失败时，额外打印 `git remote`、分支状态、`ls-remote` 和 GitHub 连通性诊断，后面查发布卡点不用再靠猜。

### 影响范围
- GitHub Actions 生产部署链路
- 服务器端代码拉取和发布稳定性
- 发布失败时的日志可读性

### 验收重点
- `Deploy to Production` 不再因为服务器端 `git fetch` 长时间挂住而卡死
- 部署失败时，日志里能直接看出是拉代码失败、网络问题还是目标提交没拉到

## 2026-03-16-11

### 这版一句话

继续拆 Flutter `AppState`：把刷新入口、结果状态和 bindings 胶水从总控里拆到独立刷新协调层。

### 主要变化
- [app_refresh_coordinator_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_refresh_coordinator_state.dart) / [app_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_state.dart)：把 `portfolioLoaded`、`lastHydrateResult`、`lastRefreshResult`、`AppRefreshBindings` 组装，以及 `hydrateFromCache / refreshHomeData / refreshByVersion / refreshAll / refreshPortfolio / loadExchangeRates` 的外层入口，从 `AppState` 拆成独立刷新协调层，`AppState` 继续保留公开接口不变。
- [app_state_cache_test.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/test/app_state_cache_test.dart)：补充刷新恢复后的公开状态断言，确保缓存恢复不仅数据对，`lastHydrateResult` 也能对上。
- [README_页面与状态地图.md](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/README_页面与状态地图.md)：补充 Flutter 状态拆分地图，明确刷新协调层的新落点。

### 影响范围
- Flutter 冷启动缓存恢复
- Flutter 首页刷新 / 增量刷新 / 全量刷新入口
- Flutter 刷新状态记录与 `portfolioLoaded` 对外读取

### 验收重点
- `hydrateFromCache / refreshAll / refreshByVersion / refreshHomeData` 公开入口保持原行为
- 缓存恢复后 `portfolioLoaded` 和 `lastHydrateResult` 继续可用

## 2026-03-16-10

### 这版一句话

继续拆 Flutter `AppState`：把新增持仓、买卖、调仓、删持仓和带现金账户交易编排从总控里拆到独立投资写操作层。

### 主要变化
- [app_investment_write_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_investment_write_state.dart) / [app_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_state.dart)：把新增持仓、买入、卖出、手动调整、删除持仓，以及带现金账户的买卖和乐观更新回滚，从 `AppState` 拆成独立投资写操作层，`AppState` 继续保留公开接口不变。
- [app_investment_write_state_test.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/test/app_investment_write_state_test.dart) / [app_state_smoke_test.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/test/app_state_smoke_test.dart)：补充投资写操作单测，并继续用现有 smoke test 兜住 `AppState` 对外调用方式不变。
- [README_页面与状态地图.md](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/README_页面与状态地图.md) / [AppState职责清单.md](/Users/kona/Desktop/kaka/工作笔记/AppState职责清单.md) / [AppState方法分组清单.md](/Users/kona/Desktop/kaka/工作笔记/AppState方法分组清单.md)：更新 Flutter 状态拆分地图和职责说明，明确投资写操作的新落点。

### 影响范围
- Flutter 投资资产新增、加仓、卖出、手动调整、删除
- Flutter 带现金账户的买入 / 卖出
- Flutter 投资交易失败时的乐观回滚和首页总额联动

### 验收重点
- 新增持仓、买入、卖出、带现金账户交易保持原行为
- 投资写操作失败时，持仓列表、现金账户和首页总额都能回滚

## 2026-03-16-09

### 这版一句话

继续拆 Flutter `AppState`：把现金 / 其他 / 负债的增删改编排从总控里拆到独立非投资资产写操作层。

### 主要变化
- [app_asset_write_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_asset_write_state.dart) / [app_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_state.dart)：把现金、其他、负债的新增 / 删除 / 编辑编排，以及乐观更新后的首页总额回滚，从 `AppState` 拆成独立非投资资产写操作层，`AppState` 继续保留对外接口不变。
- [app_asset_write_state_test.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/test/app_asset_write_state_test.dart)：补充非投资资产写操作单测，覆盖“成功后首页总额更新”和“失败时回滚”。
- [README_页面与状态地图.md](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/README_页面与状态地图.md)：补充 Flutter 状态拆分地图，明确非投资资产写操作的新落点。

### 影响范围
- Flutter 现金 / 其他 / 负债资产编辑链路
- Flutter 资产编辑后的首页总额重算
- Flutter 非投资资产乐观更新回滚

### 验收重点
- 现金 / 其他 / 负债资产新增、删除、编辑保持原行为
- 资产写操作失败时，列表和首页总额都能回滚

## 2026-03-16-08

### 这版一句话

继续拆 Flutter `AppState`：把首页总额、资产汇总和人民币折算口径从总控里拆到独立首页总额状态层。

### 主要变化
- [app_home_totals_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_home_totals_state.dart) / [app_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_state.dart)：把首页总额、现金/投资/其他/负债小计、资产人民币折算和总额重算规则从 `AppState` 拆成独立首页总额状态层，`AppState` 继续保留对外接口不变。
- [README_页面与状态地图.md](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/README_页面与状态地图.md)：补充 Flutter 状态拆分地图，明确首页总额状态的新落点。
- [app_state_cache_test.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/test/app_state_cache_test.dart) / [app_refresh_state_test.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/test/app_refresh_state_test.dart)：继续用现有缓存恢复和首页总额回归测试兜住这次拆分。

### 影响范围
- Flutter 首页总资产和四类资产小计
- Flutter 冷启动缓存恢复后的首页总额
- Flutter 交易或资产编辑后的首页总额重算

### 验收重点
- 首页总资产、现金、投资、其他、负债继续保持原口径
- 冷启动缓存恢复后首页数字不变

## 2026-03-16-07

### 这版一句话

继续拆 Flutter `AppState`：把价格缓存、投资展示、分类筛选、金额格式化从总控里拆到独立投资展示状态层。

### 主要变化
- [app_portfolio_view_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_portfolio_view_state.dart) / [app_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_state.dart)：把价格缓存、价格回退、分类筛选、投资汇总、盈亏展示和金额格式化从 `AppState` 拆成独立投资展示状态层，`AppState` 继续保留对外接口不变。
- [app_state_smoke_test.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/test/app_state_smoke_test.dart)：补充分类筛选回归，保证页面仍然按 `AppState` 原接口调用，不需要跟着改。
- [README_页面与状态地图.md](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/README_页面与状态地图.md)：补充 Flutter 状态拆分地图，明确投资展示状态的新落点。

### 影响范围
- Flutter 投资页的价格展示、分类筛选、金额格式化
- Flutter 首页 / 投资页依赖的投资汇总读取
- Flutter 行情缓存与价格回退解析

### 验收重点
- 投资页分类切换、价格显示、盈亏显示保持原行为
- `AppState` 对外接口不变，页面和测试不需要跟着改调用方式

## 2026-03-16-06

### 这版一句话

继续拆 Flutter `AppState`：把登录、会话恢复、资料同步、本地存储容错从总控里拆到独立会话编排层。

### 主要变化
- [app_session_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_session_state.dart) / [app_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_state.dart) / [README_页面与状态地图.md](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/README_页面与状态地图.md)：把登录、会话恢复、资料同步、本地存储容错从 `AppState` 拆成独立会话编排层，`AppState` 继续保留对外接口不变。
- [app_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_state.dart)：保留对外接口和其他子状态总装配，不再自己扛登录、注册、登出、资料同步、会话恢复的细逻辑。
- [README_页面与状态地图.md](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/README_页面与状态地图.md)：补充 Flutter 状态拆分地图，明确会话编排的新落点。

### 影响范围
- Flutter 登录、会话恢复、资料同步编排
- Flutter 生物识别登录与登出清理链路
- Flutter 本地会话恢复和后台会话校验

### 验收重点
- Flutter 登录恢复、登出、生物识别登录、资料页更新保持原行为
- `AppState` 对外接口不变，页面和测试不需要跟着改调用方式

## 2026-03-16-05

### 这版一句话

统一实时投资口径：Flutter / Web 的投资页和首页汇总统一先认后端持仓指标，历史区间继续认快照。

### 主要变化
- [portfolio_handlers.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/portfolio_handlers.py)：明确 `/api/portfolio?with_metrics=1` 和 sync bootstrap 的持仓 metrics 是实时投资页唯一主口径。
- [portfolio_metrics_service.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/services/portfolio_metrics_service.dart) / [portfolio_metrics_service_test.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/test/portfolio_metrics_service_test.dart)：Flutter 持仓汇总统一先吃后端 CNY 指标，缺失时只回退到同一行指标乘汇率，并补上对应测试。
- [portfolioMetrics.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/stores/portfolioMetrics.ts) / [portfolio.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/stores/portfolio.ts) / [AppInvestPage.vue](/Users/kona/Desktop/kaka/kona_repo/web/src/pages/app/AppInvestPage.vue) / [AppHomePage.vue](/Users/kona/Desktop/kaka/kona_repo/web/src/pages/app/AppHomePage.vue) / [portfolioMetrics.test.ts](/Users/kona/Desktop/kaka/kona_repo/web/tests/unit/portfolioMetrics.test.ts)：Web 的投资页、首页、市场拆分和持仓展示统一走一个汇总工具，不再在页面里各自再算一遍。
- [资产收益计算逻辑.md](/Users/kona/Desktop/kaka/kona_repo/docs/资产收益计算逻辑.md) / [价格源与快照盈亏口径说明.md](/Users/kona/Desktop/kaka/kona_repo/docs/价格源与快照盈亏口径说明.md)：文档明确“实时认持仓指标，历史认快照”。

### 影响范围
- Flutter 首页、投资页的投资汇总
- Web 首页、投资页的投资汇总与市场拆分
- 价格 / 收益 / 快照相关口径文档

### 验收重点
- Flutter / Web 投资页的总市值、今日盈亏、累计盈亏继续对齐
- Web 首页和投资页的投资总计不再各自重算出不同结果
- 分析页历史区间继续只受 `daily_snapshots` 影响

## 2026-03-16-04

### 这版一句话

管理后台治理收口：共享 helper 和巡检逻辑下沉到 `core/admin`，`admin_routes.py` 变成薄入口，后台路由不再反向依赖超大总文件。

### 主要变化
- [admin_routes.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/admin_routes.py) / [admin_routes_dashboard.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/admin_routes_dashboard.py) / [admin_routes_users.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/admin_routes_users.py) / [admin_routes_user_write.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/admin_routes_user_write.py) / [admin_routes_config_ops.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/admin_routes_config_ops.py) / [admin_routes_data.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/admin_routes_data.py) / [admin_routes_apis.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/admin_routes_apis.py) / [admin_routes_invites.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/admin_routes_invites.py)：后台路由改成直接依赖 `core/admin` 服务，`admin_routes.py` 只保留蓝图组装和兼容导出。
- [constants.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/admin/constants.py) / [cache.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/admin/cache.py) / [common.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/admin/common.py) / [runtime_config.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/admin/runtime_config.py) / [dashboard.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/admin/dashboard.py) / [monitoring.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/admin/monitoring.py)：管理后台共享常量、读缓存、运营配置、概览统计、巡检与价格告警服务正式下沉到 `core/admin`。
- [run_price_alert_report.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/scripts/run_price_alert_report.py)：价格告警日报脚本改成直接走 `core/admin/monitoring.py`，不再为了取服务逻辑去依赖后台路由入口。
- [README_结构说明.md](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/admin/README_结构说明.md) / [README_结构说明.md](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/README_结构说明.md) / [README_STRUCTURE.md](/Users/kona/Desktop/kaka/kona_repo/kona_tool/README_STRUCTURE.md)：补齐后台服务层的目录说明，明确“路由入口”和“后台共享服务层”的边界。

### 影响范围
- 后台路由依赖关系与后台共享服务结构
- 后台巡检、provider test、价格告警、运营配置、用户统计相关代码落点
- 后台测试与价格告警日报脚本

### 验收重点
- `python3 -m compileall -q kona_tool` 通过
- `python3 -m unittest kona_tool.tests.test_admin_api_foundation kona_tool.tests.test_contracts_analysis_snapshot_admin kona_tool.tests.test_admin_invites kona_tool.tests.test_admin_api_policies kona_tool.tests.test_data_rebind kona_tool.tests.test_sync_bootstrap_api -v` 通过

## 2026-03-16-03

### 这版一句话

GitHub Actions 升级到支持 Node 24 的 action 版本，去掉 Node 20 弃用预警。

### 主要变化
- [deploy.yml](/Users/kona/Desktop/kaka/kona_repo/.github/workflows/deploy.yml)：`actions/checkout` 升级到 `v5`，`actions/setup-python` 升级到 `v6`，`actions/setup-node` 升级到 `v5`。

### 影响范围
- GitHub Actions 门禁与部署工作流

### 验收重点
- 后续 `Deploy to Production` 不再出现 `actions/checkout@v4`、`actions/setup-python@v5` 的 Node 20 弃用提醒

## 2026-03-16-02

### 这版一句话

后台路由按职责拆分，sync 协议改成后端单一源并接入生成校验，关键异步链路补上结构化结果，降低后续维护和排障成本。

### 主要变化
- [admin_routes.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/admin_routes.py) 与 [admin_routes_dashboard.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/admin_routes_dashboard.py) / [admin_routes_users.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/admin_routes_users.py) / [admin_routes_user_write.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/admin_routes_user_write.py) / [admin_routes_config_ops.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/admin_routes_config_ops.py) / [admin_routes_data.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/admin_routes_data.py) / [admin_routes_apis.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/admin_routes_apis.py) / [admin_routes_invites.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/admin_routes_invites.py)：把后台读写、配置、数据修复、巡检、邀请码链路从超大单文件里拆开，`admin_routes.py` 只保留共享 helper 和蓝图注册。
- [sync_contract.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/sync_contract.py) / [generate_sync_contracts.py](/Users/kona/Desktop/kaka/kona_repo/scripts/generate_sync_contracts.py) / [generated_sync_contract.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/stores/generated_sync_contract.ts) / [generated_sync_contract.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/generated_sync_contract.dart)：sync 协议改成后端单一源，Web 和 Flutter 常量从生成文件读取，不再三端各写一份。
- [check_sync_contract_generated.sh](/Users/kona/Desktop/kaka/kona_repo/scripts/ci/check_sync_contract_generated.sh) / [deploy.yml](/Users/kona/Desktop/kaka/kona_repo/.github/workflows/deploy.yml)：把 sync 生成校验接进 `Repo Guard`，提交时如果忘了更新生成文件会直接失败。
- [auth.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/stores/auth.ts) / [composables.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/stores/composables.ts) / [sync.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/stores/sync.ts) / [app_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_state.dart) / [asyncFlow.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/shared/asyncFlow.ts) / [async_flow_logger.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/services/async_flow_logger.dart)：登录恢复、缓存恢复、refresh 主链路补结构化结果和日志，减少静默失败。
- [router.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/router.ts) / [router_admin.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/router_admin.ts)：路由守卫改为等待 bootstrap 完成再判定登录态，避免先跳再补状态。
- [composables.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/stores/composables.ts)：修掉 sync bootstrap 传字符串伪装数组的问题，避免某些场景误回落成默认全量域。

### 影响范围
- 后台路由结构、后台巡检与数据修复接口
- Web / Flutter 的 sync 协议读取方式
- Web / Flutter 登录恢复、缓存恢复、全量刷新链路
- GitHub Actions 的仓库门禁

### 验收重点
- `python3 -m unittest kona_tool.tests.test_sync_bootstrap_api kona_tool.tests.test_admin_api_foundation kona_tool.tests.test_admin_api_policies kona_tool.tests.test_admin_invites kona_tool.tests.test_data_rebind -v` 通过
- `npm run test`、`npm run build`、`flutter test` 通过
- `bash scripts/ci/check_repo_hygiene.sh` 与 `bash scripts/ci/check_sync_contract_generated.sh` 通过

## 2026-03-16-01

### 这版一句话

Flutter 投资页持仓卡片布局调整后已上机验收，通过后合回主干。

### 主要变化
- [invest_page.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/pages/invest_page.dart)：调整投资页持仓卡片布局，让信息层次和卡片排版更贴近验收版本。
- [home_page.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/pages/home_page.dart)：同步首页问候语与基金待更新展示细节，保持首页与投资页体验一致。

### 影响范围
- Flutter 投资页持仓卡片展示
- Flutter 首页局部文案与基金待更新展示

### 验收重点
- 已通过 USB 真机安装新包验收
- 后续从 `main` 打包时，应能直接看到这版投资页 UI

## 2026-03-15-12

### 这版一句话

Web 构建入口补齐：`app/admin` 入口文件恢复进仓库，避免 CI 构建找不到入口。

### 主要变化
- [.gitignore](/Users/kona/Desktop/kaka/kona_repo/.gitignore)：不再忽略 `web/app` 与 `web/admin` 源入口目录。
- [web/app/index.html](/Users/kona/Desktop/kaka/kona_repo/web/app/index.html)：业务端构建入口文件恢复跟踪。
- [web/admin/index.html](/Users/kona/Desktop/kaka/kona_repo/web/admin/index.html)：管理端构建入口文件恢复跟踪。

### 影响范围
- Web 构建入口与 CI 构建流程

### 验收重点
- `npm run build` 不再报 `Could not resolve entry module "app/index.html"`

## 2026-03-15-11

### 这版一句话

Flutter 分析页测试口径对齐后端展示规则，并支持排行测试注入数据。

### 主要变化
- [analysis_page.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/pages/analysis_page.dart)：分析页/排行页新增 `rankLoader` 注入入口，测试不再走真实网络。
- [analysis_rank_abs_cost_test.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/test/analysis_rank_abs_cost_test.dart)：使用注入排行数据，避免依赖 HTTP。
- [analysis_realtime_snapshot_policy_test.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/test/analysis_realtime_snapshot_policy_test.dart)：顶部大卡与日历预期改为后端口径。
- [app_state_cache_test.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/test/app_state_cache_test.dart)：缓存样例补充口径字段。
- [app_state_smoke_test.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/test/app_state_smoke_test.dart)：负成本场景无口径时收益率为 0 的预期。

### 影响范围
- Flutter 分析页测试与缓存样例（不影响线上接口）

### 验收重点
- `flutter test test/analysis_rank_abs_cost_test.dart test/analysis_realtime_snapshot_policy_test.dart test/app_state_cache_test.dart test/app_state_smoke_test.dart` 通过

## 2026-03-15-10

### 这版一句话

OpenAPI 说明补齐：把后台、分析、同步、行情等关键接口的请求/响应/错误码写清楚。

### 主要变化
- [openapi.yaml](/Users/kona/Desktop/kaka/kona_repo/docs/openapi.yaml)：补齐后台接口、分析页、快照、同步、行情、门户配置等路径的 schema 与错误码定义。

### 影响范围
- 接口文档与类型生成（OpenAPI）

### 验收重点
- openapi.yaml 里不再有 TODO 占位
- 关键接口能在 schema 中看到请求体/响应体/错误码

## 2026-03-15-09

### 这版一句话

行情预取线程收口到运行时服务并改走 DatabaseManager，价格缓存加上限与统计；构建产物与运行数据边界更明确。

### 主要变化
- [price_runtime.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/price_runtime.py)：新增行情预取运行时管理器，统一启动与关闭入口。
- [price.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/price.py)：预取改走 `DatabaseManager` 取码；缓存增加上限与统计输出。
- [db_portfolio.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/db_portfolio.py)：新增“全库唯一证券代码”查询方法，给预取使用。
- [startup_runtime.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/startup_runtime.py) / [runtime_bootstrap.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/runtime_bootstrap.py) / [wsgi.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/wsgi.py)：预取启动入口收口到运行时服务。
- [.gitignore](/Users/kona/Desktop/kaka/kona_repo/.gitignore) / [cleanup_artifacts.sh](/Users/kona/Desktop/kaka/kona_repo/scripts/cleanup_artifacts.sh)：构建产物与运行输出清理规则固定化。

### 影响范围
- 行情预取线程启动方式
- 价格缓存容量与运行时指标
- 本地构建产物与运行数据边界

### 验收重点
- 预取线程仍能正常启动，且不会绕开 `DatabaseManager`
- `get_price_runtime_metrics` 包含缓存统计字段
- 清理脚本执行后不影响源码结构

## 2026-03-15-08

### 这版一句话

管理后台的新增/活跃趋势与小柱图改为后端给口径，前端只做展示。

### 主要变化
- [admin_routes.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/admin_routes.py)：`/api/admin/overview` 增加趋势文案与迷你柱图数据，后端统一计算。
- [AdminOverviewPage.vue](/Users/kona/Desktop/kaka/kona_repo/web/src/pages/admin/AdminOverviewPage.vue)：去掉前端趋势计算，直接展示后端返回的趋势文案与柱图。

### 影响范围
- 管理后台概览页的新增/活跃趋势展示

### 验收重点
- 管理后台概览页“今日新增/活跃”趋势文案与柱图与后端口径一致

## 2026-03-15-07

### 这版一句话

Web 构建产物拆成业务端与管理端两份，后端按不同静态目录分别托管。

### 主要变化
- [vite.config.ts](/Users/kona/Desktop/kaka/kona_repo/web/vite.config.ts)：构建拆成 `dist/app` 与 `dist/admin` 两套输出。
- [app.html](/Users/kona/Desktop/kaka/kona_repo/web/app.html) / [admin.html](/Users/kona/Desktop/kaka/kona_repo/web/admin.html)：拆分入口 HTML，对应不同打包入口。
- [router.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/router.ts) / [router_admin.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/router_admin.ts)：业务端与管理端路由拆分。
- [web_entry_handlers.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/web_entry_handlers.py) / [app.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/app.py)：后端按 app/admin 两套静态目录提供入口。

### 影响范围
- Web 构建产物目录结构与部署路径
- `/app/*` 与 `/admin/*` 的前端入口与静态资源路径

### 验收重点
- `npm run build` 能输出 `web/dist/app` 与 `web/dist/admin`
- `/app/login` 与 `/admin/login` 能分别落到正确的入口页面

## 2026-03-15-06

### 这版一句话

Web 分析页改成只展示后端口径数据，前端不再用本地持仓去算“当日盈亏”。

### 主要变化
- [AppAnalysisPage.vue](/Users/kona/Desktop/kaka/kona_repo/web/src/pages/app/AppAnalysisPage.vue)：概览、日历、排行全部直接使用后端接口返回值；移除前端按持仓再算实时盈亏的逻辑。

### 影响范围
- Web 分析页展示口径

### 验收重点
- 分析页顶部盈亏/收益率只跟后端接口一致，不再受前端行情影响

## 2026-03-15-05

### 这版一句话

Web 端投资与首页改成只展示后端口径字段，前端不再自行算盈亏/现价。

### 主要变化
- [sync.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/stores/sync.ts)：bootstrap 请求默认带 `portfolio_metrics=true`。
- [portfolio.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/stores/portfolio.ts)：持仓行与摘要优先使用后端口径字段，缺口径时不再自行计算盈亏。
- [AppInvestPage.vue](/Users/kona/Desktop/kaka/kona_repo/web/src/pages/app/AppInvestPage.vue)：投资页汇总/分市场/持仓列表只展示后端口径字段。
- [AppHomePage.vue](/Users/kona/Desktop/kaka/kona_repo/web/src/pages/app/AppHomePage.vue)：首页投资汇总与持仓卡片只展示后端口径字段。

### 影响范围
- Web 投资页与首页展示口径

### 验收重点
- 投资页与首页的大数字、当日盈亏、累计盈亏与后端口径一致
- 后端未返回口径字段时，页面不要自己“算一套”

## 2026-03-15-04

### 这版一句话

Flutter 投资页与分析页改成只展示后端口径字段，前端不再自己算盈亏与现价。

### 主要变化
- [invest_page.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/pages/invest_page.dart)：投资页汇总与单卡展示改成使用后端口径字段（市值/盈亏/当日盈亏），本地只做格式化与简单汇总。
- [analysis_page.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/pages/analysis_page.dart)：分析页顶部盈亏不再读前端实时口径，统一展示后端概览返回值；排行完全使用后端字段。
- [app_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_state.dart)：投资相关总额/盈亏汇总改为只吃后端口径字段，不再落回本地行情计算。

### 影响范围
- Flutter 投资页、分析页展示口径
- 首页投资总额汇总（依赖投资口径字段）

### 验收重点
- 投资页总市值/当日盈亏/累计盈亏与后端口径一致，缺口径时显示 `--`
- 分析页顶部盈亏与日历/排行均来自后端接口

## 2026-03-15-03

### 这版一句话

分析页收益日历修掉了底部溢出红字，日历格子文本会自动缩放适配。

### 主要变化
- [analysis_page.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/pages/analysis_page.dart)：收益日历格子的日期/盈亏文本改成自适应缩放，避免不同屏幕尺寸出现溢出提示。

### 影响范围
- Flutter 分析页收益日历展示

### 验收重点
- 分析页收益日历不再出现红色 overflow 提示

## 2026-03-15-02

### 这版一句话

Flutter 投资页开始优先吃后端口径字段：持仓与汇总展示不再依赖前端计算（旧后端仍可自动降级）。

### 主要变化
- [api_service.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/services/api_service.dart)：`/api/portfolio` 默认带 `with_metrics=1`，`/api/sync/bootstrap` 默认带 `portfolio_metrics=true`。
- [portfolio.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/models/portfolio.dart)：持仓模型新增后端口径字段映射与缓存输出。
- [app_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_state.dart)：投资总市值/当日盈亏/累计盈亏优先使用后端口径字段。
- [invest_page.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/pages/invest_page.dart)：卡片与分类汇总优先展示后端口径字段，缺失时再降级走旧逻辑。

### 影响范围
- Flutter 投资页展示口径（前端计算权重下降）

### 验收重点
- 投资页与首页大数字优先使用后端口径字段
- 后端不带口径字段时显示仍正常（自动降级）

## 2026-03-15-01

### 这版一句话

后端补了“投资持仓口径字段”的可选输出：需要时一次性带回现价、市值、盈亏与日盈亏，前端后续可直接展示。

### 主要变化
- [portfolio_handlers.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/portfolio_handlers.py)：`/api/portfolio?with_metrics=1` 时补齐现价、市值、累计/当日盈亏等口径字段，并附带 CNY 折算字段。
- [sync_handlers.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/sync_handlers.py)：`/api/sync/bootstrap` 增加 `portfolio_metrics=true` 可选开关，开启时返回同口径字段（默认不变）。
- [app_factory.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/app_factory.py)：注入组合口径构建器与市场状态/行情依赖，供上面两处调用。

### 影响范围
- 后端接口（新增可选字段，不改变默认返回结构）

### 验收重点
- `GET /api/portfolio` 不带参数仍只返回基础字段
- `GET /api/portfolio?with_metrics=1` 能拿到口径字段
- `POST /api/sync/bootstrap` 带 `portfolio_metrics=true` 时 `portfolio` 域包含口径字段

## 2026-03-14-16

### 这版一句话

后端把 `app.py` 入口真正变薄：组装逻辑收进 `app_factory.py`，启动后台线程单独放到 `runtime_bootstrap.py`，对外入口和单测 patch 点保持不变。

### 主要变化
- 新增 [app_factory.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/app_factory.py)：集中做 Flask app / limiter / runtime / blueprint 的组装，不在 import 阶段启动任何后台线程。
- 新增 [runtime_bootstrap.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/runtime_bootstrap.py)：承接 `python app.py` 的启动逻辑（启动 scheduler / 预取线程 / app.run），避免把运行时副作用塞回入口文件。
- [app.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/app.py) 改成薄入口：仍然导出 `app/db/limiter`，并保留 `batch_get_prices / get_forex_rates / WEB_APP_DIST_DIR / WEB_ADMIN_DIST_DIR / take_snapshot` 等单测会 patch 的全局符号。

### 影响范围
- 后端工程结构（入口拆分），接口字段与路由不变
- `gunicorn` 入口和单测 `import app as app_module` 行为不变

### 验收重点
- 后端单测 `python -m unittest discover -s kona_tool/tests -p "test_*.py" -v` 全绿
- 线上启动方式（systemd/gunicorn/wsgi）不受影响

## 2026-03-14-14

### 这版一句话

修复分析页概览在某些 Python 环境下会把未来工作日误判成“全市场休市”，导致本月/本年/全部收益被清零的问题（接口字段不变）。

### 主要变化
- [market_calendar.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/market_calendar.py) 的交易日判断范围检测更稳：兼容 `exchange_calendars` 在不同 Python / pandas 版本下返回的首尾 session 类型差异，必要时从 `sessions` 取首尾并用 `pandas.Timestamp` 兜底解析，避免“超出日历覆盖范围”时把工作日当休市。

### 影响范围
- 后端分析页概览/日历中依赖“是否休市”的 day_pnl 归零规则

### 验收重点
- GitHub Actions `Backend Gate (Python 3.10/3.11)` 是否全绿（重点看 `test_analysis_overview_month_year_all_uses_snapshot_day_pnl_sum`）。

## 2026-03-14-15

### 这版一句话

修了一个 CI “CHANGELOG 守门”脚本的坑：只改测试文件时不该误判失败。

### 主要变化
- [check_changelog_guard.sh](/Users/kona/Desktop/kaka/kona_repo/scripts/ci/check_changelog_guard.sh) 修复管道在被过滤为空时会因 `set -euo pipefail` 直接退出的问题，避免“只改测试/说明文件也被卡死”。

### 影响范围
- GitHub Actions `Repo Guard` / `CHANGELOG guard`

### 验收重点
- 推送只包含测试文件的提交时，`Repo Guard` 也应保持通过。

## 2026-03-14-13

### 这版一句话

后端把 `core/db.py` 那坨“数据库 + 业务口径 + 运维辅助”继续拆细了：对外 `DatabaseManager` 入口不变，但内部按职责拆成一组 `db_*.py` mixin，后面查持仓/快照/分析/后台状态会更好定位。

### 主要变化
- `kona_tool/core/db.py` 从超大文件拆成 `db_users / db_admin_state / db_asset_accounts / db_portfolio / db_snapshots / db_analysis / db_maintenance` 七个 mixin 文件，`DatabaseManager` 继续作为唯一对外入口。
- 补了单测兼容：日历相关测试动态加载 `db.py` 时，显式把模块注册到 `sys.modules['core.db']`，确保 `datetime` 和“休市判断”这类 patch 仍然能穿透到拆分后的分析逻辑里。
- 管理后台的行情 provider test 单测不再误触网：只测“包含基金 case”这一条规则，避免因 DNS/外网环境导致假失败。

### 影响范围
- 后端数据库层（`DatabaseManager` 内部实现）
- 分析页收益日历 / 概览取数（测试覆盖）
- 管理后台行情巡检（测试覆盖）

### 验收重点
- 后端 `python -m unittest discover -s kona_tool/tests -p "test_*.py" -v` 是否继续全绿。
- 线上不应有行为变化：接口字段与对外方法名都保持不变，只是内部拆文件。

## 2026-03-14-12

### 这版一句话

Flutter 又把 `AppState` 里最容易缠成一团的“刷新编排层”单独收了一层：冷启动缓存恢复、首页刷新、增量同步、价格后台补刷和汇率刷新现在有了专门落点，后面查首页不同步、行情没补上、缓存没写回这种问题会顺很多。

### 主要变化
- 新增 [app_refresh_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_refresh_state.dart)，先承接 `hydrateFromCache / saveHomeCache / refreshHomeData / refreshByVersion / refreshAll / refreshPortfolio / refreshPricesOnly / loadExchangeRates` 这条刷新编排链。
- [app_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_state.dart) 改成继续保留原对外方法名，但内部把刷新流程委托给 `AppRefreshState`，总状态层主要只保留依赖组装和页面兼容门面。
- 新增 Flutter 刷新状态测试，锁住“缓存恢复”和“缓存落盘 + sync version 落盘”这两条基础行为，并同步更新 Flutter 状态结构文档。

### 影响范围
- Flutter 全局状态层
- 冷启动缓存恢复
- 首页刷新 / 增量同步 / 行情后台补刷
- 缓存写回与 sync version 写回

### 验收重点
- `flutter test` 是否继续全绿。
- `flutter analyze` 是否没有新增告警噪音。
- 冷启动首页、下拉刷新、行情补刷和交易后首页回刷是否继续正常。

## 2026-03-14-11

### 这版一句话

Flutter 又把交易这层里最零碎的辅助逻辑收了一下：金额换算、undo 信息和老接口兜底不再散在 `AppState` 里，交易链路查起来会更顺。

### 主要变化
- 新增 [app_trade_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_trade_state.dart)，先承接交易金额换算、undo 信息提取和老接口买卖兜底流程。
- [app_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_state.dart) 改成把这些交易 helper 委托给 `AppTradeState`，并补了统一的写操作后首页刷新入口，减少重复分支。
- 新增 Flutter 交易辅助测试，锁住金额换算、undo 信息提取和无效现金账户兜底提示。
- 同步更新 Flutter 状态结构文档，明确现在交易链路已经拆成“资产本体 / 交易辅助 / 编排入口”三层理解。

### 影响范围
- Flutter 全局状态层
- 买入 / 卖出交易辅助逻辑
- 老接口交易兜底
- 写操作后首页刷新收口

### 验收重点
- `flutter test` 是否继续全绿。
- `flutter analyze` 是否没有新增告警噪音。
- 买入、卖出、老接口兜底和交易后首页刷新是否继续正常。

## 2026-03-14-10

### 这版一句话

Flutter 又把 `AppState` 里“历史概览 / 分析辅助”这层收出来了：月变动、年变动、历史峰值和概览覆盖现在有了独立状态，后面查首页大卡和分析概览问题会更直接。

### 主要变化
- 新增 [app_overview_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_overview_state.dart)，先承接历史统计计算、`monthChange / yearChange / historyPeak`、baseline 状态和 overview milestone 覆盖。
- [app_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_state.dart) 改成组合 `AppOverviewState`，对外继续保留 `applyOverviewMilestones` 等原入口，但内部不再自己独占概览状态本体和历史统计规则。
- 新增 Flutter 概览子状态测试，锁住 `overview` 覆盖和首次记账兜底这两条基础规则。
- 同步更新 Flutter 状态结构文档，明确现在 `AppState` 在概览层主要保留首页刷新、缓存恢复和分析接口编排。

### 影响范围
- Flutter 全局状态层
- 首页大卡历史概览
- 分析页概览覆盖
- 历史峰值与 baseline 计算

### 验收重点
- `flutter test` 是否继续全绿。
- `flutter analyze` 是否没有新增告警噪音。
- 首页月变动、年变动、历史峰值和分析概览覆盖是否继续正常。

## 2026-03-14-09

### 这版一句话

Flutter 又把 `AppState` 里最重的一坨往外收了一层：资产列表、持仓列表、快照恢复和乐观更新先拆成了独立资产状态，后面查交易和总额联动问题会顺手很多。

### 主要变化
- 新增 [app_assets_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_assets_state.dart)，先承接现金/其他/负债列表、持仓列表、资产快照/持仓快照恢复、乐观增删改和资产币种规范化。
- [app_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_state.dart) 改成组合 `AppAssetsState`，对外继续保留原有 `addAsset / buyInvestment / sellInvestment / modifyInvestment` 这些入口，但内部不再自己独占资产列表本体和乐观更新细节。
- 新增 Flutter 资产子状态测试，锁住非投资资产乐观更新和持仓买卖/调整/快照恢复这两条基础行为。
- 同步更新 Flutter 状态结构文档，明确现在 `AppState` 在资产层主要保留接口调用、金额换算、总额重算和刷新编排。

### 影响范围
- Flutter 全局状态层
- 非投资资产操作
- 投资持仓乐观更新与快照恢复
- 总资产联动重算

### 验收重点
- `flutter test` 是否继续全绿。
- `flutter analyze` 是否没有新增告警噪音。
- 买入、卖出、修改、删除、现金联动和总额重算是否继续正常。

## 2026-03-14-08

### 这版一句话

Flutter 又把 `AppState` 里“假拆分”的那层缓存中转清掉了：`AppSyncState` 不只是挂名模块，现在已经真接住缓存规则和同步判断，后面查缓存 / 同步问题会更直接。

### 主要变化
- [app_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_state.dart) 删除了一批只是转手调用 `_syncState` 的 helper，像用户资料缓存、domain envelope、sync version、报价策略和静态同步跳过判断都不再继续留在总状态里当中转层。
- [app_sync_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_sync_state.dart) 补上报价刷新策略解析和静态同步跳过判断，缓存 / 同步这层的纯规则能力进一步收口。
- 新增同步状态测试，锁住 `quote policy` 和 `canSkipStaticSyncCheck` 这两条规则，避免后面又把判断散回 `AppState`。
- 同步更新 Flutter 状态结构文档，明确现在缓存 / 同步这一层的职责已经从“挂名拆出”变成了“真实收口”。

### 影响范围
- Flutter 全局状态层
- 启动缓存恢复与增量同步
- 行情刷新策略与缓存元信息判断

### 验收重点
- `flutter test` 是否继续全绿。
- `flutter analyze` 是否没有新增告警噪音。
- 冷启动缓存恢复、增量同步、行情轮询节奏是否继续正常。

## 2026-03-14-07

### 这版一句话

Flutter 又把 `AppState` 里最黏的一层往外抠了一块：缓存规则、sync 版本和缓存元信息先收成了独立状态模块，后面查缓存和启动恢复问题会顺手很多。

### 主要变化
- 新增 [app_sync_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_sync_state.dart)，先承接用户缓存作用域、cache envelope 读写、sync 版本缓存、缓存命中标记和行情刷新间隔策略状态。
- [app_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_state.dart) 改成把缓存辅助方法和同步元信息更多地委托给 `AppSyncState`，但 `hydrateFromCache / refreshByVersion / refreshAll` 这些对外入口和编排逻辑继续保留原位置。
- 新增 Flutter 同步状态测试，锁住缓存 key 规则、用户资料缓存恢复和 domain envelope 写入行为。
- 同步更新 Flutter 状态结构文档，明确现在已经拆出的 5 块子状态边界。

### 影响范围
- Flutter 全局状态层
- 启动缓存恢复
- sync 版本缓存与缓存作用域规则
- 用户资料缓存读写

### 验收重点
- 冷启动缓存恢复、登录态恢复、登出后缓存清理是否继续正常。
- `flutter test` 是否继续全绿。
- `flutter analyze` 是否没有新增告警噪音。

## 2026-03-14-06

### 这版一句话

Flutter 又把 `AppState` 里一大块纯规则状态收出来了：汇率、市场开闭市和交易日判断不再继续混在总状态文件里。

### 主要变化
- 新增 [app_market_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_market_state.dart)，先承接汇率换算、市场状态解析、交易日判断和市场状态缓存序列化。
- [app_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_state.dart) 改成组合 `AppMarketState`，首页、投资页、分析页继续沿用原有 `getCurrencyRate / convertToCny / isMarketOpen` 这些入口。
- 行情价格刷新和价格快照编排还暂时留在 `AppState`，先只拆纯状态和规则判断，避免一口气把报价链路拆散。
- 新增市场子状态测试，并同步补充 Flutter 状态结构文档。

### 影响范围
- Flutter 全局状态层
- 汇率换算、市场开闭市、交易日判断
- 行情缓存恢复与市场状态缓存写回

### 验收重点
- 首页市场开市状态、投资页当日盈亏启用条件、汇率折算是否继续正常。
- `flutter test` 全量和市场相关测试是否继续通过。
- `flutter analyze` 是否没有新增告警噪音。

## 2026-03-14-05

### 这版一句话

Flutter 又给 `AppState` 动了第二刀：认证和会话恢复相关的内存状态也先拆出去了，登录链路继续保留原入口，但内部边界比之前清楚一层。

### 主要变化
- 新增 [app_auth_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_auth_state.dart)，先承接登录态、token、用户资料、启动恢复状态和认证错误文案。
- [app_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_state.dart) 改成同时组合 `AppAuthState / AppPreferencesState / AppSecurityState`，页面层和现有测试继续沿用原 getter、原方法名。
- 启动恢复、静默 refresh、登出、生物识别登录这些流程还先留在 `AppState` 编排，但底层认证状态更新已经统一收口到 `AppAuthState`。
- 新增 Flutter 认证子状态测试，并补更新结构文档，避免后面继续把认证细节散回总状态文件。

### 影响范围
- Flutter 全局状态层
- 登录、登出、启动恢复、生物识别登录链路
- Flutter 认证相关测试与结构文档

### 验收重点
- 用户名密码登录、邀请码注册、启动恢复、登出是否继续正常。
- 生物识别保留 refresh token 的退出逻辑是否继续正常。
- `flutter test` 和 `flutter analyze` 是否没有新增阻塞错误。

## 2026-03-14-04

### 这版一句话

Flutter 先对 `AppState` 下了第一刀：UI 偏好和生物识别 / 锁屏不再继续死塞在一个 3000 多行总控类里，先拆成了两个独立状态模块。

### 主要变化
- 新增 [app_preferences_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_preferences_state.dart)，先承接主题、金额隐藏和显示币种。
- 新增 [app_security_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_security_state.dart)，先承接生物识别开关、锁屏状态和生物识别登录流程。
- [app_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_state.dart) 改成组合这两个子状态，对页面继续保留原 getter 和方法名，避免一口气改爆页面层。
- 补了 Flutter 状态层测试，锁住 UI 偏好和生物识别模块的基础行为。

### 影响范围
- Flutter 全局状态层
- 登录态 / 生物识别 / 锁屏链路
- Flutter 主题与金额显示偏好

### 验收重点
- 主题切换、金额隐藏、显示币种切换是否继续正常。
- 生物识别开关、锁屏解锁和生物识别登录是否继续正常。
- Flutter 相关测试和分析是否继续通过。

## 2026-03-14-03

### 这版一句话

把 Web 的遗留壳和测试目录边界正式钉死了：`Legacy` 层不再继续长新职责，正式测试和调试脚本也彻底分家。

### 主要变化
- Web 文档和代码里明确补上 `LegacyAppShell / LegacyAdminShell / legacy.css` 的冻结规则，这层现在只保稳定，不再承接新布局、新状态和新样式职责。
- `web/tests` 重新分成 `unit / e2e / debug` 三层，正式单元测试、正式页面验收和临时排障脚本不再混在一个目录里。
- 新增 `web/tests/README.md` 和 `web/vitest.config.ts`，把 Web 测试入口、目录分工和执行方式写清楚。
- Web 脚本入口收口成 `npm run test / test:e2e / test:e2e:debug`，并让前端 CI 门禁先跑 `npm run test` 再构建。

### 影响范围
- Web 遗留布局层
- Web 测试目录结构
- Web 本地测试命令与前端 CI 门禁

### 验收重点
- 后续新增页面和状态逻辑时，是否还能明确避开 `Legacy` 层。
- `npm run test` 是否只跑正式单元测试，不再把 Playwright 调试脚本一起卷进去。
- `npm run build` 和前端 GitHub Actions 是否继续正常。

## 2026-03-14-02

### 这版一句话

先把仓库卫生和 CI 守门补硬了一层：构建产物、本地数据库和缓存不该再混进 Git，重要工程改动如果没写版本记录也会被自动拦下来。

### 主要变化
- 仓库根 `.gitignore` 补上了 Web / Flutter 构建产物、测试结果、缓存目录和生成报告的忽略规则，减少生成物回流主仓库。
- 新增 `scripts/ci/check_repo_hygiene.sh`，专门检查构建产物、缓存目录和本地数据库有没有被 Git 跟踪。
- 新增 `scripts/ci/check_changelog_guard.sh`，重要工程或业务改动如果没同步更新 `CHANGELOG.md`，GitHub Actions 会直接拦下。
- 部署工作流新增 `Repo Guard` 前置门禁，先过仓库卫生和版本记录检查，再继续跑后端和前端构建测试。

### 影响范围
- 仓库提交流程
- GitHub Actions 门禁
- 本地构建产物与缓存管理

### 验收重点
- `git status` 不再被构建产物、缓存目录和本地数据库反复污染。
- 提交重要工程改动但没补 `CHANGELOG.md` 时，CI 是否会明确报错拦下。
- 现有后端 / Flutter / Web 的基础构建与测试流程是否不受影响。

## 2026-03-14-01

### 这版一句话

把后端主入口这一坨“大杂烩”先收成了可长期维护的一版：`app.py` 不再继续堆业务细节，路由、处理器、运行时钩子和对应测试都拆开了，后面查问题和继续扩展会轻松很多。

### 主要变化
- 后端把原来堆在 `kona_tool/app.py` 里的大块职责继续拆开，主入口现在主要只负责应用创建、运行时装配、蓝图注册和启动。
- 新增并接入一批按职责拆分的模块，包括业务路由/处理器层，以及 `request_runtime / snapshot_runtime / portfolio_runtime / market_runtime / startup_runtime` 这几块运行时能力。
- 把原来混在一个大测试文件里的后端接口回归拆成多份专题测试，并补上运行时层测试，覆盖登录、首页联动、行情、持仓、分析、启动与快照这些核心链路。
- 同步更新后端结构说明和测试地图，后面继续接手的人不用再靠猜去找入口。

### 影响范围
- 后端 Flask 应用装配入口
- 后端 API 路由分发与运行时钩子
- 后端本地回归测试与结构文档

### 验收重点
- 登录、首页、投资页、分析页、管理后台这些主链路继续正常，不因为结构整理出现白屏、500 或跳转异常。
- 本地验收里提过的二维码兜底、邀请码图片兜底、余额不足中文文案等高频交互继续保持正常。
- 后端自动化回归继续全绿，后面新增接口或修 bug 时不再只能往 `app.py` 里硬塞。

## 2026-03-13-02

### 这版一句话

把“多币种非投资资产折算”和“分析页收益率分母”两处口径 bug 一次性收口：港币/美元现金不再按人民币裸加，日历收益率也不再出现离谱值或和顶部对不上。

### 主要变化
- 后端快照计算改成统一按币种折算到 CNY 后再汇总 `现金/其他资产/负债`，不再直接把原币金额裸加进总资产。
- Flutter `AppState` 的首页总额和资产总额计算同步改成同一折算逻辑，修复“建账填 100 HKD，切港币显示成 113”这类错位。
- 后端 `analysis/calendar` 的 `total_rate` 分母改成按周期基准本金计算（本月用月初前基准、本年用年初前基准、全部用首条基准），不再固定取首条快照本金。
- 补了后端和 Flutter 回归测试，锁住“非投资资产多币种折算”和“calendar 收益率分母”这两条规则。

### 影响范围
- 后端快照计算与分析日历收益率
- Flutter 首页/投资页总资产汇总
- Web/Flutter 分析页日历收益率显示

### 验收重点
- 新增现金/其他资产时，非 CNY 币种在首页总资产里的换算是否正确。
- 分析页同一周期下，顶部大卡与日历汇总的收益率是否不再大幅偏离。
- `all/year` 这类历史周期是否不再出现明显异常的百分比。

## 2026-03-13-01

### 这版一句话

把分析页收益口径正式收口了：当日继续走实时行情，本月/本年/全部不再拿累计总盈亏差值硬算，改成按快照里的日收益累计；Flutter 底部汇总条也直接跟接口返回值对齐，不再和顶部大卡打架。

### 主要变化
- 后端 `/api/analysis/overview` 的 `本月 / 本年 / 全部` 改成按 `daily_snapshots.day_pnl` 周期累计，不再用 `total_pnl` 首尾差值充当分析页收益。
- 后端 `/api/analysis/calendar` 的 `day / month / year` 汇总也统一按同一条日收益快照链累计，和分析页顶部大卡、日历底部汇总改成同一套口径。
- Flutter 分析页继续保留“当日实时、其余周期快照、当前月今天那格允许实时覆盖”的规则，但底部汇总条现在优先直接用接口 `total_pnl`，不再自己把格子重新加一遍。
- 补了后端和 Flutter 测试，锁定“当日实时、本月/本年/全部按日收益累计、今天格可实时覆盖、切换日历视图不影响顶部周期”这几条规则，防止后面再混口径。

### 影响范围
- 后端 `/api/analysis/overview`
- Flutter 收益日历
- Flutter 分析页顶部收益大卡
- Flutter 分析页底部汇总条

### 验收重点
- 分析页切到 `当日` 时，顶部大卡是否继续跟随实时行情。
- 切到 `本月 / 本年 / 全部` 时，顶部大卡和底部汇总条是否都改成按日收益累计，不再出现一个正一个负。
- 当前月日历今天那格是否仍允许实时覆盖；切到历史月份或历史年份后，是否恢复快照值。
- `kona`、`luotianxu` 这类之前会出现顶部大卡金额明显不对的账号，修复后是否和日历累计方向一致。

## 2026-03-12-01

### 这版一句话

把 Web 登录恢复和 `BRK.B` 这类特殊美股代码一起补稳了：登录态不再因为启动时偶发超时就自己清空，带点号/横杠的美股也能按美股口径识别并继续往下拿报价。

### 主要变化
- Web 登录恢复改成更保守的清理策略：启动时如果只是 `/api/auth/me` 校验超时或临时网络失败，不再立刻把本地登录态整包清掉；只有遇到明确的 `401/403` 无效状态，才会真正清空 token。
- 这次同时补了新状态层和遗留共享 store，两条登录恢复链路保持一致，避免用户端和管理后台表现不一样。
- 后端 `parse_code` 现在支持 `BRK.B`、`BRK-B` 这种带点号/横杠的美股代码，返回会规范成 `gb_` 前缀并给出 `USD` 币种，不再误落成 `CNY`。
- 美股报价链路补了特殊符号兜底：像 `BRK.B` 这类先试原始点号代码，再试横杠变体；如果常规纳斯达克慢源超时，还会再给一次更宽松的纳斯达克兜底。

### 影响范围
- Web 用户端登录恢复
- Web 管理后台登录恢复
- 后端美股代码解析
- `BRK.B` / `BRK-B` 这类特殊美股的报价获取

### 验收重点
- Web 用户端和管理后台在刷新页面、隔一段时间后再打开时，是否还能继续保持登录，不再因为偶发超时自己退回登录页。
- 手动录入或搜索 `BRK.B` 后，代码和币种是否按美股处理，不再落成 `CNY`。
- `BRK.B` 是否能正常拿到价格，不再长期显示 `0` 或无报价。

## 2026-03-10-01

### 这版一句话

把投资页和编辑持仓弹窗里几处一直反复别扭的显示问题一起收顺了：收益卡金额改成整数，首页指数卡不再把汇率卡挤没，移动端编辑持仓摘要卡也改成了更稳的方案 B。

### 主要变化
- Web 投资页中间那 4 张市场收益卡，`今日盈亏 / 累计盈亏` 改成正负整数显示，不再夹着零碎小数。
- Web 首页顶部指数卡改成桌面端自动网格、小屏端横向滑动，`USD/CNY` 汇率卡不再因为最后一张被挤出屏幕。
- Web 编辑持仓弹窗顶部摘要区补了更硬的宽度约束，长名称会老老实实省略，不再把右侧信息块顶穿。
- Flutter 编辑持仓弹窗顶部摘要卡改成原型里的方案 B：左侧股票名，右侧大号成本价，底栏显示股数和调整额胶囊，并按真机验收继续微调了字号、边框和位置。

### 影响范围
- Web 首页指数卡
- Web 投资页市场收益卡
- Web 编辑持仓弹窗摘要区
- Flutter 编辑持仓弹窗摘要卡

### 验收重点
- 首页顶部是否能同时看到 `上证 / 深成 / 创业板 / 恒生科技 / 纳斯达克 / USD/CNY` 这 6 张卡。
- 投资页中间那 4 张市场收益卡里的金额是否都已经是整数，百分比继续正常。
- Web 编辑持仓弹窗里，长名称资产是否会自动显示成省略号，不再把 `持仓成本 / 调整额` 顶到外面。
- 安卓真机上编辑持仓弹窗顶部摘要卡是否已经改成方案 B，右上角成本价和右下角调整额胶囊显示是否顺眼。

## 2026-03-09-10

### 这版一句话

把管理后台剩下几页的手机端也一起收顺了，邀请码、接口、配置不再只是“能开”，而是更接近真能在手机上操作。

### 主要变化
- `邀请码管理` 手机端改成卡片列表，邀请码、状态、使用人和时间都能直接看，不再把桌面表格硬压到小屏里。
- `接口管理` 手机端把入口卡继续保留成一列，弹窗改得更像底部抽屉；底部按钮改成整行按钮，表格区允许横向滚动，不再在小屏里直接挤爆。
- `运营配置` 手机端卡片补上文案预览，标题、描述、标签和间距重新收过，页面不再只有几个空标签撑场面。

### 影响范围
- Web 管理后台 `邀请码管理`
- Web 管理后台 `接口管理`
- Web 管理后台 `运营配置`

### 验收重点
- 手机宽度下进入 `邀请码管理`，是否已经改成卡片列表，复制邀请码和切换已使用/未使用是否还正常。
- 手机宽度下打开 `接口管理` 的测试弹窗，按钮、标签页和表格是否还能正常看和点。
- 手机宽度下进入 `运营配置`，每张配置卡是否已经能直接看出当前文案和配置状态。

## 2026-03-09-09

### 这版一句话

把 Web 管理后台改成了手机上也能顺手用的一版：后台标题独立了，侧边栏在手机上改到底部菜单，`用户管理` 先做成了卡片版。

### 主要变化
- 管理后台路由现在会单独把网页标题设置成 `咔咔记账 - 管理后台`，不再继续沿用业务端的 `咔咔记账 - 投资记录工具`。
- 后台几个主页面统一接入新的共用导航组件，桌面端继续保留左侧菜单，手机端改成底部菜单，概览、用户、邀请码、配置、接口都能直接点。
- `用户管理` 页面在手机端不再硬塞表格，而是改成一张张用户卡，直接展示昵称、用户名、状态、资产、注册时间和最近活跃，底部保留详情和封禁按钮。
- 手机端后台页面统一补了底部安全区留白，避免内容被底部菜单压住。

### 影响范围
- Web 管理后台标题显示
- Web 管理后台导航结构
- Web 管理后台 `用户管理` 页手机端布局

### 验收重点
- 打开 `/admin/login` 并进入后台后，浏览器页签标题是否显示 `咔咔记账 - 管理后台`。
- 手机宽度下，后台底部是否出现 `概览 / 用户 / 邀请码 / 配置 / 接口` 菜单，并且切页正常。
- 手机宽度下进入 `用户管理`，是否已经改成卡片列表，不再是被压缩到难看的表格。

## v1.0.x

### 这版一句话
把移动端编辑资产弹窗的摘要卡收顺了，修掉了股数被误显示成 `1股` 的问题。

### 主要变化
- Flutter 编辑资产弹窗顶部摘要卡改成更稳的三列摘要布局，名称、持仓成本、调整额在小屏下不再互相挤坏。
- 币种显示统一成符号口径：人民币用 `￥`，美元用 `$`，港币用 `HK$`。
- 修正弹窗里的数字格式化函数，整数不再误删尾部 `0`，`1000股` 不会再被显示成 `1股`。

### 影响范围
- Flutter 投资页编辑资产弹窗
- Flutter 买入 / 卖出 / 调整顶部摘要卡显示

### 验收重点
- 安卓手机上编辑资产弹窗顶部是否能正确显示 `1000股` 这类整数持仓
- `持仓成本` 和 `调整额` 在小屏下是否还能完整可读

## v1.0.x (移动端 Web 适配)

### 这版一句话
对 Web 端的全局框架、首页、登录页、交易弹窗进行了深度移动端样式适配，在手机浏览器上对齐 Flutter App 体验。

### 主要变化
- **全局布局**：手机端隐藏左侧大导航，新增 Flutter 风格的底部 5 Tab 导航栏，优化顶部标题栏居中。
- **首页资产卡**：优化了手机端的网格布局，隐藏了挤占空间的顶部指数卡片，持仓列表支持横向滑动。
- **交易弹窗**：去除了窄屏下的单列强制折行限制，输入框和数据项在手机端也能保持紧凑的三列布局。
- **登录页面**：去除了悬浮卡片感，转为手机端原生的全屏沉浸表单，并加大了按钮与输入框尺寸。

### 影响范围
- 主要影响 `web/src/pages/app` 和 `layouts` 下的核心页面在屏幕宽度 < 768px 时的样式。
- 桌面端宽屏访问逻辑和样式均不受影响。

### 验收重点
- 在手机浏览器打开 Web 首页与登录页是否布局正常且无水平滚动条。
- 底部 Tab 导航是否能正常跳转各业务页。
- 点击持仓卡片弹出的交易窗口内，各个输入框是否未出现严重的纵向堆叠变形。
# 版本记录

这份文件专门用来记录每一版到底改了什么。

我把规则改成了大白话：

1. 先说这版主要解决什么问题。
2. 再说你能直接感受到什么变化。
3. 最后只保留少量必要的技术说明。

以后看版本，你只需要重点看这 4 项：

- `这版一句话`
- `主要变化`
- `影响范围`
- `验收重点`

版本规则也写死：

- 这份文件记录的是项目变更，不是客户端真实版本号
- Flutter 客户端版本以 `flutter/pubspec.yaml` 为准
- App 内“检查更新”版本以 `/api/app/version` 返回值为准
- 历史上的 `v1.0.x` 条目已经改成内部记录标题，原版本号保留在括号里
- 从现在开始，推荐新条目改成 `2026-03-08-01` 这种日期型内部记录

## 2026-03-09-02

### 这版一句话

把交易弹窗里的资产账户下拉补成可滚动，账户再多也不会把弹窗撑坏。

### 主要变化
- 给 Web 交易弹窗里的 `资产账户` 下拉增加最大高度和纵向滚动，账户数量多时可以直接在弹窗里下拉查看。
- 补上触控滚动和滚动条样式，桌面端和移动端都不再出现“列表展开了但没法往下翻”的情况。
- 这次修复同时覆盖 `添加资产` 和 `编辑资产`，因为两者共用同一套账户下拉组件。

### 影响范围
- Web 添加资产弹窗
- Web 编辑资产弹窗
- Web 资产账户选择下拉

### 验收重点
- 资产账户很多时，展开下拉后是否可以继续向下滚动看到后面的账户。
- 添加资产和编辑资产两种弹窗里，下拉滚动是否都正常。
- 下拉列表滚动时，整个弹窗是否不再被一路撑出可视区域。

## 2026-03-09-03

### 这版一句话

把投资页的静默刷新补成持续可用，同时修正了场内基金和部分美股拿不到趋势图的问题。

### 主要变化
- Web 投资页现在会持续自动刷新报价，切到别的标签页再切回来时也会立刻补刷，不再只在刚进页面时刷一轮就停。
- 投资页顶部的 `今日盈亏`、`持仓收益`、`累计盈亏` 三个金额改成整数显示，页面口径更稳，视觉上也不再一会儿带小数一会儿不带。
- 后端趋势链路补了两类兼容：一类是场内基金纯 6 位代码也能正确取到趋势，另一类是美股历史点太稀时会回退到 Yahoo 历史，像 `BOXX` 这类 ETF 不再只拿到 1 个点。

### 影响范围
- Web 投资页的自动刷新和顶部盈亏展示
- 首页、投资页共用的资产趋势接口
- 场内基金和部分美股 ETF 的趋势图显示

### 验收重点
- 投资页在前台停留时，报价是否会持续静默更新；切回标签页后是否会马上补刷。
- 投资页顶部的 `今日盈亏`、`持仓收益`、`累计盈亏` 是否都改成整数显示。
- 场内基金和 `BOXX` 这类美股 ETF 是否能正常出现趋势图，不再长期显示 `暂无趋势`。

## 2026-03-09-04

### 这版一句话

把登录和后台配置这两条常用链路补稳了，少点重复提交和“明明保存成功却关不掉”的别扭感。

### 主要变化
- Flutter 登录页给登录按钮补了防连点，按钮进入加载态后不会再被连续点出多次登录请求。
- 后端登录接口在请求体缺失时会多记一层诊断信息，后面排查 `body` 为空、`content-type` 不对这类线上问题会更快。
- Web 管理后台的配置弹窗和更新弹窗在保存成功后允许主动关闭，不再卡在“保存刚结束但 close 被 saving 状态拦住”的尴尬状态。
- Web 用户类型补上 `build_start_at` 字段，前端再读这个用户资料字段时不需要继续绕类型报错。

### 影响范围
- Flutter 登录页
- 后端登录接口异常诊断日志
- Web 管理后台配置页和更新配置弹窗

### 验收重点
- Flutter 登录时连续快速点按钮，是否只会发起一轮登录流程。
- 管理后台保存配置成功后，弹窗是否会正常关闭并保留成功提示。
- 后端登录接口如果收到空请求体，日志里是否能看到请求体诊断信息。

## 2026-03-09-05

### 这版一句话

把趋势模块里卡 Python 3.9 的兼容问题修掉了，主干测试不再因为导入失败整串红掉。

### 主要变化
- 把 `kona_tool/core/trend.py` 里 Python 3.11 才有的 `datetime.UTC` 改回 Python 3.9 也兼容的 `timezone.utc`。
- 修正 Yahoo 历史趋势时间戳转日期的 UTC 写法，避免 GitHub Actions 在导入趋势模块时直接抛 `ImportError`。
- 这次修的是运行环境兼容，不改趋势口径本身；场内基金和美股趋势兜底逻辑保持不变。

### 影响范围
- 后端趋势模块导入
- GitHub Actions 的 Python 3.9 测试环境
- 所有依赖 `core.trend` 的后端测试

### 验收重点
- GitHub Actions 里 `python -m unittest discover -s kona_tool/tests -p "test_*.py" -v` 是否恢复通过。
- 趋势模块导入时是否不再报 `cannot import name 'UTC' from 'datetime'`。
- 场内基金和美股趋势相关测试是否继续通过。

## 2026-03-09-06

### 这版一句话

把后端门禁和线上运维脚本的 Python 口径统一到了当前真实环境，尽量别再让系统自带的老 Python 悄悄掺进来。

### 主要变化
- GitHub Actions 的后端门禁从 `Python 3.9/3.11` 调整成 `Python 3.10/3.11`，和项目当前 `3.10+` 口径对齐。
- 线上相关的 systemd 安装脚本、故障告警脚本、快照/备份脚本改成优先使用当前目录下的 `.venv/bin/python`，不再写死 `/usr/bin/python3`。
- 备份、恢复、快照检查这类脚本的默认数据库和备份路径改成按脚本所在目录自动推导，不再绑死旧机器的 `/home/ec2-user/...` 路径。
- 部署、运维、认证和后台手册里最常用的线上命令同步改成当前腾讯云真实路径 `/opt/kaka/portfolio/kona_tool`。

### 影响范围
- GitHub Actions 后端门禁
- 线上 systemd / 告警 / 备份 / 快照相关脚本
- 部署与运维主文档

### 验收重点
- GitHub Actions 里 `Backend Gate` 是否只跑 `3.10` 和 `3.11`。
- 线上如果重新安装告警或备份服务，生成的 systemd 配置是否指向 `.venv/bin/python`。
- 线上手工执行备份、恢复、refresh token 清理等命令时，是否都按 `/opt/kaka/portfolio/kona_tool` 和 `.venv/bin/python` 这套口径走。

## 2026-03-09-07

### 这版一句话

把价格健康告警脚本的 systemd 语义改顺了，命中告警时继续发通知，但不再把定时任务本身打成失败。

### 主要变化
- `check_price_health_alert.py` 现在把“脚本执行失败”和“脚本成功探测到异常并已告警”分开处理。
- 当价格健康接口真的探测到异常时，脚本仍会输出告警内容并尝试发邮件，但返回值改成 `0`，避免 systemd 长期显示红色失败态。
- 只有价格健康接口本身拉取失败、返回非法内容这类真正执行错误，脚本才继续返回 `1`。

### 影响范围
- 腾讯云上的 `kona-price-health-alert.service`
- 价格健康巡检 timer 的 systemd 状态
- 价格健康脚本测试

### 验收重点
- 命中价格健康告警规则时，邮件/日志是否仍然会产出。
- `kona-price-health-alert.service` 在命中告警后是否不再显示 `failed`。
- `test_price_health_alert_script.py` 是否继续通过。

## 2026-03-09-08

### 这版一句话

把 Web 和 App 里的持仓调整弹窗改成“下拉选调整类型 + 单输入反算”，手机端不再需要同时填数量、成本和调整额。

### 主要变化
- Web 和 Flutter 的 `调整` 模式都改成先选调整类型，再只输入一个主值，支持 `累计收益 / 成本价 / 数量 / 分红 / 手续费` 五种调整方式。
- 选择不同调整类型后，弹窗会自动把要提交的 `qty / price / adjustment` 反算出来，继续复用原来的 `modify` 接口，不额外新开第二套后端入口。
- `分红` 会自动按 `adjustment + 金额` 处理，`手续费` 会自动按 `adjustment - 金额` 处理；`成本价` 和 `数量` 也都改成只填目标值即可。
- 调整区域补了“调整后数量 / 调整后成本价 / 调整后累计收益”预览，用户不用自己脑补系统到底会怎么改。
- 买入 / 卖出 / 调整 三个模式的顶部资产卡都改成“名称 + 持仓 + 持仓成本 + 调整额”的记录摘要，不再继续显示行情涨跌；Web 和 Flutter 统一成紧凑的双指标卡风格，并补上币种显示与长数字自适应。

### 影响范围
- Web 首页、投资页共用的交易弹窗
- Flutter 投资页交易弹窗
- 持仓调整的前端交互和提交口径

### 验收重点
- Web 和 App 进入 `调整` 后，是否都改成下拉选择调整类型，而不是同时填写多项字段。
- 选择 `累计收益 / 成本价 / 数量 / 分红 / 手续费` 时，输入区标签和预览结果是否会跟着切换。
- 保存调整后，数量、成本价、累计收益是否按预期变化；`qty=0` 这类无效场景是否会直接拦截并给出明确报错。

## 2026-03-09-01

### 这版一句话

把 Web 首页和投资页里股票编辑弹窗的资产账户补回来了，买入和卖出不再整块消失。

### 主要变化
- 修正交易弹窗的显示条件，编辑已有股票时，`买入 / 卖出` 会继续显示 `资产账户`，只有 `调整` 模式才隐藏这块。
- 交易弹窗的账户列表改成读取真实资金账户，不再继续写死几条假账户数据，同时保留“外部资金/初始转入”兜底入口。
- 给账户选择区补上 `资产账户` 标题和未选中提示，避免界面看起来像少了一整块表单。

### 影响范围
- Web 首页里的股票编辑弹窗
- Web 投资页里的股票编辑弹窗
- Web 买入 / 卖出转资金账户链路

### 验收重点
- 首页和投资页点开股票编辑后，`买入 / 卖出` 是否都能看到 `资产账户`。
- 选择真实资金账户后，买入和卖出是否还能正常提交。
- 切到 `调整` 标签时，账户区是否仍然按预期隐藏。

## 2026-03-08-01

### 这版一句话

把管理后台用户概览页的活跃和留存口径纠正了：活跃改成更接近产品 DAU，留存改成真正的第 N 日留存，顶部小图也不再是假图。

### 主要变化
- 后端新增用户日活表，按 `user_id + 日期` 记录用户当天是否活跃，不再继续拿 `last_login` 和 `last_active_at` 这种“最后一次时间”硬凑日活和留存。
- 管理后台概览页里的 `DAU / WAU / MAU`、表格里的 `活跃用户`，全部改成按日活表统计，更接近真实产品活跃口径。
- `次留 / 3留 / 7留 / 14留 / 30留` 改成真正的“注册后第 N 天当天是否活跃”，不再是“满 N 天后回来过一次就算留存”。
- 在用户增长表里新增 `活跃次留 / 活跃3留 / 活跃7留 / 活跃14留` 四列，专门看“当天活跃 cohort”后续还能回来多少。
- 数据概览页上方两张卡的小柱状图和底部提示改成近 7 天真实新增与真实活跃走势，不再继续显示写死的装饰图和假文案。

### 影响范围
- 管理后台数据概览页
- 后端用户运营统计口径
- 后端用户日活数据结构

### 验收重点
- 后台概览页里的 `今日活跃用户` 是否和产品真实使用更接近，不再只是“当天登录人数”。
- `次留 / 3留 / 7留 / 14留` 是否变成真正第 N 日留存，而不是旧的阈值后回访率。
- `活跃次留 / 活跃3留 / 活跃7留 / 活跃14留` 是否已经出现，并且和“新增留存”分成两组看。
- 概览页上方两张卡的小柱状图和“较昨日”文案，是否已经跟下方表格同口径。


## 历史记录 053（原 v1.0.53）

### 这版一句话

把登录注册这条认证链路里的英文报错统一改成中文，同时修了 Web 端老头像在浏览器里继续显示破图的问题。

### 主要变化
- 登录、注册、邀请码校验、资料更新、密码修改、刷新登录态这些认证接口，用户能直接看到的错误提示统一改成了中文，不再中英混着跳。
- 修正了 Web 端头像兼容判断顺序，Flutter 老链路留下的纯 Base64 头像现在会先被识别成图片数据，不会再被误判成站内路径。
- 后端相关测试断言同步改成中文口径，避免 CI 继续拿旧英文报错做比较。

### 影响范围
- Web 登录页和注册页
- Web 个人中心与后台头像显示
- 后端认证接口返回文案

### 验收重点
- 登录输错密码时，是否显示“账号或密码错误”，不再冒英文。
- 邀请码、用户名、密码规则这些注册报错，是否都变成中文。
- 线上用户名 `kona` 在 Web 端是否不再显示破图头像。

## 历史记录 052（原 v1.0.52）

### 这版一句话

修了 Web 端老头像显示成破图的问题，Flutter 里已经传过的头像现在在 Web 和后台也能正常显示了。

### 主要变化
- Web 新增统一头像转换逻辑，能同时兼容正常图片地址、完整 `data:image/...` 头像和 Flutter 老链路留下的纯 Base64 头像。
- 前台个人中心、旧版设置页、主壳层侧边栏，以及后台几个主页面的头像显示都接到了同一套转换逻辑，不再出现同账号在 Flutter 有头像、Web 却是破图的情况。
- 这次只修 Web 显示层，没有去改后端存储格式，也没有动 Flutter 现有读写口径，避免把已经在用的头像链路带坏。

### 影响范围
- Web 前台个人中心与侧边栏
- Web 管理后台头像显示
- 头像显示兼容逻辑

### 验收重点
- 线上用户名 `kona` 在 Web 端个人中心里，头像是否不再显示成破图。
- 管理后台侧边栏头像是否也能正常显示同一张头像。
- 新上传头像和历史老头像，是否都能在 Web 端正常显示。

## 历史记录 051（原 v1.0.51）

### 这版一句话

把 Web 首页和投资页收成了更像正式产品的一版：总资产趋势图和持仓小趋势线都接上真实数据，首页交互更顺，管理后台邀请码复制也补了兜底。

### 主要变化
- 首页总资产折线图正式接入历史快照，`近1月 / 近3月 / 近6月 / 近1年 / 全部` 都按真实快照切片显示，不再是假切换；提示框、时间范围、副标题和空态也一起补齐。
- 首页和投资页的持仓卡片小折线改成真实“近期估值趋势”，股票 / 港股 / 场内 ETF 走历史收盘，场外基金走历史净值；拿不到历史时明确显示“暂无趋势”，不再偷偷画假线。
- 场内 ETF 的交易代码和统计分类继续拆开，价格仍按交易所走，但在用户端统计和筛选里继续算进基金。
- 首页投资资产卡片改成默认不展开，点击直接进入投资页；现金 / 其他 / 负债的编辑弹窗补了删除按钮、图标持久化、货币自定义下拉和原币种展示。
- 管理后台邀请码页的复制逻辑补了 `navigator.clipboard` 失败时的传统复制兜底，不再因为浏览器权限或上下文问题直接报“复制失败”。

### 影响范围
- Web 首页、投资页、管理后台邀请码页
- 后端趋势接口与基金历史净值兜底逻辑
- 后端投资组合分类口径

### 验收重点
- 首页和投资页里，股票 / 港股 / 基金卡片的小趋势线是否都来自真实数据；拿不到历史时是否只显示“暂无趋势”。
- 首页总资产图切换 `近1月 / 近3月 / 近6月 / 近1年 / 全部` 时，折线、范围文案和副标题数值是否联动。
- 管理后台 `/admin/invites` 点击邀请码后，是否显示“复制成功”，不再提示“复制失败”。


## 历史记录 050（原 v1.0.50）

### 这版一句话

把场内 ETF 的“取价链路”和“基金统计分类”拆开，价格继续按交易所走，用户端统计重新回到基金桶。

### 主要变化
- 后端投资组合接口新增独立的 `category_type` 口径，不再把交易代码和统计分类绑死在一个 `asset_type` 上。
- `sz159201`、`sz159687`、`sh511360` 这类场内 ETF / LOF / REIT 继续按场内交易所价格刷新，但在首页和投资页的分类统计里会算进“基金”。
- Web 首页和投资页的基金筛选、市场卡片和标签展示改为优先使用 `category_type`，不影响现有场内交易行为、单位和报价链路。

### 影响范围
- Web 首页
- Web 投资页
- 后端投资组合接口返回口径

### 验收重点
- 检查场内 ETF 在“基金”标签下能看到，在“A股”标签下不再混入。
- 检查这些资产的当前价仍然等于场内交易所价格，没有退回场外净值口径。

## 历史记录 049（原 v1.0.49）

### 这版一句话

紧急修复 Web 注册页邀请码输入被卡成 8 位，恢复 10 位邀请码可正常填写。

### 主要变化
- 将 Web 注册页的邀请码输入框最大长度从 `8` 改为 `10`，不再把合法邀请码截断。
- 同步把输入占位文案改成 10 位长度，减少用户误以为邀请码只有 6 到 8 位的误导。
- 保持现有大写输入逻辑不变，不影响后端注册接口和邀请码校验链路。

### 影响范围
- Web 登录/注册页
- 邀请码注册流程

### 验收重点
- 在 `/app/login` 切到注册态后，确认邀请码可以完整输入 10 位。
- 用 10 位邀请码提交注册，确认前端不再提前截断。

## 历史记录 048（原 v1.0.48）

### 这版一句话

管理后台 (Admin) 全站 UI 风格对齐重构大功告成，全视觉 1:1 进化为极简现代风。

### 主要变化
- **邀请码管理重构与深度优化**：
    - **物理随机化修复**：彻底修复了 SQL `ORDER BY RANDOM()` 失效与后端静态缓存干扰问题，实现每次刷新“无重复惊喜”。
    - **UI 精简**：移除了生成数量输入框，默认固定为 10，并将刷新按钮改为文字样式，操作更纯粹。
    - **交互增强**：邀请码列移至首列，点击复制改为局部反馈，增加悬停视觉提示。
- **概览页细节汉化**：将数据概览的日期格式统一为 `3月8日` 中文格式，并实现表格数据居中展示，提升中文环境下的阅读感。
- **全站布局对齐**：彻底移除了遗留的 `LegacyAdminShell`，全站管理页（概览、用户、邀请码、配置、接口）统一注入了全新的极简侧边栏与主容器布局。
- **运营配置深度优化**：
    - 页面采用响应式网格卡片布局，提升了配置项的可读性。
    - 同步重构了“配置编辑”与“更新发布”两款弹窗，应用了磨砂玻璃背景、大圆角及现代化交互。
- **接口管理视觉对齐**：整合了行情测试、快照诊断与价格巡检三大监控模块，优化了状态 Badge 的视觉层级。
- **细节像素调优**：统一了全站表格、分页、按钮及个人信息栏的样式，去掉了冗余的单位说明及问候语，界面更纯净。

### 影响范围
- **AdminInvitesPage.vue / AdminConfigPage.vue / AdminApisPage.vue**
- **OpsConfigEditorModal.vue / OpsAppUpdateEditorModal.vue**
- 管理后台侧边栏及全局布局容器

### 验收重点
- 验证邀请码管理页 Tab 切换是否平滑。
- 验证运营配置项编辑弹窗的预览功能与保存逻辑。
- 验证接口管理页的各个巡检按钮及弹窗详情展示。
- 确认全站侧边栏在不同管理页间切换时保持一致且无抖动。

## 历史记录 047（原 v1.0.47）

### 这版一句话

把 Web 端浅色模式从“能切”补到了“页面和弹窗都跟着走”。

### 主要变化
- 补齐了 Web 主题的全局同步逻辑，`teleport` 到 `body` 的弹窗也会跟着浅色模式切换，不再出现页面白了、弹窗还是黑的割裂感。
- 重做了业务端登录页浅色态，表单区、右侧品牌区、邀请码气泡和统计卡片全部按浅色视觉落地。
- 修复了投资页“添加资产”弹窗、个人中心修改密码弹窗，以及首页/投资页一批按钮、分隔线、进度条和卡片底色的浅色错色问题。
- 补了一组新的主题变量，让后续页面继续做浅色收口时不用再到处写死颜色。

### 影响范围
- Web 登录页、首页、投资页、个人中心页
- Web 弹窗体系，尤其是 `teleport` 到 `body` 的业务弹窗
- 全局主题变量与页面壳层背景

### 验收重点
- 在浅色模式下检查 `/app/login` 是否已经整页变成浅色，而不是只白左半边。
- 在浅色模式下打开投资页“添加资产”弹窗，确认弹窗、输入框、下拉、遮罩都不再是深色残留。
- 在浅色模式下打开个人中心“修改密码”弹窗，确认遮罩、按钮和输入框视觉一致。
- 切换主题后刷新页面，确认主题状态能保留，弹窗也继续跟着当前主题。


## 历史记录 046（原 v1.0.46）

### 这版一句话

管理后台登录页全新视觉重构，1:1 还原现代化玻璃拟态设计并全面中文化。

### 主要变化
- **视觉升级**：应用了全新的 1:1 设计稿视觉（`login-page-2.html`），包含动态背景渐变、虚化卡片以及艺术肖像 SVG。
- **文案中文化**：将所有登录表单及页面的英文文案翻译为中文，更符合国内管理后台使用习惯。
- **响应式优化**：针对窄屏设备（<920px）增加了自适应布局逻辑，自动隐藏右侧肖像区并优化表单宽度。
- **交互完善**：新增了回车键提交、记住账号勾选逻辑，并优化了验证中状态的视觉反馈。

### 影响范围
- **AdminLoginPage.vue**：管理后台登录页（`/admin/login`）。

### 验收重点
- 检查页面视觉高度还原度。
- 验证在不同分辨率下的响应式布局表现。
- 确认中文文案准确无误。
- 测试登录功能逻辑是否完整（含错误提示）。

---

### 影响范围
- **AppShell.vue**：全局侧边栏布局。
- **AppMePage.vue**：个人中心页面功能与样式。

### 验收重点
- 查看左下角个人信息，确认状态文字已消失。
- 进入「我的」页面，点击右侧编辑图标，确认弹窗显示并能成功保存。

## 历史记录 045（原 v1.0.45）

### 清理「我的」页面冗余信息

### 主要变化
- **移除卡片**：从「我的」页面中彻底移除了“我的记账”记录次数卡片和“支持货币”动态同步卡片。
- **样式优化**：将「我的」页面布局由双栏调整为单栏，使设置项展示更加专注。
- **性能/清理**：删除了相关的计算属性（accountingProgress）与冗余样式，消除了代码告警。

### 影响范围
- **AppMePage.vue**：UI 结构与布局逻辑。

### 验收重点
- 进入「我的」页面，确认右侧两个卡片已消失，主区域宽度自适应。

## 历史记录 044（原 v1.0.44）

### 这版一句话

修复了首页卡片溢出问题，并统一了全站 Web 布局的侧边栏间距与最大宽度。

### 主要变化

- **布局容器升级 (AppShell)**：引入了 `.container-inner` 统一容器，将侧边栏与内容的间距固定为 **24px**，并为大屏增加了 **1400px** 的最大宽度限制（居中显示）。
- **首页响应式优化**：
    - 将指数卡片网格从固定 6 列改为响应式 `auto-fill`，彻底解决窄屏溢出。
    - 将持仓概要卡片网格从固定 4 列改为响应式布局。
- **样式清理**：移除了 `homepage-original.css` 中冗余的旧边距定义。

### 影响范围

- Web 全站布局对齐
- 首页渲染稳定性与大屏适配

### 验收重点

- 验证侧边栏间距是否始终保持 24px。
- 验证“我的资产”标题是否与下方内容完美对齐。
- 验证在不同窗口宽度下，首页卡片是否能正常换行而无水平滚动条。

---

## 历史记录 042（原 v1.0.42）

### 这版一句话

完成了全站 Web 布局的 AppShell 统一化重构，并深度优化了快讯页的单栏阅读体验。

### 主要变化

- **全站布局统一 (AppShell)**：重构了首页、投资页、分析页、快讯页和个人中心，统一使用性能优化的 `AppShell.vue` 布局组件，彻底解决了侧边栏在不同路由下样式不一致或缺失的问题。
- **快讯页沉浸式优化**：
    - 移除了右侧所有冗余卡片（今日快讯统计、相关持仓）。
    - 采用单栏居中布局，大幅精简了数据处理逻辑，提升首屏加载速度。
    - 修复了后端 `api.news` 接口权限导致的 Timeline 数据缺失问题。
- **首页 Bug 修复**：解决了重构过程中意外导致的首页侧边栏显示异常及 Vue 模板语法错误。
- **视觉增强**：统一了全站的截图、隐私模式和主题切换交互。

### 影响范围

- Web 全站布局逻辑
- 快讯页面数据流与布局
- 首页渲染稳定性

### 验收重点

- 验证从首页、投资、分析到快讯的切换是否丝滑，侧边栏是否始终保持一致。
- 确认快讯页是否已变为单栏居中，且内容正常加载。
- 确认首页侧边栏已恢复正常。

---

## 历史记录 035（原 v1.0.35）

### 这版一句话

修复了注册页面邀请码二维码弹出层被顶部边缘遮挡的问题。

### 主要变化

- **UI 交互优化**：将注册页“获取邀请码”二维码的弹出方向由「向上」改为「向下」。
- **视觉修正**：同步调整了弹出层小三角箭头的指向，确保持仓展示逻辑与视觉指示一致。

### 影响范围

- 注册页面（`/app/register`）

### 验收重点

- 在注册页鼠标悬停至「获取邀请码」时，二维码应顺滑地向下方弹出，且顶部不被遮挡。

---

## 历史记录 034（原 v1.0.34）

### 这版一句话

修正了全站持仓成本价的取值口径，并解决了首页资产卡片的成本价显示错误。

### 主要变化

- **口径统一**：全站统一使用「摊薄后成本价」（考虑 adjustment 调节后的真实持仓成本）进行展示。
- **Store 增强**：在数据层补齐了 `cost`（总成本）和 `displayCostPrice`（摊薄单价）字段，消除前端计算歧义。
- **首页 Bug 修复**：解决了首页持仓概览在数据缺失时演示逻辑误将「成本价」用作「现价」覆盖的问题。
- **投资页同步**：同步更新投资页映射逻辑，移除客户端冗余重复计算，直接消费 Store 标准数据。

### 影响范围

- Web 全站持仓数据展示
- 盈亏计算基准精度

### 验收重点

- 验证首页与投资页的「成本」是否一致，且符合数据库中 `price` 摊薄后的预期。
- 确认长数值金额在首页卡片右上角显示正常（不换行）。

---

## 历史记录 033（原 v1.0.33）

### 这版一句话

修复了本地验收时的登录 500 报错，并按需优化了首页持仓概览的布局与交互。

### 主要变化

- **本地环境修复**：补齐了本地后端的 `.env` 密钥配置并开启自动加载，解决了登录过程中的服务端错误。
- **首页布局重构**：持仓概览由列表改为每行 4 个的网格卡片，展示上限调整为 8 个。
- **交互限制**：首页持仓卡片点击不再跳转，防止误触。
- **视觉增强**：实现数值字号自适应缩放，确保持仓标签与数量在任何数值下都不换行。
- **代理修正**：将本地开发环境的 API 代理目标从生产 IP 切回本地后端进程。

### 影响范围

- 本地开发环境（登录/API 通道）
- Web 首页（持仓概览模块）
- 全站资产卡片（数值显示逻辑）

### 验收重点

- [http://localhost:5173/app/login](http://localhost:5173/app/login) 能否正常登录。
- 首页持仓概览是否为每行 4 个、最多 8 个，且点击无跳转。
- 长数值（如 10,000,000）是否能自动缩小字号并不换行。

---

## 历史记录 032（原 v1.0.32）

### 这版一句话

这版主要对 Web 端投资页的“添加资产”弹窗进行了 1:1 的视觉和交互原味复刻。

### 主要变化

- Web 端投资页“添加资产”弹窗全面重构，应用暗夜极客风全新 UI。
- 新增资产搜索防抖与选中确认状态，自动匹配对应市场的颜色标签。
- 买入输入框支持数量与总金额的双向自动计算同步。
- 采用原生 DOM 挂载彻底解决了由于基础组件类名混用导致的幽灵全透明 Bug。
- 引入了全新设计的独立资金账户管理侧滑层原型界面。

### 影响范围

- Web 投资页
- 添加资产与交易流程

### 验收重点

- 投资页点击“添加资产”弹窗是否秒出且正常显示
- 原型设计 1:1 UI 是否无损还原
- 买入金额关联计算与提交入库逻辑是否正常

---

## 2026-03-07-01

### 这版一句话

这版主要对 Web 端首页和投资页进行了 UI 重构，并补齐了全系统的项目结构说明文档。

- **投资页滚动优化**: 修复了页面底部滚动截断问题，确保所有持仓明细可见。
- **侧边栏 UI 精简**: 移除了投资页侧边栏冗余的“添加资产”按钮。
- **UI 操作同步**: 参照首页同步了投资页的 📸 截图拍照功能，并移除了右上角冗余的 "CNY" 文本。
- **文档完美化**: 升级 `AGENTS.md`，补充环境约束、命令速查及代码禁区规范；同步更新 `项目结构.md` 技术细节。
- **Web 端 UI 优化 (AppInvestPage)**: 整合左侧导航栏 (Sidebar)，保持与首页一致；移除“投资资产分析”标题、副标题，及“CNY 汇率折算”相关文案。
- **Store 架构重构 (composables.ts)**: 将 `useKonaStore` 的 `state` 改为基于 `reactive` 的代理模式，解决全站由于 `ComputedRef` 类型变更引发的属性访问报错。
- **TypeScript 修复**: 修正 `LegacyAppShell.vue`、`AppProfilePage.vue`、`AppMePage.vue` 和 `AppAssetDetailPage.vue` 中的类型定义与响应式访问冲突。
- **代码清理**: 移除冗余的 `archive/` 目录；清理 `AppInvestPage` 及其他页面的未使用的变量与代码。
- **CI/CD 修复**: 恢复 `flutter/android` 下的 `gradle-8.13` 版本，确保 Android 构建流水线通畅。

### 影响范围
- Web 前端所有使用 `useKonaStore` 的页面（已完成兼容性修复）。
- 投资资产详情与分析页面布局。
- Flutter Android 构建流水线。

### 验收重点
- `http://localhost:5173/app/invest` (本地 Web 端) 侧边栏是否存在且功能正常。
- Web 端构建 (`npm run build`) 是否无报错。
- 侧边栏“添加资产”按钮功能是否正常。
- `docs/` 下的文档是否清晰完整
- 仓库内不再包含 `archive/` 目录

---

## 历史记录 031（原 v1.0.31）

### 这版一句话

这版重点修了“基金价格不准、快讯偏慢、刷新节奏不稳定、部署偶尔抽风”这几件事。

### 主要变化

- 基金价格优先使用更可信的确认净值，减少价格看起来不对的情况。
- A 股、港股、美股、基金的取价顺序重新整理，优先快、优先准。
- 批量价格接口更快了，首页和投资页首屏等待更短。
- 快讯页改成“先给你一批，再慢慢补新内容”，打开更顺。
- Web 和 App 的刷新节奏更一致，失败后的回退也更稳。
- 部署流程更稳了，冷启动时不容易误判失败。

### 影响范围

- 投资页
- 快讯页
- 后端价格接口
- 自动部署

### 验收重点

- 基金现价是否更接近外部官方页面
- 快讯打开是否更快
- 投资页刷新时是否更顺
- 部署后服务是否稳定启动

---

## 历史记录 030（原 v1.0.30）

### 这版一句话

这版主要修页面闪烁、颜色不一致、日期选择不好用、版本号显示不稳这些体验问题。

### 主要变化

- 首页、投资、快讯、个人中心、分析页的主题更统一了。
- 一些白一下、闪一下、边线怪怪的问题被修掉了。
- 分析页日期选择更顺，不容易乱跳。
- 版本号显示兼容带 `v` 前缀的写法。
- 编辑资产弹窗里的删除入口恢复了。

### 影响范围

- Flutter 页面体验
- Web 视觉一致性
- 日期选择交互

### 验收重点

- 切换页面时还会不会闪
- 弹窗颜色是不是顺眼了
- 分析页日期切换是否顺手

---

## 历史记录 029（原 v1.0.29）

### 这版一句话

这版主要把“用户群弹窗”和“保存图片到相册”做顺了。

### 主要变化

- 用户群弹窗更简洁，不再堆太多废话。
- 运营文案位置更合理，层次更清楚。
- 保存二维码图片到相册的成功率明显提高。
- 弹窗右上角的关闭按钮去掉了，点空白就能关。
- 同时补齐了部分历史快照数据。

### 影响范围

- Flutter 个人中心
- 用户群弹窗
- 图片保存功能

### 验收重点

- 图片能不能正常保存到相册
- 弹窗排版是否清楚
- 点击空白关闭是否符合预期

---

## 历史记录 028（原 v1.0.28）

### 这版一句话

这版主要把分析页做得更像正式产品，同时把排行和盈亏汇总算准了。

### 主要变化

- 分析页顶部大卡片视觉升级，和首页、投资页更统一。
- 文案和金额排版更聚焦，信息层级更清楚。
- 日历下面的盈亏汇总改成更紧凑的一行布局。
- 盈利榜和亏损榜的排序逻辑修正，改成按累计盈亏看，不再乱排。
- 修复了有些汇总显示成 0 的问题。

### 影响范围

- Flutter 分析页
- 盈亏排行
- 汇总卡片

### 验收重点

- 分析页视觉是否统一
- 排行顺序是否合理
- 汇总金额是否不再显示 0

---

## 历史记录 027（原 v1.0.27）

### 这版一句话

这版主要是把分析页按目标样式大改了一轮，重点是视觉还原和排行榜观感。

### 主要变化

- 分析页整体按目标原型重做。
- 背景、卡片、切换控件、日历、榜单都更统一。
- 盈亏排行前几名加了更明显的勋章样式。
- 查看全部排行页也一起同步了风格。

### 影响范围

- Flutter 分析页
- 排行页面

### 验收重点

- 页面风格是否统一
- 日历是否整齐
- 榜单是否比以前更清楚

---

## 历史记录 026（原 v1.0.26）

### 这版一句话

这版主要优化了投资列表和账户选择器，让交易时更顺手、更好看。

### 主要变化

- 投资弹窗里的账户选择器按目标样式重做。
- 持仓列表默认按当日盈亏从高到低排，更方便先看最重要的。
- PnL 进度条单独做成组件，视觉更细。
- 长名称会自动截断，不再把布局挤坏。
- 修掉了负数盈亏有时不显示负号的问题。

### 影响范围

- Flutter 投资页
- 交易弹窗

### 验收重点

- 列表排序是否合理
- 账户选择器是否顺手
- 负数是否正常显示负号

---

## 历史记录 025（原 v1.0.25）

### 这版一句话

这版主要把登录页重做了，同时把邀请码弹窗、图片保存和启动卡顿这些问题一起处理了。

### 主要变化

- 登录页和注册页按新视觉全部重做。
- 输入框、按钮、Logo、密码强度条、动画都换成新样式。
- 邀请码弹窗支持保存图片到相册。
- 登录页字体和样式做了缓存，减少卡顿。
- 构建环境升级，解决新版工具链编译不稳定的问题。

### 影响范围

- Flutter 登录页
- 注册页
- 邀请码弹窗
- Android 构建

### 验收重点

- 登录注册流程是否顺
- 输入框聚焦是否不卡
- 邀请码弹窗图片能否保存

---

## 历史记录 024（原 v1.0.24）

### 这版一句话

这版重点收口了投资弹窗和成本展示规则，让“显示给你看的成本”和“真实录入成本”不再打架。

### 主要变化

- 投资页开始显示“摊薄后成本”，更贴近真实持仓状态。
- 但编辑时仍然保留原始录入成本，不把展示值写回去。
- 交易弹窗整体 UI 升级。
- 卖出时只允许回到同币种现金账户。
- 没有可用现金账户时，支持弹窗里直接补建。
- 其他资产和负债的币种也正式打通了。

### 影响范围

- Flutter 投资页
- Web 投资页
- 后端资产逻辑

### 验收重点

- 列表显示成本是否合理
- 编辑资产时原始成本有没有被误改
- 卖出回款是否只到同币种账户

---

## 历史记录 023（原 v1.0.23）

### 这版一句话

这版把现金账户币种和交易回款规则补完整了。

### 主要变化

- 现金账户支持选 `CNY / USD / HKD`。
- 买入和卖出时，只显示同币种资金账户。
- 卖出缺少同币种账户时，可以一键新建。
- 现金账户支持 0 余额，不再强制必须大于 0。

### 影响范围

- Flutter 交易弹窗
- 后端现金账户逻辑

### 验收重点

- 外币现金账户能不能正常新建
- 卖出时回款账户过滤是否正确
- 0 余额账户是否能保存

---

## 历史记录 022（原 v1.0.22）

### 这版一句话

这版主要修了添加资产交互和收益日历回跳问题，同时把 B 股币种口径纠正了。

### 主要变化

- 添加资产弹窗改成手动点搜索，不再边打字边乱搜。
- 数字输入规则更稳，减少误输入。
- 收益日历从历史月切回当月的问题修好了。
- B 股币种规则统一：
  - `sh900xxx` 记作美元
  - `sz200xxx` 记作港币
- 老数据里错的 B 股币种也会自动修正。

### 影响范围

- Flutter 添加资产弹窗
- Web/Flutter 分析页
- 后端币种识别

### 验收重点

- 搜索是否改成手动触发
- 收益日历能否正常切回当月
- B 股币种展示是否正确

---

## 历史记录 021（原 v1.0.21）

### 这版一句话

这版主要统一了登录提示和版本规则，同时补上了碎股支持。

### 主要变化

- 登录失败提示改成普通人能看懂的话。
- 版本号格式统一成 `1.0.x`，不再带那种看着乱的后缀。
- 投资页数量支持小数，更符合碎股场景。
- 添加资产里的价格文案改成“买入成本价”，更清楚。

### 影响范围

- Flutter 登录页
- Flutter 投资页
- 版本管理

### 验收重点

- 登录失败提示是否清楚
- 碎股数量是否正常显示
- 版本号展示是否统一

---

## 历史记录 020（原 v1.0.20）

### 这版一句话

这版把“获取邀请码”和“用户群”从外部跳转改成了站内可运营页面。

### 主要变化

- 注册页获取邀请码改成 App 内页，不再外跳。
- 管理后台可以直接改邀请码页和用户群页的文案、图片。
- 邀请码页和用户群页虽然长得像，但配置已经拆开，不会互相影响。
- 版本更新和下载地址的配置链路更完整了。

### 影响范围

- Flutter 注册页
- Flutter 个人中心
- 管理后台
- 后端配置接口

### 验收重点

- 邀请码页和用户群页是否都能站内打开
- 后台改配置后前端是否生效
- 下载地址是否正确

---

## 历史记录 019（原 v1.0.19）

### 这版一句话

这版主要修了登录时“明明有网但连不上”的问题。

### 主要变化

- App 默认接口地址改成直接连 IP，绕开某些代理环境下的域名问题。
- 服务器补了 HTTP 入口，避免 HTTPS 在特殊环境下握手失败。
- 构建工具一起升级，解决新版 Flutter 编译问题。

### 影响范围

- Flutter 登录
- 线上入口
- Android 构建

### 验收重点

- 手机在代理环境下能不能正常登录
- 构建是否不再报工具链错误

---

## 历史记录 018（原 v1.0.18）

### 这版一句话

这版是一次正式迁云，把服务从旧环境搬到了腾讯云。

### 主要变化

- 生产环境迁到腾讯云。
- 公网入口统一成新 IP。
- 服务改成反向代理 + 后端服务的正式结构。
- 补上 Redis，修掉迁移后登录报错的问题。
- Flutter 默认接口地址改到新服务器。

### 影响范围

- 线上部署
- 后端服务
- Flutter 接口地址

### 验收重点

- 首页、登录、健康检查是否正常
- 新服务器是否稳定
- 老库数据是否完整迁过去

---

## 历史记录 017（原 v1.0.17）

### 这版一句话

这版主要把管理后台用户页做实用了，同时补了首屏体验和服务器稳定性。

### 主要变化

- 用户页支持排序和分页，不再一次性拉一大堆。
- 时间和地区显示更统一，更像给人看的后台。
- 强刷管理后台不再大面积黑屏。
- 服务器小幅扩容，抗压稍微强一点。

### 影响范围

- Web 管理后台
- 后端用户接口
- 线上服务器

### 验收重点

- 用户页排序分页是否正确
- 活跃地区是否正常显示
- 强刷后台是否不再黑屏

---

## 历史记录 016（原 v1.0.16）

### 这版一句话

这版主要修了资产分类规则，特别是把一些美股 ETF 被误当基金的问题处理掉了。

### 主要变化

- 美股 ETF 不再错走基金逻辑。
- 搜索和入库前会先做更严格的代码标准化。
- 历史上错入库的数据也做了修正。

### 影响范围

- 后端搜索
- 持仓入库
- 价格获取

### 验收重点

- 美股 ETF 是否能正常取价
- 搜索结果是否不再混进奇怪的基金代码

---

## 历史记录 015（原 v1.0.15）

### 这版一句话

这版主要修了 Web 和 App 同时登录时的会话稳定性，还把 APK 下载入口补完整了。

### 主要变化

- token 失效时，App 和 Web 都更容易自动续上，不会轻易掉成空数据。
- 门户页 APK 下载链路正式打通。
- 门户强刷时首屏体验更稳。

### 影响范围

- Web 登录态
- App 登录态
- 门户下载页

### 验收重点

- 多端同时在线时会不会莫名掉登录
- 下载 APK 是否正常

---

## 历史记录 014（原 v1.0.14）

### 这版一句话

这版主要优化了 Flutter 的个人中心和投资页交互。

### 主要变化

- 系统设置入口和问题反馈入口重新整理。
- 投资页底部大块留白问题修掉了。
- 下拉刷新时不再中间冒出很打断人的大 Loading。

### 影响范围

- Flutter 个人中心
- Flutter 投资页

### 验收重点

- 个人中心入口是否更顺
- 投资页底部空白是否减少
- 下拉刷新是否更自然

---

## 历史记录 013（原 v1.0.13）

### 这版一句话

这版主要让后端提前把行情准备好，用户打开页面时更像“秒回”。

### 主要变化

- 后端会定时预取持仓行情。
- 前端请求更容易直接命中缓存。
- 整体响应速度明显提升。

### 影响范围

- 后端价格接口
- 首页、投资页等依赖行情的页面

### 验收重点

- 打开页面是不是明显更快
- 后端日志里是否能看到缓存命中

---

## 历史记录 012（原 v1.0.12）

### 这版一句话

这版主要修了 App 冷启动不同步、排行跨币种不准，以及收益率分母不对这几个口径问题。

### 主要变化

- App 启动后会立刻同步一次，不用等很久。
- 盈亏排行开始按统一币种比较，更公平。
- 收益率计算改了，避免因为当天加仓把收益率稀释得很离谱。
- 新增“外部资金 / 初始转入”选项，没有现金账户时也能记投资。
- 搜索体验更稳，清空后不会冒出幽灵结果。
- 登录页的生物识别和记住用户名体验也做了一轮优化。

### 影响范围

- Flutter 启动同步
- 分析页排行
- 收益率计算
- 添加资产和买卖流程
- 登录页体验

### 验收重点

- 冷启动后数据是否自动更新
- 排行跨币种是否更合理
- 收益率是否不再明显失真
- 没现金账户时能否正常录入投资

---

## 历史记录 008（原 v1.0.8）

### 这版一句话

这版主要是 Web 端一次比较大的整理，把门户、登录、主题、隐私模式和截图工具一起做顺了。

### 主要变化

- 门户首页换了新样式。
- 登录和注册页改版。
- Web 业务端加入深浅主题切换。
- 首页、投资页、分析页都支持隐私模式和截图。
- 页面开始更强调“先显示缓存，再后台刷新”，减少白屏。

### 影响范围

- Web 门户
- Web 登录注册
- Web 首页 / 投资 / 分析

### 验收重点

- 主题切换是否正常
- 隐私模式是否统一
- 截图功能是否可用

---

## 历史记录 007（原 v1.0.7）

### 这版一句话

这版主要把 Web 登录注册流程做清楚了，错误提示也改成中文了。

### 主要变化

- 登录和注册拆成两个独立页面。
- 新增确认密码和邀请码校验。
- 错误提示改成中文。
- 登录成功后更快进入首页。

### 影响范围

- Web 登录页
- Web 注册页

### 验收重点

- 中文提示是否清楚
- 注册校验是否完整
- 登录成功是否更快

---

## 历史记录 006（原 v1.0.6）

### 这版一句话

这版主要收了 Web 侧边栏、个人中心和快讯页体验。

### 主要变化

- 侧边栏把设置入口下沉到用户区。
- 个人中心首屏更直接。
- 快讯页的“只看重要”和 LIVE 标识更合理。
- 多个页面开始更偏缓存优先，减少强刷卡顿。

### 影响范围

- Web 侧边栏
- Web 个人中心
- Web 快讯页

### 验收重点

- 侧边栏是否更干净
- 快讯页是否更像产品页
- F5 后是否没那么容易白屏

---

## 历史记录 005（原 v1.0.5）

### 这版一句话

这版主要把 Web 分析页做得更完整，同时修了排行和外币金额显示问题。

### 主要变化

- Web 分析页更接近 App 体验。
- 排行榜改成单榜查看，不再切来切去。
- 外币盈亏统一折算后展示，金额更可信。
- 修了价格为 0 时带来的持有金额异常。

### 影响范围

- Web 分析页
- Web 排行
- 后端排行接口

### 验收重点

- 分析页日历和排行是否更顺
- 港股、美股金额是否更合理

---

## 历史记录 004（原 v1.0.4）

### 这版一句话

这版主要统一了增量刷新和休市口径，减少“今天收益看起来怪怪的”问题。

### 主要变化

- 页面启动时不再无脑全量刷新。
- 行情刷新和静态数据刷新分开。
- 休市时展示冻结值，但汇总只统计真正开市的市场。
- Web 和 Flutter 的市场状态判断更统一。

### 影响范围

- Flutter
- Web
- 后端刷新接口

### 验收重点

- 混合开市场景下今日收益是否更准
- F5 后是否不再重复疯狂请求

---

## 历史记录 003-01（原 v1.0.3）

### 这版一句话

这版主要修了收益日历和分市场收益明细。

### 主要变化

- 修掉了有些日期收益被错误压成 0 的问题。
- 增加按市场查看收益明细的能力。
- 历史补数脚本更完整，支持先预演再正式执行。
- 没证据的历史残差统一归到 `unallocated`，不瞎拆。

### 影响范围

- 后端快照
- 分析页日历
- 管理后台收益相关能力

### 验收重点

- 指定日期收益是否正确
- 分市场明细是否能看

---

## 历史记录 003-02（原 v1.0.3）

### 这版一句话

这版把投资页的持仓编辑链路和搜索报价补完整了，Web 和 Flutter 的添加资产弹窗也终于对齐了。

### 主要变化

- Web 投资页点击单个持仓后，不再跳错误详情页，改成直接弹出买入、卖出、调整编辑窗。
- 添加资产弹窗的搜索结果和已选资产，补上了现价、涨跌额、涨幅，并把真实有行情的股票排到前面。
- 后端搜索接口现在会把价格和涨跌数据一起返回，Web 和 Flutter 统一吃同一套字段。
- 搜索超时场景现在优先保证先回匹配结果，不会为了补右侧报价把接口再额外拖慢一轮。
- 修掉了投资页左侧内容区露黑缝的问题，页面布局和卡片展示更稳了。

### 影响范围

- Web 投资页
- Flutter 投资弹窗
- 后端搜索接口

### 验收重点

- Web 投资页点击持仓是否直接弹出编辑窗
- 添加资产搜索结果是否正常显示价格、涨跌额、涨幅
- Flutter 添加资产弹窗的显示口径是否和 Web 一致

---

## 历史记录 003-03（原 v1.0.3）

### 这版一句话

这版把管理后台工具页重新做顺了，也把首页和投资页里那些“看着像真的，其实是假的”趋势线换成了真实数据。

### 主要变化

- 首页总资产折线图正式接入快照数据，时间切换、区间文案、悬浮提示都能用了。
- 首页和投资页持仓卡片的小趋势线改成真实历史数据，不再用假线糊弄人。
- 接口管理页重做成卡片入口页，单资产排查、行情测试、异常测试、快照检测都改成点开弹窗看结果。
- 行情测试新增小时级自动检测快照，外卡能直接看到最近测试时间和告警状态。
- 运营配置页改成和接口管理一致的小卡片入口样式。
- 后台左下角管理员头像改成优先显示真实头像，没有头像再回退字母头像。
- 管理后台邀请码复制补了兜底逻辑，也去掉了重复的“复制成功”提示。

### 影响范围

- Web 首页
- Web 投资页
- Web 管理后台
- 后端行情测试与后台排障接口

### 验收重点

- 首页和投资页趋势线是否都是真数据，时间切换和悬浮提示是否顺手。
- 接口管理页的卡片入口、弹窗交互、行情测试状态标签是否清楚。
- 运营配置页是否已经改成 4 张小卡片入口。
- 后台侧边栏头像是否能正确显示真实头像。

---

## 历史记录 002（原 v1.0.2）

### 这版一句话

这版主要补了安全、监控、备份恢复这些“平时看不见，但出事时很要命”的底层能力。

### 主要变化

- 登录注册等关键操作有审计记录了。
- 价格健康监控和告警上线了。
- 数据库自动备份和恢复流程上线了。
- 运维从“全靠人盯”变成“系统自己盯一部分”。

### 影响范围

- 后端运维
- 安全
- 监控
- 备份恢复

### 验收重点

- 告警是否能触发
- 备份能不能生成
- 恢复流程是否能走通

---

## 历史记录 001（原 v1.0.1）

### 这版一句话

这版主要把发布流程正规化了，避免“代码没验就上线”。

### 主要变化

- 发布流程拆成“检查通过后再部署”。
- `main` 分支必须过门禁才能发版。
- PR 只做检查，不直接上线。
- 部署后会做健康检查。

### 影响范围

- GitHub Actions
- 自动部署
- 前后端发版流程

### 验收重点

- 门禁是否都能正常跑
- 部署后健康检查是否通过

---

## 历史记录 000（原 v1.0.0）

### 这版一句话

这是项目第一个可用的稳定基线版本。

### 主要变化

- 建立了资产、投资、分析、快讯、设置这些基础功能。
- 建立了登录、注册、邀请码、会话保持这些基本能力。
- 建立了快照、收益统计和多端展示的基础链路。
- 建立了后端服务、定时任务和基础文档。

### 影响范围

- Flutter
- Web
- 后端
- 运维

### 验收重点

- 整个产品主流程能跑通
- 资产和投资能正常记
- 分析和快讯能正常看
## v1.0.x

### 这版一句话
给用户建账起点加了正式口径，首页总资产趋势图会按用户自己的建账开始日截断。

### 主要变化
- 后端 `/api/history` 现在会优先尊重用户 `build_start_at`
- 只要用户设置了建账起点，首页总资产趋势图就会从这天开始返回
- 补了一条接口测试，防止以后又把建账起点口径丢掉

### 影响范围
- Web 首页总资产趋势图
- 依赖 `/api/history` 的用户历史总资产展示

### 验收重点
- 指定用户设置 `build_start_at` 后，趋势图起点是否按该日期截断
- 未设置 `build_start_at` 的用户，历史趋势是否保持原样
## 2026-03-15-01

### 这版一句话

行情预取加了进程级锁与开关，避免 gunicorn 多 worker 重复启动预取线程。

### 主要变化
- [config.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/config.py) 增加 `ENABLE_PRICE_PRELOADER / PRICE_PRELOADER_LOCK_FILE`，允许显式开关与锁文件配置。
- [price.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/price.py) 预取启动前加进程锁，拿不到锁就跳过；预取数据库读取改成只读连接并沿用 SQLite 超时/PRAGMA 配置。

### 影响范围
- 后端行情预取线程（单实例化）
- SQLite 预取读取方式（只读连接）

### 验收重点
- gunicorn 多 worker 启动后只应有一个预取线程在跑（看日志或 `lsof`）
- 行情缓存仍能持续刷新，接口响应不降级
## 2026-03-15-10

### 这版一句话

Flutter 投资口径的汇总计算收口到服务层，页面与 AppState 统一走同一套入口。

### 主要变化
- [portfolio_metrics_service.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/services/portfolio_metrics_service.dart)：新增投资口径汇总与比例计算的集中入口。
- [app_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_state.dart)：投资汇总与收益率计算改走服务层。
- [invest_page.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/pages/invest_page.dart)：投资页汇总与分类汇总改走服务层计算。

### 影响范围
- Flutter 投资页汇总展示口径计算路径
- AppState 投资汇总口径计算路径

### 验收重点
- 投资页总市值 / 当日盈亏 / 累计盈亏与之前一致
- 分类汇总的当日盈亏率 / 累计盈亏率展示正常

## 2026-03-15-11

### 这版一句话

请求运行时的分组限流与活跃打点支持共享存储，健康检查里能看到运行时指标。

### 主要变化
- [request_runtime.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/request_runtime.py)：接口分组限流与活跃打点支持 Redis 共享存储，增加运行时指标。
- [misc_handlers.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/misc_handlers.py)：`/health` 增加 `request_runtime` 指标输出。
- [app_factory.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/app_factory.py) / [app.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/app.py)：补齐请求运行时共享存储配置注入。
- [config.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/config.py)：新增 `REQUEST_RUNTIME_STORAGE_URL/REQUEST_RUNTIME_STORAGE_PREFIX` 配置。

### 影响范围
- 接口分组限流的计数口径（多 worker 可共享）
- 用户活跃打点的节流口径（多 worker 可共享）
- `/health` 返回内容

### 验收重点
- 多 worker 场景下限流仍然生效且不会被分裂
- `/health` 能看到 `request_runtime` 字段

## 2026-03-15-12

### 这版一句话

确立 OpenAPI 为接口唯一口径，并补上 Web/Flutter 的类型生成流程。

### 主要变化
- [openapi.yaml](/Users/kona/Desktop/kaka/kona_repo/docs/openapi.yaml)：补充 `/health` 的 `request_runtime` 字段 schema。
- [package.json](/Users/kona/Desktop/kaka/kona_repo/web/package.json)：新增 Web 端 `gen:api` 类型生成脚本与依赖。
- [openapi.generated.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/types/openapi.generated.ts)：新增 OpenAPI 生成类型文件。
- [接口Schema与类型生成.md](/Users/kona/Desktop/kaka/kona_repo/docs/接口Schema与类型生成.md)：固定 schema 与类型生成流程说明。
- [generate_openapi_types_web.sh](/Users/kona/Desktop/kaka/kona_repo/scripts/generate_openapi_types_web.sh) / [generate_openapi_types_flutter.sh](/Users/kona/Desktop/kaka/kona_repo/scripts/generate_openapi_types_flutter.sh)：固化 Web / Flutter 生成入口脚本。

### 影响范围
- Web 类型生成流程
- `/health` 返回字段 schema

### 验收重点
- `npm run gen:api` 能生成 `openapi.generated.ts`
- 文档里能查到生成入口与输出路径

## 2026-03-15-13

### 这版一句话

补齐 OpenAPI 路径清单并把 Web 依赖安全修复推进到“仅剩不可修项”。

### 主要变化
- [sync_openapi_paths.py](/Users/kona/Desktop/kaka/kona_repo/scripts/sync_openapi_paths.py)：新增 OpenAPI 路径补齐脚本。
- [openapi.yaml](/Users/kona/Desktop/kaka/kona_repo/docs/openapi.yaml)：自动补齐缺失路径（带 TODO 占位响应）。
- [openapi.generated.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/types/openapi.generated.ts)：根据补齐后的 schema 重新生成。
- [package.json](/Users/kona/Desktop/kaka/kona_repo/web/package.json)：升级 `puppeteer` 与 `@typescript-eslint/*` 以消除可修复漏洞。

### 影响范围
- OpenAPI 路径覆盖率
- Web 端依赖版本与安全审计结果

### 验收重点
- `python3 scripts/sync_openapi_paths.py` 可重复执行且不产生重复路径
- `npm run gen:api` 正常生成类型

## 2026-03-15-14

### 这版一句话

补齐分析页、快照、后台关键接口的字段级契约测试。

### 主要变化
- [test_contracts_analysis_snapshot_admin.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_contracts_analysis_snapshot_admin.py)：新增分析页（overview / calendar / rank / market_breakdown）、快照、后台关键接口的字段级契约测试。

### 影响范围
- 后端契约测试覆盖面

### 验收重点
- `python3 -m unittest tests.test_contracts_analysis_snapshot_admin -v` 通过
## 2026-03-15-13

### 这版一句话

持仓口径补齐仓位占比：后端返回 `position_pct`，用于前端只展示。

### 主要变化
- [kona_tool/portfolio_handlers.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/portfolio_handlers.py)：持仓指标口径新增 `position_pct` 计算与返回。
- [kona_tool/tests/test_portfolio_metrics_contract.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_portfolio_metrics_contract.py)：合同测试增加 `position_pct` 断言。

### 影响范围
- `/api/portfolio?with_metrics=1` 返回字段
- `/api/sync/bootstrap` 的 `portfolio` 数据口径

### 验收重点
- `position_pct` 字段存在且为百分比数值
- `python3 -m pytest kona_tool/tests/test_portfolio_metrics_contract.py` 通过
## 2026-03-15-14

### 这版一句话

场内 ETF 的 `f_` 代码走 A 股实时行情，且不再显示“待净值更新”。

### 主要变化
- [kona_tool/core/price.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/price.py)：新增公开 helper 判断场内 ETF 的 `f_` 代码。
- [kona_tool/portfolio_handlers.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/portfolio_handlers.py)：场内 ETF 取 A 股市场状态与实时行情，关闭 `nav_update_pending`。
- [kona_tool/tests/test_portfolio_metrics_contract.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_portfolio_metrics_contract.py)：新增场内 ETF 口径合同测试。

### 影响范围
- `/api/portfolio?with_metrics=1` 的持仓口径（场内 ETF）
- 日内盈亏展示与“待净值更新”状态

### 验收重点
- `f_511360` 不再显示“待净值更新”
- 日内盈亏可用且 `market_trading_day` 来自 A 股

## 2026-03-21-01

### 这版一句话

把“日收益归哪一天”这件事彻底收正：美股夜盘归前一交易日，场外基金按净值对应日入账。

### 主要变化
- [kona_tool/core/day_pnl_attribution.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/day_pnl_attribution.py)：新增统一的日收益归属日计算层，集中处理美股夜盘和场外基金净值日期。
- [kona_tool/core/snapshot.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/snapshot.py) / [kona_tool/snapshot_runtime.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/snapshot_runtime.py)：快照改为按归属日写入市场拆分，不再把周五美股夜盘硬写到北京时间周六。
- [kona_tool/core/db_analysis.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/db_analysis.py) / [kona_tool/core/analysis_read_service.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/analysis_read_service.py)：分析页历史日历、月度、年度读取改为优先认归属日拆分数据，今天这格也改成覆盖真正的归属日。
- [kona_tool/core/db_portfolio.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/db_portfolio.py) / [kona_tool/core/market_calendar.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/market_calendar.py)：补齐按归属日汇总买入、已实现盈亏和前一交易日判断的基础能力。
- [kona_tool/tests/test_api_baseline.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_api_baseline.py) / [kona_tool/tests/test_calendar_weekend.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_calendar_weekend.py) / [kona_tool/tests/test_read_services.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_read_services.py)：新增美股周五夜盘、场外基金净值归属日和分析页日历覆盖的回归测试。

### 影响范围
- 分析页“当日 / 本月 / 本年 / 收益日历”口径
- 快照写入、市场拆分、场外基金日收益归属

### 验收重点
- 周五夜里到周六凌晨的美股收益，应继续记在周五，不应落成周六历史收益
- 场外基金不进实时今日收益，但拿到新净值后应落到 `latest_nav_date`
- `python3 -m unittest tests/test_read_services.py tests/test_calendar_weekend.py tests/test_market_breakdown.py tests/test_api_baseline.py tests/test_portfolio_metrics_contract.py tests/test_portfolio_api.py` 通过

## 2026-03-21-02

### 这版一句话

历史收益读侧改成只认 `daily_snapshots.day_pnl`，不再拿拆分表覆盖，也不再拿累计盈亏差额猜日收益。

### 主要变化
- [kona_tool/core/db_analysis.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/db_analysis.py)：历史收益序列只从 `daily_snapshots.day_pnl` 读取，不再默认用 `daily_snapshot_market_breakdowns` 合计覆盖主快照，也不再用 `total_pnl` 差额反推 `day_pnl`。
- [kona_tool/tests/test_calendar_weekend.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_calendar_weekend.py)：把周末 / 历史日历合同改成“快照写什么就读什么”，明确禁止历史读侧偷偷猜值。
- [kona_tool/tests/test_market_breakdown.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_market_breakdown.py)：新增合同，只有 breakdown 没有 snapshot 的日期，不允许进入主收益日历。
- [kona_tool/tests/test_analysis_api.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_analysis_api.py)：补齐 overview 合同，确认月度 / 全部只认有效日期里的 `day_pnl`，并忽略未来快照。

### 影响范围
- 分析页收益日历
- 分析页 `本月 / 本年 / 全部` 汇总
- `daily_snapshots` 与 `daily_snapshot_market_breakdowns` 的历史职责边界

### 验收重点
- 历史收益日历应优先认 `daily_snapshots.day_pnl`
- breakdown 只能做解释，不应反向覆盖主快照
- `python3 -m unittest tests/test_calendar_weekend.py tests/test_market_breakdown.py tests/test_analysis_api.py` 通过
## 2026-03-21-03

### 这版一句话

补齐收益归属日第二轮的历史落账闭环：美股夜盘和场外基金晚到收益按市场局部结算，不再整天覆盖旧历史。

### 主要变化
- **快照写入新增“局部结算”能力**：后端 [kona_tool/core/snapshot.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/snapshot.py) 现在在保存当天 `snapshot_date` 快照后，会只把晚到的 `us / fund` 收益结算到对应 `effective_date`，不再把整天 `A/HK/US/Fund` 全量重写。
- **数据库支持局部更新与主快照同步**：后端 [kona_tool/core/db_snapshots.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/db_snapshots.py) 新增按市场局部更新 `daily_snapshot_market_breakdowns` 和按拆分回写 `daily_snapshots.day_pnl` 的能力，为后续美股跨周六、场外基金 T+1 净值落账提供安全落点。
- **快照运行时复用统一保存逻辑**：后端 [kona_tool/snapshot_runtime.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/snapshot_runtime.py) 改成复用同一套快照保存函数，避免自动快照和接口快照两条链继续跑出不同口径。
- **补齐回归测试**：新增“只结算最新一日的美股/基金晚到收益，不覆盖更早历史日”的集成测试，以及快照运行时的局部结算测试。

### 影响范围
- 后端：自动快照写入、快照运行时、历史日收益落账
- 数据层：`daily_snapshots`、`daily_snapshot_market_breakdowns`

### 验收重点
- 美股周五夜盘在周六保存快照时，应只回写周五的 `us` 收益，不应把更早历史日整天覆盖掉
- 场外基金 T+1 净值只应补基金那一块，不应顺手清掉当天已有的 A/HK/US 拆分
- `snapshot_runtime` 和 `take_snapshot()` 应走同一套保存规则

## 2026-03-21-04

### 这版一句话

封住 legacy adjustment 的新增写入口：从现在开始，正常新增/更新持仓不再继续往 `portfolio.adjustment` 写旧口径数据。

### 主要变化
- [kona_tool/portfolio_handlers.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/portfolio_handlers.py)：`/api/portfolio/add` 不再接收前端传入的 `adjustment`，`/api/portfolio/update` 直接拒绝更新 `field=adjustment`。
- [kona_tool/core/db_portfolio.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/db_portfolio.py)：`add_asset()` / `update_asset()` 默认不再写 legacy adjustment；只有显式传 `allow_legacy_adjustment_write=True` 的导入/回放路径才允许写。
- [kona_tool/migrate.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/migrate.py)：历史 CSV / JSON 导入脚本显式声明允许写 legacy adjustment，避免把“普通新增”与“历史导入”混成一条链。
- [kona_tool/tests/test_portfolio_api.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_portfolio_api.py) / [kona_tool/tests/test_portfolio_schema_migration.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_portfolio_schema_migration.py)：补齐合同测试，保证外部请求封口、数据库默认保守、特殊导入必须显式 opt-in。

### 影响范围
- 后端：`/api/portfolio/add`、`/api/portfolio/update`
- 数据层：`portfolio.adjustment` 不再接受新的普通写入

### 验收重点
- 新增持仓时，即使请求里带 `adjustment`，也不应再写入 legacy adjustment
- 普通更新接口不应再允许 `field=adjustment`
- 历史导入脚本仍可在显式声明下保留老字段写入
