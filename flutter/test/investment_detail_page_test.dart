import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tool/models/asset.dart';
import 'package:tool/models/asset_action_result.dart';
import 'package:tool/models/portfolio.dart';
import 'package:tool/pages/investment_detail_page.dart';
import 'package:tool/providers/app_state.dart';

class _ClearSellDetailAppState extends AppState {
  _ClearSellDetailAppState(this.item) : super(tokenLoader: () async => null) {
    _portfolio = <PortfolioItem>[item];
  }

  final PortfolioItem item;
  List<PortfolioItem> _portfolio = <PortfolioItem>[];
  final Completer<AssetActionResult> sellCompleter =
      Completer<AssetActionResult>();

  int sellCalls = 0;

  @override
  List<PortfolioItem> get portfolio => List<PortfolioItem>.from(_portfolio);

  @override
  List<Asset> get cashAssets => <Asset>[
    Asset(id: 1, name: '美元账户', amount: 0, curr: 'USD'),
  ];

  @override
  Future<List<dynamic>> getInvestmentTransactions(
    String code, {
    int? ledgerId,
  }) async {
    return <dynamic>[];
  }

  @override
  Future<void> refreshPortfolio({int? ledgerId}) async {}

  @override
  Future<AssetActionResult> sellInvestmentToCash({
    required String code,
    required double price,
    required double qty,
    required int cashAssetId,
    bool awaitRefresh = true,
    int? ledgerId,
  }) {
    sellCalls += 1;
    _portfolio = <PortfolioItem>[];
    notifyListeners();
    return sellCompleter.future;
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() async {
    SharedPreferences.setMockInitialValues({});
    FlutterSecureStorage.setMockInitialValues({});
  });

  testWidgets('clear sell from detail returns to previous page', (
    WidgetTester tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(1200, 1600));
    addTearDown(() => tester.binding.setSurfaceSize(null));

    final item = PortfolioItem(
      code: 'gb_goog',
      name: '谷歌',
      qty: 1,
      price: 100,
      curr: 'USD',
      assetType: 'us',
    );
    final appState = _ClearSellDetailAppState(item);
    await appState.setLoggedIn(
      token: 'token',
      refreshToken: 'refresh',
      username: 'kona',
      userId: 'uid-clear-sell-detail',
    );

    await tester.pumpWidget(
      ChangeNotifierProvider<AppState>.value(
        value: appState,
        child: MaterialApp(
          home: Builder(
            builder: (context) {
              return Scaffold(
                body: Center(
                  child: TextButton(
                    onPressed: () {
                      Navigator.of(context).push(
                        MaterialPageRoute<void>(
                          builder: (_) => InvestmentDetailPage(item: item),
                        ),
                      );
                    },
                    child: const Text('home'),
                  ),
                ),
              );
            },
          ),
        ),
      ),
    );

    await tester.tap(find.text('home'));
    await tester.pumpAndSettle();
    expect(find.text('谷歌'), findsWidgets);

    await tester.tap(find.text('减仓'));
    await tester.pumpAndSettle();
    final qtyField = find.byKey(const Key('invest_qty_field'));
    await tester.ensureVisible(qtyField);
    await tester.enterText(qtyField, '1');
    final submitButton = find.byKey(const Key('invest_submit_button'));
    await tester.ensureVisible(submitButton);
    await tester.pump();
    await tester.tap(submitButton);
    await tester.pump();
    await tester.pump();

    appState.sellCompleter.complete(const AssetActionResult.success());
    await tester.pumpAndSettle();

    expect(appState.sellCalls, 1);
    expect(find.text('home'), findsOneWidget);
    expect(find.text('谷歌'), findsNothing);
    await tester.pump(const Duration(seconds: 2));
  });
}
