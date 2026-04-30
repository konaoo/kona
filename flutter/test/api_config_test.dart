import 'package:flutter_test/flutter_test.dart';
import 'package:tool/config/api_config.dart';

void main() {
  test('splitBaseUrlList parses comma separated values', () {
    expect(
      ApiConfig.splitBaseUrlList(
        ' https://a.example.com,https://b.example.com/ , ',
      ),
      <String>['https://a.example.com', 'https://b.example.com/'],
    );
  });

  test('normalizeBaseUrls trims trailing slash and removes duplicates', () {
    expect(
      ApiConfig.normalizeBaseUrls(const <String>[
        'https://api.example.com/',
        'https://api.example.com',
        'http://114.132.238.12',
      ]),
      <String>['https://api.example.com', 'http://114.132.238.12'],
    );
  });

  test('normalizeBaseUrls rejects invalid schemes', () {
    expect(
      () => ApiConfig.normalizeBaseUrls(const <String>['ftp://example.com']),
      throwsA(isA<FormatException>()),
    );
  });
}
