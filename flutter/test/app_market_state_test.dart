import 'package:flutter_test/flutter_test.dart';
import 'package:tool/providers/app_market_state.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test(
    'AppMarketState parses trading day from reason and fallback open status',
    () {
      final state = AppMarketState();

      final parsed = state.parseMarketStatus(
        <String, dynamic>{
          'markets': <String, dynamic>{
            'hk': <String, dynamic>{'open': false, 'reason': 'off_hours'},
          },
        },
        openFallback: const <String, bool>{
          'a': false,
          'hk': false,
          'us': true,
          'fund': false,
        },
      );

      expect(parsed.open['hk'], isFalse);
      expect(parsed.tradingDay['hk'], isTrue);
      expect(parsed.open['us'], isTrue);
      expect(parsed.tradingDay['us'], isTrue);
    },
  );

  test('AppMarketState updates exchange rates and converts to CNY', () {
    final state = AppMarketState();

    state.updateExchangeRates(<String, dynamic>{'USD': 7.5, 'HKD': 0.95});

    expect(state.getCurrencyRate('USD'), 7.5);
    expect(state.getCurrencyRate('HKD'), 0.95);
    expect(state.convertToCny(100, 'USD'), 750);
    expect(state.convertToCny(100, 'HKD'), 95);
    expect(state.convertToCny(100, 'CNY'), 100);
  });
}
