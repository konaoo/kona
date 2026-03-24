import 'package:flutter_test/flutter_test.dart';
import 'package:tool/providers/app_auth_state.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('AppAuthState applies auth result and marks session authenticated', () {
    final state = AppAuthState();

    state.applyAuthResult(<String, dynamic>{
      'access_token': 'access-1',
      'refresh_token': 'refresh-1',
      'user': <String, dynamic>{
        'id': 'u-1',
        'username': 'kona',
        'user_number': 1001,
        'nickname': '毛毛',
        'avatar': 'avatar-data',
        'created_at': '2026-03-14T10:00:00',
      },
    });

    expect(state.isLoggedIn, isTrue);
    expect(state.sessionBootState, SessionBootState.authenticated);
    expect(state.token, 'access-1');
    expect(state.refreshToken, 'refresh-1');
    expect(state.username, 'kona');
    expect(state.userId, 'u-1');
    expect(state.userNumber, 1001);
    expect(state.nickname, '毛毛');
    expect(state.avatar, 'avatar-data');
    expect(state.createdAtRaw, '2026-03-14T10:00:00');
    expect(state.authErrorMessage, isNull);
  });

  test('AppAuthState restores cached profile without覆盖已有用户名和用户ID', () {
    final state = AppAuthState();
    state.syncLocalState(
      username: 'current-name',
      userId: 'current-id',
      nickname: '旧昵称',
      notify: false,
    );

    state.restoreCachedProfile(
      username: 'cached-name',
      userId: 'cached-id',
      userNumber: 2002,
      nickname: '缓存昵称',
      avatar: 'cached-avatar',
      createdAtRaw: '2026-03-13',
    );

    expect(state.username, 'current-name');
    expect(state.userId, 'current-id');
    expect(state.userNumber, 2002);
    expect(state.nickname, '缓存昵称');
    expect(state.avatar, 'cached-avatar');
    expect(state.createdAtRaw, '2026-03-13');
  });
}
