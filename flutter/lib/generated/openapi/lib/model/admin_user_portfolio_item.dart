//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AdminUserPortfolioItem {
  /// Returns a new [AdminUserPortfolioItem] instance.
  AdminUserPortfolioItem({
    this.code,
    this.name,
    this.qty,
    this.price,
    this.curr,
    this.assetType,
    this.latestPrice,
    this.pnlCny,
    this.pnlRate,
    this.typeLabel,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? code;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? name;

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
  num? price;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? curr;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? assetType;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? latestPrice;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? pnlCny;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? pnlRate;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? typeLabel;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AdminUserPortfolioItem &&
    other.code == code &&
    other.name == name &&
    other.qty == qty &&
    other.price == price &&
    other.curr == curr &&
    other.assetType == assetType &&
    other.latestPrice == latestPrice &&
    other.pnlCny == pnlCny &&
    other.pnlRate == pnlRate &&
    other.typeLabel == typeLabel;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (code == null ? 0 : code!.hashCode) +
    (name == null ? 0 : name!.hashCode) +
    (qty == null ? 0 : qty!.hashCode) +
    (price == null ? 0 : price!.hashCode) +
    (curr == null ? 0 : curr!.hashCode) +
    (assetType == null ? 0 : assetType!.hashCode) +
    (latestPrice == null ? 0 : latestPrice!.hashCode) +
    (pnlCny == null ? 0 : pnlCny!.hashCode) +
    (pnlRate == null ? 0 : pnlRate!.hashCode) +
    (typeLabel == null ? 0 : typeLabel!.hashCode);

  @override
  String toString() => 'AdminUserPortfolioItem[code=$code, name=$name, qty=$qty, price=$price, curr=$curr, assetType=$assetType, latestPrice=$latestPrice, pnlCny=$pnlCny, pnlRate=$pnlRate, typeLabel=$typeLabel]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.code != null) {
      json[r'code'] = this.code;
    } else {
      json[r'code'] = null;
    }
    if (this.name != null) {
      json[r'name'] = this.name;
    } else {
      json[r'name'] = null;
    }
    if (this.qty != null) {
      json[r'qty'] = this.qty;
    } else {
      json[r'qty'] = null;
    }
    if (this.price != null) {
      json[r'price'] = this.price;
    } else {
      json[r'price'] = null;
    }
    if (this.curr != null) {
      json[r'curr'] = this.curr;
    } else {
      json[r'curr'] = null;
    }
    if (this.assetType != null) {
      json[r'asset_type'] = this.assetType;
    } else {
      json[r'asset_type'] = null;
    }
    if (this.latestPrice != null) {
      json[r'latest_price'] = this.latestPrice;
    } else {
      json[r'latest_price'] = null;
    }
    if (this.pnlCny != null) {
      json[r'pnl_cny'] = this.pnlCny;
    } else {
      json[r'pnl_cny'] = null;
    }
    if (this.pnlRate != null) {
      json[r'pnl_rate'] = this.pnlRate;
    } else {
      json[r'pnl_rate'] = null;
    }
    if (this.typeLabel != null) {
      json[r'type_label'] = this.typeLabel;
    } else {
      json[r'type_label'] = null;
    }
    return json;
  }

  /// Returns a new [AdminUserPortfolioItem] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AdminUserPortfolioItem? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AdminUserPortfolioItem[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AdminUserPortfolioItem[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AdminUserPortfolioItem(
        code: mapValueOfType<String>(json, r'code'),
        name: mapValueOfType<String>(json, r'name'),
        qty: num.parse('${json[r'qty']}'),
        price: num.parse('${json[r'price']}'),
        curr: mapValueOfType<String>(json, r'curr'),
        assetType: mapValueOfType<String>(json, r'asset_type'),
        latestPrice: num.parse('${json[r'latest_price']}'),
        pnlCny: num.parse('${json[r'pnl_cny']}'),
        pnlRate: num.parse('${json[r'pnl_rate']}'),
        typeLabel: mapValueOfType<String>(json, r'type_label'),
      );
    }
    return null;
  }

  static List<AdminUserPortfolioItem> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AdminUserPortfolioItem>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AdminUserPortfolioItem.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AdminUserPortfolioItem> mapFromJson(dynamic json) {
    final map = <String, AdminUserPortfolioItem>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AdminUserPortfolioItem.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AdminUserPortfolioItem-objects as value to a dart map
  static Map<String, List<AdminUserPortfolioItem>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AdminUserPortfolioItem>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AdminUserPortfolioItem.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

