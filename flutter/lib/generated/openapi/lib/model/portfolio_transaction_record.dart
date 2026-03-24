//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class PortfolioTransactionRecord {
  /// Returns a new [PortfolioTransactionRecord] instance.
  PortfolioTransactionRecord({
    this.type,
    this.time,
    this.note,
    this.price,
    this.qty,
    this.amount,
    this.pnl,
    this.beforeQty,
    this.afterQty,
    this.beforePrice,
    this.afterPrice,
  });

  /// 交易、收益事件或修正记录的中文类型名
  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? type;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? time;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? note;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? price;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? qty;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? amount;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? pnl;

  num? beforeQty;

  num? afterQty;

  num? beforePrice;

  num? afterPrice;

  @override
  bool operator ==(Object other) => identical(this, other) || other is PortfolioTransactionRecord &&
    other.type == type &&
    other.time == time &&
    other.note == note &&
    other.price == price &&
    other.qty == qty &&
    other.amount == amount &&
    other.pnl == pnl &&
    other.beforeQty == beforeQty &&
    other.afterQty == afterQty &&
    other.beforePrice == beforePrice &&
    other.afterPrice == afterPrice;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (type == null ? 0 : type!.hashCode) +
    (time == null ? 0 : time!.hashCode) +
    (note == null ? 0 : note!.hashCode) +
    (price == null ? 0 : price!.hashCode) +
    (qty == null ? 0 : qty!.hashCode) +
    (amount == null ? 0 : amount!.hashCode) +
    (pnl == null ? 0 : pnl!.hashCode) +
    (beforeQty == null ? 0 : beforeQty!.hashCode) +
    (afterQty == null ? 0 : afterQty!.hashCode) +
    (beforePrice == null ? 0 : beforePrice!.hashCode) +
    (afterPrice == null ? 0 : afterPrice!.hashCode);

  @override
  String toString() => 'PortfolioTransactionRecord[type=$type, time=$time, note=$note, price=$price, qty=$qty, amount=$amount, pnl=$pnl, beforeQty=$beforeQty, afterQty=$afterQty, beforePrice=$beforePrice, afterPrice=$afterPrice]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.type != null) {
      json[r'type'] = this.type;
    } else {
      json[r'type'] = null;
    }
    if (this.time != null) {
      json[r'time'] = this.time;
    } else {
      json[r'time'] = null;
    }
    if (this.note != null) {
      json[r'note'] = this.note;
    } else {
      json[r'note'] = null;
    }
    if (this.price != null) {
      json[r'price'] = this.price;
    } else {
      json[r'price'] = null;
    }
    if (this.qty != null) {
      json[r'qty'] = this.qty;
    } else {
      json[r'qty'] = null;
    }
    if (this.amount != null) {
      json[r'amount'] = this.amount;
    } else {
      json[r'amount'] = null;
    }
    if (this.pnl != null) {
      json[r'pnl'] = this.pnl;
    } else {
      json[r'pnl'] = null;
    }
    if (this.beforeQty != null) {
      json[r'before_qty'] = this.beforeQty;
    } else {
      json[r'before_qty'] = null;
    }
    if (this.afterQty != null) {
      json[r'after_qty'] = this.afterQty;
    } else {
      json[r'after_qty'] = null;
    }
    if (this.beforePrice != null) {
      json[r'before_price'] = this.beforePrice;
    } else {
      json[r'before_price'] = null;
    }
    if (this.afterPrice != null) {
      json[r'after_price'] = this.afterPrice;
    } else {
      json[r'after_price'] = null;
    }
    return json;
  }

  /// Returns a new [PortfolioTransactionRecord] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static PortfolioTransactionRecord? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "PortfolioTransactionRecord[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "PortfolioTransactionRecord[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return PortfolioTransactionRecord(
        type: mapValueOfType<String>(json, r'type'),
        time: mapValueOfType<String>(json, r'time'),
        note: mapValueOfType<String>(json, r'note'),
        price: num.parse('${json[r'price']}'),
        qty: num.parse('${json[r'qty']}'),
        amount: num.parse('${json[r'amount']}'),
        pnl: num.parse('${json[r'pnl']}'),
        beforeQty: json[r'before_qty'] == null
            ? null
            : num.parse('${json[r'before_qty']}'),
        afterQty: json[r'after_qty'] == null
            ? null
            : num.parse('${json[r'after_qty']}'),
        beforePrice: json[r'before_price'] == null
            ? null
            : num.parse('${json[r'before_price']}'),
        afterPrice: json[r'after_price'] == null
            ? null
            : num.parse('${json[r'after_price']}'),
      );
    }
    return null;
  }

  static List<PortfolioTransactionRecord> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <PortfolioTransactionRecord>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = PortfolioTransactionRecord.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, PortfolioTransactionRecord> mapFromJson(dynamic json) {
    final map = <String, PortfolioTransactionRecord>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = PortfolioTransactionRecord.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of PortfolioTransactionRecord-objects as value to a dart map
  static Map<String, List<PortfolioTransactionRecord>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<PortfolioTransactionRecord>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = PortfolioTransactionRecord.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

