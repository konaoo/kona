import 'package:flutter_test/flutter_test.dart';
import 'package:tool/providers/app_security_state.dart';
import 'package:tool/services/biometric_service.dart';
import 'package:tool/services/secure_storage_service.dart';

class _FakeBiometricService extends BiometricService {
  _FakeBiometricService({
    required this.canUse,
    required this.authenticateResult,
  });

  final bool canUse;
  final bool authenticateResult;

  @override
  Future<bool> canUseBiometrics() async => canUse;

  @override
  Future<bool> authenticate() async => authenticateResult;
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('AppSecurityState reverts biometric switch when device cannot use biometrics', () async {
    final writes = <String, String>{};
    final state = AppSecurityState(
      secureStorage: SecureStorageService(
        secureWriteOverride: (key, value) async => writes[key] = value,
        secureReadOverride: (_) async => null,
        secureDeleteOverride: (_) async {},
      ),
      biometric: _FakeBiometricService(canUse: false, authenticateResult: false),
    );

    final ok = await state.setBiometricEnabled(true);

    expect(ok, isFalse);
    expect(state.biometricEnabled, isFalse);
    expect(writes, isEmpty);
  });

  test('AppSecurityState completes biometric login through refresh callback', () async {
    final state = AppSecurityState(
      secureStorage: SecureStorageService(
        secureWriteOverride: (ignoredKey, ignoredValue) async {},
        secureReadOverride: (storageKey) async {
          if (storageKey == 'auth_refresh_token') return 'refresh-from-storage';
          return null;
        },
        secureDeleteOverride: (_) async {},
      ),
      biometric: _FakeBiometricService(canUse: true, authenticateResult: true),
    );

    state.syncLocalState(biometricEnabled: true, notify: false);

    var appliedToken = '';
    final ok = await state.tryBiometricLogin(
      refreshToken: null,
      refreshSession: (refreshToken) async {
        expect(refreshToken, 'refresh-from-storage');
        return <String, dynamic>{
          'access_token': 'new-access',
          'refresh_token': 'new-refresh',
          'user': <String, dynamic>{'username': 'kona'},
        };
      },
      applyAuthResult: (result) async {
        appliedToken = result['access_token']?.toString() ?? '';
      },
    );

    expect(ok, isTrue);
    expect(appliedToken, 'new-access');
  });
}
