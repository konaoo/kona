//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AdminUserSummary {
  /// Returns a new [AdminUserSummary] instance.
  AdminUserSummary({
    this.id,
    this.username,
    this.nickname,
    this.phone,
    this.userNumber,
    this.registerMethod,
    this.isAdmin,
    this.mustChangePassword,
    this.status,
    this.createdAt,
    this.lastLogin,
    this.lastActiveAt,
    this.lastLoginIp,
    this.lastLoginRegion,
    this.lastActiveIp,
    this.lastActiveRegion,
    this.activeSessions,
    this.totalAssetCny,
    this.totalInvestCny,
    this.canManage,
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
  String? registerMethod;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? isAdmin;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? mustChangePassword;

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

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? lastActiveAt;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? lastLoginIp;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? lastLoginRegion;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? lastActiveIp;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? lastActiveRegion;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? activeSessions;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? totalAssetCny;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? totalInvestCny;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? canManage;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AdminUserSummary &&
    other.id == id &&
    other.username == username &&
    other.nickname == nickname &&
    other.phone == phone &&
    other.userNumber == userNumber &&
    other.registerMethod == registerMethod &&
    other.isAdmin == isAdmin &&
    other.mustChangePassword == mustChangePassword &&
    other.status == status &&
    other.createdAt == createdAt &&
    other.lastLogin == lastLogin &&
    other.lastActiveAt == lastActiveAt &&
    other.lastLoginIp == lastLoginIp &&
    other.lastLoginRegion == lastLoginRegion &&
    other.lastActiveIp == lastActiveIp &&
    other.lastActiveRegion == lastActiveRegion &&
    other.activeSessions == activeSessions &&
    other.totalAssetCny == totalAssetCny &&
    other.totalInvestCny == totalInvestCny &&
    other.canManage == canManage;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (id == null ? 0 : id!.hashCode) +
    (username == null ? 0 : username!.hashCode) +
    (nickname == null ? 0 : nickname!.hashCode) +
    (phone == null ? 0 : phone!.hashCode) +
    (userNumber == null ? 0 : userNumber!.hashCode) +
    (registerMethod == null ? 0 : registerMethod!.hashCode) +
    (isAdmin == null ? 0 : isAdmin!.hashCode) +
    (mustChangePassword == null ? 0 : mustChangePassword!.hashCode) +
    (status == null ? 0 : status!.hashCode) +
    (createdAt == null ? 0 : createdAt!.hashCode) +
    (lastLogin == null ? 0 : lastLogin!.hashCode) +
    (lastActiveAt == null ? 0 : lastActiveAt!.hashCode) +
    (lastLoginIp == null ? 0 : lastLoginIp!.hashCode) +
    (lastLoginRegion == null ? 0 : lastLoginRegion!.hashCode) +
    (lastActiveIp == null ? 0 : lastActiveIp!.hashCode) +
    (lastActiveRegion == null ? 0 : lastActiveRegion!.hashCode) +
    (activeSessions == null ? 0 : activeSessions!.hashCode) +
    (totalAssetCny == null ? 0 : totalAssetCny!.hashCode) +
    (totalInvestCny == null ? 0 : totalInvestCny!.hashCode) +
    (canManage == null ? 0 : canManage!.hashCode);

  @override
  String toString() => 'AdminUserSummary[id=$id, username=$username, nickname=$nickname, phone=$phone, userNumber=$userNumber, registerMethod=$registerMethod, isAdmin=$isAdmin, mustChangePassword=$mustChangePassword, status=$status, createdAt=$createdAt, lastLogin=$lastLogin, lastActiveAt=$lastActiveAt, lastLoginIp=$lastLoginIp, lastLoginRegion=$lastLoginRegion, lastActiveIp=$lastActiveIp, lastActiveRegion=$lastActiveRegion, activeSessions=$activeSessions, totalAssetCny=$totalAssetCny, totalInvestCny=$totalInvestCny, canManage=$canManage]';

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
    if (this.registerMethod != null) {
      json[r'register_method'] = this.registerMethod;
    } else {
      json[r'register_method'] = null;
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
    if (this.lastActiveAt != null) {
      json[r'last_active_at'] = this.lastActiveAt;
    } else {
      json[r'last_active_at'] = null;
    }
    if (this.lastLoginIp != null) {
      json[r'last_login_ip'] = this.lastLoginIp;
    } else {
      json[r'last_login_ip'] = null;
    }
    if (this.lastLoginRegion != null) {
      json[r'last_login_region'] = this.lastLoginRegion;
    } else {
      json[r'last_login_region'] = null;
    }
    if (this.lastActiveIp != null) {
      json[r'last_active_ip'] = this.lastActiveIp;
    } else {
      json[r'last_active_ip'] = null;
    }
    if (this.lastActiveRegion != null) {
      json[r'last_active_region'] = this.lastActiveRegion;
    } else {
      json[r'last_active_region'] = null;
    }
    if (this.activeSessions != null) {
      json[r'active_sessions'] = this.activeSessions;
    } else {
      json[r'active_sessions'] = null;
    }
    if (this.totalAssetCny != null) {
      json[r'total_asset_cny'] = this.totalAssetCny;
    } else {
      json[r'total_asset_cny'] = null;
    }
    if (this.totalInvestCny != null) {
      json[r'total_invest_cny'] = this.totalInvestCny;
    } else {
      json[r'total_invest_cny'] = null;
    }
    if (this.canManage != null) {
      json[r'can_manage'] = this.canManage;
    } else {
      json[r'can_manage'] = null;
    }
    return json;
  }

  /// Returns a new [AdminUserSummary] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AdminUserSummary? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AdminUserSummary[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AdminUserSummary[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AdminUserSummary(
        id: mapValueOfType<String>(json, r'id'),
        username: mapValueOfType<String>(json, r'username'),
        nickname: mapValueOfType<String>(json, r'nickname'),
        phone: mapValueOfType<String>(json, r'phone'),
        userNumber: mapValueOfType<int>(json, r'user_number'),
        registerMethod: mapValueOfType<String>(json, r'register_method'),
        isAdmin: mapValueOfType<int>(json, r'is_admin'),
        mustChangePassword: mapValueOfType<int>(json, r'must_change_password'),
        status: mapValueOfType<String>(json, r'status'),
        createdAt: mapValueOfType<String>(json, r'created_at'),
        lastLogin: mapValueOfType<String>(json, r'last_login'),
        lastActiveAt: mapValueOfType<String>(json, r'last_active_at'),
        lastLoginIp: mapValueOfType<String>(json, r'last_login_ip'),
        lastLoginRegion: mapValueOfType<String>(json, r'last_login_region'),
        lastActiveIp: mapValueOfType<String>(json, r'last_active_ip'),
        lastActiveRegion: mapValueOfType<String>(json, r'last_active_region'),
        activeSessions: mapValueOfType<int>(json, r'active_sessions'),
        totalAssetCny: num.parse('${json[r'total_asset_cny']}'),
        totalInvestCny: num.parse('${json[r'total_invest_cny']}'),
        canManage: mapValueOfType<int>(json, r'can_manage'),
      );
    }
    return null;
  }

  static List<AdminUserSummary> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AdminUserSummary>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AdminUserSummary.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AdminUserSummary> mapFromJson(dynamic json) {
    final map = <String, AdminUserSummary>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AdminUserSummary.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AdminUserSummary-objects as value to a dart map
  static Map<String, List<AdminUserSummary>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AdminUserSummary>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AdminUserSummary.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

