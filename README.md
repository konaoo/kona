# 咔咔记账 (Kaka Portfolio) 🚀

[![Flutter](https://img.shields.io/badge/Flutter-3.41-blue.svg)](https://flutter.dev)
[![Python](https://img.shields.io/badge/Python-3.11-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**咔咔记账** 是一款专为个人投资者打造的资产与投资管理系统。不同于传统的流水账工具，它深度聚焦于“资产配置”、“实时盈亏”与“历史收益分析”，帮助用户实时掌握全币种、跨市场的投资表现。

---

## 🌟 核心理念 (Core Value)

在碎片化的投资时代，通过“日常可用 + 可持续运维”的架构，统一管理资产快照、行情同步与后台运营，解决投资记账“难对齐、难分析、难维护”的痛点。

---

## ✨ 核心特性

### 📱 多端覆盖
- **客户端**：基于 Flutter 驱动，支持 Android / iOS / macOS，极速响应，极致动效。
- **Web 端**：Vue3 + Vite 构建的现代化业务门户与管理后台。

### 📊 深度投资分析
- **盈亏日历**：按日记录资产波动，红绿涨跌一目了然。
- **收益详情**：支持“摊薄成本”算法，真实还原卖出后的剩余持仓成本。
- **排行系统**：多币种自动汇率折算，根据累计盈亏进行动态排名。
- **PnL 进度条**：独家设计的可视化持仓表现条，精准展示盈亏平衡点。

### ⚡ 极速行情引擎
- **行情预取**：后端行情批量异步抓取，API 响应时间从数秒优化至 <50ms。
- **全市场支持**：A股、港股、美股、场内/场外基金全覆盖，支持 B 股（USD/HKD）自动汇率识别。

### 🛡 安全与体验
- **生物识别**：支持指纹/面部识别解锁，保护资产隐私。
- **1:1 原型对齐**：全量复刻 HTML 视觉原型，极致的暗黑模式与微光 UI 体验。
- **动态运营**：版本更新、用户群公告等核心文案支持后端精细化动态配置。

---

## 🏗 技术架构

### 栈概览
- **前端 (Frontend)**: Flutter 3.41, Vue3, Vite, TailwindCSS (Web).
- **后端 (Backend)**: Python Flask, Gunicorn, Flask-Limiter.
- **数据 (Data)**: SQLite (核心存储), Redis (限流/任务).
- **运维 (Ops)**: Caddy (反向代理), systemd (服务守护), GitHub Actions (自动化部署), 腾讯云 Lighhouse (广州).

### 仓库结构
```text
kona_repo/
├─ flutter/          # Flutter 移动端/桌面端源码
├─ web/              # Vue3 Web 端源码（含业务端与管理端）
├─ kona_tool/        # Python Flask 后端与核心计算模块
├─ docs/             # 深度架构、运维、交接文档 (30+ .md files)
├─ scripts/          # 仓库级工具脚本
├─ .github/          # GitHub Actions / CI/CD
└─ CHANGELOG.md      # 项目演进的唯一标准记录
```

### 仓库定位

`kona_repo/` 是咔咔记账项目的主仓库。

这里承载的是项目核心代码与工程资产，当前本质上已经是一个多端 monorepo，里面同时包含：

- 客户端
- 网页端
- 后端
- 文档
- 脚本
- CI/CD

### 仓库边界

这个仓库应该长期保留：

- 项目源码
- 工程配置
- 文档
- 测试
- 构建与部署配置

这个仓库不应该长期积累：

- 无说明的历史垃圾目录
- 随手导出的临时文件
- 无命名规则的构建产物
- 与项目无关的个人备份

一句话：

`kona_repo 应以 flutter / web / kona_tool 为核心，外加少量仓库级支撑目录，而不是继续什么都往里塞。`

---

## 🚀 快速开始

### 后端运行
```bash
cd kona_tool
pip3 install -r requirements.txt
export JWT_SECRET="your_secret_key"
python3 app.py # 本地监听 52345
```

### Flutter 运行
```bash
cd flutter
flutter pub get
flutter run
```

### Web 运行
```bash
cd web
npm install && npm run dev
```

---

## 🛠 运维与部署

### 生产入口
- **IP 直连**: `http://114.132.238.12/`
- **业务端**: `/app/login`
- **管理端**: `/admin/login`

### 常用运维操作
详细记录于 [`docs/运维手册.md`](./docs/运维手册.md):
- **快照补数**: 每 2 小时自动抓取行情快照。若日历无数据，检查 `snapshot.py` 任务。
- **APK 发布**: 
  ```bash
  cd flutter && flutter build apk --release && scp ...
  ```
  下载地址：`http://114.132.238.12/download/apk`

### 发布规则

- `CHANGELOG.md` 记录的是项目变更，不是客户端真实版本号
- Flutter 客户端真实版本只认 [flutter/pubspec.yaml](./flutter/pubspec.yaml)
- App 内“检查更新”提示的新版本，只认后端 `/api/app/version`
- 重要改动要写版本记录，但不是每次改动都要升 Flutter 版本号
- 只有准备发布新的 Flutter 客户端安装包时，才升级 `flutter/pubspec.yaml` 里的版本号
- 只有准备让 App 内“检查更新”提示新版本时，才同步更新 `CLIENT_APP_VERSION`、`CLIENT_APP_BUILD_NUMBER`、下载链接和更新文案
- 如果只是后端修复、Web 修复、数据修复、目录整理，通常不需要升客户端版本号

### AI 工作规则

- 默认所有交流、文档、目录说明、版本记录、代码注释都使用中文
- 默认写大白话，不要堆英文标题和技术黑话
- 新逻辑优先补到现有主结构里，不要另起第二套入口
- 遗留文件如果已经不是主入口，默认不要继续往里面加新职责
- Web 页面状态统一优先走 [stores/composables.ts](./web/src/stores/composables.ts)
- Flutter 当前全局状态主入口是 [app_state.dart](./flutter/lib/providers/app_state.dart)

如果是新 AI 接手这个项目，正式开工前先读：

- [AI 接手规则](../AGENTS.md)
- [工作区骨架说明](../项目结构.md)
- [版本记录规范](./版本记录规范.md)

---

## 📖 文档导航

- [环境准备与迁移说明](./docs/腾讯云迁移说明.md)
- [价格源 / 基金净值 / 快照与盈亏口径交接（2026-03）](./docs/价格源与快照盈亏口径说明.md)
- [资产收益计算逻辑](./docs/资产收益计算逻辑.md)
- [接口与页面对照图](./docs/接口与页面对照图.md)
- [状态管理职责图](./docs/状态管理职责图.md)
- [线上运维与发布操作图](./docs/线上运维与发布操作图.md)
- [资产同步与盈亏算法口径](./docs/资产同步与盈亏算法口径.md)
- [管理后台功能手册 V2](./docs/管理后台功能手册V2.md)
- [生物识别与会话持久化](./docs/登录态与生物识别说明.md)
- [后端测试地图](./kona_tool/tests/README_测试地图.md)
- [Flutter 页面与状态地图](./flutter/lib/README_页面与状态地图.md)
- [Web 页面与状态地图](./web/src/README_页面与状态地图.md)
- [工作区骨架说明](../项目结构.md)
- [目录文档规范](../目录文档规范.md)
- [AI 接手规则](../AGENTS.md)
- [AI 文档索引表](../AGENTS_文档索引表.md)
- [版本记录规范](./版本记录规范.md)

---

## 📈 版本历史

当前 Flutter 客户端版本：`1.0.28`

说明：

- 这个版本号只代表 Flutter 安装包版本
- 不是 `CHANGELOG.md` 里的内部变更记录编号
- App 内“检查更新”是否提示新版本，取决于后端 `/api/app/version` 返回值

项目历史变更请直接查阅 [CHANGELOG.md](./CHANGELOG.md)。

---

## ⚖ 许可说明

本项目仅供学习与个人投资管理使用，不构成任何投资建议。
Copyright © 2026 Kona Project Team. All Rights Reserved.
