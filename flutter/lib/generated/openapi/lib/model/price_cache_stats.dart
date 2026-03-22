//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class PriceCacheStats {
  /// Returns a new [PriceCacheStats] instance.
  PriceCacheStats({
    this.size,
    this.maxSize,
    this.evictions,
    this.ttl,
    this.staleTtl,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? size;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? maxSize;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? evictions;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? ttl;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? staleTtl;

  @override
  bool operator ==(Object other) => identical(this, other) || other is PriceCacheStats &&
    other.size == size &&
    other.maxSize == maxSize &&
    other.evictions == evictions &&
    other.ttl == ttl &&
    other.staleTtl == staleTtl;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (size == null ? 0 : size!.hashCode) +
    (maxSize == null ? 0 : maxSize!.hashCode) +
    (evictions == null ? 0 : evictions!.hashCode) +
    (ttl == null ? 0 : ttl!.hashCode) +
    (staleTtl == null ? 0 : staleTtl!.hashCode);

  @override
  String toString() => 'PriceCacheStats[size=$size, maxSize=$maxSize, evictions=$evictions, ttl=$ttl, staleTtl=$staleTtl]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.size != null) {
      json[r'size'] = this.size;
    } else {
      json[r'size'] = null;
    }
    if (this.maxSize != null) {
      json[r'max_size'] = this.maxSize;
    } else {
      json[r'max_size'] = null;
    }
    if (this.evictions != null) {
      json[r'evictions'] = this.evictions;
    } else {
      json[r'evictions'] = null;
    }
    if (this.ttl != null) {
      json[r'ttl'] = this.ttl;
    } else {
      json[r'ttl'] = null;
    }
    if (this.staleTtl != null) {
      json[r'stale_ttl'] = this.staleTtl;
    } else {
      json[r'stale_ttl'] = null;
    }
    return json;
  }

  /// Returns a new [PriceCacheStats] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static PriceCacheStats? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "PriceCacheStats[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "PriceCacheStats[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return PriceCacheStats(
        size: mapValueOfType<int>(json, r'size'),
        maxSize: mapValueOfType<int>(json, r'max_size'),
        evictions: mapValueOfType<int>(json, r'evictions'),
        ttl: mapValueOfType<int>(json, r'ttl'),
        staleTtl: mapValueOfType<int>(json, r'stale_ttl'),
      );
    }
    return null;
  }

  static List<PriceCacheStats> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <PriceCacheStats>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = PriceCacheStats.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, PriceCacheStats> mapFromJson(dynamic json) {
    final map = <String, PriceCacheStats>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = PriceCacheStats.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of PriceCacheStats-objects as value to a dart map
  static Map<String, List<PriceCacheStats>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<PriceCacheStats>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = PriceCacheStats.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

