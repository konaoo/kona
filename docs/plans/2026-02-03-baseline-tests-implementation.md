# Baseline Tests Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Establish minimal backend and frontend baseline tests before any feature changes.

**Architecture:** Backend tests use Flask test_client with mocks to avoid external APIs. Frontend tests use a small unit test on AppState (no network).

**Tech Stack:** Python unittest + unittest.mock; Flutter test.

---

### Task 0.1: Backend baseline tests

**Files:**
- Create: `kona_tool/tests/__init__.py`
- Create: `kona_tool/tests/test_api_baseline.py`

**Step 1: Write the failing test**
```python
import unittest
from unittest.mock import patch
import app as app_module

class ApiBaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app_module.app.testing = True
        cls.client = app_module.app.test_client()

    def test_health(self):
        resp = self.client.get('/health')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data.get('status'), 'ok')

    def test_price_missing_code(self):
        resp = self.client.get('/api/price')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.get_json().get('error'), 'Missing code')

    def test_prices_batch_missing_codes(self):
        resp = self.client.post('/api/prices/batch', json={})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.get_json().get('error'), 'Missing codes')

    def test_rates_mocked(self):
        with patch.object(app_module, 'get_forex_rates', return_value={'USD': 7.0}):
            resp = self.client.get('/api/rates')
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.get_json().get('USD'), 7.0)

    def test_price_mocked(self):
        with patch.object(app_module, 'get_price', return_value=(10, 9, 0, 0)):
            resp = self.client.get('/api/price?code=sh600000')
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertEqual(data.get('price'), 10)

    def test_prices_batch_mocked(self):
        with patch.object(app_module, 'batch_get_prices', return_value={'sh600000': (10, 9, 0, 0)}):
            resp = self.client.post('/api/prices/batch', json={'codes': ['sh600000']})
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertIn('sh600000', data)
            self.assertEqual(data['sh600000']['price'], 10)

if __name__ == '__main__':
    unittest.main()
```

**Step 2: Run test to verify it fails**
Run: `python -m unittest kona_tool/tests/test_api_baseline.py -v`
Expected: FAIL if tests missing

**Step 3: Write minimal implementation**
- Add test files; no production code change

**Step 4: Run test to verify it passes**
Run: `python -m unittest kona_tool/tests/test_api_baseline.py -v`
Expected: PASS

**Step 5: Commit**
```bash
git add kona_tool/tests/__init__.py kona_tool/tests/test_api_baseline.py
git commit -m "test: add backend baseline tests"
```

---

### Task 0.2: Frontend baseline test

**Files:**
- Create: `flutter/test/app_state_smoke_test.dart`

**Step 1: Write the failing test**
```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:tool/providers/app_state.dart';

void main() {
  test('AppState formatAmount hides when toggled', () {
    final state = AppState();
    final visible = state.formatAmount(1234, prefix: '¥');
    expect(visible, isNot('****'));

    state.toggleAmountHidden();
    final hidden = state.formatAmount(1234, prefix: '¥');
    expect(hidden, '****');
  });
}
```

**Step 2: Run test to verify it fails**
Run: `cd flutter && flutter test test/app_state_smoke_test.dart -r expanded`
Expected: FAIL if test missing

**Step 3: Write minimal implementation**
- Add test file; no production code change

**Step 4: Run test to verify it passes**
Run: `cd flutter && flutter test test/app_state_smoke_test.dart -r expanded`
Expected: PASS

**Step 5: Commit**
```bash
git add flutter/test/app_state_smoke_test.dart
git commit -m "test: add frontend baseline test"
```
