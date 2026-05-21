import 'package:flutter_test/flutter_test.dart';
import 'package:tool/config/api_config.dart';
import 'package:tool/services/api_service.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late ApiService api;

  setUp(() {
    api = ApiService();
  });

  tearDown(() {
    api.setPostOverrideForTesting(null);
  });

  test('resolveLoginBaseUrls removes duplicates and keeps primary first', () {
    final resolved = ApiService.resolveLoginBaseUrls(
      candidatesOverride: <String>[
        'http://114.132.246.156/',
        'http://114.132.246.156',
      ],
    );
    expect(resolved.first, ApiConfig.baseUrl);
    expect(resolved, <String>['http://114.132.246.156']);
    // baseUrl + deduplicated same ip = 1 entry
    expect(resolved.length, 1);
  });

  test(
    'login retries fallback hosts in order when network errors happen',
    () async {
      final calledEndpoints = <String>[];
      api.setPostOverrideForTesting((
        endpoint,
        data, {
        bool retryOnTransient = false,
        int transientMaxAttempts = 2,
      }) async {
        calledEndpoints.add(endpoint);
        if (calledEndpoints.length < 3) {
          throw ApiException('网络连接异常，请检查网络后重试');
        }
        return <String, dynamic>{
          'access_token': 'access-ok',
          'refresh_token': 'refresh-ok',
        };
      });

      final result = await api.login(
        username: 'konae',
        password: 'pw',
        baseUrlCandidatesOverride: const <String>[
          'http://114.132.246.156',
          'http://114.132.246.156:80',
          'http://114.132.246.156:52345',
        ],
      );

      expect(result?['access_token'], 'access-ok');
      expect(calledEndpoints, <String>[
        ApiConfig.login,
        'http://114.132.246.156:80${ApiConfig.login}',
        'http://114.132.246.156:52345${ApiConfig.login}',
      ]);
    },
  );

  test('login should not fallback on auth failure', () async {
    final calledEndpoints = <String>[];
    api.setPostOverrideForTesting((
      endpoint,
      data, {
      bool retryOnTransient = false,
      int transientMaxAttempts = 2,
    }) async {
      calledEndpoints.add(endpoint);
      throw ApiException('Unauthorized', statusCode: 401);
    });

    expect(
      () => api.login(
        username: 'konae',
        password: 'bad',
        baseUrlCandidatesOverride: const <String>[
          'http://114.132.246.156',
          'http://114.132.246.156:80',
        ],
      ),
      throwsA(isA<ApiException>()),
    );
    expect(calledEndpoints, <String>[ApiConfig.login]);
  });
}
