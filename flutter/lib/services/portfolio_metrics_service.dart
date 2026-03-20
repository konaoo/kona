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

  static double resolvePositiveAdjustmentCny(PortfolioItem item) {
    final adjustmentCny = _metricWithRate(item.adjustment, item.rateToCny) ?? 0;
    return adjustmentCny > 0 ? adjustmentCny : 0;
  }

  static double? resolveTotalPnlDenominatorCny(PortfolioItem item) {
    final costCny = resolveCostCny(item);
    if (costCny == null) return null;
    return costCny.abs() + resolvePositiveAdjustmentCny(item);
  }

  static double? resolveDayPnlAggregateCny(PortfolioItem item) {
    return item.dayPnlAggregateCny ??
        _metricWithRate(item.dayPnlAggregate, item.rateToCny);
  }

  static double? resolveTotalPnlCny(PortfolioItem item) {
    return item.totalPnlCny ?? _metricWithRate(item.totalPnl, item.rateToCny);
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
      final valueCny = resolveValueCny(item);
      if (dayPnlCny != null && valueCny != null) {
        pnl += dayPnlCny;
        base += (valueCny - dayPnlCny);
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

  static double? calcDayPnlRateNullable(double? pnl, double? totalValue) {
    if (pnl == null || totalValue == null) return null;
    final base = totalValue - pnl;
    if (base <= 0) return null;
    return pnl / base * 100;
  }

  static double? calcHoldingPnlRateNullable(double? pnl, double? costAbs) {
    if (pnl == null || costAbs == null || costAbs <= 0) return null;
    return pnl / costAbs * 100;
  }
}
