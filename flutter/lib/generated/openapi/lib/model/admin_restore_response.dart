//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AdminRestoreResponse {
  /// Returns a new [AdminRestoreResponse] instance.
  AdminRestoreResponse({
    this.status,
    this.restoredFrom,
    this.dbPath,
    this.preRestoreCopy,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? status;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? restoredFrom;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? dbPath;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? preRestoreCopy;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AdminRestoreResponse &&
    other.status == status &&
    other.restoredFrom == restoredFrom &&
    other.dbPath == dbPath &&
    other.preRestoreCopy == preRestoreCopy;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (status == null ? 0 : status!.hashCode) +
    (restoredFrom == null ? 0 : restoredFrom!.hashCode) +
    (dbPath == null ? 0 : dbPath!.hashCode) +
    (preRestoreCopy == null ? 0 : preRestoreCopy!.hashCode);

  @override
  String toString() => 'AdminRestoreResponse[status=$status, restoredFrom=$restoredFrom, dbPath=$dbPath, preRestoreCopy=$preRestoreCopy]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.status != null) {
      json[r'status'] = this.status;
    } else {
      json[r'status'] = null;
    }
    if (this.restoredFrom != null) {
      json[r'restored_from'] = this.restoredFrom;
    } else {
      json[r'restored_from'] = null;
    }
    if (this.dbPath != null) {
      json[r'db_path'] = this.dbPath;
    } else {
      json[r'db_path'] = null;
    }
    if (this.preRestoreCopy != null) {
      json[r'pre_restore_copy'] = this.preRestoreCopy;
    } else {
      json[r'pre_restore_copy'] = null;
    }
    return json;
  }

  /// Returns a new [AdminRestoreResponse] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AdminRestoreResponse? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AdminRestoreResponse[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AdminRestoreResponse[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AdminRestoreResponse(
        status: mapValueOfType<String>(json, r'status'),
        restoredFrom: mapValueOfType<String>(json, r'restored_from'),
        dbPath: mapValueOfType<String>(json, r'db_path'),
        preRestoreCopy: mapValueOfType<String>(json, r'pre_restore_copy'),
      );
    }
    return null;
  }

  static List<AdminRestoreResponse> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AdminRestoreResponse>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AdminRestoreResponse.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AdminRestoreResponse> mapFromJson(dynamic json) {
    final map = <String, AdminRestoreResponse>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AdminRestoreResponse.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AdminRestoreResponse-objects as value to a dart map
  static Map<String, List<AdminRestoreResponse>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AdminRestoreResponse>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AdminRestoreResponse.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

