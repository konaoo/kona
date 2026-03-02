import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tool/models/asset_action_result.dart';
import 'package:tool/models/portfolio.dart';
import 'package:tool/providers/app_state.dart';
import 'package:tool/widgets/invest_trade_dialog.dart';

class _ThrowingSearchAppState extends AppState {
  _ThrowingSearchAppState() : super(tokenLoader: () async => null);

  int searchCalls = 0;

  @override
  Future<List<dynamic>> searchStocks(String query) async {
    searchCalls += 1;
    throw Exception('search failed');
  }
}

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
  _SaveStateAppState({required this.result, this.searchDelay = Duration.zero})
    : super(tokenLoader: () async => null);

  final AssetActionResult result;
  final Duration searchDelay;
  int buyWithCashCalls = 0;
  int modifyCalls = 0;
  int searchCalls = 0;
  String? lastModifyCode;
  double? lastModifyQty;
  double? lastModifyPrice;
  double? lastModifyAdjustment;

  @override
  Future<List<dynamic>> searchStocks(String query) async {
    searchCalls += 1;
    if (searchDelay > Duration.zero) {
      await Future<void>.delayed(searchDelay);
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
    return result;
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

  testWidgets(
    'Numeric pad blocks minus for qty and allows one minus for price',
    (WidgetTester tester) async {
      final appState = _SaveStateAppState(
        result: const AssetActionResult.success(),
      );
      await prepareAddDialog(tester, appState, priceText: '', qtyText: '');

      await tester.tap(_fieldByLabel('数量'));
      await tester.pumpAndSettle();
      var minusBtn = tester.widget<ElevatedButton>(
        find.widgetWithText(ElevatedButton, '-'),
      );
      expect(minusBtn.onPressed, isNull);

      await tester.tap(_fieldByLabel('买入成本价'));
      await tester.pumpAndSettle();

      await tester.ensureVisible(find.widgetWithText(ElevatedButton, '-'));
      await tester.tap(find.widgetWithText(ElevatedButton, '-'));
      await tester.tap(find.widgetWithText(ElevatedButton, '-'));
      await tester.ensureVisible(find.widgetWithText(ElevatedButton, '.'));
      await tester.tap(find.widgetWithText(ElevatedButton, '.'));
      await tester.tap(find.widgetWithText(ElevatedButton, '.'));
      await tester.ensureVisible(find.widgetWithText(ElevatedButton, '1'));
      await tester.tap(find.widgetWithText(ElevatedButton, '1'));
      await tester.pumpAndSettle();

      final priceField = tester.widget<TextField>(_fieldByLabel('买入成本价'));
      expect(priceField.controller?.text, '-0.1');
    },
  );

  testWidgets('Numeric pad enforces qty max 2 decimals', (
    WidgetTester tester,
  ) async {
    final appState = _SaveStateAppState(
      result: const AssetActionResult.success(),
    );
    await prepareAddDialog(tester, appState, priceText: '', qtyText: '');

    await tester.tap(_fieldByLabel('数量'));
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.widgetWithText(ElevatedButton, '1'));
    await tester.tap(find.widgetWithText(ElevatedButton, '1'));
    await tester.tap(find.widgetWithText(ElevatedButton, '.'));
    await tester.tap(find.widgetWithText(ElevatedButton, '2'));
    await tester.tap(find.widgetWithText(ElevatedButton, '3'));
    await tester.tap(find.widgetWithText(ElevatedButton, '4'));
    await tester.pumpAndSettle();

    final qtyField = tester.widget<TextField>(_fieldByLabel('数量'));
    expect(qtyField.controller?.text, '1.23');
  });

  testWidgets('Add mode rejects non-positive price with clear message', (
    WidgetTester tester,
  ) async {
    final appState = _SaveStateAppState(
      result: const AssetActionResult.success(),
    );
    await prepareAddDialog(tester, appState, priceText: '', qtyText: '');

    await tester.tap(_fieldByLabel('买入成本价'));
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.widgetWithText(ElevatedButton, '-'));
    await tester.tap(find.widgetWithText(ElevatedButton, '-'));
    await tester.ensureVisible(find.widgetWithText(ElevatedButton, '1'));
    await tester.tap(find.widgetWithText(ElevatedButton, '1'));
    await tester.tap(_fieldByLabel('数量'));
    await tester.pumpAndSettle();
    await tester.tap(find.widgetWithText(ElevatedButton, '1'));
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
        (widget) => widget is TextField && widget.decoration?.labelText == '价格',
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

  testWidgets('Trade mode switch updates minus availability by focused field', (
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

    await tester.tap(_fieldByLabel('数量'));
    await tester.pumpAndSettle();
    var minusBtn = tester.widget<ElevatedButton>(
      find.widgetWithText(ElevatedButton, '-'),
    );
    expect(minusBtn.onPressed, isNull);

    await tester.tap(find.text('调整'));
    await tester.pumpAndSettle();
    await tester.tap(_fieldByLabel('平均成本'));
    await tester.pumpAndSettle();

    minusBtn = tester.widget<ElevatedButton>(
      find.widgetWithText(ElevatedButton, '-'),
    );
    expect(minusBtn.onPressed, isNotNull);
  });

  testWidgets('Close and reopen dialog resets numeric pad visibility', (
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
      userId: 'uid-reopen',
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

    await tester.tap(_fieldByLabel('买入成本价'));
    await tester.pumpAndSettle();
    expect(find.widgetWithText(ElevatedButton, '清空'), findsOneWidget);

    await tester.ensureVisible(find.widgetWithText(TextButton, '取消'));
    await tester.tap(find.widgetWithText(TextButton, '取消'));
    await tester.pumpAndSettle();
    expect(find.text('添加投资资产'), findsNothing);

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
}
