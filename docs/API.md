# API Reference (Backend)

This file is auto-generated from `kona_tool/app.py`.

Run: `python3 scripts/generate_api_docs.py`


---

## Detailed Request/Response

See `docs/API_DETAILS.md` for parameters and response formats.

---

## Web Pages

- `GET /`
- `GET /assets`
- `GET /test`
- `GET /compare`
- `GET /direct_test`
- `GET /analysis`
- `GET /news`
- `GET /settings`


## Core APIs

- `GET /api/price`
- `POST /api/prices/batch`
- `GET /api/rates`
- `GET /api/portfolio`
- `POST /api/portfolio/add`
- `POST /api/portfolio/update`
- `GET /api/history`
- `POST /api/portfolio/modify`
- `POST /api/portfolio/delete`
- `POST /api/portfolio/buy`
- `POST /api/portfolio/sell`
- `GET /api/transactions`
- `GET /api/search`


## Auth

- `POST /api/auth/login`
- `GET /api/auth/me`


## Analysis & News

- `GET /api/news/latest`
- `GET /api/analysis/overview`
- `GET /api/analysis/calendar`
- `GET /api/analysis/rank`


## Assets (Cash/Other/Liabilities)

- `GET /api/cash_assets`
- `POST /api/cash_assets/add`
- `POST /api/cash_assets/delete`
- `POST /api/cash_assets/update`
- `GET /api/other_assets`
- `POST /api/other_assets/add`
- `POST /api/other_assets/delete`
- `POST /api/other_assets/update`
- `GET /api/liabilities`
- `POST /api/liabilities/add`
- `POST /api/liabilities/delete`
- `POST /api/liabilities/update`


## Snapshots

- `POST /api/snapshot/save`
- `POST /api/snapshot/trigger`
- `POST /api/snapshot/fix`


## Settings

- `GET /api/settings/info`
- `GET /api/settings/check_api`
- `GET /api/settings/backup`
- `POST /api/settings/restore`


## Health

- `GET /health`

