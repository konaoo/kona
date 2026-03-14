import 'package:flutter/foundation.dart';

enum SessionBootState { initializing, authenticated, unauthenticated }

class AppAuthState extends ChangeNotifier {
  static const Object _noChange = Object();

  bool _isLoggedIn = false;
  SessionBootState _sessionBootState = SessionBootState.initializing;
  bool _isSessionChecking = false;
  String? _token;
  String? _refreshToken;
  String? _username;
  String? _userId;
  int? _userNumber;
  String? _nickname;
  String? _avatar;
  String? _createdAtRaw;
  String? _authErrorMessage;

  bool get isLoggedIn => _isLoggedIn;
  SessionBootState get sessionBootState => _sessionBootState;
  bool get isSessionChecking => _isSessionChecking;
  String? get token => _token;
  String? get refreshToken => _refreshToken;
  String? get username => _username;
  String? get userId => _userId;
  int? get userNumber => _userNumber;
  String? get nickname => _nickname;
  String? get avatar => _avatar;
  String? get createdAtRaw => _createdAtRaw;
  String? get authErrorMessage => _authErrorMessage;

  void syncLocalState({
    bool? isLoggedIn,
    SessionBootState? sessionBootState,
    bool? isSessionChecking,
    Object? token = _noChange,
    Object? refreshToken = _noChange,
    Object? username = _noChange,
    Object? userId = _noChange,
    Object? userNumber = _noChange,
    Object? nickname = _noChange,
    Object? avatar = _noChange,
    Object? createdAtRaw = _noChange,
    Object? authErrorMessage = _noChange,
    bool notify = true,
  }) {
    var changed = false;

    if (isLoggedIn != null && _isLoggedIn != isLoggedIn) {
      _isLoggedIn = isLoggedIn;
      changed = true;
    }
    if (sessionBootState != null && _sessionBootState != sessionBootState) {
      _sessionBootState = sessionBootState;
      changed = true;
    }
    if (isSessionChecking != null && _isSessionChecking != isSessionChecking) {
      _isSessionChecking = isSessionChecking;
      changed = true;
    }
    if (token != _noChange) {
      final nextToken = _stringValue(token);
      if (_token != nextToken) {
        _token = nextToken;
        changed = true;
      }
    }
    if (refreshToken != _noChange) {
      final nextRefreshToken = _stringValue(refreshToken);
      if (_refreshToken != nextRefreshToken) {
        _refreshToken = nextRefreshToken;
        changed = true;
      }
    }
    if (username != _noChange) {
      final nextUsername = _stringValue(username);
      if (_username != nextUsername) {
        _username = nextUsername;
        changed = true;
      }
    }
    if (userId != _noChange) {
      final nextUserId = _stringValue(userId);
      if (_userId != nextUserId) {
        _userId = nextUserId;
        changed = true;
      }
    }
    if (userNumber != _noChange) {
      final nextUserNumber = _intValue(userNumber);
      if (_userNumber != nextUserNumber) {
        _userNumber = nextUserNumber;
        changed = true;
      }
    }
    if (nickname != _noChange) {
      final nextNickname = _stringValue(nickname);
      if (_nickname != nextNickname) {
        _nickname = nextNickname;
        changed = true;
      }
    }
    if (avatar != _noChange) {
      final nextAvatar = _stringValue(avatar);
      if (_avatar != nextAvatar) {
        _avatar = nextAvatar;
        changed = true;
      }
    }
    if (createdAtRaw != _noChange) {
      final nextCreatedAt = _stringValue(createdAtRaw);
      if (_createdAtRaw != nextCreatedAt) {
        _createdAtRaw = nextCreatedAt;
        changed = true;
      }
    }
    if (authErrorMessage != _noChange) {
      final nextAuthErrorMessage = _stringValue(authErrorMessage);
      if (_authErrorMessage != nextAuthErrorMessage) {
        _authErrorMessage = nextAuthErrorMessage;
        changed = true;
      }
    }

    if (changed && notify) {
      notifyListeners();
    }
  }

  void applyAuthResult(Map<String, dynamic> result, {bool notify = true}) {
    final accessToken = result['access_token']?.toString();
    final refreshToken = result['refresh_token']?.toString();
    final user = result['user'] is Map<String, dynamic>
        ? result['user'] as Map<String, dynamic>
        : <String, dynamic>{};
    if (accessToken == null || accessToken.isEmpty) {
      throw Exception('缺少 access_token');
    }
    if (refreshToken == null || refreshToken.isEmpty) {
      throw Exception('缺少 refresh_token');
    }

    syncLocalState(
      isLoggedIn: true,
      sessionBootState: SessionBootState.authenticated,
      token: accessToken,
      refreshToken: refreshToken,
      username: user['username']?.toString() ?? _username,
      userId: user['id']?.toString() ?? user['user_id']?.toString(),
      userNumber: _parseOptionalInt(user['user_number']),
      nickname: user.containsKey('nickname')
          ? user['nickname']?.toString()
          : _nickname,
      avatar: user.containsKey('avatar') ? user['avatar']?.toString() : _avatar,
      createdAtRaw: user.containsKey('created_at')
          ? user['created_at']?.toString()
          : _createdAtRaw,
      authErrorMessage: null,
      notify: notify,
    );
  }

  void applyProfile(
    Map<String, dynamic> profile, {
    bool includeIdentity = true,
    bool notify = true,
  }) {
    syncLocalState(
      isLoggedIn: true,
      sessionBootState: SessionBootState.authenticated,
      username: profile['username']?.toString() ?? _username,
      userId: includeIdentity
          ? profile['id']?.toString() ?? profile['user_id']?.toString()
          : _noChange,
      userNumber: includeIdentity
          ? _parseOptionalInt(profile['user_number'])
          : _noChange,
      nickname: profile.containsKey('nickname')
          ? profile['nickname']?.toString()
          : _noChange,
      avatar: profile.containsKey('avatar')
          ? profile['avatar']?.toString()
          : _noChange,
      createdAtRaw: profile.containsKey('created_at')
          ? profile['created_at']?.toString()
          : _noChange,
      authErrorMessage: null,
      notify: notify,
    );
  }

  void restoreCachedProfile({
    String? username,
    String? userId,
    int? userNumber,
    String? nickname,
    String? avatar,
    String? createdAtRaw,
    bool notify = true,
  }) {
    syncLocalState(
      username: (_username ?? '').trim().isEmpty ? username : _noChange,
      userId: (_userId ?? '').trim().isEmpty ? userId : _noChange,
      userNumber: userNumber,
      nickname: nickname,
      avatar: avatar,
      createdAtRaw: createdAtRaw,
      notify: notify,
    );
  }

  void setAuthError(String? message, {bool notify = true}) {
    syncLocalState(authErrorMessage: message, notify: notify);
  }

  void clearAuthError({bool notify = true}) {
    syncLocalState(authErrorMessage: null, notify: notify);
  }

  int? _parseOptionalInt(dynamic value) {
    if (value is num) return value.toInt();
    if (value is String) return int.tryParse(value.trim());
    return null;
  }

  String? _stringValue(Object? value) {
    if (value is String) return value;
    return null;
  }

  int? _intValue(Object? value) {
    if (value is int) return value;
    return null;
  }
}
