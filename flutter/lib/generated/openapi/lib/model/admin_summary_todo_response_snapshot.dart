//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AdminSummaryTodoResponseSnapshot {
  /// Returns a new [AdminSummaryTodoResponseSnapshot] instance.
  AdminSummaryTodoResponseSnapshot({
    this.activeInvites,
    this.inviteThreshold,
    this.disabledPolicies,
    this.degradedUpstream,
    this.failedAuditsToday,
    this.disabledUsers,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? activeInvites;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? inviteThreshold;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? disabledPolicies;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? degradedUpstream;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? failedAuditsToday;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? disabledUsers;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AdminSummaryTodoResponseSnapshot &&
    other.activeInvites == activeInvites &&
    other.inviteThreshold == inviteThreshold &&
    other.disabledPolicies == disabledPolicies &&
    other.degradedUpstream == degradedUpstream &&
    other.failedAuditsToday == failedAuditsToday &&
    other.disabledUsers == disabledUsers;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (activeInvites == null ? 0 : activeInvites!.hashCode) +
    (inviteThreshold == null ? 0 : inviteThreshold!.hashCode) +
    (disabledPolicies == null ? 0 : disabledPolicies!.hashCode) +
    (degradedUpstream == null ? 0 : degradedUpstream!.hashCode) +
    (failedAuditsToday == null ? 0 : failedAuditsToday!.hashCode) +
    (disabledUsers == null ? 0 : disabledUsers!.hashCode);

  @override
  String toString() => 'AdminSummaryTodoResponseSnapshot[activeInvites=$activeInvites, inviteThreshold=$inviteThreshold, disabledPolicies=$disabledPolicies, degradedUpstream=$degradedUpstream, failedAuditsToday=$failedAuditsToday, disabledUsers=$disabledUsers]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.activeInvites != null) {
      json[r'active_invites'] = this.activeInvites;
    } else {
      json[r'active_invites'] = null;
    }
    if (this.inviteThreshold != null) {
      json[r'invite_threshold'] = this.inviteThreshold;
    } else {
      json[r'invite_threshold'] = null;
    }
    if (this.disabledPolicies != null) {
      json[r'disabled_policies'] = this.disabledPolicies;
    } else {
      json[r'disabled_policies'] = null;
    }
    if (this.degradedUpstream != null) {
      json[r'degraded_upstream'] = this.degradedUpstream;
    } else {
      json[r'degraded_upstream'] = null;
    }
    if (this.failedAuditsToday != null) {
      json[r'failed_audits_today'] = this.failedAuditsToday;
    } else {
      json[r'failed_audits_today'] = null;
    }
    if (this.disabledUsers != null) {
      json[r'disabled_users'] = this.disabledUsers;
    } else {
      json[r'disabled_users'] = null;
    }
    return json;
  }

  /// Returns a new [AdminSummaryTodoResponseSnapshot] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AdminSummaryTodoResponseSnapshot? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AdminSummaryTodoResponseSnapshot[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AdminSummaryTodoResponseSnapshot[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AdminSummaryTodoResponseSnapshot(
        activeInvites: mapValueOfType<int>(json, r'active_invites'),
        inviteThreshold: mapValueOfType<int>(json, r'invite_threshold'),
        disabledPolicies: mapValueOfType<int>(json, r'disabled_policies'),
        degradedUpstream: mapValueOfType<int>(json, r'degraded_upstream'),
        failedAuditsToday: mapValueOfType<int>(json, r'failed_audits_today'),
        disabledUsers: mapValueOfType<int>(json, r'disabled_users'),
      );
    }
    return null;
  }

  static List<AdminSummaryTodoResponseSnapshot> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AdminSummaryTodoResponseSnapshot>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AdminSummaryTodoResponseSnapshot.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AdminSummaryTodoResponseSnapshot> mapFromJson(dynamic json) {
    final map = <String, AdminSummaryTodoResponseSnapshot>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AdminSummaryTodoResponseSnapshot.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AdminSummaryTodoResponseSnapshot-objects as value to a dart map
  static Map<String, List<AdminSummaryTodoResponseSnapshot>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AdminSummaryTodoResponseSnapshot>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AdminSummaryTodoResponseSnapshot.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

