import 'package:flutter_test/flutter_test.dart';
import 'package:tool/models/portfolio.dart';
import 'package:tool/services/portfolio_metrics_service.dart';

void main() {
  PortfolioItem buildItem({
    double? valueCny,
    double? costCny,
    double? dayPnlAggregateCny,
    double? totalPnlCny,
    double? value,
    double? cost,
    double? dayPnlAggregate,
    double? totalPnl,
    double? rateToCny,
  }) {
    return PortfolioItem(
      code: 'sh600000',
      name: '测试资产',
      qty: 10,
      price: 10,
      valueCny: valueCny,
      costCny: costCny,
      dayPnlAggregateCny: dayPnlAggregateCny,
      totalPnlCny: totalPnlCny,
      value: value,
      cost: cost,
      dayPnlAggregate: dayPnlAggregate,
      totalPnl: totalPnl,
      rateToCny: rateToCny,
    );
  }

  test('优先使用后端直接返回的 CNY 指标', () {
    final item = buildItem(
      valueCny: 1200,
      costCny: 900,
      dayPnlAggregateCny: 80,
      totalPnlCny: 300,
      value: 999,
      cost: 999,
      dayPnlAggregate: 999,
      totalPnl: 999,
      rateToCny: 7.2,
    );

    expect(PortfolioMetricsService.resolveValueCny(item), 1200);
    expect(PortfolioMetricsService.resolveCostCny(item), 900);
    expect(PortfolioMetricsService.resolveDayPnlAggregateCny(item), 80);
    expect(PortfolioMetricsService.resolveTotalPnlCny(item), 300);
  });

  test('缺少 CNY 指标时回退到后端行指标乘汇率', () {
    final item = buildItem(
      value: 100,
      cost: 80,
      dayPnlAggregate: 5,
      totalPnl: 20,
      rateToCny: 7.2,
    );

    expect(PortfolioMetricsService.resolveValueCny(item), closeTo(720, 1e-6));
    expect(PortfolioMetricsService.resolveCostCny(item), closeTo(576, 1e-6));
    expect(
      PortfolioMetricsService.resolveDayPnlAggregateCny(item),
      closeTo(36, 1e-6),
    );
    expect(
      PortfolioMetricsService.resolveTotalPnlCny(item),
      closeTo(144, 1e-6),
    );
  });
}
