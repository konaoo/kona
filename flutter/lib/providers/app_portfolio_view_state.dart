import 'package:flutter/material.dart';

import '../models/portfolio.dart';
import '../services/api_service.dart';
import '../services/portfolio_metrics_service.dart';
import 'app_assets_state.dart';
import 'app_market_state.dart';
import 'app_preferences_state.dart';
import 'app_sync_state.dart';

class AppPortfolioViewState extends ChangeNotifier {
  final ApiService _api;
  final AppAssetsState _assetsState;
  final AppMarketState _marketState;
  final AppPreferencesState _preferencesState;
  final AppSyncState _syncState;

  Map<String, PriceInfo> _prices = <String, PriceInfo>{};
  Map<String, PriceInfo> _priceSnapshots = <String, PriceInfo>{};
  String _currentCategory = 'all';

  AppPortfolioViewState({
    required ApiService api,
    required AppAssetsState assetsState,
    required AppMarketState marketState,
    required AppPreferencesState preferencesState,
    required AppSyncState syncState,
  }) : _api = api,
       _assetsState = assetsState,
       _marketState = marketState,
       _preferencesState = preferencesState,
       _syncState = syncState;

  Map<String, PriceInfo> get prices => _prices;
  Map<String, PriceInfo> get priceSnapshots => _priceSnapshots;
  String get currentCategory => _currentCategory;

  int get quoteRefreshIntervalSeconds {
    if (_marketState.hasAnyMarketOpen) {
      return _syncState.quoteIntervalOpenSec;
    }
    if (_hasActiveUsExtendedSession()) {
      return _syncState.quoteIntervalUsExtendedSec;
    }
    return _syncState.quoteIntervalClosedSec;
  }

  List<PortfolioItem> get filteredPortfolio {
    if (_currentCategory == 'all') {
      return _assetsState.portfolio;
    }
    return _assetsState.portfolio
        .where((item) => item.marketType == _currentCategory)
        .toList();
  }

  double get investTotalMV {
    return PortfolioMetricsService.sumMetricIgnoreNull(
      _assetsState.portfolio,
      (item) => PortfolioMetricsService.resolveLiveValueCny(
        item,
        priceInfo: resolvePriceInfo(item),
        fallbackRateToCny: getCurrencyRate(item.curr),
      ),
    );
  }

  double get investDayPnl {
    return PortfolioMetricsService.sumMetricWhenAny(
          _assetsState.portfolio.where(
            (item) => isAssetDayPnlEnabled(
              item,
              priceInfo: resolvePriceInfo(item),
            ),
          ),
          (item) => PortfolioMetricsService.resolveCurrentDayPnlCny(
            item,
            priceInfo: resolvePriceInfo(item),
            fallbackRateToCny: getCurrencyRate(item.curr),
          ),
        ) ??
        0;
  }

  double get investDayPnlRate {
    final pnl = PortfolioMetricsService.sumMetricWhenAny(
      _assetsState.portfolio.where(
        (item) => isAssetDayPnlEnabled(
          item,
          priceInfo: resolvePriceInfo(item),
        ),
      ),
      (item) => PortfolioMetricsService.resolveCurrentDayPnlCny(
        item,
        priceInfo: resolvePriceInfo(item),
        fallbackRateToCny: getCurrencyRate(item.curr),
      ),
    );
    final base = PortfolioMetricsService.sumMetricWhenAny(
      _assetsState.portfolio.where(
        (item) => isAssetDayPnlEnabled(
          item,
          priceInfo: resolvePriceInfo(item),
        ),
      ),
      (item) => PortfolioMetricsService.resolveCurrentDayPnlBaseCny(
        item,
        priceInfo: resolvePriceInfo(item),
        fallbackRateToCny: getCurrencyRate(item.curr),
      ),
    );
    return PortfolioMetricsService.calcDayPnlRateNullable(pnl, base) ?? 0;
  }

  double get investHoldingPnl {
    return PortfolioMetricsService.sumMetricOrNull(
          _assetsState.portfolio,
          (item) => PortfolioMetricsService.resolveLiveFloatPnlCny(
            item,
            priceInfo: resolvePriceInfo(item),
            fallbackRateToCny: getCurrencyRate(item.curr),
          ),
        ) ??
        0;
  }

  double get investHoldingPnlRate {
    final pnl = PortfolioMetricsService.sumMetricOrNull(
      _assetsState.portfolio,
      (item) => PortfolioMetricsService.resolveLiveFloatPnlCny(
        item,
        priceInfo: resolvePriceInfo(item),
        fallbackRateToCny: getCurrencyRate(item.curr),
      ),
    );
    final costAbs = PortfolioMetricsService.sumAbsMetricOrNull(
      _assetsState.portfolio,
      (item) => PortfolioMetricsService.resolveCostCnyLive(
        item,
        fallbackRateToCny: getCurrencyRate(item.curr),
      ),
    );
    return PortfolioMetricsService.calcHoldingPnlRateNullable(pnl, costAbs) ??
        0;
  }

  void replacePrices(Map<String, PriceInfo> next, {bool notify = true}) {
    _prices = next;
    if (notify) {
      notifyListeners();
    }
  }

  void replacePriceSnapshots(
    Map<String, PriceInfo> next, {
    bool notify = true,
  }) {
    _priceSnapshots = next;
    if (notify) {
      notifyListeners();
    }
  }

  void clearPrices({bool notify = true}) {
    _prices = <String, PriceInfo>{};
    if (notify) {
      notifyListeners();
    }
  }

  void clearPriceSnapshots({bool notify = true}) {
    _priceSnapshots = <String, PriceInfo>{};
    if (notify) {
      notifyListeners();
    }
  }

  void setCategory(String category, {bool notify = true}) {
    if (_currentCategory == category) {
      return;
    }
    _currentCategory = category;
    if (notify) {
      notifyListeners();
    }
  }

  PriceInfo? resolvePriceInfoByCode(
    String code, {
    PriceInfo? preferred,
    Map<String, PriceInfo>? runtimeFallback,
  }) {
    if (_isValidPriceInfo(preferred)) {
      return preferred;
    }
    final live = _prices[code];
    if (_isValidPriceInfo(live)) {
      return live;
    }
    final runtime = runtimeFallback?[code];
    if (_isValidPriceInfo(runtime)) {
      return runtime;
    }
    final snapshot = _priceSnapshots[code];
    if (_isValidPriceInfo(snapshot)) {
      return snapshot;
    }
    return null;
  }

  PriceInfo? resolvePriceInfo(PortfolioItem item, {PriceInfo? preferred}) {
    return resolvePriceInfoByCode(item.code, preferred: preferred);
  }

  bool isAssetMarketOpen(PortfolioItem item) {
    return _marketState.isMarketOpen(item.marketType);
  }

  bool isAssetTradingDay(PortfolioItem item) {
    return _marketState.isMarketTradingDay(item.marketType);
  }

  bool isNavUpdatePendingAsset(PortfolioItem item) {
    if (item.navUpdatePending != null) {
      return item.navUpdatePending!;
    }
    final code = item.code.trim().toLowerCase();
    return code.startsWith('f_') || code.startsWith('ft_');
  }

  bool isAssetDayPnlDisplayEnabled(PortfolioItem item, {PriceInfo? priceInfo}) {
    if (PortfolioMetricsService.isPreopenOffHoursAsset(item)) {
      return false;
    }
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
    if (PortfolioMetricsService.isPreopenOffHoursAsset(item)) {
      return false;
    }
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

  String normalizeInvestmentCurrency({required String code, String? curr}) {
    final raw = code.trim();
    final lower = raw.toLowerCase();
    if (raw.isEmpty) {
      final fallback = curr?.trim().toUpperCase();
      return (fallback == null || fallback.isEmpty) ? 'CNY' : fallback;
    }
    if (lower.startsWith('sh900')) {
      return 'USD';
    }
    if (lower.startsWith('sz200')) {
      return 'HKD';
    }
    if (lower.startsWith('gb_') || lower.startsWith('ft_')) {
      return 'USD';
    }
    if (lower.endsWith('.hk') || lower.startsWith('hk')) {
      return 'HKD';
    }
    if (lower.startsWith('sh') ||
        lower.startsWith('sz') ||
        lower.startsWith('bj') ||
        lower.startsWith('f_')) {
      return 'CNY';
    }
    if (RegExp(r'^[a-z]+(\.[a-z]+)?$').hasMatch(lower)) {
      return 'USD';
    }
    if (RegExp(r'^\d+$').hasMatch(raw)) {
      return 'CNY';
    }
    final fallback = curr?.trim().toUpperCase();
    return (fallback == null || fallback.isEmpty) ? 'CNY' : fallback;
  }

  Future<double?> fetchLatestPriceForCode(String code) async {
    final raw = code.trim();
    if (raw.isEmpty) {
      return null;
    }
    final apiCode = raw.startsWith('gb_') ? raw.substring(3) : raw;
    try {
      final prices = await _api.getPricesBatch(<String>[apiCode]);
      final payload = prices[apiCode];
      if (payload is! Map<String, dynamic>) {
        return null;
      }
      final info = PriceInfo.fromJson(payload);
      if (info.price > 0) {
        return info.price;
      }
      if (info.yclose > 0) {
        return info.yclose;
      }
      return null;
    } catch (_) {
      return null;
    }
  }

  double getCurrencyRate(String curr) {
    return _marketState.rateForCurrency(curr);
  }

  double convertToCny(double amount, String curr) {
    return amount * getCurrencyRate(curr);
  }

  double convertDisplayAmount(double cnyAmount) {
    if (_preferencesState.displayCurrency == 'CNY') {
      return cnyAmount;
    }
    final rate = getCurrencyRate(_preferencesState.displayCurrency);
    if (rate <= 0) {
      return cnyAmount;
    }
    return cnyAmount / rate;
  }

  String formatAmount(double value, {String prefix = '¥'}) {
    if (_preferencesState.amountHidden) {
      return '****';
    }
    return '$prefix${_formatInteger(value.abs())}';
  }

  String formatPnl(double value) {
    if (_preferencesState.amountHidden) {
      return '****';
    }
    final sign = value >= 0 ? '+' : '';
    return '$sign${value.toStringAsFixed(2)}';
  }

  String formatPnlInt(double value) {
    if (_preferencesState.amountHidden) {
      return '****';
    }
    final sign = value > 0 ? '+' : (value < 0 ? '-' : '');
    return '$sign${_formatInteger(value.abs())}';
  }

  String formatPnlIntWithCurrency(double value, String symbol) {
    if (_preferencesState.amountHidden) {
      return '****';
    }
    final sign = value > 0 ? '+' : (value < 0 ? '-' : '');
    return '$sign$symbol${_formatInteger(value.abs())}';
  }

  String formatCompactAmount(
    double value, {
    String prefix = '',
    int decimals = 1,
  }) {
    if (_preferencesState.amountHidden) {
      return '****';
    }
    return '$prefix${_formatCompactAbs(value.abs(), decimals: decimals)}';
  }

  String formatCompactPnlWithCurrency(
    double value,
    String symbol, {
    int decimals = 1,
  }) {
    if (_preferencesState.amountHidden) {
      return '****';
    }
    final sign = value > 0 ? '+' : (value < 0 ? '-' : '');
    return '$sign$symbol${_formatCompactAbs(value.abs(), decimals: decimals)}';
  }

  String formatCompactPnlCny(double value) {
    if (_preferencesState.amountHidden) {
      return '****';
    }
    final sign = value > 0 ? '+' : (value < 0 ? '-' : '');
    return '$sign¥${_formatCompactAbs(value.abs(), decimals: 0)}';
  }

  String formatPct(double value) {
    final sign = value >= 0 ? '+' : '';
    return '$sign${value.toStringAsFixed(2)}%';
  }

  static Color getPnlColor(double value) {
    if (value > 0) {
      return const Color(0xFFEF4444);
    }
    if (value < 0) {
      return const Color(0xFF10B981);
    }
    return const Color(0xFF94A3B8);
  }

  bool _hasActiveUsExtendedSession() {
    for (final item in _assetsState.portfolio) {
      if (_marketState.normalizeMarketKey(item.marketType) != 'us') {
        continue;
      }
      if (_isUsExtendedSessionActive(item, resolvePriceInfo(item))) {
        return true;
      }
    }
    return false;
  }

  bool _isUsExtendedSessionActive(PortfolioItem item, PriceInfo? priceInfo) {
    if (priceInfo == null) {
      return false;
    }
    if (_marketState.normalizeMarketKey(item.marketType) != 'us') {
      return false;
    }
    if (priceInfo.price <= 0 || priceInfo.yclose <= 0) {
      return false;
    }
    if (priceInfo.extendedActive) {
      return true;
    }
    final session = priceInfo.effectiveSession.trim().toLowerCase();
    return session == 'pre' || session == 'post';
  }

  bool _isValidPriceInfo(PriceInfo? info) {
    return info != null && info.price > 0;
  }

  String _formatInteger(double value) {
    final normalized = value.isFinite ? value + 1e-9 : 0.0;
    return normalized
        .toStringAsFixed(0)
        .replaceAllMapped(
          RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'),
          (Match m) => '${m[1]},',
        );
  }

  String _formatCompactAbs(double absVal, {required int decimals}) {
    if (absVal >= 100000000) {
      return '${(absVal / 100000000).toStringAsFixed(decimals)}亿';
    }
    if (absVal >= 10000) {
      return '${(absVal / 10000).toStringAsFixed(decimals)}万';
    }
    return _formatInteger(absVal);
  }
}
