//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AdminAuditItem {
  /// Returns a new [AdminAuditItem] instance.
  AdminAuditItem({
    this.id,
    this.adminUserId,
    this.adminUsername,
    this.action,
    this.targetType,
    this.targetId,
    this.method,
    this.path,
    this.statusCode,
    this.result,
    this.error,
    this.createdAt,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? id;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? adminUserId;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? adminUsername;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? action;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? targetType;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? targetId;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? method;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? path;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? statusCode;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? result;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? error;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? createdAt;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AdminAuditItem &&
    other.id == id &&
    other.adminUserId == adminUserId &&
    other.adminUsername == adminUsername &&
    other.action == action &&
    other.targetType == targetType &&
    other.targetId == targetId &&
    other.method == method &&
    other.path == path &&
    other.statusCode == statusCode &&
    other.result == result &&
    other.error == error &&
    other.createdAt == createdAt;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (id == null ? 0 : id!.hashCode) +
    (adminUserId == null ? 0 : adminUserId!.hashCode) +
    (adminUsername == null ? 0 : adminUsername!.hashCode) +
    (action == null ? 0 : action!.hashCode) +
    (targetType == null ? 0 : targetType!.hashCode) +
    (targetId == null ? 0 : targetId!.hashCode) +
    (method == null ? 0 : method!.hashCode) +
    (path == null ? 0 : path!.hashCode) +
    (statusCode == null ? 0 : statusCode!.hashCode) +
    (result == null ? 0 : result!.hashCode) +
    (error == null ? 0 : error!.hashCode) +
    (createdAt == null ? 0 : createdAt!.hashCode);

  @override
  String toString() => 'AdminAuditItem[id=$id, adminUserId=$adminUserId, adminUsername=$adminUsername, action=$action, targetType=$targetType, targetId=$targetId, method=$method, path=$path, statusCode=$statusCode, result=$result, error=$error, createdAt=$createdAt]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.id != null) {
      json[r'id'] = this.id;
    } else {
      json[r'id'] = null;
    }
    if (this.adminUserId != null) {
      json[r'admin_user_id'] = this.adminUserId;
    } else {
      json[r'admin_user_id'] = null;
    }
    if (this.adminUsername != null) {
      json[r'admin_username'] = this.adminUsername;
    } else {
      json[r'admin_username'] = null;
    }
    if (this.action != null) {
      json[r'action'] = this.action;
    } else {
      json[r'action'] = null;
    }
    if (this.targetType != null) {
      json[r'target_type'] = this.targetType;
    } else {
      json[r'target_type'] = null;
    }
    if (this.targetId != null) {
      json[r'target_id'] = this.targetId;
    } else {
      json[r'target_id'] = null;
    }
    if (this.method != null) {
      json[r'method'] = this.method;
    } else {
      json[r'method'] = null;
    }
    if (this.path != null) {
      json[r'path'] = this.path;
    } else {
      json[r'path'] = null;
    }
    if (this.statusCode != null) {
      json[r'status_code'] = this.statusCode;
    } else {
      json[r'status_code'] = null;
    }
    if (this.result != null) {
      json[r'result'] = this.result;
    } else {
      json[r'result'] = null;
    }
    if (this.error != null) {
      json[r'error'] = this.error;
    } else {
      json[r'error'] = null;
    }
    if (this.createdAt != null) {
      json[r'created_at'] = this.createdAt;
    } else {
      json[r'created_at'] = null;
    }
    return json;
  }

  /// Returns a new [AdminAuditItem] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AdminAuditItem? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AdminAuditItem[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AdminAuditItem[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AdminAuditItem(
        id: mapValueOfType<int>(json, r'id'),
        adminUserId: mapValueOfType<String>(json, r'admin_user_id'),
        adminUsername: mapValueOfType<String>(json, r'admin_username'),
        action: mapValueOfType<String>(json, r'action'),
        targetType: mapValueOfType<String>(json, r'target_type'),
        targetId: mapValueOfType<String>(json, r'target_id'),
        method: mapValueOfType<String>(json, r'method'),
        path: mapValueOfType<String>(json, r'path'),
        statusCode: mapValueOfType<int>(json, r'status_code'),
        result: mapValueOfType<String>(json, r'result'),
        error: mapValueOfType<String>(json, r'error'),
        createdAt: mapValueOfType<String>(json, r'created_at'),
      );
    }
    return null;
  }

  static List<AdminAuditItem> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AdminAuditItem>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AdminAuditItem.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AdminAuditItem> mapFromJson(dynamic json) {
    final map = <String, AdminAuditItem>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AdminAuditItem.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AdminAuditItem-objects as value to a dart map
  static Map<String, List<AdminAuditItem>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AdminAuditItem>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AdminAuditItem.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

