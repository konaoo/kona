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

typedef LoginHandler =
    Future<Map<String, dynamic>?> Function({
      required String username,
      required String password,
    });

class _ParsedMarketStatus {
  final Map<String, bool> open;
  final Map<String, bool> tradingDay;

  const _ParsedMarketStatus({required this.open, required this.tradingDay});
}

/// 应用状态管理
class AppState extends ChangeNotifier {
  static const Duration _staticDataTtl = Duration(minutes: 5);
  static const Duration _historyDataTtl = Duration(minutes: 10);
  static const Duration _ratesDataTtl = Duration(minutes: 10);
  static const Duration _syncVersionTtl = Duration(days: 365);
  static const List<String> _syncBootstrapDomains = <String>[
    'portfolio',
    'cash_assets',
    'other_assets',
    'liabilities',
    'history',
    'overview_all',
    'rates',
  ];

  final ApiService _api;
  final CacheService _cache;
  final SecureStorageService _secureStorage;
  final BiometricService _biometric;
  final LoginHandler? _loginHandlerOverride;
  final Future<String?> Function()? _tokenLoaderOverride;
  final Future<Map<String, dynamic>?> Function()? _profileLoaderOverride;
  final Future<Map<String, dynamic>?> Function(String refreshToken)?
  _refreshSessionOverride;

  AppState({
    ApiService? api,
    CacheService? cache,
    SecureStorageService? secureStorage,
    BiometricService? biometric,
    LoginHandler? loginHandler,
    Future<String?> Function()? tokenLoader,
    Future<Map<String, dynamic>?> Function()? profileLoader,
    Future<Map<String, dynamic>?> Function(String refreshToken)? refreshLoader,
  }) : _api = api ?? ApiService(),
       _cache = cache ?? CacheService(),
       _secureStorage = secureStorage ?? SecureStorageService(),
       _biometric = biometric ?? BiometricService(),
       _loginHandlerOverride = loginHandler,
       _tokenLoaderOverride = tokenLoader,
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
  Map<String, PriceInfo> _priceSnapshots = {};
  String _currentCategory = 'all';
  bool _portfolioLoaded = false;

  // 资产列表
  List<Asset> _cashAssets = [];
  List<Asset> _otherAssets = [];
  List<Asset> _liabilities = [];
  int _nextTempAssetId = -1;

  // 汇率
  Map<String, double> _exchangeRates = {'USD': 7.25, 'HKD': 0.93, 'CNY': 1.0};
  Map<String, bool> _marketOpenStatus = const {
    'a': false,
    'hk': false,
    'us': false,
    'fund': false,
  };
  Map<String, bool> _marketTradingDayStatus = const {
    'a': false,
    'hk': false,
    'us': false,
    'fund': false,
  };

  // 历史数据
  double _monthChange = 0;
  double _yearChange = 0;
  double _historyPeak = 0;
  bool _hasMonthBaseline = false;
  bool _hasYearBaseline = false;
  bool _overviewMilestonesReady = false;
  bool _monthFromFirst = false;
  bool _yearFromFirst = false;
  bool _priceRefreshInFlight = false;
  DateTime? _lastPriceRefreshAt;
  static const Duration _priceRefreshMinInterval = Duration(seconds: 2);
  Future<void>? _refreshAllInFlight;
  Future<void>? _refreshByVersionInFlight;
  final Map<String, String> _syncVersions = <String, String>{};
  DateTime? _lastAssetDataUpdatedAt;
  DateTime? _lastQuoteDataUpdatedAt;
  bool _assetDataFromCache = false;
  bool _quoteDataFromCache = false;
  int _quoteIntervalOpenSec = 5;
  int _quoteIntervalClosedSec = 120;
  int _quoteIntervalUsExtendedSec = 10;

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
  Map<String, bool> get marketOpenStatus =>
      Map<String, bool>.from(_marketOpenStatus);
  Map<String, bool> get marketTradingDayStatus =>
      Map<String, bool>.from(_marketTradingDayStatus);
  bool get amountHidden => _amountHidden;
  ThemeMode get themeMode => _themeMode;
  bool get isLightTheme => _themeMode == ThemeMode.light;

  double get monthChange => _monthChange;
  double get yearChange => _yearChange;
  double get historyPeak => _historyPeak;
  bool get hasMonthBaseline => _hasMonthBaseline;
  bool get hasYearBaseline => _hasYearBaseline;
  bool get overviewMilestonesReady => _overviewMilestonesReady;
  bool get monthFromFirst => _monthFromFirst;
  bool get yearFromFirst => _yearFromFirst;
  DateTime? get assetDataUpdatedAt => _lastAssetDataUpdatedAt;
  DateTime? get quoteDataUpdatedAt => _lastQuoteDataUpdatedAt;
  bool get assetDataFromCache => _assetDataFromCache;
  bool get quoteDataFromCache => _quoteDataFromCache;
  int get quoteRefreshIntervalSeconds {
    if (_marketOpenStatus.values.any((open) => open)) {
      return _quoteIntervalOpenSec;
    }
    if (_hasActiveUsExtendedSession()) {
      return _quoteIntervalUsExtendedSec;
    }
    return _quoteIntervalClosedSec;
  }

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

  String _normalizeMarketKey(String? market) {
    final key = (market ?? '').trim().toLowerCase();
    switch (key) {
      case 'a':
      case 'hk':
      case 'us':
      case 'fund':
        return key;
      default:
        return 'a';
    }
  }

  bool isMarketOpen(String? market) {
    return _marketOpenStatus[_normalizeMarketKey(market)] ?? false;
  }

  bool isMarketTradingDay(String? market) {
    return _marketTradingDayStatus[_normalizeMarketKey(market)] ?? false;
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

  bool isAssetDayPnlDisplayEnabled(PortfolioItem item, {PriceInfo? priceInfo}) {
    final resolved = resolvePriceInfo(item, preferred: priceInfo);
    return resolved != null && resolved.yclose > 0;
  }

  bool isAssetDayPnlEnabled(PortfolioItem item, {PriceInfo? priceInfo}) {
    final resolved = resolvePriceInfo(item, preferred: priceInfo);
    if (resolved == null || resolved.yclose <= 0) return false;
    if (isAssetTradingDay(item)) return true;
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
      final priceInfo = resolvePriceInfo(item);
      final currentPrice = priceInfo?.price ?? item.price;
      final rate = _rateForCurrency(item.curr);
      total += currentPrice * item.qty * rate;
    }
    return total;
  }

  /// 投资今日盈亏
  double get investDayPnl {
    double total = 0;
    for (var item in _portfolio) {
      final priceInfo = resolvePriceInfo(item);
      if (!isAssetDayPnlEnabled(item, priceInfo: priceInfo)) continue;
      if (priceInfo != null) {
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
      final priceInfo = resolvePriceInfo(item);
      if (!isAssetDayPnlEnabled(item, priceInfo: priceInfo)) continue;
      if (priceInfo != null) {
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
      final priceInfo = resolvePriceInfo(item);
      final currentPrice = priceInfo?.price ?? item.price;
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

  static const Map<String, String> _legacyCacheKeys = {
    'portfolio': 'cache_portfolio',
    'cash_assets': 'cache_cash_assets',
    'other_assets': 'cache_other_assets',
    'liabilities': 'cache_liabilities',
    'prices': 'cache_prices',
    'market_status': 'cache_market_status',
    'history': 'cache_history',
    'analysis_overview': 'cache_analysis_overview',
    'exchange_rates': 'cache_exchange_rates',
  };

  List<String> _cacheScopes({bool includeGuestForAnonymous = true}) {
    final scopes = <String>[];
    final uname = (_username ?? '').trim().toLowerCase();
    final uid = (_userId ?? '').trim();
    if (uname.isNotEmpty) scopes.add('name:$uname');
    if (uid.isNotEmpty && !scopes.contains(uid)) scopes.add(uid);
    if (scopes.isEmpty && includeGuestForAnonymous) scopes.add('guest');
    return scopes;
  }

  String _cachePrimaryScope() {
    final scopes = _cacheScopes();
    return scopes.isEmpty ? 'guest' : scopes.first;
  }

  String _cacheKeyForScope(String scope, String domain) => 'u:$scope:$domain';

  Map<String, dynamic> _asMap(dynamic value) {
    if (value is Map<String, dynamic>) return value;
    if (value is Map) return Map<String, dynamic>.from(value);
    return <String, dynamic>{};
  }

  int _asInt(dynamic value) {
    if (value is int) return value;
    if (value is num) return value.toInt();
    if (value is String) return int.tryParse(value.trim()) ?? 0;
    return 0;
  }

  DateTime? _envelopeSavedAt(Map<String, dynamic>? envelope) {
    if (envelope == null) return null;
    final savedAtMs = _asInt(envelope['saved_at_ms']);
    if (savedAtMs <= 0) return null;
    return DateTime.fromMillisecondsSinceEpoch(savedAtMs);
  }

  Map<String, dynamic>? _normalizeEnvelope(Map<String, dynamic>? raw) {
    if (raw == null) return null;
    final hasEnvelopeFields =
        raw.containsKey('data') && raw.containsKey('saved_at_ms');
    if (hasEnvelopeFields) return raw;
    return <String, dynamic>{
      'user_id': _cachePrimaryScope(),
      'version': '',
      'saved_at_ms': 0,
      'stale_after_ms': 0,
      'data': raw,
    };
  }

  Map<String, dynamic> _buildEnvelope({
    required dynamic data,
    String? version,
    required Duration staleAfter,
  }) {
    return <String, dynamic>{
      'user_id': _cachePrimaryScope(),
      'version': (version ?? '').trim(),
      'saved_at_ms': DateTime.now().millisecondsSinceEpoch,
      'stale_after_ms': staleAfter.inMilliseconds,
      'data': data,
    };
  }

  Future<Map<String, dynamic>?> _loadDomainEnvelope(String domain) async {
    final scopes = _cacheScopes();
    for (final scope in scopes) {
      final scoped = _normalizeEnvelope(
        await _cache.getJson(_cacheKeyForScope(scope, domain)),
      );
      if (scoped != null) return scoped;
    }
    final legacyKey = _legacyCacheKeys[domain];
    if (legacyKey == null) return null;
    return _normalizeEnvelope(await _cache.getJson(legacyKey));
  }

  Future<void> _saveDomainEnvelope(
    String domain, {
    required dynamic data,
    String? version,
    required Duration staleAfter,
  }) async {
    final envelope = _buildEnvelope(
      data: data,
      version: version,
      staleAfter: staleAfter,
    );
    for (final scope in _cacheScopes()) {
      await _cache.setJson(_cacheKeyForScope(scope, domain), envelope);
    }
  }

  Future<void> _loadSyncVersionsFromCache() async {
    final envelope = await _loadDomainEnvelope('sync_versions');
    final payload = _asMap(envelope?['data']);
    final versions = _asMap(payload['versions']);
    if (versions.isEmpty) return;
    _syncVersions
      ..clear()
      ..addAll(
        versions.map((k, v) => MapEntry(k.toString(), (v ?? '').toString())),
      );
  }

  Future<void> _saveSyncVersionsToCache() async {
    if (_syncVersions.isEmpty) return;
    await _saveDomainEnvelope(
      'sync_versions',
      data: <String, dynamic>{
        'versions': Map<String, String>.from(_syncVersions),
      },
      staleAfter: _syncVersionTtl,
    );
  }

  Future<void> hydrateFromCache() async {
    await _loadSyncVersionsFromCache();

    DateTime? assetSavedAt;
    DateTime? quoteSavedAt;
    bool hasAssetCache = false;
    bool hasQuoteCache = false;

    DateTime? mergeLatest(DateTime? current, DateTime? next) {
      if (next == null) return current;
      if (current == null) return next;
      return next.isAfter(current) ? next : current;
    }

    final portfolioEnvelope = await _loadDomainEnvelope('portfolio');
    final cachedPortfolio = _asMap(portfolioEnvelope?['data']);
    if (cachedPortfolio['items'] is List) {
      _portfolio = (cachedPortfolio['items'] as List)
          .map((e) => PortfolioItem.fromJson(e))
          .toList();
      hasAssetCache = true;
      assetSavedAt = mergeLatest(
        assetSavedAt,
        _envelopeSavedAt(portfolioEnvelope),
      );
      final cachedVersion = '${portfolioEnvelope?['version'] ?? ''}'.trim();
      if (cachedVersion.isNotEmpty) _syncVersions['portfolio'] = cachedVersion;
    }

    final cashEnvelope = await _loadDomainEnvelope('cash_assets');
    final cachedCash = _asMap(cashEnvelope?['data']);
    if (cachedCash['items'] is List) {
      _cashAssets = (cachedCash['items'] as List)
          .map((e) => Asset.fromJson(e))
          .toList();
      hasAssetCache = true;
      assetSavedAt = mergeLatest(assetSavedAt, _envelopeSavedAt(cashEnvelope));
      final cachedVersion = '${cashEnvelope?['version'] ?? ''}'.trim();
      if (cachedVersion.isNotEmpty) {
        _syncVersions['cash_assets'] = cachedVersion;
      }
    }

    final otherEnvelope = await _loadDomainEnvelope('other_assets');
    final cachedOther = _asMap(otherEnvelope?['data']);
    if (cachedOther['items'] is List) {
      _otherAssets = (cachedOther['items'] as List)
          .map((e) => Asset.fromJson(e))
          .toList();
      hasAssetCache = true;
      assetSavedAt = mergeLatest(assetSavedAt, _envelopeSavedAt(otherEnvelope));
      final cachedVersion = '${otherEnvelope?['version'] ?? ''}'.trim();
      if (cachedVersion.isNotEmpty) {
        _syncVersions['other_assets'] = cachedVersion;
      }
    }

    final liabilitiesEnvelope = await _loadDomainEnvelope('liabilities');
    final cachedLiabilities = _asMap(liabilitiesEnvelope?['data']);
    if (cachedLiabilities['items'] is List) {
      _liabilities = (cachedLiabilities['items'] as List)
          .map((e) => Asset.fromJson(e))
          .toList();
      hasAssetCache = true;
      assetSavedAt = mergeLatest(
        assetSavedAt,
        _envelopeSavedAt(liabilitiesEnvelope),
      );
      final cachedVersion = '${liabilitiesEnvelope?['version'] ?? ''}'.trim();
      if (cachedVersion.isNotEmpty) {
        _syncVersions['liabilities'] = cachedVersion;
      }
    }

    final pricesEnvelope = await _loadDomainEnvelope('prices');
    final cachedPrices = _asMap(pricesEnvelope?['data']);
    if (cachedPrices['items'] is Map) {
      _prices = {};
      (cachedPrices['items'] as Map).forEach((key, value) {
        if (value is Map<String, dynamic>) {
          _prices[key.toString()] = PriceInfo.fromJson(value);
        }
      });
      hasQuoteCache = true;
      quoteSavedAt = mergeLatest(
        quoteSavedAt,
        _envelopeSavedAt(pricesEnvelope),
      );
    }

    final snapshotEnvelope = await _loadDomainEnvelope('price_snapshots');
    final cachedSnapshots = _asMap(snapshotEnvelope?['data']);
    if (cachedSnapshots['items'] is Map) {
      _priceSnapshots = {};
      (cachedSnapshots['items'] as Map).forEach((key, value) {
        if (value is Map<String, dynamic>) {
          _priceSnapshots[key.toString()] = PriceInfo.fromJson(value);
        }
      });
      hasQuoteCache = true;
      quoteSavedAt = mergeLatest(
        quoteSavedAt,
        _envelopeSavedAt(snapshotEnvelope),
      );
    } else if (_prices.isNotEmpty) {
      _priceSnapshots = Map<String, PriceInfo>.from(_prices);
    }
    if (_prices.isEmpty && _priceSnapshots.isNotEmpty) {
      _prices = Map<String, PriceInfo>.from(_priceSnapshots);
    }

    final marketStatusEnvelope = await _loadDomainEnvelope('market_status');
    final cachedMarketStatus = _asMap(marketStatusEnvelope?['data']);
    if (cachedMarketStatus.isNotEmpty) {
      final parsedStatus = _parseMarketStatus(cachedMarketStatus);
      _marketOpenStatus = parsedStatus.open;
      _marketTradingDayStatus = parsedStatus.tradingDay;
      hasQuoteCache = true;
      quoteSavedAt = mergeLatest(
        quoteSavedAt,
        _envelopeSavedAt(marketStatusEnvelope),
      );
    }

    final historyEnvelope = await _loadDomainEnvelope('history');
    final cachedHistory = _asMap(historyEnvelope?['data']);
    if (cachedHistory['items'] is List) {
      _calculateHistoryStats(cachedHistory['items'] as List);
      hasAssetCache = true;
      assetSavedAt = mergeLatest(
        assetSavedAt,
        _envelopeSavedAt(historyEnvelope),
      );
      final cachedVersion = '${historyEnvelope?['version'] ?? ''}'.trim();
      if (cachedVersion.isNotEmpty) _syncVersions['history'] = cachedVersion;
    }
    final overviewEnvelope = await _loadDomainEnvelope('analysis_overview');
    final cachedOverview = _asMap(overviewEnvelope?['data']);
    if (cachedOverview['data'] is Map) {
      applyOverviewMilestones(
        Map<String, dynamic>.from(cachedOverview['data'] as Map),
      );
      hasAssetCache = true;
      assetSavedAt = mergeLatest(
        assetSavedAt,
        _envelopeSavedAt(overviewEnvelope),
      );
      final cachedVersion = '${overviewEnvelope?['version'] ?? ''}'.trim();
      if (cachedVersion.isNotEmpty) {
        _syncVersions['overview_all'] = cachedVersion;
      }
    } else if (cachedOverview.isNotEmpty) {
      applyOverviewMilestones(cachedOverview);
      hasAssetCache = true;
      assetSavedAt = mergeLatest(
        assetSavedAt,
        _envelopeSavedAt(overviewEnvelope),
      );
    }

    final ratesEnvelope = await _loadDomainEnvelope('exchange_rates');
    final cachedRates = _asMap(ratesEnvelope?['data']);
    if (cachedRates['rates'] is Map) {
      updateExchangeRates(cachedRates['rates'] as Map<String, dynamic>);
      hasAssetCache = true;
      assetSavedAt = mergeLatest(assetSavedAt, _envelopeSavedAt(ratesEnvelope));
      final cachedVersion = '${ratesEnvelope?['version'] ?? ''}'.trim();
      if (cachedVersion.isNotEmpty) _syncVersions['rates'] = cachedVersion;
    }

    // recompute totals
    _totalCash = _cashAssets.fold(0, (sum, item) => sum + item.amount);
    _totalOther = _otherAssets.fold(0, (sum, item) => sum + item.amount);
    _totalLiability = _liabilities.fold(0, (sum, item) => sum + item.amount);
    _totalInvest = investTotalMV;
    _totalAsset = _totalCash + _totalInvest + _totalOther - _totalLiability;

    _portfolioLoaded = _portfolio.isNotEmpty || _cashAssets.isNotEmpty;
    if (hasAssetCache) {
      _assetDataFromCache = true;
      if (assetSavedAt != null) {
        _lastAssetDataUpdatedAt = assetSavedAt;
      }
    }
    if (hasQuoteCache) {
      _quoteDataFromCache = true;
      if (quoteSavedAt != null) {
        _lastQuoteDataUpdatedAt = quoteSavedAt;
      }
    }
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
    await _saveDomainEnvelope(
      'portfolio',
      data: <String, dynamic>{
        'items': _portfolio.map((e) => e.toJson()).toList(),
      },
      version: _syncVersions['portfolio'],
      staleAfter: _staticDataTtl,
    );
  }

  Map<String, dynamic> _serializePriceItems(Map<String, PriceInfo> source) {
    return source.map(
      (key, value) => MapEntry(key, {
        'price': value.price,
        'yclose': value.yclose,
        'amt': value.change,
        'chg': value.changePct,
        'regular_price': value.regularPrice,
        'premarket_price': value.premarketPrice,
        'after_hours_price': value.afterHoursPrice,
        'session': value.session,
        'effective_session': value.effectiveSession,
        'extended_active': value.extendedActive,
      }),
    );
  }

  Future<void> saveHomeCache(
    List<dynamic> history, {
    Map<String, dynamic>? overview,
  }) async {
    await _saveDomainEnvelope(
      'portfolio',
      data: <String, dynamic>{
        'items': _portfolio.map((e) => e.toJson()).toList(),
      },
      version: _syncVersions['portfolio'],
      staleAfter: _staticDataTtl,
    );
    await _saveDomainEnvelope(
      'cash_assets',
      data: <String, dynamic>{
        'items': _cashAssets.map((e) => e.toJson()).toList(),
      },
      version: _syncVersions['cash_assets'],
      staleAfter: _staticDataTtl,
    );
    await _saveDomainEnvelope(
      'other_assets',
      data: <String, dynamic>{
        'items': _otherAssets.map((e) => e.toJson()).toList(),
      },
      version: _syncVersions['other_assets'],
      staleAfter: _staticDataTtl,
    );
    await _saveDomainEnvelope(
      'liabilities',
      data: <String, dynamic>{
        'items': _liabilities.map((e) => e.toJson()).toList(),
      },
      version: _syncVersions['liabilities'],
      staleAfter: _staticDataTtl,
    );
    await _saveDomainEnvelope(
      'history',
      data: <String, dynamic>{'items': history},
      version: _syncVersions['history'],
      staleAfter: _historyDataTtl,
    );
    await _saveDomainEnvelope(
      'exchange_rates',
      data: <String, dynamic>{'rates': _exchangeRates},
      version: _syncVersions['rates'],
      staleAfter: _ratesDataTtl,
    );
    await _saveDomainEnvelope(
      'prices',
      data: <String, dynamic>{'items': _serializePriceItems(_prices)},
      staleAfter: _staticDataTtl,
    );
    await _saveDomainEnvelope(
      'price_snapshots',
      data: <String, dynamic>{'items': _serializePriceItems(_priceSnapshots)},
      staleAfter: _syncVersionTtl,
    );
    if (overview != null && overview.isNotEmpty) {
      await _saveDomainEnvelope(
        'analysis_overview',
        data: <String, dynamic>{'data': overview},
        version: _syncVersions['overview_all'],
        staleAfter: _historyDataTtl,
      );
    }
    await _saveSyncVersionsToCache();
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
    notifyListeners();

    try {
      await _secureStorage.setToken(accessToken);
      await _secureStorage.setRefreshToken(refreshToken);
      if (_username != null && _username!.isNotEmpty) {
        await _secureStorage.setUsername(_username!);
      }
      await _secureStorage.clearLogoutMode();
    } catch (e) {
      debugPrint('登录态写入本地存储失败，已保留内存登录态: $e');
    }
  }

  void clearAuthError() {
    _authErrorMessage = null;
  }

  static const Map<String, bool> _fallbackMarketOpenStatus = {
    'a': false,
    'hk': false,
    'us': false,
    'fund': false,
  };
  static const Map<String, bool> _fallbackMarketTradingDayStatus = {
    'a': false,
    'hk': false,
    'us': false,
    'fund': false,
  };

  bool _asBool(dynamic value) {
    if (value is bool) return value;
    if (value is num) return value != 0;
    if (value is String) {
      final lower = value.trim().toLowerCase();
      return lower == '1' || lower == 'true' || lower == 'yes';
    }
    return false;
  }

  bool _hasMarketStatusPayload(dynamic raw) {
    final map = _asMap(raw);
    if (map.isEmpty) return false;
    final markets = map['markets'];
    if (markets is Map && markets.isNotEmpty) return true;
    return map.containsKey('a') ||
        map.containsKey('hk') ||
        map.containsKey('us') ||
        map.containsKey('fund');
  }

  bool _inferTradingDay({required bool open, required String reason}) {
    if (open) return true;
    switch (reason.trim().toLowerCase()) {
      case 'holiday_or_weekend':
        return false;
      case 'off_hours':
      case 'open_session':
        return true;
      case 'override':
        return false;
      default:
        return open;
    }
  }

  _ParsedMarketStatus _parseMarketStatus(
    dynamic payload, {
    Map<String, bool>? openFallback,
  }) {
    final root = _asMap(payload);
    final dynamic marketsRaw = root['markets'] ?? payload;
    final markets = marketsRaw is Map
        ? Map<String, dynamic>.from(marketsRaw)
        : <String, dynamic>{};

    bool parseOpenNode(String key) {
      if (markets.isNotEmpty && markets.containsKey(key)) {
        final node = markets[key];
        if (node is Map) {
          return _asBool(node['open']);
        }
        return _asBool(node);
      }
      return openFallback?[key] ?? _fallbackMarketOpenStatus[key]!;
    }

    bool parseTradingDayNode(String key, bool open) {
      if (markets.isNotEmpty && markets.containsKey(key)) {
        final node = markets[key];
        if (node is Map) {
          if (node.containsKey('trading_day')) {
            return _asBool(node['trading_day']);
          }
          final reason = '${node['reason'] ?? ''}';
          if (reason.trim().isNotEmpty) {
            return _inferTradingDay(open: open, reason: reason);
          }
          return open;
        }
        return _asBool(node);
      }
      return open;
    }

    final open = {
      'a': parseOpenNode('a'),
      'hk': parseOpenNode('hk'),
      'us': parseOpenNode('us'),
      'fund': parseOpenNode('fund'),
    };
    final tradingDay = {
      'a': parseTradingDayNode('a', open['a'] ?? false),
      'hk': parseTradingDayNode('hk', open['hk'] ?? false),
      'us': parseTradingDayNode('us', open['us'] ?? false),
      'fund': parseTradingDayNode('fund', open['fund'] ?? false),
    };
    return _ParsedMarketStatus(open: open, tradingDay: tradingDay);
  }

  Map<String, dynamic> _serializeMarketStatusForCache() {
    return <String, dynamic>{
      'markets': {
        'a': {
          'open': _marketOpenStatus['a'] ?? false,
          'trading_day': _marketTradingDayStatus['a'] ?? false,
        },
        'hk': {
          'open': _marketOpenStatus['hk'] ?? false,
          'trading_day': _marketTradingDayStatus['hk'] ?? false,
        },
        'us': {
          'open': _marketOpenStatus['us'] ?? false,
          'trading_day': _marketTradingDayStatus['us'] ?? false,
        },
        'fund': {
          'open': _marketOpenStatus['fund'] ?? false,
          'trading_day': _marketTradingDayStatus['fund'] ?? false,
        },
      },
    };
  }

  Future<_ParsedMarketStatus> _loadMarketStatusSafe() async {
    try {
      final markets = await _api.getMarketStatuses();
      return _parseMarketStatus(markets);
    } catch (e) {
      debugPrint('读取市场状态失败，按全休市降级: $e');
      return _ParsedMarketStatus(
        open: Map<String, bool>.from(_fallbackMarketOpenStatus),
        tradingDay: Map<String, bool>.from(_fallbackMarketTradingDayStatus),
      );
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
    final raw = error.toString().trim();
    if (raw.isNotEmpty) {
      final normalized = raw.startsWith('Exception:')
          ? raw.replaceFirst('Exception:', '').trim()
          : raw;
      final lower = normalized.toLowerCase();
      if (_isWebStorageRuntimeError(lower)) {
        return '浏览器存储环境异常，请刷新页面或切换 HTTPS 后重试';
      }
      return normalized;
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
      final result = _loginHandlerOverride != null
          ? await _loginHandlerOverride(username: username, password: password)
          : await _api.login(username: username, password: password);
      if (result == null) {
        _authErrorMessage = '登录响应为空，请稍后重试';
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
    _priceSnapshots = {};
    _cashAssets = [];
    _otherAssets = [];
    _liabilities = [];
    _syncVersions.clear();
    _lastAssetDataUpdatedAt = null;
    _lastQuoteDataUpdatedAt = null;
    _assetDataFromCache = false;
    _quoteDataFromCache = false;
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
    if (_tokenLoaderOverride != null) {
      try {
        token = await _tokenLoaderOverride();
      } catch (e) {
        debugPrint('读取 access token 失败: $e');
      }
    } else {
      token = await _safeReadStorageString(
        _secureStorage.getToken,
        'access token',
      );
    }
    refreshToken = await _safeReadStorageString(
      _secureStorage.getRefreshToken,
      'refresh token',
    );
    username = await _safeReadStorageString(
      _secureStorage.getUsername,
      'username',
    );
    _biometricEnabled = await _safeReadStorageBool(
      _secureStorage.isBiometricEnabled,
      'biometric enabled',
    );
    logoutModeRaw = await _safeReadStorageString(
      _secureStorage.getLogoutMode,
      'logout mode',
    );

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
          unawaited(hydrateFromCache());
          unawaited(refreshAll());
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
    unawaited(hydrateFromCache());
    unawaited(refreshAll());
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
    _syncVersions.clear();
    _priceSnapshots = {};
    _marketOpenStatus = Map<String, bool>.from(_fallbackMarketOpenStatus);
    _marketTradingDayStatus = Map<String, bool>.from(
      _fallbackMarketTradingDayStatus,
    );
    _lastAssetDataUpdatedAt = null;
    _lastQuoteDataUpdatedAt = null;
    _assetDataFromCache = false;
    _quoteDataFromCache = false;
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

  int _positiveInt(dynamic value, {required int fallback}) {
    final parsed = _asInt(value);
    return parsed > 0 ? parsed : fallback;
  }

  void _applyQuotePolicy(dynamic rawPolicy) {
    final policy = _asMap(rawPolicy);
    if (policy.isEmpty) return;
    _quoteIntervalOpenSec = _positiveInt(
      policy['interval_open_sec'],
      fallback: _quoteIntervalOpenSec,
    );
    _quoteIntervalClosedSec = _positiveInt(
      policy['interval_closed_sec'],
      fallback: _quoteIntervalClosedSec,
    );
    _quoteIntervalUsExtendedSec = _positiveInt(
      policy['interval_us_extended_sec'],
      fallback: _quoteIntervalUsExtendedSec,
    );
  }

  Map<String, bool> _parseMarketOpenFallback(dynamic raw) {
    final status = _asMap(raw);
    if (status.isEmpty) {
      return Map<String, bool>.from(_fallbackMarketOpenStatus);
    }
    return {
      'a': _asBool(status['a']),
      'hk': _asBool(status['hk']),
      'us': _asBool(status['us']),
      'fund': _asBool(status['fund']),
    };
  }

  void _applySyncMarketStatus(dynamic rawStatuses, {dynamic rawOpenFallback}) {
    if (!_hasMarketStatusPayload(rawStatuses) &&
        !_hasMarketStatusPayload(rawOpenFallback)) {
      return;
    }
    final parsed = _parseMarketStatus(
      rawStatuses,
      openFallback: _parseMarketOpenFallback(rawOpenFallback),
    );
    _marketOpenStatus = parsed.open;
    _marketTradingDayStatus = parsed.tradingDay;
  }

  void _recalculateHomeTotals() {
    _totalCash = _cashAssets.fold(0, (sum, item) => sum + item.amount);
    _totalOther = _otherAssets.fold(0, (sum, item) => sum + item.amount);
    _totalLiability = _liabilities.fold(0, (sum, item) => sum + item.amount);
    _totalInvest = investTotalMV;
    _totalAsset = _totalCash + _totalInvest + _totalOther - _totalLiability;
    _portfolioLoaded = _portfolio.isNotEmpty || _cashAssets.isNotEmpty;
  }

  bool _canSkipStaticSyncCheck({required bool force}) {
    if (force) return false;
    if (_syncVersions.isEmpty) return false;
    final lastAt = _lastAssetDataUpdatedAt;
    if (lastAt == null) return false;
    return DateTime.now().difference(lastAt) < _staticDataTtl;
  }

  /// 刷新首页数据（全量）
  /// 刷新首页数据
  Future<void> refreshHomeData() async {
    try {
      // 核心数据优先返回，避免被慢行情阻塞。
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

      // 计算总额（必须在历史数据计算之前）
      _recalculateHomeTotals();

      // 处理历史数据（必须在总资产计算之后）
      final history = results[4] as List;
      final overview = (results[5] as Map?)?.cast<String, dynamic>();
      _calculateHistoryStats(history);
      applyOverviewMilestones(overview);

      await saveHomeCache(history, overview: overview);
      _assetDataFromCache = false;
      _lastAssetDataUpdatedAt = DateTime.now();

      _portfolioLoaded = true;
      notifyListeners();

      // 行情慢时后台更新，不影响首页收益首屏展示。
      unawaited(_refreshPortfolioPricesInBackground(force: true));
    } catch (e) {
      debugPrint('刷新首页数据失败: $e');
    }
  }

  Future<void> _applySyncDomainData({
    required String domain,
    required dynamic payload,
  }) async {
    if (domain == 'portfolio') {
      final list = (payload is List) ? payload : const <dynamic>[];
      _portfolio = list.map((e) => PortfolioItem.fromJson(e)).toList();
      final validCodes = _portfolio.map((e) => e.code).toSet();
      _prices.removeWhere((code, _) => !validCodes.contains(code));
      _priceSnapshots.removeWhere((code, _) => !validCodes.contains(code));
      _recalculateHomeTotals();
      await _saveDomainEnvelope(
        'portfolio',
        data: <String, dynamic>{
          'items': _portfolio.map((e) => e.toJson()).toList(),
        },
        version: _syncVersions['portfolio'],
        staleAfter: _staticDataTtl,
      );
      return;
    }
    if (domain == 'cash_assets') {
      final list = (payload is List) ? payload : const <dynamic>[];
      _cashAssets = list.map((e) => Asset.fromJson(e)).toList();
      _recalculateHomeTotals();
      await _saveDomainEnvelope(
        'cash_assets',
        data: <String, dynamic>{
          'items': _cashAssets.map((e) => e.toJson()).toList(),
        },
        version: _syncVersions['cash_assets'],
        staleAfter: _staticDataTtl,
      );
      return;
    }
    if (domain == 'other_assets') {
      final list = (payload is List) ? payload : const <dynamic>[];
      _otherAssets = list.map((e) => Asset.fromJson(e)).toList();
      _recalculateHomeTotals();
      await _saveDomainEnvelope(
        'other_assets',
        data: <String, dynamic>{
          'items': _otherAssets.map((e) => e.toJson()).toList(),
        },
        version: _syncVersions['other_assets'],
        staleAfter: _staticDataTtl,
      );
      return;
    }
    if (domain == 'liabilities') {
      final list = (payload is List) ? payload : const <dynamic>[];
      _liabilities = list.map((e) => Asset.fromJson(e)).toList();
      _recalculateHomeTotals();
      await _saveDomainEnvelope(
        'liabilities',
        data: <String, dynamic>{
          'items': _liabilities.map((e) => e.toJson()).toList(),
        },
        version: _syncVersions['liabilities'],
        staleAfter: _staticDataTtl,
      );
      return;
    }
    if (domain == 'history') {
      final history = (payload is List) ? payload : const <dynamic>[];
      _calculateHistoryStats(history);
      await _saveDomainEnvelope(
        'history',
        data: <String, dynamic>{'items': history},
        version: _syncVersions['history'],
        staleAfter: _historyDataTtl,
      );
      return;
    }
    if (domain == 'overview_all') {
      final overview = _asMap(payload);
      applyOverviewMilestones(overview);
      await _saveDomainEnvelope(
        'analysis_overview',
        data: <String, dynamic>{'data': overview},
        version: _syncVersions['overview_all'],
        staleAfter: _historyDataTtl,
      );
      return;
    }
    if (domain == 'rates') {
      final rates = _asMap(payload);
      if (rates.isNotEmpty) {
        updateExchangeRates(rates);
      }
      await _saveDomainEnvelope(
        'exchange_rates',
        data: <String, dynamic>{'rates': _exchangeRates},
        version: _syncVersions['rates'],
        staleAfter: _ratesDataTtl,
      );
    }
  }

  /// 按版本增量刷新，失败时自动回退全量刷新。
  Future<void> refreshByVersion({
    bool force = false,
    bool refreshQuotes = true,
  }) async {
    final existing = _refreshByVersionInFlight;
    if (existing != null) return existing;

    final future = _refreshByVersionInternal(
      force: force,
      refreshQuotes: refreshQuotes,
    );
    _refreshByVersionInFlight = future;
    try {
      await future;
    } finally {
      _refreshByVersionInFlight = null;
    }
  }

  Future<void> _refreshByVersionInternal({
    required bool force,
    required bool refreshQuotes,
  }) async {
    if (_canSkipStaticSyncCheck(force: force)) {
      if (refreshQuotes) {
        await _refreshPortfolioPricesInBackground(force: true);
      }
      return;
    }

    try {
      final response = await _api.getSyncBootstrap(
        include: _syncBootstrapDomains,
        clientVersions: force
            ? const <String, String>{}
            : Map<String, String>.from(_syncVersions),
      );
      _applyQuotePolicy(response['quote_policy']);
      _applySyncMarketStatus(
        response['market_statuses'],
        rawOpenFallback: response['market_status'],
      );

      final versions = _asMap(response['versions']);
      if (versions.isNotEmpty) {
        _syncVersions.addAll(
          versions.map((k, v) => MapEntry(k.toString(), (v ?? '').toString())),
        );
        await _saveSyncVersionsToCache();
      }

      final changedRaw = response['changed'];
      final changed = <String>[];
      if (changedRaw is List) {
        for (final item in changedRaw) {
          final key = '$item'.trim();
          if (key.isNotEmpty) changed.add(key);
        }
      }
      final data = _asMap(response['data']);

      bool staticChanged = false;
      for (final domain in changed) {
        await _applySyncDomainData(domain: domain, payload: data[domain]);
        if (domain != 'rates') {
          staticChanged = true;
        }
      }

      await _saveDomainEnvelope(
        'market_status',
        data: _serializeMarketStatusForCache(),
        staleAfter: _staticDataTtl,
      );

      if (staticChanged || changed.contains('rates')) {
        _assetDataFromCache = false;
        _lastAssetDataUpdatedAt = DateTime.now();
      }
      if (changed.isNotEmpty) {
        notifyListeners();
      }
    } catch (e) {
      debugPrint('版本增量刷新失败，降级全量刷新: $e');
      await Future.wait([refreshHomeData(), loadExchangeRates()]);
    }

    if (refreshQuotes) {
      await _refreshPortfolioPricesInBackground(force: true);
    }
  }

  /// 用分析概览覆盖首页里程碑（月/年改为收益口径）。
  /// 若接口数据异常则保留历史差值口径结果（回退行为）。
  void applyOverviewMilestones(Map<String, dynamic>? overview) {
    final data = overview ?? const <String, dynamic>{};
    final month = data['month'];
    final year = data['year'];
    double? extractPnl(dynamic node) {
      if (node is! Map) return null;
      final raw = node['pnl'];
      if (raw is num) return raw.toDouble();
      if (raw is String) return double.tryParse(raw.trim());
      return null;
    }

    final monthPnl = extractPnl(month);
    final yearPnl = extractPnl(year);
    _overviewMilestonesReady = monthPnl != null || yearPnl != null;
    debugPrint('分析概览覆盖: monthPnl=$monthPnl, yearPnl=$yearPnl, raw=$data');
    if (monthPnl != null) _monthChange = monthPnl;
    if (yearPnl != null) _yearChange = yearPnl;
  }

  Future<void> _refreshPortfolioPricesInBackground({bool force = false}) async {
    final now = DateTime.now();
    if (_priceRefreshInFlight) return;
    if (!force &&
        _lastPriceRefreshAt != null &&
        now.difference(_lastPriceRefreshAt!) < _priceRefreshMinInterval) {
      return;
    }
    _priceRefreshInFlight = true;
    try {
      final marketStatus = await _loadMarketStatusSafe();
      _marketOpenStatus = marketStatus.open;
      _marketTradingDayStatus = marketStatus.tradingDay;
      if (_portfolio.isEmpty) {
        await _saveDomainEnvelope(
          'market_status',
          data: _serializeMarketStatusForCache(),
          staleAfter: _staticDataTtl,
        );
        // 启动早期持仓尚未恢复时，避免把已有价格缓存清空写回。
        if (_portfolioLoaded) {
          _prices = {};
          _priceSnapshots = {};
          _totalInvest = 0;
          _totalAsset = _totalCash + _totalOther - _totalLiability;
          await _saveDomainEnvelope(
            'prices',
            data: <String, dynamic>{'items': <String, dynamic>{}},
            staleAfter: _staticDataTtl,
          );
          await _saveDomainEnvelope(
            'price_snapshots',
            data: <String, dynamic>{'items': <String, dynamic>{}},
            staleAfter: _syncVersionTtl,
          );
          _quoteDataFromCache = false;
          _lastQuoteDataUpdatedAt = DateTime.now();
          notifyListeners();
        }
        return;
      }

      final codes = _portfolio.map((e) => e.code).toList();
      final previousPrices = Map<String, PriceInfo>.from(_prices);
      final priceApiCodes = codes.map((code) {
        if (code.startsWith('gb_')) {
          return code.substring(3);
        }
        return code;
      }).toList();

      final pricesData = await _api.getPricesBatch(priceApiCodes);
      final nextPrices = <String, PriceInfo>{};
      for (int i = 0; i < codes.length; i++) {
        final originalCode = codes[i];
        final apiCode = priceApiCodes[i];
        PriceInfo? parsed;
        if (pricesData.containsKey(apiCode)) {
          try {
            parsed = PriceInfo.fromJson(pricesData[apiCode]);
          } catch (e) {
            debugPrint('解析价格失败: $originalCode (API: $apiCode), 错误: $e');
          }
        }
        final resolved = _resolvePriceInfoByCode(
          originalCode,
          preferred: parsed,
          runtimeFallback: previousPrices,
        );
        if (resolved != null) {
          nextPrices[originalCode] = resolved;
        }
      }

      _prices = nextPrices;
      _priceSnapshots = Map<String, PriceInfo>.from(_priceSnapshots)
        ..removeWhere((code, _) => !codes.contains(code))
        ..addAll(nextPrices);
      _totalInvest = investTotalMV;
      _totalAsset = _totalCash + _totalInvest + _totalOther - _totalLiability;
      await _saveDomainEnvelope(
        'market_status',
        data: _serializeMarketStatusForCache(),
        staleAfter: _staticDataTtl,
      );
      await _saveDomainEnvelope(
        'prices',
        data: <String, dynamic>{'items': _serializePriceItems(_prices)},
        staleAfter: _staticDataTtl,
      );
      await _saveDomainEnvelope(
        'price_snapshots',
        data: <String, dynamic>{'items': _serializePriceItems(_priceSnapshots)},
        staleAfter: _syncVersionTtl,
      );
      _quoteDataFromCache = false;
      _lastQuoteDataUpdatedAt = DateTime.now();
      notifyListeners();
    } catch (e) {
      debugPrint('后台刷新行情失败: $e');
    } finally {
      _priceRefreshInFlight = false;
      _lastPriceRefreshAt = DateTime.now();
    }
  }

  /// 仅刷新行情价格（用于定时更新今日盈亏/现价）
  Future<void> refreshPricesOnly() async {
    await _refreshPortfolioPricesInBackground(force: true);
  }

  /// 刷新所有核心数据（用于启动与下拉刷新）
  Future<void> refreshAll({bool force = false}) async {
    final existing = _refreshAllInFlight;
    if (existing != null) return existing;

    final future = _refreshAllInternal(force: force);
    _refreshAllInFlight = future;
    try {
      await future;
    } finally {
      _refreshAllInFlight = null;
    }
  }

  Future<void> _refreshAllInternal({required bool force}) async {
    if (force) {
      await Future.wait([refreshHomeData(), loadExchangeRates()]);
      await _refreshPortfolioPricesInBackground(force: true);
      return;
    }
    await refreshByVersion(force: false, refreshQuotes: true);
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
      data: {...data, 'undo_token': token, 'undo_expire_at': expire},
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

    final cashIndex = _cashAssets.indexWhere(
      (asset) => asset.id == cashAssetId,
    );
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
    final cashIndex = _cashAssets.indexWhere(
      (asset) => asset.id == cashAssetId,
    );
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
    _overviewMilestonesReady = false;
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
        debugPrint('找到本月数据: ${item['date']}, 资产=$totalAsset');
      }

      // 今年初数据（找到今年第一条记录）
      if (date.year == now.year && yearStart == null && totalAsset != 0) {
        yearStart = totalAsset;
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
      await _saveDomainEnvelope(
        'exchange_rates',
        data: <String, dynamic>{'rates': _exchangeRates},
        version: _syncVersions['rates'],
        staleAfter: _ratesDataTtl,
      );
      _assetDataFromCache = false;
      _lastAssetDataUpdatedAt = DateTime.now();
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
