import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tool/models/asset_action_result.dart';
import 'package:tool/providers/app_state.dart';
import 'package:tool/services/api_service.dart';

class _NoRefreshAppState extends AppState {
  _NoRefreshAppState({required ApiService api})
    : super(api: api, tokenLoader: () async => null);

  @override
  Future<void> refreshHomeData() async {}
}

class _FakeApiService implements ApiService {
  void Function()? _onAuthExpired;

  @override
  void Function()? get onAuthExpired => _onAuthExpired;

  @override
  set onAuthExpired(void Function()? value) {
    _onAuthExpired = value;
  }

  @override
  void setToken(String token) {}

  @override
  void clearToken() {}

  @override
  Future<AssetActionResult> addPortfolioAsset(
    String code,
    String name,
    double price,
    double qty, {
    String? curr,
    String? assetType,
    String? requestId,
  }) async {
    return const AssetActionResult.success(data: {'status': 'ok'});
  }

  @override
  Future<AssetActionResult> modifyPortfolioAsset(
    String code,
    double qty,
    double price,
    double adjustment, {
    String? requestId,
  }) async {
    return const AssetActionResult.success(data: {'status': 'ok'});
  }

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  test('AppState formatAmount hides when toggled', () {
    final state = AppState();
    final visible = state.formatAmount(1234, prefix: '¥');
    expect(visible, isNot('****'));

    state.toggleAmountHidden();
    final hidden = state.formatAmount(1234, prefix: '¥');
    expect(hidden, '****');
  });

  test(
    'AppState investment actions return failure when holding missing',
    () async {
      final state = AppState();

      final buyResult = await state.buyInvestment(
        code: 'sh600000',
        price: 10,
        qty: 1,
        awaitRefresh: false,
      );
      expect(buyResult.ok, isFalse);

      final sellResult = await state.sellInvestment(
        code: 'sh600000',
        price: 10,
        qty: 1,
        awaitRefresh: false,
      );
      expect(sellResult.ok, isFalse);

      final sellToCashResult = await state.sellInvestmentToCash(
        code: 'sh600000',
        price: 10,
        qty: 1,
        cashAssetId: 1,
        awaitRefresh: false,
      );
      expect(sellToCashResult.ok, isFalse);

      final deleteResult = await state.deleteInvestment(
        code: 'sh600000',
        awaitRefresh: false,
      );
      expect(deleteResult.ok, isFalse);

      final buyWithCashResult = await state.buyInvestmentWithCash(
        code: 'sh600000',
        name: '浦发银行',
        price: 10,
        qty: 1,
        cashAssetId: 1,
        awaitRefresh: false,
      );
      expect(buyWithCashResult.ok, isFalse);
    },
  );

  test('AppState normalizeInvestmentCurrency infers market currency first', () {
    final state = AppState();
    expect(state.normalizeInvestmentCurrency(code: 'goog', curr: 'CNY'), 'USD');
    expect(
      state.normalizeInvestmentCurrency(code: 'gb_goog', curr: 'CNY'),
      'USD',
    );
    expect(
      state.normalizeInvestmentCurrency(code: '00700.HK', curr: 'CNY'),
      'HKD',
    );
    expect(
      state.normalizeInvestmentCurrency(code: 'sh600000', curr: 'USD'),
      'CNY',
    );
    expect(
      state.normalizeInvestmentCurrency(code: 'sh900901', curr: 'CNY'),
      'USD',
    );
    expect(
      state.normalizeInvestmentCurrency(code: 'sz200002', curr: 'CNY'),
      'HKD',
    );
  });

  test(
    'AppState setCategory filters portfolio without changing public API',
    () async {
      final api = _FakeApiService();
      final state = _NoRefreshAppState(api: api);

      final cnResult = await state.addInvestment(
        code: 'sh600000',
        name: '浦发银行',
        price: 10,
        qty: 1,
        curr: 'CNY',
        assetType: 'a',
        awaitRefresh: false,
      );
      final usResult = await state.addInvestment(
        code: 'gb_tsla',
        name: 'Tesla',
        price: 20,
        qty: 2,
        curr: 'USD',
        assetType: 'us',
        awaitRefresh: false,
      );

      expect(cnResult.ok, isTrue);
      expect(usResult.ok, isTrue);
      expect(state.filteredPortfolio.length, 2);

      state.setCategory('us');

      expect(state.currentCategory, 'us');
      expect(state.filteredPortfolio.map((item) => item.code), ['gb_tsla']);
    },
  );

  test('AppState applyOverviewMilestones overrides month/year by收益口径', () {
    final state = AppState();
    state.applyOverviewMilestones({
      'month': {'pnl': 88.5},
      'year': {'pnl': -12.0},
    });
    expect(state.monthChange, 88.5);
    expect(state.yearChange, -12.0);
    expect(state.overviewMilestonesReady, isTrue);
  });

  test(
    'AppState applyOverviewMilestones marks unready when payload invalid',
    () {
      final state = AppState();
      state.applyOverviewMilestones(const {});
      expect(state.overviewMilestonesReady, isFalse);
    },
  );

  test(
    'AppState negative cost fallback keeps pnl rate at 0 without metrics',
    () async {
      final api = _FakeApiService();
      final state = _NoRefreshAppState(api: api);
      final addResult = await state.addInvestment(
        code: 'gb_tsla',
        name: 'Tesla',
        price: 2,
        qty: 10,
        curr: 'USD',
        assetType: 'us',
        awaitRefresh: false,
      );
      expect(addResult.ok, isTrue);

      final modifyResult = await state.modifyInvestment(
        code: 'gb_tsla',
        qty: 10,
        price: -2,
        adjustment: 0,
        awaitRefresh: false,
      );
      expect(modifyResult.ok, isTrue);

      expect(state.investTotalMV, 0);
      expect(state.investHoldingPnlRate, 0);
    },
  );
}
