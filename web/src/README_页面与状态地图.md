# Web 页面与状态地图

这份文档专门讲 Web 端的 3 件事：

1. 页面怎么分
2. 路由怎么走
3. 页面现在该从哪里拿状态

---

## 1. 先说结论

Web 端现在可以理解成三层：

1. 路由层
2. 状态层
3. 页面层

当前最关键的两个入口是：

- 业务端路由：[router.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/router.ts)
- 管理端路由：[router_admin.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/router_admin.ts)
- 状态统一入口：[stores/composables.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/stores/composables.ts)
- 刷新协调层：[stores/refreshCoordinator.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/stores/refreshCoordinator.ts)
- 会话协调层：[stores/sessionCoordinator.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/stores/sessionCoordinator.ts)
- 首页读状态层：[stores/home.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/stores/home.ts)
- 分析页状态层：[stores/analysis.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/stores/analysis.ts)

一句话：

`Web 页面现在已经统一走新 stores 组合入口，不再直接吃旧 shared/store.ts。`

---

## 2. 目录怎么理解

```text
web/src/
├─ App.vue
├─ main.ts
├─ router.ts
├─ components/      # 组件
├─ layouts/         # 页面外壳
├─ pages/           # 具体页面
├─ shared/          # HTTP、认证、本地工具、历史遗留
├─ stores/          # 新状态中心
├─ styles/          # 样式
├─ types/           # 类型定义
└─ views/           # 入口视图
```

说明：未接入路由的示例页和旧门户页已经移出源码目录，后续页面地图只记录真实入口和仍在维护的页面。

---

## 3. 页面怎么分

### 3.1 门户页

在：

- [/Users/kona/Desktop/kaka/kona_repo/web/src/views](/Users/kona/Desktop/kaka/kona_repo/web/src/views)

代表文件：

- [Landing.vue](/Users/kona/Desktop/kaka/kona_repo/web/src/views/Landing.vue)

### 3.2 浏览器版 App 页面

在：

- [/Users/kona/Desktop/kaka/kona_repo/web/src/pages/app](/Users/kona/Desktop/kaka/kona_repo/web/src/pages/app)

主要包括：

- 登录
- 首页
- 投资
- 分析
- 快讯
- 我的
- 资产详情

其中这轮要特别记住两页：

- [AppHomePage.vue](/Users/kona/Desktop/kaka/kona_repo/web/src/pages/app/AppHomePage.vue)
  - 首页总资产大图现在走真实 `daily_snapshots`
  - 首页的资产列表、市场卡片、历史快照和趋势线加载，已经下沉到 `home store`
- [AppInvestPage.vue](/Users/kona/Desktop/kaka/kona_repo/web/src/pages/app/AppInvestPage.vue)
  - 投资页持仓卡片和首页共用同一套趋势线口径
  - 不再本地生成假 sparkline
  - 投资总览卡和市场分组卡已拆到 `components/business/InvestSummaryCards.vue`、`components/business/InvestMarketGrid.vue`
  - 持仓明细展示已拆到 `components/business/InvestHoldingList.vue`
  - 账本选择器已拆到 `components/business/InvestLedgerSelector.vue`
  - 持仓行加工、筛选和排序规则已收敛到 `stores/investHoldingRows.ts`
  - 投资页刷新编排已拆到 `pages/app/useInvestReadState.ts`
  - 页面仍保留数据编排和交易弹窗入口，展示组件不直接访问 store

### 3.3 管理后台页面

在：

- [/Users/kona/Desktop/kaka/kona_repo/web/src/pages/admin](/Users/kona/Desktop/kaka/kona_repo/web/src/pages/admin)

主要包括：

- 管理员登录
- 总览
- 用户
- 邀请码
- 接口管理
- 配置管理

其中：

- [AdminInvitesPage.vue](/Users/kona/Desktop/kaka/kona_repo/web/src/pages/admin/AdminInvitesPage.vue)
  - 点击邀请码支持复制
  - 优先走系统剪贴板，失败时会回退到传统复制兜底

---

## 4. 路由怎么走

路由入口在：

- 业务端：[router.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/router.ts)
- 管理端：[router_admin.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/router_admin.ts)

当前主要分三段：

### 4.1 门户

- `/`

### 4.2 App

- `/app/login`
- `/app/home`
- `/app/invest`
- `/app/analysis`
- `/app/news`
- `/app/me`
- `/app/asset/:code`

### 4.3 Admin

- `/admin/login`
- `/admin/overview`
- `/admin/users`
- `/admin/invites`
- `/admin/apis`
- `/admin/config`

### 4.4 路由守卫

进入页面前，路由会先做：

- `sessionCoordinatorStore.bootstrap()`

然后判断：

- 业务端是否已登录（未登录跳 `/app/login`）
- 管理端是否已登录 + 是否管理员（未登录或无权限跳 `/admin/login`）

所以路由文件不只是跳页面，它也是登录恢复和权限控制入口；这条链路现在单独走 `sessionCoordinator`，不再让路由守卫直接依赖 `composables`。

### 4.5 页面加载规则

业务端和管理端页面组件默认使用路由级懒加载：

- 页面组件不要在 `router.ts` / `router_admin.ts` 顶部静态导入
- 新增路由时优先使用 `component: () => import(...)`
- `xlsx`、`html2canvas` 这类重依赖只在用户触发对应功能时动态导入

这样可以避免“个人中心导出 Excel”“页面截图”这类低频能力被打进所有页面的首屏包。

---

## 5. 页面现在从哪里拿状态

页面统一入口是：

- [stores/composables.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/stores/composables.ts)

它背后组合的是：

- [auth.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/stores/auth.ts)
- [portfolio.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/stores/portfolio.ts)
- [quote.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/stores/quote.ts)
- [market.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/stores/market.ts)
- [sync.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/stores/sync.ts)
- [refreshCoordinator.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/stores/refreshCoordinator.ts)
- [sessionCoordinator.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/stores/sessionCoordinator.ts)
- [home.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/stores/home.ts)
- [analysis.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/stores/analysis.ts)

一句大白话：

`页面现在统一问 composables 拿状态，composables 只做组合入口；刷新链路走 refreshCoordinator，会话恢复和路由初始化走 sessionCoordinator，首页自己的读侧状态走 home store，分析页自己的缓存和加载编排走 analysis store。`

---

## 6. 数据流怎么走

### 6.1 登录态

主要相关文件：

- [shared/auth.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/shared/auth.ts)
- [auth.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/stores/auth.ts)

### 6.2 后端请求

统一入口：

- [shared/http.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/shared/http.ts)

这轮还新增了一个趋势线共享模块：

- [shared/assetTrend.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/shared/assetTrend.ts)
  - 负责把后端返回的真实历史点位转成前端小折线 SVG path
  - 首页和投资页共用，不要再各自生成一套假走势

### 6.3 持仓、价格、汇率

主要由这些 store 管：

- [portfolio.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/stores/portfolio.ts)
- [quote.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/stores/quote.ts)
- [market.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/stores/market.ts)

### 6.4 缓存与增量同步

主要在：

- [sync.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/stores/sync.ts)

---

## 7. 布局层怎么理解

布局文件在：

- [/Users/kona/Desktop/kaka/kona_repo/web/src/layouts](/Users/kona/Desktop/kaka/kona_repo/web/src/layouts)

主要是页面外壳，比如：

- `AppShell`

一句话：

`layouts/ 是页面骨架，pages/ 是具体内容。`

组件目录现在只保留真实页面引用的组件：

- `base/AssetLogo.vue`
- `base/Modal.vue`
- `business/InvestTradeModal.vue`
- `business/LedgerManageModal.vue`
- `admin/*`
- `landing/*`

未被页面引用、只通过 barrel 文件导出的旧基础组件和业务展示组件已经移出源码目录。

对应的旧组件类型文件 `types/ui.ts` 也已经归档；旧手写 `api/portfolio/quote/user` 类型层同样已归档。新的页面类型优先放在页面附近或 `stores/types.ts` 这类真实业务边界里。

基金识别、净值日期、基金 stale 判断这类跨首页/投资页/资产详情页的展示口径统一放在 `shared/assetDisplay.ts`，不要再在页面内复制一套。

---

## 8. 哪几个文件最关键

如果你只想先抓住 Web 最关键的 5 个文件，先看这些：

1. [main.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/main.ts)
   - Web 入口

2. [router.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/router.ts)
   - 路由与权限守卫

3. [stores/composables.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/stores/composables.ts)
   - 页面统一状态入口

4. [shared/http.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/shared/http.ts)
   - 后端请求总入口

5. [AppInvestPage.vue](/Users/kona/Desktop/kaka/kona_repo/web/src/pages/app/AppInvestPage.vue)
   - 浏览器版 App 的核心页面之一

---

## 9. 当前结构的优点

现在 Web 端已经有几个明显优点：

- 页面类型分清了：门户 / App / Admin
- 页面主入口统一了
- 路由入口集中
- 状态职责开始分层
- 缓存和增量同步有专门位置

---

## 10. 当前结构的风险点

### 10.1 旧 `shared/store.ts` 已归档

页面、布局和路由已经统一走：

- [stores/composables.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/stores/composables.ts)

旧的 `shared/store.ts` 兼容入口和对应 `legacyStoreShim` 测试已经移出源码目录。后续不要再新增 `shared/store` 这类第二状态入口。

### 10.2 历史兼容层已收窄

旧页面壳和旧页面已经移出源码目录：

- `AppProfilePage`
- `AdminDataPage`
- `LegacyAppShell`
- `LegacyAdminShell`
- `AdminShell`
- `src/components/admin/ui/*`
- `legacy.css`

当前 `main_app.ts` / `main_admin.ts` 已不再加载旧样式层，正式页面样式由 `tokens.css`、`base.css`、`mixins.css`、`animations.css`、`shared.css` 和页面自身样式承担。

---

## 11. 一句结论

Web 端现在已经不是“一个 Vue 项目”这么简单。

它同时承载：

- 门户页
- 浏览器版 App
- 管理后台

而页面真正的主控制台，现在是：

- `router.ts`
- `stores/composables.ts`
