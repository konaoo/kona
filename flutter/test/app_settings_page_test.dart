import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tool/pages/app_settings_page.dart';
import 'package:tool/providers/app_state.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() async {
    SharedPreferences.setMockInitialValues({});
    FlutterSecureStorage.setMockInitialValues({});
  });

  testWidgets('App settings page shows all sections and handles actions', (
    WidgetTester tester,
  ) async {
    final appState = AppState(tokenLoader: () async => null);
    await appState.setLoggedIn(
      token: 't',
      refreshToken: 'r',
      username: 'kona',
      userId: 'uid-1',
    );

    var loggedOut = false;
    await tester.pumpWidget(
      ChangeNotifierProvider<AppState>.value(
        value: appState,
        child: MaterialApp(
          home: AppSettingsPage(
            onLogout: () {
              loggedOut = true;
            },
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('切换主题'), findsOneWidget);
    expect(find.text('生物识别登录'), findsOneWidget);
    expect(find.text('修改密码'), findsOneWidget);
    expect(find.text('检查更新'), findsNothing);
    expect(find.text('关于我们'), findsNothing);
    expect(find.text('退出登录'), findsOneWidget);
    expect(find.text('问题反馈'), findsNothing);

    await tester.tap(find.text('退出登录'));
    await tester.pumpAndSettle();
    expect(loggedOut, isTrue);
  });

  testWidgets('Logout pops to root route before callback', (
    WidgetTester tester,
  ) async {
    final appState = AppState(tokenLoader: () async => null);
    await appState.setLoggedIn(
      token: 't2',
      refreshToken: 'r2',
      username: 'kona',
      userId: 'uid-2',
    );

    var loggedOut = false;
    final openSettingsKey = GlobalKey();
    const rootMarker = Key('root-marker');

    await tester.pumpWidget(
      ChangeNotifierProvider<AppState>.value(
        value: appState,
        child: MaterialApp(
          home: Builder(
            builder: (context) => Scaffold(
              body: Column(
                children: [
                  const Text('Root', key: rootMarker),
                  ElevatedButton(
                    key: openSettingsKey,
                    onPressed: () {
                      Navigator.of(context).push(
                        MaterialPageRoute(
                          builder: (_) => AppSettingsPage(
                            onLogout: () {
                              loggedOut = true;
                            },
                          ),
                        ),
                      );
                    },
                    child: const Text('Open Settings'),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(openSettingsKey));
    await tester.pumpAndSettle();
    expect(find.text('系统设置'), findsOneWidget);

    await tester.tap(find.text('退出登录'));
    await tester.pumpAndSettle();

    expect(loggedOut, isTrue);
    expect(find.byKey(rootMarker), findsOneWidget);
    expect(find.text('系统设置'), findsNothing);
  });
}
