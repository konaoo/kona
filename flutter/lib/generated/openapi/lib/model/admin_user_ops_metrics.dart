//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AdminUserOpsMetrics {
  /// Returns a new [AdminUserOpsMetrics] instance.
  AdminUserOpsMetrics({
    this.userTotal,
    this.newToday,
    this.new7d,
    this.new30d,
    this.dau,
    this.wau,
    this.mau,
    this.lastLoginDistribution,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? userTotal;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? newToday;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? new7d;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? new30d;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? dau;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? wau;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? mau;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  AdminUserOpsMetricsLastLoginDistribution? lastLoginDistribution;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AdminUserOpsMetrics &&
    other.userTotal == userTotal &&
    other.newToday == newToday &&
    other.new7d == new7d &&
    other.new30d == new30d &&
    other.dau == dau &&
    other.wau == wau &&
    other.mau == mau &&
    other.lastLoginDistribution == lastLoginDistribution;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (userTotal == null ? 0 : userTotal!.hashCode) +
    (newToday == null ? 0 : newToday!.hashCode) +
    (new7d == null ? 0 : new7d!.hashCode) +
    (new30d == null ? 0 : new30d!.hashCode) +
    (dau == null ? 0 : dau!.hashCode) +
    (wau == null ? 0 : wau!.hashCode) +
    (mau == null ? 0 : mau!.hashCode) +
    (lastLoginDistribution == null ? 0 : lastLoginDistribution!.hashCode);

  @override
  String toString() => 'AdminUserOpsMetrics[userTotal=$userTotal, newToday=$newToday, new7d=$new7d, new30d=$new30d, dau=$dau, wau=$wau, mau=$mau, lastLoginDistribution=$lastLoginDistribution]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.userTotal != null) {
      json[r'user_total'] = this.userTotal;
    } else {
      json[r'user_total'] = null;
    }
    if (this.newToday != null) {
      json[r'new_today'] = this.newToday;
    } else {
      json[r'new_today'] = null;
    }
    if (this.new7d != null) {
      json[r'new_7d'] = this.new7d;
    } else {
      json[r'new_7d'] = null;
    }
    if (this.new30d != null) {
      json[r'new_30d'] = this.new30d;
    } else {
      json[r'new_30d'] = null;
    }
    if (this.dau != null) {
      json[r'dau'] = this.dau;
    } else {
      json[r'dau'] = null;
    }
    if (this.wau != null) {
      json[r'wau'] = this.wau;
    } else {
      json[r'wau'] = null;
    }
    if (this.mau != null) {
      json[r'mau'] = this.mau;
    } else {
      json[r'mau'] = null;
    }
    if (this.lastLoginDistribution != null) {
      json[r'last_login_distribution'] = this.lastLoginDistribution;
    } else {
      json[r'last_login_distribution'] = null;
    }
    return json;
  }

  /// Returns a new [AdminUserOpsMetrics] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AdminUserOpsMetrics? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AdminUserOpsMetrics[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AdminUserOpsMetrics[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AdminUserOpsMetrics(
        userTotal: mapValueOfType<int>(json, r'user_total'),
        newToday: mapValueOfType<int>(json, r'new_today'),
        new7d: mapValueOfType<int>(json, r'new_7d'),
        new30d: mapValueOfType<int>(json, r'new_30d'),
        dau: mapValueOfType<int>(json, r'dau'),
        wau: mapValueOfType<int>(json, r'wau'),
        mau: mapValueOfType<int>(json, r'mau'),
        lastLoginDistribution: AdminUserOpsMetricsLastLoginDistribution.fromJson(json[r'last_login_distribution']),
      );
    }
    return null;
  }

  static List<AdminUserOpsMetrics> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AdminUserOpsMetrics>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AdminUserOpsMetrics.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AdminUserOpsMetrics> mapFromJson(dynamic json) {
    final map = <String, AdminUserOpsMetrics>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AdminUserOpsMetrics.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AdminUserOpsMetrics-objects as value to a dart map
  static Map<String, List<AdminUserOpsMetrics>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AdminUserOpsMetrics>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AdminUserOpsMetrics.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

