import 'package:flutter/foundation.dart';

import '../services/cache_service.dart';
import 'app_auth_state.dart';

class AppSyncState extends ChangeNotifier {
  final CacheService _cache;

  final Map<String, String> _syncVersions = <String, String>{};
  DateTime? _lastAssetDataUpdatedAt;
  DateTime? _lastQuoteDataUpdatedAt;
  bool _assetDataFromCache = false;
  bool _quoteDataFromCache = false;
  int _quoteIntervalOpenSec = 5;
  int _quoteIntervalClosedSec = 120;
  int _quoteIntervalUsExtendedSec = 10;

  AppSyncState({required CacheService cache}) : _cache = cache;

  Map<String, String> get syncVersions => _syncVersions;
  DateTime? get assetDataUpdatedAt => _lastAssetDataUpdatedAt;
  DateTime? get quoteDataUpdatedAt => _lastQuoteDataUpdatedAt;
  bool get assetDataFromCache => _assetDataFromCache;
  bool get quoteDataFromCache => _quoteDataFromCache;
  int get quoteIntervalOpenSec => _quoteIntervalOpenSec;
  int get quoteIntervalClosedSec => _quoteIntervalClosedSec;
  int get quoteIntervalUsExtendedSec => _quoteIntervalUsExtendedSec;

  List<String> cacheScopes({
    required String? username,
    required String? userId,
    bool includeGuestForAnonymous = true,
  }) {
    final scopes = <String>[];
    final uname = (username ?? '').trim().toLowerCase();
    final uid = (userId ?? '').trim();
    if (uname.isNotEmpty) scopes.add('name:$uname');
    if (uid.isNotEmpty && !scopes.contains(uid)) scopes.add(uid);
    if (scopes.isEmpty && includeGuestForAnonymous) scopes.add('guest');
    return scopes;
  }

  String cachePrimaryScope({
    required String? username,
    required String? userId,
  }) {
    final scopes = cacheScopes(username: username, userId: userId);
    return scopes.isEmpty ? 'guest' : scopes.first;
  }

  String cacheKeyForScope(String scope, String domain) => 'u:$scope:$domain';

  List<String> profileScopes({
    required String? currentUsername,
    required String? currentUserId,
    String? usernameHint,
    String? userIdHint,
    bool includeCurrent = true,
  }) {
    final scopes = <String>[];

    void addScope(String value) {
      final trimmed = value.trim();
      if (trimmed.isEmpty || scopes.contains(trimmed)) return;
      scopes.add(trimmed);
    }

    final hintUsername = (usernameHint ?? '').trim().toLowerCase();
    if (hintUsername.isNotEmpty) addScope('name:$hintUsername');
    final hintUserId = (userIdHint ?? '').trim();
    if (hintUserId.isNotEmpty) addScope(hintUserId);

    if (includeCurrent) {
      for (final scope in cacheScopes(
        username: currentUsername,
        userId: currentUserId,
        includeGuestForAnonymous: false,
      )) {
        addScope(scope);
      }
    }

    return scopes;
  }

  String? nullableTrimmedString(dynamic value) {
    if (value == null) return null;
    final raw = value.toString().trim();
    if (raw.isEmpty) return null;
    return raw;
  }

  Future<void> persistUserProfileCache({
    required AppAuthState authState,
    required Duration staleAfter,
    required String userProfileDomain,
  }) async {
    final cachedUsername = nullableTrimmedString(
      authState.username,
    )?.toLowerCase();
    final cachedUserId = nullableTrimmedString(authState.userId);
    final scopes = profileScopes(
      currentUsername: authState.username,
      currentUserId: authState.userId,
      usernameHint: cachedUsername,
      userIdHint: cachedUserId,
      includeCurrent: true,
    );
    if (scopes.isEmpty) return;

    final data = <String, dynamic>{
      'username': cachedUsername ?? '',
      'user_id': cachedUserId ?? '',
      'user_number': authState.userNumber,
      'ai_credits_balance': authState.aiCreditsBalance,
      'nickname': authState.nickname ?? '',
      'avatar': authState.avatar ?? '',
      'created_at': authState.createdAtRaw ?? '',
      'saved_at_ms': DateTime.now().millisecondsSinceEpoch,
    };
    final envelope = buildEnvelope(
      data: data,
      version: null,
      staleAfter: staleAfter,
      username: authState.username,
      userId: authState.userId,
    );

    for (final scope in scopes) {
      await _cache.setJson(
        cacheKeyForScope(scope, userProfileDomain),
        envelope,
      );
    }
  }

  Future<void> restoreUserProfileCache({
    required AppAuthState authState,
    required String userProfileDomain,
    String? usernameHint,
    String? userIdHint,
  }) async {
    final scopes = profileScopes(
      currentUsername: authState.username,
      currentUserId: authState.userId,
      usernameHint: usernameHint,
      userIdHint: userIdHint,
      includeCurrent: true,
    );
    for (final scope in scopes) {
      final envelope = normalizeEnvelope(
        await _cache.getJson(cacheKeyForScope(scope, userProfileDomain)),
        username: authState.username,
        userId: authState.userId,
      );
      final data = asMap(envelope?['data']);
      if (data.isEmpty) continue;

      final cachedUsername = nullableTrimmedString(data['username']);
      final cachedUserId = nullableTrimmedString(data['user_id']);
      final cachedNickname = nullableTrimmedString(data['nickname']);
      final cachedAvatar = nullableTrimmedString(data['avatar']);
      final cachedCreatedAt = nullableTrimmedString(data['created_at']);
      final userNumberRaw = data['user_number'];
      final cachedUserNumber = userNumberRaw is num
          ? userNumberRaw.toInt()
          : int.tryParse('${userNumberRaw ?? ''}');
      final aiCreditsRaw = data['ai_credits_balance'];
      final cachedAiCreditsBalance = aiCreditsRaw is num
          ? aiCreditsRaw.toInt()
          : int.tryParse('${aiCreditsRaw ?? ''}');

      authState.restoreCachedProfile(
        username: cachedUsername,
        userId: cachedUserId,
        userNumber: cachedUserNumber,
        aiCreditsBalance: cachedAiCreditsBalance,
        nickname: cachedNickname,
        avatar: cachedAvatar,
        createdAtRaw: cachedCreatedAt,
        notify: false,
      );
      return;
    }
  }

  Future<void> clearUserProfileCache({
    required AppAuthState authState,
    required String userProfileDomain,
    String? usernameHint,
    String? userIdHint,
  }) async {
    final scopes = profileScopes(
      currentUsername: authState.username,
      currentUserId: authState.userId,
      usernameHint: usernameHint,
      userIdHint: userIdHint,
      includeCurrent: true,
    );
    for (final scope in scopes) {
      await _cache.remove(cacheKeyForScope(scope, userProfileDomain));
    }
  }

  Map<String, dynamic> asMap(dynamic value) {
    if (value is Map<String, dynamic>) return value;
    if (value is Map) return Map<String, dynamic>.from(value);
    return <String, dynamic>{};
  }

  int asInt(dynamic value) {
    if (value is int) return value;
    if (value is num) return value.toInt();
    if (value is String) return int.tryParse(value.trim()) ?? 0;
    return 0;
  }

  int positiveInt(dynamic value, {required int fallback}) {
    final parsed = asInt(value);
    return parsed > 0 ? parsed : fallback;
  }

  DateTime? envelopeSavedAt(Map<String, dynamic>? envelope) {
    if (envelope == null) return null;
    final savedAtMs = asInt(envelope['saved_at_ms']);
    if (savedAtMs <= 0) return null;
    return DateTime.fromMillisecondsSinceEpoch(savedAtMs);
  }

  Map<String, dynamic>? normalizeEnvelope(
    Map<String, dynamic>? raw, {
    required String? username,
    required String? userId,
  }) {
    if (raw == null) return null;
    final hasEnvelopeFields =
        raw.containsKey('data') && raw.containsKey('saved_at_ms');
    if (hasEnvelopeFields) return raw;
    return <String, dynamic>{
      'user_id': cachePrimaryScope(username: username, userId: userId),
      'version': '',
      'saved_at_ms': 0,
      'stale_after_ms': 0,
      'data': raw,
    };
  }

  Map<String, dynamic> buildEnvelope({
    required dynamic data,
    String? version,
    required Duration staleAfter,
    required String? username,
    required String? userId,
  }) {
    return <String, dynamic>{
      'user_id': cachePrimaryScope(username: username, userId: userId),
      'version': (version ?? '').trim(),
      'saved_at_ms': DateTime.now().millisecondsSinceEpoch,
      'stale_after_ms': staleAfter.inMilliseconds,
      'data': data,
    };
  }

  Future<Map<String, dynamic>?> loadDomainEnvelope({
    required String domain,
    required String? username,
    required String? userId,
    required Map<String, String> legacyCacheKeys,
  }) async {
    final scopes = cacheScopes(username: username, userId: userId);
    for (final scope in scopes) {
      final scoped = normalizeEnvelope(
        await _cache.getJson(cacheKeyForScope(scope, domain)),
        username: username,
        userId: userId,
      );
      if (scoped != null) return scoped;
    }
    final legacyKey = legacyCacheKeys[domain];
    if (legacyKey == null) return null;
    return normalizeEnvelope(
      await _cache.getJson(legacyKey),
      username: username,
      userId: userId,
    );
  }

  Future<void> saveDomainEnvelope({
    required String domain,
    required dynamic data,
    String? version,
    required Duration staleAfter,
    required String? username,
    required String? userId,
  }) async {
    final envelope = buildEnvelope(
      data: data,
      version: version,
      staleAfter: staleAfter,
      username: username,
      userId: userId,
    );
    for (final scope in cacheScopes(username: username, userId: userId)) {
      await _cache.setJson(cacheKeyForScope(scope, domain), envelope);
    }
  }

  Future<void> loadSyncVersionsFromCache({
    required String? username,
    required String? userId,
    required Map<String, String> legacyCacheKeys,
  }) async {
    final envelope = await loadDomainEnvelope(
      domain: 'sync_versions',
      username: username,
      userId: userId,
      legacyCacheKeys: legacyCacheKeys,
    );
    final payload = asMap(envelope?['data']);
    final versions = asMap(payload['versions']);
    if (versions.isEmpty) return;
    _syncVersions
      ..clear()
      ..addAll(
        versions.map((k, v) => MapEntry(k.toString(), (v ?? '').toString())),
      );
  }

  Future<void> saveSyncVersionsToCache({
    required String? username,
    required String? userId,
    required Duration staleAfter,
  }) async {
    if (_syncVersions.isEmpty) return;
    await saveDomainEnvelope(
      domain: 'sync_versions',
      data: <String, dynamic>{
        'versions': Map<String, String>.from(_syncVersions),
      },
      staleAfter: staleAfter,
      username: username,
      userId: userId,
    );
  }

  void setQuotePolicy({
    required int openSec,
    required int closedSec,
    required int usExtendedSec,
    bool notify = true,
  }) {
    var changed = false;
    if (_quoteIntervalOpenSec != openSec) {
      _quoteIntervalOpenSec = openSec;
      changed = true;
    }
    if (_quoteIntervalClosedSec != closedSec) {
      _quoteIntervalClosedSec = closedSec;
      changed = true;
    }
    if (_quoteIntervalUsExtendedSec != usExtendedSec) {
      _quoteIntervalUsExtendedSec = usExtendedSec;
      changed = true;
    }
    if (changed && notify) {
      notifyListeners();
    }
  }

  void applyQuotePolicy(dynamic rawPolicy, {bool notify = true}) {
    final policy = asMap(rawPolicy);
    if (policy.isEmpty) return;
    setQuotePolicy(
      openSec: positiveInt(
        policy['interval_open_sec'],
        fallback: _quoteIntervalOpenSec,
      ),
      closedSec: positiveInt(
        policy['interval_closed_sec'],
        fallback: _quoteIntervalClosedSec,
      ),
      usExtendedSec: positiveInt(
        policy['interval_us_extended_sec'],
        fallback: _quoteIntervalUsExtendedSec,
      ),
      notify: notify,
    );
  }

  bool canSkipStaticSyncCheck({
    required bool force,
    required Duration staticDataTtl,
  }) {
    if (force) return false;
    if (_syncVersions.isEmpty) return false;
    final lastAt = _lastAssetDataUpdatedAt;
    if (lastAt == null) return false;
    return DateTime.now().difference(lastAt) < staticDataTtl;
  }

  void markAssetCacheHydrated(DateTime? savedAt, {bool notify = true}) {
    _assetDataFromCache = true;
    if (savedAt != null) {
      _lastAssetDataUpdatedAt = savedAt;
    }
    if (notify) {
      notifyListeners();
    }
  }

  void markQuoteCacheHydrated(DateTime? savedAt, {bool notify = true}) {
    _quoteDataFromCache = true;
    if (savedAt != null) {
      _lastQuoteDataUpdatedAt = savedAt;
    }
    if (notify) {
      notifyListeners();
    }
  }

  void markAssetFresh({DateTime? updatedAt, bool notify = true}) {
    _assetDataFromCache = false;
    _lastAssetDataUpdatedAt = updatedAt ?? DateTime.now();
    if (notify) {
      notifyListeners();
    }
  }

  void markQuoteFresh({DateTime? updatedAt, bool notify = true}) {
    _quoteDataFromCache = false;
    _lastQuoteDataUpdatedAt = updatedAt ?? DateTime.now();
    if (notify) {
      notifyListeners();
    }
  }

  void clearSyncRuntime({bool notify = true}) {
    _syncVersions.clear();
    _lastAssetDataUpdatedAt = null;
    _lastQuoteDataUpdatedAt = null;
    _assetDataFromCache = false;
    _quoteDataFromCache = false;
    if (notify) {
      notifyListeners();
    }
  }
}
