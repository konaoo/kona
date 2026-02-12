import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tool/main.dart';
import 'package:tool/pages/login_page.dart';
import 'package:tool/providers/app_state.dart';
import 'package:tool/widgets/add_asset_dialog.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  testWidgets('App shows splash then login page smoke test', (WidgetTester tester) async {
    final appState = AppState(tokenLoader: () async => null);
    await tester.pumpWidget(
      ChangeNotifierProvider<AppState>.value(
        value: appState,
        child: const MaterialApp(home: AuthWrapper()),
      ),
    );

    await tester.pump(const Duration(milliseconds: 50));

    expect(find.byType(LoginPage), findsOneWidget);
    expect(find.text('咔咔记账'), findsOneWidget);
    expect(find.text('邮箱地址'), findsOneWidget);
  });

  testWidgets('Add asset dialog is not dismissible by tapping barrier', (WidgetTester tester) async {
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
}
