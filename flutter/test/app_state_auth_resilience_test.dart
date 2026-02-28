import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tool/providers/app_state.dart';
import 'package:tool/services/api_service.dart';
import 'package:tool/services/secure_storage_service.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() async {
    SharedPreferences.setMockInitialValues({});
    FlutterSecureStorage.setMockInitialValues({});
  });

  test('login succeeds even if auth persistence fails', () async {
    final failingStorage = SecureStorageService(
      isWebOverride: false,
      secureWriteOverride: (_, __) async {
        throw Exception('secure write failed');
      },
      secureReadOverride: (_) async => null,
      secureDeleteOverride: (_) async {},
    );
    final appState = AppState(
      tokenLoader: () async => null,
      secureStorage: failingStorage,
      loginHandler: ({required username, required password}) async => {
        'access_token': 'access-ok',
        'refresh_token': 'refresh-ok',
        'user': {'id': 'u-1', 'username': 'kona'},
      },
    );

    final ok = await appState.login(username: 'kona', password: 'pw');

    expect(ok, isTrue);
    expect(appState.isLoggedIn, isTrue);
    expect(appState.token, 'access-ok');
    expect(appState.authErrorMessage, isNull);
  });

  test('login maps 401 to invalid credentials message', () async {
    final appState = AppState(
      tokenLoader: () async => null,
      loginHandler: ({required username, required password}) async {
        throw ApiException('Unauthorized', statusCode: 401);
      },
    );

    final ok = await appState.login(username: 'kona', password: 'bad');

    expect(ok, isFalse);
    expect(appState.authErrorMessage, '用户名/密码错误，请重新再试');
  });

  test('login maps null-check error to storage guidance', () async {
    final appState = AppState(
      tokenLoader: () async => null,
      loginHandler: ({required username, required password}) async {
        throw Exception('Null check operator used on a null value');
      },
    );

    final ok = await appState.login(username: 'kona', password: 'pw');

    expect(ok, isFalse);
    expect(appState.authErrorMessage, '浏览器存储环境异常，请刷新页面或切换 HTTPS 后重试');
  });

  test('auth expired callback clears session immediately', () async {
    final appState = AppState(tokenLoader: () async => null);
    await Future<void>.delayed(const Duration(milliseconds: 30));
    await appState.setLoggedIn(
      token: 't-auth-expire',
      refreshToken: 'r-auth-expire',
      username: 'kona',
      userId: 'uid-auth-expire',
    );

    expect(appState.sessionBootState, SessionBootState.authenticated);
    final api = ApiService();
    expect(api.onAuthExpired, isNotNull);
    api.onAuthExpired?.call();
    await Future<void>.delayed(const Duration(milliseconds: 20));

    expect(appState.sessionBootState, SessionBootState.unauthenticated);
    expect(appState.isLoggedIn, isFalse);
  });
}
