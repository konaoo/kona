import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tool/pages/invest_page.dart';
import 'package:tool/providers/app_state.dart';
import 'package:tool/pages/home_page.dart';

class _RefreshGuardAppState extends AppState {
  _RefreshGuardAppState() : super(tokenLoader: () async => null);

  int refreshAllCalls = 0;
  int refreshHomeDataCalls = 0;
  final Completer<void> refreshAllCompleter = Completer<void>();
  final Completer<void> refreshHomeCompleter = Completer<void>();

  @override
  Future<void> refreshAll({bool force = false}) async {
    refreshAllCalls += 1;
    await refreshAllCompleter.future;
  }

  @override
  Future<void> refreshHomeData({int? ledgerId}) async {
    refreshHomeDataCalls += 1;
    await refreshHomeCompleter.future;
  }
}

void main() {
  setUp(() async {
    SharedPreferences.setMockInitialValues({});
    FlutterSecureStorage.setMockInitialValues({});
  });

  testWidgets('HomePage has pull-to-refresh', (tester) async {
    await tester.pumpWidget(
      ChangeNotifierProvider(
        create: (_) => AppState(),
        child: MaterialApp(
          home: HomePage(onNavigate: (_) {}, onSwitchTab: (_) {}),
        ),
      ),
    );

    expect(find.byType(RefreshIndicator), findsOneWidget);
  });

  testWidgets('HomePage下拉刷新并发时仅触发一次请求', (tester) async {
    final appState = _RefreshGuardAppState();
    await tester.pumpWidget(
      ChangeNotifierProvider<AppState>.value(
        value: appState,
        child: MaterialApp(
          home: HomePage(onNavigate: (_) {}, onSwitchTab: (_) {}),
        ),
      ),
    );

    final refresh = tester.widget<RefreshIndicator>(
      find.byType(RefreshIndicator),
    );

    final first = refresh.onRefresh();
    final second = refresh.onRefresh();
    await tester.pump();

    expect(appState.refreshAllCalls, 1);
    appState.refreshAllCompleter.complete();
    await Future.wait<void>([first, second]);
  });

  testWidgets('InvestPage下拉刷新并发时仅触发一次请求', (tester) async {
    final appState = _RefreshGuardAppState();
    await tester.pumpWidget(
      ChangeNotifierProvider<AppState>.value(
        value: appState,
        child: const MaterialApp(home: InvestPage()),
      ),
    );

    final refresh = tester.widget<RefreshIndicator>(
      find.byType(RefreshIndicator),
    );

    final first = refresh.onRefresh();
    final second = refresh.onRefresh();
    await tester.pump();

    expect(appState.refreshHomeDataCalls, 1);
    appState.refreshHomeCompleter.complete();
    await Future.wait<void>([first, second]);
  });
}
