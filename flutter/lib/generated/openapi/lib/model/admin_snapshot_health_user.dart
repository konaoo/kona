//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AdminSnapshotHealthUser {
  /// Returns a new [AdminSnapshotHealthUser] instance.
  AdminSnapshotHealthUser({
    this.userId,
    this.username,
    this.totalSnapshots,
    this.earliestDate,
    this.latestDate,
    this.lastUpdatedAt,
    this.gapDays,
    this.hasToday,
    this.status,
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
  String? username;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? totalSnapshots;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? earliestDate;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? latestDate;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? lastUpdatedAt;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? gapDays;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  bool? hasToday;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? status;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AdminSnapshotHealthUser &&
    other.userId == userId &&
    other.username == username &&
    other.totalSnapshots == totalSnapshots &&
    other.earliestDate == earliestDate &&
    other.latestDate == latestDate &&
    other.lastUpdatedAt == lastUpdatedAt &&
    other.gapDays == gapDays &&
    other.hasToday == hasToday &&
    other.status == status;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (userId == null ? 0 : userId!.hashCode) +
    (username == null ? 0 : username!.hashCode) +
    (totalSnapshots == null ? 0 : totalSnapshots!.hashCode) +
    (earliestDate == null ? 0 : earliestDate!.hashCode) +
    (latestDate == null ? 0 : latestDate!.hashCode) +
    (lastUpdatedAt == null ? 0 : lastUpdatedAt!.hashCode) +
    (gapDays == null ? 0 : gapDays!.hashCode) +
    (hasToday == null ? 0 : hasToday!.hashCode) +
    (status == null ? 0 : status!.hashCode);

  @override
  String toString() => 'AdminSnapshotHealthUser[userId=$userId, username=$username, totalSnapshots=$totalSnapshots, earliestDate=$earliestDate, latestDate=$latestDate, lastUpdatedAt=$lastUpdatedAt, gapDays=$gapDays, hasToday=$hasToday, status=$status]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.userId != null) {
      json[r'user_id'] = this.userId;
    } else {
      json[r'user_id'] = null;
    }
    if (this.username != null) {
      json[r'username'] = this.username;
    } else {
      json[r'username'] = null;
    }
    if (this.totalSnapshots != null) {
      json[r'total_snapshots'] = this.totalSnapshots;
    } else {
      json[r'total_snapshots'] = null;
    }
    if (this.earliestDate != null) {
      json[r'earliest_date'] = this.earliestDate;
    } else {
      json[r'earliest_date'] = null;
    }
    if (this.latestDate != null) {
      json[r'latest_date'] = this.latestDate;
    } else {
      json[r'latest_date'] = null;
    }
    if (this.lastUpdatedAt != null) {
      json[r'last_updated_at'] = this.lastUpdatedAt;
    } else {
      json[r'last_updated_at'] = null;
    }
    if (this.gapDays != null) {
      json[r'gap_days'] = this.gapDays;
    } else {
      json[r'gap_days'] = null;
    }
    if (this.hasToday != null) {
      json[r'has_today'] = this.hasToday;
    } else {
      json[r'has_today'] = null;
    }
    if (this.status != null) {
      json[r'status'] = this.status;
    } else {
      json[r'status'] = null;
    }
    return json;
  }

  /// Returns a new [AdminSnapshotHealthUser] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AdminSnapshotHealthUser? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AdminSnapshotHealthUser[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AdminSnapshotHealthUser[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AdminSnapshotHealthUser(
        userId: mapValueOfType<String>(json, r'user_id'),
        username: mapValueOfType<String>(json, r'username'),
        totalSnapshots: mapValueOfType<int>(json, r'total_snapshots'),
        earliestDate: mapValueOfType<String>(json, r'earliest_date'),
        latestDate: mapValueOfType<String>(json, r'latest_date'),
        lastUpdatedAt: mapValueOfType<String>(json, r'last_updated_at'),
        gapDays: mapValueOfType<int>(json, r'gap_days'),
        hasToday: mapValueOfType<bool>(json, r'has_today'),
        status: mapValueOfType<String>(json, r'status'),
      );
    }
    return null;
  }

  static List<AdminSnapshotHealthUser> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AdminSnapshotHealthUser>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AdminSnapshotHealthUser.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AdminSnapshotHealthUser> mapFromJson(dynamic json) {
    final map = <String, AdminSnapshotHealthUser>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AdminSnapshotHealthUser.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AdminSnapshotHealthUser-objects as value to a dart map
  static Map<String, List<AdminSnapshotHealthUser>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AdminSnapshotHealthUser>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AdminSnapshotHealthUser.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

