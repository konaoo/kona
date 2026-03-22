//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AdminUserPasswordResetResponse {
  /// Returns a new [AdminUserPasswordResetResponse] instance.
  AdminUserPasswordResetResponse({
    this.status,
    this.userId,
    this.mustChangePassword,
    this.revokedRefreshTokens,
    this.tempPassword,
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
  bool? mustChangePassword;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? revokedRefreshTokens;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? tempPassword;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AdminUserPasswordResetResponse &&
    other.status == status &&
    other.userId == userId &&
    other.mustChangePassword == mustChangePassword &&
    other.revokedRefreshTokens == revokedRefreshTokens &&
    other.tempPassword == tempPassword;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (status == null ? 0 : status!.hashCode) +
    (userId == null ? 0 : userId!.hashCode) +
    (mustChangePassword == null ? 0 : mustChangePassword!.hashCode) +
    (revokedRefreshTokens == null ? 0 : revokedRefreshTokens!.hashCode) +
    (tempPassword == null ? 0 : tempPassword!.hashCode);

  @override
  String toString() => 'AdminUserPasswordResetResponse[status=$status, userId=$userId, mustChangePassword=$mustChangePassword, revokedRefreshTokens=$revokedRefreshTokens, tempPassword=$tempPassword]';

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
    if (this.mustChangePassword != null) {
      json[r'must_change_password'] = this.mustChangePassword;
    } else {
      json[r'must_change_password'] = null;
    }
    if (this.revokedRefreshTokens != null) {
      json[r'revoked_refresh_tokens'] = this.revokedRefreshTokens;
    } else {
      json[r'revoked_refresh_tokens'] = null;
    }
    if (this.tempPassword != null) {
      json[r'temp_password'] = this.tempPassword;
    } else {
      json[r'temp_password'] = null;
    }
    return json;
  }

  /// Returns a new [AdminUserPasswordResetResponse] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AdminUserPasswordResetResponse? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AdminUserPasswordResetResponse[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AdminUserPasswordResetResponse[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AdminUserPasswordResetResponse(
        status: mapValueOfType<String>(json, r'status'),
        userId: mapValueOfType<String>(json, r'user_id'),
        mustChangePassword: mapValueOfType<bool>(json, r'must_change_password'),
        revokedRefreshTokens: mapValueOfType<int>(json, r'revoked_refresh_tokens'),
        tempPassword: mapValueOfType<String>(json, r'temp_password'),
      );
    }
    return null;
  }

  static List<AdminUserPasswordResetResponse> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AdminUserPasswordResetResponse>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AdminUserPasswordResetResponse.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AdminUserPasswordResetResponse> mapFromJson(dynamic json) {
    final map = <String, AdminUserPasswordResetResponse>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AdminUserPasswordResetResponse.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AdminUserPasswordResetResponse-objects as value to a dart map
  static Map<String, List<AdminUserPasswordResetResponse>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AdminUserPasswordResetResponse>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AdminUserPasswordResetResponse.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

