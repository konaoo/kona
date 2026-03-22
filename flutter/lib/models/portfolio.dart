import '../utils/asset_name_utils.dart';

/// 投资组合项目模型
class PortfolioItem {
  final int? id;
  final String code;
  final String name;
  final double qty;
  final double price;
  final double adjustment;
  final String curr;
  final String assetType;
  final String? market;
  final double? currentPrice;
  final double? yclose;
  final double? displayCostPrice;
  final double? cost;
  final double? rawCostTotal;
  final double? value;
  final double? positionPct;
  final double? totalPnl;
  final double? totalPnlBase;
  final double? totalPnlRate;
  final double? dayPnl;
  final double? dayPnlBase;
  final double? dayPnlRate;
  final double? dayPnlDisplay;
  final double? dayPnlBaseDisplay;
  final double? dayPnlRateDisplay;
  final double? dayPnlAggregate;
  final double? dayPnlBaseAggregate;
  final double? dayPnlRateAggregate;
  final bool? navUpdatePending;
  final String? latestNavDate;
  final bool? dayPnlDisplayEnabled;
  final bool? dayPnlAggregateEnabled;
  final bool? marketOpen;
  final bool? marketTradingDay;
  final String? marketStatusReason;
  final double? rateToCny;
  final double? valueCny;
  final double? costCny;
  final double? totalPnlCny;
  final double? totalPnlBaseCny;
  final double? dayPnlCny;
  final double? dayPnlBaseCny;
  final double? dayPnlAggregateCny;
  final double? dayPnlBaseAggregateCny;
  final double? quotePrice;
  final double? quoteChange;
  final double? quoteChangePct;

  PortfolioItem({
    this.id,
    required this.code,
    required this.name,
    required this.qty,
    required this.price,
    this.adjustment = 0,
    this.curr = 'CNY',
    this.assetType = '',
    this.market,
    this.currentPrice,
    this.yclose,
    this.displayCostPrice,
    this.cost,
    this.rawCostTotal,
    this.value,
    this.positionPct,
    this.totalPnl,
    this.totalPnlBase,
    this.totalPnlRate,
    this.dayPnl,
    this.dayPnlBase,
    this.dayPnlRate,
    this.dayPnlDisplay,
    this.dayPnlBaseDisplay,
    this.dayPnlRateDisplay,
    this.dayPnlAggregate,
    this.dayPnlBaseAggregate,
    this.dayPnlRateAggregate,
    this.navUpdatePending,
    this.latestNavDate,
    this.dayPnlDisplayEnabled,
    this.dayPnlAggregateEnabled,
    this.marketOpen,
    this.marketTradingDay,
    this.marketStatusReason,
    this.rateToCny,
    this.valueCny,
    this.costCny,
    this.totalPnlCny,
    this.totalPnlBaseCny,
    this.dayPnlCny,
    this.dayPnlBaseCny,
    this.dayPnlAggregateCny,
    this.dayPnlBaseAggregateCny,
    this.quotePrice,
    this.quoteChange,
    this.quoteChangePct,
  });

  factory PortfolioItem.fromJson(Map<String, dynamic> json) {
    return PortfolioItem(
      id: json['id'],
      code: json['code'] ?? '',
      name: json['name'] ?? '',
      qty: _parseDouble(json['qty']),
      price: _parseDouble(json['price']),
      adjustment: _parseDouble(json['adjustment']),
      curr: json['curr'] ?? 'CNY',
      assetType: json['asset_type'] ?? json['assetType'] ?? '',
      market: _parseString(json['market'] ?? json['category']),
      currentPrice: _parseDoubleOrNull(json['current_price']),
      yclose: _parseDoubleOrNull(json['yclose']),
      displayCostPrice: _parseDoubleOrNull(json['display_cost_price']),
      cost: _parseDoubleOrNull(json['cost']),
      rawCostTotal: _parseDoubleOrNull(json['raw_cost_total']),
      value: _parseDoubleOrNull(json['value']),
      positionPct: _parseDoubleOrNull(
        json['position_pct'] ??
            json['positionPct'] ??
            json['pct'] ??
            json['holding_pct'] ??
            json['holdingPct'] ??
            json['portfolio_pct'] ??
            json['portfolioPct'],
      ),
      totalPnl: _parseDoubleOrNull(json['total_pnl']),
      totalPnlBase: _parseDoubleOrNull(json['total_pnl_base']),
      totalPnlRate: _parseDoubleOrNull(json['total_pnl_rate']),
      dayPnl: _parseDoubleOrNull(json['day_pnl']),
      dayPnlBase: _parseDoubleOrNull(json['day_pnl_base']),
      dayPnlRate: _parseDoubleOrNull(json['day_pnl_rate']),
      dayPnlDisplay: _parseDoubleOrNull(json['day_pnl_display']),
      dayPnlBaseDisplay: _parseDoubleOrNull(json['day_pnl_base_display']),
      dayPnlRateDisplay: _parseDoubleOrNull(json['day_pnl_rate_display']),
      dayPnlAggregate: _parseDoubleOrNull(json['day_pnl_aggregate']),
      dayPnlBaseAggregate: _parseDoubleOrNull(json['day_pnl_base_aggregate']),
      dayPnlRateAggregate: _parseDoubleOrNull(json['day_pnl_rate_aggregate']),
      navUpdatePending: _parseBoolOrNull(json['nav_update_pending']),
      latestNavDate: _parseString(
        json['latest_nav_date'] ?? json['latestNavDate'],
      ),
      dayPnlDisplayEnabled: _parseBoolOrNull(json['day_pnl_display_enabled']),
      dayPnlAggregateEnabled: _parseBoolOrNull(
        json['day_pnl_aggregate_enabled'],
      ),
      marketOpen: _parseBoolOrNull(json['market_open']),
      marketTradingDay: _parseBoolOrNull(json['market_trading_day']),
      marketStatusReason: _parseString(json['market_status_reason']),
      rateToCny: _parseDoubleOrNull(json['rate_to_cny']),
      valueCny: _parseDoubleOrNull(json['value_cny']),
      costCny: _parseDoubleOrNull(json['cost_cny']),
      totalPnlCny: _parseDoubleOrNull(json['total_pnl_cny']),
      totalPnlBaseCny: _parseDoubleOrNull(json['total_pnl_base_cny']),
      dayPnlCny: _parseDoubleOrNull(json['day_pnl_cny']),
      dayPnlBaseCny: _parseDoubleOrNull(json['day_pnl_base_cny']),
      dayPnlAggregateCny: _parseDoubleOrNull(json['day_pnl_aggregate_cny']),
      dayPnlBaseAggregateCny: _parseDoubleOrNull(
        json['day_pnl_base_aggregate_cny'],
      ),
      quotePrice: _parseDoubleOrNull(json['quote_price']),
      quoteChange: _parseDoubleOrNull(json['quote_change']),
      quoteChangePct: _parseDoubleOrNull(json['quote_change_pct']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'code': code,
      'name': name,
      'qty': qty,
      'price': price,
      'adjustment': adjustment,
      'curr': curr,
      'asset_type': assetType,
      if (market != null) 'market': market,
      if (currentPrice != null) 'current_price': currentPrice,
      if (yclose != null) 'yclose': yclose,
      if (displayCostPrice != null) 'display_cost_price': displayCostPrice,
      if (cost != null) 'cost': cost,
      if (rawCostTotal != null) 'raw_cost_total': rawCostTotal,
      if (value != null) 'value': value,
      if (positionPct != null) 'position_pct': positionPct,
      if (totalPnl != null) 'total_pnl': totalPnl,
      if (totalPnlBase != null) 'total_pnl_base': totalPnlBase,
      if (totalPnlRate != null) 'total_pnl_rate': totalPnlRate,
      if (dayPnl != null) 'day_pnl': dayPnl,
      if (dayPnlBase != null) 'day_pnl_base': dayPnlBase,
      if (dayPnlRate != null) 'day_pnl_rate': dayPnlRate,
      if (dayPnlDisplay != null) 'day_pnl_display': dayPnlDisplay,
      if (dayPnlBaseDisplay != null) 'day_pnl_base_display': dayPnlBaseDisplay,
      if (dayPnlRateDisplay != null) 'day_pnl_rate_display': dayPnlRateDisplay,
      if (dayPnlAggregate != null) 'day_pnl_aggregate': dayPnlAggregate,
      if (dayPnlBaseAggregate != null)
        'day_pnl_base_aggregate': dayPnlBaseAggregate,
      if (dayPnlRateAggregate != null)
        'day_pnl_rate_aggregate': dayPnlRateAggregate,
      if (navUpdatePending != null) 'nav_update_pending': navUpdatePending,
      if (latestNavDate != null) 'latest_nav_date': latestNavDate,
      if (dayPnlDisplayEnabled != null)
        'day_pnl_display_enabled': dayPnlDisplayEnabled,
      if (dayPnlAggregateEnabled != null)
        'day_pnl_aggregate_enabled': dayPnlAggregateEnabled,
      if (marketOpen != null) 'market_open': marketOpen,
      if (marketTradingDay != null) 'market_trading_day': marketTradingDay,
      if (marketStatusReason != null)
        'market_status_reason': marketStatusReason,
      if (rateToCny != null) 'rate_to_cny': rateToCny,
      if (valueCny != null) 'value_cny': valueCny,
      if (costCny != null) 'cost_cny': costCny,
      if (totalPnlCny != null) 'total_pnl_cny': totalPnlCny,
      if (totalPnlBaseCny != null) 'total_pnl_base_cny': totalPnlBaseCny,
      if (dayPnlCny != null) 'day_pnl_cny': dayPnlCny,
      if (dayPnlBaseCny != null) 'day_pnl_base_cny': dayPnlBaseCny,
      if (dayPnlAggregateCny != null)
        'day_pnl_aggregate_cny': dayPnlAggregateCny,
      if (dayPnlBaseAggregateCny != null)
        'day_pnl_base_aggregate_cny': dayPnlBaseAggregateCny,
      if (quotePrice != null) 'quote_price': quotePrice,
      if (quoteChange != null) 'quote_change': quoteChange,
      if (quoteChangePct != null) 'quote_change_pct': quoteChangePct,
    };
  }

  String get displayName => formatAssetDisplayName(name);

  /// 获取市场类型
  String get marketType {
    final mkt = (market ?? '').trim().toLowerCase();
    if (mkt.isNotEmpty) return mkt;
    if (assetType.isNotEmpty) return assetType;
    final lowerCode = code.toLowerCase();
    if (lowerCode.startsWith('hk')) return 'hk';
    if (lowerCode.startsWith('gb_') || lowerCode.startsWith('us')) return 'us';
    if (lowerCode.startsWith('f_') || lowerCode.startsWith('ft_')) {
      return 'fund';
    }
    return 'a';
  }

  /// 获取币种符号
  String get currencySymbol {
    switch (curr.toUpperCase()) {
      case 'HKD':
        return 'HK\$';
      case 'USD':
        return '\$';
      default:
        return '¥';
    }
  }

  static double _parseDouble(dynamic value) {
    if (value == null) return 0;
    if (value is double) return value;
    if (value is int) return value.toDouble();
    if (value is String) return double.tryParse(value) ?? 0;
    return 0;
  }

  static double? _parseDoubleOrNull(dynamic value) {
    if (value == null) return null;
    if (value is double) return value;
    if (value is int) return value.toDouble();
    if (value is String) return double.tryParse(value);
    return null;
  }

  static bool? _parseBoolOrNull(dynamic value) {
    if (value == null) return null;
    if (value is bool) return value;
    if (value is num) return value != 0;
    if (value is String) {
      final normalized = value.trim().toLowerCase();
      if (normalized.isEmpty) return null;
      return normalized == '1' || normalized == 'true' || normalized == 'yes';
    }
    return null;
  }

  static String? _parseString(dynamic value) {
    if (value is String && value.trim().isNotEmpty) return value.trim();
    return null;
  }
}

/// 价格信息模型
class PriceInfo {
  final double price;
  final double yclose;
  final double change;
  final double changePct;
  final double regularPrice;
  final double premarketPrice;
  final double afterHoursPrice;
  final String session;
  final String effectiveSession;
  final bool extendedActive;

  PriceInfo({
    required this.price,
    required this.yclose,
    required this.change,
    required this.changePct,
    this.regularPrice = 0,
    this.premarketPrice = 0,
    this.afterHoursPrice = 0,
    this.session = 'closed',
    this.effectiveSession = 'closed',
    this.extendedActive = false,
  });

  factory PriceInfo.fromJson(Map<String, dynamic> json) {
    final price = _parseDouble(json['price']);
    final yclose = _parseDouble(json['yclose']);
    // 兼容后端/缓存不同字段命名；缺失时用 price-yclose 回推涨跌额。
    final amtRaw = json['amt'] ?? json['change'] ?? json['delta'];
    final amt = _parseDouble(amtRaw);
    final inferredAmt = (amt == 0 && price > 0 && yclose > 0)
        ? (price - yclose)
        : amt;
    final chgRaw = json['chg'] ?? json['change_pct'] ?? json['pct'];
    final chg = _parseDouble(chgRaw);
    final session = _parseString(json['session'], fallback: 'closed');
    final effectiveSession = _parseString(
      json['effective_session'],
      fallback: session,
    );
    final extendedActive = _parseBool(json['extended_active']);
    return PriceInfo(
      price: price,
      yclose: yclose,
      change: inferredAmt,
      changePct: chg != 0
          ? chg
          : (yclose > 0 ? (inferredAmt / yclose * 100) : 0),
      regularPrice: _parseDouble(json['regular_price']),
      premarketPrice: _parseDouble(json['premarket_price']),
      afterHoursPrice: _parseDouble(json['after_hours_price']),
      session: session,
      effectiveSession: effectiveSession,
      extendedActive: extendedActive,
    );
  }

  PriceInfo withDayChangeZeroed() {
    return PriceInfo(
      price: price,
      yclose: yclose,
      change: 0,
      changePct: 0,
      regularPrice: regularPrice,
      premarketPrice: premarketPrice,
      afterHoursPrice: afterHoursPrice,
      session: session,
      effectiveSession: effectiveSession,
      extendedActive: extendedActive,
    );
  }

  static bool _parseBool(dynamic value) {
    if (value is bool) return value;
    if (value is num) return value != 0;
    if (value is String) {
      final normalized = value.trim().toLowerCase();
      return normalized == '1' || normalized == 'true' || normalized == 'yes';
    }
    return false;
  }

  static String _parseString(dynamic value, {required String fallback}) {
    if (value is String) {
      final text = value.trim();
      if (text.isNotEmpty) return text;
    }
    return fallback;
  }

  static double _parseDouble(dynamic value) {
    if (value == null) return 0;
    if (value is double) return value;
    if (value is int) return value.toDouble();
    if (value is String) return double.tryParse(value) ?? 0;
    return 0;
  }
}
