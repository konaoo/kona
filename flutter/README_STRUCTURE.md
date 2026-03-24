# flutter 目录说明

## 1. 目录用途

`flutter/` 是咔咔记账客户端工程目录。

当前它主要承担：

- Android 客户端
- iOS 客户端预留
- Flutter 统一 UI 业务实现

这个目录本质上是“客户端应用工程”，不是纯组件库，也不是资源备份目录。

---

## 2. 当前核心子目录

```text
flutter/
├─ lib/            # 业务代码
├─ assets/         # 客户端静态资源
├─ test/           # Flutter 测试
├─ android/        # Android 平台工程
├─ ios/            # iOS 平台工程
├─ macos/          # macOS 平台工程
├─ linux/          # Linux 平台工程
├─ windows/        # Windows 平台工程
├─ web/            # Flutter Web 平台壳
├─ build/          # 构建产物
└─ pubspec.yaml    # 依赖与版本号入口
```

其中 `lib/` 当前是最关键的源码区，主要包括：

- `pages/`
- `providers/`
- `services/`
- `widgets/`
- `models/`
- `config/`
- `utils/`

---

## 3. 应该放什么

这个目录应该放：

- Flutter 客户端源码
- 客户端资源
- 客户端测试
- Flutter 平台配置
- 版本号和依赖配置

---

## 4. 不应该放什么

这个目录不应该长期承载：

- 随手备份文件
- 人工复制的 APK 留档
- 无说明的历史实验文件
- 与客户端无关的后端脚本

像下面这些内容，都不应该长期占着 Flutter 工程根目录：

- `app-release-fixed.apk`
- `portfolio.db`
- `.DS_Store`

另外这些目录要明确视为“生成物”，不是主结构：

- `build/`
- `.dart_tool/`
- 平台目录里的缓存和依赖产物

---

## 5. 当前逻辑

`flutter/` 当前负责实现移动端的主要业务体验。

从业务角度看，它主要承载：

- 我的资产
- 我的投资
- 资产分析
- 快讯 / 市场分析
- 设置 / 用户侧能力

从工程角度看，它当前的核心逻辑集中在：

- 页面：`lib/pages/`
- 全局状态：`lib/providers/`
- 服务调用：`lib/services/`
- 复用 UI：`lib/widgets/`

这轮状态层已经先往前走了一小步：

- [app_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_state.dart) 继续当总入口
- [app_auth_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_auth_state.dart) 先承接认证与会话内存状态
- [app_assets_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_assets_state.dart) 先承接资产列表、持仓列表、快照恢复和乐观更新
- [app_market_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_market_state.dart) 先承接汇率、市场开闭市和交易日判断
- [app_overview_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_overview_state.dart) 先承接历史统计和概览里程碑状态
- [app_refresh_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_refresh_state.dart) 先承接缓存恢复、首页刷新、增量同步和行情后台补刷编排
- [app_sync_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_sync_state.dart) 先承接缓存规则、sync 版本和缓存元信息
- [app_trade_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_trade_state.dart) 先承接交易辅助 helper 和老接口兜底流程
- [app_preferences_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_preferences_state.dart) 先承接 UI 偏好
- [app_security_state.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_security_state.dart) 先承接生物识别 / 锁屏

这一步继续往前收了一层：

- `AppState` 里原本那批只是“转手调用 `_syncState`”的缓存 helper 已经删掉
- 现在查 Flutter 缓存 / 增量同步问题，优先先看 `app_sync_state.dart`
- 现在查 Flutter 启动恢复、首页刷新、按版本增量同步和行情后台补刷问题，优先先看 `app_refresh_state.dart`
- `AppState` 在这块主要只保留原入口和依赖组装，不再自己铺整条刷新细节
- 资产 / 持仓这块也已经先切出 `app_assets_state.dart`，后面查买卖、资产列表和乐观更新问题，不用再先翻完整个 `AppState`
- 历史概览这块也已经先切出 `app_overview_state.dart`，后面查首页大卡、历史峰值和分析概览覆盖问题，不用再先翻完整个 `AppState`
- 交易辅助这块也已经先切出 `app_trade_state.dart`，后面查金额换算、undo 信息和老接口兜底问题，不用再先翻完整个 `AppState`

这说明当前 Flutter 工程更像：

`页面驱动 + AppState 集中编排`

后续如果继续工程化，重点不是先拆平台目录，而是先梳理：

- 页面职责
- 状态管理边界
- 和后端口径耦合最重的逻辑

---

## 6. 关键规则

### 6.1 版本号规则

Flutter 客户端版本号以：

- [pubspec.yaml](/Users/kona/Desktop/kaka/kona_repo/flutter/pubspec.yaml)

为准。

APK 构建、发版命名、版本记录，后续都应围绕这里的版本号展开。

### 6.2 构建逻辑

Android APK 由本目录直接构建。

典型命令：

```bash
cd /Users/kona/Desktop/kaka/kona_repo/flutter
flutter build apk --release
```

默认构建产物会进入：

`build/app/outputs/flutter-apk/`

最终对外留档的 APK 再复制到工作区顶层的：

- [/Users/kona/Desktop/kaka/apk](/Users/kona/Desktop/kaka/apk)

### 6.3 业务规则耦合

Flutter 端当前和后端耦合最深的地方包括：

- 持仓口径
- 当日盈亏 / 累计盈亏口径
- 基金待净值更新规则
- 多币种展示规则

所以这个目录后续的核心治理重点，不只是 UI，而是：

`UI 展示和业务口径的边界管理`

---

## 7. 当前结论

`flutter/` 是客户端主应用工程。

后续对它的治理重点应该是：

1. 梳理 `lib/` 内部职责
2. 收紧状态管理边界
3. 把展示逻辑和业务口径分开描述
4. 明确哪些目录是源码，哪些只是生成物

### 7.1 本地清理规则

如果只是想清理空间或保持工程目录干净，优先处理这些：

- `build/`
- `.dart_tool/`
- 根目录里误放的 APK
- 根目录里误放的临时数据库文件

原则是：

- 可再生成的缓存直接清
- 需要保留的非源码文件先归档

### 7.2 补充阅读

- [flutter/lib/README_页面与状态地图.md](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/README_页面与状态地图.md)
