# API Reference (Backend)

This list is based on `kona_tool/app.py` routes. Methods are shown when defined.

---

## Web Pages

- `GET /` main investment page
- `GET /assets` assets page
- `GET /analysis` analysis page
- `GET /news` news page
- `GET /settings` settings page
- `GET /test` API test page
- `GET /compare` JS compare page
- `GET /direct_test` direct test page

---

## Core APIs

- `GET /api/price`
- `POST /api/prices/batch`
- `GET /api/rates`
- `GET /api/portfolio`
- `POST /api/portfolio/add`
- `POST /api/portfolio/update`
- `POST /api/portfolio/modify`
- `POST /api/portfolio/delete`
- `POST /api/portfolio/buy`
- `POST /api/portfolio/sell`
- `GET /api/transactions`
- `GET /api/history`
- `GET /api/search`

---

## Cash Assets

- `GET /api/cash_assets`
- `POST /api/cash_assets/add`
- `POST /api/cash_assets/delete`
- `POST /api/cash_assets/update`

---

## Other Assets

- `GET /api/other_assets`
- `POST /api/other_assets/add`
- `POST /api/other_assets/delete`
- `POST /api/other_assets/update`

---

## Liabilities

- `GET /api/liabilities`
- `POST /api/liabilities/add`
- `POST /api/liabilities/delete`
- `POST /api/liabilities/update`

---

## Analysis & News

- `GET /api/analysis/overview`
- `GET /api/analysis/calendar`
- `GET /api/analysis/rank`
- `GET /api/news/latest`

---

## Snapshots

- `POST /api/snapshot/save`
- `POST /api/snapshot/trigger`
- `POST /api/snapshot/fix`

---

## Settings

- `GET /api/settings/info`
- `GET /api/settings/check_api`
- `GET /api/settings/backup`
- `POST /api/settings/restore`

---

## Auth

- `POST /api/auth/login`
- `GET /api/auth/me`

---

## Health

- `GET /health`
