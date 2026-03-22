import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tool/providers/app_state.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  Future<AppState> buildStateWithCache({
    required Map<String, bool> openStatus,
    required double changeAmt,
    Map<String, bool>? tradingDayStatus,
    bool usExtendedActive = false,
    String usSession = 'regular',
    Map<String, double>? dayPnlAggregateCny,
    Map<String, double>? dayPnlBaseAggregateCny,
    Map<String, double>? valueCny,
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
            if (dayPnlAggregateCny?['sh600000'] != null)
              'day_pnl_aggregate_cny': dayPnlAggregateCny!['sh600000'],
            if (dayPnlBaseAggregateCny?['sh600000'] != null)
              'day_pnl_base_aggregate_cny':
                  dayPnlBaseAggregateCny!['sh600000'],
            if (valueCny?['sh600000'] != null)
              'value_cny': valueCny!['sh600000'],
          },
          {
            'code': 'hk00700',
            'name': '腾讯控股',
            'qty': 200,
            'price': 20,
            'curr': 'HKD',
            'adjustment': 0,
            if (dayPnlAggregateCny?['hk00700'] != null)
              'day_pnl_aggregate_cny': dayPnlAggregateCny!['hk00700'],
            if (dayPnlBaseAggregateCny?['hk00700'] != null)
              'day_pnl_base_aggregate_cny':
                  dayPnlBaseAggregateCny!['hk00700'],
            if (valueCny?['hk00700'] != null) 'value_cny': valueCny!['hk00700'],
          },
          {
            'code': 'gb_aapl',
            'name': 'Apple',
            'qty': 300,
            'price': 30,
            'curr': 'USD',
            'adjustment': 0,
            if (dayPnlAggregateCny?['gb_aapl'] != null)
              'day_pnl_aggregate_cny': dayPnlAggregateCny!['gb_aapl'],
            if (dayPnlBaseAggregateCny?['gb_aapl'] != null)
              'day_pnl_base_aggregate_cny':
                  dayPnlBaseAggregateCny!['gb_aapl'],
            if (valueCny?['gb_aapl'] != null) 'value_cny': valueCny!['gb_aapl'],
          },
          {
            'code': 'f_161725',
            'name': '招商中证白酒',
            'qty': 400,
            'price': 40,
            'curr': 'CNY',
            'adjustment': 0,
            if (dayPnlAggregateCny?['f_161725'] != null)
              'day_pnl_aggregate_cny': dayPnlAggregateCny!['f_161725'],
            if (dayPnlBaseAggregateCny?['f_161725'] != null)
              'day_pnl_base_aggregate_cny':
                  dayPnlBaseAggregateCny!['f_161725'],
            if (valueCny?['f_161725'] != null)
              'value_cny': valueCny!['f_161725'],
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
          'a': {
            'open': openStatus['a'] == true,
            if (tradingDayStatus != null)
              'trading_day': tradingDayStatus['a'] == true,
          },
          'hk': {
            'open': openStatus['hk'] == true,
            if (tradingDayStatus != null)
              'trading_day': tradingDayStatus['hk'] == true,
          },
          'us': {
            'open': openStatus['us'] == true,
            if (tradingDayStatus != null)
              'trading_day': tradingDayStatus['us'] == true,
          },
          'fund': {
            'open': openStatus['fund'] == true,
            if (tradingDayStatus != null)
              'trading_day': tradingDayStatus['fund'] == true,
          },
        },
      }),
    });

    final state = AppState();
    await state.hydrateFromCache();
    return state;
  }

  test('全部市场休市时 investDayPnl 应为 0', () async {
    final state = await buildStateWithCache(
      openStatus: const {'a': false, 'hk': false, 'us': false, 'fund': false},
      changeAmt: 1,
    );
    expect(state.investDayPnl, closeTo(0, 1e-6));
    expect(state.investDayPnlRate, closeTo(0, 1e-6));
  });

  test('A/Fund 休市且 HK/US 开市时，仅 HK+US 计入汇总', () async {
    final state = await buildStateWithCache(
      openStatus: const {'a': false, 'hk': true, 'us': true, 'fund': false},
      changeAmt: 1,
      dayPnlAggregateCny: const {'hk00700': 186, 'gb_aapl': 2175},
      dayPnlBaseAggregateCny: const {'hk00700': 20000, 'gb_aapl': 30000},
      valueCny: const {'hk00700': 20000, 'gb_aapl': 30000},
    );
    // hk: 1 * 200 * 0.93 = 186
    // us: 1 * 300 * 7.25 = 2175
    expect(state.investDayPnl, closeTo(2361, 1e-6));
    expect(state.investDayPnlRate, greaterThan(0));
  });

  test('全休市但 US 扩展时段活跃时，仅 US 计入汇总', () async {
    final state = await buildStateWithCache(
      openStatus: const {'a': false, 'hk': false, 'us': false, 'fund': false},
      changeAmt: 1,
      usExtendedActive: true,
      usSession: 'pre',
      dayPnlAggregateCny: const {'gb_aapl': 2175},
      dayPnlBaseAggregateCny: const {'gb_aapl': 30000},
      valueCny: const {'gb_aapl': 30000},
    );

    // us: 1 * 300 * 7.25 = 2175
    expect(state.investDayPnl, closeTo(2175, 1e-6));
    expect(state.investDayPnlRate, greaterThan(0));
  });

  test('休市市场单只仍允许显示冻结当日盈亏（但不计入汇总）', () async {
    final state = await buildStateWithCache(
      openStatus: const {'a': false, 'hk': true, 'us': true, 'fund': false},
      changeAmt: 1,
    );
    final aItem = state.portfolio.firstWhere((e) => e.code == 'sh600000');
    final aPrice = state.resolvePriceInfoByCode(aItem.code);
    expect(aPrice, isNotNull);
    expect(state.isAssetDayPnlDisplayEnabled(aItem, priceInfo: aPrice), isTrue);
    expect(state.isAssetDayPnlEnabled(aItem, priceInfo: aPrice), isFalse);
  });

  test('交易日午休/盘后（open=false, trading_day=true）仍计入当日汇总', () async {
    final state = await buildStateWithCache(
      openStatus: const {'a': false, 'hk': false, 'us': false, 'fund': false},
      tradingDayStatus: const {
        'a': false,
        'hk': true,
        'us': false,
        'fund': false,
      },
      changeAmt: 1,
      dayPnlAggregateCny: const {'hk00700': 186},
      dayPnlBaseAggregateCny: const {'hk00700': 20000},
      valueCny: const {'hk00700': 20000},
    );

    // hk: 1 * 200 * 0.93 = 186
    expect(state.investDayPnl, closeTo(186, 1e-6));
    final hkItem = state.portfolio.firstWhere((e) => e.code == 'hk00700');
    final hkPrice = state.resolvePriceInfoByCode(hkItem.code);
    expect(state.isAssetMarketOpen(hkItem), isFalse);
    expect(state.isAssetTradingDay(hkItem), isTrue);
    expect(state.isAssetDayPnlEnabled(hkItem, priceInfo: hkPrice), isTrue);
  });
}
