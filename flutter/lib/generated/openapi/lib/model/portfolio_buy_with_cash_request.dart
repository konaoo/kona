//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class PortfolioBuyWithCashRequest {
  /// Returns a new [PortfolioBuyWithCashRequest] instance.
  PortfolioBuyWithCashRequest({
    this.code,
    this.name,
    this.price,
    this.qty,
    this.cashAssetId,
    this.curr,
    this.requestId,
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
  int? cashAssetId;

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
  String? requestId;

  @override
  bool operator ==(Object other) => identical(this, other) || other is PortfolioBuyWithCashRequest &&
    other.code == code &&
    other.name == name &&
    other.price == price &&
    other.qty == qty &&
    other.cashAssetId == cashAssetId &&
    other.curr == curr &&
    other.requestId == requestId;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (code == null ? 0 : code!.hashCode) +
    (name == null ? 0 : name!.hashCode) +
    (price == null ? 0 : price!.hashCode) +
    (qty == null ? 0 : qty!.hashCode) +
    (cashAssetId == null ? 0 : cashAssetId!.hashCode) +
    (curr == null ? 0 : curr!.hashCode) +
    (requestId == null ? 0 : requestId!.hashCode);

  @override
  String toString() => 'PortfolioBuyWithCashRequest[code=$code, name=$name, price=$price, qty=$qty, cashAssetId=$cashAssetId, curr=$curr, requestId=$requestId]';

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
    if (this.cashAssetId != null) {
      json[r'cash_asset_id'] = this.cashAssetId;
    } else {
      json[r'cash_asset_id'] = null;
    }
    if (this.curr != null) {
      json[r'curr'] = this.curr;
    } else {
      json[r'curr'] = null;
    }
    if (this.requestId != null) {
      json[r'request_id'] = this.requestId;
    } else {
      json[r'request_id'] = null;
    }
    return json;
  }

  /// Returns a new [PortfolioBuyWithCashRequest] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static PortfolioBuyWithCashRequest? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "PortfolioBuyWithCashRequest[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "PortfolioBuyWithCashRequest[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return PortfolioBuyWithCashRequest(
        code: mapValueOfType<String>(json, r'code'),
        name: mapValueOfType<String>(json, r'name'),
        price: num.parse('${json[r'price']}'),
        qty: num.parse('${json[r'qty']}'),
        cashAssetId: mapValueOfType<int>(json, r'cash_asset_id'),
        curr: mapValueOfType<String>(json, r'curr'),
        requestId: mapValueOfType<String>(json, r'request_id'),
      );
    }
    return null;
  }

  static List<PortfolioBuyWithCashRequest> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <PortfolioBuyWithCashRequest>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = PortfolioBuyWithCashRequest.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, PortfolioBuyWithCashRequest> mapFromJson(dynamic json) {
    final map = <String, PortfolioBuyWithCashRequest>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = PortfolioBuyWithCashRequest.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of PortfolioBuyWithCashRequest-objects as value to a dart map
  static Map<String, List<PortfolioBuyWithCashRequest>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<PortfolioBuyWithCashRequest>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = PortfolioBuyWithCashRequest.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

