import '../models/portfolio.dart';

/// 投资口径汇总与汇率计算的集中入口
class PortfolioMetricsService {
  const PortfolioMetricsService._();

  static double? _metricWithRate(double? metric, double? rateToCny) {
    if (metric == null) return null;
    if (rateToCny != null && rateToCny > 0) {
      return metric * rateToCny;
    }
    return metric;
  }

  static double? resolveValueCny(PortfolioItem item) {
    return item.valueCny ?? _metricWithRate(item.value, item.rateToCny);
  }

  static double? resolveCostCny(PortfolioItem item) {
    return item.costCny ?? _metricWithRate(item.cost, item.rateToCny);
  }

  static double? resolveFloatPnlCny(PortfolioItem item) {
    final valueCny = resolveValueCny(item);
    final costCny = resolveCostCny(item);
    if (valueCny == null || costCny == null) return null;
    return valueCny - costCny.abs();
  }

  static double? resolveTotalPnlDenominatorCny(PortfolioItem item) {
    return item.totalPnlBaseCny ??
        _metricWithRate(item.totalPnlBase, item.rateToCny) ??
        resolveCostCny(item)?.abs();
  }

  static double? resolveDayPnlBaseCny(PortfolioItem item) {
    return item.dayPnlBaseAggregateCny ??
        _metricWithRate(item.dayPnlBaseAggregate, item.rateToCny);
  }

  static double? resolveDayPnlAggregateCny(PortfolioItem item) {
    return item.dayPnlAggregateCny ??
        _metricWithRate(item.dayPnlAggregate, item.rateToCny);
  }

  static double? resolveTotalPnlCny(PortfolioItem item) {
    return item.totalPnlCny ?? _metricWithRate(item.totalPnl, item.rateToCny);
  }

  static double resolveCurrentPrice(
    PortfolioItem item, {
    PriceInfo? priceInfo,
  }) {
    if (priceInfo != null && priceInfo.price > 0) {
      return priceInfo.price;
    }
    if ((item.currentPrice ?? 0) > 0) {
      return item.currentPrice!;
    }
    if (priceInfo != null && priceInfo.yclose > 0) {
      return priceInfo.yclose;
    }
    if ((item.yclose ?? 0) > 0) {
      return item.yclose!;
    }
    return item.price;
  }

  static double resolveYclose(
    PortfolioItem item, {
    PriceInfo? priceInfo,
  }) {
    if (priceInfo != null && priceInfo.yclose > 0) {
      return priceInfo.yclose;
    }
    if ((item.yclose ?? 0) > 0) {
      return item.yclose!;
    }
    return item.price;
  }

  static double resolveRateToCny(
    PortfolioItem item, {
    double? fallbackRateToCny,
  }) {
    if ((item.rateToCny ?? 0) > 0) {
      return item.rateToCny!;
    }
    if ((fallbackRateToCny ?? 0) > 0) {
      return fallbackRateToCny!;
    }
    return 1.0;
  }

  static double resolveCost(
    PortfolioItem item, {
    double? fallbackRateToCny,
  }) {
    return item.cost ?? (item.price * item.qty);
  }

  static double resolveCostCnyLive(
    PortfolioItem item, {
    double? fallbackRateToCny,
  }) {
    if (item.costCny != null) {
      return item.costCny!;
    }
    return resolveCost(item) *
        resolveRateToCny(item, fallbackRateToCny: fallbackRateToCny);
  }

  static double resolveLiveValue(
    PortfolioItem item, {
    PriceInfo? priceInfo,
  }) {
    return resolveCurrentPrice(item, priceInfo: priceInfo) * item.qty;
  }

  static double resolveLiveValueCny(
    PortfolioItem item, {
    PriceInfo? priceInfo,
    double? fallbackRateToCny,
  }) {
    return resolveLiveValue(item, priceInfo: priceInfo) *
        resolveRateToCny(item, fallbackRateToCny: fallbackRateToCny);
  }

  static double resolveLiveFloatPnl(
    PortfolioItem item, {
    PriceInfo? priceInfo,
  }) {
    return resolveLiveValue(item, priceInfo: priceInfo) - resolveCost(item);
  }

  static double resolveLiveFloatPnlCny(
    PortfolioItem item, {
    PriceInfo? priceInfo,
    double? fallbackRateToCny,
  }) {
    return resolveLiveFloatPnl(item, priceInfo: priceInfo) *
        resolveRateToCny(item, fallbackRateToCny: fallbackRateToCny);
  }

  static double resolveLiveTotalPnl(
    PortfolioItem item, {
    PriceInfo? priceInfo,
  }) {
    return resolveLiveFloatPnl(item, priceInfo: priceInfo) + item.adjustment;
  }

  static double resolveLiveTotalPnlCny(
    PortfolioItem item, {
    PriceInfo? priceInfo,
    double? fallbackRateToCny,
  }) {
    return resolveLiveTotalPnl(item, priceInfo: priceInfo) *
        resolveRateToCny(item, fallbackRateToCny: fallbackRateToCny);
  }

  static double? resolveLiveDayPnl(
    PortfolioItem item, {
    PriceInfo? priceInfo,
  }) {
    if (item.navUpdatePending == true) {
      return null;
    }
    if (item.dayPnlAggregateEnabled == false) {
      return null;
    }
    final yclose = resolveYclose(item, priceInfo: priceInfo);
    if (yclose <= 0) {
      return null;
    }
    final currentPrice = resolveCurrentPrice(item, priceInfo: priceInfo);
    return (currentPrice - yclose) * item.qty;
  }

  static double? resolveLiveDayPnlCny(
    PortfolioItem item, {
    PriceInfo? priceInfo,
    double? fallbackRateToCny,
  }) {
    final pnl = resolveLiveDayPnl(item, priceInfo: priceInfo);
    if (pnl == null) return null;
    return pnl * resolveRateToCny(item, fallbackRateToCny: fallbackRateToCny);
  }

  static double? resolveLiveDayPnlBase(
    PortfolioItem item, {
    PriceInfo? priceInfo,
  }) {
    final yclose = resolveYclose(item, priceInfo: priceInfo);
    if (yclose <= 0) return null;
    return yclose * item.qty;
  }

  static double? resolveLiveDayPnlBaseCny(
    PortfolioItem item, {
    PriceInfo? priceInfo,
    double? fallbackRateToCny,
  }) {
    final base = resolveLiveDayPnlBase(item, priceInfo: priceInfo);
    if (base == null) return null;
    return base * resolveRateToCny(item, fallbackRateToCny: fallbackRateToCny);
  }

  static double? resolveLiveTotalPnlRate(
    PortfolioItem item, {
    PriceInfo? priceInfo,
    double? fallbackRateToCny,
  }) {
    final pnl = resolveLiveTotalPnlCny(
      item,
      priceInfo: priceInfo,
      fallbackRateToCny: fallbackRateToCny,
    );
    final denominator =
        resolveTotalPnlDenominatorCny(item) ??
        resolveCostCnyLive(item, fallbackRateToCny: fallbackRateToCny).abs();
    if (denominator <= 0) return null;
    return pnl / denominator * 100;
  }

  static double? resolveLiveHoldingPnlRate(
    PortfolioItem item, {
    PriceInfo? priceInfo,
    double? fallbackRateToCny,
  }) {
    final pnl = resolveLiveFloatPnlCny(
      item,
      priceInfo: priceInfo,
      fallbackRateToCny: fallbackRateToCny,
    );
    final costAbs = resolveCostCnyLive(
      item,
      fallbackRateToCny: fallbackRateToCny,
    ).abs();
    if (costAbs <= 0) return null;
    return pnl / costAbs * 100;
  }

  static double? resolveLiveDayPnlRate(
    PortfolioItem item, {
    PriceInfo? priceInfo,
    double? fallbackRateToCny,
  }) {
    final pnl = resolveLiveDayPnlCny(
      item,
      priceInfo: priceInfo,
      fallbackRateToCny: fallbackRateToCny,
    );
    final base = resolveLiveDayPnlBaseCny(
      item,
      priceInfo: priceInfo,
      fallbackRateToCny: fallbackRateToCny,
    );
    if (pnl == null || base == null || base <= 0) return null;
    return pnl / base * 100;
  }

  static double sumMetricIgnoreNull(
    Iterable<PortfolioItem> items,
    double? Function(PortfolioItem item) pick,
  ) {
    double total = 0;
    for (final item in items) {
      final value = pick(item);
      if (value != null) {
        total += value;
      }
    }
    return total;
  }

  static double? sumMetricOrNull(
    Iterable<PortfolioItem> items,
    double? Function(PortfolioItem item) pick,
  ) {
    var hasAny = false;
    double total = 0;
    for (final item in items) {
      final value = pick(item);
      if (value == null) return null;
      hasAny = true;
      total += value;
    }
    return hasAny ? total : null;
  }

  static double? sumMetricWhenAny(
    Iterable<PortfolioItem> items,
    double? Function(PortfolioItem item) pick,
  ) {
    var hasAny = false;
    double total = 0;
    for (final item in items) {
      final value = pick(item);
      if (value == null) continue;
      hasAny = true;
      total += value;
    }
    return hasAny ? total : null;
  }

  static double? sumAbsMetricOrNull(
    Iterable<PortfolioItem> items,
    double? Function(PortfolioItem item) pick,
  ) {
    var hasAny = false;
    double total = 0;
    for (final item in items) {
      final value = pick(item);
      if (value == null) return null;
      hasAny = true;
      total += value.abs();
    }
    return hasAny ? total : null;
  }

  static double calcInvestTotalMV(Iterable<PortfolioItem> items) {
    return sumMetricIgnoreNull(items, resolveValueCny);
  }

  static double calcInvestDayPnl(Iterable<PortfolioItem> items) {
    return sumMetricIgnoreNull(items, resolveDayPnlAggregateCny);
  }

  static double calcInvestHoldingPnl(Iterable<PortfolioItem> items) {
    return sumMetricIgnoreNull(items, resolveFloatPnlCny);
  }

  static double calcInvestDayPnlRate(Iterable<PortfolioItem> items) {
    double pnl = 0;
    double base = 0;
    var hasMetrics = false;
    for (final item in items) {
      final dayPnlCny = resolveDayPnlAggregateCny(item);
      final dayPnlBaseCny = resolveDayPnlBaseCny(item);
      if (dayPnlCny != null && dayPnlBaseCny != null) {
        pnl += dayPnlCny;
        base += dayPnlBaseCny;
        hasMetrics = true;
      }
    }
    if (!hasMetrics || base <= 0) return 0;
    return pnl / base * 100;
  }

  static double calcInvestHoldingPnlRate(Iterable<PortfolioItem> items) {
    double totalCostAbs = 0;
    var hasMetrics = false;
    for (final item in items) {
      final costCny = resolveCostCny(item);
      if (costCny != null) {
        totalCostAbs += costCny.abs();
        hasMetrics = true;
      }
    }
    if (!hasMetrics || totalCostAbs <= 0) return 0;
    final holdingPnl = calcInvestHoldingPnl(items);
    return holdingPnl / totalCostAbs * 100;
  }

  static double calcInvestTotalPnl(Iterable<PortfolioItem> items) {
    return sumMetricIgnoreNull(items, resolveTotalPnlCny);
  }

  static double calcInvestTotalPnlRate(Iterable<PortfolioItem> items) {
    double totalPnlDenominator = 0;
    var hasMetrics = false;
    for (final item in items) {
      final denominatorCny = resolveTotalPnlDenominatorCny(item);
      if (denominatorCny != null) {
        totalPnlDenominator += denominatorCny;
        hasMetrics = true;
      }
    }
    if (!hasMetrics || totalPnlDenominator <= 0) return 0;
    final totalPnl = calcInvestTotalPnl(items);
    return totalPnl / totalPnlDenominator * 100;
  }

  static double? calcDayPnlRateNullable(double? pnl, double? base) {
    if (pnl == null || base == null || base <= 0) return null;
    return pnl / base * 100;
  }

  static double? calcHoldingPnlRateNullable(double? pnl, double? costAbs) {
    if (pnl == null || costAbs == null || costAbs <= 0) return null;
    return pnl / costAbs * 100;
  }
}
