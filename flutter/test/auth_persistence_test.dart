import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:tool/providers/app_state.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('AppState persists token to secure storage', () async {
    FlutterSecureStorage.setMockInitialValues({});
    final appState = AppState();

    await appState.setLoggedIn(
      token: 't123',
      email: 'u@example.com',
      userId: 'uid-1',
    );

    final storage = FlutterSecureStorage();
    final token = await storage.read(key: 'auth_token');
    expect(token, 't123');
  });
}
