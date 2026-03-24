import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tool/services/cache_service.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('CacheService stores and loads JSON', () async {
    SharedPreferences.setMockInitialValues({});
    final cache = CacheService();

    final data = {'a': 1, 'b': 'x'};
    await cache.setJson('test_key', data);
    final loaded = await cache.getJson('test_key');

    expect(loaded, data);
  });
}
