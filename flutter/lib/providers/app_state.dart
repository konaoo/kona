import 'dart:async';

import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/async_flow_logger.dart';
import '../services/biometric_service.dart';
import '../services/cache_service.dart';
import '../services/secure_storage_service.dart';
import '../models/portfolio.dart';
import '../models/asset.dart';
import '../models/asset_action_result.dart';
import 'app_asset_write_state.dart';
import 'app_assets_state.dart';
import 'app_auth_state.dart';
import 'app_home_totals_state.dart';
import 'app_investment_write_state.dart';
import 'app_market_state.dart';
import 'app_overview_state.dart';
import 'app_portfolio_view_state.dart';
import 'app_preferences_state.dart';
import 'app_refresh_coordinator_state.dart';
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
  late final AppAssetWriteState _assetWriteState;
  late final AppInvestmentWriteState _investmentWriteState;
  final AppAssetsState _assetsState;
  final AppAuthState _authState;
  late final AppHomeTotalsState _homeTotalsState;
  final AppMarketState _marketState;
  final AppOverviewState _overviewState;
  late final AppRefreshCoordinatorState _refreshCoordinatorState;
  final AppRefreshState _refreshState;
  final AppSyncState _syncState;
  late final AppPortfolioViewState _portfolioViewState;
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
    _portfolioViewState = AppPortfolioViewState(
      api: api,
      assetsState: _assetsState,
      marketState: _marketState,
      preferencesState: _preferencesState,
      syncState: _syncState,
    );
    _homeTotalsState = AppHomeTotalsState(
      assetsState: _assetsState,
      marketState: _marketState,
      portfolioViewState: _portfolioViewState,
    );
    _assetWriteState = AppAssetWriteState(
      api: api,
      assetsState: _assetsState,
      homeTotalsState: _homeTotalsState,
    );
    _investmentWriteState = AppInvestmentWriteState(
      api: api,
      assetsState: _assetsState,
      homeTotalsState: _homeTotalsState,
      tradeState: _tradeState,
    );
    _refreshCoordinatorState = AppRefreshCoordinatorState(
      refreshState: _refreshState,
      syncState: _syncState,
      username: () => username,
      userId: () => userId,
      currentLedgerId: () => _currentLedgerId,
      portfolio: () => _portfolio,
      replacePortfolio: (value) => _portfolio = value,
      cashAssets: () => _cashAssets,
      replaceCashAssets: (value) => _cashAssets = value,
      otherAssets: () => _otherAssets,
      replaceOtherAssets: (value) => _otherAssets = value,
      liabilities: () => _liabilities,
      replaceLiabilities: (value) => _liabilities = value,
      prices: () => _portfolioViewState.prices,
      replacePrices: (value) =>
          _portfolioViewState.replacePrices(value, notify: false),
      priceSnapshots: () => _portfolioViewState.priceSnapshots,
      replacePriceSnapshots: (value) =>
          _portfolioViewState.replacePriceSnapshots(value, notify: false),
      exchangeRates: () => exchangeRates,
      recalculateHomeTotals: _recalculateHomeTotals,
      calculateHistoryStats: _calculateHistoryStats,
      applyOverviewMilestones: applyOverviewMilestones,
      updateExchangeRates: updateExchangeRates,
      applySyncMarketStatus: _applySyncMarketStatus,
      serializeMarketStatusForCache: _marketState.serializeMarketStatusForCache,
      loadMarketStatusWithBudget: _loadMarketStatusWithBudget,
      resolvePriceInfoByCode: _portfolioViewState.resolvePriceInfoByCode,
      notifyListeners: notifyListeners,
    );
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
    _homeTotalsState.addListener(_relayChildStateChange);
    _marketState.addListener(_relayChildStateChange);
    _overviewState.addListener(_relayChildStateChange);
    _portfolioViewState.addListener(_relayChildStateChange);
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
    _homeTotalsState.removeListener(_relayChildStateChange);
    _marketState.removeListener(_relayChildStateChange);
    _overviewState.removeListener(_relayChildStateChange);
    _portfolioViewState.removeListener(_relayChildStateChange);
    _syncState.removeListener(_relayChildStateChange);
    _preferencesState.removeListener(_relayChildStateChange);
    _securityState.removeListener(_relayChildStateChange);
    _assetsState.dispose();
    _authState.dispose();
    _homeTotalsState.dispose();
    _marketState.dispose();
    _overviewState.dispose();
    _portfolioViewState.dispose();
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
  int get aiCreditsBalance => _authState.aiCreditsBalance;
  String? get nickname => _authState.nickname;
  String? get avatar => _authState.avatar;
  String? get createdAtRaw => _authState.createdAtRaw;
  bool get biometricEnabled => _securityState.biometricEnabled;
  String? get authErrorMessage => _authState.authErrorMessage;
  AuthLogoutMode get logoutMode => _securityState.logoutMode;
  bool get isAppLocked => _securityState.isAppLocked;

  double get totalAsset => _homeTotalsState.totalAsset;
  double get totalCash => _homeTotalsState.totalCash;
  double get totalInvest => _homeTotalsState.totalInvest;
  double get totalOther => _homeTotalsState.totalOther;
  double get totalLiability => _homeTotalsState.totalLiability;

  List<PortfolioItem> get portfolio => _assetsState.portfolio;
  Map<String, PriceInfo> get prices => _portfolioViewState.prices;
  String get currentCategory => _portfolioViewState.currentCategory;
  bool get portfolioLoaded => _refreshCoordinatorState.portfolioLoaded;

  // ─── 账本状态 ─────────────────────────────────────
  List<Map<String, dynamic>> _ledgers = [];
  int? _currentLedgerId;
  Map<String, dynamic> _realtimeToday = const {};
  List<Map<String, dynamic>> get ledgers => _ledgers;
  int? get currentLedgerId => _currentLedgerId;
  Map<String, dynamic> get realtimeToday => _realtimeToday;

  List<Map<String, dynamic>> _cloneLedgers(List<Map<String, dynamic>> source) {
    return source
        .map((ledger) => Map<String, dynamic>.from(ledger))
        .toList(growable: false);
  }

  int? _coerceLedgerId(dynamic rawId) {
    if (rawId is int) return rawId;
    return int.tryParse(rawId?.toString() ?? '');
  }

  int? _pickLedgerSelection(
    List<Map<String, dynamic>> ledgers, {
    int? preferredLedgerId,
  }) {
    if (ledgers.isEmpty) return null;
    if (preferredLedgerId != null &&
        ledgers.any(
          (ledger) => _coerceLedgerId(ledger['id']) == preferredLedgerId,
        )) {
      return preferredLedgerId;
    }
    final defaultLedger = ledgers.firstWhere(
      (ledger) => ledger['is_default'] == 1 || ledger['is_default'] == true,
      orElse: () => ledgers.first,
    );
    return _coerceLedgerId(defaultLedger['id']);
  }

  void _replaceLedgers(
    List<Map<String, dynamic>> nextLedgers, {
    int? preferredLedgerId,
  }) {
    _ledgers = nextLedgers;
    _currentLedgerId = _pickLedgerSelection(
      nextLedgers,
      preferredLedgerId: preferredLedgerId,
    );
    notifyListeners();
  }

  /// 切换当前账本，null 表示全部
  void switchLedger(int? ledgerId) {
    if (_currentLedgerId == ledgerId) return;
    _currentLedgerId = ledgerId;
    notifyListeners();
    unawaited(refreshHomeData(ledgerId: ledgerId));
  }

  /// 加载账本列表
  Future<void> loadLedgers() async {
    if (!isLoggedIn) return;
    try {
      final data = await _api.getLedgers();
      _replaceLedgers(
        data.cast<Map<String, dynamic>>(),
        preferredLedgerId: _currentLedgerId,
      );
    } catch (e) {
      debugPrint('Failed to load ledgers: $e');
    }
  }

  /// 创建账本
  Future<AssetActionResult> createLedger(
    String name, {
    String description = '',
  }) async {
    final cleanName = name.trim();
    if (cleanName.isEmpty) {
      return const AssetActionResult.failure('账本名称不能为空');
    }
    final previousLedgers = _cloneLedgers(_ledgers);
    final previousCurrentLedgerId = _currentLedgerId;
    final tempId = -DateTime.now().microsecondsSinceEpoch;
    final nextSortOrder =
        _ledgers.fold<int>(-1, (maxValue, ledger) {
          final sortOrder = ledger['sort_order'];
          final parsed = sortOrder is int
              ? sortOrder
              : int.tryParse(sortOrder?.toString() ?? '') ?? -1;
          return parsed > maxValue ? parsed : maxValue;
        }) +
        1;
    final optimisticLedgers = [
      ...previousLedgers,
      <String, dynamic>{
        'id': tempId,
        'user_id': userId,
        'name': cleanName,
        'description': description.trim(),
        'sort_order': nextSortOrder,
        'is_default': false,
        'pending': true,
      },
    ];
    _replaceLedgers(
      optimisticLedgers,
      preferredLedgerId: previousCurrentLedgerId,
    );

    final result = await _api.createLedger(name, description: description);
    if (!result.ok) {
      _replaceLedgers(
        previousLedgers,
        preferredLedgerId: previousCurrentLedgerId,
      );
      return result;
    }

    final createdLedgerId = _coerceLedgerId(result.data?['ledger_id']);
    if (createdLedgerId != null) {
      final settledLedgers = _cloneLedgers(_ledgers)
          .map((ledger) {
            if (_coerceLedgerId(ledger['id']) != tempId) return ledger;
            return <String, dynamic>{
              ...ledger,
              'id': createdLedgerId,
              'pending': false,
            };
          })
          .toList(growable: false);
      _replaceLedgers(
        settledLedgers,
        preferredLedgerId: previousCurrentLedgerId,
      );
    }
    unawaited(loadLedgers());
    return result;
  }

  /// 更新账本
  Future<AssetActionResult> updateLedger(
    int id,
    String name, {
    String description = '',
  }) async {
    final result = await _api.updateLedger(id, name, description: description);
    if (result.ok) await loadLedgers();
    return result;
  }

  /// 删除账本
  Future<AssetActionResult> deleteLedger(int id) async {
    final removedCurrent = _currentLedgerId == id;
    final previousLedgers = _cloneLedgers(_ledgers);
    final previousCurrentLedgerId = _currentLedgerId;
    final nextLedgers = previousLedgers
        .where((ledger) => _coerceLedgerId(ledger['id']) != id)
        .toList(growable: false);
    final nextCurrentLedgerId = removedCurrent
        ? _pickLedgerSelection(nextLedgers)
        : previousCurrentLedgerId;
    _replaceLedgers(nextLedgers, preferredLedgerId: nextCurrentLedgerId);
    if (removedCurrent) {
      unawaited(refreshHomeData(ledgerId: nextCurrentLedgerId));
    }

    final result = await _api.deleteLedger(id);
    if (!result.ok) {
      _replaceLedgers(
        previousLedgers,
        preferredLedgerId: previousCurrentLedgerId,
      );
      if (removedCurrent) {
        unawaited(refreshHomeData(ledgerId: previousCurrentLedgerId));
      }
      return result;
    }
    unawaited(loadLedgers());
    if (removedCurrent) {
      unawaited(refreshHomeData(ledgerId: nextCurrentLedgerId));
    }
    return result;
  }

  /// 更新账本排序
  Future<AssetActionResult> reorderLedgers(List<int> ledgerIds) async {
    final result = await _api.reorderLedgers(ledgerIds);
    if (result.ok) {
      await loadLedgers();
    }
    return result;
  }

  AppAsyncFlowResult? get lastHydrateResult =>
      _refreshCoordinatorState.lastHydrateResult;
  AppAsyncFlowResult? get lastRefreshResult =>
      _refreshCoordinatorState.lastRefreshResult;
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

  int get quoteRefreshIntervalSeconds =>
      _portfolioViewState.quoteRefreshIntervalSeconds;

  double _rateForCurrency(String curr) {
    return _marketState.rateForCurrency(curr);
  }

  double getCurrencyRate(String curr) => _rateForCurrency(curr);

  double convertToCny(double amount, String curr) {
    return amount * _rateForCurrency(curr);
  }

  bool isMarketOpen(String? market) {
    return _marketState.isMarketOpen(market);
  }

  bool isMarketTradingDay(String? market) {
    return _marketState.isMarketTradingDay(market);
  }

  bool isAssetMarketOpen(PortfolioItem item) {
    return _portfolioViewState.isAssetMarketOpen(item);
  }

  bool isAssetTradingDay(PortfolioItem item) {
    return _portfolioViewState.isAssetTradingDay(item);
  }

  PriceInfo? resolvePriceInfoByCode(String code, {PriceInfo? preferred}) {
    return _portfolioViewState.resolvePriceInfoByCode(
      code,
      preferred: preferred,
    );
  }

  PriceInfo? resolvePriceInfo(PortfolioItem item, {PriceInfo? preferred}) {
    return _portfolioViewState.resolvePriceInfo(item, preferred: preferred);
  }

  bool isNavUpdatePendingAsset(PortfolioItem item) {
    return _portfolioViewState.isNavUpdatePendingAsset(item);
  }

  bool isAssetDayPnlDisplayEnabled(PortfolioItem item, {PriceInfo? priceInfo}) {
    return _portfolioViewState.isAssetDayPnlDisplayEnabled(
      item,
      priceInfo: priceInfo,
    );
  }

  bool isAssetDayPnlEnabled(PortfolioItem item, {PriceInfo? priceInfo}) {
    return _portfolioViewState.isAssetDayPnlEnabled(item, priceInfo: priceInfo);
  }

  /// 投资币种归一：优先按代码识别市场，无法识别时再回退到传入币种。
  String normalizeInvestmentCurrency({required String code, String? curr}) {
    return _portfolioViewState.normalizeInvestmentCurrency(
      code: code,
      curr: curr,
    );
  }

  Future<double?> fetchLatestPriceForCode(String code) async {
    return _portfolioViewState.fetchLatestPriceForCode(code);
  }

  /// 过滤后的投资组合
  List<PortfolioItem> get filteredPortfolio {
    return _portfolioViewState.filteredPortfolio;
  }

  /// 投资总市值
  double get investTotalMV {
    return _portfolioViewState.investTotalMV;
  }

  /// 投资今日盈亏
  double get investDayPnl {
    return _portfolioViewState.investDayPnl;
  }

  /// 投资今日盈亏率
  double get investDayPnlRate {
    return _portfolioViewState.investDayPnlRate;
  }

  /// 投资持仓盈亏
  double get investHoldingPnl {
    return _portfolioViewState.investHoldingPnl;
  }

  /// 投资持仓盈亏率
  double get investHoldingPnlRate {
    return _portfolioViewState.investHoldingPnlRate;
  }

  // ============================================================
  // 8) 缓存与同步基础
  // ============================================================

  AppSessionBindings get _sessionBindings => AppSessionBindings(
    notifyListeners: notifyListeners,
    clearPrices: () => _portfolioViewState.clearPrices(notify: false),
    clearPriceSnapshots: () =>
        _portfolioViewState.clearPriceSnapshots(notify: false),
    setPortfolioLoaded: _refreshCoordinatorState.setPortfolioLoaded,
    hydrateFromCache: hydrateFromCache,
    refreshAll: refreshAll,
  );

  AppAssetWriteBindings get _assetWriteBindings => AppAssetWriteBindings(
    notifyListeners: notifyListeners,
    triggerHomeRefresh: (awaitRefresh) =>
        _triggerHomeRefresh(awaitRefresh: awaitRefresh),
  );

  AppInvestmentWriteBindings get _investmentWriteBindings =>
      AppInvestmentWriteBindings(
        notifyListeners: notifyListeners,
        triggerHomeRefresh: (awaitRefresh) =>
            _triggerHomeRefresh(awaitRefresh: awaitRefresh),
        normalizeInvestmentCurrency: normalizeInvestmentCurrency,
        rateForCurrency: _rateForCurrency,
      );

  Future<void> hydrateFromCache() async {
    await _refreshCoordinatorState.hydrateFromCache();
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
    await _refreshCoordinatorState.savePortfolioToCache();
  }

  Future<void> saveHomeCache(
    List<dynamic> history, {
    Map<String, dynamic>? overview,
  }) async {
    await _refreshCoordinatorState.saveHomeCache(history, overview: overview);
  }

  Future<List<dynamic>> loadCachedHistory() async {
    return _refreshCoordinatorState.loadCachedHistory();
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
    final success = await _sessionState.login(
      username: username,
      password: password,
      bindings: _sessionBindings,
    );
    if (success) {
      unawaited(loadLedgers());
    }
    return success;
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
    int? aiCreditsBalance,
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
      aiCreditsBalance: aiCreditsBalance,
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
      unawaited(loadLedgers());
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
    return _portfolioViewState.convertDisplayAmount(cnyAmount);
  }

  /// 格式化金额（支持隐藏）
  String formatAmount(double value, {String prefix = '¥'}) {
    return _portfolioViewState.formatAmount(value, prefix: prefix);
  }

  /// 设置分类
  void setCategory(String category) {
    _portfolioViewState.setCategory(category);
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

  void _recalculateHomeTotals() {
    _homeTotalsState.recalculateHomeTotals(notify: false);
  }

  // ============================================================
  // 11) 首页、同步与行情刷新
  // ============================================================

  /// 刷新首页数据（全量）
  /// 刷新首页数据
  Future<void> refreshHomeData({int? ledgerId}) async {
    final resolvedLedgerId = ledgerId ?? _currentLedgerId;
    await Future.wait<void>([
      _refreshCoordinatorState.refreshHomeData(ledgerId: resolvedLedgerId),
      refreshRealtimeToday(ledgerId: resolvedLedgerId),
    ]);
  }

  Future<void> refreshRealtimeToday({int? ledgerId}) async {
    try {
      final payload = await _api.getRealtimeToday(
        ledgerId: ledgerId ?? _currentLedgerId,
      );
      _realtimeToday = payload;
      notifyListeners();
    } catch (e) {
      debugPrint('Failed to load realtime today: $e');
    }
  }

  /// 按版本增量刷新，失败时自动回退全量刷新。
  Future<void> refreshByVersion({
    bool force = false,
    bool refreshQuotes = true,
  }) async {
    await _refreshCoordinatorState.refreshByVersion(
      force: force,
      refreshQuotes: refreshQuotes,
      ledgerId: _currentLedgerId,
    );
  }

  /// 用分析概览覆盖首页里程碑（月/年改为收益口径）。
  /// 若接口数据异常则保留历史差值口径结果（回退行为）。
  void applyOverviewMilestones(Map<String, dynamic>? overview) {
    _overviewState.applyOverviewMilestones(overview, notify: false);
  }

  /// 仅刷新行情价格（用于定时更新今日盈亏/现价）
  Future<void> refreshPricesOnly() async {
    await _refreshCoordinatorState.refreshPricesOnly();
  }

  /// 刷新所有核心数据（用于启动与下拉刷新）
  Future<void> refreshAll({bool force = false}) async {
    await _refreshCoordinatorState.refreshAll(
      force: force,
      ledgerId: _currentLedgerId,
    );
  }

  // ============================================================
  // 12) 非投资资产操作
  // ============================================================

  /// 添加资产（现金/其他/负债）
  Future<AssetActionResult> addAsset({
    required String type,
    required String name,
    required double amount,
    String? curr,
    bool awaitRefresh = true,
  }) async {
    return _assetWriteState.addAsset(
      type: type,
      name: name,
      amount: amount,
      curr: curr,
      awaitRefresh: awaitRefresh,
      bindings: _assetWriteBindings,
    );
  }

  /// 删除资产（现金/其他/负债）
  Future<AssetActionResult> deleteAsset({
    required String type,
    required int id,
    bool awaitRefresh = true,
  }) async {
    return _assetWriteState.deleteAsset(
      type: type,
      id: id,
      awaitRefresh: awaitRefresh,
      bindings: _assetWriteBindings,
    );
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
    return _assetWriteState.updateAsset(
      type: type,
      id: id,
      name: name,
      amount: amount,
      curr: curr,
      awaitRefresh: awaitRefresh,
      bindings: _assetWriteBindings,
    );
  }

  /// 资产增减调整（同时写入调整记录）
  Future<AssetActionResult> adjustAsset({
    required String type,
    required int id,
    required String name,
    required double currentAmount,
    required String mode,
    required double delta,
    required String note,
    String? curr,
    double? targetAmount,
  }) async {
    return _assetWriteState.adjustAsset(
      type: type,
      id: id,
      name: name,
      currentAmount: currentAmount,
      mode: mode,
      delta: delta,
      note: note,
      curr: curr,
      targetAmount: targetAmount,
      awaitRefresh: false,
      bindings: _assetWriteBindings,
    );
  }

  /// 获取资产调整记录
  Future<List<dynamic>> getAssetAdjustments({
    required String type,
    required int id,
  }) {
    return _api.getAssetAdjustments(assetType: type, assetId: id);
  }

  /// 获取投资持仓交易记录
  Future<List<dynamic>> getInvestmentTransactions(
    String code, {
    int? ledgerId,
  }) {
    return _api.getPortfolioTransactions(
      code,
      ledgerId: ledgerId ?? _currentLedgerId,
    );
  }

  // ============================================================
  // 13) 投资持仓操作
  // ============================================================

  Future<void> _triggerHomeRefresh({required bool awaitRefresh}) async {
    if (awaitRefresh) {
      await refreshHomeData();
    } else {
      unawaited(refreshHomeData());
    }
  }

  /// 搜索股票/基金
  Future<List<dynamic>> searchStocks(String query) async {
    return await _api.searchStocks(query);
  }

  /// 上传截图，解析“添加资产”候选结果
  Future<Map<String, dynamic>> parsePortfolioAssetScreenshot(
    String filePath,
  ) async {
    return _api.parsePortfolioAssetScreenshot(filePath);
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
    int? ledgerId,
  }) async {
    return _investmentWriteState.addInvestment(
      code: code,
      name: name,
      price: price,
      qty: qty,
      curr: curr,
      assetType: assetType,
      awaitRefresh: awaitRefresh,
      bindings: _investmentWriteBindings,
      ledgerId: ledgerId ?? _currentLedgerId,
    );
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
    int? ledgerId,
  }) async {
    return _investmentWriteState.buyInvestmentWithCash(
      code: code,
      name: name,
      price: price,
      qty: qty,
      cashAssetId: cashAssetId,
      assetType: assetType,
      curr: curr,
      awaitRefresh: awaitRefresh,
      bindings: _investmentWriteBindings,
      ledgerId: ledgerId ?? _currentLedgerId,
    );
  }

  /// 卖出到指定现金账户（同一事务减仓 + 回款）
  Future<AssetActionResult> sellInvestmentToCash({
    required String code,
    required double price,
    required double qty,
    required int cashAssetId,
    bool awaitRefresh = true,
    int? ledgerId,
  }) async {
    return _investmentWriteState.sellInvestmentToCash(
      code: code,
      price: price,
      qty: qty,
      cashAssetId: cashAssetId,
      awaitRefresh: awaitRefresh,
      bindings: _investmentWriteBindings,
      ledgerId: ledgerId ?? _currentLedgerId,
    );
  }

  /// 买入（加仓）
  Future<AssetActionResult> buyInvestment({
    required String code,
    required double price,
    required double qty,
    bool awaitRefresh = true,
    int? ledgerId,
  }) async {
    return _investmentWriteState.buyInvestment(
      code: code,
      price: price,
      qty: qty,
      awaitRefresh: awaitRefresh,
      bindings: _investmentWriteBindings,
      ledgerId: ledgerId ?? _currentLedgerId,
    );
  }

  /// 卖出（减仓）
  Future<AssetActionResult> sellInvestment({
    required String code,
    required double price,
    required double qty,
    bool awaitRefresh = true,
    int? ledgerId,
  }) async {
    return _investmentWriteState.sellInvestment(
      code: code,
      price: price,
      qty: qty,
      awaitRefresh: awaitRefresh,
      bindings: _investmentWriteBindings,
      ledgerId: ledgerId ?? _currentLedgerId,
    );
  }

  /// 手动调整（数量/成本）
  Future<AssetActionResult> modifyInvestment({
    required String code,
    required double qty,
    required double price,
    String? note,
    bool awaitRefresh = true,
    int? ledgerId,
  }) async {
    return _investmentWriteState.modifyInvestment(
      code: code,
      qty: qty,
      price: price,
      note: note,
      awaitRefresh: awaitRefresh,
      bindings: _investmentWriteBindings,
      ledgerId: ledgerId ?? _currentLedgerId,
    );
  }

  /// 投资收益事件（分红/手续费）
  Future<AssetActionResult> addInvestmentAdjustmentEvent({
    required String code,
    required String eventType,
    required double amount,
    String? note,
    bool awaitRefresh = true,
    int? ledgerId,
  }) async {
    return _investmentWriteState.addInvestmentAdjustmentEvent(
      code: code,
      eventType: eventType,
      amount: amount,
      note: note,
      awaitRefresh: awaitRefresh,
      bindings: _investmentWriteBindings,
      ledgerId: ledgerId ?? _currentLedgerId,
    );
  }

  /// 撤销投资写操作（买入/卖出/调整）
  Future<AssetActionResult> undoInvestmentOperation(String undoToken) async {
    return _investmentWriteState.undoInvestmentOperation(
      undoToken,
      bindings: _investmentWriteBindings,
    );
  }

  /// 删除投资资产
  Future<AssetActionResult> deleteInvestment({
    required String code,
    bool corrective = false,
    bool awaitRefresh = true,
  }) async {
    return _investmentWriteState.deleteInvestment(
      code: code,
      corrective: corrective,
      awaitRefresh: awaitRefresh,
      bindings: _investmentWriteBindings,
    );
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
  Future<void> refreshPortfolio({int? ledgerId}) async {
    await _refreshCoordinatorState.refreshPortfolio(
      ledgerId: ledgerId ?? _currentLedgerId,
    );
  }

  /// 加载汇率
  Future<void> loadExchangeRates() async {
    await _refreshCoordinatorState.loadExchangeRates();
  }

  /// 获取盈亏颜色
  static Color getPnlColor(double value) {
    return AppPortfolioViewState.getPnlColor(value);
  }

  /// 格式化盈亏
  String formatPnl(double value) {
    return _portfolioViewState.formatPnl(value);
  }

  /// 格式化盈亏（整数）
  String formatPnlInt(double value) {
    return _portfolioViewState.formatPnlInt(value);
  }

  /// 格式化盈亏（整数 + 币种）
  String formatPnlIntWithCurrency(double value, String symbol) {
    return _portfolioViewState.formatPnlIntWithCurrency(value, symbol);
  }

  /// 格式化金额（紧凑：万/亿）
  String formatCompactAmount(
    double value, {
    String prefix = '',
    int decimals = 1,
  }) {
    return _portfolioViewState.formatCompactAmount(
      value,
      prefix: prefix,
      decimals: decimals,
    );
  }

  /// 格式化盈亏（紧凑：万/亿 + 币种）
  String formatCompactPnlWithCurrency(
    double value,
    String symbol, {
    int decimals = 1,
  }) {
    return _portfolioViewState.formatCompactPnlWithCurrency(
      value,
      symbol,
      decimals: decimals,
    );
  }

  /// 格式化盈亏（人民币，紧凑：万/亿，整数）
  String formatCompactPnlCny(double value) {
    return _portfolioViewState.formatCompactPnlCny(value);
  }

  /// 格式化百分比
  String formatPct(double value) {
    return _portfolioViewState.formatPct(value);
  }
}
