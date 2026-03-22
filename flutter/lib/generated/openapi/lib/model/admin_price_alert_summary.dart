//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AdminPriceAlertSummary {
  /// Returns a new [AdminPriceAlertSummary] instance.
  AdminPriceAlertSummary({
    this.critical,
    this.warning,
    this.info,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? critical;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? warning;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? info;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AdminPriceAlertSummary &&
    other.critical == critical &&
    other.warning == warning &&
    other.info == info;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (critical == null ? 0 : critical!.hashCode) +
    (warning == null ? 0 : warning!.hashCode) +
    (info == null ? 0 : info!.hashCode);

  @override
  String toString() => 'AdminPriceAlertSummary[critical=$critical, warning=$warning, info=$info]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.critical != null) {
      json[r'critical'] = this.critical;
    } else {
      json[r'critical'] = null;
    }
    if (this.warning != null) {
      json[r'warning'] = this.warning;
    } else {
      json[r'warning'] = null;
    }
    if (this.info != null) {
      json[r'info'] = this.info;
    } else {
      json[r'info'] = null;
    }
    return json;
  }

  /// Returns a new [AdminPriceAlertSummary] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AdminPriceAlertSummary? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AdminPriceAlertSummary[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AdminPriceAlertSummary[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AdminPriceAlertSummary(
        critical: mapValueOfType<int>(json, r'critical'),
        warning: mapValueOfType<int>(json, r'warning'),
        info: mapValueOfType<int>(json, r'info'),
      );
    }
    return null;
  }

  static List<AdminPriceAlertSummary> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AdminPriceAlertSummary>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AdminPriceAlertSummary.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AdminPriceAlertSummary> mapFromJson(dynamic json) {
    final map = <String, AdminPriceAlertSummary>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AdminPriceAlertSummary.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AdminPriceAlertSummary-objects as value to a dart map
  static Map<String, List<AdminPriceAlertSummary>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AdminPriceAlertSummary>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AdminPriceAlertSummary.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

