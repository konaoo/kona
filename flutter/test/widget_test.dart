import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tool/pages/login_page.dart';
import 'package:tool/providers/app_state.dart';
import 'package:tool/widgets/add_asset_dialog.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  testWidgets('Login page smoke test', (WidgetTester tester) async {
    final appState = AppState(tokenLoader: () async => null);
    await tester.pumpWidget(
      ChangeNotifierProvider<AppState>.value(
        value: appState,
        child: MaterialApp(home: LoginPage(onLoginSuccess: () {})),
      ),
    );

    await tester.pump();

    expect(find.byType(LoginPage), findsOneWidget);
    expect(find.text('咔咔记账'), findsOneWidget);
    expect(find.text('账号'), findsOneWidget);
    expect(find.text('密码'), findsOneWidget);
    expect(find.byKey(const Key('login_brand_area')), findsOneWidget);
    expect(find.byKey(const Key('login_primary_action')), findsOneWidget);
    expect(find.text('注册'), findsOneWidget);
  });

  testWidgets('Add asset dialog is not dismissible by tapping barrier', (
    WidgetTester tester,
  ) async {
    final appState = AppState(tokenLoader: () async => null);
    await tester.pumpWidget(
      ChangeNotifierProvider<AppState>.value(
        value: appState,
        child: MaterialApp(
          home: Builder(
            builder: (context) => Scaffold(
              body: Center(
                child: ElevatedButton(
                  onPressed: () {
                    showDialog(
                      context: context,
                      barrierDismissible: false,
                      builder: (_) => AddAssetDialog(hostContext: context),
                    );
                  },
                  child: const Text('open-dialog'),
                ),
              ),
            ),
          ),
        ),
      ),
    );

    await tester.tap(find.text('open-dialog'));
    await tester.pumpAndSettle();
    expect(find.byType(AddAssetDialog), findsOneWidget);

    await tester.tapAt(const Offset(2, 2));
    await tester.pumpAndSettle();
    expect(find.byType(AddAssetDialog), findsOneWidget);
  });

  testWidgets('Add asset dialog shows currency selector for all asset types', (
    WidgetTester tester,
  ) async {
    final appState = AppState(tokenLoader: () async => null);
    await tester.pumpWidget(
      ChangeNotifierProvider<AppState>.value(
        value: appState,
        child: MaterialApp(
          home: Builder(
            builder: (context) => Scaffold(
              body: Center(
                child: ElevatedButton(
                  onPressed: () {
                    showDialog(
                      context: context,
                      barrierDismissible: false,
                      builder: (_) => AddAssetDialog(hostContext: context),
                    );
                  },
                  child: const Text('open-dialog'),
                ),
              ),
            ),
          ),
        ),
      ),
    );

    await tester.tap(find.text('open-dialog'));
    await tester.pumpAndSettle();

    expect(find.text('币种'), findsOneWidget);
    expect(find.text('🇨🇳'), findsOneWidget);
    expect(find.text('CNY'), findsWidgets);

    await tester.tap(find.text('📦 其他资产'));
    await tester.pumpAndSettle();
    expect(find.text('币种'), findsOneWidget);
    expect(find.text('CNY'), findsWidgets);

    await tester.tap(find.text('💳 我的负债'));
    await tester.pumpAndSettle();
    expect(find.text('币种'), findsOneWidget);
    expect(find.text('CNY'), findsWidgets);

    await tester.tap(find.text('💰 现金资产'));
    await tester.pumpAndSettle();
    expect(find.text('币种'), findsOneWidget);
  });

  testWidgets('Currency dropdown is rendered below trigger field', (
    WidgetTester tester,
  ) async {
    final appState = AppState(tokenLoader: () async => null);
    await tester.pumpWidget(
      ChangeNotifierProvider<AppState>.value(
        value: appState,
        child: MaterialApp(
          home: Builder(
            builder: (context) => Scaffold(
              body: Center(
                child: ElevatedButton(
                  onPressed: () {
                    showDialog(
                      context: context,
                      barrierDismissible: false,
                      builder: (_) => AddAssetDialog(hostContext: context),
                    );
                  },
                  child: const Text('open-dialog'),
                ),
              ),
            ),
          ),
        ),
      ),
    );

    await tester.tap(find.text('open-dialog'));
    await tester.pumpAndSettle();

    final trigger = find.byKey(const Key('add_asset_currency_trigger'));
    expect(trigger, findsOneWidget);
    await tester.tap(trigger);
    await tester.pumpAndSettle();

    final triggerBottom = tester.getRect(trigger).bottom;
    final firstOverlayItemTop = tester.getRect(find.text('USD').first).top;
    expect(firstOverlayItemTop, greaterThan(triggerBottom));
  });
}
