import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:tool/services/api_service.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    FlutterSecureStorage.setMockInitialValues({});
    ApiService().clearAuthTokens();
  });

  test('ApiService 请求头会带 X-Request-Id', () {
    final api = ApiService();
    api.setToken('token-demo');

    final headers = api.debugBuildHeaders(requestId: 'trace-demo-1');

    expect(headers['Content-Type'], 'application/json');
    expect(headers['Authorization'], 'Bearer token-demo');
    expect(headers['X-Request-Id'], 'trace-demo-1');
  });

  test('ApiService 可在无 token 场景下单独构建追踪头', () {
    final api = ApiService();
    api.clearToken();

    final headers = api.debugBuildHeaders(
      requestId: 'trace-demo-2',
      includeAuth: false,
    );

    expect(headers['Content-Type'], 'application/json');
    expect(headers.containsKey('Authorization'), false);
    expect(headers['X-Request-Id'], 'trace-demo-2');
  });

  test('ApiService 续签优先使用内存里的 refresh token', () async {
    FlutterSecureStorage.setMockInitialValues({
      'auth_refresh_token': 'refresh-from-storage',
    });
    final api = ApiService();
    api.setAuthTokens(
      accessToken: 'token-demo',
      refreshToken: 'refresh-from-memory',
    );

    final resolved = await api.debugResolveRefreshToken();

    expect(resolved, 'refresh-from-memory');
  });
}
