# 咔咔记账 Flutter 客户端

Flutter 客户端模块，负责移动端（Android / iOS / macOS）资产管理、投资、分析、快讯与个人中心功能。

## 1. 环境要求

- Flutter: `3.35.x`（建议与本机已安装版本保持一致）
- Dart: `3.10.x`
- Android Studio / Xcode（按目标平台安装）

## 2. 快速启动

```bash
cd /Users/kona/Desktop/kaka/kona_repo/flutter
flutter pub get
flutter run
```

指定安卓设备运行：

```bash
cd /Users/kona/Desktop/kaka/kona_repo/flutter
flutter run -d <device_id>
```

查看设备：

```bash
cd /Users/kona/Desktop/kaka/kona_repo/flutter
flutter devices
```

## 3. 常用验证命令

静态检查：

```bash
cd /Users/kona/Desktop/kaka/kona_repo/flutter
flutter analyze
```

单元/组件测试：

```bash
cd /Users/kona/Desktop/kaka/kona_repo/flutter
flutter test
```

仅跑关键用例：

```bash
cd /Users/kona/Desktop/kaka/kona_repo/flutter
flutter test test/profile_page_test.dart test/app_settings_page_test.dart test/auth_persistence_test.dart
```

## 4. 打包命令

Android APK（release）：

```bash
cd /Users/kona/Desktop/kaka/kona_repo/flutter
flutter build apk --release
```

Android App Bundle：

```bash
cd /Users/kona/Desktop/kaka/kona_repo/flutter
flutter build appbundle --release
```

## 5. 目录说明

```text
flutter/
├─ lib/
│  ├─ pages/         # 页面
│  ├─ providers/     # 状态管理（AppState）
│  ├─ widgets/       # 复用组件
│  └─ config/        # 配置与主题
├─ test/             # 测试
├─ assets/images/    # 静态资源
└─ pubspec.yaml      # 依赖与版本
```

## 6. 版本说明

- 当前版本：`1.0.14+14`
- 版本来源：`pubspec.yaml` 的 `version`
- 版本历史：统一维护在仓库根目录 `CHANGELOG.md`

## 7. 开发约定（简版）

- 下拉刷新仅保留顶部动画，避免页面中部大 Loading 打断。
- 用户体验相关改动优先做最小可回归验证（针对性测试先跑，再全量测试）。
- Flutter 变更提交前，建议至少执行一次 `flutter analyze` 与关键测试。
