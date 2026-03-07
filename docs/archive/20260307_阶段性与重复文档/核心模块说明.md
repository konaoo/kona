# Backend Core Modules

This document explains what each module under `kona_tool/core/` is responsible for.

---

## core/auth.py

- Authentication helpers
- Token generation and user lookup
- Used by API auth endpoints

## core/db.py

- Database access layer
- CRUD for assets, transactions, and users
- Wraps SQLite operations

## core/fund.py

- Fund data fetching
- Normalizes fund symbols and data sources

## core/news.py

- News data fetcher
- Provides latest news data for `/api/news/latest`

## core/parser.py

- Security code parsing
- Normalizes market codes and currency mapping

## core/price.py

- Price fetching and caching
- Batch queries are cache-first (skip already cached codes)

## core/snapshot.py

- Snapshot and export helpers
- Used by snapshot APIs

## core/stock.py

- Stock data fetching
- Integrates with external quote sources

## core/system.py

- System utilities
- Used by settings and system checks

## core/utils.py

- General utilities and helpers
