# API Details (Request/Response)

This document summarizes request parameters and response formats based on `kona_tool/app.py` and `kona_tool/core/db.py`.

---

## Auth Header

Some endpoints require or accept JWT:

```
Authorization: Bearer <token>
```

- `@login_required` = required
- `@optional_auth` = optional (if missing, user_id is treated as empty/legacy)

---

## Web Pages

### `GET /`
- Response: HTML page (investment.html)

### `GET /assets`
- Response: HTML page (assets.html)

### `GET /analysis`
- Response: HTML page (analysis.html)

### `GET /news`
- Response: HTML page (news.html)

### `GET /settings`
- Response: HTML page (settings.html)

### `GET /test`
- Response: HTML page (test_api.html)

### `GET /compare`
- Response: HTML (static_compare.html)

### `GET /direct_test`
- Response: HTML (direct_test.html)

---

## Pricing

### `GET /api/price`
**Query**
- `code` (string, required)

**Response**
```json
{
  "price": 0,
  "yclose": 0,
  "amt": 0,
  "chg": 0
}
```

### `POST /api/prices/batch`
**Body**
```json
{ "codes": ["sh600000", "sz000001"] }
```

**Response**
```json
{
  "sh600000": {"price": 0, "yclose": 0, "amt": 0, "chg": 0},
  "sz000001": {"price": 0, "yclose": 0, "amt": 0, "chg": 0}
}
```

### `GET /api/rates`
**Response**
```json
{ "USD": 7.25, "HKD": 0.93, "CNY": 1.0 }
```

---

## Portfolio (Auth: optional)

### `GET /api/portfolio`
**Query**
- `type` (string, optional) one of `all|stock_cn|stock_us|stock_hk|fund`

**Response**
```json
[
  {
    "code": "sh600000",
    "name": "xxx",
    "qty": 100,
    "price": 10.0,
    "curr": "CNY",
    "adjustment": 0
  }
]
```

### `POST /api/portfolio/add`
**Body**
```json
{ "code": "sh600000", "name": "xxx", "qty": 100, "price": 10.0, "curr": "CNY" }
```

**Response**
```json
{ "status": "ok" }
```

### `POST /api/portfolio/update`
**Body**
```json
{ "code": "sh600000", "field": "qty", "val": 200 }
```

**Response**
```json
{ "status": "ok" }
```

### `POST /api/portfolio/modify`
**Body**
```json
{ "code": "sh600000", "qty": 100, "price": 10.0, "adjustment": 0 }
```

**Response**
```json
{ "status": "ok" }
```

### `POST /api/portfolio/delete`
**Body**
```json
{ "code": "sh600000" }
```

**Response**
```json
{ "status": "ok" }
```

### `POST /api/portfolio/buy`
**Body**
```json
{ "code": "sh600000", "price": 10.2, "qty": 50 }
```

**Response**
```json
{ "status": "ok" }
```

### `POST /api/portfolio/sell`
**Body**
```json
{ "code": "sh600000", "price": 10.5, "qty": 30 }
```

**Response**
```json
{ "status": "ok" }
```

---

## Transactions (Auth: optional)

### `GET /api/transactions`
**Query**
- `limit` (int, default 100)

**Response**
```json
[
  {
    "time": "2026-02-03 12:00:00",
    "code": "sh600000",
    "name": "xxx",
    "type": "加仓|减仓",
    "price": 10.0,
    "qty": 100,
    "amount": 1000,
    "pnl": 0
  }
]
```

---

## History / Snapshots

### `GET /api/history` (Auth: optional)
**Query**
- `days` (int, default 365)

**Response**
```json
[
  {
    "date": "2026-02-01",
    "total_asset": 0,
    "total_invest": 0,
    "total_cash": 0,
    "total_other": 0,
    "total_liability": 0,
    "total_pnl": 0,
    "day_pnl": 0,
    "updated_at": "...",
    "user_id": "..."
  }
]
```

### `POST /api/snapshot/save` (Auth: optional)
**Body**
```json
{
  "total_asset": 0,
  "total_invest": 0,
  "total_cash": 0,
  "total_other": 0,
  "total_liability": 0,
  "total_pnl": 0,
  "day_pnl": 0
}
```

**Response**
```json
{ "status": "ok" }
```

### `POST /api/snapshot/trigger`
**Response**
```json
{ "status": "ok", "message": "Snapshot taken successfully" }
```

### `POST /api/snapshot/fix` (Auth: optional)
**Body**
```json
{ "dates": ["2026-01-17", "2026-01-18"] }
```

**Response**
```json
{ "status": "ok", "message": "Fixed 2 records" }
```

---

## Cash Assets (Auth: optional)

### `GET /api/cash_assets`
**Response**
```json
[{"id": 1, "name": "现金", "amount": 1000, "curr": "CNY"}]
```

### `POST /api/cash_assets/add`
**Body**
```json
{ "name": "现金", "amount": 1000, "curr": "CNY" }
```

### `POST /api/cash_assets/delete`
**Body**
```json
{ "id": 1 }
```

### `POST /api/cash_assets/update`
**Body**
```json
{ "id": 1, "name": "现金", "amount": 1200, "curr": "CNY" }
```

---

## Other Assets (Auth: optional)

Same format as Cash Assets:
- `GET /api/other_assets`
- `POST /api/other_assets/add`
- `POST /api/other_assets/delete`
- `POST /api/other_assets/update`

---

## Liabilities (Auth: optional)

Same format as Cash Assets:
- `GET /api/liabilities`
- `POST /api/liabilities/add`
- `POST /api/liabilities/delete`
- `POST /api/liabilities/update`

---

## News

### `GET /api/news/latest`
**Response**
JSON list from news source (see `core/news.py`).

---

## Search

### `GET /api/search`
**Query**
- `q` (string)

**Response**
JSON list of matched securities.

---

## Settings

### `GET /api/settings/info`
**Response**
System version info.

### `GET /api/settings/check_api`
**Response**
API availability status.

### `GET /api/settings/backup`
**Response**
Downloads `portfolio.db` file.

### `POST /api/settings/restore`
**Body (multipart/form-data)**
- `file` (database file)

**Response**
```json
{ "status": "ok", "message": "Restore successful" }
```

---

## Auth

### `POST /api/auth/login`
**Body**
```json
{ "user_id": "xxx", "email": "xx@xx.com", "access_token": "optional" }
```

**Response**
```json
{ "token": "jwt", "user_id": "xxx", "user_number": 10001, "email": "xx@xx.com" }
```

### `GET /api/auth/me` (Auth: required)
**Response**
```json
{ "user_id": "xxx", "email": "xx@xx.com" }
```

---

## Analysis (Auth: optional)

### `GET /api/analysis/overview`
**Query**
- `period` (day|month|year|all)

**Response**
```json
{
  "day": {"pnl": 0, "pnl_rate": 0, "base_value": 0},
  "month": {"pnl": 0, "pnl_rate": 0, "base_value": 0},
  "year": {"pnl": 0, "pnl_rate": 0, "base_value": 0},
  "all": {"pnl": 0, "pnl_rate": 0, "base_value": 0}
}
```

### `GET /api/analysis/calendar`
**Query**
- `type` (day|month|year)

**Response**
```json
{ "items": [{"label": "1", "pnl": 0}], "total_pnl": 0, "total_rate": 0, "title": "" }
```

### `GET /api/analysis/rank`
**Query**
- `type` (gain|loss|all)
- `market` (all|a|us|hk|fund)

**Response**
```json
{ "gain": [{"code":"", "name":"", "pnl":0, "pnl_rate":0, "market":""}], "loss": [] }
```

---

## Health

### `GET /health`
**Response**
```json
{ "status": "ok", "version": "v12.0.0" }
```
