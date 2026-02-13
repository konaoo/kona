import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tool/providers/app_state.dart';

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
  });
}
