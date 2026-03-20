import 'dart:async';

import 'package:flutter/foundation.dart';

import '../services/api_service.dart';
import '../services/async_flow_logger.dart';
import '../services/secure_storage_service.dart';
import '../utils/error_text.dart';
import 'app_assets_state.dart';
import 'app_auth_state.dart';
import 'app_market_state.dart';
import 'app_security_state.dart';
import 'app_sync_state.dart';

typedef LoginHandler =
    Future<Map<String, dynamic>?> Function({
      required String username,
      required String password,
    });

class AppSessionBindings {
  final void Function() notifyListeners;
  final void Function() clearPrices;
  final void Function() clearPriceSnapshots;
  final void Function(bool value) setPortfolioLoaded;
  final Future<void> Function() hydrateFromCache;
  final Future<void> Function() refreshAll;

  const AppSessionBindings({
    required this.notifyListeners,
    required this.clearPrices,
    required this.clearPriceSnapshots,
    required this.setPortfolioLoaded,
    required this.hydrateFromCache,
    required this.refreshAll,
  });
}

class AppSessionState {
  final ApiService _api;
  final SecureStorageService _secureStorage;
  final AppAssetsState _assetsState;
  final AppAuthState _authState;
  final AppMarketState _marketState;
  final AppSecurityState _securityState;
  final AppSyncState _syncState;
  final Duration _userProfileTtl;
  final String _userProfileDomain;
  final LoginHandler? _loginHandlerOverride;
  final Future<String?> Function()? _tokenLoaderOverride;
  final Future<Map<String, dynamic>?> Function()? _profileLoaderOverride;
  final Future<Map<String, dynamic>?> Function(String refreshToken)?
  _refreshSessionOverride;

  AppSessionState({
    required ApiService api,
    required SecureStorageService secureStorage,
    required AppAssetsState assetsState,
    required AppAuthState authState,
    required AppMarketState marketState,
    required AppSecurityState securityState,
    required AppSyncState syncState,
    required Duration userProfileTtl,
    required String userProfileDomain,
    LoginHandler? loginHandler,
    Future<String?> Function()? tokenLoader,
    Future<Map<String, dynamic>?> Function()? profileLoader,
    Future<Map<String, dynamic>?> Function(String refreshToken)? refreshLoader,
  }) : _api = api,
       _secureStorage = secureStorage,
       _assetsState = assetsState,
       _authState = authState,
       _marketState = marketState,
       _securityState = securityState,
       _syncState = syncState,
       _userProfileTtl = userProfileTtl,
       _userProfileDomain = userProfileDomain,
       _loginHandlerOverride = loginHandler,
       _tokenLoaderOverride = tokenLoader,
       _profileLoaderOverride = profileLoader,
       _refreshSessionOverride = refreshLoader;

  bool get biometricEnabled => _securityState.biometricEnabled;
  AuthLogoutMode get logoutMode => _securityState.logoutMode;
  String? get refreshToken => _authState.refreshToken;
  String? get token => _authState.token;
  String? get username => _authState.username;
  String? get userId => _authState.userId;

  Future<void> applyAuthResult(
    Map<String, dynamic> result, {
    required AppSessionBindings bindings,
  }) async {
    _authState.applyAuthResult(result, notify: false);
    _api.setAuthTokens(accessToken: token, refreshToken: refreshToken);
    _securityState.syncLocalState(
      logoutMode: AuthLogoutMode.normal,
      isAppLocked: false,
      notify: false,
    );
    bindings.notifyListeners();

    try {
      await _secureStorage.setToken(token!);
      await _secureStorage.setRefreshToken(refreshToken!);
      if (username != null && username!.isNotEmpty) {
        await _secureStorage.setUsername(username!);
      }
      await _secureStorage.clearLogoutMode();
      await _syncState.persistUserProfileCache(
        authState: _authState,
        staleAfter: _userProfileTtl,
        userProfileDomain: _userProfileDomain,
      );
    } catch (e) {
      debugPrint('登录态写入本地存储失败，已保留内存登录态: $e');
    }
  }

  Future<String?> _safeReadStorageString(
    Future<String?> Function() reader,
    String label,
  ) async {
    try {
      return await reader();
    } catch (e) {
      debugPrint('读取$label失败: $e');
      return null;
    }
  }

  Future<bool> _safeReadStorageBool(
    Future<bool> Function() reader,
    String label,
  ) async {
    try {
      return await reader();
    } catch (e) {
      debugPrint('读取$label失败: $e');
      return false;
    }
  }

  bool _isWebStorageRuntimeError(String lower) {
    return lower.contains('null check operator used on a null value') ||
        lower.contains('window.crypto') ||
        lower.contains('secure storage') ||
        lower.contains('fluttersecurestorage') ||
        lower.contains('localstorage');
  }

  String mapAuthErrorMessage(Object error, {required bool isRegister}) {
    if (error is ApiException) {
      final raw = error.message.trim();
      final lower = raw.toLowerCase();
      if (isRegister) {
        if (error.statusCode == 409 ||
            lower.contains('username already exists')) {
          return '注册失败，用户名重复';
        }
        if (lower.contains('invite code')) {
          return '邀请码不正确或已被使用';
        }
      } else if (error.statusCode == 401) {
        return '用户名/密码错误，请重试';
      }
      return resolveApiErrorText(
        message: raw,
        statusCode: error.statusCode,
        fallback: isRegister ? '注册失败，请稍后重试' : '登录失败，请稍后重试',
      );
    }
    final raw = error.toString().trim();
    if (raw.isNotEmpty) {
      final normalized = raw.startsWith('Exception:')
          ? raw.replaceFirst('Exception:', '').trim()
          : raw;
      final lower = normalized.toLowerCase();
      if (_isWebStorageRuntimeError(lower)) {
        return '浏览器存储环境异常，请刷新页面或切换 HTTPS 后重试';
      }
      return translateErrorText(
        normalized,
        fallback: isRegister ? '注册失败，请稍后重试' : '登录失败，请稍后重试',
      );
    }
    return isRegister ? '注册失败，请稍后重试' : '登录失败，请稍后重试';
  }

  Future<bool> login({
    required String username,
    required String password,
    required AppSessionBindings bindings,
  }) async {
    _authState.clearAuthError(notify: false);
    try {
      final result = _loginHandlerOverride != null
          ? await _loginHandlerOverride(username: username, password: password)
          : await _api.login(username: username, password: password);
      if (result == null) {
        _authState.setAuthError('登录响应为空，请稍后重试');
        return false;
      }
      await applyAuthResult(result, bindings: bindings);
      _authState.clearAuthError(notify: false);
      return true;
    } catch (e) {
      _authState.setAuthError(mapAuthErrorMessage(e, isRegister: false));
      debugPrint('登录异常(${e.runtimeType}): $e');
      return false;
    }
  }

  Future<bool> register({
    required String username,
    required String password,
    required String inviteCode,
    required AppSessionBindings bindings,
  }) async {
    _authState.clearAuthError(notify: false);
    try {
      final result = await _api.register(
        username: username,
        password: password,
        inviteCode: inviteCode,
      );
      if (result == null) {
        _authState.setAuthError('注册失败，请稍后重试');
        return false;
      }
      await applyAuthResult(result, bindings: bindings);
      _authState.clearAuthError(notify: false);
      return true;
    } catch (e) {
      _authState.setAuthError(mapAuthErrorMessage(e, isRegister: true));
      debugPrint('注册异常: $e');
      return false;
    }
  }

  Future<bool> validateInviteCode(String inviteCode) async {
    try {
      return await _api.validateInviteCode(inviteCode);
    } catch (e) {
      return false;
    }
  }

  Future<bool> changePassword({
    required String oldPassword,
    required String newPassword,
  }) async {
    try {
      await _api.changePassword(
        oldPassword: oldPassword,
        newPassword: newPassword,
      );
      await _securityState.disableBiometric();
      return true;
    } catch (e) {
      debugPrint('修改密码失败: $e');
      return false;
    }
  }

  Future<bool> setBiometricEnabled(bool enabled) async {
    return _securityState.setBiometricEnabled(enabled);
  }

  Future<bool> tryBiometricLogin({required AppSessionBindings bindings}) async {
    return _securityState.tryBiometricLogin(
      refreshToken: refreshToken,
      refreshSession: (refreshToken) async {
        return _refreshSessionOverride != null
            ? _refreshSessionOverride(refreshToken)
            : _api.refreshSession(refreshToken: refreshToken);
      },
      applyAuthResult: (result) => applyAuthResult(result, bindings: bindings),
    );
  }

  Future<bool> fetchProfile({required AppSessionBindings bindings}) async {
    final profile = await _api.getProfile();
    if (profile != null) {
      _authState.applyProfile(profile, includeIdentity: false, notify: false);
      await _syncState.persistUserProfileCache(
        authState: _authState,
        staleAfter: _userProfileTtl,
        userProfileDomain: _userProfileDomain,
      );
      bindings.notifyListeners();
      return true;
    }
    return false;
  }

  Future<bool> updateProfile({
    String? nickname,
    String? avatar,
    required AppSessionBindings bindings,
  }) async {
    final result = await _api.updateProfile(nickname: nickname, avatar: avatar);
    if (result != null) {
      _authState.applyProfile(result, includeIdentity: false, notify: false);
      await _syncState.persistUserProfileCache(
        authState: _authState,
        staleAfter: _userProfileTtl,
        userProfileDomain: _userProfileDomain,
      );
      bindings.notifyListeners();
      return true;
    }
    return false;
  }

  Future<void> setLoggedIn({
    required String token,
    required String refreshToken,
    required String username,
    required String userId,
    int? userNumber,
    int? aiCreditsBalance,
    String? nickname,
    String? avatar,
    String? createdAtRaw,
    required AppSessionBindings bindings,
  }) async {
    _authState.syncLocalState(
      isLoggedIn: true,
      sessionBootState: SessionBootState.authenticated,
      token: token,
      refreshToken: refreshToken,
      username: username,
      userId: userId,
      userNumber: userNumber,
      aiCreditsBalance: aiCreditsBalance,
      nickname: nickname,
      avatar: avatar,
      createdAtRaw: createdAtRaw,
      authErrorMessage: null,
      notify: false,
    );
    _api.setAuthTokens(accessToken: token, refreshToken: refreshToken);
    _securityState.syncLocalState(
      logoutMode: AuthLogoutMode.normal,
      isAppLocked: false,
      notify: false,
    );
    await _secureStorage.setToken(token);
    await _secureStorage.setRefreshToken(refreshToken);
    await _secureStorage.setUsername(username);
    await _secureStorage.clearLogoutMode();
    await _syncState.persistUserProfileCache(
      authState: _authState,
      staleAfter: _userProfileTtl,
      userProfileDomain: _userProfileDomain,
    );
    bindings.notifyListeners();
  }

  void logout({required AppSessionBindings bindings}) {
    final currentRefreshToken = refreshToken;
    final currentUsername = username;
    final currentUserId = userId;
    final preserveBiometricSession =
        biometricEnabled &&
        currentRefreshToken != null &&
        currentRefreshToken.isNotEmpty;
    if (!preserveBiometricSession) {
      unawaited(() async {
        try {
          await _api.logout(refreshToken: currentRefreshToken);
        } catch (_) {
          // 本地会话已清理，后端登出失败不阻断前端退出流程。
        }
      }());
    }
    debugPrint(
      'Logout called. preserveBiometricSession=$preserveBiometricSession',
    );
    _securityState.syncLocalState(
      logoutMode: preserveBiometricSession
          ? AuthLogoutMode.biometricReady
          : AuthLogoutMode.normal,
      isAppLocked: false,
      notify: false,
    );
    _authState.syncLocalState(
      isLoggedIn: false,
      sessionBootState: SessionBootState.unauthenticated,
      isSessionChecking: false,
      token: null,
      refreshToken: preserveBiometricSession ? currentRefreshToken : null,
      username: preserveBiometricSession ? currentUsername : null,
      userId: null,
      userNumber: null,
      nickname: null,
      avatar: null,
      createdAtRaw: null,
      authErrorMessage: null,
      notify: false,
    );
    _api.clearAuthTokens();
    _assetsState.clearAll(notify: false);
    bindings.clearPrices();
    bindings.clearPriceSnapshots();
    _syncState.clearSyncRuntime(notify: false);
    bindings.setPortfolioLoaded(false);
    if (preserveBiometricSession) {
      unawaited(() async {
        await _secureStorage.clearToken();
        await _secureStorage.setLogoutMode('biometric_ready');
      }());
    } else {
      unawaited(() async {
        await _secureStorage.clearAllAuth();
        await _secureStorage.setLogoutMode('normal');
        await _syncState.clearUserProfileCache(
          authState: _authState,
          userProfileDomain: _userProfileDomain,
          usernameHint: currentUsername,
          userIdHint: currentUserId,
        );
      }());
    }
    bindings.notifyListeners();
  }

  Future<AppAsyncFlowResult> restoreSession({
    required AppSessionBindings bindings,
  }) async {
    final flow = startAppAsyncFlow('flutter.restoreSession');
    if (_authState.isSessionChecking) {
      return finishAppAsyncFlow(flow, stage: 'skip:checking');
    }
    _authState.syncLocalState(isSessionChecking: true, notify: false);

    String? resolvedToken;
    String? resolvedRefreshToken;
    String? resolvedUsername;
    String? logoutModeRaw;
    if (_tokenLoaderOverride != null) {
      try {
        resolvedToken = await _tokenLoaderOverride();
      } catch (e) {
        debugPrint('读取 access token 失败: $e');
      }
    } else {
      resolvedToken = await _safeReadStorageString(
        _secureStorage.getToken,
        'access token',
      );
    }
    resolvedRefreshToken = await _safeReadStorageString(
      _secureStorage.getRefreshToken,
      'refresh token',
    );
    resolvedUsername = await _safeReadStorageString(
      _secureStorage.getUsername,
      'username',
    );
    final storedBiometricEnabled = await _safeReadStorageBool(
      _secureStorage.isBiometricEnabled,
      'biometric enabled',
    );
    logoutModeRaw = await _safeReadStorageString(
      _secureStorage.getLogoutMode,
      'logout mode',
    );

    final parsedLogoutMode = _securityState.parseLogoutMode(logoutModeRaw);
    _securityState.syncLocalState(
      biometricEnabled: storedBiometricEnabled,
      logoutMode: parsedLogoutMode,
      notify: false,
    );

    if (resolvedRefreshToken != null && resolvedRefreshToken.isNotEmpty) {
      _authState.syncLocalState(
        refreshToken: resolvedRefreshToken,
        username: resolvedUsername,
        notify: false,
      );
      await _syncState.restoreUserProfileCache(
        authState: _authState,
        userProfileDomain: _userProfileDomain,
        usernameHint: resolvedUsername,
      );
    }
    if (_securityState.logoutMode == AuthLogoutMode.biometricReady) {
      _authState.syncLocalState(
        isLoggedIn: false,
        token: null,
        sessionBootState: SessionBootState.unauthenticated,
        isSessionChecking: false,
        notify: false,
      );
      _api.clearAuthTokens();
      _securityState.lockApp(notify: false);
      bindings.notifyListeners();
      return finishAppAsyncFlow(flow, stage: 'biometric-locked');
    }

    if (resolvedRefreshToken == null || resolvedRefreshToken.isEmpty) {
      _authState.syncLocalState(
        sessionBootState: SessionBootState.unauthenticated,
        isSessionChecking: false,
        notify: false,
      );
      bindings.notifyListeners();
      return finishAppAsyncFlow(flow, stage: 'skip:no-refresh-token');
    }

    if (resolvedToken == null || resolvedToken.isEmpty) {
      try {
        final refreshed = _refreshSessionOverride != null
            ? await _refreshSessionOverride(resolvedRefreshToken)
            : await _api.refreshSession(refreshToken: resolvedRefreshToken);
        if (refreshed != null) {
          await applyAuthResult(refreshed, bindings: bindings);
          _authState.syncLocalState(isSessionChecking: false, notify: false);
          unawaited(bindings.hydrateFromCache());
          unawaited(bindings.refreshAll());
          return finishAppAsyncFlow(flow, stage: 'refresh-restored');
        }
      } catch (e) {
        debugPrint('启动静默 refresh 失败: $e');
      }
      await clearSessionAndUnauthenticated(bindings: bindings);
      _authState.syncLocalState(isSessionChecking: false, notify: false);
      return finishAppAsyncFlow(flow, stage: 'refresh-failed');
    }

    _authState.syncLocalState(
      token: resolvedToken,
      refreshToken: resolvedRefreshToken,
      username: resolvedUsername,
      isLoggedIn: true,
      sessionBootState: SessionBootState.authenticated,
      isSessionChecking: false,
      authErrorMessage: null,
      notify: false,
    );
    _api.setAuthTokens(
      accessToken: resolvedToken,
      refreshToken: resolvedRefreshToken,
    );
    _securityState.syncLocalState(
      logoutMode: AuthLogoutMode.normal,
      isAppLocked: false,
      notify: false,
    );
    bindings.notifyListeners();
    unawaited(bindings.hydrateFromCache());
    unawaited(bindings.refreshAll());
    return finishAppAsyncFlow(flow, stage: 'token-restored');
  }

  Future<AppAsyncFlowResult> validateSessionInBackground({
    required AppSessionBindings bindings,
  }) async {
    final flow = startAppAsyncFlow('flutter.validateSessionInBackground');
    Map<String, dynamic>? profile = _profileLoaderOverride != null
        ? await _profileLoaderOverride()
        : await _api.getProfile();
    if (profile == null && refreshToken != null && refreshToken!.isNotEmpty) {
      try {
        final refreshed = _refreshSessionOverride != null
            ? await _refreshSessionOverride(refreshToken!)
            : await _api.refreshSession(refreshToken: refreshToken!);
        if (refreshed != null) {
          await applyAuthResult(refreshed, bindings: bindings);
          profile = refreshed['user'] is Map<String, dynamic>
              ? refreshed['user'] as Map<String, dynamic>
              : await _api.getProfile();
        }
      } catch (error) {
        return finishAppAsyncFlow(flow, stage: 'refresh-failed', error: error);
      }
    }
    if (profile == null) {
      await clearSessionAndUnauthenticated(bindings: bindings);
      return finishAppAsyncFlow(flow, stage: 'profile-missing');
    }

    _authState.applyProfile(profile, notify: false);
    await _syncState.persistUserProfileCache(
      authState: _authState,
      staleAfter: _userProfileTtl,
      userProfileDomain: _userProfileDomain,
    );
    _securityState.syncLocalState(
      logoutMode: AuthLogoutMode.normal,
      isAppLocked: false,
      notify: false,
    );
    bindings.notifyListeners();
    return finishAppAsyncFlow(flow, stage: 'profile-restored');
  }

  Future<void> clearSessionAndUnauthenticated({
    required AppSessionBindings bindings,
  }) async {
    final previousUsername = username;
    final previousUserId = userId;
    _authState.syncLocalState(
      isLoggedIn: false,
      isSessionChecking: false,
      token: null,
      refreshToken: null,
      username: null,
      userId: null,
      userNumber: null,
      nickname: null,
      avatar: null,
      createdAtRaw: null,
      sessionBootState: SessionBootState.unauthenticated,
      authErrorMessage: null,
      notify: false,
    );
    _api.clearAuthTokens();
    _syncState.clearSyncRuntime(notify: false);
    bindings.clearPriceSnapshots();
    _marketState.resetMarketStatus(notify: false);
    _securityState.syncLocalState(
      logoutMode: AuthLogoutMode.normal,
      isAppLocked: false,
      notify: false,
    );
    bindings.notifyListeners();
    try {
      await _secureStorage.clearAllAuth();
      await _secureStorage.clearLogoutMode();
      await _syncState.clearUserProfileCache(
        authState: _authState,
        userProfileDomain: _userProfileDomain,
        usernameHint: previousUsername,
        userIdHint: previousUserId,
      );
    } catch (e) {
      debugPrint('清理失效 token 失败: $e');
    }
  }
}
