//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AdminOverviewResponse {
  /// Returns a new [AdminOverviewResponse] instance.
  AdminOverviewResponse({
    this.dashboard,
    this.retentionRows = const [],
    this.users,
    this.userOps,
    this.snapshots,
    this.recentAudits = const [],
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  AdminOverviewResponseDashboard? dashboard;

  List<AdminRetentionRow> retentionRows;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  AdminOverviewResponseUsers? users;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  AdminUserOpsMetrics? userOps;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  AdminOverviewResponseSnapshots? snapshots;

  List<AdminAuditItem> recentAudits;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AdminOverviewResponse &&
    other.dashboard == dashboard &&
    _deepEquality.equals(other.retentionRows, retentionRows) &&
    other.users == users &&
    other.userOps == userOps &&
    other.snapshots == snapshots &&
    _deepEquality.equals(other.recentAudits, recentAudits);

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (dashboard == null ? 0 : dashboard!.hashCode) +
    (retentionRows.hashCode) +
    (users == null ? 0 : users!.hashCode) +
    (userOps == null ? 0 : userOps!.hashCode) +
    (snapshots == null ? 0 : snapshots!.hashCode) +
    (recentAudits.hashCode);

  @override
  String toString() => 'AdminOverviewResponse[dashboard=$dashboard, retentionRows=$retentionRows, users=$users, userOps=$userOps, snapshots=$snapshots, recentAudits=$recentAudits]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.dashboard != null) {
      json[r'dashboard'] = this.dashboard;
    } else {
      json[r'dashboard'] = null;
    }
      json[r'retention_rows'] = this.retentionRows;
    if (this.users != null) {
      json[r'users'] = this.users;
    } else {
      json[r'users'] = null;
    }
    if (this.userOps != null) {
      json[r'user_ops'] = this.userOps;
    } else {
      json[r'user_ops'] = null;
    }
    if (this.snapshots != null) {
      json[r'snapshots'] = this.snapshots;
    } else {
      json[r'snapshots'] = null;
    }
      json[r'recent_audits'] = this.recentAudits;
    return json;
  }

  /// Returns a new [AdminOverviewResponse] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AdminOverviewResponse? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AdminOverviewResponse[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AdminOverviewResponse[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AdminOverviewResponse(
        dashboard: AdminOverviewResponseDashboard.fromJson(json[r'dashboard']),
        retentionRows: AdminRetentionRow.listFromJson(json[r'retention_rows']),
        users: AdminOverviewResponseUsers.fromJson(json[r'users']),
        userOps: AdminUserOpsMetrics.fromJson(json[r'user_ops']),
        snapshots: AdminOverviewResponseSnapshots.fromJson(json[r'snapshots']),
        recentAudits: AdminAuditItem.listFromJson(json[r'recent_audits']),
      );
    }
    return null;
  }

  static List<AdminOverviewResponse> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AdminOverviewResponse>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AdminOverviewResponse.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AdminOverviewResponse> mapFromJson(dynamic json) {
    final map = <String, AdminOverviewResponse>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AdminOverviewResponse.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AdminOverviewResponse-objects as value to a dart map
  static Map<String, List<AdminOverviewResponse>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AdminOverviewResponse>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AdminOverviewResponse.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

