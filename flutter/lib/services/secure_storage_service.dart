import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class SecureStorageService {
  static const _tokenKey = 'auth_access_token';
  static const _refreshTokenKey = 'auth_refresh_token';
  static const _usernameKey = 'auth_username';
  static const _biometricEnabledKey = 'auth_biometric_enabled';
  static const _logoutModeKey = 'auth_logout_mode';
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  Future<void> setToken(String token) async {
    await _storage.write(key: _tokenKey, value: token);
  }

  Future<String?> getToken() async {
    return _storage.read(key: _tokenKey);
  }

  Future<void> clearToken() async {
    await _storage.delete(key: _tokenKey);
  }

  Future<void> setRefreshToken(String token) async {
    await _storage.write(key: _refreshTokenKey, value: token);
  }

  Future<String?> getRefreshToken() async {
    return _storage.read(key: _refreshTokenKey);
  }

  Future<void> clearRefreshToken() async {
    await _storage.delete(key: _refreshTokenKey);
  }

  Future<void> setUsername(String username) async {
    await _storage.write(key: _usernameKey, value: username);
  }

  Future<String?> getUsername() async {
    return _storage.read(key: _usernameKey);
  }

  Future<void> clearUsername() async {
    await _storage.delete(key: _usernameKey);
  }

  Future<void> setBiometricEnabled(bool enabled) async {
    await _storage.write(key: _biometricEnabledKey, value: enabled ? '1' : '0');
  }

  Future<bool> isBiometricEnabled() async {
    final value = await _storage.read(key: _biometricEnabledKey);
    return value == '1';
  }

  Future<void> clearBiometricEnabled() async {
    await _storage.delete(key: _biometricEnabledKey);
  }

  Future<void> setLogoutMode(String mode) async {
    await _storage.write(key: _logoutModeKey, value: mode);
  }

  Future<String?> getLogoutMode() async {
    return _storage.read(key: _logoutModeKey);
  }

  Future<void> clearLogoutMode() async {
    await _storage.delete(key: _logoutModeKey);
  }

  Future<void> clearAllAuth() async {
    await Future.wait([clearToken(), clearRefreshToken(), clearUsername()]);
  }
}
