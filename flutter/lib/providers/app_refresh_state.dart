import 'dart:async';

import 'package:flutter/foundation.dart';

import '../models/asset.dart';
import '../models/portfolio.dart';
import '../services/api_service.dart';
import 'app_market_state.dart';
import 'app_sync_state.dart';

typedef AppRefreshPriceResolver =
    PriceInfo? Function(
      String code, {
      PriceInfo? preferred,
      Map<String, PriceInfo>? runtimeFallback,
    });

class AppRefreshBindings {
  final String? Function() username;
  final String? Function() userId;
  final AppSyncState syncState;
  final Map<String, String> Function() syncVersions;
  final List<PortfolioItem> Function() portfolio;
  final void Function(List<PortfolioItem>) replacePortfolio;
  final List<Asset> Function() cashAssets;
  final void Function(List<Asset>) replaceCashAssets;
  final List<Asset> Function() otherAssets;
  final void Function(List<Asset>) replaceOtherAssets;
  final List<Asset> Function() liabilities;
  final void Function(List<Asset>) replaceLiabilities;
  final Map<String, PriceInfo> Function() prices;
  final void Function(Map<String, PriceInfo>) replacePrices;
  final Map<String, PriceInfo> Function() priceSnapshots;
  final void Function(Map<String, PriceInfo>) replacePriceSnapshots;
  final bool Function() portfolioLoaded;
  final void Function(bool) setPortfolioLoaded;
  final Map<String, double> Function() exchangeRates;
  final void Function() recalculateHomeTotals;
  final void Function(List<dynamic>) calculateHistoryStats;
  final void Function(Map<String, dynamic>?) applyOverviewMilestones;
  final void Function(Map<String, dynamic>) updateExchangeRates;
  final void Function(dynamic rawStatuses, {dynamic rawOpenFallback})
  applySyncMarketStatus;
  final Map<String, dynamic> Function() serializeMarketStatusForCache;
  final Future<ParsedMarketStatus> Function() loadMarketStatusWithBudget;
  final AppRefreshPriceResolver resolvePriceInfoByCode;
  final void Function() notifyListeners;

  const AppRefreshBindings({
    required this.username,
    required this.userId,
    required this.syncState,
    required this.syncVersions,
    required this.portfolio,
    required this.replacePortfolio,
    required this.cashAssets,
    required this.replaceCashAssets,
    required this.otherAssets,
    required this.replaceOtherAssets,
    required this.liabilities,
    required this.replaceLiabilities,
    required this.prices,
    required this.replacePrices,
    required this.priceSnapshots,
    required this.replacePriceSnapshots,
    required this.portfolioLoaded,
    required this.setPortfolioLoaded,
    required this.exchangeRates,
    required this.recalculateHomeTotals,
    required this.calculateHistoryStats,
    required this.applyOverviewMilestones,
    required this.updateExchangeRates,
    required this.applySyncMarketStatus,
    required this.serializeMarketStatusForCache,
    required this.loadMarketStatusWithBudget,
    required this.resolvePriceInfoByCode,
    required this.notifyListeners,
  });
}

class AppRefreshState {
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

  final ApiService _api;
  final Duration _staticDataTtl;
  final Duration _historyDataTtl;
  final Duration _ratesDataTtl;
  final Duration _syncVersionTtl;
  final Duration _priceRefreshMinInterval;
  final List<String> _syncBootstrapDomains;

  bool _priceRefreshInFlight = false;
  DateTime? _lastPriceRefreshAt;
  Future<void>? _refreshAllInFlight;
  Future<void>? _refreshByVersionInFlight;

  AppRefreshState({
    required ApiService api,
    required Duration staticDataTtl,
    required Duration historyDataTtl,
    required Duration ratesDataTtl,
    required Duration syncVersionTtl,
    required Duration priceRefreshMinInterval,
    required List<String> syncBootstrapDomains,
  }) : _api = api,
       _staticDataTtl = staticDataTtl,
       _historyDataTtl = historyDataTtl,
       _ratesDataTtl = ratesDataTtl,
       _syncVersionTtl = syncVersionTtl,
       _priceRefreshMinInterval = priceRefreshMinInterval,
       _syncBootstrapDomains = List<String>.from(syncBootstrapDomains);

  Future<void> hydrateFromCache({required AppRefreshBindings bindings}) async {
    final syncState = bindings.syncState;
    final currentUsername = bindings.username();
    final currentUserId = bindings.userId();
    final syncVersions = bindings.syncVersions();

    await syncState.loadSyncVersionsFromCache(
      username: currentUsername,
      userId: currentUserId,
      legacyCacheKeys: _legacyCacheKeys,
    );

    DateTime? assetSavedAt;
    DateTime? quoteSavedAt;
    var hasAssetCache = false;
    var hasQuoteCache = false;

    DateTime? mergeLatest(DateTime? current, DateTime? next) {
      if (next == null) return current;
      if (current == null) return next;
      return next.isAfter(current) ? next : current;
    }

    final portfolioEnvelope = await syncState.loadDomainEnvelope(
      domain: 'portfolio',
      username: currentUsername,
      userId: currentUserId,
      legacyCacheKeys: _legacyCacheKeys,
    );
    final cachedPortfolio = syncState.asMap(portfolioEnvelope?['data']);
    if (cachedPortfolio['items'] is List) {
      bindings.replacePortfolio(
        (cachedPortfolio['items'] as List)
            .map((e) => PortfolioItem.fromJson(e))
            .toList(),
      );
      hasAssetCache = true;
      assetSavedAt = mergeLatest(
        assetSavedAt,
        syncState.envelopeSavedAt(portfolioEnvelope),
      );
      final cachedVersion = '${portfolioEnvelope?['version'] ?? ''}'.trim();
      if (cachedVersion.isNotEmpty) {
        syncVersions['portfolio'] = cachedVersion;
      }
    }

    final cashEnvelope = await syncState.loadDomainEnvelope(
      domain: 'cash_assets',
      username: currentUsername,
      userId: currentUserId,
      legacyCacheKeys: _legacyCacheKeys,
    );
    final cachedCash = syncState.asMap(cashEnvelope?['data']);
    if (cachedCash['items'] is List) {
      bindings.replaceCashAssets(
        (cachedCash['items'] as List).map((e) => Asset.fromJson(e)).toList(),
      );
      hasAssetCache = true;
      assetSavedAt = mergeLatest(
        assetSavedAt,
        syncState.envelopeSavedAt(cashEnvelope),
      );
      final cachedVersion = '${cashEnvelope?['version'] ?? ''}'.trim();
      if (cachedVersion.isNotEmpty) {
        syncVersions['cash_assets'] = cachedVersion;
      }
    }

    final otherEnvelope = await syncState.loadDomainEnvelope(
      domain: 'other_assets',
      username: currentUsername,
      userId: currentUserId,
      legacyCacheKeys: _legacyCacheKeys,
    );
    final cachedOther = syncState.asMap(otherEnvelope?['data']);
    if (cachedOther['items'] is List) {
      bindings.replaceOtherAssets(
        (cachedOther['items'] as List).map((e) => Asset.fromJson(e)).toList(),
      );
      hasAssetCache = true;
      assetSavedAt = mergeLatest(
        assetSavedAt,
        syncState.envelopeSavedAt(otherEnvelope),
      );
      final cachedVersion = '${otherEnvelope?['version'] ?? ''}'.trim();
      if (cachedVersion.isNotEmpty) {
        syncVersions['other_assets'] = cachedVersion;
      }
    }

    final liabilitiesEnvelope = await syncState.loadDomainEnvelope(
      domain: 'liabilities',
      username: currentUsername,
      userId: currentUserId,
      legacyCacheKeys: _legacyCacheKeys,
    );
    final cachedLiabilities = syncState.asMap(liabilitiesEnvelope?['data']);
    if (cachedLiabilities['items'] is List) {
      bindings.replaceLiabilities(
        (cachedLiabilities['items'] as List)
            .map((e) => Asset.fromJson(e))
            .toList(),
      );
      hasAssetCache = true;
      assetSavedAt = mergeLatest(
        assetSavedAt,
        syncState.envelopeSavedAt(liabilitiesEnvelope),
      );
      final cachedVersion = '${liabilitiesEnvelope?['version'] ?? ''}'.trim();
      if (cachedVersion.isNotEmpty) {
        syncVersions['liabilities'] = cachedVersion;
      }
    }

    final pricesEnvelope = await syncState.loadDomainEnvelope(
      domain: 'prices',
      username: currentUsername,
      userId: currentUserId,
      legacyCacheKeys: _legacyCacheKeys,
    );
    final cachedPrices = syncState.asMap(pricesEnvelope?['data']);
    if (cachedPrices['items'] is Map) {
      final nextPrices = <String, PriceInfo>{};
      (cachedPrices['items'] as Map).forEach((key, value) {
        if (value is Map<String, dynamic>) {
          nextPrices[key.toString()] = PriceInfo.fromJson(value);
        }
      });
      bindings.replacePrices(nextPrices);
      hasQuoteCache = true;
      quoteSavedAt = mergeLatest(
        quoteSavedAt,
        syncState.envelopeSavedAt(pricesEnvelope),
      );
    }

    final snapshotEnvelope = await syncState.loadDomainEnvelope(
      domain: 'price_snapshots',
      username: currentUsername,
      userId: currentUserId,
      legacyCacheKeys: _legacyCacheKeys,
    );
    final cachedSnapshots = syncState.asMap(snapshotEnvelope?['data']);
    if (cachedSnapshots['items'] is Map) {
      final nextSnapshots = <String, PriceInfo>{};
      (cachedSnapshots['items'] as Map).forEach((key, value) {
        if (value is Map<String, dynamic>) {
          nextSnapshots[key.toString()] = PriceInfo.fromJson(value);
        }
      });
      bindings.replacePriceSnapshots(nextSnapshots);
      hasQuoteCache = true;
      quoteSavedAt = mergeLatest(
        quoteSavedAt,
        syncState.envelopeSavedAt(snapshotEnvelope),
      );
    } else if (bindings.prices().isNotEmpty) {
      bindings.replacePriceSnapshots(
        Map<String, PriceInfo>.from(bindings.prices()),
      );
    }
    if (bindings.prices().isEmpty && bindings.priceSnapshots().isNotEmpty) {
      bindings.replacePrices(
        Map<String, PriceInfo>.from(bindings.priceSnapshots()),
      );
    }

    final marketStatusEnvelope = await syncState.loadDomainEnvelope(
      domain: 'market_status',
      username: currentUsername,
      userId: currentUserId,
      legacyCacheKeys: _legacyCacheKeys,
    );
    final cachedMarketStatus = syncState.asMap(marketStatusEnvelope?['data']);
    if (cachedMarketStatus.isNotEmpty) {
      bindings.applySyncMarketStatus(cachedMarketStatus);
      hasQuoteCache = true;
      quoteSavedAt = mergeLatest(
        quoteSavedAt,
        syncState.envelopeSavedAt(marketStatusEnvelope),
      );
    }

    final historyEnvelope = await syncState.loadDomainEnvelope(
      domain: 'history',
      username: currentUsername,
      userId: currentUserId,
      legacyCacheKeys: _legacyCacheKeys,
    );
    final cachedHistory = syncState.asMap(historyEnvelope?['data']);
    if (cachedHistory['items'] is List) {
      bindings.calculateHistoryStats(cachedHistory['items'] as List);
      hasAssetCache = true;
      assetSavedAt = mergeLatest(
        assetSavedAt,
        syncState.envelopeSavedAt(historyEnvelope),
      );
      final cachedVersion = '${historyEnvelope?['version'] ?? ''}'.trim();
      if (cachedVersion.isNotEmpty) {
        syncVersions['history'] = cachedVersion;
      }
    }

    final overviewEnvelope = await syncState.loadDomainEnvelope(
      domain: 'analysis_overview',
      username: currentUsername,
      userId: currentUserId,
      legacyCacheKeys: _legacyCacheKeys,
    );
    final cachedOverview = syncState.asMap(overviewEnvelope?['data']);
    if (cachedOverview['data'] is Map) {
      bindings.applyOverviewMilestones(
        Map<String, dynamic>.from(cachedOverview['data'] as Map),
      );
      hasAssetCache = true;
      assetSavedAt = mergeLatest(
        assetSavedAt,
        syncState.envelopeSavedAt(overviewEnvelope),
      );
      final cachedVersion = '${overviewEnvelope?['version'] ?? ''}'.trim();
      if (cachedVersion.isNotEmpty) {
        syncVersions['overview_all'] = cachedVersion;
      }
    } else if (cachedOverview.isNotEmpty) {
      bindings.applyOverviewMilestones(cachedOverview);
      hasAssetCache = true;
      assetSavedAt = mergeLatest(
        assetSavedAt,
        syncState.envelopeSavedAt(overviewEnvelope),
      );
    }

    final ratesEnvelope = await syncState.loadDomainEnvelope(
      domain: 'exchange_rates',
      username: currentUsername,
      userId: currentUserId,
      legacyCacheKeys: _legacyCacheKeys,
    );
    final cachedRates = syncState.asMap(ratesEnvelope?['data']);
    if (cachedRates['rates'] is Map) {
      bindings.updateExchangeRates(
        Map<String, dynamic>.from(cachedRates['rates'] as Map),
      );
      hasAssetCache = true;
      assetSavedAt = mergeLatest(
        assetSavedAt,
        syncState.envelopeSavedAt(ratesEnvelope),
      );
      final cachedVersion = '${ratesEnvelope?['version'] ?? ''}'.trim();
      if (cachedVersion.isNotEmpty) {
        syncVersions['rates'] = cachedVersion;
      }
    }

    bindings.recalculateHomeTotals();
    bindings.setPortfolioLoaded(
      bindings.portfolio().isNotEmpty || bindings.cashAssets().isNotEmpty,
    );
    if (hasAssetCache) {
      syncState.markAssetCacheHydrated(assetSavedAt, notify: false);
    }
    if (hasQuoteCache) {
      syncState.markQuoteCacheHydrated(quoteSavedAt, notify: false);
    }
    bindings.notifyListeners();
  }

  Future<void> savePortfolioToCache({
    required AppRefreshBindings bindings,
  }) async {
    await _savePortfolioEnvelope(bindings: bindings);
  }

  Future<void> saveHomeCache({
    required AppRefreshBindings bindings,
    required List<dynamic> history,
    Map<String, dynamic>? overview,
  }) async {
    await _savePortfolioEnvelope(bindings: bindings);
    await _saveAssetListEnvelope(
      bindings: bindings,
      domain: 'cash_assets',
      items: bindings.cashAssets(),
      version: bindings.syncVersions()['cash_assets'],
    );
    await _saveAssetListEnvelope(
      bindings: bindings,
      domain: 'other_assets',
      items: bindings.otherAssets(),
      version: bindings.syncVersions()['other_assets'],
    );
    await _saveAssetListEnvelope(
      bindings: bindings,
      domain: 'liabilities',
      items: bindings.liabilities(),
      version: bindings.syncVersions()['liabilities'],
    );
    await bindings.syncState.saveDomainEnvelope(
      domain: 'history',
      data: <String, dynamic>{'items': history},
      version: bindings.syncVersions()['history'],
      staleAfter: _historyDataTtl,
      username: bindings.username(),
      userId: bindings.userId(),
    );
    await _saveRatesEnvelope(bindings: bindings);
    await bindings.syncState.saveDomainEnvelope(
      domain: 'prices',
      data: <String, dynamic>{'items': _serializePriceItems(bindings.prices())},
      staleAfter: _staticDataTtl,
      username: bindings.username(),
      userId: bindings.userId(),
    );
    await bindings.syncState.saveDomainEnvelope(
      domain: 'price_snapshots',
      data: <String, dynamic>{
        'items': _serializePriceItems(bindings.priceSnapshots()),
      },
      staleAfter: _syncVersionTtl,
      username: bindings.username(),
      userId: bindings.userId(),
    );
    await bindings.syncState.saveDomainEnvelope(
      domain: 'market_status',
      data: bindings.serializeMarketStatusForCache(),
      staleAfter: _staticDataTtl,
      username: bindings.username(),
      userId: bindings.userId(),
    );
    if (overview != null && overview.isNotEmpty) {
      await bindings.syncState.saveDomainEnvelope(
        domain: 'analysis_overview',
        data: <String, dynamic>{'data': overview},
        version: bindings.syncVersions()['overview_all'],
        staleAfter: _historyDataTtl,
        username: bindings.username(),
        userId: bindings.userId(),
      );
    }
    await bindings.syncState.saveSyncVersionsToCache(
      username: bindings.username(),
      userId: bindings.userId(),
      staleAfter: _syncVersionTtl,
    );
  }

  Future<void> refreshHomeData({required AppRefreshBindings bindings}) async {
    try {
      final results = await Future.wait([
        _api.getCashAssets(),
        _api.getOtherAssets(),
        _api.getLiabilities(),
        _api.getPortfolio(withMetrics: true),
        _api.getHistory(),
        _api.getAnalysisOverview(period: 'all'),
      ]);

      bindings.replaceCashAssets(
        (results[0] as List).map((e) => Asset.fromJson(e)).toList(),
      );
      bindings.replaceOtherAssets(
        (results[1] as List).map((e) => Asset.fromJson(e)).toList(),
      );
      bindings.replaceLiabilities(
        (results[2] as List).map((e) => Asset.fromJson(e)).toList(),
      );
      bindings.replacePortfolio(
        (results[3] as List).map((e) => PortfolioItem.fromJson(e)).toList(),
      );

      bindings.recalculateHomeTotals();

      final history = results[4] as List;
      final overview = (results[5] as Map?)?.cast<String, dynamic>();
      bindings.calculateHistoryStats(history);
      bindings.applyOverviewMilestones(overview);

      await saveHomeCache(
        bindings: bindings,
        history: history,
        overview: overview,
      );
      bindings.syncState.markAssetFresh(notify: false);
      bindings.setPortfolioLoaded(true);
      bindings.notifyListeners();

      unawaited(
        refreshPortfolioPricesInBackground(bindings: bindings, force: true),
      );
    } catch (e) {
      debugPrint('刷新首页数据失败: $e');
    }
  }

  Future<void> refreshByVersion({
    required AppRefreshBindings bindings,
    bool force = false,
    bool refreshQuotes = true,
  }) async {
    final existing = _refreshByVersionInFlight;
    if (existing != null) return existing;

    final future = _refreshByVersionInternal(
      bindings: bindings,
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

  Future<void> refreshPricesOnly({required AppRefreshBindings bindings}) async {
    await refreshPortfolioPricesInBackground(bindings: bindings, force: true);
  }

  Future<void> refreshAll({
    required AppRefreshBindings bindings,
    bool force = false,
  }) async {
    final existing = _refreshAllInFlight;
    if (existing != null) return existing;

    final future = _refreshAllInternal(bindings: bindings, force: force);
    _refreshAllInFlight = future;
    try {
      await future;
    } finally {
      _refreshAllInFlight = null;
    }
  }

  Future<void> refreshPortfolio({required AppRefreshBindings bindings}) async {
    try {
      final data = await _api.getPortfolio(withMetrics: true);
      bindings.replacePortfolio(
        (data).map((e) => PortfolioItem.fromJson(e)).toList(),
      );

      if (bindings.portfolio().isNotEmpty) {
        final codes = bindings.portfolio().map((e) => e.code).toList();
        final pricesData = await _api.getPricesBatch(codes);
        bindings.replacePrices(
          pricesData.map(
            (key, value) => MapEntry(key, PriceInfo.fromJson(value)),
          ),
        );
      }

      bindings.recalculateHomeTotals();
      bindings.setPortfolioLoaded(true);
      bindings.notifyListeners();
    } catch (e) {
      debugPrint('刷新投资组合失败: $e');
    }
  }

  Future<void> loadExchangeRates({required AppRefreshBindings bindings}) async {
    try {
      final rates = await _api.getExchangeRates();
      bindings.updateExchangeRates(rates);
      await _saveRatesEnvelope(bindings: bindings);
      bindings.syncState.markAssetFresh(notify: false);
    } catch (e) {
      debugPrint('加载汇率失败: $e');
    }
  }

  Future<void> refreshPortfolioPricesInBackground({
    required AppRefreshBindings bindings,
    bool force = false,
  }) async {
    final now = DateTime.now();
    if (_priceRefreshInFlight) return;
    if (!force &&
        _lastPriceRefreshAt != null &&
        now.difference(_lastPriceRefreshAt!) < _priceRefreshMinInterval) {
      return;
    }

    _priceRefreshInFlight = true;
    try {
      final marketStatusFuture = bindings.loadMarketStatusWithBudget();
      if (bindings.portfolio().isEmpty) {
        final marketStatus = await marketStatusFuture;
        bindings.applySyncMarketStatus(<String, dynamic>{
          'markets': {
            'a': {
              'open': marketStatus.open['a'] ?? false,
              'trading_day': marketStatus.tradingDay['a'] ?? false,
            },
            'hk': {
              'open': marketStatus.open['hk'] ?? false,
              'trading_day': marketStatus.tradingDay['hk'] ?? false,
            },
            'us': {
              'open': marketStatus.open['us'] ?? false,
              'trading_day': marketStatus.tradingDay['us'] ?? false,
            },
            'fund': {
              'open': marketStatus.open['fund'] ?? false,
              'trading_day': marketStatus.tradingDay['fund'] ?? false,
            },
          },
        });
        await bindings.syncState.saveDomainEnvelope(
          domain: 'market_status',
          data: bindings.serializeMarketStatusForCache(),
          staleAfter: _staticDataTtl,
          username: bindings.username(),
          userId: bindings.userId(),
        );
        if (bindings.portfolioLoaded()) {
          bindings.replacePrices(<String, PriceInfo>{});
          bindings.replacePriceSnapshots(<String, PriceInfo>{});
          bindings.recalculateHomeTotals();
          await bindings.syncState.saveDomainEnvelope(
            domain: 'prices',
            data: <String, dynamic>{'items': <String, dynamic>{}},
            staleAfter: _staticDataTtl,
            username: bindings.username(),
            userId: bindings.userId(),
          );
          await bindings.syncState.saveDomainEnvelope(
            domain: 'price_snapshots',
            data: <String, dynamic>{'items': <String, dynamic>{}},
            staleAfter: _syncVersionTtl,
            username: bindings.username(),
            userId: bindings.userId(),
          );
          bindings.syncState.markQuoteFresh(notify: false);
          bindings.notifyListeners();
        }
        return;
      }

      final codes = bindings.portfolio().map((e) => e.code).toList();
      final previousPrices = Map<String, PriceInfo>.from(bindings.prices());
      final priceApiCodes = codes.map((code) {
        if (code.startsWith('gb_')) {
          return code.substring(3);
        }
        return code;
      }).toList();

      final pricesData = await _api.getPricesBatch(priceApiCodes);
      final marketStatus = await marketStatusFuture;
      bindings.applySyncMarketStatus(<String, dynamic>{
        'markets': {
          'a': {
            'open': marketStatus.open['a'] ?? false,
            'trading_day': marketStatus.tradingDay['a'] ?? false,
          },
          'hk': {
            'open': marketStatus.open['hk'] ?? false,
            'trading_day': marketStatus.tradingDay['hk'] ?? false,
          },
          'us': {
            'open': marketStatus.open['us'] ?? false,
            'trading_day': marketStatus.tradingDay['us'] ?? false,
          },
          'fund': {
            'open': marketStatus.open['fund'] ?? false,
            'trading_day': marketStatus.tradingDay['fund'] ?? false,
          },
        },
      });
      final nextPrices = <String, PriceInfo>{};
      for (var i = 0; i < codes.length; i++) {
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
        final resolved = bindings.resolvePriceInfoByCode(
          originalCode,
          preferred: parsed,
          runtimeFallback: previousPrices,
        );
        if (resolved != null) {
          nextPrices[originalCode] = resolved;
        }
      }

      bindings.replacePrices(nextPrices);
      final nextSnapshots =
          Map<String, PriceInfo>.from(bindings.priceSnapshots())
            ..removeWhere((code, _) => !codes.contains(code))
            ..addAll(nextPrices);
      bindings.replacePriceSnapshots(nextSnapshots);
      bindings.recalculateHomeTotals();
      await bindings.syncState.saveDomainEnvelope(
        domain: 'market_status',
        data: bindings.serializeMarketStatusForCache(),
        staleAfter: _staticDataTtl,
        username: bindings.username(),
        userId: bindings.userId(),
      );
      await bindings.syncState.saveDomainEnvelope(
        domain: 'prices',
        data: <String, dynamic>{
          'items': _serializePriceItems(bindings.prices()),
        },
        staleAfter: _staticDataTtl,
        username: bindings.username(),
        userId: bindings.userId(),
      );
      await bindings.syncState.saveDomainEnvelope(
        domain: 'price_snapshots',
        data: <String, dynamic>{
          'items': _serializePriceItems(bindings.priceSnapshots()),
        },
        staleAfter: _syncVersionTtl,
        username: bindings.username(),
        userId: bindings.userId(),
      );
      bindings.syncState.markQuoteFresh(notify: false);
      bindings.notifyListeners();
    } catch (e) {
      debugPrint('后台刷新行情失败: $e');
    } finally {
      _priceRefreshInFlight = false;
      _lastPriceRefreshAt = DateTime.now();
    }
  }

  Future<void> _refreshByVersionInternal({
    required AppRefreshBindings bindings,
    required bool force,
    required bool refreshQuotes,
  }) async {
    if (bindings.syncState.canSkipStaticSyncCheck(
      force: force,
      staticDataTtl: _staticDataTtl,
    )) {
      if (refreshQuotes) {
        await refreshPortfolioPricesInBackground(
          bindings: bindings,
          force: true,
        );
      }
      return;
    }

    try {
      final syncVersions = bindings.syncVersions();
      final response = await _api.getSyncBootstrap(
        include: _syncBootstrapDomains,
        clientVersions: force
            ? const <String, String>{}
            : Map<String, String>.from(syncVersions),
        portfolioMetrics: true,
      );
      bindings.syncState.applyQuotePolicy(
        response['quote_policy'],
        notify: false,
      );
      bindings.applySyncMarketStatus(
        response['market_statuses'],
        rawOpenFallback: response['market_status'],
      );

      final versions = bindings.syncState.asMap(response['versions']);
      if (versions.isNotEmpty) {
        syncVersions.addAll(
          versions.map((k, v) => MapEntry(k.toString(), (v ?? '').toString())),
        );
        await bindings.syncState.saveSyncVersionsToCache(
          username: bindings.username(),
          userId: bindings.userId(),
          staleAfter: _syncVersionTtl,
        );
      }

      final changedRaw = response['changed'];
      final changed = <String>[];
      if (changedRaw is List) {
        for (final item in changedRaw) {
          final key = '$item'.trim();
          if (key.isNotEmpty) changed.add(key);
        }
      }
      final data = bindings.syncState.asMap(response['data']);

      var staticChanged = false;
      for (final domain in changed) {
        await _applySyncDomainData(
          bindings: bindings,
          domain: domain,
          payload: data[domain],
        );
        if (domain != 'rates') {
          staticChanged = true;
        }
      }

      await bindings.syncState.saveDomainEnvelope(
        domain: 'market_status',
        data: bindings.serializeMarketStatusForCache(),
        staleAfter: _staticDataTtl,
        username: bindings.username(),
        userId: bindings.userId(),
      );

      if (staticChanged || changed.contains('rates')) {
        bindings.syncState.markAssetFresh(notify: false);
      }
      if (changed.isNotEmpty) {
        bindings.notifyListeners();
      }
    } catch (e) {
      debugPrint('版本增量刷新失败，降级全量刷新: $e');
      await Future.wait([
        refreshHomeData(bindings: bindings),
        loadExchangeRates(bindings: bindings),
      ]);
    }

    if (refreshQuotes) {
      await refreshPortfolioPricesInBackground(bindings: bindings, force: true);
    }
  }

  Future<void> _refreshAllInternal({
    required AppRefreshBindings bindings,
    required bool force,
  }) async {
    if (force) {
      await Future.wait([
        refreshHomeData(bindings: bindings),
        loadExchangeRates(bindings: bindings),
      ]);
      await refreshPortfolioPricesInBackground(bindings: bindings, force: true);
      return;
    }
    await refreshByVersion(
      bindings: bindings,
      force: false,
      refreshQuotes: true,
    );
  }

  Future<void> _applySyncDomainData({
    required AppRefreshBindings bindings,
    required String domain,
    required dynamic payload,
  }) async {
    final syncVersions = bindings.syncVersions();
    switch (domain) {
      case 'portfolio':
        final list = (payload is List) ? payload : const <dynamic>[];
        bindings.replacePortfolio(
          list.map((e) => PortfolioItem.fromJson(e)).toList(),
        );
        final validCodes = bindings.portfolio().map((e) => e.code).toSet();
        final nextPrices = Map<String, PriceInfo>.from(bindings.prices())
          ..removeWhere((code, _) => !validCodes.contains(code));
        final nextSnapshots = Map<String, PriceInfo>.from(
          bindings.priceSnapshots(),
        )..removeWhere((code, _) => !validCodes.contains(code));
        bindings.replacePrices(nextPrices);
        bindings.replacePriceSnapshots(nextSnapshots);
        bindings.recalculateHomeTotals();
        await _savePortfolioEnvelope(bindings: bindings);
        return;
      case 'cash_assets':
        final list = (payload is List) ? payload : const <dynamic>[];
        bindings.replaceCashAssets(list.map((e) => Asset.fromJson(e)).toList());
        bindings.recalculateHomeTotals();
        await _saveAssetListEnvelope(
          bindings: bindings,
          domain: 'cash_assets',
          items: bindings.cashAssets(),
          version: syncVersions['cash_assets'],
        );
        return;
      case 'other_assets':
        final list = (payload is List) ? payload : const <dynamic>[];
        bindings.replaceOtherAssets(
          list.map((e) => Asset.fromJson(e)).toList(),
        );
        bindings.recalculateHomeTotals();
        await _saveAssetListEnvelope(
          bindings: bindings,
          domain: 'other_assets',
          items: bindings.otherAssets(),
          version: syncVersions['other_assets'],
        );
        return;
      case 'liabilities':
        final list = (payload is List) ? payload : const <dynamic>[];
        bindings.replaceLiabilities(
          list.map((e) => Asset.fromJson(e)).toList(),
        );
        bindings.recalculateHomeTotals();
        await _saveAssetListEnvelope(
          bindings: bindings,
          domain: 'liabilities',
          items: bindings.liabilities(),
          version: syncVersions['liabilities'],
        );
        return;
      case 'history':
        final history = (payload is List) ? payload : const <dynamic>[];
        bindings.calculateHistoryStats(history);
        await bindings.syncState.saveDomainEnvelope(
          domain: 'history',
          data: <String, dynamic>{'items': history},
          version: syncVersions['history'],
          staleAfter: _historyDataTtl,
          username: bindings.username(),
          userId: bindings.userId(),
        );
        return;
      case 'overview_all':
        final overview = bindings.syncState.asMap(payload);
        bindings.applyOverviewMilestones(overview);
        await bindings.syncState.saveDomainEnvelope(
          domain: 'analysis_overview',
          data: <String, dynamic>{'data': overview},
          version: syncVersions['overview_all'],
          staleAfter: _historyDataTtl,
          username: bindings.username(),
          userId: bindings.userId(),
        );
        return;
      case 'rates':
        final rates = bindings.syncState.asMap(payload);
        if (rates.isNotEmpty) {
          bindings.updateExchangeRates(rates);
        }
        await _saveRatesEnvelope(bindings: bindings);
        return;
    }
  }

  Future<void> _savePortfolioEnvelope({
    required AppRefreshBindings bindings,
  }) async {
    await bindings.syncState.saveDomainEnvelope(
      domain: 'portfolio',
      data: <String, dynamic>{
        'items': bindings.portfolio().map((e) => e.toJson()).toList(),
      },
      version: bindings.syncVersions()['portfolio'],
      staleAfter: _staticDataTtl,
      username: bindings.username(),
      userId: bindings.userId(),
    );
  }

  Future<void> _saveAssetListEnvelope({
    required AppRefreshBindings bindings,
    required String domain,
    required List<Asset> items,
    required String? version,
  }) async {
    await bindings.syncState.saveDomainEnvelope(
      domain: domain,
      data: <String, dynamic>{'items': items.map((e) => e.toJson()).toList()},
      version: version,
      staleAfter: _staticDataTtl,
      username: bindings.username(),
      userId: bindings.userId(),
    );
  }

  Future<void> _saveRatesEnvelope({
    required AppRefreshBindings bindings,
  }) async {
    await bindings.syncState.saveDomainEnvelope(
      domain: 'exchange_rates',
      data: <String, dynamic>{'rates': bindings.exchangeRates()},
      version: bindings.syncVersions()['rates'],
      staleAfter: _ratesDataTtl,
      username: bindings.username(),
      userId: bindings.userId(),
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
}
