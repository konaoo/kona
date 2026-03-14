import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tool/providers/app_auth_state.dart';
import 'package:tool/providers/app_sync_state.dart';
import 'package:tool/services/cache_service.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
    FlutterSecureStorage.setMockInitialValues({});
  });

  test(
    'AppSyncState builds user cache scopes and saves domain envelope',
    () async {
      final state = AppSyncState(cache: CacheService());

      expect(
        state.cacheScopes(username: null, userId: null),
        equals(const <String>['guest']),
      );
      expect(
        state.cacheScopes(username: 'Kona', userId: 'u-1'),
        equals(const <String>['name:kona', 'u-1']),
      );

      await state.saveDomainEnvelope(
        domain: 'portfolio',
        data: <String, dynamic>{'items': <dynamic>[]},
        staleAfter: const Duration(minutes: 5),
        username: 'Kona',
        userId: 'u-1',
      );

      final prefs = await SharedPreferences.getInstance();
      expect(prefs.getString('u:name:kona:portfolio'), isNotNull);
      expect(prefs.getString('u:u-1:portfolio'), isNotNull);
    },
  );

  test('AppSyncState persists and restores user profile cache', () async {
    final state = AppSyncState(cache: CacheService());
    final authState = AppAuthState();
    authState.syncLocalState(
      username: 'kona',
      userId: 'uid-1',
      userNumber: 1001,
      nickname: '毛毛',
      avatar: 'avatar-1',
      createdAtRaw: '2026-03-14',
      notify: false,
    );

    await state.persistUserProfileCache(
      authState: authState,
      staleAfter: const Duration(days: 30),
      userProfileDomain: 'user_profile',
    );

    final restoredAuth = AppAuthState();
    await state.restoreUserProfileCache(
      authState: restoredAuth,
      userProfileDomain: 'user_profile',
      usernameHint: 'kona',
      userIdHint: 'uid-1',
    );

    expect(restoredAuth.username, 'kona');
    expect(restoredAuth.userId, 'uid-1');
    expect(restoredAuth.userNumber, 1001);
    expect(restoredAuth.nickname, '毛毛');
    expect(restoredAuth.avatar, 'avatar-1');
    expect(restoredAuth.createdAtRaw, '2026-03-14');
  });

  test('AppSyncState applies quote policy and decides static sync skip', () {
    final state = AppSyncState(cache: CacheService());

    state.applyQuotePolicy(<String, dynamic>{
      'interval_open_sec': 8,
      'interval_closed_sec': 180,
      'interval_us_extended_sec': 12,
    }, notify: false);

    expect(state.quoteIntervalOpenSec, 8);
    expect(state.quoteIntervalClosedSec, 180);
    expect(state.quoteIntervalUsExtendedSec, 12);

    expect(
      state.canSkipStaticSyncCheck(
        force: false,
        staticDataTtl: const Duration(minutes: 5),
      ),
      isFalse,
    );

    state.syncVersions['portfolio'] = 'v1';
    state.markAssetFresh(
      updatedAt: DateTime.now().subtract(const Duration(minutes: 1)),
      notify: false,
    );

    expect(
      state.canSkipStaticSyncCheck(
        force: false,
        staticDataTtl: const Duration(minutes: 5),
      ),
      isTrue,
    );
    expect(
      state.canSkipStaticSyncCheck(
        force: true,
        staticDataTtl: const Duration(minutes: 5),
      ),
      isFalse,
    );
  });
}
