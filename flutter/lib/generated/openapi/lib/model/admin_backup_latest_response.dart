//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AdminBackupLatestResponse {
  /// Returns a new [AdminBackupLatestResponse] instance.
  AdminBackupLatestResponse({
    this.status,
    this.backupFile,
    this.backupDir,
    this.modifiedAt,
    this.sizeBytes,
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
  String? backupFile;

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
  String? modifiedAt;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? sizeBytes;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AdminBackupLatestResponse &&
    other.status == status &&
    other.backupFile == backupFile &&
    other.backupDir == backupDir &&
    other.modifiedAt == modifiedAt &&
    other.sizeBytes == sizeBytes;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (status == null ? 0 : status!.hashCode) +
    (backupFile == null ? 0 : backupFile!.hashCode) +
    (backupDir == null ? 0 : backupDir!.hashCode) +
    (modifiedAt == null ? 0 : modifiedAt!.hashCode) +
    (sizeBytes == null ? 0 : sizeBytes!.hashCode);

  @override
  String toString() => 'AdminBackupLatestResponse[status=$status, backupFile=$backupFile, backupDir=$backupDir, modifiedAt=$modifiedAt, sizeBytes=$sizeBytes]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.status != null) {
      json[r'status'] = this.status;
    } else {
      json[r'status'] = null;
    }
    if (this.backupFile != null) {
      json[r'backup_file'] = this.backupFile;
    } else {
      json[r'backup_file'] = null;
    }
    if (this.backupDir != null) {
      json[r'backup_dir'] = this.backupDir;
    } else {
      json[r'backup_dir'] = null;
    }
    if (this.modifiedAt != null) {
      json[r'modified_at'] = this.modifiedAt;
    } else {
      json[r'modified_at'] = null;
    }
    if (this.sizeBytes != null) {
      json[r'size_bytes'] = this.sizeBytes;
    } else {
      json[r'size_bytes'] = null;
    }
    return json;
  }

  /// Returns a new [AdminBackupLatestResponse] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AdminBackupLatestResponse? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AdminBackupLatestResponse[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AdminBackupLatestResponse[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AdminBackupLatestResponse(
        status: mapValueOfType<String>(json, r'status'),
        backupFile: mapValueOfType<String>(json, r'backup_file'),
        backupDir: mapValueOfType<String>(json, r'backup_dir'),
        modifiedAt: mapValueOfType<String>(json, r'modified_at'),
        sizeBytes: mapValueOfType<int>(json, r'size_bytes'),
      );
    }
    return null;
  }

  static List<AdminBackupLatestResponse> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AdminBackupLatestResponse>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AdminBackupLatestResponse.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AdminBackupLatestResponse> mapFromJson(dynamic json) {
    final map = <String, AdminBackupLatestResponse>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AdminBackupLatestResponse.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AdminBackupLatestResponse-objects as value to a dart map
  static Map<String, List<AdminBackupLatestResponse>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AdminBackupLatestResponse>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AdminBackupLatestResponse.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

