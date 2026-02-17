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

  PortfolioItem({
    this.id,
    required this.code,
    required this.name,
    required this.qty,
    required this.price,
    this.adjustment = 0,
    this.curr = 'CNY',
    this.assetType = '',
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
    };
  }

  /// 获取市场类型
  String get marketType {
    if (assetType.isNotEmpty) return assetType;
    final lowerCode = code.toLowerCase();
    if (lowerCode.startsWith('hk')) return 'hk';
    if (lowerCode.startsWith('gb_') || lowerCode.startsWith('us')) return 'us';
    if (lowerCode.startsWith('f_') || lowerCode.startsWith('ft_'))
      return 'fund';
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
