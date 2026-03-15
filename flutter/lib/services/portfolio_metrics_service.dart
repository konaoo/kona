import '../models/portfolio.dart';

/// 投资口径汇总与汇率计算的集中入口
class PortfolioMetricsService {
  const PortfolioMetricsService._();

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
    return sumMetricIgnoreNull(items, (item) => item.valueCny);
  }

  static double calcInvestDayPnl(Iterable<PortfolioItem> items) {
    return sumMetricIgnoreNull(items, (item) => item.dayPnlAggregateCny);
  }

  static double calcInvestHoldingPnl(Iterable<PortfolioItem> items) {
    return sumMetricIgnoreNull(items, (item) => item.totalPnlCny);
  }

  static double calcInvestDayPnlRate(Iterable<PortfolioItem> items) {
    double pnl = 0;
    double base = 0;
    var hasMetrics = false;
    for (final item in items) {
      final dayPnlCny = item.dayPnlAggregateCny;
      final valueCny = item.valueCny;
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
      final costCny = item.costCny;
      if (costCny != null) {
        totalCostAbs += costCny.abs();
        hasMetrics = true;
      }
    }
    if (!hasMetrics || totalCostAbs <= 0) return 0;
    final holdingPnl = calcInvestHoldingPnl(items);
    return holdingPnl / totalCostAbs * 100;
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
