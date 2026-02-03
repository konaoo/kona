# Frontend Setup (Flutter)

This guide explains how to set up and run the Flutter frontend from a new computer.

---

## 1. Install Flutter SDK

- Download Flutter from the official Flutter website
- Add Flutter to your PATH
- Run:
```
flutter doctor
```
Fix any issues it reports.

---

## 2. Install Platform Tools

**macOS (iOS):**
- Install Xcode
- Open Xcode once and accept licenses

**Android:**
- Install Android Studio
- Install SDK and an emulator

---

## 3. Project Setup

```
cd flutter
flutter pub get
```

---

## 4. Configure API Base URL

Edit:
```
flutter/lib/config/api_config.dart
```

For local development:
```
http://127.0.0.1:5003
```

For AWS (production):
```
http://35.78.253.89:5003
```

---

## 5. Run

```
flutter run
```

---

## 6. Common Issues

- If the app cannot call API, check the base URL
- If Flutter fails to build, re-run `flutter doctor`
- The app uses local cache for faster first paint; clear app storage if you need to reset
