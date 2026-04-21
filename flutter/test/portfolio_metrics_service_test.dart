import 'package:flutter_test/flutter_test.dart';
import 'package:tool/models/portfolio.dart';
import 'package:tool/services/portfolio_metrics_service.dart';

void main() {
  PortfolioItem buildItem({
    double? valueCny,
    double? costCny,
    double? dayPnlAggregateCny,
    double? dayPnlBaseAggregateCny,
    double? totalPnlCny,
    double? value,
    double? cost,
    double? dayPnlAggregate,
    double? dayPnlBaseAggregate,
    double? totalPnl,
    double? rateToCny,
    bool? marketOpen,
    bool? marketTradingDay,
    String? marketStatusReason,
    bool? dayPnlAggregateEnabled,
    bool? navUpdatePending,
    String market = 'a',
  }) {
    return PortfolioItem(
      code: 'sh600000',
      name: '测试资产',
      qty: 10,
      price: 10,
      market: market,
      valueCny: valueCny,
      costCny: costCny,
      dayPnlAggregateCny: dayPnlAggregateCny,
      dayPnlBaseAggregateCny: dayPnlBaseAggregateCny,
      totalPnlCny: totalPnlCny,
      value: value,
      cost: cost,
      dayPnlAggregate: dayPnlAggregate,
      dayPnlBaseAggregate: dayPnlBaseAggregate,
      totalPnl: totalPnl,
      rateToCny: rateToCny,
      marketOpen: marketOpen,
      marketTradingDay: marketTradingDay,
      marketStatusReason: marketStatusReason,
      dayPnlAggregateEnabled: dayPnlAggregateEnabled,
      navUpdatePending: navUpdatePending,
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

  test('实时价格会驱动市值与盈亏重算', () {
    final item = PortfolioItem(
      code: 'sh600000',
      name: '测试资产',
      qty: 10,
      price: 10,
      cost: 100,
      adjustment: 15,
      curr: 'CNY',
    );
    final priceInfo = PriceInfo(
      price: 12,
      yclose: 11,
      change: 1,
      changePct: 9.09,
    );

    expect(
      PortfolioMetricsService.resolveLiveValue(item, priceInfo: priceInfo),
      120,
    );
    expect(
      PortfolioMetricsService.resolveLiveFloatPnl(item, priceInfo: priceInfo),
      20,
    );
    expect(
      PortfolioMetricsService.resolveLiveTotalPnl(item, priceInfo: priceInfo),
      35,
    );
    expect(
      PortfolioMetricsService.resolveLiveDayPnl(item, priceInfo: priceInfo),
      10,
    );
    expect(
      PortfolioMetricsService.resolveLiveDayPnlRate(item, priceInfo: priceInfo),
      closeTo(9.0909, 1e-4),
    );
  });

  test('缺少 currentPrice 时会回退到 quotePrice 或 value/qty', () {
    final fromQuotePrice = PortfolioItem(
      code: '00700.HK',
      name: '腾讯控股',
      qty: 100,
      price: 500,
      curr: 'HKD',
      quotePrice: 520,
      value: 52000,
    );
    final fromValue = PortfolioItem(
      code: '00175.HK',
      name: '吉利汽车',
      qty: 1000,
      price: 15,
      curr: 'HKD',
      value: 23920,
    );

    expect(PortfolioMetricsService.resolveCurrentPrice(fromQuotePrice), 520);
    expect(
      PortfolioMetricsService.resolveCurrentPrice(fromValue),
      closeTo(23.92, 1e-6),
    );
  });

  test('sumMetricWhenAny 会忽略缺失项，只在全空时返回空', () {
    final items = <PortfolioItem>[
      buildItem(dayPnlAggregateCny: 12),
      buildItem(dayPnlAggregateCny: null),
      buildItem(dayPnlAggregateCny: -2),
    ];

    expect(
      PortfolioMetricsService.sumMetricWhenAny(
        items,
        (item) => item.dayPnlAggregateCny,
      ),
      10,
    );
    expect(
      PortfolioMetricsService.sumMetricWhenAny(
        <PortfolioItem>[buildItem(dayPnlAggregateCny: null)],
        (item) => item.dayPnlAggregateCny,
      ),
      isNull,
    );
  });

  test('当前日盈亏会在缺少实时口径时回退到后端 aggregate 字段', () {
    final item = buildItem(
      navUpdatePending: true,
      dayPnlAggregate: 5,
      dayPnlAggregateCny: 5,
      dayPnlBaseAggregate: 100,
      dayPnlBaseAggregateCny: 100,
      rateToCny: 1,
      market: 'fund',
    );

    expect(PortfolioMetricsService.resolveCurrentDayPnl(item), 5);
    expect(PortfolioMetricsService.resolveCurrentDayPnlCny(item), 5);
    expect(PortfolioMetricsService.resolveCurrentDayPnlBase(item), 100);
    expect(PortfolioMetricsService.resolveCurrentDayPnlBaseCny(item), 100);
    expect(PortfolioMetricsService.resolveCurrentDayPnlRate(item), 5);
  });

  test('交易日盘前的 A/HK/基金今日盈亏会被压成 0', () {
    final item = buildItem(
      market: 'fund',
      marketOpen: false,
      marketTradingDay: true,
      marketStatusReason: 'off_hours',
      dayPnlAggregateEnabled: true,
      dayPnlAggregate: 88,
      dayPnlAggregateCny: 88,
      dayPnlBaseAggregate: 1000,
      dayPnlBaseAggregateCny: 1000,
      rateToCny: 1,
    );
    final priceInfo = PriceInfo(
      price: 101.5,
      yclose: 100.5,
      change: 1.0,
      changePct: 0.99,
    );

    expect(
      PortfolioMetricsService.isPreopenOffHoursAsset(
        item,
        now: DateTime(2026, 3, 24, 9, 15),
      ),
      isTrue,
    );
    expect(
      PortfolioMetricsService.resolveCurrentDayPnl(
        item,
        priceInfo: priceInfo,
        now: DateTime(2026, 3, 24, 9, 15),
      ),
      0,
    );
    expect(
      PortfolioMetricsService.resolveCurrentDayPnlCny(
        item,
        priceInfo: priceInfo,
        fallbackRateToCny: 1,
        now: DateTime(2026, 3, 24, 9, 15),
      ),
      0,
    );
    expect(
      PortfolioMetricsService.resolveCurrentDayPnlRate(
        item,
        priceInfo: priceInfo,
        fallbackRateToCny: 1,
        now: DateTime(2026, 3, 24, 9, 15),
      ),
      0,
    );
  });
}
