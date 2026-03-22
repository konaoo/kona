//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AdminUserSessionsCountResponse {
  /// Returns a new [AdminUserSessionsCountResponse] instance.
  AdminUserSessionsCountResponse({
    this.userId,
    this.activeSessions,
  });

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
  int? activeSessions;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AdminUserSessionsCountResponse &&
    other.userId == userId &&
    other.activeSessions == activeSessions;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (userId == null ? 0 : userId!.hashCode) +
    (activeSessions == null ? 0 : activeSessions!.hashCode);

  @override
  String toString() => 'AdminUserSessionsCountResponse[userId=$userId, activeSessions=$activeSessions]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.userId != null) {
      json[r'user_id'] = this.userId;
    } else {
      json[r'user_id'] = null;
    }
    if (this.activeSessions != null) {
      json[r'active_sessions'] = this.activeSessions;
    } else {
      json[r'active_sessions'] = null;
    }
    return json;
  }

  /// Returns a new [AdminUserSessionsCountResponse] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AdminUserSessionsCountResponse? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AdminUserSessionsCountResponse[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AdminUserSessionsCountResponse[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AdminUserSessionsCountResponse(
        userId: mapValueOfType<String>(json, r'user_id'),
        activeSessions: mapValueOfType<int>(json, r'active_sessions'),
      );
    }
    return null;
  }

  static List<AdminUserSessionsCountResponse> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AdminUserSessionsCountResponse>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AdminUserSessionsCountResponse.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AdminUserSessionsCountResponse> mapFromJson(dynamic json) {
    final map = <String, AdminUserSessionsCountResponse>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AdminUserSessionsCountResponse.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AdminUserSessionsCountResponse-objects as value to a dart map
  static Map<String, List<AdminUserSessionsCountResponse>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AdminUserSessionsCountResponse>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AdminUserSessionsCountResponse.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

