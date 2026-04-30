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

### 6.4 品牌资源生成规则

客户端品牌资源不要分散手工替换，优先按下面的固定入口处理：

- 主 Logo 源图：[assets/images/logo.png](/Users/kona/Desktop/kaka/kona_repo/flutter/assets/images/logo.png)
- 关于页 Logo：[assets/images/about_logo_light.png](/Users/kona/Desktop/kaka/kona_repo/flutter/assets/images/about_logo_light.png) 和 [assets/images/about_logo_dark_small.png](/Users/kona/Desktop/kaka/kona_repo/flutter/assets/images/about_logo_dark_small.png)
- Android 启屏整图：[android/app/src/main/res/drawable-nodpi/splash_screen.png](/Users/kona/Desktop/kaka/kona_repo/flutter/android/app/src/main/res/drawable-nodpi/splash_screen.png)
- Android 12+ 启屏配置：[android/app/src/main/res/values-v31/styles.xml](/Users/kona/Desktop/kaka/kona_repo/flutter/android/app/src/main/res/values-v31/styles.xml)
- 品牌资源生成脚本：[scripts/generate_brand_assets.sh](/Users/kona/Desktop/kaka/kona_repo/flutter/scripts/generate_brand_assets.sh)

替换 Logo 或启动图后，在 `flutter/` 目录执行：

```bash
bash scripts/generate_brand_assets.sh
```

这个脚本会把主 Logo 同步到 about 页 Logo，统一生成桌面图标，并检查启屏图和 Android 12+ 启屏配置是否存在。当前 Android 启屏采用原生配置，原因是 Android 12+ 系统会强制接管冷启动画面，如果直接让系统抓 `ic_launcher`，就容易再次出现居中的方形 Logo 闪一下。

所以这几个文件要一起看，不要只替换其中一个：

- `assets/images/logo.png`
- `assets/images/about_logo_light.png`
- `assets/images/about_logo_dark_small.png`
- `android/app/src/main/res/drawable-nodpi/splash_screen.png`
- `android/app/src/main/res/drawable/splash_transparent_icon.xml`
- `android/app/src/main/res/values-v31/styles.xml`
- `android/app/src/main/res/values-night-v31/styles.xml`

### 6.5 API 地址和明文网络规则

Flutter API 地址统一从 [lib/config/api_config.dart](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/config/api_config.dart) 进入，不要在页面或服务里散落硬编码地址。

当前生产后端仍是 HTTP IP，因此 Android 侧暂时保留 `android:usesCleartextTraffic="true"`，否则登录和接口访问会在运行时被系统拦截。不要把这个开关理解成长期方案，它只是在 HTTPS/域名切换完成前维持兼容。

构建时可用的配置入口：

```bash
flutter build apk --release \
  --dart-define=APP_ENV=production \
  --dart-define=MOBILE_API_BASE_URL=http://114.132.238.12 \
  --dart-define=ALLOW_INSECURE_HTTP=true
```

如果后端切到 HTTPS，发版时应同步改成：

```bash
flutter build apk --release \
  --dart-define=APP_ENV=production \
  --dart-define=MOBILE_API_BASE_URL=https://你的正式域名 \
  --dart-define=ALLOW_INSECURE_HTTP=false
```

同时需要移除 Android Manifest 里的 `android:usesCleartextTraffic="true"`，让系统侧也禁止明文请求。

备用登录入口不要写死在业务代码里，统一用逗号分隔传入：

```bash
--dart-define=MOBILE_LOGIN_FALLBACK_BASE_URLS=https://a.example.com,https://b.example.com
```

如果临时需要改成本地或测试 HTTP 地址，必须显式保留 `ALLOW_INSECURE_HTTP=true`。如果已经切到 HTTPS 发版配置，则不要再混入 HTTP 备用地址。

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
- `lib/generated/openapi/` 里的生成器样板目录，例如 `doc/`、`test/`、`.openapi-generator/`

原则是：

- 可再生成的缓存直接清
- 需要保留的非源码文件先归档

当前 `lib/generated/openapi/` 只保留生成客户端主体和必要包元信息。OpenAPI 生成器自带的文档、空测试壳、CI 样板和 push 脚本不属于 Flutter 客户端运行依赖，已经归档到项目外的 `移出资源/`。

这部分代码是生成产物，当前业务代码没有直接 import。Flutter 静态分析通过 `analysis_options.yaml` 排除整个 `lib/generated/openapi/**`，避免生成器内部 deprecated API 噪音干扰业务代码体检。

### 7.2 补充阅读

- [flutter/lib/README_页面与状态地图.md](/Users/kona/Desktop/kaka/kona_repo/flutter/lib/README_页面与状态地图.md)
