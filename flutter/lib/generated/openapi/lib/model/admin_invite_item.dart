//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AdminInviteItem {
  /// Returns a new [AdminInviteItem] instance.
  AdminInviteItem({
    this.code,
    this.batchId,
    this.status,
    this.createdBy,
    this.createdAt,
    this.usedByUserId,
    this.usedAt,
    this.note,
    this.usedByUsername,
    this.usedByUserNumber,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? code;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? batchId;

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
  String? createdBy;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? createdAt;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? usedByUserId;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? usedAt;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? note;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? usedByUsername;

  int? usedByUserNumber;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AdminInviteItem &&
    other.code == code &&
    other.batchId == batchId &&
    other.status == status &&
    other.createdBy == createdBy &&
    other.createdAt == createdAt &&
    other.usedByUserId == usedByUserId &&
    other.usedAt == usedAt &&
    other.note == note &&
    other.usedByUsername == usedByUsername &&
    other.usedByUserNumber == usedByUserNumber;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (code == null ? 0 : code!.hashCode) +
    (batchId == null ? 0 : batchId!.hashCode) +
    (status == null ? 0 : status!.hashCode) +
    (createdBy == null ? 0 : createdBy!.hashCode) +
    (createdAt == null ? 0 : createdAt!.hashCode) +
    (usedByUserId == null ? 0 : usedByUserId!.hashCode) +
    (usedAt == null ? 0 : usedAt!.hashCode) +
    (note == null ? 0 : note!.hashCode) +
    (usedByUsername == null ? 0 : usedByUsername!.hashCode) +
    (usedByUserNumber == null ? 0 : usedByUserNumber!.hashCode);

  @override
  String toString() => 'AdminInviteItem[code=$code, batchId=$batchId, status=$status, createdBy=$createdBy, createdAt=$createdAt, usedByUserId=$usedByUserId, usedAt=$usedAt, note=$note, usedByUsername=$usedByUsername, usedByUserNumber=$usedByUserNumber]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.code != null) {
      json[r'code'] = this.code;
    } else {
      json[r'code'] = null;
    }
    if (this.batchId != null) {
      json[r'batch_id'] = this.batchId;
    } else {
      json[r'batch_id'] = null;
    }
    if (this.status != null) {
      json[r'status'] = this.status;
    } else {
      json[r'status'] = null;
    }
    if (this.createdBy != null) {
      json[r'created_by'] = this.createdBy;
    } else {
      json[r'created_by'] = null;
    }
    if (this.createdAt != null) {
      json[r'created_at'] = this.createdAt;
    } else {
      json[r'created_at'] = null;
    }
    if (this.usedByUserId != null) {
      json[r'used_by_user_id'] = this.usedByUserId;
    } else {
      json[r'used_by_user_id'] = null;
    }
    if (this.usedAt != null) {
      json[r'used_at'] = this.usedAt;
    } else {
      json[r'used_at'] = null;
    }
    if (this.note != null) {
      json[r'note'] = this.note;
    } else {
      json[r'note'] = null;
    }
    if (this.usedByUsername != null) {
      json[r'used_by_username'] = this.usedByUsername;
    } else {
      json[r'used_by_username'] = null;
    }
    if (this.usedByUserNumber != null) {
      json[r'used_by_user_number'] = this.usedByUserNumber;
    } else {
      json[r'used_by_user_number'] = null;
    }
    return json;
  }

  /// Returns a new [AdminInviteItem] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AdminInviteItem? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AdminInviteItem[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AdminInviteItem[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AdminInviteItem(
        code: mapValueOfType<String>(json, r'code'),
        batchId: mapValueOfType<String>(json, r'batch_id'),
        status: mapValueOfType<String>(json, r'status'),
        createdBy: mapValueOfType<String>(json, r'created_by'),
        createdAt: mapValueOfType<String>(json, r'created_at'),
        usedByUserId: mapValueOfType<String>(json, r'used_by_user_id'),
        usedAt: mapValueOfType<String>(json, r'used_at'),
        note: mapValueOfType<String>(json, r'note'),
        usedByUsername: mapValueOfType<String>(json, r'used_by_username'),
        usedByUserNumber: mapValueOfType<int>(json, r'used_by_user_number'),
      );
    }
    return null;
  }

  static List<AdminInviteItem> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AdminInviteItem>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AdminInviteItem.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AdminInviteItem> mapFromJson(dynamic json) {
    final map = <String, AdminInviteItem>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AdminInviteItem.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AdminInviteItem-objects as value to a dart map
  static Map<String, List<AdminInviteItem>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AdminInviteItem>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AdminInviteItem.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

