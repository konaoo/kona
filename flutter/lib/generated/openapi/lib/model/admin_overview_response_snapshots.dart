//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AdminOverviewResponseSnapshots {
  /// Returns a new [AdminOverviewResponseSnapshots] instance.
  AdminOverviewResponseSnapshots({
    this.total,
    this.latestDate,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? total;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? latestDate;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AdminOverviewResponseSnapshots &&
    other.total == total &&
    other.latestDate == latestDate;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (total == null ? 0 : total!.hashCode) +
    (latestDate == null ? 0 : latestDate!.hashCode);

  @override
  String toString() => 'AdminOverviewResponseSnapshots[total=$total, latestDate=$latestDate]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.total != null) {
      json[r'total'] = this.total;
    } else {
      json[r'total'] = null;
    }
    if (this.latestDate != null) {
      json[r'latest_date'] = this.latestDate;
    } else {
      json[r'latest_date'] = null;
    }
    return json;
  }

  /// Returns a new [AdminOverviewResponseSnapshots] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AdminOverviewResponseSnapshots? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AdminOverviewResponseSnapshots[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AdminOverviewResponseSnapshots[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AdminOverviewResponseSnapshots(
        total: mapValueOfType<int>(json, r'total'),
        latestDate: mapValueOfType<String>(json, r'latest_date'),
      );
    }
    return null;
  }

  static List<AdminOverviewResponseSnapshots> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AdminOverviewResponseSnapshots>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AdminOverviewResponseSnapshots.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AdminOverviewResponseSnapshots> mapFromJson(dynamic json) {
    final map = <String, AdminOverviewResponseSnapshots>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AdminOverviewResponseSnapshots.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AdminOverviewResponseSnapshots-objects as value to a dart map
  static Map<String, List<AdminOverviewResponseSnapshots>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AdminOverviewResponseSnapshots>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AdminOverviewResponseSnapshots.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

