//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class RequestRuntimeMetrics {
  /// Returns a new [RequestRuntimeMetrics] instance.
  RequestRuntimeMetrics({
    this.policyRateAllowed,
    this.policyRateLimited,
    this.policyRateErrors,
    this.activityTouchWrite,
    this.activityTouchSkipped,
    this.activityTouchErrors,
    this.storageErrors,
    this.lastError,
    this.lastErrorAt,
    this.storage,
    this.activityTouchIntervalSeconds,
    this.policyRateTtlSeconds,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? policyRateAllowed;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? policyRateLimited;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? policyRateErrors;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? activityTouchWrite;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? activityTouchSkipped;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? activityTouchErrors;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? storageErrors;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? lastError;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? lastErrorAt;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  RequestRuntimeMetricsStorage? storage;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? activityTouchIntervalSeconds;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? policyRateTtlSeconds;

  @override
  bool operator ==(Object other) => identical(this, other) || other is RequestRuntimeMetrics &&
    other.policyRateAllowed == policyRateAllowed &&
    other.policyRateLimited == policyRateLimited &&
    other.policyRateErrors == policyRateErrors &&
    other.activityTouchWrite == activityTouchWrite &&
    other.activityTouchSkipped == activityTouchSkipped &&
    other.activityTouchErrors == activityTouchErrors &&
    other.storageErrors == storageErrors &&
    other.lastError == lastError &&
    other.lastErrorAt == lastErrorAt &&
    other.storage == storage &&
    other.activityTouchIntervalSeconds == activityTouchIntervalSeconds &&
    other.policyRateTtlSeconds == policyRateTtlSeconds;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (policyRateAllowed == null ? 0 : policyRateAllowed!.hashCode) +
    (policyRateLimited == null ? 0 : policyRateLimited!.hashCode) +
    (policyRateErrors == null ? 0 : policyRateErrors!.hashCode) +
    (activityTouchWrite == null ? 0 : activityTouchWrite!.hashCode) +
    (activityTouchSkipped == null ? 0 : activityTouchSkipped!.hashCode) +
    (activityTouchErrors == null ? 0 : activityTouchErrors!.hashCode) +
    (storageErrors == null ? 0 : storageErrors!.hashCode) +
    (lastError == null ? 0 : lastError!.hashCode) +
    (lastErrorAt == null ? 0 : lastErrorAt!.hashCode) +
    (storage == null ? 0 : storage!.hashCode) +
    (activityTouchIntervalSeconds == null ? 0 : activityTouchIntervalSeconds!.hashCode) +
    (policyRateTtlSeconds == null ? 0 : policyRateTtlSeconds!.hashCode);

  @override
  String toString() => 'RequestRuntimeMetrics[policyRateAllowed=$policyRateAllowed, policyRateLimited=$policyRateLimited, policyRateErrors=$policyRateErrors, activityTouchWrite=$activityTouchWrite, activityTouchSkipped=$activityTouchSkipped, activityTouchErrors=$activityTouchErrors, storageErrors=$storageErrors, lastError=$lastError, lastErrorAt=$lastErrorAt, storage=$storage, activityTouchIntervalSeconds=$activityTouchIntervalSeconds, policyRateTtlSeconds=$policyRateTtlSeconds]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.policyRateAllowed != null) {
      json[r'policy_rate_allowed'] = this.policyRateAllowed;
    } else {
      json[r'policy_rate_allowed'] = null;
    }
    if (this.policyRateLimited != null) {
      json[r'policy_rate_limited'] = this.policyRateLimited;
    } else {
      json[r'policy_rate_limited'] = null;
    }
    if (this.policyRateErrors != null) {
      json[r'policy_rate_errors'] = this.policyRateErrors;
    } else {
      json[r'policy_rate_errors'] = null;
    }
    if (this.activityTouchWrite != null) {
      json[r'activity_touch_write'] = this.activityTouchWrite;
    } else {
      json[r'activity_touch_write'] = null;
    }
    if (this.activityTouchSkipped != null) {
      json[r'activity_touch_skipped'] = this.activityTouchSkipped;
    } else {
      json[r'activity_touch_skipped'] = null;
    }
    if (this.activityTouchErrors != null) {
      json[r'activity_touch_errors'] = this.activityTouchErrors;
    } else {
      json[r'activity_touch_errors'] = null;
    }
    if (this.storageErrors != null) {
      json[r'storage_errors'] = this.storageErrors;
    } else {
      json[r'storage_errors'] = null;
    }
    if (this.lastError != null) {
      json[r'last_error'] = this.lastError;
    } else {
      json[r'last_error'] = null;
    }
    if (this.lastErrorAt != null) {
      json[r'last_error_at'] = this.lastErrorAt;
    } else {
      json[r'last_error_at'] = null;
    }
    if (this.storage != null) {
      json[r'storage'] = this.storage;
    } else {
      json[r'storage'] = null;
    }
    if (this.activityTouchIntervalSeconds != null) {
      json[r'activity_touch_interval_seconds'] = this.activityTouchIntervalSeconds;
    } else {
      json[r'activity_touch_interval_seconds'] = null;
    }
    if (this.policyRateTtlSeconds != null) {
      json[r'policy_rate_ttl_seconds'] = this.policyRateTtlSeconds;
    } else {
      json[r'policy_rate_ttl_seconds'] = null;
    }
    return json;
  }

  /// Returns a new [RequestRuntimeMetrics] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static RequestRuntimeMetrics? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "RequestRuntimeMetrics[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "RequestRuntimeMetrics[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return RequestRuntimeMetrics(
        policyRateAllowed: mapValueOfType<int>(json, r'policy_rate_allowed'),
        policyRateLimited: mapValueOfType<int>(json, r'policy_rate_limited'),
        policyRateErrors: mapValueOfType<int>(json, r'policy_rate_errors'),
        activityTouchWrite: mapValueOfType<int>(json, r'activity_touch_write'),
        activityTouchSkipped: mapValueOfType<int>(json, r'activity_touch_skipped'),
        activityTouchErrors: mapValueOfType<int>(json, r'activity_touch_errors'),
        storageErrors: mapValueOfType<int>(json, r'storage_errors'),
        lastError: mapValueOfType<String>(json, r'last_error'),
        lastErrorAt: num.parse('${json[r'last_error_at']}'),
        storage: RequestRuntimeMetricsStorage.fromJson(json[r'storage']),
        activityTouchIntervalSeconds: num.parse('${json[r'activity_touch_interval_seconds']}'),
        policyRateTtlSeconds: num.parse('${json[r'policy_rate_ttl_seconds']}'),
      );
    }
    return null;
  }

  static List<RequestRuntimeMetrics> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <RequestRuntimeMetrics>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = RequestRuntimeMetrics.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, RequestRuntimeMetrics> mapFromJson(dynamic json) {
    final map = <String, RequestRuntimeMetrics>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = RequestRuntimeMetrics.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of RequestRuntimeMetrics-objects as value to a dart map
  static Map<String, List<RequestRuntimeMetrics>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<RequestRuntimeMetrics>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = RequestRuntimeMetrics.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

