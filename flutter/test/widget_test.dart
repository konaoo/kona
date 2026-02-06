import 'package:flutter_test/flutter_test.dart';
import 'package:tool/main.dart';

void main() {
  testWidgets('App shows login page smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const MyApp());
    await tester.pumpAndSettle();

    expect(find.text('咔咔记账'), findsOneWidget);
    expect(find.text('邮箱地址'), findsOneWidget);
  });
}
