//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AdminUserPortfolioResponseSummary {
  /// Returns a new [AdminUserPortfolioResponseSummary] instance.
  AdminUserPortfolioResponseSummary({
    this.cashCny,
    this.otherCny,
    this.liabilityCny,
    this.asOf,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? cashCny;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? otherCny;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? liabilityCny;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? asOf;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AdminUserPortfolioResponseSummary &&
    other.cashCny == cashCny &&
    other.otherCny == otherCny &&
    other.liabilityCny == liabilityCny &&
    other.asOf == asOf;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (cashCny == null ? 0 : cashCny!.hashCode) +
    (otherCny == null ? 0 : otherCny!.hashCode) +
    (liabilityCny == null ? 0 : liabilityCny!.hashCode) +
    (asOf == null ? 0 : asOf!.hashCode);

  @override
  String toString() => 'AdminUserPortfolioResponseSummary[cashCny=$cashCny, otherCny=$otherCny, liabilityCny=$liabilityCny, asOf=$asOf]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.cashCny != null) {
      json[r'cash_cny'] = this.cashCny;
    } else {
      json[r'cash_cny'] = null;
    }
    if (this.otherCny != null) {
      json[r'other_cny'] = this.otherCny;
    } else {
      json[r'other_cny'] = null;
    }
    if (this.liabilityCny != null) {
      json[r'liability_cny'] = this.liabilityCny;
    } else {
      json[r'liability_cny'] = null;
    }
    if (this.asOf != null) {
      json[r'as_of'] = this.asOf;
    } else {
      json[r'as_of'] = null;
    }
    return json;
  }

  /// Returns a new [AdminUserPortfolioResponseSummary] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AdminUserPortfolioResponseSummary? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AdminUserPortfolioResponseSummary[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AdminUserPortfolioResponseSummary[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AdminUserPortfolioResponseSummary(
        cashCny: num.parse('${json[r'cash_cny']}'),
        otherCny: num.parse('${json[r'other_cny']}'),
        liabilityCny: num.parse('${json[r'liability_cny']}'),
        asOf: mapValueOfType<String>(json, r'as_of'),
      );
    }
    return null;
  }

  static List<AdminUserPortfolioResponseSummary> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AdminUserPortfolioResponseSummary>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AdminUserPortfolioResponseSummary.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AdminUserPortfolioResponseSummary> mapFromJson(dynamic json) {
    final map = <String, AdminUserPortfolioResponseSummary>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AdminUserPortfolioResponseSummary.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AdminUserPortfolioResponseSummary-objects as value to a dart map
  static Map<String, List<AdminUserPortfolioResponseSummary>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AdminUserPortfolioResponseSummary>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AdminUserPortfolioResponseSummary.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

