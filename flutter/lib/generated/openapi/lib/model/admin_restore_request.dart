//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AdminRestoreRequest {
  /// Returns a new [AdminRestoreRequest] instance.
  AdminRestoreRequest({
    this.backupDir,
    this.backupFile,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? backupDir;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? backupFile;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AdminRestoreRequest &&
    other.backupDir == backupDir &&
    other.backupFile == backupFile;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (backupDir == null ? 0 : backupDir!.hashCode) +
    (backupFile == null ? 0 : backupFile!.hashCode);

  @override
  String toString() => 'AdminRestoreRequest[backupDir=$backupDir, backupFile=$backupFile]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.backupDir != null) {
      json[r'backup_dir'] = this.backupDir;
    } else {
      json[r'backup_dir'] = null;
    }
    if (this.backupFile != null) {
      json[r'backup_file'] = this.backupFile;
    } else {
      json[r'backup_file'] = null;
    }
    return json;
  }

  /// Returns a new [AdminRestoreRequest] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AdminRestoreRequest? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AdminRestoreRequest[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AdminRestoreRequest[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AdminRestoreRequest(
        backupDir: mapValueOfType<String>(json, r'backup_dir'),
        backupFile: mapValueOfType<String>(json, r'backup_file'),
      );
    }
    return null;
  }

  static List<AdminRestoreRequest> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AdminRestoreRequest>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AdminRestoreRequest.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AdminRestoreRequest> mapFromJson(dynamic json) {
    final map = <String, AdminRestoreRequest>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AdminRestoreRequest.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AdminRestoreRequest-objects as value to a dart map
  static Map<String, List<AdminRestoreRequest>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AdminRestoreRequest>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AdminRestoreRequest.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

