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

---

## 3. 页面怎么分

### 3.1 门户页

在：

- [/Users/kona/Desktop/kaka/kona_repo/web/src/views](/Users/kona/Desktop/kaka/kona_repo/web/src/views)
- [/Users/kona/Desktop/kaka/kona_repo/web/src/pages/portal](/Users/kona/Desktop/kaka/kona_repo/web/src/pages/portal)

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
  - 持仓卡片的小趋势线也已经接上真实历史数据
- [AppInvestPage.vue](/Users/kona/Desktop/kaka/kona_repo/web/src/pages/app/AppInvestPage.vue)
  - 投资页持仓卡片和首页共用同一套趋势线口径
  - 不再本地生成假 sparkline

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
- [analysis.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/stores/analysis.ts)

一句大白话：

`页面现在统一问 composables 拿状态，composables 只做组合入口；刷新链路走 refreshCoordinator，会话恢复和路由初始化走 sessionCoordinator，分析页自己的缓存和加载编排走 analysis store。`

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
- `AdminShell`
- `LegacyAppShell`
- `LegacyAdminShell`

一句话：

`layouts/ 是页面骨架，pages/ 是具体内容。`

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

### 10.1 旧 `shared/store.ts` 还留在仓库里

虽然页面已经迁走，但旧文件路径还在。

风险不是“它现在会直接生效”，而是：

`后面的人可能又把新逻辑塞回去。`

所以这轮已经把它收成极薄兼容壳，只保留旧导入路径，不再保留第二套状态实现。

### 10.2 还有历史兼容层

你现在还能看到：

- `LegacyAppShell`
- `LegacyAdminShell`
- `legacy.css`

说明 Web 端已经在工程化，但还没有完全摆脱历史包袱。

从现在开始，这层按下面规则处理：

- 只保现有页面稳定
- 不再接新状态入口
- 不再接新布局规范
- 不再接新样式体系

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
