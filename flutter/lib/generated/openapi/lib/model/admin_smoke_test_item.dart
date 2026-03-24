//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AdminSmokeTestItem {
  /// Returns a new [AdminSmokeTestItem] instance.
  AdminSmokeTestItem({
    this.name,
    this.ok,
    this.detail = const {},
    this.error,
  });

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
  bool? ok;

  Map<String, Object> detail;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? error;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AdminSmokeTestItem &&
    other.name == name &&
    other.ok == ok &&
    _deepEquality.equals(other.detail, detail) &&
    other.error == error;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (name == null ? 0 : name!.hashCode) +
    (ok == null ? 0 : ok!.hashCode) +
    (detail.hashCode) +
    (error == null ? 0 : error!.hashCode);

  @override
  String toString() => 'AdminSmokeTestItem[name=$name, ok=$ok, detail=$detail, error=$error]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.name != null) {
      json[r'name'] = this.name;
    } else {
      json[r'name'] = null;
    }
    if (this.ok != null) {
      json[r'ok'] = this.ok;
    } else {
      json[r'ok'] = null;
    }
      json[r'detail'] = this.detail;
    if (this.error != null) {
      json[r'error'] = this.error;
    } else {
      json[r'error'] = null;
    }
    return json;
  }

  /// Returns a new [AdminSmokeTestItem] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AdminSmokeTestItem? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AdminSmokeTestItem[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AdminSmokeTestItem[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AdminSmokeTestItem(
        name: mapValueOfType<String>(json, r'name'),
        ok: mapValueOfType<bool>(json, r'ok'),
        detail: mapCastOfType<String, Object>(json, r'detail') ?? const {},
        error: mapValueOfType<String>(json, r'error'),
      );
    }
    return null;
  }

  static List<AdminSmokeTestItem> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AdminSmokeTestItem>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AdminSmokeTestItem.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AdminSmokeTestItem> mapFromJson(dynamic json) {
    final map = <String, AdminSmokeTestItem>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AdminSmokeTestItem.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AdminSmokeTestItem-objects as value to a dart map
  static Map<String, List<AdminSmokeTestItem>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AdminSmokeTestItem>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AdminSmokeTestItem.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

