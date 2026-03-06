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
├─ scripts/          # 运维与调优工具脚本
└─ CHANGELOG.md      # 项目演进的唯一标准标准记录
```

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
详细记录于 [`docs/RUNBOOK.md`](./docs/RUNBOOK.md):
- **快照补数**: 每 2 小时自动抓取行情快照。若日历无数据，检查 `snapshot.py` 任务。
- **APK 发布**: 
  ```bash
  cd flutter && flutter build apk --release && scp ...
  ```
  下载地址：`http://114.132.238.12/download/apk`

---

## 📖 文档导航

- [环境准备与迁移说明](./docs/README_HANDOVER_2026_03_TENCENT_MIGRATION.md)
- [行情与快讯性能交接（v1.0.31）](./docs/README_HANDOVER_2026_03_QUOTE_NEWS_PERF_AND_CI.md)
- [价格源 / 基金净值 / 快照与盈亏口径交接（2026-03）](./docs/README_HANDOVER_2026_03_PRICE_ALERTS_AND_PNL_LOGIC.md)
- [资产同步与盈亏算法口径](./docs/README_HANDOVER_2026_02_ASSET_REFRESH_AND_PNL_LOGIC.md)
- [管理后台功能手册 V2](./docs/README_ADMIN_CONSOLE_V2.md)
- [生物识别与会话持久化](./docs/README_AUTH_PERSISTENCE_BIOMETRIC.md)

---

## 📈 版本历史

最新稳定版：`v1.0.31`
- **行情与快讯性能升级 (v1.0.31)**
  - 四市场报价链路改为速度优先：快源先返回、慢源受控兜底。
  - 基金净值改为确认值优先（Eastmoney F10），新增腾讯 `jj` 备源。
  - 快讯页升级为“预加载近 50 条 + 增量刷新”。
  - Web/Flutter 刷新节奏对齐，并补 optimistic rollback 与部署重试稳定性。
- **UI & 交互体验升级 (v1.0.30)**
  - 修复首页头像闪烁、添加资产面板主题闪烁、投资弹窗浅色态错色等问题。
  - 优化分析页日期交互与多页面主题一致性。
- `v1.0.29` 及更早：
  - 修复 Android 16 真机图片保存与用户群弹窗层级细节。
- 详情请查阅 [CHANGELOG.md](./CHANGELOG.md)。

---

## ⚖ 许可说明

本项目仅供学习与个人投资管理使用，不构成任何投资建议。
Copyright © 2026 Kona Project Team. All Rights Reserved.
