//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class BuyPortfolioAssetRequest {
  /// Returns a new [BuyPortfolioAssetRequest] instance.
  BuyPortfolioAssetRequest({
    required this.code,
    required this.price,
    required this.qty,
  });

  String code;

  num price;

  num qty;

  @override
  bool operator ==(Object other) => identical(this, other) || other is BuyPortfolioAssetRequest &&
    other.code == code &&
    other.price == price &&
    other.qty == qty;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (code.hashCode) +
    (price.hashCode) +
    (qty.hashCode);

  @override
  String toString() => 'BuyPortfolioAssetRequest[code=$code, price=$price, qty=$qty]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
      json[r'code'] = this.code;
      json[r'price'] = this.price;
      json[r'qty'] = this.qty;
    return json;
  }

  /// Returns a new [BuyPortfolioAssetRequest] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static BuyPortfolioAssetRequest? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "BuyPortfolioAssetRequest[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "BuyPortfolioAssetRequest[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return BuyPortfolioAssetRequest(
        code: mapValueOfType<String>(json, r'code')!,
        price: num.parse('${json[r'price']}'),
        qty: num.parse('${json[r'qty']}'),
      );
    }
    return null;
  }

  static List<BuyPortfolioAssetRequest> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <BuyPortfolioAssetRequest>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = BuyPortfolioAssetRequest.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, BuyPortfolioAssetRequest> mapFromJson(dynamic json) {
    final map = <String, BuyPortfolioAssetRequest>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = BuyPortfolioAssetRequest.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of BuyPortfolioAssetRequest-objects as value to a dart map
  static Map<String, List<BuyPortfolioAssetRequest>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<BuyPortfolioAssetRequest>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = BuyPortfolioAssetRequest.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
    'code',
    'price',
    'qty',
  };
}

