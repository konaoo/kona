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

- [router.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/router.ts)
- [stores/composables.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/stores/composables.ts)

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

---

## 4. 路由怎么走

路由入口在：

- [router.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/router.ts)

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

- `store.bootstrap()`

然后判断：

- 是否已登录
- 是否需要管理员权限
- 是否该跳回登录页

所以 `router.ts` 不只是跳页面，它也是登录恢复和权限控制入口。

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

一句大白话：

`页面现在统一问 composables 拿状态，composables 再去找各个专业 store。`

---

## 6. 数据流怎么走

### 6.1 登录态

主要相关文件：

- [shared/auth.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/shared/auth.ts)
- [auth.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/stores/auth.ts)

### 6.2 后端请求

统一入口：

- [shared/http.ts](/Users/kona/Desktop/kaka/kona_repo/web/src/shared/http.ts)

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

虽然页面已经迁走，但旧文件还在。

风险不是“它现在会直接生效”，而是：

`后面的人可能又把新逻辑塞回去。`

### 10.2 还有历史兼容层

你现在还能看到：

- `LegacyAppShell`
- `LegacyAdminShell`
- `legacy.css`

说明 Web 端已经在工程化，但还没有完全摆脱历史包袱。

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
