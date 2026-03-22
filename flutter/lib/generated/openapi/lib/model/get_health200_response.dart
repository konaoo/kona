//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class GetHealth200Response {
  /// Returns a new [GetHealth200Response] instance.
  GetHealth200Response({
    this.status,
    this.version,
    this.requestRuntime,
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
  String? version;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  RequestRuntimeMetrics? requestRuntime;

  @override
  bool operator ==(Object other) => identical(this, other) || other is GetHealth200Response &&
    other.status == status &&
    other.version == version &&
    other.requestRuntime == requestRuntime;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (status == null ? 0 : status!.hashCode) +
    (version == null ? 0 : version!.hashCode) +
    (requestRuntime == null ? 0 : requestRuntime!.hashCode);

  @override
  String toString() => 'GetHealth200Response[status=$status, version=$version, requestRuntime=$requestRuntime]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.status != null) {
      json[r'status'] = this.status;
    } else {
      json[r'status'] = null;
    }
    if (this.version != null) {
      json[r'version'] = this.version;
    } else {
      json[r'version'] = null;
    }
    if (this.requestRuntime != null) {
      json[r'request_runtime'] = this.requestRuntime;
    } else {
      json[r'request_runtime'] = null;
    }
    return json;
  }

  /// Returns a new [GetHealth200Response] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static GetHealth200Response? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "GetHealth200Response[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "GetHealth200Response[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return GetHealth200Response(
        status: mapValueOfType<String>(json, r'status'),
        version: mapValueOfType<String>(json, r'version'),
        requestRuntime: RequestRuntimeMetrics.fromJson(json[r'request_runtime']),
      );
    }
    return null;
  }

  static List<GetHealth200Response> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <GetHealth200Response>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = GetHealth200Response.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, GetHealth200Response> mapFromJson(dynamic json) {
    final map = <String, GetHealth200Response>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = GetHealth200Response.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of GetHealth200Response-objects as value to a dart map
  static Map<String, List<GetHealth200Response>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<GetHealth200Response>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = GetHealth200Response.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

