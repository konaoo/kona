import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tool/models/asset.dart';
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
  int sellWithCashCalls = 0;

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

  @override
  Future<AssetActionResult> sellInvestmentToCash({
    required String code,
    required double price,
    required double qty,
    required int cashAssetId,
    bool awaitRefresh = true,
  }) async {
    sellWithCashCalls += 1;
    return result;
  }
}

class _CashAccountStateAppState extends _SaveStateAppState {
  _CashAccountStateAppState({
    required super.result,
    required List<Asset> cashAssets,
  }) : _cashAssets = List<Asset>.from(cashAssets);

  final List<Asset> _cashAssets;
  int addAssetCalls = 0;
  String? lastAddedCurr;

  @override
  List<Asset> get cashAssets => List<Asset>.from(_cashAssets);

  @override
  Future<AssetActionResult> addAsset({
    required String type,
    required String name,
    required double amount,
    String? curr,
    bool awaitRefresh = true,
  }) async {
    addAssetCalls += 1;
    lastAddedCurr = curr;
    if (type != 'cash') {
      return const AssetActionResult.failure('unexpected type');
    }
    final nextId = _cashAssets.isEmpty
        ? 1
        : (_cashAssets
                  .map((asset) => asset.id ?? 0)
                  .reduce((a, b) => a > b ? a : b) +
              1);
    _cashAssets.add(
      Asset(
        id: nextId,
        name: name,
        amount: amount,
        curr: (curr ?? 'CNY').toUpperCase(),
      ),
    );
    notifyListeners();
    return const AssetActionResult.success();
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() async {
    SharedPreferences.setMockInitialValues({});
    FlutterSecureStorage.setMockInitialValues({});
  });

  Finder _k(String key) => find.byKey(Key(key));

  Future<void> _ensureLargeViewport(WidgetTester tester) async {
    await tester.binding.setSurfaceSize(const Size(1200, 1600));
    addTearDown(() => tester.binding.setSurfaceSize(null));
  }

  Future<void> _login(AppState appState, String userId) async {
    await appState.setLoggedIn(
      token: 'token',
      refreshToken: 'refresh',
      username: 'kona',
      userId: userId,
    );
  }

  Future<void> _pumpDialog(
    WidgetTester tester,
    AppState appState, {
    required String mode,
    PortfolioItem? item,
  }) async {
    await _ensureLargeViewport(tester);
    await _login(appState, 'uid-$mode');
    await tester.pumpWidget(
      ChangeNotifierProvider<AppState>.value(
        value: appState,
        child: MaterialApp(
          home: Scaffold(
            body: InvestTradeDialog(mode: mode, item: item),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
  }

  Future<void> _openAndPickTesla(WidgetTester tester) async {
    await tester.tap(_k('invest_search_field'));
    await tester.pumpAndSettle();
    await tester.enterText(_k('invest_search_field'), 'tsla');
    await tester.tap(_k('invest_search_button'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Tesla').first);
    await tester.pumpAndSettle();
  }

  testWidgets('renders as sheet structure', (WidgetTester tester) async {
    final appState = _SaveStateAppState(
      result: const AssetActionResult.success(),
    );
    await _pumpDialog(tester, appState, mode: 'add');

    expect(_k('invest_sheet_root'), findsOneWidget);
    expect(_k('invest_sheet_handle'), findsOneWidget);
    expect(_k('invest_cancel_button'), findsOneWidget);
    expect(_k('invest_submit_button'), findsOneWidget);
  });

  testWidgets('showInvestTradeSheet opens modal sheet', (
    WidgetTester tester,
  ) async {
    final appState = _SaveStateAppState(
      result: const AssetActionResult.success(),
    );
    await _ensureLargeViewport(tester);
    await _login(appState, 'uid-sheet-open');

    await tester.pumpWidget(
      ChangeNotifierProvider<AppState>.value(
        value: appState,
        child: MaterialApp(
          home: Builder(
            builder: (context) {
              return Scaffold(
                body: Center(
                  child: ElevatedButton(
                    onPressed: () {
                      showInvestTradeSheet(
                        context: context,
                        mode: 'add',
                        hostContext: context,
                      );
                    },
                    child: const Text('open'),
                  ),
                ),
              );
            },
          ),
        ),
      ),
    );

    await tester.tap(find.text('open'));
    await tester.pumpAndSettle();
    expect(_k('invest_sheet_root'), findsOneWidget);
  });

  testWidgets('search overlay opens on focus and supports retry', (
    WidgetTester tester,
  ) async {
    final appState = _RetrySearchAppState();
    await _pumpDialog(tester, appState, mode: 'add');

    await tester.tap(_k('invest_search_field'));
    await tester.pumpAndSettle();
    expect(appState.searchCalls, 0);
    expect(find.text('Tesla'), findsNothing);

    await tester.enterText(_k('invest_search_field'), 'tsla');
    await tester.tap(_k('invest_search_button'));
    await tester.pumpAndSettle();
    expect(appState.searchCalls, 1);
    expect(find.text('搜索失败，请稍后重试'), findsOneWidget);

    await tester.tap(_k('invest_search_button'));
    await tester.pumpAndSettle();
    expect(appState.searchCalls, 2);
    expect(find.text('Tesla'), findsWidgets);
  });

  testWidgets('selecting result shows pill and clear resets inputs', (
    WidgetTester tester,
  ) async {
    final appState = _SaveStateAppState(
      result: const AssetActionResult.success(),
    );
    await _pumpDialog(tester, appState, mode: 'add');

    await _openAndPickTesla(tester);
    expect(find.byKey(const ValueKey<String>('selected-pill')), findsOneWidget);

    await tester.enterText(_k('invest_price_field'), '100');
    await tester.enterText(_k('invest_qty_field'), '2');
    await tester.pumpAndSettle();
    expect(
      tester.widget<TextField>(_k('invest_amount_field')).controller?.text,
      '200',
    );

    await tester.tap(
      find.descendant(
        of: find.byKey(const ValueKey<String>('selected-pill')),
        matching: find.byIcon(Icons.close),
      ),
    );
    await tester.pumpAndSettle();

    expect(_k('invest_search_field'), findsOneWidget);
    expect(
      tester.widget<TextField>(_k('invest_price_field')).controller?.text,
      '',
    );
    expect(
      tester.widget<TextField>(_k('invest_qty_field')).controller?.text,
      '',
    );
    expect(
      tester.widget<TextField>(_k('invest_amount_field')).controller?.text,
      '',
    );
  });

  testWidgets('amount back-calculates qty in non-fund mode', (
    WidgetTester tester,
  ) async {
    final appState = _SaveStateAppState(
      result: const AssetActionResult.success(),
    );
    await _pumpDialog(tester, appState, mode: 'add');
    await _openAndPickTesla(tester);

    await tester.enterText(_k('invest_price_field'), '10');
    await tester.enterText(_k('invest_amount_field'), '29');
    await tester.pumpAndSettle();

    expect(
      tester.widget<TextField>(_k('invest_qty_field')).controller?.text,
      '2',
    );
  });

  testWidgets('add mode submit still calls buyInvestmentWithCash', (
    WidgetTester tester,
  ) async {
    final appState = _SaveStateAppState(
      result: const AssetActionResult.success(),
    );
    await _pumpDialog(tester, appState, mode: 'add');
    await _openAndPickTesla(tester);

    await tester.enterText(_k('invest_price_field'), '100');
    await tester.enterText(_k('invest_qty_field'), '2');
    await tester.pumpAndSettle();

    await tester.tap(_k('invest_submit_button'));
    await tester.pumpAndSettle();

    expect(appState.buyWithCashCalls, 1);
    expect(appState.lastBuyCode, 'gb_tsla');
    expect(appState.lastBuyPrice, 100);
    expect(appState.lastBuyQty, 2);
    await tester.pump(const Duration(seconds: 3));
    await tester.pumpAndSettle();
  });

  testWidgets('save failure keeps sheet open and shows error', (
    WidgetTester tester,
  ) async {
    final appState = _SaveStateAppState(
      result: const AssetActionResult.failure('后端失败'),
    );
    await _pumpDialog(tester, appState, mode: 'add');
    await _openAndPickTesla(tester);

    await tester.enterText(_k('invest_price_field'), '100');
    await tester.enterText(_k('invest_qty_field'), '2');
    await tester.pumpAndSettle();

    await tester.tap(_k('invest_submit_button'));
    await tester.pumpAndSettle();

    expect(find.byType(InvestTradeDialog), findsOneWidget);
    expect(find.text('后端失败'), findsWidgets);
    expect(appState.buyWithCashCalls, 1);
    await tester.pump(const Duration(seconds: 3));
    await tester.pumpAndSettle();
  });

  testWidgets('trade adjust mode allows negative cost and calls modify', (
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
    await _pumpDialog(tester, appState, mode: 'trade', item: item);

    await tester.tap(find.text('调整'));
    await tester.pumpAndSettle();

    await tester.enterText(_k('invest_adjust_price_field'), '-1.23');
    await tester.enterText(_k('invest_adjust_amount_field'), '8.5');
    await tester.pumpAndSettle();

    await tester.tap(_k('invest_submit_button'));
    await tester.pumpAndSettle();

    expect(appState.modifyCalls, 1);
    expect(appState.lastModifyCode, 'gb_tsla');
    expect(appState.lastModifyQty, 5);
    expect(appState.lastModifyPrice, -1.23);
    expect(appState.lastModifyAdjustment, 8.5);
    await tester.pump(const Duration(seconds: 3));
    await tester.pumpAndSettle();
  });

  testWidgets(
    'add mode keeps external funding without same-currency cash account',
    (WidgetTester tester) async {
      final appState = _CashAccountStateAppState(
        result: const AssetActionResult.success(),
        cashAssets: <Asset>[
          Asset(id: 1, name: '人民币账户', amount: 1000, curr: 'CNY'),
        ],
      );

      await _pumpDialog(tester, appState, mode: 'add');
      await tester.enterText(_k('invest_search_field'), 'tsla');
      await tester.tap(_k('invest_search_button'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Tesla').first);
      await tester.pumpAndSettle();

      expect(find.text('未找到 USD 资金账户'), findsNothing);
      expect(find.text('外部资金/初始转入'), findsWidgets);
      expect(find.textContaining('· 外部'), findsNothing);
    },
  );

  testWidgets('sell mode can add same-currency cash account from dropdown', (
    WidgetTester tester,
  ) async {
    final appState = _CashAccountStateAppState(
      result: const AssetActionResult.success(),
      cashAssets: <Asset>[
        Asset(id: 1, name: '人民币账户', amount: 1000, curr: 'CNY'),
      ],
    );
    final item = PortfolioItem(
      code: 'gb_tsla',
      name: 'Tesla',
      qty: 5,
      price: 10,
      curr: 'USD',
      assetType: 'us',
    );
    await _pumpDialog(tester, appState, mode: 'trade', item: item);

    await tester.tap(find.text('卖出'));
    await tester.pumpAndSettle();

    expect(find.text('未找到 USD 资金账户'), findsNothing);
    await tester.tap(_k('invest_cash_trigger'));
    await tester.pumpAndSettle();
    expect(find.text('添加账户'), findsOneWidget);

    await tester.tap(find.text('添加账户'));
    await tester.pumpAndSettle();

    await tester.enterText(
      find.byKey(const Key('add_asset_name_field')),
      '美元回款账户',
    );
    await tester.enterText(
      find.byKey(const Key('add_asset_amount_field')),
      '100',
    );
    await tester.tap(find.byKey(const Key('add_asset_submit_button')));
    await tester.pump();
    await tester.pump(const Duration(seconds: 2));
    await tester.pumpAndSettle();

    expect(appState.addAssetCalls, 1);
    expect(appState.lastAddedCurr, 'USD');
    expect(find.text('未找到 USD 资金账户'), findsNothing);
    expect(find.textContaining('美元回款账户'), findsOneWidget);
  });

  testWidgets('fund add defaults to amount mode and submits derived qty', (
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

    await _pumpDialog(tester, appState, mode: 'add');
    await tester.tap(_k('invest_search_field'));
    await tester.enterText(_k('invest_search_field'), '110017');
    await tester.tap(_k('invest_search_button'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('易方达增强回报债券A').first);
    await tester.pumpAndSettle();

    expect(find.text('按金额'), findsOneWidget);
    expect(_k('invest_qty_field'), findsNothing);

    await tester.enterText(_k('invest_amount_field'), '100');
    await tester.pumpAndSettle();
    await tester.tap(_k('invest_submit_button'));
    await tester.pumpAndSettle();

    expect(appState.buyWithCashCalls, 1);
    expect(appState.lastBuyCode, 'f_110017');
    expect(appState.lastBuyPrice, closeTo(1.2345, 0.000001));
    expect(appState.lastBuyQty, closeTo(81.0044, 0.000001));
    await tester.pump(const Duration(seconds: 3));
    await tester.pumpAndSettle();
  });

  testWidgets('fund amount mode rejects too-small amount', (
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

    await _pumpDialog(tester, appState, mode: 'add');
    await tester.tap(_k('invest_search_field'));
    await tester.enterText(_k('invest_search_field'), '110017');
    await tester.tap(_k('invest_search_button'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('易方达增强回报债券A').first);
    await tester.pumpAndSettle();

    await tester.enterText(_k('invest_amount_field'), '0.001');
    await tester.pumpAndSettle();
    await tester.tap(_k('invest_submit_button'));
    await tester.pumpAndSettle();

    expect(find.text('金额过小，按当前净值不足以买入最小份额（0.0001）'), findsOneWidget);
    expect(appState.buyWithCashCalls, 0);
  });
}
