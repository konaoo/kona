# Project Structure

This document explains the purpose of each top-level directory and the key folders inside the backend and frontend.

---

## Top-Level

```
.
├─ .github/workflows/          # GitHub Actions (auto deploy)
├─ flutter/                    # Flutter frontend
├─ kona_tool/                  # Flask backend
├─ archive/HI/                 # Archived legacy code (not used in production)
├─ docs/                       # Documentation (this folder)
└─ README.md
```

---

## Frontend (flutter)

```
flutter/
├─ lib/
│  ├─ main.dart                # App entry point
│  ├─ config/                  # App config, theme, API base URL
│  ├─ models/                  # Data models
│  ├─ pages/                   # Screens/pages
│  ├─ providers/               # State management
│  ├─ services/                # API client
│  └─ widgets/                 # Reusable UI components
├─ assets/                     # Images and assets
├─ android/ ios/ web/ macos/ windows/ linux/  # Platform targets
└─ pubspec.yaml                # Flutter dependencies and assets
```

Key file: `flutter/lib/config/api_config.dart`

---

## Backend (kona_tool)

```
kona_tool/
├─ app.py                      # Flask app entry
├─ core/                       # Core business modules
│  ├─ auth.py                  # Auth / token handling
│  ├─ db.py                    # Database manager
│  ├─ fund.py                  # Fund data fetching
│  ├─ news.py                  # News data fetching
│  ├─ parser.py                # Code parsing
│  ├─ price.py                 # Price fetching + cache
│  ├─ snapshot.py              # Snapshot/export
│  ├─ stock.py                 # Stock data fetching
│  ├─ system.py                # System helpers
│  └─ utils.py                 # Utilities
├─ templates/                  # Web templates
├─ migrations/                 # DB migration files
├─ requirements.txt            # Python dependencies
├─ config.py                   # Server config and data sources
├─ portfolio.db                # SQLite database (important)
├─ app.pid                     # PID file for auto deploy
├─ rotate_log.sh               # Log rotation script
└─ archive/old_files/          # Archived tests and old files
```

---

## Archived

- `archive/HI/` is legacy code kept for reference. It is not used in deployment.
- `kona_tool/archive/old_files/` contains old tests, logs, and backups.
