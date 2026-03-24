//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AdminUserUpdateResponseUser {
  /// Returns a new [AdminUserUpdateResponseUser] instance.
  AdminUserUpdateResponseUser({
    this.id,
    this.username,
    this.nickname,
    this.phone,
    this.userNumber,
    this.isAdmin,
    this.mustChangePassword,
    this.status,
    this.createdAt,
    this.lastLogin,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? id;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? username;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? nickname;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? phone;

  int? userNumber;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  bool? isAdmin;

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
  String? status;

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
  String? lastLogin;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AdminUserUpdateResponseUser &&
    other.id == id &&
    other.username == username &&
    other.nickname == nickname &&
    other.phone == phone &&
    other.userNumber == userNumber &&
    other.isAdmin == isAdmin &&
    other.mustChangePassword == mustChangePassword &&
    other.status == status &&
    other.createdAt == createdAt &&
    other.lastLogin == lastLogin;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (id == null ? 0 : id!.hashCode) +
    (username == null ? 0 : username!.hashCode) +
    (nickname == null ? 0 : nickname!.hashCode) +
    (phone == null ? 0 : phone!.hashCode) +
    (userNumber == null ? 0 : userNumber!.hashCode) +
    (isAdmin == null ? 0 : isAdmin!.hashCode) +
    (mustChangePassword == null ? 0 : mustChangePassword!.hashCode) +
    (status == null ? 0 : status!.hashCode) +
    (createdAt == null ? 0 : createdAt!.hashCode) +
    (lastLogin == null ? 0 : lastLogin!.hashCode);

  @override
  String toString() => 'AdminUserUpdateResponseUser[id=$id, username=$username, nickname=$nickname, phone=$phone, userNumber=$userNumber, isAdmin=$isAdmin, mustChangePassword=$mustChangePassword, status=$status, createdAt=$createdAt, lastLogin=$lastLogin]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.id != null) {
      json[r'id'] = this.id;
    } else {
      json[r'id'] = null;
    }
    if (this.username != null) {
      json[r'username'] = this.username;
    } else {
      json[r'username'] = null;
    }
    if (this.nickname != null) {
      json[r'nickname'] = this.nickname;
    } else {
      json[r'nickname'] = null;
    }
    if (this.phone != null) {
      json[r'phone'] = this.phone;
    } else {
      json[r'phone'] = null;
    }
    if (this.userNumber != null) {
      json[r'user_number'] = this.userNumber;
    } else {
      json[r'user_number'] = null;
    }
    if (this.isAdmin != null) {
      json[r'is_admin'] = this.isAdmin;
    } else {
      json[r'is_admin'] = null;
    }
    if (this.mustChangePassword != null) {
      json[r'must_change_password'] = this.mustChangePassword;
    } else {
      json[r'must_change_password'] = null;
    }
    if (this.status != null) {
      json[r'status'] = this.status;
    } else {
      json[r'status'] = null;
    }
    if (this.createdAt != null) {
      json[r'created_at'] = this.createdAt;
    } else {
      json[r'created_at'] = null;
    }
    if (this.lastLogin != null) {
      json[r'last_login'] = this.lastLogin;
    } else {
      json[r'last_login'] = null;
    }
    return json;
  }

  /// Returns a new [AdminUserUpdateResponseUser] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AdminUserUpdateResponseUser? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AdminUserUpdateResponseUser[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AdminUserUpdateResponseUser[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AdminUserUpdateResponseUser(
        id: mapValueOfType<String>(json, r'id'),
        username: mapValueOfType<String>(json, r'username'),
        nickname: mapValueOfType<String>(json, r'nickname'),
        phone: mapValueOfType<String>(json, r'phone'),
        userNumber: mapValueOfType<int>(json, r'user_number'),
        isAdmin: mapValueOfType<bool>(json, r'is_admin'),
        mustChangePassword: mapValueOfType<bool>(json, r'must_change_password'),
        status: mapValueOfType<String>(json, r'status'),
        createdAt: mapValueOfType<String>(json, r'created_at'),
        lastLogin: mapValueOfType<String>(json, r'last_login'),
      );
    }
    return null;
  }

  static List<AdminUserUpdateResponseUser> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AdminUserUpdateResponseUser>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AdminUserUpdateResponseUser.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AdminUserUpdateResponseUser> mapFromJson(dynamic json) {
    final map = <String, AdminUserUpdateResponseUser>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AdminUserUpdateResponseUser.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AdminUserUpdateResponseUser-objects as value to a dart map
  static Map<String, List<AdminUserUpdateResponseUser>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AdminUserUpdateResponseUser>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AdminUserUpdateResponseUser.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

