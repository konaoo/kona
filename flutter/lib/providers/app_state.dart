import 'dart:async';

import 'package:flutter/material.dart';
import '../config/theme.dart';
import '../services/api_service.dart';
import '../services/biometric_service.dart';
import '../services/cache_service.dart';
import '../services/secure_storage_service.dart';
import '../models/portfolio.dart';
import '../models/asset.dart';
import '../models/asset_action_result.dart';

enum SessionBootState { initializing, authenticated, unauthenticated }

enum AuthLogoutMode { normal, biometricReady }

/// 应用状态管理
class AppState extends ChangeNotifier {
  final ApiService _api = ApiService();
  final CacheService _cache = CacheService();
  final SecureStorageService _secureStorage = SecureStorageService();
  final BiometricService _biometric = BiometricService();
  final Future<String?> Function()? _tokenLoaderOverride;
  final Future<Map<String, dynamic>?> Function()? _profileLoaderOverride;
  final Future<Map<String, dynamic>?> Function(String refreshToken)?
  _refreshSessionOverride;

  AppState({
    Future<String?> Function()? tokenLoader,
    Future<Map<String, dynamic>?> Function()? profileLoader,
    Future<Map<String, dynamic>?> Function(String refreshToken)? refreshLoader,
  }) : _tokenLoaderOverride = tokenLoader,
       _profileLoaderOverride = profileLoader,
       _refreshSessionOverride = refreshLoader {
    _loadTheme();
    _restoreSession();
  }

  // 用户状态
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
  bool _biometricEnabled = false;
  String? _authErrorMessage;
  AuthLogoutMode _logoutMode = AuthLogoutMode.normal;

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
  int _nextTempAssetId = -1;

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

  // 主题模式
  ThemeMode _themeMode = ThemeMode.dark;

  // ============================================================
  // Getters
  // ============================================================

  bool get isLoggedIn => _isLoggedIn;
  SessionBootState get sessionBootState => _sessionBootState;
  bool get isSessionReady => _sessionBootState != SessionBootState.initializing;
  String? get token => _token;
  String? get refreshToken => _refreshToken;
  String? get username => _username;
  String? get userId => _userId;
  int? get userNumber => _userNumber;
  String? get nickname => _nickname;
  String? get avatar => _avatar;
  bool get biometricEnabled => _biometricEnabled;
  String? get authErrorMessage => _authErrorMessage;
  AuthLogoutMode get logoutMode => _logoutMode;

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
  ThemeMode get themeMode => _themeMode;
  bool get isLightTheme => _themeMode == ThemeMode.light;

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

  double getCurrencyRate(String curr) => _rateForCurrency(curr);

  double convertToCny(double amount, String curr) {
    return amount * _rateForCurrency(curr);
  }

  /// 投资币种归一：优先按代码识别市场，无法识别时再回退到传入币种。
  String normalizeInvestmentCurrency({required String code, String? curr}) {
    final raw = code.trim();
    final lower = raw.toLowerCase();
    if (raw.isEmpty) {
      final fallback = curr?.trim().toUpperCase();
      return (fallback == null || fallback.isEmpty) ? 'CNY' : fallback;
    }
    if (lower.startsWith('gb_') || lower.startsWith('ft_')) return 'USD';
    if (lower.endsWith('.hk') || lower.startsWith('hk')) return 'HKD';
    if (lower.startsWith('sh') ||
        lower.startsWith('sz') ||
        lower.startsWith('bj') ||
        lower.startsWith('f_')) {
      return 'CNY';
    }
    if (RegExp(r'^[a-z]+(\.[a-z]+)?$').hasMatch(lower)) return 'USD';
    if (RegExp(r'^\d+$').hasMatch(raw)) return 'CNY';
    final fallback = curr?.trim().toUpperCase();
    return (fallback == null || fallback.isEmpty) ? 'CNY' : fallback;
  }

  /// 过滤后的投资组合
  List<PortfolioItem> get filteredPortfolio {
    if (_currentCategory == 'all') return _portfolio;
    return _portfolio
        .where((item) => item.marketType == _currentCategory)
        .toList();
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
      _cashAssets = (cachedCash['items'] as List)
          .map((e) => Asset.fromJson(e))
          .toList();
    }

    final cachedOther = await _cache.getJson('cache_other_assets');
    if (cachedOther != null && cachedOther['items'] is List) {
      _otherAssets = (cachedOther['items'] as List)
          .map((e) => Asset.fromJson(e))
          .toList();
    }

    final cachedLiabilities = await _cache.getJson('cache_liabilities');
    if (cachedLiabilities != null && cachedLiabilities['items'] is List) {
      _liabilities = (cachedLiabilities['items'] as List)
          .map((e) => Asset.fromJson(e))
          .toList();
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

  Future<void> _loadTheme() async {
    final saved = await _cache.getString('theme_mode');
    if (saved == 'light') {
      _themeMode = ThemeMode.light;
      AppTheme.setMode(ThemeMode.light);
      notifyListeners();
    } else if (saved == 'dark') {
      _themeMode = ThemeMode.dark;
      AppTheme.setMode(ThemeMode.dark);
      notifyListeners();
    }
  }

  Future<void> setThemeMode(ThemeMode mode, {bool save = true}) async {
    _themeMode = mode;
    AppTheme.setMode(mode);
    if (save) {
      await _cache.setString(
        'theme_mode',
        mode == ThemeMode.light ? 'light' : 'dark',
      );
    }
    notifyListeners();
  }

  void toggleTheme() {
    setThemeMode(isLightTheme ? ThemeMode.dark : ThemeMode.light);
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
    await _cache.setJson('cache_history', {'items': history});
    await _cache.setJson('cache_exchange_rates', {'rates': _exchangeRates});
    await _cache.setJson('cache_prices', {
      'items': _prices.map(
        (key, value) => MapEntry(key, {
          'price': value.price,
          'yclose': value.yclose,
          'amt': value.change,
          'chg': value.changePct,
        }),
      ),
    });
  }

  Future<void> _applyAuthResult(Map<String, dynamic> result) async {
    final accessToken = result['access_token']?.toString();
    final refreshToken = result['refresh_token']?.toString();
    final user = (result['user'] is Map<String, dynamic>)
        ? (result['user'] as Map<String, dynamic>)
        : <String, dynamic>{};
    if (accessToken == null || accessToken.isEmpty) {
      throw Exception('缺少 access_token');
    }
    if (refreshToken == null || refreshToken.isEmpty) {
      throw Exception('缺少 refresh_token');
    }

    _isLoggedIn = true;
    _token = accessToken;
    _refreshToken = refreshToken;
    _username = user['username']?.toString();
    _userId = user['id']?.toString() ?? user['user_id']?.toString();
    final userNumberRaw = user['user_number'];
    _userNumber = userNumberRaw is num ? userNumberRaw.toInt() : null;
    _nickname = user['nickname']?.toString();
    _avatar = user['avatar']?.toString();
    _api.setToken(accessToken);
    _sessionBootState = SessionBootState.authenticated;
    _logoutMode = AuthLogoutMode.normal;

    await _secureStorage.setToken(accessToken);
    await _secureStorage.setRefreshToken(refreshToken);
    if (_username != null && _username!.isNotEmpty) {
      await _secureStorage.setUsername(_username!);
    }
    await _secureStorage.clearLogoutMode();
    notifyListeners();
  }

  void clearAuthError() {
    _authErrorMessage = null;
  }

  Future<void> reloadBiometricPreference() async {
    try {
      final enabled = await _secureStorage.isBiometricEnabled();
      if (_biometricEnabled == enabled) return;
      _biometricEnabled = enabled;
      notifyListeners();
    } catch (e) {
      debugPrint('刷新生物识别开关失败: $e');
    }
  }

  String _mapAuthErrorMessage(Object error, {required bool isRegister}) {
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
      } else {
        final invalidCreds = error.statusCode == 401;
        if (invalidCreds) {
          return '用户名/密码错误，请重新再试';
        }
      }
      return raw.isNotEmpty ? raw : (isRegister ? '注册失败，请稍后重试' : '登录失败，请稍后重试');
    }
    return isRegister ? '注册失败，请稍后重试' : '登录失败，请稍后重试';
  }

  /// 用户名密码登录
  Future<bool> login({
    required String username,
    required String password,
  }) async {
    _authErrorMessage = null;
    try {
      final result = await _api.login(username: username, password: password);
      if (result == null) {
        _authErrorMessage = '登录失败，请稍后重试';
        return false;
      }
      await _applyAuthResult(result);
      _authErrorMessage = null;
      return true;
    } catch (e) {
      _authErrorMessage = _mapAuthErrorMessage(e, isRegister: false);
      debugPrint('登录异常: $e');
      return false;
    }
  }

  /// 邀请码注册
  Future<bool> register({
    required String username,
    required String password,
    required String inviteCode,
  }) async {
    _authErrorMessage = null;
    try {
      final result = await _api.register(
        username: username,
        password: password,
        inviteCode: inviteCode,
      );
      if (result == null) {
        _authErrorMessage = '注册失败，请稍后重试';
        return false;
      }
      await _applyAuthResult(result);
      _authErrorMessage = null;
      return true;
    } catch (e) {
      _authErrorMessage = _mapAuthErrorMessage(e, isRegister: true);
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
      await _secureStorage.clearBiometricEnabled();
      _biometricEnabled = false;
      notifyListeners();
      return true;
    } catch (e) {
      debugPrint('修改密码失败: $e');
      return false;
    }
  }

  Future<bool> setBiometricEnabled(bool enabled) async {
    final previous = _biometricEnabled;
    _biometricEnabled = enabled;
    notifyListeners();
    if (enabled) {
      final canUse = await _biometric.canUseBiometrics();
      if (!canUse) {
        _biometricEnabled = previous;
        notifyListeners();
        return false;
      }
    }
    await _secureStorage.setBiometricEnabled(enabled);
    debugPrint('Biometric switch updated: enabled=$_biometricEnabled');
    return true;
  }

  Future<bool> tryBiometricLogin() async {
    if (!_biometricEnabled) {
      debugPrint('Biometric login blocked: biometric switch disabled');
      return false;
    }
    if (!await _biometric.canUseBiometrics()) {
      debugPrint('Biometric login failed: device biometrics unavailable');
      return false;
    }
    var refreshToken = _refreshToken;
    if (refreshToken == null || refreshToken.isEmpty) {
      try {
        refreshToken = await _secureStorage.getRefreshToken();
      } catch (_) {
        debugPrint('Biometric login failed: unable to read refresh token');
        return false;
      }
    }
    if (refreshToken == null || refreshToken.isEmpty) {
      debugPrint('Biometric login failed: refresh token missing');
      return false;
    }
    final ok = await _biometric.authenticate();
    if (!ok) {
      debugPrint('Biometric login cancelled/failed in local auth');
      return false;
    }
    try {
      final result = _refreshSessionOverride != null
          ? await _refreshSessionOverride(refreshToken)
          : await _api.refreshSession(refreshToken: refreshToken);
      if (result == null) return false;
      await _applyAuthResult(result);
      debugPrint('Biometric login success');
      return true;
    } catch (e) {
      debugPrint('Biometric login refresh failed: $e');
      return false;
    }
  }

  Future<bool> fetchProfile() async {
    final profile = await _api.getProfile();
    if (profile != null) {
      _username = profile['username']?.toString() ?? _username;
      _nickname = profile['nickname'];
      _avatar = profile['avatar'];
      notifyListeners();
      return true;
    }
    return false;
  }

  /// 更新用户资料
  Future<bool> updateProfile({String? nickname, String? avatar}) async {
    final result = await _api.updateProfile(nickname: nickname, avatar: avatar);
    if (result != null) {
      _username = result['username']?.toString() ?? _username;
      _nickname = result['nickname'];
      _avatar = result['avatar'];
      notifyListeners();
      return true;
    }
    return false;
  }

  /// 设置登录状态
  Future<void> setLoggedIn({
    required String token,
    required String refreshToken,
    required String username,
    required String userId,
    int? userNumber,
    String? nickname,
    String? avatar,
  }) async {
    _isLoggedIn = true;
    _token = token;
    _refreshToken = refreshToken;
    _username = username;
    _userId = userId;
    _userNumber = userNumber;
    _nickname = nickname;
    _avatar = avatar;
    _api.setToken(token);
    _sessionBootState = SessionBootState.authenticated;
    _logoutMode = AuthLogoutMode.normal;
    await _secureStorage.setToken(token);
    await _secureStorage.setRefreshToken(refreshToken);
    await _secureStorage.setUsername(username);
    await _secureStorage.clearLogoutMode();
    notifyListeners();
  }

  /// 退出登录
  void logout() {
    final currentRefreshToken = _refreshToken;
    final preserveBiometricSession =
        _biometricEnabled &&
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
    _isLoggedIn = false;
    _sessionBootState = SessionBootState.unauthenticated;
    _logoutMode = preserveBiometricSession
        ? AuthLogoutMode.biometricReady
        : AuthLogoutMode.normal;
    _token = null;
    if (!preserveBiometricSession) {
      _refreshToken = null;
      _username = null;
    }
    _userId = null;
    _userNumber = null;
    _nickname = null;
    _avatar = null;
    _api.clearToken();
    _portfolio = [];
    _prices = {};
    _cashAssets = [];
    _otherAssets = [];
    _liabilities = [];
    _portfolioLoaded = false;
    if (preserveBiometricSession) {
      unawaited(() async {
        await _secureStorage.clearToken();
        await _secureStorage.setLogoutMode('biometric_ready');
      }());
    } else {
      unawaited(() async {
        await _secureStorage.clearAllAuth();
        await _secureStorage.setLogoutMode('normal');
      }());
    }
    notifyListeners();
  }

  Future<void> _restoreSession() async {
    if (_isSessionChecking) return;
    _isSessionChecking = true;

    String? token;
    String? refreshToken;
    String? username;
    String? logoutModeRaw;
    try {
      token = _tokenLoaderOverride != null
          ? await _tokenLoaderOverride()
          : await _secureStorage.getToken();
      refreshToken = await _secureStorage.getRefreshToken();
      username = await _secureStorage.getUsername();
      _biometricEnabled = await _secureStorage.isBiometricEnabled();
      logoutModeRaw = await _secureStorage.getLogoutMode();
    } catch (e) {
      debugPrint('读取 token 失败，跳过自动登录: $e');
      _sessionBootState = SessionBootState.unauthenticated;
      _isSessionChecking = false;
      notifyListeners();
      return;
    }

    _logoutMode = _parseLogoutMode(logoutModeRaw);

    if (refreshToken != null && refreshToken.isNotEmpty) {
      _refreshToken = refreshToken;
      _username = username;
    }
    if (_logoutMode == AuthLogoutMode.biometricReady) {
      _isLoggedIn = false;
      _token = null;
      _api.clearToken();
      _sessionBootState = SessionBootState.unauthenticated;
      _isSessionChecking = false;
      notifyListeners();
      return;
    }

    if (refreshToken == null || refreshToken.isEmpty) {
      _sessionBootState = SessionBootState.unauthenticated;
      _isSessionChecking = false;
      notifyListeners();
      return;
    }

    if (token == null || token.isEmpty) {
      try {
        final refreshed = _refreshSessionOverride != null
            ? await _refreshSessionOverride(refreshToken)
            : await _api.refreshSession(refreshToken: refreshToken);
        if (refreshed != null) {
          await _applyAuthResult(refreshed);
          _isSessionChecking = false;
          unawaited(_validateSessionInBackground());
          return;
        }
      } catch (e) {
        debugPrint('启动静默 refresh 失败: $e');
      }
      await _clearSessionAndUnauthenticated();
      _isSessionChecking = false;
      return;
    }

    _token = token;
    _refreshToken = refreshToken;
    _username = username;
    _isLoggedIn = true;
    _api.setToken(token);
    _sessionBootState = SessionBootState.authenticated;
    _isSessionChecking = false;
    notifyListeners();
    unawaited(_validateSessionInBackground());
  }

  Future<void> _validateSessionInBackground() async {
    Map<String, dynamic>? profile = _profileLoaderOverride != null
        ? await _profileLoaderOverride()
        : await _api.getProfile();
    if (profile == null && _refreshToken != null && _refreshToken!.isNotEmpty) {
      try {
        final refreshed = _refreshSessionOverride != null
            ? await _refreshSessionOverride(_refreshToken!)
            : await _api.refreshSession(refreshToken: _refreshToken!);
        if (refreshed != null) {
          await _applyAuthResult(refreshed);
          profile = refreshed['user'] is Map<String, dynamic>
              ? refreshed['user'] as Map<String, dynamic>
              : await _api.getProfile();
        }
      } catch (_) {}
    }
    if (profile == null) {
      await _clearSessionAndUnauthenticated();
      return;
    }

    _username = profile['username']?.toString() ?? _username;
    _userId = profile['id']?.toString() ?? profile['user_id']?.toString();
    final userNumberRaw = profile['user_number'];
    if (userNumberRaw is num) {
      _userNumber = userNumberRaw.toInt();
    } else {
      _userNumber = null;
    }
    _nickname = profile['nickname']?.toString();
    _avatar = profile['avatar']?.toString();
    _isLoggedIn = true;
    _sessionBootState = SessionBootState.authenticated;
    notifyListeners();
  }

  Future<void> _clearSessionAndUnauthenticated() async {
    _isLoggedIn = false;
    _token = null;
    _refreshToken = null;
    _username = null;
    _userId = null;
    _userNumber = null;
    _nickname = null;
    _avatar = null;
    _logoutMode = AuthLogoutMode.normal;
    _sessionBootState = SessionBootState.unauthenticated;
    _api.clearToken();
    notifyListeners();
    try {
      await _secureStorage.clearAllAuth();
      await _secureStorage.clearLogoutMode();
    } catch (e) {
      debugPrint('清理失效 token 失败: $e');
    }
  }

  AuthLogoutMode _parseLogoutMode(String? raw) {
    if (raw == 'biometric_ready') {
      return AuthLogoutMode.biometricReady;
    }
    return AuthLogoutMode.normal;
  }

  /// 切换金额隐藏
  void toggleAmountHidden() {
    _amountHidden = !_amountHidden;
    notifyListeners();
  }

  /// 格式化金额（支持隐藏）
  String formatAmount(double value, {String prefix = '¥'}) {
    if (_amountHidden) return '****';
    return '$prefix${value.toStringAsFixed(0).replaceAllMapped(RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'), (Match m) => '${m[1]},')}';
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
        _api.getAnalysisOverview(period: 'all'),
      ]);

      _cashAssets = (results[0] as List).map((e) => Asset.fromJson(e)).toList();
      _otherAssets = (results[1] as List)
          .map((e) => Asset.fromJson(e))
          .toList();
      _liabilities = (results[2] as List)
          .map((e) => Asset.fromJson(e))
          .toList();
      _portfolio = (results[3] as List)
          .map((e) => PortfolioItem.fromJson(e))
          .toList();

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
              debugPrint(
                '成功解析价格: $originalCode (API: $apiCode) = ${pricesData[apiCode]}',
              );
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
      applyOverviewMilestones(results[5] as Map<String, dynamic>?);

      await saveHomeCache(history);

      _portfolioLoaded = true;
      notifyListeners();
    } catch (e) {
      debugPrint('刷新首页数据失败: $e');
    }
  }

  /// 用分析概览覆盖首页里程碑（月/年改为收益口径）。
  /// 若接口数据异常则保留历史差值口径结果（回退行为）。
  void applyOverviewMilestones(Map<String, dynamic>? overview) {
    final data = overview ?? const <String, dynamic>{};
    final month = data['month'];
    final year = data['year'];
    double? _extractPnl(dynamic node) {
      if (node is! Map) return null;
      final raw = node['pnl'];
      if (raw is num) return raw.toDouble();
      if (raw is String) return double.tryParse(raw.trim());
      return null;
    }

    final monthPnl = _extractPnl(month);
    final yearPnl = _extractPnl(year);
    debugPrint('分析概览覆盖: monthPnl=$monthPnl, yearPnl=$yearPnl, raw=$data');
    if (monthPnl != null) _monthChange = monthPnl;
    if (yearPnl != null) _yearChange = yearPnl;
  }

  /// 仅刷新行情价格（用于定时更新今日盈亏/现价）
  Future<void> refreshPricesOnly() async {
    try {
      if (_portfolio.isEmpty) return;

      final codes = _portfolio.map((e) => e.code).toList();
      final priceApiCodes = codes.map((code) {
        if (code.startsWith('gb_')) {
          return code.substring(3);
        }
        return code;
      }).toList();

      final pricesData = await _api.getPricesBatch(priceApiCodes);
      _prices = {};
      for (int i = 0; i < codes.length; i++) {
        final originalCode = codes[i];
        final apiCode = priceApiCodes[i];
        if (pricesData.containsKey(apiCode)) {
          _prices[originalCode] = PriceInfo.fromJson(pricesData[apiCode]);
        }
      }

      _totalInvest = investTotalMV;
      _totalAsset = _totalCash + _totalInvest + _totalOther - _totalLiability;
      notifyListeners();
    } catch (e) {
      debugPrint('刷新行情价格失败: $e');
    }
  }

  /// 刷新所有核心数据（用于启动与下拉刷新）
  Future<void> refreshAll() async {
    await Future.wait([refreshHomeData(), loadExchangeRates()]);
  }

  _AssetSnapshot _captureAssetSnapshot() {
    return _AssetSnapshot(
      cashAssets: List<Asset>.from(_cashAssets),
      otherAssets: List<Asset>.from(_otherAssets),
      liabilities: List<Asset>.from(_liabilities),
    );
  }

  void _restoreAssetSnapshot(_AssetSnapshot snapshot) {
    _cashAssets = snapshot.cashAssets;
    _otherAssets = snapshot.otherAssets;
    _liabilities = snapshot.liabilities;
    _recalculateAssetTotals();
  }

  void _recalculateAssetTotals() {
    _totalCash = _cashAssets.fold(0, (sum, item) => sum + item.amount);
    _totalOther = _otherAssets.fold(0, (sum, item) => sum + item.amount);
    _totalLiability = _liabilities.fold(0, (sum, item) => sum + item.amount);
    _totalAsset = _totalCash + _totalInvest + _totalOther - _totalLiability;
    notifyListeners();
  }

  bool _optimisticAddAsset({
    required String type,
    required String name,
    required double amount,
  }) {
    switch (type) {
      case 'cash':
        final tempAsset = Asset(
          id: _nextTempAssetId--,
          name: name,
          amount: amount,
        );
        _cashAssets = [..._cashAssets, tempAsset];
        return true;
      case 'other':
        final tempAsset = Asset(
          id: _nextTempAssetId--,
          name: name,
          amount: amount,
        );
        _otherAssets = [..._otherAssets, tempAsset];
        return true;
      case 'liability':
        final tempAsset = Asset(
          id: _nextTempAssetId--,
          name: name,
          amount: amount,
        );
        _liabilities = [..._liabilities, tempAsset];
        return true;
      default:
        return false;
    }
  }

  bool _optimisticDeleteAsset({required String type, required int id}) {
    switch (type) {
      case 'cash':
        final before = _cashAssets.length;
        _cashAssets = _cashAssets.where((item) => item.id != id).toList();
        return _cashAssets.length != before;
      case 'other':
        final before = _otherAssets.length;
        _otherAssets = _otherAssets.where((item) => item.id != id).toList();
        return _otherAssets.length != before;
      case 'liability':
        final before = _liabilities.length;
        _liabilities = _liabilities.where((item) => item.id != id).toList();
        return _liabilities.length != before;
      default:
        return false;
    }
  }

  bool _optimisticUpdateAsset({
    required String type,
    required int id,
    required String name,
    required double amount,
  }) {
    bool updated = false;
    List<Asset> updateList(List<Asset> source) {
      return source.map((asset) {
        if (asset.id != id) return asset;
        updated = true;
        return Asset(
          id: asset.id,
          name: name,
          amount: amount,
          curr: asset.curr,
        );
      }).toList();
    }

    switch (type) {
      case 'cash':
        _cashAssets = updateList(_cashAssets);
        return updated;
      case 'other':
        _otherAssets = updateList(_otherAssets);
        return updated;
      case 'liability':
        _liabilities = updateList(_liabilities);
        return updated;
      default:
        return false;
    }
  }

  /// 添加资产（现金/其他/负债）
  Future<AssetActionResult> addAsset({
    required String type,
    required String name,
    required double amount,
    bool awaitRefresh = true,
  }) async {
    final snapshot = _captureAssetSnapshot();
    final changed = _optimisticAddAsset(type: type, name: name, amount: amount);
    if (!changed) return const AssetActionResult.failure('不支持的资产类型');
    _recalculateAssetTotals();

    final result = switch (type) {
      'cash' => await _api.addCashAsset(name, amount),
      'other' => await _api.addOtherAsset(name, amount),
      'liability' => await _api.addLiability(name, amount),
      _ => const AssetActionResult.failure('不支持的资产类型'),
    };
    if (!result.ok) {
      _restoreAssetSnapshot(snapshot);
      return result;
    }
    if (awaitRefresh) {
      await refreshHomeData();
    } else {
      unawaited(refreshHomeData());
    }
    return const AssetActionResult.success();
  }

  /// 删除资产（现金/其他/负债）
  Future<AssetActionResult> deleteAsset({
    required String type,
    required int id,
    bool awaitRefresh = true,
  }) async {
    if (id <= 0) {
      return const AssetActionResult.failure('操作失败，请稍后重试');
    }
    final snapshot = _captureAssetSnapshot();
    final changed = _optimisticDeleteAsset(type: type, id: id);
    if (changed) {
      _recalculateAssetTotals();
    } else if (type != 'cash' && type != 'other' && type != 'liability') {
      return const AssetActionResult.failure('不支持的资产类型');
    }

    AssetActionResult result;
    if (type == 'cash') {
      result = await _api.deleteCashAsset(id);
    } else if (type == 'other') {
      result = await _api.deleteOtherAsset(id);
    } else if (type == 'liability') {
      result = await _api.deleteLiability(id);
    } else {
      return const AssetActionResult.failure('不支持的资产类型');
    }
    if (!result.ok) {
      if (changed) {
        _restoreAssetSnapshot(snapshot);
      }
      return result;
    }
    if (awaitRefresh) {
      await refreshHomeData();
    } else {
      unawaited(refreshHomeData());
    }
    return const AssetActionResult.success();
  }

  /// 更新资产（现金/其他/负债）
  Future<AssetActionResult> updateAsset({
    required String type,
    required int id,
    required String name,
    required double amount,
    bool awaitRefresh = true,
  }) async {
    if (id <= 0) {
      return const AssetActionResult.failure('操作失败，请稍后重试');
    }
    final snapshot = _captureAssetSnapshot();
    final changed = _optimisticUpdateAsset(
      type: type,
      id: id,
      name: name,
      amount: amount,
    );
    if (changed) {
      _recalculateAssetTotals();
    } else if (type != 'cash' && type != 'other' && type != 'liability') {
      return const AssetActionResult.failure('不支持的资产类型');
    }

    AssetActionResult result;
    if (type == 'cash') {
      result = await _api.updateCashAsset(id, name, amount);
    } else if (type == 'other') {
      result = await _api.updateOtherAsset(id, name, amount);
    } else if (type == 'liability') {
      result = await _api.updateLiability(id, name, amount);
    } else {
      return const AssetActionResult.failure('不支持的资产类型');
    }
    if (!result.ok) {
      if (changed) {
        _restoreAssetSnapshot(snapshot);
      }
      return result;
    }
    if (awaitRefresh) {
      await refreshHomeData();
    } else {
      unawaited(refreshHomeData());
    }
    return const AssetActionResult.success();
  }

  _PortfolioSnapshot _capturePortfolioSnapshot() {
    return _PortfolioSnapshot(portfolio: List<PortfolioItem>.from(_portfolio));
  }

  void _restorePortfolioSnapshot(_PortfolioSnapshot snapshot) {
    _portfolio = snapshot.portfolio;
    _recalculatePortfolioTotals();
  }

  void _recalculatePortfolioTotals() {
    _totalInvest = investTotalMV;
    _totalAsset = _totalCash + _totalInvest + _totalOther - _totalLiability;
    notifyListeners();
  }

  int _portfolioIndexByCode(String code) {
    return _portfolio.indexWhere((item) => item.code == code);
  }

  bool _optimisticAddInvestment({
    required String code,
    required String name,
    required double price,
    required double qty,
    String? curr,
    String? assetType,
  }) {
    final normalizedCurr = normalizeInvestmentCurrency(code: code, curr: curr);
    final next = PortfolioItem(
      code: code,
      name: name,
      qty: qty,
      price: price,
      adjustment: 0,
      curr: normalizedCurr,
      assetType: (assetType == null || assetType.isEmpty) ? '' : assetType,
    );
    final index = _portfolioIndexByCode(code);
    if (index >= 0) {
      final updated = List<PortfolioItem>.from(_portfolio);
      updated[index] = next;
      _portfolio = updated;
      return true;
    }
    _portfolio = [..._portfolio, next];
    return true;
  }

  bool _optimisticBuyInvestment({
    required String code,
    required double price,
    required double qty,
  }) {
    final index = _portfolioIndexByCode(code);
    if (index < 0) return false;
    final old = _portfolio[index];
    final newQty = old.qty + qty;
    if (newQty <= 0) return false;
    final newPrice = (old.qty * old.price + qty * price) / newQty;
    final updated = List<PortfolioItem>.from(_portfolio);
    updated[index] = PortfolioItem(
      id: old.id,
      code: old.code,
      name: old.name,
      qty: newQty,
      price: newPrice,
      adjustment: old.adjustment,
      curr: old.curr,
      assetType: old.assetType,
    );
    _portfolio = updated;
    return true;
  }

  bool _optimisticSellInvestment({
    required String code,
    required double price,
    required double qty,
  }) {
    final index = _portfolioIndexByCode(code);
    if (index < 0) return false;
    final old = _portfolio[index];
    if (qty > old.qty + 1e-6) return false;
    final pnl = (price - old.price) * qty;
    final newQty = old.qty - qty;
    final updated = List<PortfolioItem>.from(_portfolio);
    if (newQty < 0.001) {
      updated.removeAt(index);
    } else {
      updated[index] = PortfolioItem(
        id: old.id,
        code: old.code,
        name: old.name,
        qty: newQty,
        price: old.price,
        adjustment: old.adjustment + pnl,
        curr: old.curr,
        assetType: old.assetType,
      );
    }
    _portfolio = updated;
    return true;
  }

  bool _optimisticModifyInvestment({
    required String code,
    required double qty,
    required double price,
    required double adjustment,
  }) {
    final index = _portfolioIndexByCode(code);
    if (index < 0) return false;
    final old = _portfolio[index];
    final updated = List<PortfolioItem>.from(_portfolio);
    updated[index] = PortfolioItem(
      id: old.id,
      code: old.code,
      name: old.name,
      qty: qty,
      price: price,
      adjustment: adjustment,
      curr: old.curr,
      assetType: old.assetType,
    );
    _portfolio = updated;
    return true;
  }

  bool _optimisticDeleteInvestment({required String code}) {
    final before = _portfolio.length;
    _portfolio = _portfolio.where((item) => item.code != code).toList();
    return _portfolio.length != before;
  }

  bool _optimisticAdjustCashAssetAmount({
    required int cashAssetId,
    required double deltaAmount,
  }) {
    bool updated = false;
    _cashAssets = _cashAssets.map((asset) {
      if (asset.id != cashAssetId) return asset;
      final nextAmount = asset.amount + deltaAmount;
      if (nextAmount < -1e-6) {
        return asset;
      }
      updated = true;
      return Asset(
        id: asset.id,
        name: asset.name,
        amount: nextAmount < 0 ? 0 : nextAmount,
        curr: asset.curr,
      );
    }).toList();
    return updated;
  }

  double _convertAmountByCurrency({
    required double amount,
    required String fromCurr,
    required String toCurr,
  }) {
    final fromRate = _rateForCurrency(fromCurr);
    final toRate = _rateForCurrency(toCurr);
    if (toRate <= 0) return amount * fromRate;
    return amount * fromRate / toRate;
  }

  AssetActionResult _extractUndoInfo(AssetActionResult result) {
    if (!result.ok) return result;
    final data = result.data;
    if (data == null) return result;
    final token = data['undo_token']?.toString();
    final expire = data['undo_expire_at']?.toString();
    if (token == null || token.isEmpty || expire == null || expire.isEmpty) {
      return result;
    }
    return AssetActionResult(
      ok: true,
      data: {
        ...data,
        'undo_token': token,
        'undo_expire_at': expire,
      },
    );
  }

  Future<AssetActionResult> _legacyBuyWithCashFallback({
    required String code,
    required String name,
    required double price,
    required double qty,
    required Asset cashAsset,
    required double cashDeductAmount,
  }) async {
    final buyResult = await _api.buyPortfolioAsset(code, price, qty);
    if (!buyResult.ok) return buyResult;

    final cashId = cashAsset.id;
    if (cashId == null || cashId <= 0) {
      // 尽力回滚买入，避免现金未扣减造成数据偏差。
      await _api.sellPortfolioAsset(code, price, qty);
      return const AssetActionResult.failure('现金账户无效，请稍后重试');
    }

    final updateResult = await _api.updateCashAsset(
      cashId,
      cashAsset.name,
      cashAsset.amount - cashDeductAmount,
      curr: cashAsset.curr,
    );
    if (updateResult.ok) {
      return const AssetActionResult.success(
        data: {'code': 'LEGACY_BUY_WITH_CASH'},
      );
    }

    final rollbackSell = await _api.sellPortfolioAsset(code, price, qty);
    if (!rollbackSell.ok) {
      return const AssetActionResult.failure('现金扣减失败，且买入回滚失败，请手动核对账户和持仓');
    }
    return AssetActionResult.failure(updateResult.message ?? '现金扣减失败，已回滚买入');
  }

  Future<AssetActionResult> _legacySellToCashFallback({
    required String code,
    required double price,
    required double qty,
    required Asset cashAsset,
    required double cashCreditAmount,
  }) async {
    final cashId = cashAsset.id;
    if (cashId == null || cashId <= 0) {
      return const AssetActionResult.failure('现金账户无效，请稍后重试');
    }

    final updateCashResult = await _api.updateCashAsset(
      cashId,
      cashAsset.name,
      cashAsset.amount + cashCreditAmount,
      curr: cashAsset.curr,
    );
    if (!updateCashResult.ok) {
      return updateCashResult;
    }

    final sellResult = await _api.sellPortfolioAsset(code, price, qty);
    if (sellResult.ok) {
      return const AssetActionResult.success(
        data: {'code': 'LEGACY_SELL_TO_CASH'},
      );
    }

    final rollbackCash = await _api.updateCashAsset(
      cashId,
      cashAsset.name,
      cashAsset.amount,
      curr: cashAsset.curr,
    );
    if (!rollbackCash.ok) {
      return const AssetActionResult.failure('卖出失败，且回款回滚失败，请手动核对现金账户');
    }
    return sellResult;
  }

  /// 搜索股票/基金
  Future<List<dynamic>> searchStocks(String query) async {
    return await _api.searchStocks(query);
  }

  /// 添加投资资产
  Future<AssetActionResult> addInvestment({
    required String code,
    required String name,
    required double price,
    required double qty,
    String? curr,
    String? assetType,
    bool awaitRefresh = true,
  }) async {
    final normalizedCurr = normalizeInvestmentCurrency(code: code, curr: curr);
    final snapshot = _capturePortfolioSnapshot();
    final changed = _optimisticAddInvestment(
      code: code,
      name: name,
      price: price,
      qty: qty,
      curr: normalizedCurr,
      assetType: assetType,
    );
    if (!changed) return const AssetActionResult.failure('添加失败，请稍后重试');
    _recalculatePortfolioTotals();

    final result = await _api.addPortfolioAsset(
      code,
      name,
      price,
      qty,
      curr: normalizedCurr,
      assetType: assetType,
    );
    if (!result.ok) {
      _restorePortfolioSnapshot(snapshot);
      return result;
    }
    if (awaitRefresh) {
      await refreshHomeData();
    } else {
      unawaited(refreshHomeData());
    }
    return result;
  }

  /// 从指定现金账户买入（同一事务扣现金 + 加仓）
  Future<AssetActionResult> buyInvestmentWithCash({
    required String code,
    required String name,
    required double price,
    required double qty,
    required int cashAssetId,
    String? curr,
    String? assetType,
    bool awaitRefresh = true,
  }) async {
    if (price <= 0 || qty <= 0) {
      return const AssetActionResult.failure('请输入有效价格和数量');
    }
    if (cashAssetId <= 0) {
      return const AssetActionResult.failure('请选择资金来源账户');
    }

    final cashIndex = _cashAssets.indexWhere((asset) => asset.id == cashAssetId);
    if (cashIndex < 0) {
      return const AssetActionResult.failure('未找到资金来源账户');
    }
    final cashAsset = _cashAssets[cashIndex];
    final normalizedCurr = normalizeInvestmentCurrency(code: code, curr: curr);
    final investAmount = price * qty;
    final cashDeductAmount = _convertAmountByCurrency(
      amount: investAmount,
      fromCurr: normalizedCurr,
      toCurr: cashAsset.curr,
    );
    if (cashDeductAmount <= 0) {
      return const AssetActionResult.failure('扣款金额计算失败');
    }
    if (cashAsset.amount + 1e-6 < cashDeductAmount) {
      return AssetActionResult.failure(
        '账户余额不足：${cashAsset.name}',
        data: {
          'available': cashAsset.amount,
          'required': cashDeductAmount,
          'cash_curr': cashAsset.curr,
        },
      );
    }

    final assetSnapshot = _captureAssetSnapshot();
    final portfolioSnapshot = _capturePortfolioSnapshot();
    final hadHolding = _portfolioIndexByCode(code) >= 0;
    final portfolioChanged = hadHolding
        ? _optimisticBuyInvestment(code: code, price: price, qty: qty)
        : _optimisticAddInvestment(
            code: code,
            name: name,
            price: price,
            qty: qty,
            curr: normalizedCurr,
            assetType: assetType,
          );
    final cashChanged = _optimisticAdjustCashAssetAmount(
      cashAssetId: cashAssetId,
      deltaAmount: -cashDeductAmount,
    );
    if (!portfolioChanged || !cashChanged) {
      _restoreAssetSnapshot(assetSnapshot);
      _restorePortfolioSnapshot(portfolioSnapshot);
      return const AssetActionResult.failure('买入失败，请稍后重试');
    }
    _totalCash = _cashAssets.fold(0, (sum, item) => sum + item.amount);
    _recalculatePortfolioTotals();

    final result = await _api.buyPortfolioAssetWithCash(
      code,
      name,
      price,
      qty,
      cashAssetId: cashAssetId,
      curr: normalizedCurr,
      assetType: assetType,
    );
    if (!result.ok) {
      final statusCode = result.data?['status_code'];
      if (statusCode == 404) {
        final fallbackResult = await _legacyBuyWithCashFallback(
          code: code,
          name: name,
          price: price,
          qty: qty,
          cashAsset: cashAsset,
          cashDeductAmount: cashDeductAmount,
        );
        if (!fallbackResult.ok) {
          _restoreAssetSnapshot(assetSnapshot);
          _restorePortfolioSnapshot(portfolioSnapshot);
          return fallbackResult;
        }
        if (awaitRefresh) {
          await refreshHomeData();
        } else {
          unawaited(refreshHomeData());
        }
        return fallbackResult;
      }
      _restoreAssetSnapshot(assetSnapshot);
      _restorePortfolioSnapshot(portfolioSnapshot);
      return result;
    }
    if (awaitRefresh) {
      await refreshHomeData();
    } else {
      unawaited(refreshHomeData());
    }
    return _extractUndoInfo(result);
  }

  /// 卖出到指定现金账户（同一事务减仓 + 回款）
  Future<AssetActionResult> sellInvestmentToCash({
    required String code,
    required double price,
    required double qty,
    required int cashAssetId,
    bool awaitRefresh = true,
  }) async {
    final index = _portfolioIndexByCode(code);
    if (index < 0) return const AssetActionResult.failure('未找到该持仓');
    if (qty <= 0 || price <= 0) {
      return const AssetActionResult.failure('请输入有效价格和数量');
    }
    final current = _portfolio[index];
    if (qty > current.qty + 1e-6) {
      return const AssetActionResult.failure('卖出数量超过持仓数量');
    }
    if (cashAssetId <= 0) {
      return const AssetActionResult.failure('请选择回款账户');
    }
    final cashIndex = _cashAssets.indexWhere((asset) => asset.id == cashAssetId);
    if (cashIndex < 0) {
      return const AssetActionResult.failure('未找到回款账户');
    }
    final cashAsset = _cashAssets[cashIndex];
    final sellAmount = price * qty;
    final cashCreditAmount = _convertAmountByCurrency(
      amount: sellAmount,
      fromCurr: current.curr,
      toCurr: cashAsset.curr,
    );
    if (cashCreditAmount <= 0) {
      return const AssetActionResult.failure('回款金额计算失败');
    }

    final assetSnapshot = _captureAssetSnapshot();
    final portfolioSnapshot = _capturePortfolioSnapshot();
    final portfolioChanged = _optimisticSellInvestment(
      code: code,
      price: price,
      qty: qty,
    );
    final cashChanged = _optimisticAdjustCashAssetAmount(
      cashAssetId: cashAssetId,
      deltaAmount: cashCreditAmount,
    );
    if (!portfolioChanged || !cashChanged) {
      _restoreAssetSnapshot(assetSnapshot);
      _restorePortfolioSnapshot(portfolioSnapshot);
      return const AssetActionResult.failure('卖出失败，请稍后重试');
    }
    _totalCash = _cashAssets.fold(0, (sum, item) => sum + item.amount);
    _recalculatePortfolioTotals();

    final result = await _api.sellPortfolioAssetToCash(
      code,
      price,
      qty,
      cashAssetId: cashAssetId,
    );
    if (!result.ok) {
      final statusCode = result.data?['status_code'];
      if (statusCode == 404) {
        final fallbackResult = await _legacySellToCashFallback(
          code: code,
          price: price,
          qty: qty,
          cashAsset: cashAsset,
          cashCreditAmount: cashCreditAmount,
        );
        if (!fallbackResult.ok) {
          _restoreAssetSnapshot(assetSnapshot);
          _restorePortfolioSnapshot(portfolioSnapshot);
          return fallbackResult;
        }
        if (awaitRefresh) {
          await refreshHomeData();
        } else {
          unawaited(refreshHomeData());
        }
        return fallbackResult;
      }
      _restoreAssetSnapshot(assetSnapshot);
      _restorePortfolioSnapshot(portfolioSnapshot);
      return result;
    }

    if (awaitRefresh) {
      await refreshHomeData();
    } else {
      unawaited(refreshHomeData());
    }
    return _extractUndoInfo(result);
  }

  /// 买入（加仓）
  Future<AssetActionResult> buyInvestment({
    required String code,
    required double price,
    required double qty,
    bool awaitRefresh = true,
  }) async {
    if (_portfolioIndexByCode(code) < 0) {
      return const AssetActionResult.failure('未找到该持仓');
    }
    final snapshot = _capturePortfolioSnapshot();
    final changed = _optimisticBuyInvestment(
      code: code,
      price: price,
      qty: qty,
    );
    if (!changed) return const AssetActionResult.failure('买入失败，请稍后重试');
    _recalculatePortfolioTotals();

    final result = await _api.buyPortfolioAsset(code, price, qty);
    if (!result.ok) {
      _restorePortfolioSnapshot(snapshot);
      return result;
    }
    if (awaitRefresh) {
      await refreshHomeData();
    } else {
      unawaited(refreshHomeData());
    }
    return _extractUndoInfo(result);
  }

  /// 卖出（减仓）
  Future<AssetActionResult> sellInvestment({
    required String code,
    required double price,
    required double qty,
    bool awaitRefresh = true,
  }) async {
    final index = _portfolioIndexByCode(code);
    if (index < 0) return const AssetActionResult.failure('未找到该持仓');
    if (qty > _portfolio[index].qty + 1e-6) {
      return const AssetActionResult.failure('卖出数量超过持仓数量');
    }
    final snapshot = _capturePortfolioSnapshot();
    final changed = _optimisticSellInvestment(
      code: code,
      price: price,
      qty: qty,
    );
    if (!changed) return const AssetActionResult.failure('卖出失败，请稍后重试');
    _recalculatePortfolioTotals();

    final result = await _api.sellPortfolioAsset(code, price, qty);
    if (!result.ok) {
      _restorePortfolioSnapshot(snapshot);
      return result;
    }
    if (awaitRefresh) {
      await refreshHomeData();
    } else {
      unawaited(refreshHomeData());
    }
    return _extractUndoInfo(result);
  }

  /// 手动调整（数量/成本/调整）
  Future<AssetActionResult> modifyInvestment({
    required String code,
    required double qty,
    required double price,
    required double adjustment,
    bool awaitRefresh = true,
  }) async {
    if (_portfolioIndexByCode(code) < 0) {
      return const AssetActionResult.failure('未找到该持仓');
    }
    final snapshot = _capturePortfolioSnapshot();
    final changed = _optimisticModifyInvestment(
      code: code,
      qty: qty,
      price: price,
      adjustment: adjustment,
    );
    if (!changed) return const AssetActionResult.failure('调整失败，请稍后重试');
    _recalculatePortfolioTotals();

    final result = await _api.modifyPortfolioAsset(
      code,
      qty,
      price,
      adjustment,
    );
    if (!result.ok) {
      _restorePortfolioSnapshot(snapshot);
      return result;
    }
    if (awaitRefresh) {
      await refreshHomeData();
    } else {
      unawaited(refreshHomeData());
    }
    return _extractUndoInfo(result);
  }

  /// 撤销投资写操作（买入/卖出/调整）
  Future<AssetActionResult> undoInvestmentOperation(String undoToken) async {
    if (undoToken.trim().isEmpty) {
      return const AssetActionResult.failure('撤销凭证无效');
    }
    final result = await _api.undoPortfolioOperation(undoToken.trim());
    if (!result.ok) {
      return result;
    }
    unawaited(refreshHomeData());
    return result;
  }

  /// 删除投资资产
  Future<AssetActionResult> deleteInvestment({
    required String code,
    bool corrective = false,
    bool awaitRefresh = true,
  }) async {
    final snapshot = _capturePortfolioSnapshot();
    final changed = _optimisticDeleteInvestment(code: code);
    if (!changed) return const AssetActionResult.failure('未找到该持仓');
    _recalculatePortfolioTotals();

    var result = corrective
        ? await _api.deletePortfolioAssetCorrective(code)
        : await _api.deletePortfolioAsset(code);
    if (!result.ok && corrective) {
      // 纠错删除失败时回退到普通删除，避免列表回弹。
      result = await _api.deletePortfolioAsset(code);
    }
    if (!result.ok) {
      _restorePortfolioSnapshot(snapshot);
      return result;
    }
    if (awaitRefresh) {
      await refreshHomeData();
    } else {
      unawaited(refreshHomeData());
    }
    return const AssetActionResult.success();
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
      history.map((e) => e as Map<String, dynamic>),
    );
    sortedHistory.sort((a, b) => a['date'].compareTo(b['date']));

    final latestSnapshotAsset = sortedHistory.last['total_asset'] as num;
    final currentSnapshot = latestSnapshotAsset.toDouble();
    debugPrint(
      '历史数据计算: 当前日期=${now.toString().substring(0, 10)}, 快照总资产=$currentSnapshot',
    );
    debugPrint('历史数据条数: ${sortedHistory.length}');
    if (sortedHistory.isNotEmpty) {
      debugPrint(
        '最早记录: ${sortedHistory.first['date']}, 资产=${sortedHistory.first['total_asset']}',
      );
      debugPrint(
        '最新记录: ${sortedHistory.last['date']}, 资产=${sortedHistory.last['total_asset']}',
      );
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
      if (date.year == now.year &&
          date.month == now.month &&
          monthStart == null &&
          totalAsset != 0) {
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
    _monthChange = monthStart != null ? currentSnapshot - monthStart : 0;
    _yearChange = yearStart != null ? currentSnapshot - yearStart : 0;

    debugPrint(
      '计算结果: 本月变动=$_monthChange (基准=$monthStart), 今年变动=$_yearChange (基准=$yearStart)',
    );
  }

  /// 刷新投资组合
  Future<void> refreshPortfolio() async {
    try {
      final data = await _api.getPortfolio();
      _portfolio = (data).map((e) => PortfolioItem.fromJson(e)).toList();

      if (_portfolio.isNotEmpty) {
        final codes = _portfolio.map((e) => e.code).toList();
        final pricesData = await _api.getPricesBatch(codes);
        _prices = pricesData.map(
          (key, value) => MapEntry(key, PriceInfo.fromJson(value)),
        );
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
    final text = absVal
        .toStringAsFixed(0)
        .replaceAllMapped(
          RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'),
          (Match m) => '${m[1]},',
        );
    return '$sign$text';
  }

  /// 格式化盈亏（整数 + 币种）
  String formatPnlIntWithCurrency(double value, String symbol) {
    if (_amountHidden) return '****';
    final sign = value > 0 ? '+' : (value < 0 ? '-' : '');
    final absVal = value.abs();
    final text = absVal
        .toStringAsFixed(0)
        .replaceAllMapped(
          RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'),
          (Match m) => '${m[1]},',
        );
    return '$sign$symbol$text';
  }

  /// 格式化金额（紧凑：万/亿）
  String formatCompactAmount(
    double value, {
    String prefix = '',
    int decimals = 1,
  }) {
    if (_amountHidden) return '****';
    final absVal = value.abs();
    if (absVal >= 100000000) {
      return '$prefix${(absVal / 100000000).toStringAsFixed(decimals)}亿';
    }
    if (absVal >= 10000) {
      return '$prefix${(absVal / 10000).toStringAsFixed(decimals)}万';
    }
    final text = absVal
        .toStringAsFixed(0)
        .replaceAllMapped(
          RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'),
          (Match m) => '${m[1]},',
        );
    return '$prefix$text';
  }

  /// 格式化盈亏（紧凑：万/亿 + 币种）
  String formatCompactPnlWithCurrency(
    double value,
    String symbol, {
    int decimals = 1,
  }) {
    if (_amountHidden) return '****';
    final sign = value > 0 ? '+' : (value < 0 ? '-' : '');
    final absVal = value.abs();
    if (absVal >= 100000000) {
      return '$sign$symbol${(absVal / 100000000).toStringAsFixed(decimals)}亿';
    }
    if (absVal >= 10000) {
      return '$sign$symbol${(absVal / 10000).toStringAsFixed(decimals)}万';
    }
    final text = absVal
        .toStringAsFixed(0)
        .replaceAllMapped(
          RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'),
          (Match m) => '${m[1]},',
        );
    return '$sign$symbol$text';
  }

  /// 格式化盈亏（人民币，紧凑：万/亿，整数）
  String formatCompactPnlCny(double value) {
    if (_amountHidden) return '****';
    final sign = value > 0 ? '+' : (value < 0 ? '-' : '');
    final absVal = value.abs();
    if (absVal >= 100000000) {
      return '$sign¥${(absVal / 100000000).toStringAsFixed(0)}亿';
    }
    if (absVal >= 10000) {
      return '$sign¥${(absVal / 10000).toStringAsFixed(0)}万';
    }
    final text = absVal
        .toStringAsFixed(0)
        .replaceAllMapped(
          RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'),
          (Match m) => '${m[1]},',
        );
    return '$sign¥$text';
  }

  /// 格式化百分比
  String formatPct(double value) {
    final sign = value >= 0 ? '+' : '';
    return '$sign${value.toStringAsFixed(2)}%';
  }
}

class _AssetSnapshot {
  final List<Asset> cashAssets;
  final List<Asset> otherAssets;
  final List<Asset> liabilities;

  const _AssetSnapshot({
    required this.cashAssets,
    required this.otherAssets,
    required this.liabilities,
  });
}

class _PortfolioSnapshot {
  final List<PortfolioItem> portfolio;

  const _PortfolioSnapshot({required this.portfolio});
}
