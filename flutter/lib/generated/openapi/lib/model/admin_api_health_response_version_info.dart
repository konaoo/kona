//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AdminApiHealthResponseVersionInfo {
  /// Returns a new [AdminApiHealthResponseVersionInfo] instance.
  AdminApiHealthResponseVersionInfo({
    this.version,
    this.commitHash,
    this.lastUpdate,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? version;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? commitHash;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? lastUpdate;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AdminApiHealthResponseVersionInfo &&
    other.version == version &&
    other.commitHash == commitHash &&
    other.lastUpdate == lastUpdate;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (version == null ? 0 : version!.hashCode) +
    (commitHash == null ? 0 : commitHash!.hashCode) +
    (lastUpdate == null ? 0 : lastUpdate!.hashCode);

  @override
  String toString() => 'AdminApiHealthResponseVersionInfo[version=$version, commitHash=$commitHash, lastUpdate=$lastUpdate]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.version != null) {
      json[r'version'] = this.version;
    } else {
      json[r'version'] = null;
    }
    if (this.commitHash != null) {
      json[r'commit_hash'] = this.commitHash;
    } else {
      json[r'commit_hash'] = null;
    }
    if (this.lastUpdate != null) {
      json[r'last_update'] = this.lastUpdate;
    } else {
      json[r'last_update'] = null;
    }
    return json;
  }

  /// Returns a new [AdminApiHealthResponseVersionInfo] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AdminApiHealthResponseVersionInfo? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AdminApiHealthResponseVersionInfo[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AdminApiHealthResponseVersionInfo[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AdminApiHealthResponseVersionInfo(
        version: mapValueOfType<String>(json, r'version'),
        commitHash: mapValueOfType<String>(json, r'commit_hash'),
        lastUpdate: mapValueOfType<String>(json, r'last_update'),
      );
    }
    return null;
  }

  static List<AdminApiHealthResponseVersionInfo> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AdminApiHealthResponseVersionInfo>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AdminApiHealthResponseVersionInfo.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AdminApiHealthResponseVersionInfo> mapFromJson(dynamic json) {
    final map = <String, AdminApiHealthResponseVersionInfo>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AdminApiHealthResponseVersionInfo.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AdminApiHealthResponseVersionInfo-objects as value to a dart map
  static Map<String, List<AdminApiHealthResponseVersionInfo>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AdminApiHealthResponseVersionInfo>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AdminApiHealthResponseVersionInfo.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

