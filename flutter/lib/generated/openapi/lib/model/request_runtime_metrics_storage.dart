//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class RequestRuntimeMetricsStorage {
  /// Returns a new [RequestRuntimeMetricsStorage] instance.
  RequestRuntimeMetricsStorage({
    this.backend,
    this.shared,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? backend;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  bool? shared;

  @override
  bool operator ==(Object other) => identical(this, other) || other is RequestRuntimeMetricsStorage &&
    other.backend == backend &&
    other.shared == shared;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (backend == null ? 0 : backend!.hashCode) +
    (shared == null ? 0 : shared!.hashCode);

  @override
  String toString() => 'RequestRuntimeMetricsStorage[backend=$backend, shared=$shared]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.backend != null) {
      json[r'backend'] = this.backend;
    } else {
      json[r'backend'] = null;
    }
    if (this.shared != null) {
      json[r'shared'] = this.shared;
    } else {
      json[r'shared'] = null;
    }
    return json;
  }

  /// Returns a new [RequestRuntimeMetricsStorage] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static RequestRuntimeMetricsStorage? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "RequestRuntimeMetricsStorage[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "RequestRuntimeMetricsStorage[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return RequestRuntimeMetricsStorage(
        backend: mapValueOfType<String>(json, r'backend'),
        shared: mapValueOfType<bool>(json, r'shared'),
      );
    }
    return null;
  }

  static List<RequestRuntimeMetricsStorage> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <RequestRuntimeMetricsStorage>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = RequestRuntimeMetricsStorage.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, RequestRuntimeMetricsStorage> mapFromJson(dynamic json) {
    final map = <String, RequestRuntimeMetricsStorage>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = RequestRuntimeMetricsStorage.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of RequestRuntimeMetricsStorage-objects as value to a dart map
  static Map<String, List<RequestRuntimeMetricsStorage>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<RequestRuntimeMetricsStorage>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = RequestRuntimeMetricsStorage.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

