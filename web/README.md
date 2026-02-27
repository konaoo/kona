# 咔咔记账 Web（Vue3 + Vite）

本目录是咔咔记账独立 Web 前端工程，包含三部分：

- 门户页：`/`（公开主页）
- 业务端：`/app/*`
- 管理端：`/admin/*`

后端 API 协议保持不变，统一走 Flask 的 `/api/*`。

---

## 1. 技术栈与目录

- 框架：Vue 3 + TypeScript + Vite
- 路由：Vue Router
- 截图：`html2canvas`（首页隐私遮罩截图导出）
- 鉴权：JWT + refresh token（`localStorage`）

目录结构：

```text
web/
├─ src/
│  ├─ layouts/
│  │  ├─ LegacyAppShell.vue       # 业务端壳层
│  │  └─ LegacyAdminShell.vue     # 管理端壳层
│  ├─ pages/
│  │  ├─ portal/PortalPage.vue    # 门户页
│  │  ├─ app/                     # 业务页（home/invest/analysis/news/profile）
│  │  └─ admin/                   # 管理页（overview/users/config/invites/data/apis/audit）
│  ├─ shared/
│  │  ├─ auth.ts                  # token 持久化
│  │  ├─ http.ts                  # API 请求与 refresh 续签
│  │  ├─ store.ts                 # 全局状态、市场口径、持仓计算
│  │  └─ format.ts                # 金额/币种/百分比格式化
│  ├─ styles/
│  │  ├─ tokens.css               # 全局设计 token
│  │  └─ legacy.css               # 业务/管理端主题与布局基线
│  ├─ router.ts
│  └─ main.ts
└─ package.json
```

---

## 2. 页面路由与业务映射

### 2.1 门户/业务/管理路由

- 门户：`/`
- 业务登录：`/app/login`
- 我的资产：`/app/home`
- 我的投资：`/app/invest`
- 资产分析：`/app/analysis`
- 市场分析：`/app/news`
- 设置：`/app/profile`
- 管理登录：`/admin/login`
- 管理页：`/admin/overview`、`/admin/users`、`/admin/config`、`/admin/invites`、`/admin/data`、`/admin/apis`、`/admin/audit`

### 2.2 你确认的映射关系

- 我的资产 = 首页
- 我的投资 = 投资
- 资产分析 = 分析
- 市场分析 = 快讯
- 设置 = 我的

---

## 3. 鉴权与会话（Web）

### 3.1 本地存储键

- `kona_web_access_token`
- `kona_web_refresh_token`
- `kona_web_user`

### 3.2 鉴权流程

1. 登录成功后写入 token 与用户信息。
2. 页面刷新时通过 `store.bootstrap()` 调 `/api/auth/me` 恢复会话。
3. 401 时自动调用 `/api/auth/refresh`，刷新成功后重试原请求。
4. refresh 失败则清空本地会话并回到登录页。

---

## 4. 市场口径与收益计算

### 4.1 市场状态来源

- Web 通过 `/api/market/status` 获取 A/HK/US/Fund 开休市状态。
- 当前前端口径（`src/shared/store.ts`）：
  - `dayPnl = (currentPrice - yclose) * qty`，仅当该市场开市且 `yclose > 0` 才计算。
  - 休市时 `dayPnl = 0`、`dayPnlRate = 0`。

### 4.2 币种展示

- 持有金额与盈亏按资产所属市场币种展示（CNY/HKD/USD）。
- 累计盈亏继续使用后端持仓字段与前端计算口径，不改 API 字段语义。

---

## 5. 投资页（`/app/invest`）本轮完整修改细节

文件：`src/pages/app/AppInvestPage.vue`

### 5.1 表格结构

- 7 列统一等宽（`100% / 7`）：
  - 资产名称
  - 持有数量
  - 成本/现价
  - 持有金额
  - 当日盈亏
  - 累计盈亏
  - 操作
- 增加轻量竖向分隔线，提升列边界可读性。

### 5.2 对齐规则（当前）

- 资产名称列：左对齐（表头 + 内容）。
- 当日盈亏、累计盈亏：右对齐（表头 + 内容）。
- 其余列：维持当前布局样式。

### 5.3 字体字阶规范（当前页内 token）

- 表头：12
- 主值（资产名/金额/盈亏金额）：16
- 次值（代码/成本现价/收益率）：13
- 状态提示（休市）：11
- 行高：主行 `1.25`，次行 `1.2`

### 5.4 交互与校验

- 资产名超过 10 个中文字符按 `...` 截断。
- 操作列为单按钮下拉菜单（买入/卖出/调整/删除）。
- 数量提交强校验为正整数（新增/买入/卖出/调整）。
- 休市且当日为 0 时显示弱提示 `休市`（仅说明，不影响计算）。

---

## 6. 门户页与管理端改造说明

### 6.1 门户页（`/`）

- 已改为单屏 Hero 风格入口页。
- 从 `/api/web/config` 读取：
  - `portal_title`
  - `apk_download_url`
- 当 APK 链接为空时按钮置灰并显示“APK 暂未提供”。
- 后端默认回退逻辑：
  - 若未设置 `WEB_APK_DOWNLOAD_URL` 且本地存在 `kona_tool/static/downloads/kaka-latest-release.apk`，
    门户自动使用 `/download/apk` 作为下载链接。

APK 发布最小流程（与你当前结构一致）：

```bash
mkdir -p /Users/kona/Desktop/kaka/kona_repo/kona_tool/static/downloads
cp /Users/kona/Desktop/kaka/apk_exports/kaka-latest-release.apk \
  /Users/kona/Desktop/kaka/kona_repo/kona_tool/static/downloads/kaka-latest-release.apk
```

验证：

```bash
curl -I http://127.0.0.1:52345/download/apk
curl http://127.0.0.1:52345/api/web/config
```

### 6.2 管理端（`/admin/*`）

- 已迁移至 Vue 页面并使用 `LegacyAdminShell`。
- 功能与后端 `/api/admin/*` 保持一致，主要做 UI 与交互重构。

---

## 7. 本地开发与构建

```bash
cd /Users/kona/Desktop/kaka/kona_repo/web
npm ci
npm run dev
```

构建：

```bash
cd /Users/kona/Desktop/kaka/kona_repo/web
npm run build
```

预览：

```bash
cd /Users/kona/Desktop/kaka/kona_repo/web
npm run preview
```

---

## 8. 部署到 Flask 静态目录

Web 打包产物由后端托管：`kona_tool/static/web`

```bash
cd /Users/kona/Desktop/kaka/kona_repo/web
npm run build

mkdir -p /Users/kona/Desktop/kaka/kona_repo/kona_tool/static/web
rsync -a --delete \
  /Users/kona/Desktop/kaka/kona_repo/web/dist/ \
  /Users/kona/Desktop/kaka/kona_repo/kona_tool/static/web/
```

若访问根路径返回 `{"error":"Web bundle not found"}`，说明静态目录没有最新构建产物，按上面同步一次即可。

---

## 9. CI/CD 说明（与你当前流程一致）

- Web 门禁：`npm run build`。
- Flutter 的 `build apk --debug` 已做路径条件触发：
  - 非 `flutter/android/**` 改动默认跳过 APK smoke。
  - 改动 Android 工程时才执行。

---

## 10. 验收清单（Web）

### 10.1 路由 smoke

- `/`
- `/app/login`
- `/app/home`
- `/app/invest`
- `/app/analysis`
- `/app/news`
- `/app/profile`
- `/admin/login`
- `/admin/overview`

### 10.2 投资页专项

- 列宽等分、边界清晰。
- 资产名称左对齐。
- 当日盈亏/累计盈亏右对齐。
- 资产名过长截断。
- 操作菜单可用。
- 休市提示显示正确。

### 10.3 市场口径

- 休市时 day pnl 显示 0。
- 开市时 day pnl 按 `current - yclose` 计算。

---

## 11. 常见问题

### Q1：Web 登录页正常，但 `/app/*` 打不开

优先检查 token 是否写入以下键：

- `kona_web_access_token`
- `kona_web_refresh_token`

并确认 `/api/auth/me` 返回 200。

### Q2：页面样式更新后看起来没变

浏览器强刷缓存：`Cmd+Shift+R`。

### Q3：根路径返回 `Web bundle not found`

说明后端静态目录缺构建包，重新执行第 8 节同步命令。

---

## 12. 变更归档建议

后续每次 UI/口径调整，请在本 README 追加一条“变更记录（日期 + 文件 + 验收命令）”，避免口头同步造成偏差。
