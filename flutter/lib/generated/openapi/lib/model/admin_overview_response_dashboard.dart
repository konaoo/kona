//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AdminOverviewResponseDashboard {
  /// Returns a new [AdminOverviewResponseDashboard] instance.
  AdminOverviewResponseDashboard({
    this.newUsersToday,
    this.activeUsersToday,
    this.totalUsers,
    this.newUsersAvatarCount,
    this.newUserTrendText,
    this.activeUserTrendText,
    this.newUserBars = const [],
    this.activeUserBars = const [],
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? newUsersToday;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? activeUsersToday;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? totalUsers;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? newUsersAvatarCount;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? newUserTrendText;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? activeUserTrendText;

  List<AdminMiniBar> newUserBars;

  List<AdminMiniBar> activeUserBars;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AdminOverviewResponseDashboard &&
    other.newUsersToday == newUsersToday &&
    other.activeUsersToday == activeUsersToday &&
    other.totalUsers == totalUsers &&
    other.newUsersAvatarCount == newUsersAvatarCount &&
    other.newUserTrendText == newUserTrendText &&
    other.activeUserTrendText == activeUserTrendText &&
    _deepEquality.equals(other.newUserBars, newUserBars) &&
    _deepEquality.equals(other.activeUserBars, activeUserBars);

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (newUsersToday == null ? 0 : newUsersToday!.hashCode) +
    (activeUsersToday == null ? 0 : activeUsersToday!.hashCode) +
    (totalUsers == null ? 0 : totalUsers!.hashCode) +
    (newUsersAvatarCount == null ? 0 : newUsersAvatarCount!.hashCode) +
    (newUserTrendText == null ? 0 : newUserTrendText!.hashCode) +
    (activeUserTrendText == null ? 0 : activeUserTrendText!.hashCode) +
    (newUserBars.hashCode) +
    (activeUserBars.hashCode);

  @override
  String toString() => 'AdminOverviewResponseDashboard[newUsersToday=$newUsersToday, activeUsersToday=$activeUsersToday, totalUsers=$totalUsers, newUsersAvatarCount=$newUsersAvatarCount, newUserTrendText=$newUserTrendText, activeUserTrendText=$activeUserTrendText, newUserBars=$newUserBars, activeUserBars=$activeUserBars]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.newUsersToday != null) {
      json[r'new_users_today'] = this.newUsersToday;
    } else {
      json[r'new_users_today'] = null;
    }
    if (this.activeUsersToday != null) {
      json[r'active_users_today'] = this.activeUsersToday;
    } else {
      json[r'active_users_today'] = null;
    }
    if (this.totalUsers != null) {
      json[r'total_users'] = this.totalUsers;
    } else {
      json[r'total_users'] = null;
    }
    if (this.newUsersAvatarCount != null) {
      json[r'new_users_avatar_count'] = this.newUsersAvatarCount;
    } else {
      json[r'new_users_avatar_count'] = null;
    }
    if (this.newUserTrendText != null) {
      json[r'new_user_trend_text'] = this.newUserTrendText;
    } else {
      json[r'new_user_trend_text'] = null;
    }
    if (this.activeUserTrendText != null) {
      json[r'active_user_trend_text'] = this.activeUserTrendText;
    } else {
      json[r'active_user_trend_text'] = null;
    }
      json[r'new_user_bars'] = this.newUserBars;
      json[r'active_user_bars'] = this.activeUserBars;
    return json;
  }

  /// Returns a new [AdminOverviewResponseDashboard] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AdminOverviewResponseDashboard? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AdminOverviewResponseDashboard[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AdminOverviewResponseDashboard[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AdminOverviewResponseDashboard(
        newUsersToday: mapValueOfType<int>(json, r'new_users_today'),
        activeUsersToday: mapValueOfType<int>(json, r'active_users_today'),
        totalUsers: mapValueOfType<int>(json, r'total_users'),
        newUsersAvatarCount: mapValueOfType<int>(json, r'new_users_avatar_count'),
        newUserTrendText: mapValueOfType<String>(json, r'new_user_trend_text'),
        activeUserTrendText: mapValueOfType<String>(json, r'active_user_trend_text'),
        newUserBars: AdminMiniBar.listFromJson(json[r'new_user_bars']),
        activeUserBars: AdminMiniBar.listFromJson(json[r'active_user_bars']),
      );
    }
    return null;
  }

  static List<AdminOverviewResponseDashboard> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AdminOverviewResponseDashboard>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AdminOverviewResponseDashboard.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AdminOverviewResponseDashboard> mapFromJson(dynamic json) {
    final map = <String, AdminOverviewResponseDashboard>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AdminOverviewResponseDashboard.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AdminOverviewResponseDashboard-objects as value to a dart map
  static Map<String, List<AdminOverviewResponseDashboard>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AdminOverviewResponseDashboard>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AdminOverviewResponseDashboard.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

