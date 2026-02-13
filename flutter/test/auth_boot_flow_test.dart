import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:tool/main.dart';
import 'package:tool/pages/login_page.dart';
import 'package:tool/providers/app_state.dart';

Widget _buildApp(AppState appState) {
  return ChangeNotifierProvider<AppState>.value(
    value: appState,
    child: const MaterialApp(home: AuthWrapper()),
  );
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() async {
    SharedPreferences.setMockInitialValues({});
    FlutterSecureStorage.setMockInitialValues({});
  });

  testWidgets('无 token 时：启动页后进入登录页', (tester) async {
    final appState = AppState(
      tokenLoader: () async {
        await Future<void>.delayed(const Duration(milliseconds: 10));
        return null;
      },
    );

    await tester.pumpWidget(_buildApp(appState));
    expect(find.byType(StartupSplashPage), findsOneWidget);
    expect(find.byType(LoginPage), findsNothing);

    await tester.pump(const Duration(milliseconds: 20));
    expect(find.byType(LoginPage), findsOneWidget);
    expect(find.byType(MainApp), findsNothing);
  });

  testWidgets('normal + refresh token：启动时静默 refresh 恢复登录', (tester) async {
    FlutterSecureStorage.setMockInitialValues({
      'auth_refresh_token': 'refresh-only',
      'auth_username': 'demo',
      'auth_logout_mode': 'normal',
    });
    final appState = AppState(
      tokenLoader: () async {
        await Future<void>.delayed(const Duration(milliseconds: 10));
        return null;
      },
      profileLoader: () async => {
        'username': 'demo',
        'id': 'u-1',
        'user_number': 1,
        'nickname': 'demo',
        'avatar': null,
      },
      refreshLoader: (refreshToken) async {
        return {
          'access_token': 'token-refreshed',
          'refresh_token': 'refresh-refreshed',
          'user': {
            'username': 'demo',
            'id': 'u-1',
            'user_number': 1,
            'nickname': 'demo',
            'avatar': null,
          },
        };
      },
    );

    await tester.pumpWidget(_buildApp(appState));
    expect(find.byType(StartupSplashPage), findsOneWidget);

    await tester.pump(const Duration(milliseconds: 40));
    expect(find.byType(MainApp), findsOneWidget);
    expect(find.byType(LoginPage), findsNothing);
  });

  testWidgets('biometric_ready：启动后停留登录页，不自动登录', (tester) async {
    FlutterSecureStorage.setMockInitialValues({
      'auth_refresh_token': 'refresh-biometric',
      'auth_username': 'demo',
      'auth_biometric_enabled': '1',
      'auth_logout_mode': 'biometric_ready',
    });
    final appState = AppState(
      tokenLoader: () async {
        await Future<void>.delayed(const Duration(milliseconds: 10));
        return null;
      },
    );

    await tester.pumpWidget(_buildApp(appState));
    expect(find.byType(StartupSplashPage), findsOneWidget);

    await tester.pump(const Duration(milliseconds: 20));
    expect(find.byType(LoginPage), findsOneWidget);
    expect(find.byType(MainApp), findsNothing);
  });

  testWidgets('有 token 且校验成功：不出现登录页闪现', (tester) async {
    FlutterSecureStorage.setMockInitialValues({
      'auth_refresh_token': 'refresh-ok',
      'auth_username': 'demo',
    });
    final appState = AppState(
      tokenLoader: () async {
        await Future<void>.delayed(const Duration(milliseconds: 10));
        return 'token-ok';
      },
      profileLoader: () async {
        await Future<void>.delayed(const Duration(milliseconds: 30));
        return {
          'username': 'demo',
          'id': 'u-1',
          'user_number': 1,
          'nickname': 'demo',
          'avatar': null,
        };
      },
    );

    await tester.pumpWidget(_buildApp(appState));
    expect(find.byType(StartupSplashPage), findsOneWidget);

    await tester.pump(const Duration(milliseconds: 15));
    expect(find.byType(MainApp), findsOneWidget);
    expect(find.byType(LoginPage), findsNothing);

    await tester.pump(const Duration(milliseconds: 50));
    expect(find.byType(MainApp), findsOneWidget);
    expect(find.byType(LoginPage), findsNothing);
  });

  testWidgets('有 token 但校验失败：回退到登录页', (tester) async {
    FlutterSecureStorage.setMockInitialValues({
      'auth_refresh_token': 'refresh-expired',
      'auth_username': 'demo',
    });
    final appState = AppState(
      tokenLoader: () async {
        await Future<void>.delayed(const Duration(milliseconds: 10));
        return 'token-expired';
      },
      profileLoader: () async {
        await Future<void>.delayed(const Duration(milliseconds: 30));
        return null;
      },
      refreshLoader: (refreshToken) async {
        await Future<void>.delayed(const Duration(milliseconds: 20));
        return null;
      },
    );

    await tester.pumpWidget(_buildApp(appState));
    expect(find.byType(StartupSplashPage), findsOneWidget);

    await tester.pump(const Duration(milliseconds: 15));
    expect(find.byType(MainApp), findsOneWidget);

    await tester.pump(const Duration(milliseconds: 50));
    expect(find.byType(LoginPage), findsOneWidget);
    expect(find.byType(MainApp), findsNothing);
  });
}
