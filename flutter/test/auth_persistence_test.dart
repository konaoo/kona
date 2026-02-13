import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tool/providers/app_state.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() async {
    SharedPreferences.setMockInitialValues({});
    FlutterSecureStorage.setMockInitialValues({});
  });

  test('AppState persists token to secure storage', () async {
    final appState = AppState();

    await appState.setLoggedIn(
      token: 't123',
      refreshToken: 'r123',
      username: 'u_test',
      userId: 'uid-1',
    );

    final storage = FlutterSecureStorage();
    final token = await storage.read(key: 'auth_access_token');
    final refresh = await storage.read(key: 'auth_refresh_token');
    expect(token, 't123');
    expect(refresh, 'r123');
  });

  test('Logout keeps refresh token when biometric is enabled', () async {
    FlutterSecureStorage.setMockInitialValues({'auth_biometric_enabled': '1'});
    final appState = AppState(tokenLoader: () async => null);
    await Future<void>.delayed(const Duration(milliseconds: 20));
    expect(appState.biometricEnabled, isTrue);

    await appState.setLoggedIn(
      token: 't_keep',
      refreshToken: 'r_keep',
      username: 'u_keep',
      userId: 'uid-keep',
    );
    appState.logout();
    await Future<void>.delayed(const Duration(milliseconds: 20));

    final storage = FlutterSecureStorage();
    expect(await storage.read(key: 'auth_access_token'), isNull);
    expect(await storage.read(key: 'auth_refresh_token'), 'r_keep');
    expect(await storage.read(key: 'auth_biometric_enabled'), '1');
  });

  test('Logout clears refresh token when biometric is disabled', () async {
    FlutterSecureStorage.setMockInitialValues({});
    final appState = AppState(tokenLoader: () async => null);
    await Future<void>.delayed(const Duration(milliseconds: 20));
    expect(appState.biometricEnabled, isFalse);

    await appState.setLoggedIn(
      token: 't_clear',
      refreshToken: 'r_clear',
      username: 'u_clear',
      userId: 'uid-clear',
    );
    appState.logout();
    await Future<void>.delayed(const Duration(milliseconds: 20));

    final storage = FlutterSecureStorage();
    expect(await storage.read(key: 'auth_access_token'), isNull);
    expect(await storage.read(key: 'auth_refresh_token'), isNull);
  });
}
