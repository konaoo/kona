import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';

typedef SecureWriteOverride = Future<void> Function(String key, String value);
typedef SecureReadOverride = Future<String?> Function(String key);
typedef SecureDeleteOverride = Future<void> Function(String key);

class SecureStorageService {
  static const _tokenKey = 'auth_access_token';
  static const _refreshTokenKey = 'auth_refresh_token';
  static const _usernameKey = 'auth_username';
  static const _biometricEnabledKey = 'auth_biometric_enabled';
  static const _logoutModeKey = 'auth_logout_mode';

  final FlutterSecureStorage _storage;
  final Future<SharedPreferences> Function() _prefsLoader;
  final bool _isWeb;
  final SecureWriteOverride? _secureWriteOverride;
  final SecureReadOverride? _secureReadOverride;
  final SecureDeleteOverride? _secureDeleteOverride;

  SecureStorageService({
    FlutterSecureStorage? storage,
    Future<SharedPreferences> Function()? prefsLoader,
    bool? isWebOverride,
    SecureWriteOverride? secureWriteOverride,
    SecureReadOverride? secureReadOverride,
    SecureDeleteOverride? secureDeleteOverride,
  }) : _storage = storage ?? const FlutterSecureStorage(),
       _prefsLoader = prefsLoader ?? SharedPreferences.getInstance,
       _isWeb = isWebOverride ?? kIsWeb,
       _secureWriteOverride = secureWriteOverride,
       _secureReadOverride = secureReadOverride,
       _secureDeleteOverride = secureDeleteOverride;

  Future<void> setToken(String token) async {
    await _writeValue(_tokenKey, token);
  }

  Future<String?> getToken() async {
    return _readValue(_tokenKey);
  }

  Future<void> clearToken() async {
    await _deleteValue(_tokenKey);
  }

  Future<void> setRefreshToken(String token) async {
    await _writeValue(_refreshTokenKey, token);
  }

  Future<String?> getRefreshToken() async {
    return _readValue(_refreshTokenKey);
  }

  Future<void> clearRefreshToken() async {
    await _deleteValue(_refreshTokenKey);
  }

  Future<void> setUsername(String username) async {
    await _writeValue(_usernameKey, username);
  }

  Future<String?> getUsername() async {
    return _readValue(_usernameKey);
  }

  Future<void> clearUsername() async {
    await _deleteValue(_usernameKey);
  }

  Future<void> setBiometricEnabled(bool enabled) async {
    await _writeValue(_biometricEnabledKey, enabled ? '1' : '0');
  }

  Future<bool> isBiometricEnabled() async {
    final value = await _readValue(_biometricEnabledKey);
    return value == '1';
  }

  Future<void> clearBiometricEnabled() async {
    await _deleteValue(_biometricEnabledKey);
  }

  Future<void> setLogoutMode(String mode) async {
    await _writeValue(_logoutModeKey, mode);
  }

  Future<String?> getLogoutMode() async {
    return _readValue(_logoutModeKey);
  }

  Future<void> clearLogoutMode() async {
    await _deleteValue(_logoutModeKey);
  }

  Future<void> clearAllAuth() async {
    await Future.wait([clearToken(), clearRefreshToken(), clearUsername()]);
  }

  Future<void> _writeSecure(String key, String value) async {
    if (_secureWriteOverride != null) {
      await _secureWriteOverride(key, value);
      return;
    }
    await _storage.write(key: key, value: value);
  }

  Future<String?> _readSecure(String key) async {
    if (_secureReadOverride != null) {
      return _secureReadOverride(key);
    }
    return _storage.read(key: key);
  }

  Future<void> _deleteSecure(String key) async {
    if (_secureDeleteOverride != null) {
      await _secureDeleteOverride(key);
      return;
    }
    await _storage.delete(key: key);
  }

  Future<SharedPreferences?> _fallbackStore() async {
    if (!_isWeb) return null;
    try {
      return await _prefsLoader();
    } catch (e) {
      debugPrint('读取浏览器 fallback 存储失败: $e');
      return null;
    }
  }

  Future<void> _writeFallback(String key, String value) async {
    final prefs = await _fallbackStore();
    if (prefs == null) return;
    try {
      await prefs.setString(key, value);
    } catch (e) {
      debugPrint('写入浏览器 fallback 存储失败($key): $e');
    }
  }

  Future<String?> _readFallback(String key) async {
    final prefs = await _fallbackStore();
    if (prefs == null) return null;
    try {
      return prefs.getString(key);
    } catch (e) {
      debugPrint('读取浏览器 fallback 存储失败($key): $e');
      return null;
    }
  }

  Future<void> _deleteFallback(String key) async {
    final prefs = await _fallbackStore();
    if (prefs == null) return;
    try {
      await prefs.remove(key);
    } catch (e) {
      debugPrint('删除浏览器 fallback 存储失败($key): $e');
    }
  }

  Future<void> _writeValue(String key, String value) async {
    try {
      await _writeSecure(key, value);
    } catch (e) {
      debugPrint('secure storage 写入失败($key): $e');
      if (!_isWeb) rethrow;
    }
    if (_isWeb) {
      await _writeFallback(key, value);
    }
  }

  Future<String?> _readValue(String key) async {
    try {
      final value = await _readSecure(key);
      if (value != null && value.isNotEmpty) {
        if (_isWeb) {
          await _writeFallback(key, value);
        }
        return value;
      }
    } catch (e) {
      debugPrint('secure storage 读取失败($key): $e');
      if (!_isWeb) return null;
    }
    if (_isWeb) {
      return _readFallback(key);
    }
    return null;
  }

  Future<void> _deleteValue(String key) async {
    try {
      await _deleteSecure(key);
    } catch (e) {
      debugPrint('secure storage 删除失败($key): $e');
      if (!_isWeb) rethrow;
    }
    if (_isWeb) {
      await _deleteFallback(key);
    }
  }
}
