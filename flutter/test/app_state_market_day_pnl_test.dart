import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tool/providers/app_state.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  Future<AppState> _buildStateWithCache({
    required Map<String, bool> openStatus,
    required double changeAmt,
    bool usExtendedActive = false,
    String usSession = 'regular',
  }) async {
    SharedPreferences.setMockInitialValues({
      'cache_portfolio': jsonEncode({
        'items': [
          {
            'code': 'sh600000',
            'name': '浦发银行',
            'qty': 100,
            'price': 10,
            'curr': 'CNY',
            'adjustment': 0,
          },
          {
            'code': 'hk00700',
            'name': '腾讯控股',
            'qty': 200,
            'price': 20,
            'curr': 'HKD',
            'adjustment': 0,
          },
          {
            'code': 'gb_aapl',
            'name': 'Apple',
            'qty': 300,
            'price': 30,
            'curr': 'USD',
            'adjustment': 0,
          },
          {
            'code': 'f_161725',
            'name': '招商中证白酒',
            'qty': 400,
            'price': 40,
            'curr': 'CNY',
            'adjustment': 0,
          },
        ],
      }),
      'cache_prices': jsonEncode({
        'items': {
          'sh600000': {'price': 11, 'yclose': 10, 'amt': changeAmt, 'chg': 10},
          'hk00700': {'price': 21, 'yclose': 20, 'amt': changeAmt, 'chg': 5},
          'gb_aapl': {
            'price': 31,
            'yclose': 30,
            'amt': changeAmt,
            'chg': 3.33,
            'session': usSession,
            'extended_active': usExtendedActive,
          },
          'f_161725': {'price': 41, 'yclose': 40, 'amt': changeAmt, 'chg': 2.5},
        },
      }),
      'cache_market_status': jsonEncode({
        'markets': {
          'a': {'open': openStatus['a'] == true},
          'hk': {'open': openStatus['hk'] == true},
          'us': {'open': openStatus['us'] == true},
          'fund': {'open': openStatus['fund'] == true},
        },
      }),
    });

    final state = AppState();
    await state.hydrateFromCache();
    return state;
  }

  test('全部市场休市时 investDayPnl 仍保留冻结值', () async {
    final state = await _buildStateWithCache(
      openStatus: const {'a': false, 'hk': false, 'us': false, 'fund': false},
      changeAmt: 1,
    );
    // a: 1 * 100 * 1 = 100
    // hk: 1 * 200 * 0.93 = 186
    // us: 1 * 300 * 7.25 = 2175
    // fund: 1 * 400 * 1 = 400
    expect(state.investDayPnl, closeTo(2861, 1e-6));
    expect(state.investDayPnlRate, greaterThan(0));
  });

  test('开休市切换不影响冻结当日盈亏展示', () async {
    final state = await _buildStateWithCache(
      openStatus: const {'a': false, 'hk': true, 'us': true, 'fund': false},
      changeAmt: 1,
    );
    expect(state.investDayPnl, closeTo(2861, 1e-6));
  });

  test('美股扩展时段活跃时仍按冻结口径展示当日盈亏', () async {
    final state = await _buildStateWithCache(
      openStatus: const {'a': false, 'hk': false, 'us': false, 'fund': false},
      changeAmt: 1,
      usExtendedActive: true,
      usSession: 'pre',
    );

    expect(state.investDayPnl, closeTo(2861, 1e-6));
    expect(state.investDayPnlRate, greaterThan(0));
  });
}
