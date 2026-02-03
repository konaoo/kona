# SWR Performance & Stability Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** App opens with cached data, page switches are instant, background refresh updates data within ~10–30s; backend handles slow external APIs with timeout/retry and cache-first batch responses.

**Architecture:** Use Stale-While-Revalidate on Flutter: hydrate from persistent cache into AppState, render immediately, then refresh in background and update cache. Backend adds a small HTTP helper with timeout/retry and uses cache-first for batch pricing.

**Tech Stack:** Flutter (Dart), SharedPreferences, Provider; Flask (Python), requests, SQLite.

---

### Task 1: Add Flutter Cache Service (persistent JSON)

**Files:**
- Create: `flutter/lib/services/cache_service.dart`
- Test: `flutter/test/cache_service_test.dart`

**Step 1: Write the failing test**
```dart
// flutter/test/cache_service_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';
import 'package:tool/services/cache_service.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('CacheService stores and loads JSON', () async {
    SharedPreferences.setMockInitialValues({});
    final cache = CacheService();

    final data = {'a': 1, 'b': 'x'};
    await cache.setJson('test_key', data);
    final loaded = await cache.getJson('test_key');

    expect(loaded, data);
  });
}
```

**Step 2: Run test to verify it fails**
Run: `cd flutter && flutter test test/cache_service_test.dart -r expanded`
Expected: FAIL (CacheService not found)

**Step 3: Write minimal implementation**
```dart
// flutter/lib/services/cache_service.dart
import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

class CacheService {
  Future<void> setJson(String key, Map<String, dynamic> data) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(key, jsonEncode(data));
  }

  Future<Map<String, dynamic>?> getJson(String key) async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(key);
    if (raw == null) return null;
    return jsonDecode(raw) as Map<String, dynamic>;
  }

  Future<void> setString(String key, String value) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(key, value);
  }

  Future<String?> getString(String key) async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(key);
  }
}
```

**Step 4: Run test to verify it passes**
Run: `cd flutter && flutter test test/cache_service_test.dart -r expanded`
Expected: PASS

**Step 5: Commit**
```bash
git add flutter/lib/services/cache_service.dart flutter/test/cache_service_test.dart
git commit -m "feat: add cache service"
```

---

### Task 2: AppState hydration from cache + background refresh

**Files:**
- Modify: `flutter/lib/providers/app_state.dart`
- Modify: `flutter/lib/models/portfolio.dart` (if needed for JSON parsing)
- Test: `flutter/test/app_state_cache_test.dart`

**Step 1: Write the failing test**
```dart
// flutter/test/app_state_cache_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';
import 'package:tool/providers/app_state.dart';
import 'package:tool/services/cache_service.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('AppState hydrates portfolio from cache', () async {
    SharedPreferences.setMockInitialValues({
      'cache_portfolio': jsonEncode({
        'items': [
          {'code': 'sh600000', 'name': 'X', 'qty': 1, 'price': 10, 'curr': 'CNY', 'adjustment': 0}
        ]
      })
    });

    final state = AppState();
    await state.hydrateFromCache();

    expect(state.portfolioLoaded, true);
    expect(state.portfolio.first.code, 'sh600000');
  });
}
```

**Step 2: Run test to verify it fails**
Run: `cd flutter && flutter test test/app_state_cache_test.dart -r expanded`
Expected: FAIL (hydrateFromCache missing)

**Step 3: Write minimal implementation**
Add to `AppState`:
```dart
final CacheService _cache = CacheService();

Future<void> hydrateFromCache() async {
  final cached = await _cache.getJson('cache_portfolio');
  if (cached != null && cached['items'] is List) {
    _portfolio = (cached['items'] as List)
        .map((e) => PortfolioItem.fromJson(e))
        .toList();
    _portfolioLoaded = true;
    notifyListeners();
  }
}

Future<void> savePortfolioToCache() async {
  await _cache.setJson('cache_portfolio', {
    'items': _portfolio.map((e) => e.toJson()).toList(),
  });
}
```

Also call `savePortfolioToCache()` after successful refresh.

**Step 4: Run test to verify it passes**
Run: `cd flutter && flutter test test/app_state_cache_test.dart -r expanded`
Expected: PASS

**Step 5: Commit**
```bash
git add flutter/lib/providers/app_state.dart flutter/test/app_state_cache_test.dart
git commit -m "feat: hydrate app state from cache"
```

---

### Task 3: Page switching uses AppState only + pull-to-refresh

**Files:**
- Modify: `flutter/lib/pages/home_page.dart`
- Modify: `flutter/lib/pages/invest_page.dart`
- Modify: `flutter/lib/pages/analysis_page.dart`
- Modify: `flutter/lib/pages/news_page.dart`
- Test: `flutter/test/page_refresh_widget_test.dart`

**Step 1: Write the failing test**
```dart
// flutter/test/page_refresh_widget_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:tool/providers/app_state.dart';
import 'package:tool/pages/home_page.dart';

void main() {
  testWidgets('HomePage has pull-to-refresh', (tester) async {
    await tester.pumpWidget(
      ChangeNotifierProvider(
        create: (_) => AppState(),
        child: const MaterialApp(home: HomePage(onNavigate: (_) {}, onSwitchTab: (_) {})),
      ),
    );

    expect(find.byType(RefreshIndicator), findsOneWidget);
  });
}
```

**Step 2: Run test to verify it fails**
Run: `cd flutter && flutter test test/page_refresh_widget_test.dart -r expanded`
Expected: FAIL if RefreshIndicator missing

**Step 3: Write minimal implementation**
- Wrap main list view with `RefreshIndicator`
- On refresh call `context.read<AppState>().refreshAll()` or page-specific refresh
- Ensure pages read from `AppState` without triggering fetch in `initState`

**Step 4: Run test to verify it passes**
Run: `cd flutter && flutter test test/page_refresh_widget_test.dart -r expanded`
Expected: PASS

**Step 5: Commit**
```bash
git add flutter/lib/pages/*.dart flutter/test/page_refresh_widget_test.dart
git commit -m "feat: pull-to-refresh and no re-fetch on tab switch"
```

---

### Task 4: Backend HTTP helper (timeout/retry)

**Files:**
- Modify: `kona_tool/core/utils.py`
- Test: `kona_tool/tests/test_http_utils.py`

**Step 1: Write the failing test**
```python
# kona_tool/tests/test_http_utils.py
import unittest
from unittest.mock import patch
from core.utils import http_get

class TestHttpGet(unittest.TestCase):
    @patch('core.utils.requests.get')
    def test_http_get_retries(self, mock_get):
        mock_get.side_effect = Exception('boom')
        with self.assertRaises(Exception):
            http_get('http://example.com', retries=2)
        self.assertEqual(mock_get.call_count, 2)

if __name__ == '__main__':
    unittest.main()
```

**Step 2: Run test to verify it fails**
Run: `python -m unittest kona_tool/tests/test_http_utils.py -v`
Expected: FAIL (http_get missing)

**Step 3: Write minimal implementation**
```python
# kona_tool/core/utils.py
import time
import requests

def http_get(url, params=None, headers=None, timeout=3, retries=2, backoff=0.3):
    last_err = None
    for i in range(retries):
        try:
            return requests.get(url, params=params, headers=headers, timeout=timeout)
        except Exception as e:
            last_err = e
            time.sleep(backoff)
    raise last_err
```

**Step 4: Run test to verify it passes**
Run: `python -m unittest kona_tool/tests/test_http_utils.py -v`
Expected: PASS

**Step 5: Commit**
```bash
git add kona_tool/core/utils.py kona_tool/tests/test_http_utils.py
git commit -m "feat: add http helper with retry"
```

---

### Task 5: Cache-first batch pricing

**Files:**
- Modify: `kona_tool/core/price.py`
- Test: `kona_tool/tests/test_price_cache.py`

**Step 1: Write the failing test**
```python
# kona_tool/tests/test_price_cache.py
import unittest
from unittest.mock import patch
import core.price as price

class TestBatchCache(unittest.TestCase):
    def test_batch_returns_cached_first(self):
        price._PRICE_CACHE = {'sh600000': (10, 9, 0, 0)}
        res = price.batch_get_prices(['sh600000'])
        self.assertIn('sh600000', res)

if __name__ == '__main__':
    unittest.main()
```

**Step 2: Run test to verify it fails**
Run: `python -m unittest kona_tool/tests/test_price_cache.py -v`
Expected: FAIL if cache not used

**Step 3: Write minimal implementation**
- In `batch_get_prices`, return cached items immediately
- Only request missing codes from external APIs

**Step 4: Run test to verify it passes**
Run: `python -m unittest kona_tool/tests/test_price_cache.py -v`
Expected: PASS

**Step 5: Commit**
```bash
git add kona_tool/core/price.py kona_tool/tests/test_price_cache.py
git commit -m "perf: cache-first batch pricing"
```

---

### Task 6: Update docs

**Files:**
- Modify: `docs/PROJECT_OVERVIEW.md`
- Modify: `docs/RUNBOOK.md`

**Step 1: Write failing doc check**
- Ensure new cache/refresh behavior is documented

**Step 2: Update docs**
- Add "SWR cache" note
- Mention pull-to-refresh

**Step 3: Commit**
```bash
git add docs/PROJECT_OVERVIEW.md docs/RUNBOOK.md
git commit -m "docs: update for swr cache"
```

