import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/cache_service.dart';
import '../models/portfolio.dart';
import '../models/asset.dart';

/// 应用状态管理
class AppState extends ChangeNotifier {
  final ApiService _api = ApiService();
  final CacheService _cache = CacheService();

  // 用户状态
  bool _isLoggedIn = false;
  String? _token;
  String? _email;
  String? _userId;
  int? _userNumber;

  // 资产数据
  double _totalAsset = 0;
  double _totalCash = 0;
  double _totalInvest = 0;
  double _totalOther = 0;
  double _totalLiability = 0;

  // 投资组合
  List<PortfolioItem> _portfolio = [];
  Map<String, PriceInfo> _prices = {};
  String _currentCategory = 'all';
  bool _portfolioLoaded = false;

  // 资产列表
  List<Asset> _cashAssets = [];
  List<Asset> _otherAssets = [];
  List<Asset> _liabilities = [];

  // 汇率
  Map<String, double> _exchangeRates = {'USD': 7.25, 'HKD': 0.93, 'CNY': 1.0};

  // 历史数据
  double _monthChange = 0;
  double _yearChange = 0;
  double _historyPeak = 0;
  bool _hasMonthBaseline = false;
  bool _hasYearBaseline = false;
  bool _monthFromFirst = false;
  bool _yearFromFirst = false;

  // 金额隐藏
  bool _amountHidden = false;

  // ============================================================
  // Getters
  // ============================================================

  bool get isLoggedIn => _isLoggedIn;
  String? get token => _token;
  String? get email => _email;
  String? get userId => _userId;
  int? get userNumber => _userNumber;

  double get totalAsset => _totalAsset;
  double get totalCash => _totalCash;
  double get totalInvest => _totalInvest;
  double get totalOther => _totalOther;
  double get totalLiability => _totalLiability;

  List<PortfolioItem> get portfolio => _portfolio;
  Map<String, PriceInfo> get prices => _prices;
  String get currentCategory => _currentCategory;
  bool get portfolioLoaded => _portfolioLoaded;

  List<Asset> get cashAssets => _cashAssets;
  List<Asset> get otherAssets => _otherAssets;
  List<Asset> get liabilities => _liabilities;

  Map<String, double> get exchangeRates => _exchangeRates;
  bool get amountHidden => _amountHidden;

  double get monthChange => _monthChange;
  double get yearChange => _yearChange;
  double get historyPeak => _historyPeak;
  bool get hasMonthBaseline => _hasMonthBaseline;
  bool get hasYearBaseline => _hasYearBaseline;
  bool get monthFromFirst => _monthFromFirst;
  bool get yearFromFirst => _yearFromFirst;

  double _rateForCurrency(String curr) {
    switch (curr.toUpperCase()) {
      case 'USD':
        return _exchangeRates['USD'] ?? 7.25;
      case 'HKD':
        return _exchangeRates['HKD'] ?? 0.93;
      default:
        return 1.0;
    }
  }

  /// 过滤后的投资组合
  List<PortfolioItem> get filteredPortfolio {
    if (_currentCategory == 'all') return _portfolio;
    return _portfolio.where((item) => item.marketType == _currentCategory).toList();
  }

  /// 投资总市值
  double get investTotalMV {
    double total = 0;
    for (var item in _portfolio) {
      final priceInfo = _prices[item.code];
      final hasValidPrice = priceInfo != null && priceInfo.price > 0;
      final currentPrice = hasValidPrice ? priceInfo.price : item.price;
      final rate = _rateForCurrency(item.curr);
      total += currentPrice * item.qty * rate;
    }
    return total;
  }

  /// 投资今日盈亏
  double get investDayPnl {
    double total = 0;
    for (var item in _portfolio) {
      final priceInfo = _prices[item.code];
      if (priceInfo != null && priceInfo.price > 0) {
        final rate = _rateForCurrency(item.curr);
        total += priceInfo.change * item.qty * rate;
      }
    }
    return total;
  }

  /// 投资今日盈亏率
  double get investDayPnlRate {
    double pnl = 0;
    double base = 0;
    for (var item in _portfolio) {
      final priceInfo = _prices[item.code];
      if (priceInfo != null && priceInfo.price > 0) {
        final rate = _rateForCurrency(item.curr);
        final yclose = priceInfo.yclose > 0 ? priceInfo.yclose : item.price;
        pnl += priceInfo.change * item.qty * rate;
        base += yclose * item.qty * rate;
      } else {
        final rate = _rateForCurrency(item.curr);
        base += item.price * item.qty * rate;
      }
    }
    return base > 0 ? (pnl / base * 100) : 0;
  }

  /// 投资持仓盈亏
  double get investHoldingPnl {
    double total = 0;
    for (var item in _portfolio) {
      final priceInfo = _prices[item.code];
      final hasValidPrice = priceInfo != null && priceInfo.price > 0;
      final currentPrice = hasValidPrice ? priceInfo.price : item.price;
      final rate = _rateForCurrency(item.curr);
      final mv = currentPrice * item.qty * rate;
      final cost = item.price * item.qty * rate;
      total += mv - cost + item.adjustment * rate;
    }
    return total;
  }

  /// 投资持仓盈亏率
  double get investHoldingPnlRate {
    double totalCost = 0;
    for (var item in _portfolio) {
      final rate = _rateForCurrency(item.curr);
      totalCost += item.price * item.qty * rate;
    }
    return totalCost > 0 ? (investHoldingPnl / totalCost * 100) : 0;
  }

  // ============================================================
  // Methods
  // ============================================================

  Future<void> hydrateFromCache() async {
    final cachedPortfolio = await _cache.getJson('cache_portfolio');
    if (cachedPortfolio != null && cachedPortfolio['items'] is List) {
      _portfolio = (cachedPortfolio['items'] as List)
          .map((e) => PortfolioItem.fromJson(e))
          .toList();
    }

    final cachedCash = await _cache.getJson('cache_cash_assets');
    if (cachedCash != null && cachedCash['items'] is List) {
      _cashAssets = (cachedCash['items'] as List).map((e) => Asset.fromJson(e)).toList();
    }

    final cachedOther = await _cache.getJson('cache_other_assets');
    if (cachedOther != null && cachedOther['items'] is List) {
      _otherAssets = (cachedOther['items'] as List).map((e) => Asset.fromJson(e)).toList();
    }

    final cachedLiabilities = await _cache.getJson('cache_liabilities');
    if (cachedLiabilities != null && cachedLiabilities['items'] is List) {
      _liabilities = (cachedLiabilities['items'] as List).map((e) => Asset.fromJson(e)).toList();
    }

    final cachedPrices = await _cache.getJson('cache_prices');
    if (cachedPrices != null && cachedPrices['items'] is Map) {
      _prices = {};
      (cachedPrices['items'] as Map).forEach((key, value) {
        if (value is Map<String, dynamic>) {
          _prices[key.toString()] = PriceInfo.fromJson(value);
        }
      });
    }

    final cachedHistory = await _cache.getJson('cache_history');
    if (cachedHistory != null && cachedHistory['items'] is List) {
      _calculateHistoryStats(cachedHistory['items'] as List);
    }

    final cachedRates = await _cache.getJson('cache_exchange_rates');
    if (cachedRates != null && cachedRates['rates'] is Map) {
      updateExchangeRates(cachedRates['rates'] as Map<String, dynamic>);
    }

    // recompute totals
    _totalCash = _cashAssets.fold(0, (sum, item) => sum + item.amount);
    _totalOther = _otherAssets.fold(0, (sum, item) => sum + item.amount);
    _totalLiability = _liabilities.fold(0, (sum, item) => sum + item.amount);
    _totalInvest = investTotalMV;
    _totalAsset = _totalCash + _totalInvest + _totalOther - _totalLiability;

    _portfolioLoaded = _portfolio.isNotEmpty || _cashAssets.isNotEmpty;
    notifyListeners();
  }

  Future<void> savePortfolioToCache() async {
    await _cache.setJson('cache_portfolio', {
      'items': _portfolio.map((e) => e.toJson()).toList(),
    });
  }

  Future<void> saveHomeCache(List<dynamic> history) async {
    await _cache.setJson('cache_portfolio', {
      'items': _portfolio.map((e) => e.toJson()).toList(),
    });
    await _cache.setJson('cache_cash_assets', {
      'items': _cashAssets.map((e) => e.toJson()).toList(),
    });
    await _cache.setJson('cache_other_assets', {
      'items': _otherAssets.map((e) => e.toJson()).toList(),
    });
    await _cache.setJson('cache_liabilities', {
      'items': _liabilities.map((e) => e.toJson()).toList(),
    });
    await _cache.setJson('cache_history', {
      'items': history,
    });
    await _cache.setJson('cache_exchange_rates', {
      'rates': _exchangeRates,
    });
    await _cache.setJson('cache_prices', {
      'items': _prices.map((key, value) => MapEntry(key, {
        'price': value.price,
        'yclose': value.yclose,
        'chg': value.change,
      })),
    });
  }

  /// 登录
  Future<bool> login(String userId, String email) async {
    try {
      final result = await _api.login(userId, email);
      if (result != null && result['token'] != null) {
        _isLoggedIn = true;
        _token = result['token'];
        _email = result['email'];
        _userId = result['user_id'];
        _userNumber = result['user_number'];
        _api.setToken(result['token']);
        notifyListeners();
        return true;
      }
      return false;
    } catch (e) {
      return false;
    }
  }

  /// 设置登录状态
  void setLoggedIn({
    required String token,
    required String email,
    required String userId,
    int? userNumber,
  }) {
    _isLoggedIn = true;
    _token = token;
    _email = email;
    _userId = userId;
    _userNumber = userNumber;
    _api.setToken(token);
    notifyListeners();
  }

  /// 退出登录
  void logout() {
    _isLoggedIn = false;
    _token = null;
    _email = null;
    _userId = null;
    _userNumber = null;
    _api.clearToken();
    _portfolio = [];
    _prices = {};
    _cashAssets = [];
    _otherAssets = [];
    _liabilities = [];
    _portfolioLoaded = false;
    notifyListeners();
  }

  /// 切换金额隐藏
  void toggleAmountHidden() {
    _amountHidden = !_amountHidden;
    notifyListeners();
  }

  /// 格式化金额（支持隐藏）
  String formatAmount(double value, {String prefix = '¥'}) {
    if (_amountHidden) return '****';
    return '$prefix${value.toStringAsFixed(0).replaceAllMapped(
      RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'),
      (Match m) => '${m[1]},',
    )}';
  }

  /// 设置分类
  void setCategory(String category) {
    _currentCategory = category;
    notifyListeners();
  }

  /// 更新汇率
  void updateExchangeRates(Map<String, dynamic> rates) {
    _exchangeRates = {
      'USD': (rates['USD'] as num?)?.toDouble() ?? 7.25,
      'HKD': (rates['HKD'] as num?)?.toDouble() ?? 0.93,
      'CNY': 1.0,
    };
    notifyListeners();
  }

  /// 刷新首页数据
  Future<void> refreshHomeData() async {
    try {
      // 并行获取数据
      final results = await Future.wait([
        _api.getCashAssets(),
        _api.getOtherAssets(),
        _api.getLiabilities(),
        _api.getPortfolio(),
        _api.getHistory(),
      ]);

      _cashAssets = (results[0] as List).map((e) => Asset.fromJson(e)).toList();
      _otherAssets = (results[1] as List).map((e) => Asset.fromJson(e)).toList();
      _liabilities = (results[2] as List).map((e) => Asset.fromJson(e)).toList();
      _portfolio = (results[3] as List).map((e) => PortfolioItem.fromJson(e)).toList();

      // 获取价格
      if (_portfolio.isNotEmpty) {
        final codes = _portfolio.map((e) => e.code).toList();

        // 代码转换：将前端代码转换为价格API需要的格式
        final priceApiCodes = codes.map((code) {
          // gb_boxx -> boxx (去掉 gb_ 前缀)
          if (code.startsWith('gb_')) {
            return code.substring(3); // 去掉 "gb_" 前缀
          }
          return code;
        }).toList();

        debugPrint('请求价格的代码列表: $codes');
        debugPrint('价格API代码转换: $priceApiCodes');

        final pricesData = await _api.getPricesBatch(priceApiCodes);
        debugPrint('价格API返回数据: ${pricesData.keys.toList()}');

        // 转换价格数据，将价格API的key映射回原始代码
        _prices = {};
        for (int i = 0; i < codes.length; i++) {
          final originalCode = codes[i];
          final apiCode = priceApiCodes[i];

          if (pricesData.containsKey(apiCode)) {
            try {
              _prices[originalCode] = PriceInfo.fromJson(pricesData[apiCode]);
              debugPrint('成功解析价格: $originalCode (API: $apiCode) = ${pricesData[apiCode]}');
            } catch (e) {
              debugPrint('解析价格失败: $originalCode (API: $apiCode), 错误: $e');
            }
          } else {
            debugPrint('警告: 价格API未返回代码 $apiCode (原始: $originalCode)');
          }
        }
      }

      // 计算总额（必须在历史数据计算之前）
      _totalCash = _cashAssets.fold(0, (sum, item) => sum + item.amount);
      _totalOther = _otherAssets.fold(0, (sum, item) => sum + item.amount);
      _totalLiability = _liabilities.fold(0, (sum, item) => sum + item.amount);
      _totalInvest = investTotalMV;
      _totalAsset = _totalCash + _totalInvest + _totalOther - _totalLiability;

      // 处理历史数据（必须在总资产计算之后）
      final history = results[4] as List;
      _calculateHistoryStats(history);

      await saveHomeCache(history);

      _portfolioLoaded = true;
      notifyListeners();
    } catch (e) {
      debugPrint('刷新首页数据失败: $e');
    }
  }

  /// 刷新所有核心数据（用于启动与下拉刷新）
  Future<void> refreshAll() async {
    await Future.wait([
      refreshHomeData(),
      loadExchangeRates(),
    ]);
  }

  /// 添加资产（现金/其他/负债）
  Future<bool> addAsset({
    required String type,
    required String name,
    required double amount,
  }) async {
    bool ok = false;
    if (type == 'cash') {
      ok = await _api.addCashAsset(name, amount);
    } else if (type == 'other') {
      ok = await _api.addOtherAsset(name, amount);
    } else if (type == 'liability') {
      ok = await _api.addLiability(name, amount);
    }
    if (!ok) return false;
    await refreshHomeData();
    return true;
  }

  /// 删除资产（现金/其他/负债）
  Future<bool> deleteAsset({
    required String type,
    required int id,
  }) async {
    bool ok = false;
    if (type == 'cash') {
      ok = await _api.deleteCashAsset(id);
    } else if (type == 'other') {
      ok = await _api.deleteOtherAsset(id);
    } else if (type == 'liability') {
      ok = await _api.deleteLiability(id);
    }
    if (!ok) return false;
    await refreshHomeData();
    return true;
  }

  /// 搜索股票/基金
  Future<List<dynamic>> searchStocks(String query) async {
    return await _api.searchStocks(query);
  }

  /// 添加投资资产
  Future<bool> addInvestment({
    required String code,
    required String name,
    required double price,
    required double qty,
    String? curr,
  }) async {
    final ok = await _api.addPortfolioAsset(code, name, price, qty, curr: curr);
    if (!ok) return false;
    await refreshHomeData();
    return true;
  }

  /// 买入（加仓）
  Future<bool> buyInvestment({
    required String code,
    required double price,
    required double qty,
  }) async {
    final ok = await _api.buyPortfolioAsset(code, price, qty);
    if (!ok) return false;
    await refreshHomeData();
    return true;
  }

  /// 卖出（减仓）
  Future<bool> sellInvestment({
    required String code,
    required double price,
    required double qty,
  }) async {
    final ok = await _api.sellPortfolioAsset(code, price, qty);
    if (!ok) return false;
    await refreshHomeData();
    return true;
  }

  /// 计算历史统计数据
  void _calculateHistoryStats(List<dynamic> history) {
    if (history.isEmpty) {
      _monthChange = 0;
      _yearChange = 0;
      _historyPeak = 0;
      _hasMonthBaseline = false;
      _hasYearBaseline = false;
      _monthFromFirst = false;
      _yearFromFirst = false;
      return;
    }

    final now = DateTime.now();

    double? monthStart;
    double? yearStart;
    double peak = 0;
    double? firstNonZero;
    String? firstNonZeroDate;
    bool monthFromCurrent = false;
    bool yearFromCurrent = false;

    // 按日期排序
    final sortedHistory = List<Map<String, dynamic>>.from(
      history.map((e) => e as Map<String, dynamic>)
    );
    sortedHistory.sort((a, b) => a['date'].compareTo(b['date']));

    debugPrint('历史数据计算: 当前日期=${now.toString().substring(0,10)}, 当前总资产=$_totalAsset');
    debugPrint('历史数据条数: ${sortedHistory.length}');
    if (sortedHistory.isNotEmpty) {
      debugPrint('最早记录: ${sortedHistory.first['date']}, 资产=${sortedHistory.first['total_asset']}');
      debugPrint('最新记录: ${sortedHistory.last['date']}, 资产=${sortedHistory.last['total_asset']}');
    }

    for (var item in sortedHistory) {
      final date = DateTime.parse(item['date']);
      final totalAsset = (item['total_asset'] as num).toDouble();

      // 历史峰值
      if (totalAsset > peak) peak = totalAsset;

      if (totalAsset != 0 && firstNonZero == null) {
        firstNonZero = totalAsset;
        firstNonZeroDate = item['date'];
      }

      // 本月初数据（找到本月第一条记录）
      if (date.year == now.year && date.month == now.month && monthStart == null && totalAsset != 0) {
        monthStart = totalAsset;
        monthFromCurrent = true;
        debugPrint('找到本月数据: ${item['date']}, 资产=$totalAsset');
      }

      // 今年初数据（找到今年第一条记录）
      if (date.year == now.year && yearStart == null && totalAsset != 0) {
        yearStart = totalAsset;
        yearFromCurrent = true;
        debugPrint('找到今年数据: ${item['date']}, 资产=$totalAsset');
      }
    }

    // 如果没有本月/今年数据，使用首次记账作为起点（新用户友好）
    if (monthStart == null && firstNonZero != null) {
      monthStart = firstNonZero;
      _monthFromFirst = true;
      debugPrint('使用首次记账作为本月起点: $firstNonZeroDate, 资产=$monthStart');
    } else {
      _monthFromFirst = false;
    }

    if (yearStart == null && firstNonZero != null) {
      yearStart = firstNonZero;
      _yearFromFirst = true;
      debugPrint('使用首次记账作为今年起点: $firstNonZeroDate, 资产=$yearStart');
    } else {
      _yearFromFirst = false;
    }

    _historyPeak = peak;
    _hasMonthBaseline = monthStart != null;
    _hasYearBaseline = yearStart != null;
    _monthChange = monthStart != null ? _totalAsset - monthStart : 0;
    _yearChange = yearStart != null ? _totalAsset - yearStart : 0;

    debugPrint('计算结果: 本月变动=$_monthChange (基准=$monthStart), 今年变动=$_yearChange (基准=$yearStart)');
  }

  /// 刷新投资组合
  Future<void> refreshPortfolio() async {
    try {
      final data = await _api.getPortfolio();
      _portfolio = (data).map((e) => PortfolioItem.fromJson(e)).toList();

      if (_portfolio.isNotEmpty) {
        final codes = _portfolio.map((e) => e.code).toList();
        final pricesData = await _api.getPricesBatch(codes);
        _prices = pricesData.map((key, value) => MapEntry(key, PriceInfo.fromJson(value)));
      }

      _totalInvest = investTotalMV;
      _portfolioLoaded = true;
      notifyListeners();
    } catch (e) {
      debugPrint('刷新投资组合失败: $e');
    }
  }

  /// 加载汇率
  Future<void> loadExchangeRates() async {
    try {
      final rates = await _api.getExchangeRates();
      updateExchangeRates(rates);
    } catch (e) {
      debugPrint('加载汇率失败: $e');
    }
  }

  /// 获取盈亏颜色
  static Color getPnlColor(double value) {
    if (value > 0) return const Color(0xFFEF4444); // 红色（盈利）
    if (value < 0) return const Color(0xFF10B981); // 绿色（亏损）
    return const Color(0xFF94A3B8); // 灰色
  }

  /// 格式化盈亏
  String formatPnl(double value) {
    if (_amountHidden) return '****';
    final sign = value >= 0 ? '+' : '';
    return '$sign${value.toStringAsFixed(2)}';
  }

  /// 格式化盈亏（整数）
  String formatPnlInt(double value) {
    if (_amountHidden) return '****';
    final sign = value > 0 ? '+' : (value < 0 ? '-' : '');
    final absVal = value.abs();
    final text = absVal.toStringAsFixed(0).replaceAllMapped(
      RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'),
      (Match m) => '${m[1]},',
    );
    return '$sign$text';
  }

  /// 格式化百分比
  String formatPct(double value) {
    final sign = value >= 0 ? '+' : '';
    return '$sign${value.toStringAsFixed(2)}%';
  }
}
