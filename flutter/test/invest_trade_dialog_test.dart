import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tool/models/asset_action_result.dart';
import 'package:tool/models/portfolio.dart';
import 'package:tool/providers/app_state.dart';
import 'package:tool/widgets/invest_trade_dialog.dart';

class _RetrySearchAppState extends AppState {
  _RetrySearchAppState() : super(tokenLoader: () async => null);

  int searchCalls = 0;

  @override
  Future<List<dynamic>> searchStocks(String query) async {
    searchCalls += 1;
    if (searchCalls == 1) {
      throw Exception('search failed once');
    }
    return <dynamic>[
      <String, dynamic>{
        'code': 'gb_tsla',
        'name': 'Tesla',
        'type_name': '美股',
        'currency': 'USD',
        'asset_type': 'us',
      },
    ];
  }
}

class _SaveStateAppState extends AppState {
  _SaveStateAppState({
    required this.result,
    this.searchDelay = Duration.zero,
    List<dynamic>? searchResults,
    Map<String, double?>? latestPriceByCode,
  }) : _searchResults =
           searchResults ??
           <dynamic>[
             <String, dynamic>{
               'code': 'gb_tsla',
               'name': 'Tesla',
               'type_name': '美股',
               'currency': 'USD',
               'asset_type': 'us',
             },
           ],
       _latestPriceByCode = latestPriceByCode ?? <String, double?>{},
       super(tokenLoader: () async => null);

  final AssetActionResult result;
  final Duration searchDelay;
  final List<dynamic> _searchResults;
  final Map<String, double?> _latestPriceByCode;
  int buyWithCashCalls = 0;
  int modifyCalls = 0;
  int searchCalls = 0;
  String? lastModifyCode;
  double? lastModifyQty;
  double? lastModifyPrice;
  double? lastModifyAdjustment;
  String? lastBuyCode;
  double? lastBuyPrice;
  double? lastBuyQty;

  @override
  Future<List<dynamic>> searchStocks(String query) async {
    searchCalls += 1;
    if (searchDelay > Duration.zero) {
      await Future<void>.delayed(searchDelay);
    }
    return _searchResults;
  }

  @override
  Future<AssetActionResult> buyInvestmentWithCash({
    required String code,
    required String name,
    required double price,
    required double qty,
    required int cashAssetId,
    String? curr,
    String? assetType,
    bool awaitRefresh = true,
  }) async {
    buyWithCashCalls += 1;
    lastBuyCode = code;
    lastBuyPrice = price;
    lastBuyQty = qty;
    return result;
  }

  @override
  Future<double?> fetchLatestPriceForCode(String code) async {
    if (_latestPriceByCode.containsKey(code)) {
      return _latestPriceByCode[code];
    }
    return null;
  }

  @override
  Future<AssetActionResult> modifyInvestment({
    required String code,
    required double qty,
    required double price,
    required double adjustment,
    bool awaitRefresh = true,
  }) async {
    modifyCalls += 1;
    lastModifyCode = code;
    lastModifyQty = qty;
    lastModifyPrice = price;
    lastModifyAdjustment = adjustment;
    return result;
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() async {
    SharedPreferences.setMockInitialValues({});
    FlutterSecureStorage.setMockInitialValues({});
  });

  Finder _fieldByLabel(String label) {
    return find.byWidgetPredicate(
      (widget) => widget is TextField && widget.decoration?.labelText == label,
    );
  }

  Future<void> _ensureLargeViewport(WidgetTester tester) async {
    await tester.binding.setSurfaceSize(const Size(1200, 1600));
    addTearDown(() => tester.binding.setSurfaceSize(null));
  }

  testWidgets('Add mode does not auto search while typing', (
    WidgetTester tester,
  ) async {
    await _ensureLargeViewport(tester);
    final appState = _SaveStateAppState(
      result: const AssetActionResult.success(),
    );
    await appState.setLoggedIn(
      token: 'token',
      refreshToken: 'refresh',
      username: 'kona',
      userId: 'uid-search',
    );

    await tester.pumpWidget(
      ChangeNotifierProvider<AppState>.value(
        value: appState,
        child: const MaterialApp(
          home: Scaffold(body: InvestTradeDialog(mode: 'add')),
        ),
      ),
    );
    await tester.pumpAndSettle();

    await tester.enterText(find.byType(TextField).first, 'tsla');
    await tester.pump(const Duration(milliseconds: 900));
    await tester.pumpAndSettle();

    expect(appState.searchCalls, 0);
    expect(find.text('Tesla'), findsNothing);
  });

  Future<void> prepareAddDialog(
    WidgetTester tester,
    AppState appState, {
    String priceText = '100',
    String qtyText = '2',
  }) async {
    await _ensureLargeViewport(tester);
    await appState.setLoggedIn(
      token: 'token',
      refreshToken: 'refresh',
      username: 'kona',
      userId: 'uid-save',
    );
    await tester.pumpWidget(
      ChangeNotifierProvider<AppState>.value(
        value: appState,
        child: const MaterialApp(
          home: Scaffold(body: InvestTradeDialog(mode: 'add')),
        ),
      ),
    );
    await tester.pumpAndSettle();

    await tester.enterText(find.byType(TextField).first, 'tsla');
    await tester.tap(find.widgetWithText(ElevatedButton, '搜索'));
    await tester.pump();
    await tester.pumpAndSettle();
    await tester.tap(find.text('TSLA').first);
    await tester.pumpAndSettle();
    expect(find.text('已选择：'), findsOneWidget);

    await tester.enterText(_fieldByLabel('买入成本价'), priceText);
    await tester.enterText(_fieldByLabel('数量'), qtyText);
    await tester.pumpAndSettle();
  }

  Future<void> prepareTradeDialogWithItem(
    WidgetTester tester,
    AppState appState, {
    required PortfolioItem item,
  }) async {
    await _ensureLargeViewport(tester);
    await appState.setLoggedIn(
      token: 'token',
      refreshToken: 'refresh',
      username: 'kona',
      userId: 'uid-trade',
    );
    await tester.pumpWidget(
      ChangeNotifierProvider<AppState>.value(
        value: appState,
        child: MaterialApp(
          home: Scaffold(
            body: InvestTradeDialog(mode: 'trade', item: item),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
  }

  testWidgets('Add mode search triggers only on button tap', (
    WidgetTester tester,
  ) async {
    await _ensureLargeViewport(tester);
    final appState = _SaveStateAppState(
      result: const AssetActionResult.success(),
    );
    await appState.setLoggedIn(
      token: 'token',
      refreshToken: 'refresh',
      username: 'kona',
      userId: 'uid-search-btn',
    );
    await tester.pumpWidget(
      ChangeNotifierProvider<AppState>.value(
        value: appState,
        child: const MaterialApp(
          home: Scaffold(body: InvestTradeDialog(mode: 'add')),
        ),
      ),
    );
    await tester.pumpAndSettle();

    await tester.enterText(find.byType(TextField).first, 'tsla');
    await tester.pumpAndSettle();
    expect(appState.searchCalls, 0);

    await tester.tap(find.widgetWithText(ElevatedButton, '搜索'));
    await tester.pumpAndSettle();
    expect(appState.searchCalls, 1);
    expect(find.text('Tesla'), findsWidgets);
  });

  testWidgets('Add mode search shows loading and hides after finish', (
    WidgetTester tester,
  ) async {
    await _ensureLargeViewport(tester);
    final appState = _SaveStateAppState(
      result: const AssetActionResult.success(),
      searchDelay: const Duration(milliseconds: 600),
    );
    await appState.setLoggedIn(
      token: 'token',
      refreshToken: 'refresh',
      username: 'kona',
      userId: 'uid-search-loading',
    );
    await tester.pumpWidget(
      ChangeNotifierProvider<AppState>.value(
        value: appState,
        child: const MaterialApp(
          home: Scaffold(body: InvestTradeDialog(mode: 'add')),
        ),
      ),
    );
    await tester.pumpAndSettle();

    await tester.enterText(find.byType(TextField).first, 'tsla');
    await tester.tap(find.widgetWithText(ElevatedButton, '搜索'));
    await tester.pump();

    expect(find.widgetWithText(ElevatedButton, '搜索中'), findsOneWidget);

    await tester.pump(const Duration(milliseconds: 700));
    await tester.pumpAndSettle();

    expect(find.widgetWithText(ElevatedButton, '搜索'), findsOneWidget);
    expect(find.text('Tesla'), findsWidgets);
  });

  testWidgets('Add mode search failure supports retry', (
    WidgetTester tester,
  ) async {
    await _ensureLargeViewport(tester);
    final appState = _RetrySearchAppState();
    await appState.setLoggedIn(
      token: 'token',
      refreshToken: 'refresh',
      username: 'kona',
      userId: 'uid-search-retry',
    );
    await tester.pumpWidget(
      ChangeNotifierProvider<AppState>.value(
        value: appState,
        child: const MaterialApp(
          home: Scaffold(body: InvestTradeDialog(mode: 'add')),
        ),
      ),
    );
    await tester.pumpAndSettle();

    await tester.enterText(find.byType(TextField).first, 'tsla');
    await tester.tap(find.widgetWithText(ElevatedButton, '搜索'));
    await tester.pumpAndSettle();

    expect(find.text('搜索失败，请稍后重试'), findsOneWidget);
    expect(appState.searchCalls, 1);

    await tester.tap(find.widgetWithText(ElevatedButton, '搜索'));
    await tester.pumpAndSettle();

    expect(appState.searchCalls, 2);
    expect(find.text('Tesla'), findsWidgets);
  });

  testWidgets('Add mode shows 买入成本价 and accepts fractional qty', (
    WidgetTester tester,
  ) async {
    final appState = _SaveStateAppState(
      result: const AssetActionResult.success(),
    );
    await prepareAddDialog(tester, appState, priceText: '100', qtyText: '1.25');

    expect(find.text('买入成本价'), findsOneWidget);
    await tester.ensureVisible(find.widgetWithText(ElevatedButton, '保存'));
    await tester.tap(find.widgetWithText(ElevatedButton, '保存'));
    await tester.pumpAndSettle();

    expect(find.text('添加投资资产'), findsNothing);
    expect(appState.buyWithCashCalls, 1);
    await tester.pump(const Duration(seconds: 3));
    await tester.pumpAndSettle();
  });

  testWidgets('Save failure keeps dialog open and shows error', (
    WidgetTester tester,
  ) async {
    final appState = _SaveStateAppState(
      result: const AssetActionResult.failure('后端失败'),
    );
    await prepareAddDialog(tester, appState);

    await tester.ensureVisible(find.widgetWithText(ElevatedButton, '保存'));
    await tester.tap(find.widgetWithText(ElevatedButton, '保存'));
    await tester.pumpAndSettle();

    expect(find.byType(InvestTradeDialog), findsOneWidget);
    expect(find.text('后端失败'), findsWidgets);
    expect(appState.buyWithCashCalls, 1);
    await tester.pump(const Duration(seconds: 3));
    await tester.pumpAndSettle();
  });

  testWidgets('Save success closes dialog', (WidgetTester tester) async {
    final appState = _SaveStateAppState(
      result: const AssetActionResult.success(),
    );
    await prepareAddDialog(tester, appState);

    await tester.ensureVisible(find.widgetWithText(ElevatedButton, '保存'));
    await tester.tap(find.widgetWithText(ElevatedButton, '保存'));
    await tester.pumpAndSettle();

    expect(find.text('添加投资资产'), findsNothing);
    expect(appState.buyWithCashCalls, 1);
    await tester.pump(const Duration(seconds: 3));
    await tester.pumpAndSettle();
  });

  testWidgets('Changing query clears selected asset and disables save', (
    WidgetTester tester,
  ) async {
    final appState = _SaveStateAppState(
      result: const AssetActionResult.success(),
    );
    await prepareAddDialog(tester, appState, priceText: '10', qtyText: '2');

    var saveBtn = tester.widget<ElevatedButton>(
      find.widgetWithText(ElevatedButton, '保存'),
    );
    expect(saveBtn.onPressed, isNotNull);

    await tester.enterText(find.byType(TextField).first, 'tsla new');
    await tester.pumpAndSettle();

    saveBtn = tester.widget<ElevatedButton>(
      find.widgetWithText(ElevatedButton, '保存'),
    );
    expect(saveBtn.onPressed, isNull);
  });

  testWidgets('Trade dialog does not show numeric pad buttons', (
    WidgetTester tester,
  ) async {
    await _ensureLargeViewport(tester);
    final appState = _SaveStateAppState(
      result: const AssetActionResult.success(),
    );
    await appState.setLoggedIn(
      token: 'token',
      refreshToken: 'refresh',
      username: 'kona',
      userId: 'uid-no-pad',
    );
    await tester.pumpWidget(
      ChangeNotifierProvider<AppState>.value(
        value: appState,
        child: const MaterialApp(
          home: Scaffold(body: InvestTradeDialog(mode: 'add')),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.widgetWithText(ElevatedButton, '清空'), findsNothing);
    expect(find.widgetWithText(ElevatedButton, '删除'), findsNothing);
    expect(find.widgetWithText(ElevatedButton, '确认'), findsNothing);
  });

  testWidgets('Add mode rejects non-positive price with clear message', (
    WidgetTester tester,
  ) async {
    final appState = _SaveStateAppState(
      result: const AssetActionResult.success(),
    );
    await prepareAddDialog(tester, appState, priceText: '', qtyText: '');

    await tester.enterText(_fieldByLabel('买入成本价'), '-1');
    await tester.enterText(_fieldByLabel('数量'), '1');
    await tester.pumpAndSettle();

    await tester.ensureVisible(find.widgetWithText(ElevatedButton, '保存'));
    await tester.tap(find.widgetWithText(ElevatedButton, '保存'));
    await tester.pumpAndSettle();

    expect(find.text('价格必须大于 0'), findsOneWidget);
    expect(appState.buyWithCashCalls, 0);
  });

  testWidgets('Trade mode fund prefill keeps 4 decimals', (
    WidgetTester tester,
  ) async {
    final appState = _SaveStateAppState(
      result: const AssetActionResult.success(),
    );
    final item = PortfolioItem(
      code: 'f_110017',
      name: '易方达增强回报债券A',
      qty: 1,
      price: 1.23456,
      curr: 'CNY',
      assetType: 'fund',
    );
    await prepareTradeDialogWithItem(tester, appState, item: item);

    final priceField = tester.widget<TextField>(
      find.byWidgetPredicate(
        (widget) => widget is TextField && widget.decoration?.labelText == '净值',
      ),
    );
    expect(priceField.controller?.text, '1.2346');
  });

  testWidgets('Trade mode non-fund prefill keeps 3 decimals', (
    WidgetTester tester,
  ) async {
    final appState = _SaveStateAppState(
      result: const AssetActionResult.success(),
    );
    final item = PortfolioItem(
      code: 'gb_tsla',
      name: 'Tesla',
      qty: 1,
      price: 1.23456,
      curr: 'USD',
      assetType: 'us',
    );
    await prepareTradeDialogWithItem(tester, appState, item: item);

    final priceField = tester.widget<TextField>(
      find.byWidgetPredicate(
        (widget) => widget is TextField && widget.decoration?.labelText == '价格',
      ),
    );
    expect(priceField.controller?.text, '1.235');
  });

  testWidgets('Trade adjust mode allows negative cost and calls modify', (
    WidgetTester tester,
  ) async {
    final appState = _SaveStateAppState(
      result: const AssetActionResult.success(),
    );
    final item = PortfolioItem(
      code: 'gb_tsla',
      name: 'Tesla',
      qty: 5,
      price: 10,
      curr: 'USD',
      assetType: 'us',
    );
    await prepareTradeDialogWithItem(tester, appState, item: item);

    await tester.tap(find.text('调整'));
    await tester.pumpAndSettle();

    await tester.enterText(
      find.byWidgetPredicate(
        (widget) =>
            widget is TextField && widget.decoration?.labelText == '平均成本',
      ),
      '-1.23',
    );
    await tester.enterText(
      find.byWidgetPredicate(
        (widget) =>
            widget is TextField && widget.decoration?.labelText == '调整金额',
      ),
      '8.5',
    );
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.widgetWithText(ElevatedButton, '保存'));
    await tester.tap(find.widgetWithText(ElevatedButton, '保存'));
    await tester.pumpAndSettle();

    expect(appState.modifyCalls, 1);
    expect(appState.lastModifyCode, 'gb_tsla');
    expect(appState.lastModifyQty, 5);
    expect(appState.lastModifyPrice, -1.23);
    expect(appState.lastModifyAdjustment, 8.5);
    await tester.pump(const Duration(seconds: 3));
    await tester.pumpAndSettle();
  });

  testWidgets('Fund add defaults to amount mode and submits derived qty', (
    WidgetTester tester,
  ) async {
    final appState = _SaveStateAppState(
      result: const AssetActionResult.success(),
      searchResults: <dynamic>[
        <String, dynamic>{
          'code': 'f_110017',
          'name': '易方达增强回报债券A',
          'type_name': '基金',
          'currency': 'CNY',
          'asset_type': 'fund',
        },
      ],
      latestPriceByCode: <String, double?>{'f_110017': 1.2345},
    );
    await _ensureLargeViewport(tester);
    await appState.setLoggedIn(
      token: 'token',
      refreshToken: 'refresh',
      username: 'kona',
      userId: 'uid-fund-add',
    );
    await tester.pumpWidget(
      ChangeNotifierProvider<AppState>.value(
        value: appState,
        child: const MaterialApp(
          home: Scaffold(body: InvestTradeDialog(mode: 'add')),
        ),
      ),
    );
    await tester.pumpAndSettle();

    await tester.enterText(find.byType(TextField).first, '110017');
    await tester.tap(find.widgetWithText(ElevatedButton, '搜索'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('易方达增强回报债券A').first);
    await tester.pumpAndSettle();

    expect(find.text('按金额'), findsOneWidget);
    expect(_fieldByLabel('买入金额'), findsOneWidget);
    expect(_fieldByLabel('数量'), findsNothing);

    await tester.enterText(_fieldByLabel('买入金额'), '100');
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.widgetWithText(ElevatedButton, '保存'));
    await tester.tap(find.widgetWithText(ElevatedButton, '保存'));
    await tester.pumpAndSettle();

    expect(appState.buyWithCashCalls, 1);
    expect(appState.lastBuyCode, 'f_110017');
    expect(appState.lastBuyPrice, closeTo(1.2345, 0.000001));
    expect(appState.lastBuyQty, closeTo(81.0044, 0.000001));
    await tester.pump(const Duration(seconds: 3));
    await tester.pumpAndSettle();
  });

  testWidgets('Fund trade-buy mode submits amount-derived qty', (
    WidgetTester tester,
  ) async {
    final appState = _SaveStateAppState(
      result: const AssetActionResult.success(),
      latestPriceByCode: <String, double?>{'f_110017': 1.25},
    );
    final item = PortfolioItem(
      code: 'f_110017',
      name: '易方达增强回报债券A',
      qty: 10,
      price: 1.2,
      curr: 'CNY',
      assetType: 'fund',
    );
    await prepareTradeDialogWithItem(tester, appState, item: item);

    expect(find.text('按金额'), findsOneWidget);
    expect(_fieldByLabel('买入金额'), findsOneWidget);
    await tester.enterText(_fieldByLabel('买入金额'), '50');
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.widgetWithText(ElevatedButton, '保存'));
    await tester.tap(find.widgetWithText(ElevatedButton, '保存'));
    await tester.pumpAndSettle();

    expect(appState.buyWithCashCalls, 1);
    expect(appState.lastBuyCode, 'f_110017');
    expect(appState.lastBuyQty, closeTo(40.0, 0.000001));
    expect(appState.lastBuyPrice, closeTo(1.25, 0.000001));
    await tester.pump(const Duration(seconds: 3));
    await tester.pumpAndSettle();
  });

  testWidgets('Fund amount mode allows manual nav when fetch failed', (
    WidgetTester tester,
  ) async {
    final appState = _SaveStateAppState(
      result: const AssetActionResult.success(),
      searchResults: <dynamic>[
        <String, dynamic>{
          'code': 'f_110017',
          'name': '易方达增强回报债券A',
          'type_name': '基金',
          'currency': 'CNY',
          'asset_type': 'fund',
        },
      ],
      latestPriceByCode: <String, double?>{'f_110017': null},
    );
    await _ensureLargeViewport(tester);
    await appState.setLoggedIn(
      token: 'token',
      refreshToken: 'refresh',
      username: 'kona',
      userId: 'uid-fund-nav-fallback',
    );
    await tester.pumpWidget(
      ChangeNotifierProvider<AppState>.value(
        value: appState,
        child: const MaterialApp(
          home: Scaffold(body: InvestTradeDialog(mode: 'add')),
        ),
      ),
    );
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField).first, '110017');
    await tester.tap(find.widgetWithText(ElevatedButton, '搜索'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('易方达增强回报债券A').first);
    await tester.pumpAndSettle();

    expect(find.text('净值获取失败，可手动输入'), findsOneWidget);
    await tester.enterText(_fieldByLabel('净值'), '1.1');
    await tester.enterText(_fieldByLabel('买入金额'), '22');
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.widgetWithText(ElevatedButton, '保存'));
    await tester.tap(find.widgetWithText(ElevatedButton, '保存'));
    await tester.pumpAndSettle();
    expect(appState.buyWithCashCalls, 1);
    expect(appState.lastBuyQty, closeTo(20.0, 0.000001));
    await tester.pump(const Duration(seconds: 3));
    await tester.pumpAndSettle();
  });

  testWidgets('Fund amount mode rejects too-small amount', (
    WidgetTester tester,
  ) async {
    final appState = _SaveStateAppState(
      result: const AssetActionResult.success(),
      searchResults: <dynamic>[
        <String, dynamic>{
          'code': 'f_110017',
          'name': '易方达增强回报债券A',
          'type_name': '基金',
          'currency': 'CNY',
          'asset_type': 'fund',
        },
      ],
      latestPriceByCode: <String, double?>{'f_110017': 100},
    );
    await _ensureLargeViewport(tester);
    await appState.setLoggedIn(
      token: 'token',
      refreshToken: 'refresh',
      username: 'kona',
      userId: 'uid-fund-small-amount',
    );
    await tester.pumpWidget(
      ChangeNotifierProvider<AppState>.value(
        value: appState,
        child: const MaterialApp(
          home: Scaffold(body: InvestTradeDialog(mode: 'add')),
        ),
      ),
    );
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField).first, '110017');
    await tester.tap(find.widgetWithText(ElevatedButton, '搜索'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('易方达增强回报债券A').first);
    await tester.pumpAndSettle();
    await tester.enterText(_fieldByLabel('买入金额'), '0.001');
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.widgetWithText(ElevatedButton, '保存'));
    await tester.tap(find.widgetWithText(ElevatedButton, '保存'));
    await tester.pumpAndSettle();
    expect(find.text('金额过小，按当前净值不足以买入最小份额（0.0001）'), findsOneWidget);
    expect(appState.buyWithCashCalls, 0);
  });

  testWidgets('Non-fund add does not show fund amount mode controls', (
    WidgetTester tester,
  ) async {
    final appState = _SaveStateAppState(
      result: const AssetActionResult.success(),
    );
    await prepareAddDialog(tester, appState, priceText: '100', qtyText: '1');
    expect(find.text('按金额'), findsNothing);
    expect(_fieldByLabel('买入金额'), findsNothing);
  });
}
