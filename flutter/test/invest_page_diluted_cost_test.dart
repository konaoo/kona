import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tool/models/portfolio.dart';
import 'package:tool/pages/invest_page.dart';
import 'package:tool/providers/app_state.dart';

class _InvestPageCostAppState extends AppState {
  _InvestPageCostAppState(this._items) : super(tokenLoader: () async => null);

  final List<PortfolioItem> _items;

  @override
  List<PortfolioItem> get filteredPortfolio => _items;

  @override
  Future<void> refreshHomeData({int? ledgerId}) async {}
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() async {
    SharedPreferences.setMockInitialValues({});
    FlutterSecureStorage.setMockInitialValues({});
  });

  Future<void> pumpInvestPage(
    WidgetTester tester,
    List<PortfolioItem> items,
  ) async {
    await tester.binding.setSurfaceSize(const Size(1200, 1600));
    addTearDown(() => tester.binding.setSurfaceSize(null));

    final appState = _InvestPageCostAppState(items);
    await tester.pumpWidget(
      ChangeNotifierProvider<AppState>.value(
        value: appState,
        child: const MaterialApp(home: InvestPage()),
      ),
    );
    await tester.pumpAndSettle();
  }

  testWidgets('InvestPage shows diluted cost after realized profit', (
    tester,
  ) async {
    await pumpInvestPage(tester, <PortfolioItem>[
      PortfolioItem(
        code: 'sh600000',
        name: '浦发银行',
        qty: 100,
        price: 10,
        adjustment: 200,
        displayCostPrice: 8.0,
        curr: 'CNY',
        assetType: 'a',
      ),
    ]);

    expect(find.text('成本价'), findsOneWidget);
    expect(find.text('¥8.000'), findsOneWidget);
  });

  testWidgets('InvestPage keeps negative diluted cost visible', (tester) async {
    await pumpInvestPage(tester, <PortfolioItem>[
      PortfolioItem(
        code: 'sh600001',
        name: '测试负成本',
        qty: 60,
        price: 10,
        adjustment: 800,
        displayCostPrice: -3.333,
        curr: 'CNY',
        assetType: 'a',
      ),
    ]);

    expect(find.text('成本价'), findsOneWidget);
    expect(find.text('¥-3.333'), findsOneWidget);
  });
}
