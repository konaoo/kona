import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tool/pages/profile_page.dart';
import 'package:tool/providers/app_state.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() async {
    SharedPreferences.setMockInitialValues({});
    FlutterSecureStorage.setMockInitialValues({});
  });

  testWidgets('Profile page shows nickname only once when same as username', (
    WidgetTester tester,
  ) async {
    final appState = AppState(tokenLoader: () async => null);
    await appState.setLoggedIn(
      token: 't',
      refreshToken: 'r',
      username: 'kona',
      userId: 'uid-1',
      nickname: 'kona',
    );

    await tester.pumpWidget(
      ChangeNotifierProvider<AppState>.value(
        value: appState,
        child: MaterialApp(
          home: Scaffold(body: ProfilePage(onLogout: () {})),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('kona'), findsOneWidget);
    expect(find.text('系统设置'), findsOneWidget);
    expect(find.text('修改密码'), findsNothing);
    expect(find.text('生物识别登录'), findsNothing);
    expect(find.text('退出登录'), findsNothing);
  });
}
