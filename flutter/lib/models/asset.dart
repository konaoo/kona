/// 资产模型（现金、其他资产、负债）
class Asset {
  final int? id;
  final String name;
  final double amount;
  final String curr;

  Asset({
    this.id,
    required this.name,
    required this.amount,
    this.curr = 'CNY',
  });

  factory Asset.fromJson(Map<String, dynamic> json) {
    return Asset(
      id: json['id'],
      name: json['name'] ?? '',
      amount: _parseDouble(json['amount']),
      curr: json['curr'] ?? 'CNY',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'amount': amount,
      'curr': curr,
    };
  }

  static double _parseDouble(dynamic value) {
    if (value == null) return 0;
    if (value is double) return value;
    if (value is int) return value.toDouble();
    if (value is String) return double.tryParse(value) ?? 0;
    return 0;
  }
}
