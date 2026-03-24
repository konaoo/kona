//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class SyncBootstrapResponseQuotePolicy {
  /// Returns a new [SyncBootstrapResponseQuotePolicy] instance.
  SyncBootstrapResponseQuotePolicy({
    this.intervalOpenSec,
    this.intervalClosedSec,
    this.intervalUsExtendedSec,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? intervalOpenSec;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? intervalClosedSec;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? intervalUsExtendedSec;

  @override
  bool operator ==(Object other) => identical(this, other) || other is SyncBootstrapResponseQuotePolicy &&
    other.intervalOpenSec == intervalOpenSec &&
    other.intervalClosedSec == intervalClosedSec &&
    other.intervalUsExtendedSec == intervalUsExtendedSec;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (intervalOpenSec == null ? 0 : intervalOpenSec!.hashCode) +
    (intervalClosedSec == null ? 0 : intervalClosedSec!.hashCode) +
    (intervalUsExtendedSec == null ? 0 : intervalUsExtendedSec!.hashCode);

  @override
  String toString() => 'SyncBootstrapResponseQuotePolicy[intervalOpenSec=$intervalOpenSec, intervalClosedSec=$intervalClosedSec, intervalUsExtendedSec=$intervalUsExtendedSec]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.intervalOpenSec != null) {
      json[r'interval_open_sec'] = this.intervalOpenSec;
    } else {
      json[r'interval_open_sec'] = null;
    }
    if (this.intervalClosedSec != null) {
      json[r'interval_closed_sec'] = this.intervalClosedSec;
    } else {
      json[r'interval_closed_sec'] = null;
    }
    if (this.intervalUsExtendedSec != null) {
      json[r'interval_us_extended_sec'] = this.intervalUsExtendedSec;
    } else {
      json[r'interval_us_extended_sec'] = null;
    }
    return json;
  }

  /// Returns a new [SyncBootstrapResponseQuotePolicy] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static SyncBootstrapResponseQuotePolicy? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "SyncBootstrapResponseQuotePolicy[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "SyncBootstrapResponseQuotePolicy[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return SyncBootstrapResponseQuotePolicy(
        intervalOpenSec: mapValueOfType<int>(json, r'interval_open_sec'),
        intervalClosedSec: mapValueOfType<int>(json, r'interval_closed_sec'),
        intervalUsExtendedSec: mapValueOfType<int>(json, r'interval_us_extended_sec'),
      );
    }
    return null;
  }

  static List<SyncBootstrapResponseQuotePolicy> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <SyncBootstrapResponseQuotePolicy>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = SyncBootstrapResponseQuotePolicy.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, SyncBootstrapResponseQuotePolicy> mapFromJson(dynamic json) {
    final map = <String, SyncBootstrapResponseQuotePolicy>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = SyncBootstrapResponseQuotePolicy.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of SyncBootstrapResponseQuotePolicy-objects as value to a dart map
  static Map<String, List<SyncBootstrapResponseQuotePolicy>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<SyncBootstrapResponseQuotePolicy>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = SyncBootstrapResponseQuotePolicy.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

