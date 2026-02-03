import 'package:flutter_test/flutter_test.dart';
import 'package:tool/providers/app_state.dart';

void main() {
  test('AppState formatAmount hides when toggled', () {
    final state = AppState();
    final visible = state.formatAmount(1234, prefix: '¥');
    expect(visible, isNot('****'));

    state.toggleAmountHidden();
    final hidden = state.formatAmount(1234, prefix: '¥');
    expect(hidden, '****');
  });
}
