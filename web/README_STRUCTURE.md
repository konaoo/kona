# web 目录说明

## 1. 目录用途

`web/` 是咔咔记账网页端工程目录。

当前它同时承载 3 类页面：

- 门户页
- 业务端
- 管理后台

也就是说，这不是单一官网目录，而是一个多角色 Web 前端工程。

---

## 2. 当前核心子目录

```text
web/
├─ app/                   # 业务端构建入口（index.html）
├─ admin/                 # 管理端构建入口（index.html）
├─ src/                    # Web 主源码
├─ public/                 # 公共静态资源
├─ tests/                  # 测试
├─ screenshots/            # 页面截图/验收素材
├─ dist/                   # 构建产物（app / admin 两份）
├─ node_modules/           # 当前依赖安装目录
├─ node_modules.old.*      # 历史依赖备份目录
└─ package.json            # 依赖和脚本入口
```

其中 `src/` 当前核心结构包括：

- `pages/`
- `layouts/`
- `shared/`
- `stores/`
- `components/`
- `styles/`
- `types/`

已清理的历史内容：

- `src/examples/ComponentExample.vue`：无入口引用的组件示例页，已移出源码目录
- `src/pages/portal/PortalPage.vue`：未接入路由的旧门户页，已移出源码目录
- `src/pages/app/AppProfilePage.vue`：旧个人资料页，路由已重定向到 `/app/me`，已移出源码目录
- `src/pages/admin/AdminDataPage.vue`：旧数据管理页，路由已重定向到 `/admin/overview`，已移出源码目录
- `src/layouts/LegacyAppShell.vue` / `src/layouts/LegacyAdminShell.vue`：旧页面壳，已无真实页面引用，已移出源码目录
- `src/layouts/AdminShell.vue`：旧管理壳，已无真实页面引用，已移出源码目录
- `src/components/admin/ui/*`：旧管理壳专用组件，已无真实页面引用，已移出源码目录
- `src/styles/legacy.css`：旧页面壳样式，入口已不再加载，已移出源码目录
- `src/components/base` / `src/components/business` 中未被真实页面引用的组件：已移出源码目录
- `src/types/ui.ts`：旧组件库配套类型，组件已归档且无真实引用，已移出源码目录
- `src/types/api.ts` / `portfolio.ts` / `quote.ts` / `user.ts`：旧手写类型层，真实 store 已有自己的边界类型，已移出源码目录
- `src/styles/design-test.css`：设计系统测试样式，无入口引用，已移出源码目录
- `src/shared/store.ts`：旧状态兼容入口，页面已统一走 `stores/composables.ts`，已移出源码目录
- `tests/unit/legacyStoreShim.test.ts`：旧状态兼容入口测试，随兼容入口一起归档

---

## 3. 应该放什么

这个目录应该放：

- Vue Web 源码
- Web 端样式
- Web 端测试
- Web 端构建配置
- Web 静态资源

---

## 4. 不应该放什么

这个目录不应该长期承载：

- 无说明的旧依赖备份
- 临时试验页面
- 与 Web 无关的后端脚本
- 无整理的手工构建垃圾

另外这些目录要明确看成“生成物或依赖物”，不是主结构：

- `dist/`
- `node_modules/`
- `node_modules.old.*`

其中 `node_modules.old.20260301_093304/` 这种目录，已经明显属于历史遗留，需要后续专门清理。

---

## 5. 当前逻辑

`web/` 当前是一个“多入口业务前端”。

它承载的不是单页官网，而是：

- 公开门户
- 用户业务页面
- 管理台页面

当前 `src/` 里的分工可以先理解成：

- `pages/`：具体页面
- `layouts/`：页面壳层
- `shared/`：共享逻辑与格式化
- `stores/`：状态管理
- `components/`：复用组件
- `styles/`：样式和设计 token

组件目录现在只保留真实页面会加载的组件；未接入页面的旧组件库文件已经归档，避免 barrel 导出把无用组件重新带回构建图。

从业务角度看，它和 Flutter 端共享很多同一套后端口径，但表现层不同。

所以这个目录后续治理的核心不是“把页面拆更碎”，而是：

- 把共享规则和页面逻辑分开
- 把业务端和管理端边界拉清
- 清理历史依赖和构建垃圾

---

## 6. 关键规则

### 6.1 这是一个多角色前端

必须明确：

- 门户页不是管理后台
- 管理后台不是业务端
- 这三类页面虽然共用一个工程，但职责不同

后续目录治理时，要防止三者继续互相污染。

### 6.2 当前构建逻辑

Web 构建入口在本目录。

常用命令：

```bash
cd /Users/kona/Desktop/kaka/kona_repo/web
npm run dev
npm run build
```

构建产物默认进入：

- `dist/app/`
- `dist/admin/`

### 6.3 当前最大结构风险

这个目录当前最明显的风险有两个：

1. `node_modules.old.*` 这类历史备份目录混在工程里
2. `dist/` 这类生成物容易被误当作源码结构的一部分

当前已处理：

- `dist/` 和 `test-results/` 按生成物清理
- 无引用示例页和旧门户页已移到项目外归档目录

如果不在认知上切开，后面 Web 目录会越来越像仓库垃圾场。

### 6.4 包体积规则

Web 端现在按页面做路由级懒加载。

后续新增页面或低频功能时，默认遵守两条规则：

- 路由页面不要在路由文件顶部静态导入，使用 `component: () => import(...)`
- 重依赖不要挂在全局壳层或首屏页面里，优先在用户触发功能时动态导入

当前已按需加载的重依赖包括：

- `xlsx`：个人中心导出 Excel 时加载
- `html2canvas`：触发截图保存时加载

---

## 7. 当前结论

`web/` 是网页端主应用工程，而且是多角色混合工程。

后续治理重点应该是：

1. 梳理 `src/` 内部职责
2. 拆清门户 / 业务端 / 管理端边界
3. 清理依赖和构建历史垃圾
4. 把共享业务口径单独沉淀出来

### 7.2 Legacy 归档规则

旧 App / Admin 页面壳已经没有真实页面引用，已移出源码目录：

- `src/layouts/LegacyAppShell.vue`
- `src/layouts/LegacyAdminShell.vue`
- `src/layouts/AdminShell.vue`
- `src/components/admin/ui/*`
- `src/styles/legacy.css`

当前 `main_app.ts` 和 `main_admin.ts` 只加载正式设计系统样式，不再加载 legacy 样式。

### 7.3 测试目录规则

`web/tests/` 现在默认分成：

- `unit/`：Vitest 单元测试
- `e2e/`：Playwright 正式验收
- `debug/`：临时排障脚本

正式门禁默认只认：

- `unit/`
- `e2e/`

### 7.1 补充阅读

- [web/src/README_页面与状态地图.md](/Users/kona/Desktop/kaka/kona_repo/web/src/README_页面与状态地图.md)
- [web/tests/README.md](/Users/kona/Desktop/kaka/kona_repo/web/tests/README.md)
