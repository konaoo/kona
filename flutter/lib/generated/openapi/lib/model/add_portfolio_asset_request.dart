//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AddPortfolioAssetRequest {
  /// Returns a new [AddPortfolioAssetRequest] instance.
  AddPortfolioAssetRequest({
    required this.code,
    this.name,
    required this.qty,
    required this.price,
    this.curr,
  });

  String code;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? name;

  num qty;

  num price;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? curr;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AddPortfolioAssetRequest &&
    other.code == code &&
    other.name == name &&
    other.qty == qty &&
    other.price == price &&
    other.curr == curr;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (code.hashCode) +
    (name == null ? 0 : name!.hashCode) +
    (qty.hashCode) +
    (price.hashCode) +
    (curr == null ? 0 : curr!.hashCode);

  @override
  String toString() => 'AddPortfolioAssetRequest[code=$code, name=$name, qty=$qty, price=$price, curr=$curr]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
      json[r'code'] = this.code;
    if (this.name != null) {
      json[r'name'] = this.name;
    } else {
      json[r'name'] = null;
    }
      json[r'qty'] = this.qty;
      json[r'price'] = this.price;
    if (this.curr != null) {
      json[r'curr'] = this.curr;
    } else {
      json[r'curr'] = null;
    }
    return json;
  }

  /// Returns a new [AddPortfolioAssetRequest] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AddPortfolioAssetRequest? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AddPortfolioAssetRequest[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AddPortfolioAssetRequest[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AddPortfolioAssetRequest(
        code: mapValueOfType<String>(json, r'code')!,
        name: mapValueOfType<String>(json, r'name'),
        qty: num.parse('${json[r'qty']}'),
        price: num.parse('${json[r'price']}'),
        curr: mapValueOfType<String>(json, r'curr'),
      );
    }
    return null;
  }

  static List<AddPortfolioAssetRequest> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AddPortfolioAssetRequest>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AddPortfolioAssetRequest.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AddPortfolioAssetRequest> mapFromJson(dynamic json) {
    final map = <String, AddPortfolioAssetRequest>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AddPortfolioAssetRequest.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AddPortfolioAssetRequest-objects as value to a dart map
  static Map<String, List<AddPortfolioAssetRequest>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AddPortfolioAssetRequest>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AddPortfolioAssetRequest.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
    'code',
    'qty',
    'price',
  };
}

