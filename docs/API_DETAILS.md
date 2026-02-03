# API Details (Auto Generated)

Generated from `kona_tool/app.py` by `scripts/generate_api_details.py`.

This is a best-effort extraction; verify against code for edge cases.


---

## `/assets`

**Methods**: GET

---

## `/compare`

**Methods**: GET

---

## `/api/price`

**Methods**: GET

---

## `/api/rates`

**Methods**: GET

---

## `/api/portfolio/add`

**Methods**: POST

**Query Params**
  - `type`, default: 'all'

---

## `/analysis`

**Methods**: GET

**Request Body**
- required: code, field, val

---

## `/settings`

**Methods**: GET

---

## `/api/settings/check_api`

**Methods**: GET

---

## `/api/settings/restore`

**Methods**: POST

---

## `/api/history`

**Methods**: GET

---

## `/api/snapshot/save`

**Methods**: POST

**Request Body**
- required: code, qty, price, adjustment

---

## `/api/snapshot/fix`

**Methods**: POST

---

## `/api/portfolio/buy`

**Methods**: POST

**Request Body**
- required: code

---

## `/api/transactions`

**Methods**: GET

**Request Body**
- required: code, price, qty

---

## `/api/cash_assets`

**Methods**: GET

**Query Params**
  - `q`, default: ''

---

## `/api/cash_assets/delete`

**Methods**: POST

---

## `/api/other_assets`

**Methods**: GET

---

## `/api/other_assets/delete`

**Methods**: POST

---

## `/api/liabilities`

**Methods**: GET

---

## `/api/liabilities/delete`

**Methods**: POST

---

## `/api/liabilities/update`

**Methods**: POST

---

## `/api/auth/me`

**Methods**: GET

**Request Body**
- required: user_id, email

---

## `/api/analysis/overview`

**Methods**: GET

---

## `/api/analysis/rank`

**Methods**: GET

**Query Params**
  - `type`, default: 'day'

---
