import 'package:flutter_test/flutter_test.dart';
import 'package:tool/providers/app_assets_state.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('AppAssetsState manages non-investment assets optimistically', () {
    final state = AppAssetsState();

    final added = state.optimisticAddAsset(
      type: 'cash',
      name: '港股账户',
      amount: 1000,
      curr: 'hkd',
      notify: false,
    );

    expect(added, isTrue);
    expect(state.cashAssets, hasLength(1));
    expect(state.cashAssets.first.curr, 'HKD');

    final assetId = state.cashAssets.first.id!;
    final updated = state.optimisticUpdateAsset(
      type: 'cash',
      id: assetId,
      name: '港股主账户',
      amount: 1200,
      curr: 'usd',
      notify: false,
    );

    expect(updated, isTrue);
    expect(state.cashAssets.first.name, '港股主账户');
    expect(state.cashAssets.first.amount, 1200);
    expect(state.cashAssets.first.curr, 'USD');

    final deleted = state.optimisticDeleteAsset(
      type: 'cash',
      id: assetId,
      notify: false,
    );

    expect(deleted, isTrue);
    expect(state.cashAssets, isEmpty);
  });

  test('AppAssetsState manages investment holdings optimistically', () {
    final state = AppAssetsState();

    state.optimisticAddInvestment(
      code: 'AAPL',
      name: 'Apple',
      price: 100,
      qty: 2,
      normalizedCurr: 'USD',
      notify: false,
    );
    state.optimisticBuyInvestment(
      code: 'AAPL',
      price: 200,
      qty: 1,
      notify: false,
    );

    final holding = state.portfolio.single;
    expect(holding.qty, 3);
    expect(holding.price, closeTo(133.3333, 0.0001));

    state.optimisticSellInvestment(
      code: 'AAPL',
      price: 300,
      qty: 1,
      notify: false,
    );
    state.optimisticModifyInvestment(
      code: 'AAPL',
      qty: 2,
      price: 120,
      adjustment: 66.6,
      notify: false,
    );

    final modified = state.portfolio.single;
    expect(modified.qty, 2);
    expect(modified.price, 120);
    expect(modified.adjustment, 66.6);

    final snapshot = state.capturePortfolioSnapshot();
    state.optimisticDeleteInvestment(code: 'AAPL', notify: false);
    expect(state.portfolio, isEmpty);

    state.restorePortfolioSnapshot(snapshot, notify: false);
    expect(state.portfolio.single.code, 'AAPL');
    expect(state.portfolio.single.qty, 2);
  });
}
