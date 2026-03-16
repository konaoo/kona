import 'dart:async';

import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/async_flow_logger.dart';
import '../services/biometric_service.dart';
import '../services/cache_service.dart';
import '../services/portfolio_metrics_service.dart';
import '../services/secure_storage_service.dart';
import '../models/portfolio.dart';
import '../models/asset.dart';
import '../models/asset_action_result.dart';
import 'app_assets_state.dart';
import 'app_auth_state.dart';
import 'app_market_state.dart';
import 'app_overview_state.dart';
import 'app_preferences_state.dart';
import 'app_refresh_state.dart';
import 'app_security_state.dart';
import 'app_session_state.dart';
import 'app_sync_state.dart';
import 'app_trade_state.dart';
import 'generated_sync_contract.dart';
export 'app_security_state.dart' show AuthLogoutMode;
export 'app_auth_state.dart' show SessionBootState;

/// 应用状态管理
class AppState extends ChangeNotifier {
  // 1) 常量与依赖
  static const Duration _staticDataTtl = Duration(minutes: 5);
  static const Duration _historyDataTtl = Duration(minutes: 10);
  static const Duration _ratesDataTtl = Duration(minutes: 10);
  static const Duration _marketStatusRefreshBudget = Duration(
    milliseconds: 350,
  );
  static const Duration _syncVersionTtl = Duration(days: 365);
  static const Duration _userProfileTtl = Duration(days: 30);
  static const String _userProfileDomain = 'user_profile';
  final ApiService _api;
  final AppAssetsState _assetsState;
  final AppAuthState _authState;
  final AppMarketState _marketState;
  final AppOverviewState _overviewState;
  final AppRefreshState _refreshState;
  final AppSyncState _syncState;
  late final AppSessionState _sessionState;
  final AppTradeState _tradeState;
  final AppPreferencesState _preferencesState;
  final AppSecurityState _securityState;

  AppState({
    ApiService? api,
    CacheService? cache,
    SecureStorageService? secureStorage,
    BiometricService? biometric,
    LoginHandler? loginHandler,
    Future<String?> Function()? tokenLoader,
    Future<Map<String, dynamic>?> Function()? profileLoader,
    Future<Map<String, dynamic>?> Function(String refreshToken)? refreshLoader,
  }) : this._internal(
         api: api ?? ApiService(),
         cache: cache ?? CacheService(),
         secureStorage: secureStorage ?? SecureStorageService(),
         biometric: biometric ?? BiometricService(),
         loginHandler: loginHandler,
         tokenLoader: tokenLoader,
         profileLoader: profileLoader,
         refreshLoader: refreshLoader,
       );

  AppState._internal({
    required ApiService api,
    required CacheService cache,
    required SecureStorageService secureStorage,
    required BiometricService biometric,
    LoginHandler? loginHandler,
    Future<String?> Function()? tokenLoader,
    Future<Map<String, dynamic>?> Function()? profileLoader,
    Future<Map<String, dynamic>?> Function(String refreshToken)? refreshLoader,
  }) : _api = api,
       _assetsState = AppAssetsState(),
       _authState = AppAuthState(),
       _marketState = AppMarketState(),
       _overviewState = AppOverviewState(),
       _refreshState = AppRefreshState(
         api: api,
         staticDataTtl: _staticDataTtl,
         historyDataTtl: _historyDataTtl,
         ratesDataTtl: _ratesDataTtl,
         syncVersionTtl: _syncVersionTtl,
         priceRefreshMinInterval: _priceRefreshMinInterval,
         syncBootstrapDomains: generatedSyncBootstrapDomains,
       ),
       _syncState = AppSyncState(cache: cache),
       _preferencesState = AppPreferencesState(cache: cache),
       _securityState = AppSecurityState(
         secureStorage: secureStorage,
         biometric: biometric,
       ),
       _tradeState = AppTradeState(api: api) {
    _sessionState = AppSessionState(
      api: api,
      secureStorage: secureStorage,
      assetsState: _assetsState,
      authState: _authState,
      marketState: _marketState,
      securityState: _securityState,
      syncState: _syncState,
      userProfileTtl: _userProfileTtl,
      userProfileDomain: _userProfileDomain,
      loginHandler: loginHandler,
      tokenLoader: tokenLoader,
      profileLoader: profileLoader,
      refreshLoader: refreshLoader,
    );
    _api.onAuthExpired = () {
      unawaited(_handleAuthExpired());
    };
    _assetsState.addListener(_relayChildStateChange);
    _authState.addListener(_relayChildStateChange);
    _marketState.addListener(_relayChildStateChange);
    _overviewState.addListener(_relayChildStateChange);
    _syncState.addListener(_relayChildStateChange);
    _preferencesState.addListener(_relayChildStateChange);
    _securityState.addListener(_relayChildStateChange);
    _loadTheme();
    _restoreSession();
  }

  void _relayChildStateChange() {
    notifyListeners();
  }

  @override
  void dispose() {
    _assetsState.removeListener(_relayChildStateChange);
    _authState.removeListener(_relayChildStateChange);
    _marketState.removeListener(_relayChildStateChange);
    _overviewState.removeListener(_relayChildStateChange);
    _syncState.removeListener(_relayChildStateChange);
    _preferencesState.removeListener(_relayChildStateChange);
    _securityState.removeListener(_relayChildStateChange);
    _assetsState.dispose();
    _authState.dispose();
    _marketState.dispose();
    _overviewState.dispose();
    _syncState.dispose();
    _preferencesState.dispose();
    _securityState.dispose();
    super.dispose();
  }

  // 2) 认证与安全状态
  bool _handlingAuthExpired = false;

  Future<void> _handleAuthExpired() async {
    if (_handlingAuthExpired) return;
    _handlingAuthExpired = true;
    try {
      await _clearSessionAndUnauthenticated();
    } finally {
      _handlingAuthExpired = false;
    }
  }

  // 3) 资产与持仓状态
  double _totalAsset = 0;
  double _totalCash = 0;
  double _totalInvest = 0;
  double _totalOther = 0;
  double _totalLiability = 0;

  Map<String, PriceInfo> _prices = {};
  Map<String, PriceInfo> _priceSnapshots = {};
  String _currentCategory = 'all';
  bool _portfolioLoaded = false;
  AppAsyncFlowResult? _lastHydrateResult;
  AppAsyncFlowResult? _lastRefreshResult;
  AppAsyncFlowResult? _lastSessionRestoreResult;
  AppAsyncFlowResult? _lastSessionValidationResult;

  // 4) 汇率、市场与行情状态
  // 5) 历史概览与同步状态
  static const Duration _priceRefreshMinInterval = Duration(seconds: 2);

  // ============================================================
  // 7) 基础 getters
  // ============================================================

  ApiService get apiService => _api;
  bool get isLoggedIn => _authState.isLoggedIn;
  SessionBootState get sessionBootState => _authState.sessionBootState;
  bool get isSessionReady =>
      _authState.sessionBootState != SessionBootState.initializing;
  String? get token => _authState.token;
  String? get refreshToken => _authState.refreshToken;
  String? get username => _authState.username;
  String? get userId => _authState.userId;
  int? get userNumber => _authState.userNumber;
  String? get nickname => _authState.nickname;
  String? get avatar => _authState.avatar;
  String? get createdAtRaw => _authState.createdAtRaw;
  bool get biometricEnabled => _securityState.biometricEnabled;
  String? get authErrorMessage => _authState.authErrorMessage;
  AuthLogoutMode get logoutMode => _securityState.logoutMode;
  bool get isAppLocked => _securityState.isAppLocked;

  double get totalAsset => _totalAsset;
  double get totalCash => _totalCash;
  double get totalInvest => _totalInvest;
  double get totalOther => _totalOther;
  double get totalLiability => _totalLiability;

  List<PortfolioItem> get portfolio => _assetsState.portfolio;
  Map<String, PriceInfo> get prices => _prices;
  String get currentCategory => _currentCategory;
  bool get portfolioLoaded => _portfolioLoaded;
  AppAsyncFlowResult? get lastHydrateResult => _lastHydrateResult;
  AppAsyncFlowResult? get lastRefreshResult => _lastRefreshResult;
  AppAsyncFlowResult? get lastSessionRestoreResult => _lastSessionRestoreResult;
  AppAsyncFlowResult? get lastSessionValidationResult =>
      _lastSessionValidationResult;

  List<Asset> get cashAssets => _assetsState.cashAssets;
  List<Asset> get otherAssets => _assetsState.otherAssets;
  List<Asset> get liabilities => _assetsState.liabilities;

  Map<String, double> get exchangeRates => _marketState.exchangeRates;
  Map<String, bool> get marketOpenStatus => _marketState.marketOpenStatus;
  Map<String, bool> get marketTradingDayStatus =>
      _marketState.marketTradingDayStatus;
  bool get amountHidden => _preferencesState.amountHidden;
  String get displayCurrency => _preferencesState.displayCurrency;
  ThemeMode get themeMode => _preferencesState.themeMode;
  bool get isLightTheme => _preferencesState.isLightTheme;

  double get monthChange => _overviewState.monthChange;
  double get yearChange => _overviewState.yearChange;
  double get historyPeak => _overviewState.historyPeak;
  bool get hasMonthBaseline => _overviewState.hasMonthBaseline;
  bool get hasYearBaseline => _overviewState.hasYearBaseline;
  bool get overviewMilestonesReady => _overviewState.overviewMilestonesReady;
  bool get monthFromFirst => _overviewState.monthFromFirst;
  bool get yearFromFirst => _overviewState.yearFromFirst;
  DateTime? get assetDataUpdatedAt => _syncState.assetDataUpdatedAt;
  DateTime? get quoteDataUpdatedAt => _syncState.quoteDataUpdatedAt;
  bool get assetDataFromCache => _syncState.assetDataFromCache;
  bool get quoteDataFromCache => _syncState.quoteDataFromCache;
  Map<String, String> get _syncVersions => _syncState.syncVersions;

  List<PortfolioItem> get _portfolio => _assetsState.portfolio;
  set _portfolio(List<PortfolioItem> value) {
    _assetsState.replacePortfolio(value, notify: false);
  }

  List<Asset> get _cashAssets => _assetsState.cashAssets;
  set _cashAssets(List<Asset> value) {
    _assetsState.replaceCashAssets(value, notify: false);
  }

  List<Asset> get _otherAssets => _assetsState.otherAssets;
  set _otherAssets(List<Asset> value) {
    _assetsState.replaceOtherAssets(value, notify: false);
  }

  List<Asset> get _liabilities => _assetsState.liabilities;
  set _liabilities(List<Asset> value) {
    _assetsState.replaceLiabilities(value, notify: false);
  }

  int get quoteRefreshIntervalSeconds {
    if (_marketState.hasAnyMarketOpen) {
      return _syncState.quoteIntervalOpenSec;
    }
    if (_hasActiveUsExtendedSession()) {
      return _syncState.quoteIntervalUsExtendedSec;
    }
    return _syncState.quoteIntervalClosedSec;
  }

  double _rateForCurrency(String curr) {
    return _marketState.rateForCurrency(curr);
  }

  double getCurrencyRate(String curr) => _rateForCurrency(curr);

  double convertToCny(double amount, String curr) {
    return amount * _rateForCurrency(curr);
  }

  String _normalizeMarketKey(String? market) {
    return _marketState.normalizeMarketKey(market);
  }

  bool isMarketOpen(String? market) {
    return _marketState.isMarketOpen(market);
  }

  bool isMarketTradingDay(String? market) {
    return _marketState.isMarketTradingDay(market);
  }

  bool isAssetMarketOpen(PortfolioItem item) {
    return isMarketOpen(item.marketType);
  }

  bool isAssetTradingDay(PortfolioItem item) {
    return isMarketTradingDay(item.marketType);
  }

  bool _isUsExtendedSessionActive(PortfolioItem item, PriceInfo? priceInfo) {
    if (priceInfo == null) return false;
    if (_normalizeMarketKey(item.marketType) != 'us') return false;
    if (priceInfo.price <= 0 || priceInfo.yclose <= 0) return false;
    if (priceInfo.extendedActive) return true;
    final session = priceInfo.effectiveSession.trim().toLowerCase();
    return session == 'pre' || session == 'post';
  }

  bool _hasActiveUsExtendedSession() {
    for (final item in _portfolio) {
      if (_normalizeMarketKey(item.marketType) != 'us') continue;
      if (_isUsExtendedSessionActive(item, resolvePriceInfo(item))) {
        return true;
      }
    }
    return false;
  }

  bool _isValidPriceInfo(PriceInfo? info) {
    return info != null && info.price > 0;
  }

  PriceInfo? _resolvePriceInfoByCode(
    String code, {
    PriceInfo? preferred,
    Map<String, PriceInfo>? runtimeFallback,
  }) {
    if (_isValidPriceInfo(preferred)) return preferred;
    final live = _prices[code];
    if (_isValidPriceInfo(live)) return live;
    final runtime = runtimeFallback?[code];
    if (_isValidPriceInfo(runtime)) return runtime;
    final snapshot = _priceSnapshots[code];
    if (_isValidPriceInfo(snapshot)) return snapshot;
    return null;
  }

  PriceInfo? resolvePriceInfoByCode(String code, {PriceInfo? preferred}) {
    return _resolvePriceInfoByCode(code, preferred: preferred);
  }

  PriceInfo? resolvePriceInfo(PortfolioItem item, {PriceInfo? preferred}) {
    return _resolvePriceInfoByCode(item.code, preferred: preferred);
  }

  bool isNavUpdatePendingAsset(PortfolioItem item) {
    if (item.navUpdatePending != null) return item.navUpdatePending!;
    final code = item.code.trim().toLowerCase();
    return code.startsWith('f_') || code.startsWith('ft_');
  }

  bool isAssetDayPnlDisplayEnabled(PortfolioItem item, {PriceInfo? priceInfo}) {
    if (item.dayPnlDisplayEnabled != null) {
      return item.dayPnlDisplayEnabled!;
    }
    if (isNavUpdatePendingAsset(item)) {
      return false;
    }
    final resolved = resolvePriceInfo(item, preferred: priceInfo);
    return resolved != null && resolved.yclose > 0;
  }

  bool isAssetDayPnlEnabled(PortfolioItem item, {PriceInfo? priceInfo}) {
    if (item.dayPnlAggregateEnabled != null) {
      return item.dayPnlAggregateEnabled!;
    }
    if (isNavUpdatePendingAsset(item)) {
      return false;
    }
    final resolved = resolvePriceInfo(item, preferred: priceInfo);
    if (resolved == null || resolved.yclose <= 0) {
      return false;
    }
    if (isAssetTradingDay(item)) {
      return true;
    }
    return _isUsExtendedSessionActive(item, resolved);
  }

  /// 投资币种归一：优先按代码识别市场，无法识别时再回退到传入币种。
  String normalizeInvestmentCurrency({required String code, String? curr}) {
    final raw = code.trim();
    final lower = raw.toLowerCase();
    if (raw.isEmpty) {
      final fallback = curr?.trim().toUpperCase();
      return (fallback == null || fallback.isEmpty) ? 'CNY' : fallback;
    }
    if (lower.startsWith('sh900')) return 'USD';
    if (lower.startsWith('sz200')) return 'HKD';
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

  Future<double?> fetchLatestPriceForCode(String code) async {
    final raw = code.trim();
    if (raw.isEmpty) return null;
    final apiCode = raw.startsWith('gb_') ? raw.substring(3) : raw;
    try {
      final prices = await _api.getPricesBatch(<String>[apiCode]);
      final payload = prices[apiCode];
      if (payload is! Map<String, dynamic>) return null;
      final info = PriceInfo.fromJson(payload);
      if (info.price > 0) return info.price;
      if (info.yclose > 0) return info.yclose;
      return null;
    } catch (_) {
      return null;
    }
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
    return PortfolioMetricsService.calcInvestTotalMV(_portfolio);
  }

  /// 投资今日盈亏
  double get investDayPnl {
    return PortfolioMetricsService.calcInvestDayPnl(_portfolio);
  }

  /// 投资今日盈亏率
  double get investDayPnlRate {
    return PortfolioMetricsService.calcInvestDayPnlRate(_portfolio);
  }

  /// 投资持仓盈亏
  double get investHoldingPnl {
    return PortfolioMetricsService.calcInvestHoldingPnl(_portfolio);
  }

  /// 投资持仓盈亏率
  double get investHoldingPnlRate {
    return PortfolioMetricsService.calcInvestHoldingPnlRate(_portfolio);
  }

  // ============================================================
  // 8) 缓存与同步基础
  // ============================================================

  AppSessionBindings get _sessionBindings => AppSessionBindings(
    notifyListeners: notifyListeners,
    clearPrices: () => _prices = <String, PriceInfo>{},
    clearPriceSnapshots: () => _priceSnapshots = <String, PriceInfo>{},
    setPortfolioLoaded: (value) => _portfolioLoaded = value,
    hydrateFromCache: hydrateFromCache,
    refreshAll: refreshAll,
  );

  AppRefreshBindings get _refreshBindings => AppRefreshBindings(
    username: () => username,
    userId: () => userId,
    syncState: _syncState,
    syncVersions: () => _syncVersions,
    portfolio: () => _portfolio,
    replacePortfolio: (value) => _portfolio = value,
    cashAssets: () => _cashAssets,
    replaceCashAssets: (value) => _cashAssets = value,
    otherAssets: () => _otherAssets,
    replaceOtherAssets: (value) => _otherAssets = value,
    liabilities: () => _liabilities,
    replaceLiabilities: (value) => _liabilities = value,
    prices: () => _prices,
    replacePrices: (value) => _prices = value,
    priceSnapshots: () => _priceSnapshots,
    replacePriceSnapshots: (value) => _priceSnapshots = value,
    portfolioLoaded: () => _portfolioLoaded,
    setPortfolioLoaded: (value) => _portfolioLoaded = value,
    exchangeRates: () => exchangeRates,
    recalculateHomeTotals: _recalculateHomeTotals,
    calculateHistoryStats: _calculateHistoryStats,
    applyOverviewMilestones: applyOverviewMilestones,
    updateExchangeRates: updateExchangeRates,
    applySyncMarketStatus: _applySyncMarketStatus,
    serializeMarketStatusForCache: _marketState.serializeMarketStatusForCache,
    loadMarketStatusWithBudget: _loadMarketStatusWithBudget,
    resolvePriceInfoByCode: _resolvePriceInfoByCode,
    notifyListeners: notifyListeners,
  );

  Future<void> hydrateFromCache() async {
    final flow = startAppAsyncFlow('flutter.hydrateFromCache');
    try {
      await _refreshState.hydrateFromCache(bindings: _refreshBindings);
      _lastHydrateResult = finishAppAsyncFlow(flow, stage: 'cache-restored');
    } catch (error) {
      _lastHydrateResult = finishAppAsyncFlow(
        flow,
        stage: 'failed',
        error: error,
      );
    }
  }

  // ============================================================
  // 9) UI 偏好
  // ============================================================

  Future<void> _loadTheme() => _preferencesState.loadTheme();

  Future<void> setThemeMode(ThemeMode mode, {bool save = true}) =>
      _preferencesState.setThemeMode(mode, save: save);

  void toggleTheme() {
    _preferencesState.toggleTheme();
  }

  Future<void> savePortfolioToCache() async {
    await _refreshState.savePortfolioToCache(bindings: _refreshBindings);
  }

  Future<void> saveHomeCache(
    List<dynamic> history, {
    Map<String, dynamic>? overview,
  }) async {
    await _refreshState.saveHomeCache(
      bindings: _refreshBindings,
      history: history,
      overview: overview,
    );
  }

  // ============================================================
  // 10) 认证、资料与生物识别
  // ============================================================

  void clearAuthError() {
    _authState.clearAuthError(notify: false);
  }

  // C2: App 锁屏控制
  void lockApp() {
    _securityState.lockApp();
  }

  void unlockApp() {
    _securityState.unlockApp();
  }

  Future<ParsedMarketStatus> _loadMarketStatusSafe() async {
    try {
      final markets = await _api.getMarketStatuses();
      return _marketState.parseMarketStatus(markets);
    } catch (e) {
      debugPrint('读取市场状态失败，按全休市降级: $e');
      return const ParsedMarketStatus(
        open: AppMarketState.fallbackMarketOpenStatus,
        tradingDay: AppMarketState.fallbackMarketTradingDayStatus,
      );
    }
  }

  ParsedMarketStatus _currentMarketStatusSnapshot() {
    return _marketState.currentMarketStatusSnapshot();
  }

  Future<ParsedMarketStatus> _loadMarketStatusWithBudget() async {
    try {
      return await _loadMarketStatusSafe().timeout(
        _marketStatusRefreshBudget,
        onTimeout: () => _currentMarketStatusSnapshot(),
      );
    } catch (_) {
      return _currentMarketStatusSnapshot();
    }
  }

  Future<void> reloadBiometricPreference() async {
    await _securityState.reloadBiometricPreference();
  }

  /// 用户名密码登录
  Future<bool> login({
    required String username,
    required String password,
  }) async {
    return _sessionState.login(
      username: username,
      password: password,
      bindings: _sessionBindings,
    );
  }

  /// 邀请码注册
  Future<bool> register({
    required String username,
    required String password,
    required String inviteCode,
  }) async {
    return _sessionState.register(
      username: username,
      password: password,
      inviteCode: inviteCode,
      bindings: _sessionBindings,
    );
  }

  Future<bool> validateInviteCode(String inviteCode) async {
    return _sessionState.validateInviteCode(inviteCode);
  }

  Future<bool> changePassword({
    required String oldPassword,
    required String newPassword,
  }) async {
    return _sessionState.changePassword(
      oldPassword: oldPassword,
      newPassword: newPassword,
    );
  }

  Future<bool> setBiometricEnabled(bool enabled) async {
    return _sessionState.setBiometricEnabled(enabled);
  }

  Future<bool> tryBiometricLogin() async {
    return _sessionState.tryBiometricLogin(bindings: _sessionBindings);
  }

  Future<bool> fetchProfile() async {
    return _sessionState.fetchProfile(bindings: _sessionBindings);
  }

  /// 更新用户资料
  Future<bool> updateProfile({String? nickname, String? avatar}) async {
    return _sessionState.updateProfile(
      nickname: nickname,
      avatar: avatar,
      bindings: _sessionBindings,
    );
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
    String? createdAtRaw,
  }) async {
    await _sessionState.setLoggedIn(
      token: token,
      refreshToken: refreshToken,
      username: username,
      userId: userId,
      userNumber: userNumber,
      nickname: nickname,
      avatar: avatar,
      createdAtRaw: createdAtRaw,
      bindings: _sessionBindings,
    );
  }

  /// 退出登录
  void logout() {
    _sessionState.logout(bindings: _sessionBindings);
  }

  Future<void> _restoreSession() async {
    _lastSessionRestoreResult = await _sessionState.restoreSession(
      bindings: _sessionBindings,
    );
    if (_lastSessionRestoreResult?.ok == true &&
        (_lastSessionRestoreResult?.stage == 'refresh-restored' ||
            _lastSessionRestoreResult?.stage == 'token-restored')) {
      unawaited(_validateSessionInBackground());
    }
  }

  Future<void> _validateSessionInBackground() async {
    _lastSessionValidationResult = await _sessionState
        .validateSessionInBackground(bindings: _sessionBindings);
  }

  Future<void> _clearSessionAndUnauthenticated() async {
    await _sessionState.clearSessionAndUnauthenticated(
      bindings: _sessionBindings,
    );
  }

  /// 切换金额隐藏
  void toggleAmountHidden() {
    _preferencesState.toggleAmountHidden();
  }

  void setDisplayCurrency(String currency) {
    _preferencesState.setDisplayCurrency(currency);
  }

  /// Convert a CNY-denominated amount to the global display currency
  double convertDisplayAmount(double cnyAmount) {
    if (displayCurrency == 'CNY') return cnyAmount;
    final rate = _rateForCurrency(displayCurrency);
    if (rate <= 0) return cnyAmount;
    return cnyAmount / rate;
  }

  /// 格式化金额（支持隐藏）
  String formatAmount(double value, {String prefix = '¥'}) {
    if (amountHidden) return '****';
    return '$prefix${value.toStringAsFixed(0).replaceAllMapped(RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'), (Match m) => '${m[1]},')}';
  }

  /// 设置分类
  void setCategory(String category) {
    _currentCategory = category;
    notifyListeners();
  }

  /// 更新汇率
  void updateExchangeRates(Map<String, dynamic> rates) {
    _marketState.updateExchangeRates(rates);
  }

  void _applySyncMarketStatus(dynamic rawStatuses, {dynamic rawOpenFallback}) {
    _marketState.applySyncMarketStatus(
      rawStatuses,
      rawOpenFallback: rawOpenFallback,
      notify: false,
    );
  }

  double _assetAmountToCny(Asset item, {bool useAbs = false}) {
    final amount = useAbs ? item.amount.abs() : item.amount;
    return convertToCny(amount, _normalizeAssetCurrency(item.curr));
  }

  double _sumAssetListToCny(List<Asset> items, {bool useAbs = false}) {
    double total = 0;
    for (final item in items) {
      total += _assetAmountToCny(item, useAbs: useAbs);
    }
    return total;
  }

  void _recalculateHomeTotals() {
    _totalCash = _sumAssetListToCny(_cashAssets);
    _totalOther = _sumAssetListToCny(_otherAssets);
    _totalLiability = _sumAssetListToCny(_liabilities, useAbs: true);
    _totalInvest = investTotalMV;
    _totalAsset = _totalCash + _totalInvest + _totalOther - _totalLiability;
    _portfolioLoaded = _portfolio.isNotEmpty || _cashAssets.isNotEmpty;
  }

  // ============================================================
  // 11) 首页、同步与行情刷新
  // ============================================================

  /// 刷新首页数据（全量）
  /// 刷新首页数据
  Future<void> refreshHomeData() async {
    await _refreshState.refreshHomeData(bindings: _refreshBindings);
  }

  /// 按版本增量刷新，失败时自动回退全量刷新。
  Future<void> refreshByVersion({
    bool force = false,
    bool refreshQuotes = true,
  }) async {
    await _refreshState.refreshByVersion(
      bindings: _refreshBindings,
      force: force,
      refreshQuotes: refreshQuotes,
    );
  }

  /// 用分析概览覆盖首页里程碑（月/年改为收益口径）。
  /// 若接口数据异常则保留历史差值口径结果（回退行为）。
  void applyOverviewMilestones(Map<String, dynamic>? overview) {
    _overviewState.applyOverviewMilestones(overview, notify: false);
  }

  Future<void> _refreshPortfolioPricesInBackground({bool force = false}) async {
    await _refreshState.refreshPortfolioPricesInBackground(
      bindings: _refreshBindings,
      force: force,
    );
  }

  /// 仅刷新行情价格（用于定时更新今日盈亏/现价）
  Future<void> refreshPricesOnly() async {
    await _refreshState.refreshPricesOnly(bindings: _refreshBindings);
  }

  /// 刷新所有核心数据（用于启动与下拉刷新）
  Future<void> refreshAll({bool force = false}) async {
    final flow = startAppAsyncFlow('flutter.refreshAll');
    try {
      await _refreshState.refreshAll(bindings: _refreshBindings, force: force);
      _lastRefreshResult = finishAppAsyncFlow(
        flow,
        stage: force ? 'force-finished' : 'finished',
      );
    } catch (error) {
      _lastRefreshResult = finishAppAsyncFlow(
        flow,
        stage: 'failed',
        error: error,
      );
    }
  }

  // ============================================================
  // 12) 非投资资产操作
  // ============================================================

  AssetSnapshot _captureAssetSnapshot() {
    return _assetsState.captureAssetSnapshot();
  }

  void _restoreAssetSnapshot(AssetSnapshot snapshot) {
    _assetsState.restoreAssetSnapshot(snapshot, notify: false);
    _recalculateAssetTotals();
  }

  void _recalculateAssetTotals() {
    _totalCash = _sumAssetListToCny(_cashAssets);
    _totalOther = _sumAssetListToCny(_otherAssets);
    _totalLiability = _sumAssetListToCny(_liabilities, useAbs: true);
    _totalAsset = _totalCash + _totalInvest + _totalOther - _totalLiability;
    notifyListeners();
  }

  bool _optimisticAddAsset({
    required String type,
    required String name,
    required double amount,
    String? curr,
  }) {
    return _assetsState.optimisticAddAsset(
      type: type,
      name: name,
      amount: amount,
      curr: curr,
      notify: false,
    );
  }

  bool _optimisticDeleteAsset({required String type, required int id}) {
    return _assetsState.optimisticDeleteAsset(
      type: type,
      id: id,
      notify: false,
    );
  }

  bool _optimisticUpdateAsset({
    required String type,
    required int id,
    required String name,
    required double amount,
    String? curr,
  }) {
    return _assetsState.optimisticUpdateAsset(
      type: type,
      id: id,
      name: name,
      amount: amount,
      curr: curr,
      notify: false,
    );
  }

  /// 添加资产（现金/其他/负债）
  Future<AssetActionResult> addAsset({
    required String type,
    required String name,
    required double amount,
    String? curr,
    bool awaitRefresh = true,
  }) async {
    final snapshot = _captureAssetSnapshot();
    final changed = _optimisticAddAsset(
      type: type,
      name: name,
      amount: amount,
      curr: curr,
    );
    if (!changed) return const AssetActionResult.failure('不支持的资产类型');
    _recalculateAssetTotals();
    final normalizedCurr = _normalizeAssetCurrency(curr);

    final result = switch (type) {
      'cash' => await _api.addCashAsset(name, amount, curr: normalizedCurr),
      'other' => await _api.addOtherAsset(name, amount, curr: normalizedCurr),
      'liability' => await _api.addLiability(
        name,
        amount,
        curr: normalizedCurr,
      ),
      _ => const AssetActionResult.failure('不支持的资产类型'),
    };
    if (!result.ok) {
      _restoreAssetSnapshot(snapshot);
      return result;
    }
    await _triggerHomeRefresh(awaitRefresh: awaitRefresh);
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
    await _triggerHomeRefresh(awaitRefresh: awaitRefresh);
    return const AssetActionResult.success();
  }

  /// 更新资产（现金/其他/负债）
  Future<AssetActionResult> updateAsset({
    required String type,
    required int id,
    required String name,
    required double amount,
    String? curr,
    bool awaitRefresh = true,
  }) async {
    if (id <= 0) {
      return const AssetActionResult.failure('操作失败，请稍后重试');
    }
    final normalizedCurr = _normalizeAssetCurrency(curr);
    final snapshot = _captureAssetSnapshot();
    final changed = _optimisticUpdateAsset(
      type: type,
      id: id,
      name: name,
      amount: amount,
      curr: normalizedCurr,
    );
    if (changed) {
      _recalculateAssetTotals();
    } else if (type != 'cash' && type != 'other' && type != 'liability') {
      return const AssetActionResult.failure('不支持的资产类型');
    }

    AssetActionResult result;
    if (type == 'cash') {
      result = await _api.updateCashAsset(
        id,
        name,
        amount,
        curr: normalizedCurr,
      );
    } else if (type == 'other') {
      result = await _api.updateOtherAsset(
        id,
        name,
        amount,
        curr: normalizedCurr,
      );
    } else if (type == 'liability') {
      result = await _api.updateLiability(
        id,
        name,
        amount,
        curr: normalizedCurr,
      );
    } else {
      return const AssetActionResult.failure('不支持的资产类型');
    }
    if (!result.ok) {
      if (changed) {
        _restoreAssetSnapshot(snapshot);
      }
      return result;
    }
    await _triggerHomeRefresh(awaitRefresh: awaitRefresh);
    return const AssetActionResult.success();
  }

  // ============================================================
  // 13) 投资持仓操作
  // ============================================================

  String _normalizeAssetCurrency(String? curr) {
    return _assetsState.normalizeAssetCurrency(curr);
  }

  PortfolioSnapshot _capturePortfolioSnapshot() {
    return _assetsState.capturePortfolioSnapshot();
  }

  void _restorePortfolioSnapshot(PortfolioSnapshot snapshot) {
    _assetsState.restorePortfolioSnapshot(snapshot, notify: false);
    _recalculatePortfolioTotals();
  }

  void _recalculatePortfolioTotals() {
    _totalInvest = investTotalMV;
    _totalAsset = _totalCash + _totalInvest + _totalOther - _totalLiability;
    notifyListeners();
  }

  int _portfolioIndexByCode(String code) {
    return _assetsState.portfolioIndexByCode(code);
  }

  bool _optimisticAddInvestment({
    required String code,
    required String name,
    required double price,
    required double qty,
    String? curr,
    String? assetType,
  }) {
    return _assetsState.optimisticAddInvestment(
      code: code,
      name: name,
      price: price,
      qty: qty,
      normalizedCurr: normalizeInvestmentCurrency(code: code, curr: curr),
      assetType: assetType,
      notify: false,
    );
  }

  bool _optimisticBuyInvestment({
    required String code,
    required double price,
    required double qty,
  }) {
    return _assetsState.optimisticBuyInvestment(
      code: code,
      price: price,
      qty: qty,
      notify: false,
    );
  }

  bool _optimisticSellInvestment({
    required String code,
    required double price,
    required double qty,
  }) {
    return _assetsState.optimisticSellInvestment(
      code: code,
      price: price,
      qty: qty,
      notify: false,
    );
  }

  bool _optimisticModifyInvestment({
    required String code,
    required double qty,
    required double price,
    required double adjustment,
  }) {
    return _assetsState.optimisticModifyInvestment(
      code: code,
      qty: qty,
      price: price,
      adjustment: adjustment,
      notify: false,
    );
  }

  bool _optimisticDeleteInvestment({required String code}) {
    return _assetsState.optimisticDeleteInvestment(code: code, notify: false);
  }

  bool _optimisticAdjustCashAssetAmount({
    required int cashAssetId,
    required double deltaAmount,
  }) {
    return _assetsState.optimisticAdjustCashAssetAmount(
      cashAssetId: cashAssetId,
      deltaAmount: deltaAmount,
      notify: false,
    );
  }

  Future<void> _triggerHomeRefresh({required bool awaitRefresh}) async {
    if (awaitRefresh) {
      await refreshHomeData();
    } else {
      unawaited(refreshHomeData());
    }
  }

  double _convertAmountByCurrency({
    required double amount,
    required String fromCurr,
    required String toCurr,
  }) {
    return _tradeState.convertAmountByCurrency(
      amount: amount,
      fromCurr: fromCurr,
      toCurr: toCurr,
      rateForCurrency: _rateForCurrency,
    );
  }

  AssetActionResult _extractUndoInfo(AssetActionResult result) {
    return _tradeState.extractUndoInfo(result);
  }

  Future<AssetActionResult> _legacyBuyWithCashFallback({
    required String code,
    required String name,
    required double price,
    required double qty,
    required Asset cashAsset,
    required double cashDeductAmount,
  }) async {
    return _tradeState.legacyBuyWithCashFallback(
      code: code,
      name: name,
      price: price,
      qty: qty,
      cashAsset: cashAsset,
      cashDeductAmount: cashDeductAmount,
    );
  }

  Future<AssetActionResult> _legacySellToCashFallback({
    required String code,
    required double price,
    required double qty,
    required Asset cashAsset,
    required double cashCreditAmount,
  }) async {
    return _tradeState.legacySellToCashFallback(
      code: code,
      price: price,
      qty: qty,
      cashAsset: cashAsset,
      cashCreditAmount: cashCreditAmount,
    );
  }

  /// 搜索股票/基金
  Future<List<dynamic>> searchStocks(String query) async {
    return await _api.searchStocks(query);
  }

  // ============================================================
  // 14) 投资交易与调仓写操作
  // ============================================================

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
    if (price <= 0 || qty <= 0) {
      return const AssetActionResult.failure('请输入有效价格和数量');
    }
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
    if (cashAssetId == -999) {
      if (_portfolioIndexByCode(code) >= 0) {
        return buyInvestment(
          code: code,
          price: price,
          qty: qty,
          awaitRefresh: awaitRefresh,
        );
      } else {
        return addInvestment(
          code: code,
          name: name,
          price: price,
          qty: qty,
          curr: curr,
          assetType: assetType,
          awaitRefresh: awaitRefresh,
        );
      }
    }
    if (cashAssetId <= 0) {
      return const AssetActionResult.failure('请选择资金来源账户');
    }

    final cashIndex = _cashAssets.indexWhere(
      (asset) => asset.id == cashAssetId,
    );
    if (cashIndex < 0) {
      return const AssetActionResult.failure('未找到资金来源账户');
    }
    final cashAsset = _cashAssets[cashIndex];
    final normalizedCurr = normalizeInvestmentCurrency(code: code, curr: curr);
    final normalizedCashCurr = _normalizeAssetCurrency(cashAsset.curr);
    if (normalizedCashCurr != _normalizeAssetCurrency(normalizedCurr)) {
      return AssetActionResult.failure(
        '资金账户币种不匹配：需要${_normalizeAssetCurrency(normalizedCurr)}账户',
        data: {
          'asset_curr': _normalizeAssetCurrency(normalizedCurr),
          'cash_curr': normalizedCashCurr,
        },
      );
    }
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
    _totalCash = _sumAssetListToCny(_cashAssets);
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
        await _triggerHomeRefresh(awaitRefresh: awaitRefresh);
        return fallbackResult;
      }
      _restoreAssetSnapshot(assetSnapshot);
      _restorePortfolioSnapshot(portfolioSnapshot);
      return result;
    }
    await _triggerHomeRefresh(awaitRefresh: awaitRefresh);
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
    if (cashAssetId == -999) {
      return sellInvestment(
        code: code,
        price: price,
        qty: qty,
        awaitRefresh: awaitRefresh,
      );
    }
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
    final cashIndex = _cashAssets.indexWhere(
      (asset) => asset.id == cashAssetId,
    );
    if (cashIndex < 0) {
      return const AssetActionResult.failure('未找到回款账户');
    }
    final cashAsset = _cashAssets[cashIndex];
    final normalizedAssetCurr = _normalizeAssetCurrency(current.curr);
    final normalizedCashCurr = _normalizeAssetCurrency(cashAsset.curr);
    if (normalizedAssetCurr != normalizedCashCurr) {
      return AssetActionResult.failure(
        '回款账户币种不匹配：需要$normalizedAssetCurr账户',
        data: {
          'asset_curr': normalizedAssetCurr,
          'cash_curr': normalizedCashCurr,
        },
      );
    }
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
    _totalCash = _sumAssetListToCny(_cashAssets);
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
        await _triggerHomeRefresh(awaitRefresh: awaitRefresh);
        return fallbackResult;
      }
      _restoreAssetSnapshot(assetSnapshot);
      _restorePortfolioSnapshot(portfolioSnapshot);
      return result;
    }

    await _triggerHomeRefresh(awaitRefresh: awaitRefresh);
    return _extractUndoInfo(result);
  }

  /// 买入（加仓）
  Future<AssetActionResult> buyInvestment({
    required String code,
    required double price,
    required double qty,
    bool awaitRefresh = true,
  }) async {
    if (price <= 0 || qty <= 0) {
      return const AssetActionResult.failure('请输入有效价格和数量');
    }
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
    await _triggerHomeRefresh(awaitRefresh: awaitRefresh);
    return _extractUndoInfo(result);
  }

  /// 卖出（减仓）
  Future<AssetActionResult> sellInvestment({
    required String code,
    required double price,
    required double qty,
    bool awaitRefresh = true,
  }) async {
    if (price <= 0 || qty <= 0) {
      return const AssetActionResult.failure('请输入有效价格和数量');
    }
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
    await _triggerHomeRefresh(awaitRefresh: awaitRefresh);
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
    if (qty <= 0 || !price.isFinite || !adjustment.isFinite) {
      return const AssetActionResult.failure('请输入有效调整参数');
    }
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
    await _triggerHomeRefresh(awaitRefresh: awaitRefresh);
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
    unawaited(_triggerHomeRefresh(awaitRefresh: false));
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
    await _triggerHomeRefresh(awaitRefresh: awaitRefresh);
    return const AssetActionResult.success();
  }

  // ============================================================
  // 15) 历史统计与概览口径
  // ============================================================

  /// 计算历史统计数据
  void _calculateHistoryStats(List<dynamic> history) {
    _overviewState.calculateHistoryStats(history, notify: false);
  }

  // ============================================================
  // 16) 汇率、组合刷新与展示工具
  // ============================================================

  /// 刷新投资组合
  Future<void> refreshPortfolio() async {
    await _refreshState.refreshPortfolio(bindings: _refreshBindings);
  }

  /// 加载汇率
  Future<void> loadExchangeRates() async {
    await _refreshState.loadExchangeRates(bindings: _refreshBindings);
  }

  /// 获取盈亏颜色
  static Color getPnlColor(double value) {
    if (value > 0) return const Color(0xFFEF4444); // 红色（盈利）
    if (value < 0) return const Color(0xFF10B981); // 绿色（亏损）
    return const Color(0xFF94A3B8); // 灰色
  }

  /// 格式化盈亏
  String formatPnl(double value) {
    if (amountHidden) return '****';
    final sign = value >= 0 ? '+' : '';
    return '$sign${value.toStringAsFixed(2)}';
  }

  /// 格式化盈亏（整数）
  String formatPnlInt(double value) {
    if (amountHidden) return '****';
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
    if (amountHidden) return '****';
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
    if (amountHidden) return '****';
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
    if (amountHidden) return '****';
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
    if (amountHidden) return '****';
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
