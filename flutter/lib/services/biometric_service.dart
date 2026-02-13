import 'package:flutter/foundation.dart';
import 'package:local_auth/local_auth.dart';

class BiometricService {
  final LocalAuthentication _localAuth = LocalAuthentication();

  bool get supportsBiometricPlatform {
    if (kIsWeb) return false;
    return defaultTargetPlatform == TargetPlatform.iOS ||
        defaultTargetPlatform == TargetPlatform.android;
  }

  Future<bool> canUseBiometrics() async {
    if (!supportsBiometricPlatform) return false;
    final canCheck = await _localAuth.canCheckBiometrics;
    final isSupported = await _localAuth.isDeviceSupported();
    return canCheck && isSupported;
  }

  Future<bool> authenticate() async {
    if (!supportsBiometricPlatform) return false;
    try {
      return await _localAuth.authenticate(
        localizedReason: '请验证身份以登录',
        options: const AuthenticationOptions(
          stickyAuth: true,
          biometricOnly: true,
        ),
      );
    } catch (e) {
      debugPrint('Biometric authenticate error: $e');
      return false;
    }
  }
}
