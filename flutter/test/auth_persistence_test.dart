import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tool/providers/app_state.dart';
import 'dart:convert';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() async {
    SharedPreferences.setMockInitialValues({});
    FlutterSecureStorage.setMockInitialValues({});
  });

  test('AppState persists token to secure storage', () async {
    FlutterSecureStorage.setMockInitialValues({
      'auth_logout_mode': 'biometric_ready',
    });
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
    final logoutMode = await storage.read(key: 'auth_logout_mode');
    expect(token, 't123');
    expect(refresh, 'r123');
    expect(logoutMode, isNull);
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
    expect(await storage.read(key: 'auth_logout_mode'), 'biometric_ready');
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
    expect(await storage.read(key: 'auth_logout_mode'), 'normal');
  });

  test('AppState persists user profile cache for avatar/nickname', () async {
    final appState = AppState(tokenLoader: () async => null);

    await appState.setLoggedIn(
      token: 't_profile',
      refreshToken: 'r_profile',
      username: 'u_profile',
      userId: 'uid-profile',
      userNumber: 10001,
      nickname: 'Kona',
      avatar: 'base64-avatar',
    );

    final prefs = await SharedPreferences.getInstance();
    final rawByName = prefs.getString('u:name:u_profile:user_profile');
    expect(rawByName, isNotNull);
    final byName = jsonDecode(rawByName!) as Map<String, dynamic>;
    final byNameData = byName['data'] as Map<String, dynamic>;
    expect(byNameData['username'], 'u_profile');
    expect(byNameData['nickname'], 'Kona');
    expect(byNameData['avatar'], 'base64-avatar');
    expect(byNameData['user_number'], 10001);
  });

  test('Logout clears user profile cache when biometric is disabled', () async {
    final appState = AppState(tokenLoader: () async => null);

    await appState.setLoggedIn(
      token: 't_profile_clear',
      refreshToken: 'r_profile_clear',
      username: 'u_profile_clear',
      userId: 'uid-profile-clear',
      nickname: 'ToClear',
      avatar: 'avatar-clear',
    );

    appState.logout();
    await Future<void>.delayed(const Duration(milliseconds: 30));

    final prefs = await SharedPreferences.getInstance();
    expect(prefs.getString('u:name:u_profile_clear:user_profile'), isNull);
    expect(prefs.getString('u:uid-profile-clear:user_profile'), isNull);
  });
}
