import 'dart:async';
import 'dart:convert';
import 'dart:math';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../config/api_config.dart';
import '../models/asset_action_result.dart';
import '../utils/network_error_stub.dart'
    if (dart.library.io) '../utils/network_error_io.dart';

/// API 服务 - 封装所有后端 API 调用
class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  String? _token;
  final http.Client _client = http.Client();

  /// 设置认证 token
  void setToken(String token) {
    _token = token;
  }

  /// 清除认证 token
  void clearToken() {
    _token = null;
  }

  /// 获取请求头
  Map<String, String> _getHeaders() {
    final headers = <String, String>{'Content-Type': 'application/json'};
    if (_token != null) {
      headers['Authorization'] = 'Bearer $_token';
    }
    return headers;
  }

  static Uri buildApiUri(
    String endpoint, {
    bool? isWebOverride,
    String? webOriginOverride,
    String? mobileBaseUrlOverride,
  }) {
    if (endpoint.startsWith('http://') || endpoint.startsWith('https://')) {
      return Uri.parse(endpoint);
    }
    final normalizedEndpoint = endpoint.startsWith('/') ? endpoint : '/$endpoint';
    final isWebPlatform = isWebOverride ?? kIsWeb;
    if (isWebPlatform) {
      final rawOrigin = (webOriginOverride != null && webOriginOverride.trim().isNotEmpty)
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
        if (err is String && err.trim().isNotEmpty) {
          return err.trim();
        }
      }
    } catch (_) {}
    return '请求失败: ${response.statusCode}';
  }

  bool _isRetryableError(Object error) {
    return error is TimeoutException ||
        isSocketLikeError(error) ||
        error is http.ClientException;
  }

  ApiException _mapNetworkError(Object error) {
    if (error is TimeoutException) {
      return ApiException('请求超时，请稍后重试');
    }
    if (isSocketLikeError(error) || error is http.ClientException) {
      return ApiException('网络连接异常，请检查网络后重试');
    }
    return ApiException('网络连接失败: $error');
  }

  /// 通用 GET 请求
  Future<dynamic> _get(String endpoint) async {
    Object? lastError;
    for (int attempt = 0; attempt < 2; attempt++) {
      try {
        final response = await _client
            .get(
              buildApiUri(endpoint),
              headers: _getHeaders(),
            )
            .timeout(const Duration(seconds: ApiConfig.timeout));

        if (response.statusCode == 200) {
          return jsonDecode(response.body);
        } else if (response.statusCode == 401) {
          throw ApiException('未登录或登录已过期', statusCode: 401);
        } else {
          throw ApiException(
            _extractErrorMessage(response),
            statusCode: response.statusCode,
          );
        }
      } catch (e) {
        if (e is ApiException) rethrow;
        lastError = e;
        if (_isRetryableError(e) && attempt == 0) {
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
  }) async {
    Object? lastError;
    final maxAttempts = retryOnTransient ? 2 : 1;
    for (int attempt = 0; attempt < maxAttempts; attempt++) {
      try {
        final response = await _client
            .post(
              buildApiUri(endpoint),
              headers: _getHeaders(),
              body: jsonEncode(data),
            )
            .timeout(const Duration(seconds: ApiConfig.timeout));

        if (response.statusCode == 200) {
          return jsonDecode(response.body);
        } else if (response.statusCode == 401) {
          throw ApiException('未登录或登录已过期', statusCode: 401);
        } else {
          throw ApiException(
            _extractErrorMessage(response),
            statusCode: response.statusCode,
          );
        }
      } catch (e) {
        if (e is ApiException) rethrow;
        lastError = e;
        if (_isRetryableError(e) && attempt < maxAttempts - 1) {
          await Future<void>.delayed(const Duration(milliseconds: 300));
          continue;
        }
        throw _mapNetworkError(e);
      }
    }
    throw _mapNetworkError(lastError ?? 'unknown error');
  }

  AssetActionResult _failureResult(
    Object error, {
    String fallback = '操作失败，请稍后再试',
  }) {
    if (error is ApiException) {
      return AssetActionResult.failure(
        error.message,
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
    final error = data['error']?.toString().trim();
    final message = (error != null && error.isNotEmpty) ? error : '操作失败，请稍后重试';
    return AssetActionResult.failure(message, data: data);
  }

  // ============================================================
  // 认证相关
  // ============================================================

  Future<Map<String, dynamic>?> login({
    required String username,
    required String password,
    String? deviceId,
  }) async {
    final raw = await _post(ApiConfig.login, {
      'username': username,
      'password': password,
      if (deviceId != null && deviceId.isNotEmpty) 'device_id': deviceId,
    });
    final data = _ensureMapResponse(raw, actionLabel: '登录');
    if (data != null && data['access_token'] != null) {
      _token = data['access_token'];
    }
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
    if (data != null && data['access_token'] != null) {
      _token = data['access_token'];
    }
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
    if (data != null && data['access_token'] != null) {
      _token = data['access_token'];
    }
    return data;
  }

  Future<bool> logout({String? refreshToken}) async {
    await _post(ApiConfig.logout, {
      if (refreshToken != null && refreshToken.isNotEmpty)
        'refresh_token': refreshToken,
    });
    _token = null;
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
        if (nickname != null) 'nickname': nickname,
        if (avatar != null) 'avatar': avatar,
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

  // ============================================================
  // 资产相关
  // ============================================================

  /// 获取投资组合
  Future<List<dynamic>> getPortfolio() async {
    return await _get(ApiConfig.portfolio) ?? [];
  }

  /// 搜索股票/基金
  Future<List<dynamic>> searchStocks(String query) async {
    if (query.isEmpty) return [];
    return await _get('${ApiConfig.search}?q=$query') ?? [];
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
  }) async {
    try {
      final response = await _post(ApiConfig.portfolioBuy, {
        'code': code,
        'price': price,
        'qty': qty,
        'request_id': requestId ?? _newRequestId(),
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
  }) async {
    try {
      final response = await _post(ApiConfig.portfolioSell, {
        'code': code,
        'price': price,
        'qty': qty,
        'request_id': requestId ?? _newRequestId(),
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
  }) async {
    try {
      final response = await _post(ApiConfig.portfolioSellToCash, {
        'code': code,
        'price': price,
        'qty': qty,
        'cash_asset_id': cashAssetId,
        'request_id': requestId ?? _newRequestId(),
      });
      return _okResultOrFailure(response);
    } catch (e) {
      return _failureResult(e);
    }
  }

  /// 修正资产（数量/成本/调整）
  Future<AssetActionResult> modifyPortfolioAsset(
    String code,
    double qty,
    double price,
    double adjustment, {
    String? requestId,
  }) async {
    try {
      final response = await _post(ApiConfig.portfolioModify, {
        'code': code,
        'qty': qty,
        'price': price,
        'adjustment': adjustment,
        'request_id': requestId ?? _newRequestId(),
      });
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
    return await _post(ApiConfig.pricesBatch, {'codes': codes}) ?? {};
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

  // ============================================================
  // 分析相关
  // ============================================================

  /// 获取盈亏概览
  Future<Map<String, dynamic>> getAnalysisOverview({
    String period = 'all',
  }) async {
    return await _get('${ApiConfig.analysisOverview}?period=$period') ?? {};
  }

  /// 获取收益日历
  Future<Map<String, dynamic>> getAnalysisCalendar({
    String timeType = 'day',
    int? year,
    int? month,
  }) async {
    final query = <String, String>{
      'type': timeType,
      if (year != null) 'year': '$year',
      if (month != null) 'month': '$month',
    };
    final endpoint =
        '${ApiConfig.analysisCalendar}?${Uri(queryParameters: query).query}';
    return await _get(endpoint) ?? {};
  }

  /// 获取盈亏排行
  Future<Map<String, dynamic>> getAnalysisRank({
    String rankType = 'all',
    String market = 'all',
  }) async {
    return await _get(
          '${ApiConfig.analysisRank}?type=$rankType&market=$market',
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
  }) async {
    final data = await _get('${ApiConfig.news}?page=$page&page_size=$pageSize');
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
