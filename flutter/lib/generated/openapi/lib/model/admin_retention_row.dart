//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AdminRetentionRow {
  /// Returns a new [AdminRetentionRow] instance.
  AdminRetentionRow({
    this.date,
    this.newUsers,
    this.activeUsers,
    this.retention1d,
    this.retention3d,
    this.retention7d,
    this.retention14d,
    this.retention30d,
    this.activeRetention1d,
    this.activeRetention3d,
    this.activeRetention7d,
    this.activeRetention14d,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? date;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? newUsers;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? activeUsers;

  num? retention1d;

  num? retention3d;

  num? retention7d;

  num? retention14d;

  num? retention30d;

  num? activeRetention1d;

  num? activeRetention3d;

  num? activeRetention7d;

  num? activeRetention14d;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AdminRetentionRow &&
    other.date == date &&
    other.newUsers == newUsers &&
    other.activeUsers == activeUsers &&
    other.retention1d == retention1d &&
    other.retention3d == retention3d &&
    other.retention7d == retention7d &&
    other.retention14d == retention14d &&
    other.retention30d == retention30d &&
    other.activeRetention1d == activeRetention1d &&
    other.activeRetention3d == activeRetention3d &&
    other.activeRetention7d == activeRetention7d &&
    other.activeRetention14d == activeRetention14d;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (date == null ? 0 : date!.hashCode) +
    (newUsers == null ? 0 : newUsers!.hashCode) +
    (activeUsers == null ? 0 : activeUsers!.hashCode) +
    (retention1d == null ? 0 : retention1d!.hashCode) +
    (retention3d == null ? 0 : retention3d!.hashCode) +
    (retention7d == null ? 0 : retention7d!.hashCode) +
    (retention14d == null ? 0 : retention14d!.hashCode) +
    (retention30d == null ? 0 : retention30d!.hashCode) +
    (activeRetention1d == null ? 0 : activeRetention1d!.hashCode) +
    (activeRetention3d == null ? 0 : activeRetention3d!.hashCode) +
    (activeRetention7d == null ? 0 : activeRetention7d!.hashCode) +
    (activeRetention14d == null ? 0 : activeRetention14d!.hashCode);

  @override
  String toString() => 'AdminRetentionRow[date=$date, newUsers=$newUsers, activeUsers=$activeUsers, retention1d=$retention1d, retention3d=$retention3d, retention7d=$retention7d, retention14d=$retention14d, retention30d=$retention30d, activeRetention1d=$activeRetention1d, activeRetention3d=$activeRetention3d, activeRetention7d=$activeRetention7d, activeRetention14d=$activeRetention14d]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.date != null) {
      json[r'date'] = this.date;
    } else {
      json[r'date'] = null;
    }
    if (this.newUsers != null) {
      json[r'new_users'] = this.newUsers;
    } else {
      json[r'new_users'] = null;
    }
    if (this.activeUsers != null) {
      json[r'active_users'] = this.activeUsers;
    } else {
      json[r'active_users'] = null;
    }
    if (this.retention1d != null) {
      json[r'retention_1d'] = this.retention1d;
    } else {
      json[r'retention_1d'] = null;
    }
    if (this.retention3d != null) {
      json[r'retention_3d'] = this.retention3d;
    } else {
      json[r'retention_3d'] = null;
    }
    if (this.retention7d != null) {
      json[r'retention_7d'] = this.retention7d;
    } else {
      json[r'retention_7d'] = null;
    }
    if (this.retention14d != null) {
      json[r'retention_14d'] = this.retention14d;
    } else {
      json[r'retention_14d'] = null;
    }
    if (this.retention30d != null) {
      json[r'retention_30d'] = this.retention30d;
    } else {
      json[r'retention_30d'] = null;
    }
    if (this.activeRetention1d != null) {
      json[r'active_retention_1d'] = this.activeRetention1d;
    } else {
      json[r'active_retention_1d'] = null;
    }
    if (this.activeRetention3d != null) {
      json[r'active_retention_3d'] = this.activeRetention3d;
    } else {
      json[r'active_retention_3d'] = null;
    }
    if (this.activeRetention7d != null) {
      json[r'active_retention_7d'] = this.activeRetention7d;
    } else {
      json[r'active_retention_7d'] = null;
    }
    if (this.activeRetention14d != null) {
      json[r'active_retention_14d'] = this.activeRetention14d;
    } else {
      json[r'active_retention_14d'] = null;
    }
    return json;
  }

  /// Returns a new [AdminRetentionRow] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AdminRetentionRow? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AdminRetentionRow[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AdminRetentionRow[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AdminRetentionRow(
        date: mapValueOfType<String>(json, r'date'),
        newUsers: mapValueOfType<int>(json, r'new_users'),
        activeUsers: mapValueOfType<int>(json, r'active_users'),
        retention1d: json[r'retention_1d'] == null
            ? null
            : num.parse('${json[r'retention_1d']}'),
        retention3d: json[r'retention_3d'] == null
            ? null
            : num.parse('${json[r'retention_3d']}'),
        retention7d: json[r'retention_7d'] == null
            ? null
            : num.parse('${json[r'retention_7d']}'),
        retention14d: json[r'retention_14d'] == null
            ? null
            : num.parse('${json[r'retention_14d']}'),
        retention30d: json[r'retention_30d'] == null
            ? null
            : num.parse('${json[r'retention_30d']}'),
        activeRetention1d: json[r'active_retention_1d'] == null
            ? null
            : num.parse('${json[r'active_retention_1d']}'),
        activeRetention3d: json[r'active_retention_3d'] == null
            ? null
            : num.parse('${json[r'active_retention_3d']}'),
        activeRetention7d: json[r'active_retention_7d'] == null
            ? null
            : num.parse('${json[r'active_retention_7d']}'),
        activeRetention14d: json[r'active_retention_14d'] == null
            ? null
            : num.parse('${json[r'active_retention_14d']}'),
      );
    }
    return null;
  }

  static List<AdminRetentionRow> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AdminRetentionRow>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AdminRetentionRow.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AdminRetentionRow> mapFromJson(dynamic json) {
    final map = <String, AdminRetentionRow>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AdminRetentionRow.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AdminRetentionRow-objects as value to a dart map
  static Map<String, List<AdminRetentionRow>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AdminRetentionRow>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AdminRetentionRow.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

