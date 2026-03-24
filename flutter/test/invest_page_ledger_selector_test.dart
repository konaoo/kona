import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tool/pages/invest_page.dart';
import 'package:tool/providers/app_state.dart';

class _LedgerSelectorAppState extends AppState {
  _LedgerSelectorAppState({
    required List<Map<String, dynamic>> ledgers,
    required int currentLedgerId,
  }) : _ledgers = ledgers,
       _currentLedgerId = currentLedgerId,
       super(tokenLoader: () async => null);

  final List<Map<String, dynamic>> _ledgers;
  int _currentLedgerId;
  int? switchedLedgerId;

  @override
  List<Map<String, dynamic>> get ledgers => _ledgers;

  @override
  int? get currentLedgerId => _currentLedgerId;

  @override
  void switchLedger(int? ledgerId) {
    switchedLedgerId = ledgerId;
    _currentLedgerId = ledgerId ?? _currentLedgerId;
    notifyListeners();
  }

  @override
  Future<void> refreshHomeData({int? ledgerId}) async {}
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() async {
    SharedPreferences.setMockInitialValues({});
    FlutterSecureStorage.setMockInitialValues({});
  });

  Future<void> pumpPage(
    WidgetTester tester,
    _LedgerSelectorAppState appState,
  ) async {
    await tester.pumpWidget(
      ChangeNotifierProvider<AppState>.value(
        value: appState,
        child: const MaterialApp(home: InvestPage()),
      ),
    );
    await tester.pumpAndSettle();
  }

  testWidgets('投资页账本选择器可切换账本', (tester) async {
    final appState = _LedgerSelectorAppState(
      ledgers: const [
        {'id': 1, 'name': '默认账本', 'is_default': true, 'sort_order': 0},
        {'id': 2, 'name': '旅行账本', 'is_default': false, 'sort_order': 1},
      ],
      currentLedgerId: 1,
    );

    await pumpPage(tester, appState);

    await tester.tap(find.text('默认账本').first);
    await tester.pumpAndSettle();
    await tester.tap(find.text('旅行账本').last);
    await tester.pumpAndSettle();

    expect(appState.switchedLedgerId, 2);
  });

  testWidgets('投资页账本选择器可进入管理账本页', (tester) async {
    final appState = _LedgerSelectorAppState(
      ledgers: const [
        {'id': 1, 'name': '默认账本', 'is_default': true, 'sort_order': 0},
      ],
      currentLedgerId: 1,
    );

    await pumpPage(tester, appState);

    await tester.tap(find.text('默认账本').first);
    await tester.pumpAndSettle();
    await tester.tap(find.text('管理账本').last);
    await tester.pumpAndSettle();

    expect(find.text('管理账本'), findsOneWidget);
    expect(find.text('新增账本'), findsOneWidget);
  });
}
