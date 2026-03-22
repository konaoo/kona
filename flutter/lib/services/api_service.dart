import 'dart:async';
import 'dart:convert';
import 'dart:math';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../config/api_config.dart';
import '../models/app_version.dart';
import '../models/asset_action_result.dart';
import 'secure_storage_service.dart';
import '../utils/error_text.dart';
import '../utils/network_error_stub.dart'
    if (dart.library.io) '../utils/network_error_io.dart';

typedef PostTransport =
    Future<dynamic> Function(
      String endpoint,
      Map<String, dynamic> data, {
      bool retryOnTransient,
      int transientMaxAttempts,
    });

/// API 服务 - 封装所有后端 API 调用
class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  String? _token;
  String? _refreshToken;
  final http.Client _client = http.Client();
  final SecureStorageService _secureStorage = SecureStorageService();
  Future<bool>? _refreshInFlight;
  bool _lastRefreshHardFailure = false;
  void Function()? onAuthExpired;
  PostTransport? _postOverrideForTesting;

  /// 设置认证 token
  void setToken(String token) {
    _token = token;
  }

  /// 清除认证 token
  void clearToken() {
    _token = null;
  }

  /// 同步整组认证 token，避免续签时反复读取安全存储。
  void setAuthTokens({
    String? accessToken,
    String? refreshToken,
  }) {
    _token = accessToken;
    _refreshToken = refreshToken;
  }

  /// 清除整组认证 token
  void clearAuthTokens() {
    _token = null;
    _refreshToken = null;
  }

  /// 获取请求头
  Map<String, String> _buildHeaders({
    String? requestId,
    bool includeAuth = true,
  }) {
    final headers = <String, String>{'Content-Type': 'application/json'};
    final traceId = (requestId ?? '').trim();
    if (traceId.isNotEmpty) {
      headers['X-Request-Id'] = traceId;
    }
    if (includeAuth && _token != null) {
      headers['Authorization'] = 'Bearer $_token';
    }
    return headers;
  }

  /// 构建包含认证信息的请求头（供需要自定义请求的服务使用）
  Map<String, String> buildHeaders({
    String? requestId,
    bool includeAuth = true,
  }) {
    return _buildHeaders(requestId: requestId, includeAuth: includeAuth);
  }

  @visibleForTesting
  Map<String, String> debugBuildHeaders({
    String? requestId,
    bool includeAuth = true,
  }) {
    return _buildHeaders(requestId: requestId, includeAuth: includeAuth);
  }

  @visibleForTesting
  Future<String?> debugResolveRefreshToken() {
    return _resolveRefreshToken();
  }

  Future<void> _clearAuthTokensFromStorage() async {
    try {
      await _secureStorage.clearToken();
      await _secureStorage.clearRefreshToken();
    } catch (_) {}
    clearAuthTokens();
  }

  Future<String?> _resolveRefreshToken() async {
    final cached = _refreshToken?.trim() ?? '';
    if (cached.isNotEmpty) {
      return cached;
    }
    final stored = (await _secureStorage.getRefreshToken())?.trim() ?? '';
    if (stored.isEmpty) {
      return null;
    }
    _refreshToken = stored;
    return stored;
  }

  void _notifyAuthExpired() {
    final cb = onAuthExpired;
    if (cb != null) {
      scheduleMicrotask(cb);
    }
  }

  ApiException _buildAuthFailureException() {
    final hardFailure = _lastRefreshHardFailure;
    _lastRefreshHardFailure = false;
    if (hardFailure) {
      _notifyAuthExpired();
      return ApiException('未登录或登录已过期', statusCode: 401);
    }
    return ApiException('会话校验失败，请检查网络后重试');
  }

  Future<bool> _refreshAccessToken() async {
    final inFlight = _refreshInFlight;
    if (inFlight != null) return inFlight;

    final future = _refreshAccessTokenInternal();
    _refreshInFlight = future;
    try {
      return await future;
    } finally {
      if (identical(_refreshInFlight, future)) {
        _refreshInFlight = null;
      }
    }
  }

  Future<bool> _refreshAccessTokenInternal() async {
    _lastRefreshHardFailure = false;
    final refreshToken = await _resolveRefreshToken();
    if (refreshToken == null || refreshToken.isEmpty) {
      _lastRefreshHardFailure = true;
      return false;
    }
    try {
      final requestId = _newRequestId();
      final response = await _client
          .post(
            buildApiUri(ApiConfig.refresh),
            headers: _buildHeaders(requestId: requestId, includeAuth: false),
            body: jsonEncode({'refresh_token': refreshToken}),
          )
          .timeout(const Duration(seconds: ApiConfig.timeout));
      if (response.statusCode != 200) {
        if (response.statusCode == 401 || response.statusCode == 403) {
          await _clearAuthTokensFromStorage();
          _lastRefreshHardFailure = true;
        }
        return false;
      }

      final decoded = jsonDecode(response.body);
      if (decoded is! Map<String, dynamic>) {
        await _clearAuthTokensFromStorage();
        _lastRefreshHardFailure = true;
        return false;
      }
      final accessToken = decoded['access_token']?.toString() ?? '';
      final nextRefreshToken = decoded['refresh_token']?.toString() ?? '';
      if (accessToken.isEmpty || nextRefreshToken.isEmpty) {
        await _clearAuthTokensFromStorage();
        _lastRefreshHardFailure = true;
        return false;
      }
      setAuthTokens(accessToken: accessToken, refreshToken: nextRefreshToken);
      await _secureStorage.setToken(accessToken);
      await _secureStorage.setRefreshToken(nextRefreshToken);
      return true;
    } on TimeoutException {
      _lastRefreshHardFailure = false;
      return false;
    } on http.ClientException {
      _lastRefreshHardFailure = false;
      return false;
    } catch (_) {
      _lastRefreshHardFailure = false;
      return false;
    }
  }

  static Uri buildApiUri(
    String endpoint, {
    bool? isWebOverride,
    String? webOriginOverride,
    String? webApiBaseOverride,
    String? mobileBaseUrlOverride,
  }) {
    if (endpoint.startsWith('http://') || endpoint.startsWith('https://')) {
      return Uri.parse(endpoint);
    }
    final normalizedEndpoint = endpoint.startsWith('/')
        ? endpoint
        : '/$endpoint';
    final isWebPlatform = isWebOverride ?? kIsWeb;
    if (isWebPlatform) {
      final rawWebApiBase =
          (webApiBaseOverride ??
                  const String.fromEnvironment('WEB_API_BASE_URL'))
              .trim();
      if (rawWebApiBase.isNotEmpty) {
        final webBase = rawWebApiBase.replaceFirst(RegExp(r'/$'), '');
        return Uri.parse('$webBase$normalizedEndpoint');
      }
      final rawOrigin =
          (webOriginOverride != null && webOriginOverride.trim().isNotEmpty)
          ? webOriginOverride.trim()
          : Uri.base.origin;
      final origin = rawOrigin.replaceFirst(RegExp(r'/$'), '');
      return Uri.parse('$origin$normalizedEndpoint');
    }
    final base = (mobileBaseUrlOverride ?? ApiConfig.baseUrl)
        .trim()
        .replaceFirst(RegExp(r'/$'), '');
    return Uri.parse('$base$normalizedEndpoint');
  }

  String _extractErrorMessage(http.Response response) {
    try {
      final decoded = jsonDecode(response.body);
      if (decoded is Map<String, dynamic>) {
        final err = decoded['error'] ?? decoded['message'];
        return resolveApiErrorText(
          code: decoded['code']?.toString(),
          message: err?.toString(),
          statusCode: response.statusCode,
          fallback: '请求失败: ${response.statusCode}',
        );
      }
    } catch (_) {}
    return resolveApiErrorText(
      statusCode: response.statusCode,
      fallback: '请求失败: ${response.statusCode}',
    );
  }

  bool _isRetryableError(Object error) {
    return error is TimeoutException ||
        isSocketLikeError(error) ||
        error is http.ClientException ||
        _isHandshakeLikeError(error);
  }

  bool _isHandshakeLikeError(Object error) {
    final text = error.toString().toLowerCase();
    return text.contains('handshakeexception') ||
        text.contains('sslhandshakeexception') ||
        text.contains('connection terminated during handshake') ||
        text.contains('tls') ||
        text.contains('ssl');
  }

  ApiException _mapNetworkError(Object error) {
    if (error is TimeoutException) {
      return ApiException('请求超时，请稍后重试');
    }
    if (_isHandshakeLikeError(error)) {
      return ApiException('网络连接异常（TLS 握手失败），请检查网络后重试');
    }
    if (isSocketLikeError(error) || error is http.ClientException) {
      return ApiException('网络连接异常，请检查网络后重试');
    }
    return ApiException(translateErrorText(error, fallback: '网络连接失败，请检查网络后重试'));
  }

  @visibleForTesting
  void setPostOverrideForTesting(PostTransport? override) {
    _postOverrideForTesting = override;
  }

  @visibleForTesting
  static List<String> resolveLoginBaseUrls({List<String>? candidatesOverride}) {
    final raw = (candidatesOverride == null || candidatesOverride.isEmpty)
        ? ApiConfig.loginBaseUrlCandidates
        : candidatesOverride;
    final normalized = <String>[];
    final seen = <String>{};
    for (final item in raw) {
      final base = item.trim().replaceFirst(RegExp(r'/$'), '');
      if (base.isEmpty || seen.contains(base)) continue;
      seen.add(base);
      normalized.add(base);
    }
    final primary = ApiConfig.baseUrl.trim().replaceFirst(RegExp(r'/$'), '');
    if (primary.isNotEmpty && !seen.contains(primary)) {
      normalized.insert(0, primary);
    }
    return normalized;
  }

  bool _isNetworkCategoryApiException(ApiException e) {
    if (e.statusCode != null) return false;
    final msg = e.message.toLowerCase();
    return msg.contains('网络连接异常') ||
        msg.contains('tls') ||
        msg.contains('握手') ||
        msg.contains('超时') ||
        msg.contains('network');
  }

  /// 通用 GET 请求
  Future<dynamic> _get(String endpoint) async {
    Object? lastError;
    var retriedAfterRefresh = false;
    final requestId = _newRequestId();
    for (int attempt = 0; attempt < 3; attempt++) {
      try {
        final response = await _client
            .get(
              buildApiUri(endpoint),
              headers: _buildHeaders(requestId: requestId),
            )
            .timeout(const Duration(seconds: ApiConfig.timeout));

        if (response.statusCode == 200) {
          return jsonDecode(response.body);
        } else if (response.statusCode == 401) {
          if (!retriedAfterRefresh && endpoint != ApiConfig.refresh) {
            final refreshed = await _refreshAccessToken();
            if (refreshed) {
              retriedAfterRefresh = true;
              attempt -= 1;
              continue;
            }
          } else if (endpoint == ApiConfig.refresh) {
            _lastRefreshHardFailure = true;
          }
          throw _buildAuthFailureException();
        } else {
          throw ApiException(
            _extractErrorMessage(response),
            statusCode: response.statusCode,
          );
        }
      } catch (e) {
        if (e is ApiException) rethrow;
        lastError = e;
        if (_isRetryableError(e) && attempt < 2) {
          await Future<void>.delayed(const Duration(milliseconds: 300));
          continue;
        }
        throw _mapNetworkError(e);
      }
    }
    throw _mapNetworkError(lastError ?? 'unknown error');
  }

  /// 通用 POST 请求
  /// 注意：非幂等写操作默认不重试，避免重复提交。
  Future<dynamic> _post(
    String endpoint,
    Map<String, dynamic> data, {
    bool retryOnTransient = false,
    int transientMaxAttempts = 2,
  }) async {
    Object? lastError;
    final maxAttempts = retryOnTransient ? max(2, transientMaxAttempts) : 1;
    var retriedAfterRefresh = false;
    final requestId = _resolveRequestId(data);
    final payload = _withRequestId(data, requestId);
    for (int attempt = 0; attempt < maxAttempts; attempt++) {
      try {
        final response = await _client
            .post(
              buildApiUri(endpoint),
              headers: _buildHeaders(requestId: requestId),
              body: jsonEncode(payload),
            )
            .timeout(const Duration(seconds: ApiConfig.timeout));

        if (response.statusCode == 200) {
          return jsonDecode(response.body);
        } else if (response.statusCode == 401) {
          if (endpoint == ApiConfig.login || endpoint == ApiConfig.register) {
            throw ApiException(_extractErrorMessage(response), statusCode: 401);
          }
          if (!retriedAfterRefresh &&
              endpoint != ApiConfig.refresh &&
              endpoint != ApiConfig.login &&
              endpoint != ApiConfig.register) {
            final refreshed = await _refreshAccessToken();
            if (refreshed) {
              retriedAfterRefresh = true;
              attempt -= 1;
              continue;
            }
          } else if (endpoint == ApiConfig.refresh) {
            _lastRefreshHardFailure = true;
          }
          throw _buildAuthFailureException();
        } else {
          throw ApiException(
            _extractErrorMessage(response),
            statusCode: response.statusCode,
          );
        }
      } catch (e) {
        if (e is ApiException) rethrow;
        lastError = e;
        debugPrint(
          'POST失败 endpoint=$endpoint attempt=${attempt + 1}/$maxAttempts '
          'type=${e.runtimeType} error=$e',
        );
        if (_isRetryableError(e) && attempt < maxAttempts - 1) {
          await Future<void>.delayed(const Duration(milliseconds: 300));
          continue;
        }
        throw _mapNetworkError(e);
      }
    }
    throw _mapNetworkError(lastError ?? 'unknown error');
  }

  Future<dynamic> _put(String endpoint, Map<String, dynamic> data) async {
    var retriedAfterRefresh = false;
    for (int attempt = 0; attempt < 2; attempt++) {
      try {
        final response = await _client
            .put(
              buildApiUri(endpoint),
              headers: _buildHeaders(),
              body: jsonEncode(data),
            )
            .timeout(const Duration(seconds: ApiConfig.timeout));
        if (response.statusCode == 200) {
          return jsonDecode(response.body);
        } else if (response.statusCode == 401 && !retriedAfterRefresh) {
          final refreshed = await _refreshAccessToken();
          if (refreshed) {
            retriedAfterRefresh = true;
            continue;
          }
          throw _buildAuthFailureException();
        } else {
          throw ApiException(_extractErrorMessage(response), statusCode: response.statusCode);
        }
      } catch (e) {
        if (e is ApiException) rethrow;
        throw _mapNetworkError(e);
      }
    }
    throw _mapNetworkError('unknown error');
  }

  Future<dynamic> _delete(String endpoint) async {
    var retriedAfterRefresh = false;
    for (int attempt = 0; attempt < 2; attempt++) {
      try {
        final response = await _client
            .delete(
              buildApiUri(endpoint),
              headers: _buildHeaders(),
            )
            .timeout(const Duration(seconds: ApiConfig.timeout));
        if (response.statusCode == 200) {
          return jsonDecode(response.body);
        } else if (response.statusCode == 401 && !retriedAfterRefresh) {
          final refreshed = await _refreshAccessToken();
          if (refreshed) {
            retriedAfterRefresh = true;
            continue;
          }
          throw _buildAuthFailureException();
        } else {
          throw ApiException(_extractErrorMessage(response), statusCode: response.statusCode);
        }
      } catch (e) {
        if (e is ApiException) rethrow;
        throw _mapNetworkError(e);
      }
    }
    throw _mapNetworkError('unknown error');
  }

  Future<dynamic> _postRequest(
    String endpoint,
    Map<String, dynamic> data, {
    bool retryOnTransient = false,
    int transientMaxAttempts = 2,
  }) {
    final override = _postOverrideForTesting;
    if (override != null) {
      return override(
        endpoint,
        data,
        retryOnTransient: retryOnTransient,
        transientMaxAttempts: transientMaxAttempts,
      );
    }
    return _post(
      endpoint,
      data,
      retryOnTransient: retryOnTransient,
      transientMaxAttempts: transientMaxAttempts,
    );
  }

  Future<dynamic> _postMultipart(
    String endpoint, {
    required String fileField,
    required String filePath,
    Map<String, String>? fields,
  }) async {
    if (filePath.trim().isEmpty) {
      throw ApiException('截图文件不能为空');
    }
    final requestId = _newRequestId();
    var retriedAfterRefresh = false;
    for (int attempt = 0; attempt < 2; attempt++) {
      try {
        final request = http.MultipartRequest(
          'POST',
          buildApiUri(endpoint),
        );
        final headers = _buildHeaders(requestId: requestId);
        headers.remove('Content-Type');
        request.headers.addAll(headers);
        if (fields != null && fields.isNotEmpty) {
          request.fields.addAll(fields);
        }
        request.files.add(await http.MultipartFile.fromPath(fileField, filePath));
        final streamed = await _client.send(request).timeout(
          const Duration(seconds: ApiConfig.timeout),
        );
        final response = await http.Response.fromStream(streamed);
        if (response.statusCode == 200) {
          return jsonDecode(response.body);
        } else if (response.statusCode == 401 && !retriedAfterRefresh) {
          final refreshed = await _refreshAccessToken();
          if (refreshed) {
            retriedAfterRefresh = true;
            continue;
          }
          throw _buildAuthFailureException();
        } else {
          throw ApiException(
            _extractErrorMessage(response),
            statusCode: response.statusCode,
          );
        }
      } catch (e) {
        if (e is ApiException) rethrow;
        if (e is FileSystemException) {
          throw ApiException('读取截图失败，请重新选择图片');
        }
        throw _mapNetworkError(e);
      }
    }
    throw _mapNetworkError('unknown error');
  }

  AssetActionResult _failureResult(
    Object error, {
    String fallback = '操作失败，请稍后再试',
  }) {
    if (error is ApiException) {
      return AssetActionResult.failure(
        resolveApiErrorText(
          message: error.message,
          statusCode: error.statusCode,
          fallback: fallback,
        ),
        data: {if (error.statusCode != null) 'status_code': error.statusCode},
      );
    }
    return AssetActionResult.failure(fallback);
  }

  String _newRequestId() {
    final ts = DateTime.now().microsecondsSinceEpoch;
    final rand = Random.secure().nextInt(0x7fffffff).toRadixString(16);
    return '$ts-$rand';
  }

  String _resolveRequestId(Map<String, dynamic> data) {
    final raw = data['request_id']?.toString().trim() ?? '';
    if (raw.isNotEmpty) return raw;
    return _newRequestId();
  }

  Map<String, dynamic> _withRequestId(
    Map<String, dynamic> data,
    String requestId,
  ) {
    if ((data['request_id']?.toString().trim() ?? '').isNotEmpty) {
      return data;
    }
    return <String, dynamic>{...data, 'request_id': requestId};
  }

  Map<String, dynamic> _toMap(dynamic value) {
    if (value is Map<String, dynamic>) return value;
    if (value is Map) return Map<String, dynamic>.from(value);
    return const {};
  }

  Map<String, dynamic> _ensureMapResponse(
    dynamic value, {
    required String actionLabel,
  }) {
    final map = _toMap(value);
    if (map.isEmpty) {
      throw ApiException('$actionLabel响应异常，请稍后重试');
    }
    return map;
  }

  AssetActionResult _okResultOrFailure(dynamic response) {
    final data = _toMap(response);
    if (data.isEmpty) return const AssetActionResult.success();
    final status = data['status']?.toString().trim();
    if (status == 'ok') return AssetActionResult(ok: true, data: data);
    final message = resolveApiErrorText(
      code: data['code']?.toString(),
      message: data['error']?.toString(),
      fallback: '操作失败，请稍后重试',
    );
    return AssetActionResult.failure(message, data: data);
  }

  // ============================================================
  // 认证相关
  // ============================================================

  Future<Map<String, dynamic>?> login({
    required String username,
    required String password,
    String? deviceId,
    List<String>? baseUrlCandidatesOverride,
  }) async {
    final payload = <String, dynamic>{
      'username': username,
      'password': password,
      if (deviceId != null && deviceId.isNotEmpty) 'device_id': deviceId,
    };

    dynamic raw;
    try {
      raw = await _postRequest(
        ApiConfig.login,
        payload,
        retryOnTransient: true,
        transientMaxAttempts: 3,
      );
    } catch (e) {
      final canFallback =
          !kIsWeb && e is ApiException && _isNetworkCategoryApiException(e);
      if (!canFallback) {
        rethrow;
      }
      final baseCandidates = resolveLoginBaseUrls(
        candidatesOverride: baseUrlCandidatesOverride,
      );
      if (baseCandidates.length <= 1) {
        rethrow;
      }
      ApiException? lastApiError = e;
      var succeeded = false;
      for (final fallbackBase in baseCandidates.skip(1)) {
        final fallbackEndpoint = '$fallbackBase${ApiConfig.login}';
        debugPrint('登录主域失败，切换备用域重试: $fallbackEndpoint');
        try {
          raw = await _postRequest(
            fallbackEndpoint,
            payload,
            retryOnTransient: true,
            transientMaxAttempts: 2,
          );
          succeeded = true;
          break;
        } catch (fallbackError) {
          if (fallbackError is ApiException &&
              _isNetworkCategoryApiException(fallbackError)) {
            lastApiError = fallbackError;
            continue;
          }
          rethrow;
        }
      }
      if (!succeeded) {
        throw lastApiError ?? ApiException('网络连接异常，请检查网络后重试');
      }
    }
    final data = _ensureMapResponse(raw, actionLabel: '登录');
    setAuthTokens(
      accessToken: data['access_token']?.toString(),
      refreshToken: data['refresh_token']?.toString(),
    );
    return data;
  }

  Future<Map<String, dynamic>?> register({
    required String username,
    required String password,
    required String inviteCode,
    String? deviceId,
  }) async {
    final raw = await _post(ApiConfig.register, {
      'username': username,
      'password': password,
      'invite_code': inviteCode,
      if (deviceId != null && deviceId.isNotEmpty) 'device_id': deviceId,
    });
    final data = _ensureMapResponse(raw, actionLabel: '注册');
    setAuthTokens(
      accessToken: data['access_token']?.toString(),
      refreshToken: data['refresh_token']?.toString(),
    );
    return data;
  }

  Future<bool> validateInviteCode(String inviteCode) async {
    final data = await _post(ApiConfig.inviteValidate, {
      'invite_code': inviteCode,
    });
    return data != null && data['valid'] == true;
  }

  Future<Map<String, dynamic>?> refreshSession({
    required String refreshToken,
    String? deviceId,
  }) async {
    final raw = await _post(ApiConfig.refresh, {
      'refresh_token': refreshToken,
      if (deviceId != null && deviceId.isNotEmpty) 'device_id': deviceId,
    });
    final data = _ensureMapResponse(raw, actionLabel: '会话刷新');
    setAuthTokens(
      accessToken: data['access_token']?.toString(),
      refreshToken: data['refresh_token']?.toString() ?? refreshToken,
    );
    return data;
  }

  Future<bool> logout({String? refreshToken}) async {
    await _post(ApiConfig.logout, {
      if (refreshToken != null && refreshToken.isNotEmpty)
        'refresh_token': refreshToken,
    });
    clearAuthTokens();
    return true;
  }

  Future<bool> changePassword({
    required String oldPassword,
    required String newPassword,
  }) async {
    await _post(ApiConfig.changePassword, {
      'old_password': oldPassword,
      'new_password': newPassword,
    });
    return true;
  }

  /// 更新用户资料（昵称/头像）
  Future<Map<String, dynamic>?> updateProfile({
    String? nickname,
    String? avatar,
  }) async {
    try {
      final data = await _post(ApiConfig.profileUpdate, {
        'nickname': nickname,
        'avatar': avatar,
      });
      return data;
    } catch (e) {
      return null;
    }
  }

  /// 获取当前用户资料
  Future<Map<String, dynamic>?> getProfile() async {
    try {
      final data = await _get(ApiConfig.profileMe);
      return data;
    } catch (e) {
      return null;
    }
  }

  /// 获取最新版本信息
  Future<AppVersion?> getAppVersion() async {
    try {
      final data = await _get(ApiConfig.getAppVersion);
      if (data == null) return null;
      return AppVersion.fromJson(data);
    } catch (e) {
      debugPrint('获取版本信息失败: $e');
      return null;
    }
  }

  Future<Map<String, dynamic>?> getWebConfig() async {
    try {
      final data = await _get(ApiConfig.webConfig);
      return _ensureMapResponse(data, actionLabel: '读取Web配置');
    } catch (e) {
      debugPrint('获取 Web 配置失败: $e');
      return null;
    }
  }

  // ============================================================
  // 资产相关
  // ============================================================

  /// 获取投资组合
  Future<List<dynamic>> getPortfolio({
    bool withMetrics = true,
    int? ledgerId,
  }) async {
    final params = <String, String>{
      if (withMetrics) 'with_metrics': '1',
      if (ledgerId != null) 'ledger_id': ledgerId.toString(),
    };
    final endpoint = params.isNotEmpty
        ? Uri(path: ApiConfig.portfolio, queryParameters: params).toString()
        : ApiConfig.portfolio;
    return await _get(endpoint) ?? [];
  }

  // ─── 账本 API ─────────────────────────────────────

  /// 获取账本列表
  Future<List<dynamic>> getLedgers() async {
    return await _get(ApiConfig.portfolioLedgers) ?? [];
  }

  /// 创建账本
  Future<AssetActionResult> createLedger(String name, {String description = ''}) async {
    try {
      final response = await _post(ApiConfig.portfolioLedgers, {
        'name': name,
        'description': description,
      });
      return _okResultOrFailure(response);
    } catch (e) {
      return _failureResult(e);
    }
  }

  /// 更新账本
  Future<AssetActionResult> updateLedger(int id, String name, {String description = ''}) async {
    try {
      final response = await _put('${ApiConfig.portfolioLedgers}/$id', {
        'name': name,
        'description': description,
      });
      return _okResultOrFailure(response);
    } catch (e) {
      return _failureResult(e);
    }
  }

  /// 删除账本
  Future<AssetActionResult> deleteLedger(int id) async {
    try {
      final response = await _delete('${ApiConfig.portfolioLedgers}/$id');
      return _okResultOrFailure(response);
    } catch (e) {
      return _failureResult(e);
    }
  }

  /// 搜索股票/基金
  Future<List<dynamic>> searchStocks(String query) async {
    if (query.isEmpty) return [];
    final endpoint = Uri(
      path: ApiConfig.search,
      queryParameters: {'q': query},
    ).toString();
    return await _get(endpoint) ?? [];
  }

  /// 上传截图，解析添加资产候选结果
  Future<Map<String, dynamic>> parsePortfolioAssetScreenshot(String filePath) async {
    final response = await _postMultipart(
      ApiConfig.portfolioOcrParseAsset,
      fileField: 'file',
      filePath: filePath,
    );
    if (response is Map<String, dynamic>) {
      return response;
    }
    throw ApiException('截图识别返回格式不正确');
  }

  /// 添加投资资产
  Future<AssetActionResult> addPortfolioAsset(
    String code,
    String name,
    double price,
    double qty, {
    String? curr,
    String? assetType,
    String? requestId,
    int? ledgerId,
  }) async {
    try {
      final response = await _post(ApiConfig.portfolioAdd, {
        'code': code,
        'name': name,
        'price': price,
        'qty': qty,
        if (curr != null && curr.isNotEmpty) 'curr': curr,
        if (assetType != null && assetType.isNotEmpty) 'asset_type': assetType,
        'request_id': requestId ?? _newRequestId(),
        ...?(ledgerId == null ? null : {'ledger_id': ledgerId}),
      });
      return _okResultOrFailure(response);
    } catch (e) {
      return _failureResult(e);
    }
  }

  /// 买入（加仓）
  Future<AssetActionResult> buyPortfolioAsset(
    String code,
    double price,
    double qty, {
    String? requestId,
    int? ledgerId,
  }) async {
    try {
      final response = await _post(ApiConfig.portfolioBuy, {
        'code': code,
        'price': price,
        'qty': qty,
        'request_id': requestId ?? _newRequestId(),
        ...?(ledgerId == null ? null : {'ledger_id': ledgerId}),
      });
      return _okResultOrFailure(response);
    } catch (e) {
      return _failureResult(e);
    }
  }

  /// 指定现金账户买入（扣现金 + 加仓）
  Future<AssetActionResult> buyPortfolioAssetWithCash(
    String code,
    String name,
    double price,
    double qty, {
    required int cashAssetId,
    String? curr,
    String? assetType,
    String? requestId,
    int? ledgerId,
  }) async {
    try {
      final response = await _post(ApiConfig.portfolioBuyWithCash, {
        'code': code,
        'name': name,
        'price': price,
        'qty': qty,
        'cash_asset_id': cashAssetId,
        if (curr != null && curr.isNotEmpty) 'curr': curr,
        if (assetType != null && assetType.isNotEmpty) 'asset_type': assetType,
        'request_id': requestId ?? _newRequestId(),
        ...?(ledgerId == null ? null : {'ledger_id': ledgerId}),
      });
      return _okResultOrFailure(response);
    } catch (e) {
      return _failureResult(e);
    }
  }

  /// 卖出（减仓）
  Future<AssetActionResult> sellPortfolioAsset(
    String code,
    double price,
    double qty, {
    String? requestId,
    int? ledgerId,
  }) async {
    try {
      final response = await _post(ApiConfig.portfolioSell, {
        'code': code,
        'price': price,
        'qty': qty,
        'request_id': requestId ?? _newRequestId(),
        ...?(ledgerId == null ? null : {'ledger_id': ledgerId}),
      });
      return _okResultOrFailure(response);
    } catch (e) {
      return _failureResult(e);
    }
  }

  /// 指定现金账户卖出（减仓 + 回款）
  Future<AssetActionResult> sellPortfolioAssetToCash(
    String code,
    double price,
    double qty, {
    required int cashAssetId,
    String? requestId,
    int? ledgerId,
  }) async {
    try {
      final response = await _post(ApiConfig.portfolioSellToCash, {
        'code': code,
        'price': price,
        'qty': qty,
        'cash_asset_id': cashAssetId,
        'request_id': requestId ?? _newRequestId(),
        ...?(ledgerId == null ? null : {'ledger_id': ledgerId}),
      });
      return _okResultOrFailure(response);
    } catch (e) {
      return _failureResult(e);
    }
  }

  /// 修正资产（数量/成本）
  Future<AssetActionResult> modifyPortfolioAsset(
    String code,
    double qty,
    double price, {
    String? note,
    String? requestId,
    int? ledgerId,
  }) async {
    try {
      final payload = <String, dynamic>{
        'code': code,
        'qty': qty,
        'price': price,
        'request_id': requestId ?? _newRequestId(),
        ...?(ledgerId == null ? null : {'ledger_id': ledgerId}),
      };
      final cleanNote = (note ?? '').trim();
      if (cleanNote.isNotEmpty) {
        payload['note'] = cleanNote;
      }
      final response = await _post(ApiConfig.portfolioModify, payload);
      return _okResultOrFailure(response);
    } catch (e) {
      return _failureResult(e);
    }
  }

  Future<AssetActionResult> addPortfolioAdjustmentEvent(
    String code,
    String eventType,
    double amount, {
    String? note,
    String? curr,
    String? requestId,
    int? ledgerId,
  }) async {
    try {
      final payload = <String, dynamic>{
        'code': code,
        'event_type': eventType,
        'amount': amount,
        'request_id': requestId ?? _newRequestId(),
        ...?(ledgerId == null ? null : {'ledger_id': ledgerId}),
      };
      final cleanNote = (note ?? '').trim();
      if (cleanNote.isNotEmpty) {
        payload['note'] = cleanNote;
      }
      final cleanCurr = (curr ?? '').trim();
      if (cleanCurr.isNotEmpty) {
        payload['curr'] = cleanCurr;
      }
      final response = await _post(ApiConfig.portfolioAdjustmentEvent, payload);
      return _okResultOrFailure(response);
    } catch (e) {
      return _failureResult(e);
    }
  }

  /// 删除持仓
  Future<AssetActionResult> deletePortfolioAsset(
    String code, {
    String? requestId,
  }) async {
    try {
      final response = await _post(ApiConfig.portfolioDelete, {
        'code': code,
        'request_id': requestId ?? _newRequestId(),
      });
      return _okResultOrFailure(response);
    } catch (e) {
      return _failureResult(e);
    }
  }

  /// 删除持仓并清理历史交易/快照污染
  Future<AssetActionResult> deletePortfolioAssetCorrective(
    String code, {
    String? requestId,
  }) async {
    try {
      final response = await _post(ApiConfig.portfolioDeleteCorrective, {
        'code': code,
        'request_id': requestId ?? _newRequestId(),
      });
      return _okResultOrFailure(response);
    } catch (e) {
      return _failureResult(e);
    }
  }

  /// 撤销投资写操作
  Future<AssetActionResult> undoPortfolioOperation(String undoToken) async {
    try {
      final response = await _post(ApiConfig.portfolioUndo, {
        'undo_token': undoToken,
      });
      return _okResultOrFailure(response);
    } catch (e) {
      return _failureResult(e);
    }
  }

  /// 批量获取价格
  Future<Map<String, dynamic>> getPricesBatch(List<String> codes) async {
    return await _post(ApiConfig.pricesBatch, {
          'codes': codes,
        }, retryOnTransient: true) ??
        {};
  }

  /// 获取现金资产
  Future<List<dynamic>> getCashAssets() async {
    return await _get(ApiConfig.cashAssets) ?? [];
  }

  /// 获取其他资产
  Future<List<dynamic>> getOtherAssets() async {
    return await _get(ApiConfig.otherAssets) ?? [];
  }

  /// 获取负债
  Future<List<dynamic>> getLiabilities() async {
    return await _get(ApiConfig.liabilities) ?? [];
  }

  /// 添加现金资产
  Future<AssetActionResult> addCashAsset(
    String name,
    double amount, {
    String curr = 'CNY',
  }) async {
    try {
      await _post('${ApiConfig.cashAssets}/add', {
        'name': name,
        'amount': amount,
        'curr': curr,
      });
      return const AssetActionResult.success();
    } catch (e) {
      return _failureResult(e);
    }
  }

  /// 添加其他资产
  Future<AssetActionResult> addOtherAsset(
    String name,
    double amount, {
    String curr = 'CNY',
  }) async {
    try {
      await _post('${ApiConfig.otherAssets}/add', {
        'name': name,
        'amount': amount,
        'curr': curr,
      });
      return const AssetActionResult.success();
    } catch (e) {
      return _failureResult(e);
    }
  }

  /// 添加负债
  Future<AssetActionResult> addLiability(
    String name,
    double amount, {
    String curr = 'CNY',
  }) async {
    try {
      await _post('${ApiConfig.liabilities}/add', {
        'name': name,
        'amount': amount,
        'curr': curr,
      });
      return const AssetActionResult.success();
    } catch (e) {
      return _failureResult(e);
    }
  }

  /// 删除现金资产
  Future<AssetActionResult> deleteCashAsset(int id) async {
    try {
      await _post('${ApiConfig.cashAssets}/delete', {'id': id});
      return const AssetActionResult.success();
    } catch (e) {
      return _failureResult(e);
    }
  }

  /// 删除其他资产
  Future<AssetActionResult> deleteOtherAsset(int id) async {
    try {
      await _post('${ApiConfig.otherAssets}/delete', {'id': id});
      return const AssetActionResult.success();
    } catch (e) {
      return _failureResult(e);
    }
  }

  /// 删除负债
  Future<AssetActionResult> deleteLiability(int id) async {
    try {
      await _post('${ApiConfig.liabilities}/delete', {'id': id});
      return const AssetActionResult.success();
    } catch (e) {
      return _failureResult(e);
    }
  }

  /// 更新现金资产
  Future<AssetActionResult> updateCashAsset(
    int id,
    String name,
    double amount, {
    String curr = 'CNY',
  }) async {
    try {
      await _post('${ApiConfig.cashAssets}/update', {
        'id': id,
        'name': name,
        'amount': amount,
        'curr': curr,
      }, retryOnTransient: true);
      return const AssetActionResult.success();
    } catch (e) {
      return _failureResult(e);
    }
  }

  /// 更新其他资产
  Future<AssetActionResult> updateOtherAsset(
    int id,
    String name,
    double amount, {
    String curr = 'CNY',
  }) async {
    try {
      await _post('${ApiConfig.otherAssets}/update', {
        'id': id,
        'name': name,
        'amount': amount,
        'curr': curr,
      }, retryOnTransient: true);
      return const AssetActionResult.success();
    } catch (e) {
      return _failureResult(e);
    }
  }

  /// 更新负债
  Future<AssetActionResult> updateLiability(
    int id,
    String name,
    double amount, {
    String curr = 'CNY',
  }) async {
    try {
      await _post('${ApiConfig.liabilities}/update', {
        'id': id,
        'name': name,
        'amount': amount,
        'curr': curr,
      }, retryOnTransient: true);
      return const AssetActionResult.success();
    } catch (e) {
      return _failureResult(e);
    }
  }

  /// 新增资产调整记录（同时更新余额）
  Future<AssetActionResult> adjustAsset({
    required String assetType,
    required int assetId,
    required String name,
    required String mode,
    required double delta,
    required String note,
  }) async {
    try {
      final data = await _post(
        '/api/assets/$assetType/$assetId/adjustments',
        {'name': name, 'mode': mode, 'delta': delta, 'note': note},
      );
      final map = (data is Map) ? Map<String, dynamic>.from(data) : <String, dynamic>{};
      return AssetActionResult.success(data: map);
    } catch (e) {
      return _failureResult(e);
    }
  }

  /// 获取资产调整记录列表
  Future<List<dynamic>> getAssetAdjustments({
    required String assetType,
    required int assetId,
  }) async {
    final data = await _get('/api/assets/$assetType/$assetId/adjustments');
    if (data is Map && data['adjustments'] is List) {
      return data['adjustments'] as List<dynamic>;
    }
    return [];
  }

  /// 获取投资持仓交易记录
  Future<List<dynamic>> getPortfolioTransactions(String code, {int? ledgerId}) async {
    final params = <String, String>{'code': code};
    if (ledgerId != null) params['ledger_id'] = ledgerId.toString();
    final endpoint = Uri(path: ApiConfig.portfolioTransactions, queryParameters: params).toString();
    final data = await _get(endpoint);
    if (data is Map && data['records'] is List) {
      return data['records'] as List<dynamic>;
    }
    return [];
  }

  // ============================================================
  // 分析相关
  // ============================================================

  /// 获取盈亏概览
  Future<Map<String, dynamic>> getAnalysisOverview({
    String period = 'all',
    int? ledgerId,
  }) async {
    final query = StringBuffer('period=$period');
    if (ledgerId != null) query.write('&ledger_id=$ledgerId');
    return await _get('${ApiConfig.analysisOverview}?$query') ?? {};
  }

  /// 获取收益日历
  Future<Map<String, dynamic>> getAnalysisCalendar({
    String timeType = 'day',
    int? year,
    int? month,
    int? ledgerId,
  }) async {
    final query = <String, String>{
      'type': timeType,
      if (year != null) 'year': '$year',
      if (month != null) 'month': '$month',
      if (ledgerId != null) 'ledger_id': '$ledgerId',
    };
    final endpoint =
        '${ApiConfig.analysisCalendar}?${Uri(queryParameters: query).query}';
    return await _get(endpoint) ?? {};
  }

  /// 获取盈亏排行
  Future<Map<String, dynamic>> getAnalysisRank({
    String rankType = 'all',
    String market = 'all',
    int? ledgerId,
  }) async {
    final query = StringBuffer('type=$rankType&market=$market');
    if (ledgerId != null) query.write('&ledger_id=$ledgerId');
    return await _get(
          '${ApiConfig.analysisRank}?$query',
        ) ??
        {};
  }

  // ============================================================
  // 其他
  // ============================================================

  /// 获取最新快讯（支持分页）
  Future<Map<String, dynamic>> getNews({
    int page = 1,
    int pageSize = 30,
    String? sinceId,
  }) async {
    final query = StringBuffer('page=$page&page_size=$pageSize');
    final marker = sinceId?.trim() ?? '';
    if (marker.isNotEmpty) {
      query.write('&since_id=${Uri.encodeQueryComponent(marker)}');
    }
    final data = await _get('${ApiConfig.news}?$query');
    if (data is Map<String, dynamic>) {
      return data;
    }
    if (data is Map) {
      return Map<String, dynamic>.from(data);
    }
    if (data is List) {
      return {
        "items": data,
        "page": page,
        "page_size": pageSize,
        "has_more": data.length >= pageSize,
      };
    }
    return {
      "items": [],
      "page": page,
      "page_size": pageSize,
      "has_more": false,
    };
  }

  /// 获取汇率
  Future<Map<String, dynamic>> getExchangeRates() async {
    try {
      return await _get(ApiConfig.rates) ??
          {'USD': 7.25, 'HKD': 0.93, 'CNY': 1.0};
    } catch (e) {
      return {'USD': 7.25, 'HKD': 0.93, 'CNY': 1.0};
    }
  }

  /// 获取市场开闭状态（A/HK/US/Fund）。
  /// 失败时安全降级为全部休市，避免误算当日盈亏。
  Future<Map<String, bool>> getMarketOpenStatus() async {
    const fallback = {'a': false, 'hk': false, 'us': false, 'fund': false};
    bool parseBool(dynamic value) {
      if (value is bool) return value;
      if (value is num) return value != 0;
      if (value is String) {
        final lower = value.trim().toLowerCase();
        return lower == '1' || lower == 'true' || lower == 'yes';
      }
      return false;
    }

    try {
      final data = await _get(ApiConfig.marketStatus);
      final map = _toMap(data);
      final markets = map['markets'];
      if (markets is! Map) return fallback;
      return {
        'a': parseBool((markets['a'] as Map?)?['open']),
        'hk': parseBool((markets['hk'] as Map?)?['open']),
        'us': parseBool((markets['us'] as Map?)?['open']),
        'fund': parseBool((markets['fund'] as Map?)?['open']),
      };
    } catch (e) {
      debugPrint('获取市场状态失败: $e');
      return fallback;
    }
  }

  /// 获取市场详细状态（含 open/reason/trading_day）。
  /// 失败时返回空映射，交由上层按保守策略降级。
  Future<Map<String, dynamic>> getMarketStatuses() async {
    try {
      final data = await _get(ApiConfig.marketStatus);
      final map = _toMap(data);
      final markets = map['markets'];
      if (markets is Map<String, dynamic>) return markets;
      if (markets is Map) return Map<String, dynamic>.from(markets);
      return const <String, dynamic>{};
    } catch (e) {
      debugPrint('获取市场详细状态失败: $e');
      return const <String, dynamic>{};
    }
  }

  /// 增量同步引导：按版本比较返回变更域。
  Future<Map<String, dynamic>> getSyncBootstrap({
    List<String>? include,
    Map<String, String>? clientVersions,
    bool portfolioMetrics = true,
  }) async {
    final payload = <String, dynamic>{
      'include':
          include ??
          const [
            'portfolio',
            'cash_assets',
            'other_assets',
            'liabilities',
            'history',
            'overview_all',
            'rates',
          ],
      'client_versions': clientVersions ?? const {},
    };
    if (portfolioMetrics) {
      payload['portfolio_metrics'] = true;
    }
    final response = await _post(
      ApiConfig.syncBootstrap,
      payload,
      retryOnTransient: true,
    );
    return _toMap(response);
  }

  /// 获取资产历史
  Future<List<dynamic>> getHistory() async {
    return await _get(ApiConfig.history) ?? [];
  }
}

/// API 异常
class ApiException implements Exception {
  final String message;
  final int? statusCode;

  ApiException(this.message, {this.statusCode});

  @override
  String toString() => message;
}
