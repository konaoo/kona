import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tool/services/secure_storage_service.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() async {
    SharedPreferences.setMockInitialValues({});
    FlutterSecureStorage.setMockInitialValues({});
  });

  test('web write falls back when secure storage write throws', () async {
    final service = SecureStorageService(
      isWebOverride: true,
      secureWriteOverride: (key, value) async {
        throw Exception('secure write failed');
      },
      secureReadOverride: (_) async {
        throw Exception('secure read failed');
      },
      secureDeleteOverride: (_) async {
        throw Exception('secure delete failed');
      },
    );

    await service.setToken('token-web-fallback');

    final prefs = await SharedPreferences.getInstance();
    expect(prefs.getString('auth_access_token'), 'token-web-fallback');
  });

  test('web read falls back when secure storage read throws', () async {
    SharedPreferences.setMockInitialValues({
      'auth_access_token': 'token-from-fallback',
    });

    final service = SecureStorageService(
      isWebOverride: true,
      secureReadOverride: (_) async {
        throw Exception('secure read failed');
      },
    );

    final token = await service.getToken();
    expect(token, 'token-from-fallback');
  });

  test('clearAllAuth clears both secure and fallback storage', () async {
    SharedPreferences.setMockInitialValues({
      'auth_access_token': 'prefs-token',
      'auth_refresh_token': 'prefs-refresh',
      'auth_username': 'prefs-user',
    });
    FlutterSecureStorage.setMockInitialValues({
      'auth_access_token': 'secure-token',
      'auth_refresh_token': 'secure-refresh',
      'auth_username': 'secure-user',
    });

    final service = SecureStorageService(isWebOverride: true);
    await service.clearAllAuth();

    final prefs = await SharedPreferences.getInstance();
    final storage = FlutterSecureStorage();
    expect(prefs.getString('auth_access_token'), isNull);
    expect(prefs.getString('auth_refresh_token'), isNull);
    expect(prefs.getString('auth_username'), isNull);
    expect(await storage.read(key: 'auth_access_token'), isNull);
    expect(await storage.read(key: 'auth_refresh_token'), isNull);
    expect(await storage.read(key: 'auth_username'), isNull);
  });
}
