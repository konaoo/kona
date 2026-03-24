//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AdminBackupResponse {
  /// Returns a new [AdminBackupResponse] instance.
  AdminBackupResponse({
    this.status,
    this.backupFile,
    this.backupDir,
    this.retentionDays,
    this.deletedCount,
    this.deleted = const [],
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
  int? retentionDays;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? deletedCount;

  List<String> deleted;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AdminBackupResponse &&
    other.status == status &&
    other.backupFile == backupFile &&
    other.backupDir == backupDir &&
    other.retentionDays == retentionDays &&
    other.deletedCount == deletedCount &&
    _deepEquality.equals(other.deleted, deleted);

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (status == null ? 0 : status!.hashCode) +
    (backupFile == null ? 0 : backupFile!.hashCode) +
    (backupDir == null ? 0 : backupDir!.hashCode) +
    (retentionDays == null ? 0 : retentionDays!.hashCode) +
    (deletedCount == null ? 0 : deletedCount!.hashCode) +
    (deleted.hashCode);

  @override
  String toString() => 'AdminBackupResponse[status=$status, backupFile=$backupFile, backupDir=$backupDir, retentionDays=$retentionDays, deletedCount=$deletedCount, deleted=$deleted]';

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
    if (this.retentionDays != null) {
      json[r'retention_days'] = this.retentionDays;
    } else {
      json[r'retention_days'] = null;
    }
    if (this.deletedCount != null) {
      json[r'deleted_count'] = this.deletedCount;
    } else {
      json[r'deleted_count'] = null;
    }
      json[r'deleted'] = this.deleted;
    return json;
  }

  /// Returns a new [AdminBackupResponse] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AdminBackupResponse? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AdminBackupResponse[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AdminBackupResponse[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AdminBackupResponse(
        status: mapValueOfType<String>(json, r'status'),
        backupFile: mapValueOfType<String>(json, r'backup_file'),
        backupDir: mapValueOfType<String>(json, r'backup_dir'),
        retentionDays: mapValueOfType<int>(json, r'retention_days'),
        deletedCount: mapValueOfType<int>(json, r'deleted_count'),
        deleted: json[r'deleted'] is Iterable
            ? (json[r'deleted'] as Iterable).cast<String>().toList(growable: false)
            : const [],
      );
    }
    return null;
  }

  static List<AdminBackupResponse> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AdminBackupResponse>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AdminBackupResponse.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AdminBackupResponse> mapFromJson(dynamic json) {
    final map = <String, AdminBackupResponse>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AdminBackupResponse.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AdminBackupResponse-objects as value to a dart map
  static Map<String, List<AdminBackupResponse>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AdminBackupResponse>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AdminBackupResponse.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

