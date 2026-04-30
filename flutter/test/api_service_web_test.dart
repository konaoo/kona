import 'package:flutter_test/flutter_test.dart';
import 'package:tool/services/api_service.dart';

void main() {
  test('ApiService buildApiUri uses provided web origin when web', () {
    final uri = ApiService.buildApiUri(
      '/api/health',
      isWebOverride: true,
      webOriginOverride: 'https://demo.example.com',
    );
    expect(uri.toString(), 'https://demo.example.com/api/health');
  });

  test('ApiService buildApiUri uses mobile base url when not web', () {
    final uri = ApiService.buildApiUri('/api/health', isWebOverride: false);
    expect(uri.toString(), 'http://114.132.238.12/api/health');
  });

  test('ApiService rejects insecure http when disabled', () {
    expect(
      () => ApiService.buildApiUri(
        '/api/health',
        isWebOverride: false,
        allowInsecureHttpOverride: false,
      ),
      throwsA(isA<StateError>()),
    );
  });

  test('ApiService accepts https when insecure http is disabled', () {
    final uri = ApiService.buildApiUri(
      '/api/health',
      isWebOverride: false,
      mobileBaseUrlOverride: 'https://api.example.com',
      allowInsecureHttpOverride: false,
    );
    expect(uri.toString(), 'https://api.example.com/api/health');
  });

  test('ApiException toString returns readable message', () {
    final e = ApiException('登录响应异常，请稍后重试');
    expect(e.toString(), '登录响应异常，请稍后重试');
  });
}
