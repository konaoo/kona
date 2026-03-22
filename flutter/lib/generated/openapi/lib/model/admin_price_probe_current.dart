//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AdminPriceProbeCurrent {
  /// Returns a new [AdminPriceProbeCurrent] instance.
  AdminPriceProbeCurrent({
    this.price,
    this.yclose,
    this.amt,
    this.chg,
    this.sourceHint,
  });

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
  num? yclose;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? amt;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? chg;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? sourceHint;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AdminPriceProbeCurrent &&
    other.price == price &&
    other.yclose == yclose &&
    other.amt == amt &&
    other.chg == chg &&
    other.sourceHint == sourceHint;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (price == null ? 0 : price!.hashCode) +
    (yclose == null ? 0 : yclose!.hashCode) +
    (amt == null ? 0 : amt!.hashCode) +
    (chg == null ? 0 : chg!.hashCode) +
    (sourceHint == null ? 0 : sourceHint!.hashCode);

  @override
  String toString() => 'AdminPriceProbeCurrent[price=$price, yclose=$yclose, amt=$amt, chg=$chg, sourceHint=$sourceHint]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.price != null) {
      json[r'price'] = this.price;
    } else {
      json[r'price'] = null;
    }
    if (this.yclose != null) {
      json[r'yclose'] = this.yclose;
    } else {
      json[r'yclose'] = null;
    }
    if (this.amt != null) {
      json[r'amt'] = this.amt;
    } else {
      json[r'amt'] = null;
    }
    if (this.chg != null) {
      json[r'chg'] = this.chg;
    } else {
      json[r'chg'] = null;
    }
    if (this.sourceHint != null) {
      json[r'source_hint'] = this.sourceHint;
    } else {
      json[r'source_hint'] = null;
    }
    return json;
  }

  /// Returns a new [AdminPriceProbeCurrent] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AdminPriceProbeCurrent? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AdminPriceProbeCurrent[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AdminPriceProbeCurrent[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AdminPriceProbeCurrent(
        price: num.parse('${json[r'price']}'),
        yclose: num.parse('${json[r'yclose']}'),
        amt: num.parse('${json[r'amt']}'),
        chg: num.parse('${json[r'chg']}'),
        sourceHint: mapValueOfType<String>(json, r'source_hint'),
      );
    }
    return null;
  }

  static List<AdminPriceProbeCurrent> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AdminPriceProbeCurrent>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AdminPriceProbeCurrent.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AdminPriceProbeCurrent> mapFromJson(dynamic json) {
    final map = <String, AdminPriceProbeCurrent>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AdminPriceProbeCurrent.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AdminPriceProbeCurrent-objects as value to a dart map
  static Map<String, List<AdminPriceProbeCurrent>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AdminPriceProbeCurrent>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AdminPriceProbeCurrent.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

