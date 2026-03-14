# Flutter 页面与状态地图

这份文档专门讲 Flutter 客户端的 3 件事：

1. 页面怎么分
2. 状态由谁管
3. 数据是怎么流动的

它不是给 Flutter 工程师炫技用的，而是给你这种要掌控全局的人看。

---

## 1. 先说结论

Flutter 客户端当前的核心结构其实很清楚：

- `main.dart` 负责启动和页面骨架
- `AppState` 负责绝大多数全局状态
- `pages/` 放页面
- `services/` 负责接口、缓存、生物识别、密钥存储
- `models/` 放数据模型
- `widgets/` 放可复用组件

一句话：

`Flutter 端现在本质上是“单一全局状态中心 + 多页面壳子”的结构。`

---

## 2. 目录怎么理解

```text
flutter/lib/
├─ main.dart              # App 入口与总导航骨架
├─ config/                # 接口地址、主题
├─ models/                # 数据模型
├─ pages/                 # 页面
├─ providers/             # 全局状态（当前核心是 AppState，总入口下已开始拆子状态）
├─ services/              # API、缓存、生物识别、存储
├─ utils/                 # 工具函数
└─ widgets/               # 可复用组件
```

---

## 3. 页面结构

主要页面都在：

- [/Users/kona/Desktop/kaka/kona_repo/flutter/lib/pages](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/pages)

当前主页面有这些：

- [login_page.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/pages/login_page.dart)
  - 登录页

- [home_page.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/pages/home_page.dart)
  - 首页 / 资产总览

- [invest_page.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/pages/invest_page.dart)
  - 投资页 / 持仓、卡片、交易弹窗

- [analysis_page.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/pages/analysis_page.dart)
  - 分析页 / 收益、排行、日历

- [news_page.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/pages/news_page.dart)
  - 快讯页

- [profile_page.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/pages/profile_page.dart)
  - 我的 / 设置

- [asset_detail_page.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/pages/asset_detail_page.dart)
  - 单个资产详情

其他页面多是辅助页，比如：

- 关于页
- WebView 页
- 邀请码获取页

---

## 4. 真正的状态中心是谁

当前 Flutter 端最核心的状态文件是：

- [app_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_state.dart)

但这轮已经先拆出两块独立模块：

- [app_auth_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_auth_state.dart)
- [app_assets_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_assets_state.dart)
- [app_market_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_market_state.dart)
- [app_overview_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_overview_state.dart)
- [app_refresh_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_refresh_state.dart)
- [app_sync_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_sync_state.dart)
- [app_trade_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_trade_state.dart)
- [app_preferences_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_preferences_state.dart)
- [app_security_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_security_state.dart)

它负责的事情很多，包括：

- 登录状态
- Token / Refresh Token
- 当前用户信息
- 生物识别开关
- 资产总额
- 持仓列表
- 价格缓存
- 汇率
- 市场开闭市状态
- 历史概览
- 主题
- 金额隐藏
- 启动缓存恢复
- 增量同步

一句大白话：

`AppState 现在还是 Flutter 客户端的大总管，但认证、行情/市场、概览、刷新编排、缓存/同步、交易辅助、UI 偏好和安全状态已经先切出第一层边界。`

补充当前这一步：

- 缓存作用域
- cache envelope 读写
- sync version 读写
- 行情刷新策略
- “静态数据是否可以跳过同步”的判断

这些现在已经收口到 [app_sync_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_sync_state.dart)，`AppState` 在这块主要保留编排，不再继续夹一层假中转 helper。

刷新编排这一步也继续往前收了一层：

- 冷启动缓存恢复
- 首页全量刷新
- 增量同步
- 行情后台补刷
- 汇率刷新

这些现在已经收口到 [app_refresh_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_refresh_state.dart)，`AppState` 在这块主要保留原来的入口名和对子状态的组装，不再继续自己兼管整条刷新细节。

资产 / 持仓这一步也继续往前收了一层：

- 资产列表
- 持仓列表
- 快照恢复
- 乐观增删改

这些现在已经收口到 [app_assets_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_assets_state.dart)，`AppState` 在这块主要保留交易接口调用、金额换算、总额重算和刷新编排。

概览 / 历史这一步也继续往前收了一层：

- 月变动 / 年变动 / 历史峰值
- baseline 是否存在
- overview milestone 覆盖
- 历史统计计算

这些现在已经收口到 [app_overview_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_overview_state.dart)，`AppState` 在这块主要保留首页刷新、缓存恢复和分析接口编排。

交易辅助这一层也继续往前收了一点：

- 跨币种金额换算
- undo 信息提取
- 老接口交易兜底

这些现在已经收口到 [app_trade_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_trade_state.dart)，`AppState` 在这块主要保留买卖入口和刷新编排。

所以 Flutter 端后续如果要继续工程化，第一关注点一定也是这里。

---

## 5. App 启动流程

入口在：

- [main.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/main.dart)

启动链路大致是：

1. `main()` 启动 Flutter
2. `MyApp` 用 `ChangeNotifierProvider` 注入 `AppState`
3. `AuthWrapper` 根据登录状态决定显示：
   - 启动页
   - 登录页
   - 主应用
4. `hydrateFromCache()` 先恢复本地缓存
5. 登录成功后 `refreshAll()` 再刷新远端数据

这就是为什么当前客户端体验上更像：

`先秒开本地缓存，再后台刷新`

而不是每次冷启动都白屏等接口。

---

## 6. 数据流怎么走

当前最重要的数据流是这条：

### 6.1 登录态

页面：

- 登录页

调用：

- [api_service.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/services/api_service.dart)

持久化：

- [secure_storage_service.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/services/secure_storage_service.dart)

状态归口：

- [app_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_state.dart)

### 6.2 资产与持仓

后端接口拉回来后，主要进入：

- `AppState._portfolio`
- 资产列表
- 汇率
- 概览数据

页面再通过 `context.watch<AppState>()` 渲染。

### 6.3 价格数据

当前价格和价格快照主要归到：

- `AppState._prices`
- `AppState._priceSnapshots`

页面优先通过：

- `resolvePriceInfo(...)`
- `resolvePriceInfoByCode(...)`

来拿价格。

这也是为什么后来价格回退链、净值待更新、休市冻结这些逻辑，基本都集中在 `AppState + invest_page.dart`。

### 6.4 本地缓存

缓存服务在：

- [cache_service.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/services/cache_service.dart)

它主要帮客户端做到：

- 冷启动快速展示
- 弱网时不至于全白
- 行情失败时尽量保留上次有效值

---

## 7. 哪几个文件最关键

如果你只想抓住 Flutter 端最关键的 5 个文件，先看这些：

1. [main.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/main.dart)
   - App 怎么启动

2. [app_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_state.dart)
   - 全局状态怎么管

3. [api_service.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/services/api_service.dart)
   - 客户端怎么调用后端

4. [invest_page.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/pages/invest_page.dart)
   - 投资页口径、成本、盈亏逻辑

5. [home_page.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/pages/home_page.dart)
   - 首页大卡片和资产总览逻辑

---

## 8. 当前结构的优点

当前 Flutter 结构有几个明显优点：

- 页面划分已经比较清楚
- 服务层和页面层至少分开了
- 大多数状态集中在一个地方，查问题比较快
- 缓存和刷新逻辑已经有统一入口

---

## 9. 当前结构的风险点

### 9.1 `AppState` 太大

这是最明显的问题。

它现在既像：

- 登录状态中心
- 资产状态中心
- 行情状态中心
- 主题状态中心

所以后面如果继续涨，会越来越重。

### 9.2 页面里仍然夹着不少口径逻辑

比如：

- [invest_page.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/pages/invest_page.dart)

现在不只是页面，还包含了不少：

- 成本
- 盈亏
- 汇率折算
- 待净值更新

这种逻辑以后如果继续变复杂，最好逐步往更明确的计算层收。

### 9.3 还缺一层更清楚的“页面状态分层”

现在很多东西都直接问 `AppState`，开发速度快，但规模继续涨以后会变得吃力。

不过这件事现在不用急着大拆。

---

## 10. 一句结论

Flutter 端现在已经不是乱堆页面了。

它的主骨架已经很明确：

`main.dart + AppState + pages + services`

当前最该做的不是重写，而是：

- 先把认知地图立住
- 后面再慢慢收 `AppState`
- 再把复杂口径逻辑从页面中剥出来
