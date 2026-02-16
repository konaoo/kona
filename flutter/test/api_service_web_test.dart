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
    expect(uri.toString(), 'http://57.180.79.186:5003/api/health');
  });
}
