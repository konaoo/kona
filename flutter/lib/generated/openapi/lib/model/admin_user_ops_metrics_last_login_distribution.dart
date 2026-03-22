//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AdminUserOpsMetricsLastLoginDistribution {
  /// Returns a new [AdminUserOpsMetricsLastLoginDistribution] instance.
  AdminUserOpsMetricsLastLoginDistribution({
    this.within1d,
    this.within7d,
    this.within30d,
    this.over30d,
    this.neverLogin,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? within1d;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? within7d;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? within30d;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? over30d;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? neverLogin;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AdminUserOpsMetricsLastLoginDistribution &&
    other.within1d == within1d &&
    other.within7d == within7d &&
    other.within30d == within30d &&
    other.over30d == over30d &&
    other.neverLogin == neverLogin;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (within1d == null ? 0 : within1d!.hashCode) +
    (within7d == null ? 0 : within7d!.hashCode) +
    (within30d == null ? 0 : within30d!.hashCode) +
    (over30d == null ? 0 : over30d!.hashCode) +
    (neverLogin == null ? 0 : neverLogin!.hashCode);

  @override
  String toString() => 'AdminUserOpsMetricsLastLoginDistribution[within1d=$within1d, within7d=$within7d, within30d=$within30d, over30d=$over30d, neverLogin=$neverLogin]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.within1d != null) {
      json[r'within_1d'] = this.within1d;
    } else {
      json[r'within_1d'] = null;
    }
    if (this.within7d != null) {
      json[r'within_7d'] = this.within7d;
    } else {
      json[r'within_7d'] = null;
    }
    if (this.within30d != null) {
      json[r'within_30d'] = this.within30d;
    } else {
      json[r'within_30d'] = null;
    }
    if (this.over30d != null) {
      json[r'over_30d'] = this.over30d;
    } else {
      json[r'over_30d'] = null;
    }
    if (this.neverLogin != null) {
      json[r'never_login'] = this.neverLogin;
    } else {
      json[r'never_login'] = null;
    }
    return json;
  }

  /// Returns a new [AdminUserOpsMetricsLastLoginDistribution] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AdminUserOpsMetricsLastLoginDistribution? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AdminUserOpsMetricsLastLoginDistribution[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AdminUserOpsMetricsLastLoginDistribution[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AdminUserOpsMetricsLastLoginDistribution(
        within1d: mapValueOfType<int>(json, r'within_1d'),
        within7d: mapValueOfType<int>(json, r'within_7d'),
        within30d: mapValueOfType<int>(json, r'within_30d'),
        over30d: mapValueOfType<int>(json, r'over_30d'),
        neverLogin: mapValueOfType<int>(json, r'never_login'),
      );
    }
    return null;
  }

  static List<AdminUserOpsMetricsLastLoginDistribution> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AdminUserOpsMetricsLastLoginDistribution>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AdminUserOpsMetricsLastLoginDistribution.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AdminUserOpsMetricsLastLoginDistribution> mapFromJson(dynamic json) {
    final map = <String, AdminUserOpsMetricsLastLoginDistribution>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AdminUserOpsMetricsLastLoginDistribution.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AdminUserOpsMetricsLastLoginDistribution-objects as value to a dart map
  static Map<String, List<AdminUserOpsMetricsLastLoginDistribution>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AdminUserOpsMetricsLastLoginDistribution>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AdminUserOpsMetricsLastLoginDistribution.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

