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
            'adjustment': 0
          }
        ]
      }),
      'cache_cash_assets': jsonEncode({
        'items': [
          {'id': 1, 'name': '现金', 'amount': 5, 'curr': 'CNY'}
        ]
      }),
      'cache_other_assets': jsonEncode({
        'items': [
          {'id': 2, 'name': '其他', 'amount': 2, 'curr': 'CNY'}
        ]
      }),
      'cache_liabilities': jsonEncode({
        'items': [
          {'id': 3, 'name': '负债', 'amount': 1, 'curr': 'CNY'}
        ]
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
            'updated_at': '2026-01-01'
          }
        ]
      }),
      'cache_exchange_rates': jsonEncode({
        'rates': {'USD': 8.0, 'HKD': 1.0, 'CNY': 1.0}
      }),
      'cache_prices': jsonEncode({
        'items': {
          'sh600000': {'price': 11, 'yclose': 10, 'chg': 1}
        }
      })
    });

    final state = AppState();
    await state.hydrateFromCache();

    expect(state.portfolioLoaded, true);
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

    expect(prefs.getString('cache_portfolio'), isNotNull);
    expect(prefs.getString('cache_cash_assets'), isNotNull);
    expect(prefs.getString('cache_other_assets'), isNotNull);
    expect(prefs.getString('cache_liabilities'), isNotNull);
    expect(prefs.getString('cache_history'), isNotNull);
    expect(prefs.getString('cache_exchange_rates'), isNotNull);
    expect(prefs.getString('cache_prices'), isNotNull);
  });
}
