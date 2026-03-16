import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tool/models/asset.dart';
import 'package:tool/models/asset_action_result.dart';
import 'package:tool/providers/app_assets_state.dart';
import 'package:tool/providers/app_home_totals_state.dart';
import 'package:tool/providers/app_investment_write_state.dart';
import 'package:tool/providers/app_market_state.dart';
import 'package:tool/providers/app_portfolio_view_state.dart';
import 'package:tool/providers/app_preferences_state.dart';
import 'package:tool/providers/app_sync_state.dart';
import 'package:tool/providers/app_trade_state.dart';
import 'package:tool/services/api_service.dart';
import 'package:tool/services/cache_service.dart';

class _FakeInvestmentApiService implements ApiService {
  _FakeInvestmentApiService({this.failBuyWithCash = false});

  final bool failBuyWithCash;

  @override
  Future<AssetActionResult> buyPortfolioAssetWithCash(
    String code,
    String name,
    double price,
    double qty, {
    required int cashAssetId,
    String? curr,
    String? assetType,
    String? requestId,
  }) async {
    if (failBuyWithCash) {
      return const AssetActionResult.failure('买入失败');
    }
    return const AssetActionResult.success(
      data: {'undo_token': 'undo-1', 'undo_expire_at': '2099-01-01T00:00:00Z'},
    );
  }

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  AppHomeTotalsState buildHomeTotals({
    required ApiService api,
    required AppAssetsState assetsState,
  }) {
    final marketState = AppMarketState();
    final preferencesState = AppPreferencesState(cache: CacheService());
    final syncState = AppSyncState(cache: CacheService());
    final portfolioViewState = AppPortfolioViewState(
      api: api,
      assetsState: assetsState,
      marketState: marketState,
      preferencesState: preferencesState,
      syncState: syncState,
    );
    return AppHomeTotalsState(
      assetsState: assetsState,
      marketState: marketState,
      portfolioViewState: portfolioViewState,
    );
  }

  AppInvestmentWriteState buildState({
    required ApiService api,
    required AppAssetsState assetsState,
    required AppHomeTotalsState homeTotalsState,
  }) {
    return AppInvestmentWriteState(
      api: api,
      assetsState: assetsState,
      homeTotalsState: homeTotalsState,
      tradeState: AppTradeState(api: api),
    );
  }

  test('AppInvestmentWriteState buyInvestmentWithCash 成功时同步更新现金和持仓', () async {
    final api = _FakeInvestmentApiService();
    final assetsState = AppAssetsState();
    assetsState.replaceCashAssets([
      Asset(id: 1, name: '主账户', amount: 1000, curr: 'CNY'),
    ], notify: false);
    final homeTotalsState = buildHomeTotals(api: api, assetsState: assetsState);
    homeTotalsState.recalculateHomeTotals(notify: false);
    final state = buildState(
      api: api,
      assetsState: assetsState,
      homeTotalsState: homeTotalsState,
    );

    var notifyCount = 0;
    var refreshCalled = false;

    final result = await state.buyInvestmentWithCash(
      code: 'sh600000',
      name: '浦发银行',
      price: 10,
      qty: 10,
      cashAssetId: 1,
      awaitRefresh: false,
      bindings: AppInvestmentWriteBindings(
        notifyListeners: () => notifyCount += 1,
        triggerHomeRefresh: (awaitRefresh) async {
          refreshCalled = true;
          expect(awaitRefresh, isFalse);
        },
        normalizeInvestmentCurrency: ({required code, String? curr}) =>
            curr ?? 'CNY',
        rateForCurrency: (_) => 1,
      ),
    );

    expect(result.ok, isTrue);
    expect(result.data?['undo_token'], 'undo-1');
    expect(assetsState.portfolio, hasLength(1));
    expect(assetsState.portfolio.first.code, 'sh600000');
    expect(assetsState.cashAssets.first.amount, 900);
    expect(homeTotalsState.totalCash, 900);
    expect(homeTotalsState.totalInvest, 0);
    expect(homeTotalsState.totalAsset, 900);
    expect(refreshCalled, isTrue);
    expect(notifyCount, greaterThan(0));
  });

  test('AppInvestmentWriteState buyInvestmentWithCash 失败时回滚现金和持仓', () async {
    final api = _FakeInvestmentApiService(failBuyWithCash: true);
    final assetsState = AppAssetsState();
    assetsState.replaceCashAssets([
      Asset(id: 1, name: '主账户', amount: 1000, curr: 'CNY'),
    ], notify: false);
    final homeTotalsState = buildHomeTotals(api: api, assetsState: assetsState);
    homeTotalsState.recalculateHomeTotals(notify: false);
    final state = buildState(
      api: api,
      assetsState: assetsState,
      homeTotalsState: homeTotalsState,
    );

    var refreshCalled = false;

    final result = await state.buyInvestmentWithCash(
      code: 'sh600000',
      name: '浦发银行',
      price: 10,
      qty: 10,
      cashAssetId: 1,
      awaitRefresh: false,
      bindings: AppInvestmentWriteBindings(
        notifyListeners: () {},
        triggerHomeRefresh: (_) async {
          refreshCalled = true;
        },
        normalizeInvestmentCurrency: ({required code, String? curr}) =>
            curr ?? 'CNY',
        rateForCurrency: (_) => 1,
      ),
    );

    expect(result.ok, isFalse);
    expect(assetsState.portfolio, isEmpty);
    expect(assetsState.cashAssets.first.amount, 1000);
    expect(homeTotalsState.totalCash, 1000);
    expect(homeTotalsState.totalInvest, 0);
    expect(homeTotalsState.totalAsset, 1000);
    expect(refreshCalled, isFalse);
  });
}
