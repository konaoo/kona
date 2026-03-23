import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tool/models/asset.dart';
import 'package:tool/models/portfolio.dart';
import 'package:tool/providers/app_market_state.dart';
import 'package:tool/providers/app_overview_state.dart';
import 'package:tool/providers/app_refresh_state.dart';
import 'package:tool/providers/app_sync_state.dart';
import 'package:tool/services/api_service.dart';
import 'package:tool/services/cache_service.dart';

class _RefreshHarness {
  final AppSyncState syncState = AppSyncState(cache: CacheService());
  final AppMarketState marketState = AppMarketState();
  final AppOverviewState overviewState = AppOverviewState();

  List<PortfolioItem> portfolio = <PortfolioItem>[];
  List<Asset> cashAssets = <Asset>[];
  List<Asset> otherAssets = <Asset>[];
  List<Asset> liabilities = <Asset>[];
  Map<String, PriceInfo> prices = <String, PriceInfo>{};
  Map<String, PriceInfo> priceSnapshots = <String, PriceInfo>{};

  double totalCash = 0;
  double totalOther = 0;
  double totalLiability = 0;
  double totalInvest = 0;
  double totalAsset = 0;
  bool portfolioLoaded = false;
  int notifyCount = 0;

  void recalculateHomeTotals() {
    totalCash = _sumAssetListToCny(cashAssets);
    totalOther = _sumAssetListToCny(otherAssets);
    totalLiability = _sumAssetListToCny(liabilities, useAbs: true);
    totalInvest = portfolio.fold(0, (sum, item) {
      final priceInfo = resolvePriceInfoByCode(item.code);
      final resolvedPrice = priceInfo?.price ?? item.price;
      return sum +
          marketState.convertToCny(resolvedPrice * item.qty, item.curr);
    });
    totalAsset = totalCash + totalInvest + totalOther - totalLiability;
    portfolioLoaded = portfolio.isNotEmpty || cashAssets.isNotEmpty;
  }

  double _sumAssetListToCny(List<Asset> items, {bool useAbs = false}) {
    return items.fold(0, (sum, item) {
      final amount = useAbs ? item.amount.abs() : item.amount;
      return sum + marketState.convertToCny(amount, item.curr);
    });
  }

  PriceInfo? resolvePriceInfoByCode(
    String code, {
    PriceInfo? preferred,
    Map<String, PriceInfo>? runtimeFallback,
  }) {
    return preferred ??
        prices[code] ??
        runtimeFallback?[code] ??
        priceSnapshots[code];
  }

  Future<ParsedMarketStatus> loadMarketStatusWithBudget() async {
    return marketState.currentMarketStatusSnapshot();
  }

  void notifyListeners() {
    notifyCount += 1;
  }

  AppRefreshBindings buildBindings() {
    return AppRefreshBindings(
      username: () => null,
      userId: () => null,
      currentLedgerId: () => null,
      syncState: syncState,
      syncVersions: () => syncState.syncVersions,
      portfolio: () => portfolio,
      replacePortfolio: (value) => portfolio = value,
      cashAssets: () => cashAssets,
      replaceCashAssets: (value) => cashAssets = value,
      otherAssets: () => otherAssets,
      replaceOtherAssets: (value) => otherAssets = value,
      liabilities: () => liabilities,
      replaceLiabilities: (value) => liabilities = value,
      prices: () => prices,
      replacePrices: (value) => prices = value,
      priceSnapshots: () => priceSnapshots,
      replacePriceSnapshots: (value) => priceSnapshots = value,
      portfolioLoaded: () => portfolioLoaded,
      setPortfolioLoaded: (value) => portfolioLoaded = value,
      exchangeRates: () => marketState.exchangeRates,
      recalculateHomeTotals: recalculateHomeTotals,
      calculateHistoryStats: (history) =>
          overviewState.calculateHistoryStats(history, notify: false),
      applyOverviewMilestones: (overview) =>
          overviewState.applyOverviewMilestones(overview, notify: false),
      updateExchangeRates: (rates) =>
          marketState.updateExchangeRates(rates, notify: false),
      applySyncMarketStatus: (rawStatuses, {rawOpenFallback}) =>
          marketState.applySyncMarketStatus(
            rawStatuses,
            rawOpenFallback: rawOpenFallback,
            notify: false,
          ),
      serializeMarketStatusForCache: marketState.serializeMarketStatusForCache,
      loadMarketStatusWithBudget: loadMarketStatusWithBudget,
      resolvePriceInfoByCode: resolvePriceInfoByCode,
      notifyListeners: notifyListeners,
    );
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  AppRefreshState buildState() {
    return AppRefreshState(
      api: ApiService(),
      staticDataTtl: const Duration(minutes: 5),
      historyDataTtl: const Duration(minutes: 10),
      ratesDataTtl: const Duration(minutes: 10),
      syncVersionTtl: const Duration(days: 365),
      priceRefreshMinInterval: const Duration(seconds: 2),
      syncBootstrapDomains: const <String>[
        'portfolio',
        'cash_assets',
        'other_assets',
        'liabilities',
        'history',
        'overview_all',
        'rates',
      ],
    );
  }

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  test('AppRefreshState 从缓存恢复首页和价格数据', () async {
    SharedPreferences.setMockInitialValues({
      'cache_portfolio': jsonEncode({
        'items': [
          {
            'code': 'sh600000',
            'name': '浦发银行',
            'qty': 1,
            'price': 10,
            'curr': 'CNY',
            'adjustment': 0,
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

    final harness = _RefreshHarness();
    final state = buildState();

    await state.hydrateFromCache(bindings: harness.buildBindings());

    expect(harness.portfolioLoaded, true);
    expect(harness.portfolio.first.code, 'sh600000');
    expect(harness.totalCash, 5);
    expect(harness.totalOther, 2);
    expect(harness.totalLiability, 1);
    expect(harness.totalInvest, 11);
    expect(harness.totalAsset, 17);
    expect(harness.marketState.exchangeRates['USD'], 8.0);
    expect(harness.prices['sh600000']?.price, 11);
    expect(harness.notifyCount, greaterThan(0));
  });

  test('AppRefreshState 保存首页缓存并同步版本缓存', () async {
    final harness = _RefreshHarness();
    harness.portfolio = <PortfolioItem>[
      PortfolioItem(
        code: 'sh600000',
        name: '浦发银行',
        qty: 2,
        price: 10,
        curr: 'CNY',
      ),
    ];
    harness.cashAssets = <Asset>[
      Asset(id: 1, name: '现金', amount: 100, curr: 'CNY'),
    ];
    harness.prices = <String, PriceInfo>{
      'sh600000': PriceInfo(price: 11, yclose: 10, change: 1, changePct: 10),
    };
    harness.priceSnapshots = Map<String, PriceInfo>.from(harness.prices);
    harness.syncState.syncVersions['portfolio'] = 'v1';
    harness.syncState.syncVersions['history'] = 'v2';
    harness.recalculateHomeTotals();

    final state = buildState();
    await state.saveHomeCache(
      bindings: harness.buildBindings(),
      history: const <dynamic>[],
      overview: {
        'month': {'pnl': 12},
      },
    );

    final prefs = await SharedPreferences.getInstance();
    expect(prefs.getString('u:guest:portfolio'), isNotNull);
    expect(prefs.getString('u:guest:cash_assets'), isNotNull);
    expect(prefs.getString('u:guest:history'), isNotNull);
    expect(prefs.getString('u:guest:prices'), isNotNull);
    expect(prefs.getString('u:guest:price_snapshots'), isNotNull);
    expect(prefs.getString('u:guest:market_status'), isNotNull);
    expect(prefs.getString('u:guest:sync_versions'), isNotNull);
    expect(prefs.getString('u:guest:analysis_overview'), isNotNull);
  });
}
