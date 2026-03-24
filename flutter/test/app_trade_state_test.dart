import 'package:flutter_test/flutter_test.dart';
import 'package:tool/models/asset.dart';
import 'package:tool/models/asset_action_result.dart';
import 'package:tool/providers/app_trade_state.dart';
import 'package:tool/services/api_service.dart';

class _TradeApiStub implements ApiService {
  AssetActionResult buyResult = const AssetActionResult.success();
  AssetActionResult sellResult = const AssetActionResult.success();
  AssetActionResult updateCashResult = const AssetActionResult.success();

  @override
  Future<AssetActionResult> buyPortfolioAsset(
    String code,
    double price,
    double qty, {
    String? requestId,
    int? ledgerId,
  }) async {
    return buyResult;
  }

  @override
  Future<AssetActionResult> sellPortfolioAsset(
    String code,
    double price,
    double qty, {
    String? requestId,
    int? ledgerId,
  }) async {
    return sellResult;
  }

  @override
  Future<AssetActionResult> updateCashAsset(
    int id,
    String name,
    double amount, {
    String? curr,
  }) async {
    return updateCashResult;
  }

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('AppTradeState converts amount by currency and extracts undo info', () {
    final state = AppTradeState(api: _TradeApiStub());

    final converted = state.convertAmountByCurrency(
      amount: 100,
      fromCurr: 'USD',
      toCurr: 'HKD',
      rateForCurrency: (curr) => switch (curr) {
        'USD' => 7.2,
        'HKD' => 0.9,
        _ => 1.0,
      },
    );

    expect(converted, 800);

    final extracted = state.extractUndoInfo(
      const AssetActionResult.success(
        data: {'undo_token': 'undo-1', 'undo_expire_at': '2026-03-14T10:00:00'},
      ),
    );

    expect(extracted.ok, isTrue);
    expect(extracted.data?['undo_token'], 'undo-1');
    expect(extracted.data?['undo_expire_at'], '2026-03-14T10:00:00');
  });

  test(
    'AppTradeState legacy buy fallback reports invalid cash account',
    () async {
      final api = _TradeApiStub();
      final state = AppTradeState(api: api);

      final result = await state.legacyBuyWithCashFallback(
        code: 'AAPL',
        name: 'Apple',
        price: 100,
        qty: 1,
        cashAsset: Asset(id: 0, name: '现金', amount: 1000, curr: 'USD'),
        cashDeductAmount: 100,
      );

      expect(result.ok, isFalse);
      expect(result.message, '现金账户无效，请稍后重试');
    },
  );
}
