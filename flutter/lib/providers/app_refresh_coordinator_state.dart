import 'dart:async';

import '../models/asset.dart';
import '../models/portfolio.dart';
import '../services/async_flow_logger.dart';
import 'app_market_state.dart';
import 'app_refresh_state.dart';
import 'app_sync_state.dart';

class AppRefreshCoordinatorState {
  final AppRefreshState _refreshState;
  final AppSyncState _syncState;
  final String? Function() _username;
  final String? Function() _userId;
  final List<PortfolioItem> Function() _portfolio;
  final void Function(List<PortfolioItem>) _replacePortfolio;
  final List<Asset> Function() _cashAssets;
  final void Function(List<Asset>) _replaceCashAssets;
  final List<Asset> Function() _otherAssets;
  final void Function(List<Asset>) _replaceOtherAssets;
  final List<Asset> Function() _liabilities;
  final void Function(List<Asset>) _replaceLiabilities;
  final Map<String, PriceInfo> Function() _prices;
  final void Function(Map<String, PriceInfo>) _replacePrices;
  final Map<String, PriceInfo> Function() _priceSnapshots;
  final void Function(Map<String, PriceInfo>) _replacePriceSnapshots;
  final Map<String, double> Function() _exchangeRates;
  final void Function() _recalculateHomeTotals;
  final void Function(List<dynamic>) _calculateHistoryStats;
  final void Function(Map<String, dynamic>?) _applyOverviewMilestones;
  final void Function(Map<String, dynamic>) _updateExchangeRates;
  final void Function(dynamic rawStatuses, {dynamic rawOpenFallback})
  _applySyncMarketStatus;
  final Map<String, dynamic> Function() _serializeMarketStatusForCache;
  final Future<ParsedMarketStatus> Function() _loadMarketStatusWithBudget;
  final AppRefreshPriceResolver _resolvePriceInfoByCode;
  final void Function() _notifyListeners;

  bool _portfolioLoaded = false;
  AppAsyncFlowResult? _lastHydrateResult;
  AppAsyncFlowResult? _lastRefreshResult;

  AppRefreshCoordinatorState({
    required AppRefreshState refreshState,
    required AppSyncState syncState,
    required String? Function() username,
    required String? Function() userId,
    required List<PortfolioItem> Function() portfolio,
    required void Function(List<PortfolioItem>) replacePortfolio,
    required List<Asset> Function() cashAssets,
    required void Function(List<Asset>) replaceCashAssets,
    required List<Asset> Function() otherAssets,
    required void Function(List<Asset>) replaceOtherAssets,
    required List<Asset> Function() liabilities,
    required void Function(List<Asset>) replaceLiabilities,
    required Map<String, PriceInfo> Function() prices,
    required void Function(Map<String, PriceInfo>) replacePrices,
    required Map<String, PriceInfo> Function() priceSnapshots,
    required void Function(Map<String, PriceInfo>) replacePriceSnapshots,
    required Map<String, double> Function() exchangeRates,
    required void Function() recalculateHomeTotals,
    required void Function(List<dynamic>) calculateHistoryStats,
    required void Function(Map<String, dynamic>?) applyOverviewMilestones,
    required void Function(Map<String, dynamic>) updateExchangeRates,
    required void Function(dynamic rawStatuses, {dynamic rawOpenFallback})
    applySyncMarketStatus,
    required Map<String, dynamic> Function() serializeMarketStatusForCache,
    required Future<ParsedMarketStatus> Function() loadMarketStatusWithBudget,
    required AppRefreshPriceResolver resolvePriceInfoByCode,
    required void Function() notifyListeners,
  }) : _refreshState = refreshState,
       _syncState = syncState,
       _username = username,
       _userId = userId,
       _portfolio = portfolio,
       _replacePortfolio = replacePortfolio,
       _cashAssets = cashAssets,
       _replaceCashAssets = replaceCashAssets,
       _otherAssets = otherAssets,
       _replaceOtherAssets = replaceOtherAssets,
       _liabilities = liabilities,
       _replaceLiabilities = replaceLiabilities,
       _prices = prices,
       _replacePrices = replacePrices,
       _priceSnapshots = priceSnapshots,
       _replacePriceSnapshots = replacePriceSnapshots,
       _exchangeRates = exchangeRates,
       _recalculateHomeTotals = recalculateHomeTotals,
       _calculateHistoryStats = calculateHistoryStats,
       _applyOverviewMilestones = applyOverviewMilestones,
       _updateExchangeRates = updateExchangeRates,
       _applySyncMarketStatus = applySyncMarketStatus,
       _serializeMarketStatusForCache = serializeMarketStatusForCache,
       _loadMarketStatusWithBudget = loadMarketStatusWithBudget,
       _resolvePriceInfoByCode = resolvePriceInfoByCode,
       _notifyListeners = notifyListeners;

  bool get portfolioLoaded => _portfolioLoaded;
  AppAsyncFlowResult? get lastHydrateResult => _lastHydrateResult;
  AppAsyncFlowResult? get lastRefreshResult => _lastRefreshResult;

  void setPortfolioLoaded(bool value) {
    _portfolioLoaded = value;
  }

  Future<void> hydrateFromCache() async {
    final flow = startAppAsyncFlow('flutter.hydrateFromCache');
    try {
      await _refreshState.hydrateFromCache(bindings: _bindings);
      _lastHydrateResult = finishAppAsyncFlow(flow, stage: 'cache-restored');
    } catch (error) {
      _lastHydrateResult = finishAppAsyncFlow(
        flow,
        stage: 'failed',
        error: error,
      );
    }
  }

  Future<void> savePortfolioToCache() async {
    await _refreshState.savePortfolioToCache(bindings: _bindings);
  }

  Future<void> saveHomeCache(
    List<dynamic> history, {
    Map<String, dynamic>? overview,
  }) async {
    await _refreshState.saveHomeCache(
      bindings: _bindings,
      history: history,
      overview: overview,
    );
  }

  Future<void> refreshHomeData() async {
    await _refreshState.refreshHomeData(bindings: _bindings);
  }

  Future<void> refreshByVersion({
    bool force = false,
    bool refreshQuotes = true,
  }) async {
    await _refreshState.refreshByVersion(
      bindings: _bindings,
      force: force,
      refreshQuotes: refreshQuotes,
    );
  }

  Future<void> refreshPricesOnly() async {
    await _refreshState.refreshPricesOnly(bindings: _bindings);
  }

  Future<void> refreshAll({bool force = false}) async {
    final flow = startAppAsyncFlow('flutter.refreshAll');
    try {
      await _refreshState.refreshAll(bindings: _bindings, force: force);
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

  Future<void> refreshPortfolio() async {
    await _refreshState.refreshPortfolio(bindings: _bindings);
  }

  Future<void> loadExchangeRates() async {
    await _refreshState.loadExchangeRates(bindings: _bindings);
  }

  Future<void> triggerHomeRefresh({required bool awaitRefresh}) async {
    if (awaitRefresh) {
      await refreshHomeData();
    } else {
      unawaited(refreshHomeData());
    }
  }

  AppRefreshBindings get _bindings => AppRefreshBindings(
    username: _username,
    userId: _userId,
    syncState: _syncState,
    syncVersions: () => _syncState.syncVersions,
    portfolio: _portfolio,
    replacePortfolio: _replacePortfolio,
    cashAssets: _cashAssets,
    replaceCashAssets: _replaceCashAssets,
    otherAssets: _otherAssets,
    replaceOtherAssets: _replaceOtherAssets,
    liabilities: _liabilities,
    replaceLiabilities: _replaceLiabilities,
    prices: _prices,
    replacePrices: _replacePrices,
    priceSnapshots: _priceSnapshots,
    replacePriceSnapshots: _replacePriceSnapshots,
    portfolioLoaded: () => _portfolioLoaded,
    setPortfolioLoaded: (value) => _portfolioLoaded = value,
    exchangeRates: _exchangeRates,
    recalculateHomeTotals: _recalculateAndSyncPortfolioLoaded,
    calculateHistoryStats: _calculateHistoryStats,
    applyOverviewMilestones: _applyOverviewMilestones,
    updateExchangeRates: _updateExchangeRates,
    applySyncMarketStatus: _applySyncMarketStatus,
    serializeMarketStatusForCache: _serializeMarketStatusForCache,
    loadMarketStatusWithBudget: _loadMarketStatusWithBudget,
    resolvePriceInfoByCode: _resolvePriceInfoByCode,
    notifyListeners: _notifyListeners,
  );

  void _recalculateAndSyncPortfolioLoaded() {
    _recalculateHomeTotals();
    _portfolioLoaded = _portfolio().isNotEmpty || _cashAssets().isNotEmpty;
  }
}
