import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:tool/providers/app_state.dart';
import 'package:tool/pages/home_page.dart';

void main() {
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
}
