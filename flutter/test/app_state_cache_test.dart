import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tool/providers/app_state.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('AppState hydrates home data from cache', () async {
    SharedPreferences.setMockInitialValues({
      'cache_portfolio': jsonEncode({
        'items': [
          {
            'code': 'sh600000',
            'name': 'X',
            'qty': 1,
            'price': 10,
            'curr': 'CNY',
            'adjustment': 0,
            'value_cny': 11,
            'cost_cny': 10,
          },
        ],
      }),
      'cache_cash_assets': jsonEncode({
        'items': [
          {'id': 1, 'name': '现金', 'amount': 5, 'curr': 'CNY'},
        ],
      }),
      'cache_other_assets': jsonEncode({
        'items': [
          {'id': 2, 'name': '其他', 'amount': 2, 'curr': 'CNY'},
        ],
      }),
      'cache_liabilities': jsonEncode({
        'items': [
          {'id': 3, 'name': '负债', 'amount': 1, 'curr': 'CNY'},
        ],
      }),
      'cache_history': jsonEncode({
        'items': [
          {
            'date': '2026-01-01',
            'total_asset': 10,
            'total_invest': 10,
            'total_cash': 0,
            'total_other': 0,
            'total_liability': 0,
            'total_pnl': 0,
            'day_pnl': 0,
            'updated_at': '2026-01-01',
          },
        ],
      }),
      'cache_exchange_rates': jsonEncode({
        'rates': {'USD': 8.0, 'HKD': 1.0, 'CNY': 1.0},
      }),
      'cache_prices': jsonEncode({
        'items': {
          'sh600000': {'price': 11, 'yclose': 10, 'chg': 1},
        },
      }),
    });

    final state = AppState();
    await state.hydrateFromCache();

    expect(state.portfolioLoaded, true);
    expect(state.lastHydrateResult?.ok, isTrue);
    expect(state.lastHydrateResult?.stage, 'cache-restored');
    expect(state.portfolio.first.code, 'sh600000');
    expect(state.totalCash, 5);
    expect(state.totalOther, 2);
    expect(state.totalLiability, 1);
    expect(state.totalInvest, 11);
    expect(state.totalAsset, 17);
    expect(state.exchangeRates['USD'], 8.0);
    expect(state.prices['sh600000']?.price, 11);
  });

  test('AppState saves home cache', () async {
    SharedPreferences.setMockInitialValues({});
    final state = AppState();

    await state.saveHomeCache([]);
    final prefs = await SharedPreferences.getInstance();

    expect(prefs.getString('u:guest:portfolio'), isNotNull);
    expect(prefs.getString('u:guest:cash_assets'), isNotNull);
    expect(prefs.getString('u:guest:other_assets'), isNotNull);
    expect(prefs.getString('u:guest:liabilities'), isNotNull);
    expect(prefs.getString('u:guest:history'), isNotNull);
    expect(prefs.getString('u:guest:exchange_rates'), isNotNull);
    expect(prefs.getString('u:guest:prices'), isNotNull);
  });

  test('AppState converts non-CNY cash and liability totals to CNY', () async {
    SharedPreferences.setMockInitialValues({
      'cache_cash_assets': jsonEncode({
        'items': [
          {'id': 1, 'name': '港币账户', 'amount': 100, 'curr': 'HKD'},
        ],
      }),
      'cache_other_assets': jsonEncode({
        'items': [
          {'id': 2, 'name': '美元资产', 'amount': 10, 'curr': 'USD'},
        ],
      }),
      'cache_liabilities': jsonEncode({
        'items': [
          {'id': 3, 'name': '美元负债', 'amount': 5, 'curr': 'USD'},
        ],
      }),
      'cache_exchange_rates': jsonEncode({
        'rates': {'USD': 7.0, 'HKD': 0.88, 'CNY': 1.0},
      }),
    });

    final state = AppState();
    await state.hydrateFromCache();

    expect(state.totalCash, 88);
    expect(state.totalOther, 70);
    expect(state.totalLiability, 35);
    expect(state.totalAsset, 123);
    expect(state.lastHydrateResult?.ok, isTrue);
  });
}
