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
          'gb_aapl': {'price': 31, 'yclose': 30, 'amt': changeAmt, 'chg': 3.33},
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

  test('全部市场休市时 investDayPnl 应为 0', () async {
    final state = await _buildStateWithCache(
      openStatus: const {'a': false, 'hk': false, 'us': false, 'fund': false},
      changeAmt: 1,
    );
    expect(state.investDayPnl, 0);
    expect(state.investDayPnlRate, 0);
  });

  test('仅开市市场计入当日盈亏（A/HK/US/Fund 全量覆盖）', () async {
    final state = await _buildStateWithCache(
      openStatus: const {'a': false, 'hk': true, 'us': true, 'fund': false},
      changeAmt: 1,
    );

    // hk: 1 * 200 * 0.93 = 186
    // us: 1 * 300 * 7.25 = 2175
    expect(state.investDayPnl, closeTo(2361, 1e-6));
  });
}
