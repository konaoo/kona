import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/api_config.dart';

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
    final headers = <String, String>{
      'Content-Type': 'application/json',
    };
    if (_token != null) {
      headers['Authorization'] = 'Bearer $_token';
    }
    return headers;
  }

  /// 通用 GET 请求
  Future<dynamic> _get(String endpoint) async {
    try {
      final response = await _client
          .get(
            Uri.parse('${ApiConfig.baseUrl}$endpoint'),
            headers: _getHeaders(),
          )
          .timeout(const Duration(seconds: ApiConfig.timeout));

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else if (response.statusCode == 401) {
        throw ApiException('未登录或登录已过期', statusCode: 401);
      } else {
        throw ApiException('请求失败: ${response.statusCode}', statusCode: response.statusCode);
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('网络连接失败: $e');
    }
  }

  /// 通用 POST 请求
  Future<dynamic> _post(String endpoint, Map<String, dynamic> data) async {
    try {
      final response = await _client
          .post(
            Uri.parse('${ApiConfig.baseUrl}$endpoint'),
            headers: _getHeaders(),
            body: jsonEncode(data),
          )
          .timeout(const Duration(seconds: ApiConfig.timeout));

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else if (response.statusCode == 401) {
        throw ApiException('未登录或登录已过期', statusCode: 401);
      } else {
        throw ApiException('请求失败: ${response.statusCode}', statusCode: response.statusCode);
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('网络连接失败: $e');
    }
  }

  // ============================================================
  // 认证相关
  // ============================================================

  /// 登录
  Future<Map<String, dynamic>?> login(String userId, String email, String code) async {
    try {
      final data = await _post(ApiConfig.login, {
        'user_id': userId,
        'email': email,
        'code': code,
      });
      if (data != null && data['token'] != null) {
        _token = data['token'];
      }
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
  Future<bool> addPortfolioAsset(
    String code,
    String name,
    double price,
    double qty, {
    String? curr,
    String? assetType,
  }) async {
    try {
      await _post(ApiConfig.portfolioAdd, {
        'code': code,
        'name': name,
        'price': price,
        'qty': qty,
        if (curr != null && curr.isNotEmpty) 'curr': curr,
        if (assetType != null && assetType.isNotEmpty) 'asset_type': assetType,
      });
      return true;
    } catch (e) {
      return false;
    }
  }

  /// 买入（加仓）
  Future<bool> buyPortfolioAsset(String code, double price, double qty) async {
    try {
      await _post(ApiConfig.portfolioBuy, {
        'code': code,
        'price': price,
        'qty': qty,
      });
      return true;
    } catch (e) {
      return false;
    }
  }

  /// 卖出（减仓）
  Future<bool> sellPortfolioAsset(String code, double price, double qty) async {
    try {
      await _post(ApiConfig.portfolioSell, {
        'code': code,
        'price': price,
        'qty': qty,
      });
      return true;
    } catch (e) {
      return false;
    }
  }

  /// 修正资产（数量/成本/调整）
  Future<bool> modifyPortfolioAsset(String code, double qty, double price, double adjustment) async {
    try {
      await _post(ApiConfig.portfolioModify, {
        'code': code,
        'qty': qty,
        'price': price,
        'adjustment': adjustment,
      });
      return true;
    } catch (e) {
      return false;
    }
  }

  /// 删除持仓
  Future<bool> deletePortfolioAsset(String code) async {
    try {
      await _post(ApiConfig.portfolioDelete, {'code': code});
      return true;
    } catch (e) {
      return false;
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
  Future<bool> addCashAsset(String name, double amount, {String curr = 'CNY'}) async {
    try {
      await _post('${ApiConfig.cashAssets}/add', {
        'name': name,
        'amount': amount,
        'curr': curr,
      });
      return true;
    } catch (e) {
      return false;
    }
  }

  /// 添加其他资产
  Future<bool> addOtherAsset(String name, double amount, {String curr = 'CNY'}) async {
    try {
      await _post('${ApiConfig.otherAssets}/add', {
        'name': name,
        'amount': amount,
        'curr': curr,
      });
      return true;
    } catch (e) {
      return false;
    }
  }

  /// 添加负债
  Future<bool> addLiability(String name, double amount, {String curr = 'CNY'}) async {
    try {
      await _post('${ApiConfig.liabilities}/add', {
        'name': name,
        'amount': amount,
        'curr': curr,
      });
      return true;
    } catch (e) {
      return false;
    }
  }

  /// 删除现金资产
  Future<bool> deleteCashAsset(int id) async {
    try {
      await _post('${ApiConfig.cashAssets}/delete', {'id': id});
      return true;
    } catch (e) {
      return false;
    }
  }

  /// 删除其他资产
  Future<bool> deleteOtherAsset(int id) async {
    try {
      await _post('${ApiConfig.otherAssets}/delete', {'id': id});
      return true;
    } catch (e) {
      return false;
    }
  }

  /// 删除负债
  Future<bool> deleteLiability(int id) async {
    try {
      await _post('${ApiConfig.liabilities}/delete', {'id': id});
      return true;
    } catch (e) {
      return false;
    }
  }

  // ============================================================
  // 分析相关
  // ============================================================

  /// 获取盈亏概览
  Future<Map<String, dynamic>> getAnalysisOverview({String period = 'all'}) async {
    return await _get('${ApiConfig.analysisOverview}?period=$period') ?? {};
  }

  /// 获取收益日历
  Future<Map<String, dynamic>> getAnalysisCalendar({String timeType = 'day'}) async {
    return await _get('${ApiConfig.analysisCalendar}?type=$timeType') ?? {};
  }

  /// 获取盈亏排行
  Future<Map<String, dynamic>> getAnalysisRank({String rankType = 'all', String market = 'all'}) async {
    return await _get('${ApiConfig.analysisRank}?type=$rankType&market=$market') ?? {};
  }

  // ============================================================
  // 其他
  // ============================================================

  /// 获取最新快讯（支持分页）
  Future<Map<String, dynamic>> getNews({int page = 1, int pageSize = 30}) async {
    final data = await _get('${ApiConfig.news}?page=$page&page_size=$pageSize');
    if (data is Map<String, dynamic>) {
      return data;
    }
    if (data is Map) {
      return Map<String, dynamic>.from(data as Map);
    }
    if (data is List) {
      return {"items": data, "page": page, "page_size": pageSize, "has_more": data.length >= pageSize};
    }
    return {"items": [], "page": page, "page_size": pageSize, "has_more": false};
  }

  /// 发送登录验证码
  Future<bool> sendLoginCode(String email) async {
    try {
      await _post(ApiConfig.sendCode, {'email': email});
      return true;
    } catch (e) {
      return false;
    }
  }

  /// 获取汇率
  Future<Map<String, dynamic>> getExchangeRates() async {
    try {
      return await _get(ApiConfig.rates) ?? {'USD': 7.25, 'HKD': 0.93, 'CNY': 1.0};
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
