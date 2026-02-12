import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:tool/main.dart';
import 'package:tool/pages/login_page.dart';
import 'package:tool/providers/app_state.dart';

void main() {
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
}
