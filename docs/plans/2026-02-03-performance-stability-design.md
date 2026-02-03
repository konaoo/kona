# Performance & Stability Design (2026-02-03)

## Goal
Improve UX so the app opens with data immediately, page switches are instant (no empty state), and stability is higher without changing business logic.

## User-Desired Experience
- App opens with data visible immediately
- Page switching is smooth and does not re-fetch
- Returning to a page does not trigger a full reload
- Data may be slightly stale (10–30s OK)
- No manual refresh button; use pull-to-refresh

## Approach (SWR: Stale-While-Revalidate)
Use a three-layer data strategy:
1. **Persistent cache** for fast startup
2. **In-memory AppState** for fast page switching
3. **Background refresh** to update data quietly

## Frontend Plan (Flutter)

### 1) Persistent Cache
- Store core datasets as JSON in local storage (SharedPreferences is sufficient initially).
- Datasets to cache:
  - portfolio
  - prices
  - cash_assets / other_assets / liabilities
  - analysis overview / calendar / rank
  - news
  - rates
- Save a `lastUpdated` timestamp per dataset.

### 2) AppState Hydration
- On app start, call `hydrateFromCache()` to load cached data into memory.
- Render UI immediately using the hydrated data.
- After hydration, trigger `refreshAll()` in background to update from API.

### 3) Background Refresh
- API refresh happens after first paint to avoid blocking UI.
- Update in-memory state and cache when new data arrives.
- If API fails, keep cached data and show a non-blocking error message.

### 4) Page Switching Without Reload
- Pages must read from `AppState` only.
- Remove/avoid data fetching in `initState` of pages if AppState already has data.
- Keep `IndexedStack` to preserve page state.

### 5) Pull-to-Refresh
- Keep pull-to-refresh on main pages.
- Trigger a targeted refresh for that page’s data only.

## Backend Plan (Flask)

### 1) Unified Timeout & Retry
- Use a single request helper with short timeout (2–3s) and limited retries.
- Prevent slow external sources from blocking overall API.

### 2) Cache Hit Optimization
- Batch endpoints (`/api/prices/batch`) should return cache hits first.
- Only missing items trigger external fetch.

## Deployment Stability
- Keep current GitHub Actions deployment.
- Continue post-deploy health check.
- No structural change to runtime needed at this phase.

## File-Level Change Map

### Frontend
- `flutter/lib/providers/app_state.dart`
  - Add `hydrateFromCache()`, `saveToCache()`, `refreshAll()`
- `flutter/lib/services/api_service.dart`
  - Add unified timeout & retry
- `flutter/lib/pages/*`
  - Read data from `AppState` only
  - Remove page-init fetches
  - Enable pull-to-refresh
- `flutter/lib/config/api_config.dart`
  - No change (ensure correct base URL)

### Backend
- `kona_tool/core/price.py`
  - Use helper for timeout/retry
  - Cache-first for batch
- `kona_tool/core/utils.py` (or new helper)
  - HTTP helper for external requests

## Out of Scope
- Major refactor or new architecture
- Replace SQLite
- Build full offline mode
- Change external data providers

## Success Criteria
- Launch shows data within < 1s from cache
- Page switching is instant, no empty states
- Data refresh completes within 10–30s in background
- API errors do not blank out UI

