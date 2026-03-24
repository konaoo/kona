//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AnalysisMarketBreakdownItemMarkets {
  /// Returns a new [AnalysisMarketBreakdownItemMarkets] instance.
  AnalysisMarketBreakdownItemMarkets({
    this.a,
    this.hk,
    this.us,
    this.fund,
    this.unallocated,
  });

  num? a;

  num? hk;

  num? us;

  num? fund;

  num? unallocated;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AnalysisMarketBreakdownItemMarkets &&
    other.a == a &&
    other.hk == hk &&
    other.us == us &&
    other.fund == fund &&
    other.unallocated == unallocated;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (a == null ? 0 : a!.hashCode) +
    (hk == null ? 0 : hk!.hashCode) +
    (us == null ? 0 : us!.hashCode) +
    (fund == null ? 0 : fund!.hashCode) +
    (unallocated == null ? 0 : unallocated!.hashCode);

  @override
  String toString() => 'AnalysisMarketBreakdownItemMarkets[a=$a, hk=$hk, us=$us, fund=$fund, unallocated=$unallocated]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.a != null) {
      json[r'a'] = this.a;
    } else {
      json[r'a'] = null;
    }
    if (this.hk != null) {
      json[r'hk'] = this.hk;
    } else {
      json[r'hk'] = null;
    }
    if (this.us != null) {
      json[r'us'] = this.us;
    } else {
      json[r'us'] = null;
    }
    if (this.fund != null) {
      json[r'fund'] = this.fund;
    } else {
      json[r'fund'] = null;
    }
    if (this.unallocated != null) {
      json[r'unallocated'] = this.unallocated;
    } else {
      json[r'unallocated'] = null;
    }
    return json;
  }

  /// Returns a new [AnalysisMarketBreakdownItemMarkets] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AnalysisMarketBreakdownItemMarkets? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AnalysisMarketBreakdownItemMarkets[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AnalysisMarketBreakdownItemMarkets[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AnalysisMarketBreakdownItemMarkets(
        a: json[r'a'] == null
            ? null
            : num.parse('${json[r'a']}'),
        hk: json[r'hk'] == null
            ? null
            : num.parse('${json[r'hk']}'),
        us: json[r'us'] == null
            ? null
            : num.parse('${json[r'us']}'),
        fund: json[r'fund'] == null
            ? null
            : num.parse('${json[r'fund']}'),
        unallocated: json[r'unallocated'] == null
            ? null
            : num.parse('${json[r'unallocated']}'),
      );
    }
    return null;
  }

  static List<AnalysisMarketBreakdownItemMarkets> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AnalysisMarketBreakdownItemMarkets>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AnalysisMarketBreakdownItemMarkets.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AnalysisMarketBreakdownItemMarkets> mapFromJson(dynamic json) {
    final map = <String, AnalysisMarketBreakdownItemMarkets>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AnalysisMarketBreakdownItemMarkets.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AnalysisMarketBreakdownItemMarkets-objects as value to a dart map
  static Map<String, List<AnalysisMarketBreakdownItemMarkets>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AnalysisMarketBreakdownItemMarkets>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AnalysisMarketBreakdownItemMarkets.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

