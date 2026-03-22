//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class PriceRuntimeMetrics {
  /// Returns a new [PriceRuntimeMetrics] instance.
  PriceRuntimeMetrics({
    this.cacheHits,
    this.staleHits,
    this.networkFetch,
    this.networkFail,
    this.lastFetchAt,
    this.cache,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? cacheHits;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? staleHits;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? networkFetch;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? networkFail;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? lastFetchAt;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  PriceCacheStats? cache;

  @override
  bool operator ==(Object other) => identical(this, other) || other is PriceRuntimeMetrics &&
    other.cacheHits == cacheHits &&
    other.staleHits == staleHits &&
    other.networkFetch == networkFetch &&
    other.networkFail == networkFail &&
    other.lastFetchAt == lastFetchAt &&
    other.cache == cache;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (cacheHits == null ? 0 : cacheHits!.hashCode) +
    (staleHits == null ? 0 : staleHits!.hashCode) +
    (networkFetch == null ? 0 : networkFetch!.hashCode) +
    (networkFail == null ? 0 : networkFail!.hashCode) +
    (lastFetchAt == null ? 0 : lastFetchAt!.hashCode) +
    (cache == null ? 0 : cache!.hashCode);

  @override
  String toString() => 'PriceRuntimeMetrics[cacheHits=$cacheHits, staleHits=$staleHits, networkFetch=$networkFetch, networkFail=$networkFail, lastFetchAt=$lastFetchAt, cache=$cache]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.cacheHits != null) {
      json[r'cache_hits'] = this.cacheHits;
    } else {
      json[r'cache_hits'] = null;
    }
    if (this.staleHits != null) {
      json[r'stale_hits'] = this.staleHits;
    } else {
      json[r'stale_hits'] = null;
    }
    if (this.networkFetch != null) {
      json[r'network_fetch'] = this.networkFetch;
    } else {
      json[r'network_fetch'] = null;
    }
    if (this.networkFail != null) {
      json[r'network_fail'] = this.networkFail;
    } else {
      json[r'network_fail'] = null;
    }
    if (this.lastFetchAt != null) {
      json[r'last_fetch_at'] = this.lastFetchAt;
    } else {
      json[r'last_fetch_at'] = null;
    }
    if (this.cache != null) {
      json[r'cache'] = this.cache;
    } else {
      json[r'cache'] = null;
    }
    return json;
  }

  /// Returns a new [PriceRuntimeMetrics] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static PriceRuntimeMetrics? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "PriceRuntimeMetrics[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "PriceRuntimeMetrics[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return PriceRuntimeMetrics(
        cacheHits: mapValueOfType<int>(json, r'cache_hits'),
        staleHits: mapValueOfType<int>(json, r'stale_hits'),
        networkFetch: mapValueOfType<int>(json, r'network_fetch'),
        networkFail: mapValueOfType<int>(json, r'network_fail'),
        lastFetchAt: num.parse('${json[r'last_fetch_at']}'),
        cache: PriceCacheStats.fromJson(json[r'cache']),
      );
    }
    return null;
  }

  static List<PriceRuntimeMetrics> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <PriceRuntimeMetrics>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = PriceRuntimeMetrics.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, PriceRuntimeMetrics> mapFromJson(dynamic json) {
    final map = <String, PriceRuntimeMetrics>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = PriceRuntimeMetrics.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of PriceRuntimeMetrics-objects as value to a dart map
  static Map<String, List<PriceRuntimeMetrics>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<PriceRuntimeMetrics>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = PriceRuntimeMetrics.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

