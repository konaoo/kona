import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tool/models/asset_action_result.dart';
import 'package:tool/providers/app_asset_write_state.dart';
import 'package:tool/providers/app_assets_state.dart';
import 'package:tool/providers/app_home_totals_state.dart';
import 'package:tool/providers/app_market_state.dart';
import 'package:tool/providers/app_portfolio_view_state.dart';
import 'package:tool/providers/app_preferences_state.dart';
import 'package:tool/providers/app_sync_state.dart';
import 'package:tool/services/api_service.dart';
import 'package:tool/services/cache_service.dart';

class _FakeAssetApiService implements ApiService {
  _FakeAssetApiService({this.failAddCash = false});

  final bool failAddCash;

  @override
  Future<AssetActionResult> addCashAsset(
    String name,
    double amount, {
    String? curr,
  }) async {
    if (failAddCash) {
      return const AssetActionResult.failure('新增现金资产失败');
    }
    return const AssetActionResult.success();
  }

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  AppAssetWriteState buildState({
    required ApiService api,
    required AppAssetsState assetsState,
    required AppHomeTotalsState homeTotalsState,
  }) {
    return AppAssetWriteState(
      api: api,
      assetsState: assetsState,
      homeTotalsState: homeTotalsState,
    );
  }

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

  test('AppAssetWriteState addAsset 成功后更新首页总额并触发刷新', () async {
    final api = _FakeAssetApiService();
    final assetsState = AppAssetsState();
    final homeTotalsState = buildHomeTotals(api: api, assetsState: assetsState);
    final state = buildState(
      api: api,
      assetsState: assetsState,
      homeTotalsState: homeTotalsState,
    );

    var notifyCount = 0;
    var refreshCalled = false;

    final result = await state.addAsset(
      type: 'cash',
      name: '现金账户',
      amount: 100,
      curr: 'CNY',
      awaitRefresh: false,
      bindings: AppAssetWriteBindings(
        notifyListeners: () => notifyCount += 1,
        triggerHomeRefresh: (awaitRefresh) async {
          refreshCalled = true;
          expect(awaitRefresh, isFalse);
        },
      ),
    );

    expect(result.ok, isTrue);
    expect(assetsState.cashAssets, hasLength(1));
    expect(homeTotalsState.totalCash, 100);
    expect(homeTotalsState.totalAsset, 100);
    expect(refreshCalled, isTrue);
    expect(notifyCount, greaterThan(0));
  });

  test('AppAssetWriteState addAsset 失败时回滚列表和首页总额', () async {
    final api = _FakeAssetApiService(failAddCash: true);
    final assetsState = AppAssetsState();
    final homeTotalsState = buildHomeTotals(api: api, assetsState: assetsState);
    final state = buildState(
      api: api,
      assetsState: assetsState,
      homeTotalsState: homeTotalsState,
    );

    var refreshCalled = false;

    final result = await state.addAsset(
      type: 'cash',
      name: '现金账户',
      amount: 100,
      curr: 'CNY',
      bindings: AppAssetWriteBindings(
        notifyListeners: () {},
        triggerHomeRefresh: (_) async {
          refreshCalled = true;
        },
      ),
    );

    expect(result.ok, isFalse);
    expect(assetsState.cashAssets, isEmpty);
    expect(homeTotalsState.totalCash, 0);
    expect(homeTotalsState.totalAsset, 0);
    expect(refreshCalled, isFalse);
  });
}
