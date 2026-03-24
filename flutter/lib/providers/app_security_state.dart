import 'package:flutter/foundation.dart';

import '../services/biometric_service.dart';
import '../services/secure_storage_service.dart';

enum AuthLogoutMode { normal, biometricReady }

typedef RefreshSessionHandler =
    Future<Map<String, dynamic>?> Function(String refreshToken);
typedef ApplyAuthResultHandler =
    Future<void> Function(Map<String, dynamic> result);

class AppSecurityState extends ChangeNotifier {
  final SecureStorageService _secureStorage;
  final BiometricService _biometric;

  bool _biometricEnabled = false;
  bool _isAppLocked = false;
  AuthLogoutMode _logoutMode = AuthLogoutMode.normal;

  AppSecurityState({
    required SecureStorageService secureStorage,
    required BiometricService biometric,
  }) : _secureStorage = secureStorage,
       _biometric = biometric;

  bool get biometricEnabled => _biometricEnabled;
  bool get isAppLocked => _isAppLocked;
  AuthLogoutMode get logoutMode => _logoutMode;

  AuthLogoutMode parseLogoutMode(String? raw) {
    if (raw == 'biometric_ready') {
      return AuthLogoutMode.biometricReady;
    }
    return AuthLogoutMode.normal;
  }

  void syncLocalState({
    bool? biometricEnabled,
    AuthLogoutMode? logoutMode,
    bool? isAppLocked,
    bool notify = true,
  }) {
    var changed = false;
    if (biometricEnabled != null && _biometricEnabled != biometricEnabled) {
      _biometricEnabled = biometricEnabled;
      changed = true;
    }
    if (logoutMode != null && _logoutMode != logoutMode) {
      _logoutMode = logoutMode;
      changed = true;
    }
    if (isAppLocked != null && _isAppLocked != isAppLocked) {
      _isAppLocked = isAppLocked;
      changed = true;
    }
    if (changed && notify) {
      notifyListeners();
    }
  }

  Future<void> reloadBiometricPreference() async {
    try {
      final enabled = await _secureStorage.isBiometricEnabled();
      if (_biometricEnabled == enabled) return;
      _biometricEnabled = enabled;
      notifyListeners();
    } catch (e) {
      debugPrint('刷新生物识别开关失败: $e');
    }
  }

  Future<void> disableBiometric() async {
    try {
      await _secureStorage.clearBiometricEnabled();
    } catch (e) {
      debugPrint('清理生物识别开关失败: $e');
    }
    if (!_biometricEnabled) return;
    _biometricEnabled = false;
    notifyListeners();
  }

  Future<bool> setBiometricEnabled(bool enabled) async {
    if (_biometricEnabled == enabled) return true;
    final previous = _biometricEnabled;
    _biometricEnabled = enabled;
    notifyListeners();
    if (enabled) {
      final canUse = await _biometric.canUseBiometrics();
      if (!canUse) {
        _biometricEnabled = previous;
        notifyListeners();
        return false;
      }
    }
    try {
      await _secureStorage.setBiometricEnabled(enabled);
      debugPrint('Biometric switch updated: enabled=$_biometricEnabled');
      return true;
    } catch (e) {
      _biometricEnabled = previous;
      notifyListeners();
      debugPrint('写入生物识别开关失败: $e');
      return false;
    }
  }

  Future<bool> tryBiometricLogin({
    required String? refreshToken,
    required RefreshSessionHandler refreshSession,
    required ApplyAuthResultHandler applyAuthResult,
  }) async {
    if (!_biometricEnabled) {
      debugPrint('Biometric login blocked: biometric switch disabled');
      return false;
    }
    if (!await _biometric.canUseBiometrics()) {
      debugPrint('Biometric login failed: device biometrics unavailable');
      return false;
    }
    var resolvedRefreshToken = refreshToken;
    if (resolvedRefreshToken == null || resolvedRefreshToken.isEmpty) {
      try {
        resolvedRefreshToken = await _secureStorage.getRefreshToken();
      } catch (_) {
        debugPrint('Biometric login failed: unable to read refresh token');
        return false;
      }
    }
    if (resolvedRefreshToken == null || resolvedRefreshToken.isEmpty) {
      debugPrint('Biometric login failed: refresh token missing');
      return false;
    }
    final ok = await _biometric.authenticate();
    if (!ok) {
      debugPrint('Biometric login cancelled/failed in local auth');
      return false;
    }
    try {
      final result = await refreshSession(resolvedRefreshToken);
      if (result == null) return false;
      await applyAuthResult(result);
      debugPrint('Biometric login success');
      return true;
    } catch (e) {
      debugPrint('Biometric login refresh failed: $e');
      return false;
    }
  }

  void lockApp({bool notify = true}) {
    if (_isAppLocked) return;
    _isAppLocked = true;
    if (notify) {
      notifyListeners();
    }
  }

  void unlockApp({bool notify = true}) {
    if (!_isAppLocked) return;
    _isAppLocked = false;
    if (notify) {
      notifyListeners();
    }
  }
}
