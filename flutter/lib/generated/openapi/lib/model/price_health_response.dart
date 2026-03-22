//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class PriceHealthResponse {
  /// Returns a new [PriceHealthResponse] instance.
  PriceHealthResponse({
    this.status,
    this.version,
    this.serverTimeUtc,
    this.runtime,
    this.sources = const {},
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
  String? serverTimeUtc;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  PriceRuntimeMetrics? runtime;

  Map<String, PriceSourceHealthItem> sources;

  @override
  bool operator ==(Object other) => identical(this, other) || other is PriceHealthResponse &&
    other.status == status &&
    other.version == version &&
    other.serverTimeUtc == serverTimeUtc &&
    other.runtime == runtime &&
    _deepEquality.equals(other.sources, sources);

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (status == null ? 0 : status!.hashCode) +
    (version == null ? 0 : version!.hashCode) +
    (serverTimeUtc == null ? 0 : serverTimeUtc!.hashCode) +
    (runtime == null ? 0 : runtime!.hashCode) +
    (sources.hashCode);

  @override
  String toString() => 'PriceHealthResponse[status=$status, version=$version, serverTimeUtc=$serverTimeUtc, runtime=$runtime, sources=$sources]';

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
    if (this.serverTimeUtc != null) {
      json[r'server_time_utc'] = this.serverTimeUtc;
    } else {
      json[r'server_time_utc'] = null;
    }
    if (this.runtime != null) {
      json[r'runtime'] = this.runtime;
    } else {
      json[r'runtime'] = null;
    }
      json[r'sources'] = this.sources;
    return json;
  }

  /// Returns a new [PriceHealthResponse] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static PriceHealthResponse? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "PriceHealthResponse[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "PriceHealthResponse[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return PriceHealthResponse(
        status: mapValueOfType<String>(json, r'status'),
        version: mapValueOfType<String>(json, r'version'),
        serverTimeUtc: mapValueOfType<String>(json, r'server_time_utc'),
        runtime: PriceRuntimeMetrics.fromJson(json[r'runtime']),
        sources: PriceSourceHealthItem.mapFromJson(json[r'sources']),
      );
    }
    return null;
  }

  static List<PriceHealthResponse> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <PriceHealthResponse>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = PriceHealthResponse.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, PriceHealthResponse> mapFromJson(dynamic json) {
    final map = <String, PriceHealthResponse>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = PriceHealthResponse.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of PriceHealthResponse-objects as value to a dart map
  static Map<String, List<PriceHealthResponse>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<PriceHealthResponse>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = PriceHealthResponse.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

