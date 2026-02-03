/// 投资组合项目模型
class PortfolioItem {
  final int? id;
  final String code;
  final String name;
  final double qty;
  final double price;
  final double adjustment;
  final String curr;

  PortfolioItem({
    this.id,
    required this.code,
    required this.name,
    required this.qty,
    required this.price,
    this.adjustment = 0,
    this.curr = 'CNY',
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
    };
  }

  /// 获取市场类型
  String get marketType {
    final lowerCode = code.toLowerCase();
    if (lowerCode.startsWith('hk')) return 'hk';
    if (lowerCode.startsWith('gb_') || lowerCode.startsWith('us')) return 'us';
    if (lowerCode.startsWith('f_') || lowerCode.startsWith('ft_')) return 'fund';
    return 'a';
  }

  /// 获取币种符号
  String get currencySymbol {
    switch (marketType) {
      case 'hk':
        return 'HK\$';
      case 'us':
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

  PriceInfo({
    required this.price,
    required this.yclose,
    required this.change,
    required this.changePct,
  });

  factory PriceInfo.fromJson(Map<String, dynamic> json) {
    final price = _parseDouble(json['price']);
    final yclose = _parseDouble(json['yclose']);
    final amt = _parseDouble(json['amt']);  // 涨跌额
    final chg = _parseDouble(json['chg']);  // 涨跌幅%
    return PriceInfo(
      price: price,
      yclose: yclose,
      change: amt,
      changePct: chg != 0 ? chg : (yclose > 0 ? (amt / yclose * 100) : 0),
    );
  }

  static double _parseDouble(dynamic value) {
    if (value == null) return 0;
    if (value is double) return value;
    if (value is int) return value.toDouble();
    if (value is String) return double.tryParse(value) ?? 0;
    return 0;
  }
}
