//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AdminUserStatusResponse {
  /// Returns a new [AdminUserStatusResponse] instance.
  AdminUserStatusResponse({
    this.status,
    this.userId,
    this.newStatus,
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
  String? userId;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? newStatus;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AdminUserStatusResponse &&
    other.status == status &&
    other.userId == userId &&
    other.newStatus == newStatus;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (status == null ? 0 : status!.hashCode) +
    (userId == null ? 0 : userId!.hashCode) +
    (newStatus == null ? 0 : newStatus!.hashCode);

  @override
  String toString() => 'AdminUserStatusResponse[status=$status, userId=$userId, newStatus=$newStatus]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.status != null) {
      json[r'status'] = this.status;
    } else {
      json[r'status'] = null;
    }
    if (this.userId != null) {
      json[r'user_id'] = this.userId;
    } else {
      json[r'user_id'] = null;
    }
    if (this.newStatus != null) {
      json[r'new_status'] = this.newStatus;
    } else {
      json[r'new_status'] = null;
    }
    return json;
  }

  /// Returns a new [AdminUserStatusResponse] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AdminUserStatusResponse? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AdminUserStatusResponse[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AdminUserStatusResponse[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AdminUserStatusResponse(
        status: mapValueOfType<String>(json, r'status'),
        userId: mapValueOfType<String>(json, r'user_id'),
        newStatus: mapValueOfType<String>(json, r'new_status'),
      );
    }
    return null;
  }

  static List<AdminUserStatusResponse> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AdminUserStatusResponse>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AdminUserStatusResponse.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AdminUserStatusResponse> mapFromJson(dynamic json) {
    final map = <String, AdminUserStatusResponse>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AdminUserStatusResponse.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AdminUserStatusResponse-objects as value to a dart map
  static Map<String, List<AdminUserStatusResponse>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AdminUserStatusResponse>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AdminUserStatusResponse.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

