//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AdminSnapshotHealthResponse {
  /// Returns a new [AdminSnapshotHealthResponse] instance.
  AdminSnapshotHealthResponse({
    this.status,
    this.serverTime,
    this.today,
    this.todaySnapshotUsers,
    this.totalUsers,
    this.maxGapDays,
    this.users = const [],
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
  String? serverTime;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? today;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? todaySnapshotUsers;

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
  int? maxGapDays;

  List<AdminSnapshotHealthUser> users;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AdminSnapshotHealthResponse &&
    other.status == status &&
    other.serverTime == serverTime &&
    other.today == today &&
    other.todaySnapshotUsers == todaySnapshotUsers &&
    other.totalUsers == totalUsers &&
    other.maxGapDays == maxGapDays &&
    _deepEquality.equals(other.users, users);

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (status == null ? 0 : status!.hashCode) +
    (serverTime == null ? 0 : serverTime!.hashCode) +
    (today == null ? 0 : today!.hashCode) +
    (todaySnapshotUsers == null ? 0 : todaySnapshotUsers!.hashCode) +
    (totalUsers == null ? 0 : totalUsers!.hashCode) +
    (maxGapDays == null ? 0 : maxGapDays!.hashCode) +
    (users.hashCode);

  @override
  String toString() => 'AdminSnapshotHealthResponse[status=$status, serverTime=$serverTime, today=$today, todaySnapshotUsers=$todaySnapshotUsers, totalUsers=$totalUsers, maxGapDays=$maxGapDays, users=$users]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.status != null) {
      json[r'status'] = this.status;
    } else {
      json[r'status'] = null;
    }
    if (this.serverTime != null) {
      json[r'server_time'] = this.serverTime;
    } else {
      json[r'server_time'] = null;
    }
    if (this.today != null) {
      json[r'today'] = this.today;
    } else {
      json[r'today'] = null;
    }
    if (this.todaySnapshotUsers != null) {
      json[r'today_snapshot_users'] = this.todaySnapshotUsers;
    } else {
      json[r'today_snapshot_users'] = null;
    }
    if (this.totalUsers != null) {
      json[r'total_users'] = this.totalUsers;
    } else {
      json[r'total_users'] = null;
    }
    if (this.maxGapDays != null) {
      json[r'max_gap_days'] = this.maxGapDays;
    } else {
      json[r'max_gap_days'] = null;
    }
      json[r'users'] = this.users;
    return json;
  }

  /// Returns a new [AdminSnapshotHealthResponse] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AdminSnapshotHealthResponse? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AdminSnapshotHealthResponse[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AdminSnapshotHealthResponse[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AdminSnapshotHealthResponse(
        status: mapValueOfType<String>(json, r'status'),
        serverTime: mapValueOfType<String>(json, r'server_time'),
        today: mapValueOfType<String>(json, r'today'),
        todaySnapshotUsers: mapValueOfType<int>(json, r'today_snapshot_users'),
        totalUsers: mapValueOfType<int>(json, r'total_users'),
        maxGapDays: mapValueOfType<int>(json, r'max_gap_days'),
        users: AdminSnapshotHealthUser.listFromJson(json[r'users']),
      );
    }
    return null;
  }

  static List<AdminSnapshotHealthResponse> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AdminSnapshotHealthResponse>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AdminSnapshotHealthResponse.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AdminSnapshotHealthResponse> mapFromJson(dynamic json) {
    final map = <String, AdminSnapshotHealthResponse>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AdminSnapshotHealthResponse.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AdminSnapshotHealthResponse-objects as value to a dart map
  static Map<String, List<AdminSnapshotHealthResponse>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AdminSnapshotHealthResponse>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AdminSnapshotHealthResponse.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

