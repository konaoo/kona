# Project Overview (Quick Reference)

This is a compact, durable summary of the project so a new machine or a fresh session can quickly recover context.

---

## What This Project Is

- Portfolio management system
- Frontend: Flutter (mobile/desktop/web)
- Backend: Python Flask (API + web pages)
- Database: SQLite (`portfolio.db`)
- Deployment: AWS + GitHub Actions (auto + manual)

---

## Repo Layout

```
.
├─ flutter/                    # Flutter frontend
├─ kona_tool/                  # Flask backend
├─ .github/workflows/          # GitHub Actions (deploy)
├─ archive/HI/                 # Legacy (archived)
└─ docs/                       # Documentation
```

---

## Frontend (Flutter)

- API base URL: `flutter/lib/config/api_config.dart`
- Run:
```
cd flutter
flutter pub get
flutter run
```

## Data Refresh (SWR)

- App loads cached data first (instant UI)
- Background refresh updates data automatically
- Switching pages does not clear or reload data
- Pull-to-refresh triggers a manual refresh

Key files:
- `flutter/lib/providers/app_state.dart`
- `flutter/lib/services/cache_service.dart`

---

## Backend (Flask)

- Entry: `kona_tool/app.py`
- Run:
```
cd kona_tool
pip3 install -r requirements.txt
python3 app.py
```
- Port: `5003` (see `kona_tool/config.py`)

---

## Deployment (AWS + GitHub Actions)

- Push to `main` triggers deploy
- Manual deploy button enabled via `workflow_dispatch`
- Health check: `http://127.0.0.1:5003/api/rates`

Secrets required:
- `SSH_HOST`, `SSH_USER`, `SSH_KEY`, `APP_DIR`

---

## Logs & Maintenance

- Log file: `kona_tool/app.log`
- Log rotation: `kona_tool/rotate_log.sh` (cron weekly)
- Maintenance guide: `docs/MAINTENANCE.md`

---

## API Docs

- Summary list: `docs/API.md`
- Detailed params: `docs/API_DETAILS.md`
- OpenAPI: `docs/openapi.yaml`
- Swagger UI: `docs/swagger-ui.html`
- Import guide: `docs/API_IMPORT.md`

---

## Auto Doc Scripts

- `python3 scripts/generate_api_docs.py`
- `python3 scripts/generate_api_details.py`

---

## Common Checks

- Service running:
```
ps -ef | grep "python3 app.py"
```
- Health check:
```
http://<server-ip>:5003/api/rates
```
