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

class _InvestPageLiveQuoteAppState extends AppState {
  _InvestPageLiveQuoteAppState({
    required List<PortfolioItem> items,
    required PriceInfo priceInfo,
  }) : _items = items,
       _priceInfo = priceInfo,
       super(tokenLoader: () async => null);

  final List<PortfolioItem> _items;
  PriceInfo _priceInfo;

  @override
  List<PortfolioItem> get portfolio => _items;

  @override
  List<PortfolioItem> get filteredPortfolio => _items;

  @override
  PriceInfo? resolvePriceInfo(PortfolioItem item, {PriceInfo? preferred}) {
    return _priceInfo;
  }

  void updatePriceInfo(PriceInfo next) {
    _priceInfo = next;
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

  testWidgets('InvestPage 会跟随实时价格缓存更新今日盈亏', (tester) async {
    await tester.binding.setSurfaceSize(const Size(1200, 1600));
    addTearDown(() => tester.binding.setSurfaceSize(null));

    final appState = _InvestPageLiveQuoteAppState(
      items: <PortfolioItem>[
        PortfolioItem(
          code: 'sh600000',
          name: '浦发银行',
          qty: 10,
          price: 10,
          cost: 100,
          curr: 'CNY',
          assetType: 'a',
        ),
      ],
      priceInfo: PriceInfo(
        price: 10,
        yclose: 10,
        change: 0,
        changePct: 0,
        session: 'regular',
        effectiveSession: 'regular',
      ),
    );
    await tester.pumpWidget(
      ChangeNotifierProvider<AppState>.value(
        value: appState,
        child: const MaterialApp(home: InvestPage()),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('+¥20'), findsNothing);

    appState.updatePriceInfo(
      PriceInfo(
        price: 12,
        yclose: 10,
        change: 2,
        changePct: 20,
        session: 'regular',
        effectiveSession: 'regular',
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('+¥20'), findsWidgets);
    expect(find.text('¥120'), findsOneWidget);
  });
}
