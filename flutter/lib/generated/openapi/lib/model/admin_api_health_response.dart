//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AdminApiHealthResponse {
  /// Returns a new [AdminApiHealthResponse] instance.
  AdminApiHealthResponse({
    this.status,
    this.serverTimeUtc,
    this.db,
    this.upstream = const {},
    this.policies = const [],
    this.runtime,
    this.sources = const {},
    this.versionInfo,
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
  String? serverTimeUtc;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  AdminApiHealthResponseDb? db;

  Map<String, AdminUpstreamStatusItem> upstream;

  List<AdminPolicyItem> policies;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  PriceRuntimeMetrics? runtime;

  Map<String, PriceSourceHealthItem> sources;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  AdminApiHealthResponseVersionInfo? versionInfo;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AdminApiHealthResponse &&
    other.status == status &&
    other.serverTimeUtc == serverTimeUtc &&
    other.db == db &&
    _deepEquality.equals(other.upstream, upstream) &&
    _deepEquality.equals(other.policies, policies) &&
    other.runtime == runtime &&
    _deepEquality.equals(other.sources, sources) &&
    other.versionInfo == versionInfo;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (status == null ? 0 : status!.hashCode) +
    (serverTimeUtc == null ? 0 : serverTimeUtc!.hashCode) +
    (db == null ? 0 : db!.hashCode) +
    (upstream.hashCode) +
    (policies.hashCode) +
    (runtime == null ? 0 : runtime!.hashCode) +
    (sources.hashCode) +
    (versionInfo == null ? 0 : versionInfo!.hashCode);

  @override
  String toString() => 'AdminApiHealthResponse[status=$status, serverTimeUtc=$serverTimeUtc, db=$db, upstream=$upstream, policies=$policies, runtime=$runtime, sources=$sources, versionInfo=$versionInfo]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.status != null) {
      json[r'status'] = this.status;
    } else {
      json[r'status'] = null;
    }
    if (this.serverTimeUtc != null) {
      json[r'server_time_utc'] = this.serverTimeUtc;
    } else {
      json[r'server_time_utc'] = null;
    }
    if (this.db != null) {
      json[r'db'] = this.db;
    } else {
      json[r'db'] = null;
    }
      json[r'upstream'] = this.upstream;
      json[r'policies'] = this.policies;
    if (this.runtime != null) {
      json[r'runtime'] = this.runtime;
    } else {
      json[r'runtime'] = null;
    }
      json[r'sources'] = this.sources;
    if (this.versionInfo != null) {
      json[r'version_info'] = this.versionInfo;
    } else {
      json[r'version_info'] = null;
    }
    return json;
  }

  /// Returns a new [AdminApiHealthResponse] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AdminApiHealthResponse? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AdminApiHealthResponse[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AdminApiHealthResponse[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AdminApiHealthResponse(
        status: mapValueOfType<String>(json, r'status'),
        serverTimeUtc: mapValueOfType<String>(json, r'server_time_utc'),
        db: AdminApiHealthResponseDb.fromJson(json[r'db']),
        upstream: AdminUpstreamStatusItem.mapFromJson(json[r'upstream']),
        policies: AdminPolicyItem.listFromJson(json[r'policies']),
        runtime: PriceRuntimeMetrics.fromJson(json[r'runtime']),
        sources: PriceSourceHealthItem.mapFromJson(json[r'sources']),
        versionInfo: AdminApiHealthResponseVersionInfo.fromJson(json[r'version_info']),
      );
    }
    return null;
  }

  static List<AdminApiHealthResponse> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AdminApiHealthResponse>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AdminApiHealthResponse.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AdminApiHealthResponse> mapFromJson(dynamic json) {
    final map = <String, AdminApiHealthResponse>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AdminApiHealthResponse.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AdminApiHealthResponse-objects as value to a dart map
  static Map<String, List<AdminApiHealthResponse>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AdminApiHealthResponse>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AdminApiHealthResponse.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

