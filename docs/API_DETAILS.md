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

## `/api/auth/login`

**Methods**: POST

**Request Body**
- required: `username`, `password`
- optional: `device_id`

**Response**
- `access_token`, `refresh_token`, `refresh_expires_at`, `user`

---

## `/api/auth/register`

**Methods**: POST

**Request Body**
- required: `username`, `password`, `invite_code`
- optional: `device_id`

---

## `/api/auth/invite/validate`

**Methods**: POST

**Request Body**
- required: `invite_code`

---

## `/api/auth/password/change`

**Methods**: POST

**Request Body**
- required: `old_password`, `new_password`

---

## `/api/auth/refresh`

**Methods**: POST

**Request Body**
- required: `refresh_token`
- optional: `device_id`

---

## `/api/auth/logout`

**Methods**: POST

**Request Body**
- optional: `refresh_token`

---

## `/api/auth/send_code`

**Methods**: POST

**Status**
- Deprecated, always returns `410`

---
