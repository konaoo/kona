//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class PriceSourceHealthItem {
  /// Returns a new [PriceSourceHealthItem] instance.
  PriceSourceHealthItem({
    this.ok,
    this.fail,
    this.timeout,
    this.consecutiveFail,
    this.latencyAvgMs,
    this.lastError,
    this.lastOkAt,
    this.lastFailAt,
    this.circuitOpenUntil,
    this.circuitOpen,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? ok;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? fail;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? timeout;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? consecutiveFail;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? latencyAvgMs;

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
  String? lastOkAt;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? lastFailAt;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? circuitOpenUntil;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  bool? circuitOpen;

  @override
  bool operator ==(Object other) => identical(this, other) || other is PriceSourceHealthItem &&
    other.ok == ok &&
    other.fail == fail &&
    other.timeout == timeout &&
    other.consecutiveFail == consecutiveFail &&
    other.latencyAvgMs == latencyAvgMs &&
    other.lastError == lastError &&
    other.lastOkAt == lastOkAt &&
    other.lastFailAt == lastFailAt &&
    other.circuitOpenUntil == circuitOpenUntil &&
    other.circuitOpen == circuitOpen;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (ok == null ? 0 : ok!.hashCode) +
    (fail == null ? 0 : fail!.hashCode) +
    (timeout == null ? 0 : timeout!.hashCode) +
    (consecutiveFail == null ? 0 : consecutiveFail!.hashCode) +
    (latencyAvgMs == null ? 0 : latencyAvgMs!.hashCode) +
    (lastError == null ? 0 : lastError!.hashCode) +
    (lastOkAt == null ? 0 : lastOkAt!.hashCode) +
    (lastFailAt == null ? 0 : lastFailAt!.hashCode) +
    (circuitOpenUntil == null ? 0 : circuitOpenUntil!.hashCode) +
    (circuitOpen == null ? 0 : circuitOpen!.hashCode);

  @override
  String toString() => 'PriceSourceHealthItem[ok=$ok, fail=$fail, timeout=$timeout, consecutiveFail=$consecutiveFail, latencyAvgMs=$latencyAvgMs, lastError=$lastError, lastOkAt=$lastOkAt, lastFailAt=$lastFailAt, circuitOpenUntil=$circuitOpenUntil, circuitOpen=$circuitOpen]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.ok != null) {
      json[r'ok'] = this.ok;
    } else {
      json[r'ok'] = null;
    }
    if (this.fail != null) {
      json[r'fail'] = this.fail;
    } else {
      json[r'fail'] = null;
    }
    if (this.timeout != null) {
      json[r'timeout'] = this.timeout;
    } else {
      json[r'timeout'] = null;
    }
    if (this.consecutiveFail != null) {
      json[r'consecutive_fail'] = this.consecutiveFail;
    } else {
      json[r'consecutive_fail'] = null;
    }
    if (this.latencyAvgMs != null) {
      json[r'latency_avg_ms'] = this.latencyAvgMs;
    } else {
      json[r'latency_avg_ms'] = null;
    }
    if (this.lastError != null) {
      json[r'last_error'] = this.lastError;
    } else {
      json[r'last_error'] = null;
    }
    if (this.lastOkAt != null) {
      json[r'last_ok_at'] = this.lastOkAt;
    } else {
      json[r'last_ok_at'] = null;
    }
    if (this.lastFailAt != null) {
      json[r'last_fail_at'] = this.lastFailAt;
    } else {
      json[r'last_fail_at'] = null;
    }
    if (this.circuitOpenUntil != null) {
      json[r'circuit_open_until'] = this.circuitOpenUntil;
    } else {
      json[r'circuit_open_until'] = null;
    }
    if (this.circuitOpen != null) {
      json[r'circuit_open'] = this.circuitOpen;
    } else {
      json[r'circuit_open'] = null;
    }
    return json;
  }

  /// Returns a new [PriceSourceHealthItem] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static PriceSourceHealthItem? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "PriceSourceHealthItem[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "PriceSourceHealthItem[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return PriceSourceHealthItem(
        ok: mapValueOfType<int>(json, r'ok'),
        fail: mapValueOfType<int>(json, r'fail'),
        timeout: mapValueOfType<int>(json, r'timeout'),
        consecutiveFail: mapValueOfType<int>(json, r'consecutive_fail'),
        latencyAvgMs: num.parse('${json[r'latency_avg_ms']}'),
        lastError: mapValueOfType<String>(json, r'last_error'),
        lastOkAt: mapValueOfType<String>(json, r'last_ok_at'),
        lastFailAt: mapValueOfType<String>(json, r'last_fail_at'),
        circuitOpenUntil: num.parse('${json[r'circuit_open_until']}'),
        circuitOpen: mapValueOfType<bool>(json, r'circuit_open'),
      );
    }
    return null;
  }

  static List<PriceSourceHealthItem> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <PriceSourceHealthItem>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = PriceSourceHealthItem.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, PriceSourceHealthItem> mapFromJson(dynamic json) {
    final map = <String, PriceSourceHealthItem>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = PriceSourceHealthItem.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of PriceSourceHealthItem-objects as value to a dart map
  static Map<String, List<PriceSourceHealthItem>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<PriceSourceHealthItem>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = PriceSourceHealthItem.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

