import 'package:flutter_test/flutter_test.dart';
import 'package:tool/services/api_service.dart';

void main() {
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
}
