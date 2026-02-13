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
- `POST /api/auth/register`
- `POST /api/auth/invite/validate`
- `POST /api/auth/password/change`
- `POST /api/auth/refresh`
- `POST /api/auth/logout`
- `GET /api/auth/me`
- `POST /api/auth/profile`
- `POST /api/auth/bootstrap_credentials`
- `POST /api/auth/send_code` (deprecated, returns 410)


## Admin APIs

- `GET /api/admin/overview`
- `GET /api/admin/users`
- `GET /api/admin/users/metrics`
- `GET /api/admin/users/<user_id>`
- `POST /api/admin/users/status`
- `POST /api/admin/users/update`
- `POST /api/admin/users/disable`
- `POST /api/admin/users/enable`
- `POST /api/admin/users/password/reset`
- `POST /api/admin/users/sessions/revoke`
- `GET /api/admin/config`
- `POST /api/admin/config/update`
- `GET /api/admin/data/snapshots`
- `POST /api/admin/data/snapshot/trigger`
- `POST /api/admin/data/snapshot/cleanup_weekend`
- `POST /api/admin/data/backup`
- `POST /api/admin/data/restore`
- `GET /api/admin/data/rebind/preview`
- `POST /api/admin/data/rebind/execute`
- `GET /api/admin/apis/health`
- `POST /api/admin/apis/smoke_test`
- `GET /api/admin/apis/policies`
- `POST /api/admin/apis/policies/update`
- `POST /api/admin/apis/policies/batch_update`
- `POST /api/admin/invites/generate`
- `GET /api/admin/invites`
- `GET /api/admin/invites/stats`
- `POST /api/admin/invites/revoke`
- `GET /api/admin/invites/export`


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
