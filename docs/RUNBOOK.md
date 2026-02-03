# Runbook (Local Development)

This guide covers how to run the backend and frontend locally, and common checks.

---

## Backend (kona_tool)

### Requirements
- Python 3.9+
- pip

### Install
```
cd kona_tool
pip3 install -r requirements.txt
```

### Run
```
python3 app.py
```

### Health Check
```
http://127.0.0.1:5003/api/rates
```

### Common Checks
```
ps -ef | grep "python3 app.py"
```

---

## Frontend (flutter)

### Requirements
- Flutter SDK (3.x)
- Xcode (macOS) or Android Studio

### Install
```
cd flutter
flutter pub get
```

### Configure API Base URL
Edit:
```
flutter/lib/config/api_config.dart
```
Set base URL to local backend for dev:
```
http://127.0.0.1:5003
```

### Run
```
flutter run
```

### Data Refresh Behavior (SWR)

- App shows cached data immediately on launch
- Background refresh updates data automatically
- Switching pages does not clear data
- Pull down to refresh on pages that support it

If you need a clean slate for testing:
- Clear app storage on the device, or
- Uninstall and reinstall the app

---

## When Things Go Wrong

- If API calls fail, confirm backend is running and base URL is correct.
- If Flutter cannot run, check Flutter SDK installation.
- If backend fails to start, check `kona_tool/app.log`.

---

## Update API Docs

If you change routes in `kona_tool/app.py`, regenerate docs:

```
python3 scripts/generate_api_docs.py
python3 scripts/generate_api_details.py
```
