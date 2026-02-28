import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tool/models/asset_action_result.dart';
import 'package:tool/providers/app_state.dart';
import 'package:tool/widgets/invest_trade_dialog.dart';

class _ThrowingSearchAppState extends AppState {
  _ThrowingSearchAppState() : super(tokenLoader: () async => null);

  @override
  Future<List<dynamic>> searchStocks(String query) async {
    throw Exception('search failed');
  }
}

class _SaveStateAppState extends AppState {
  _SaveStateAppState({required this.result}) : super(tokenLoader: () async => null);

  final AssetActionResult result;
  int buyWithCashCalls = 0;

  @override
  Future<List<dynamic>> searchStocks(String query) async {
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
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() async {
    SharedPreferences.setMockInitialValues({});
    FlutterSecureStorage.setMockInitialValues({});
  });

  testWidgets('Search failure does not keep loading state forever', (
    WidgetTester tester,
  ) async {
    final appState = _ThrowingSearchAppState();
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
          home: Scaffold(
            body: InvestTradeDialog(mode: 'add'),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    await tester.enterText(
      find.byType(TextField).first,
      'tsla',
    );
    await tester.pump(const Duration(milliseconds: 900));
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);
    expect(find.text('搜索中...'), findsNothing);
  });

  Future<void> prepareAddDialog(
    WidgetTester tester,
    AppState appState,
  ) async {
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
          home: Scaffold(
            body: InvestTradeDialog(mode: 'add'),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    await tester.enterText(find.byType(TextField).first, 'tsla');
    await tester.pump(const Duration(milliseconds: 350));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Tesla').first);
    await tester.pumpAndSettle();

    await tester.enterText(find.byType(TextField).at(1), '100');
    await tester.enterText(find.byType(TextField).at(2), '2');
    await tester.pumpAndSettle();
  }

  testWidgets('Save failure keeps dialog open and shows error', (
    WidgetTester tester,
  ) async {
    final appState = _SaveStateAppState(
      result: const AssetActionResult.failure('后端失败'),
    );
    await prepareAddDialog(tester, appState);

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

    await tester.tap(find.widgetWithText(ElevatedButton, '保存'));
    await tester.pumpAndSettle();

    expect(find.byType(InvestTradeDialog), findsNothing);
    expect(appState.buyWithCashCalls, 1);
    await tester.pump(const Duration(seconds: 3));
    await tester.pumpAndSettle();
  });
}
