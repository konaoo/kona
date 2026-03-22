//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class MarketStatusResponse {
  /// Returns a new [MarketStatusResponse] instance.
  MarketStatusResponse({
    this.serverTimeUtc,
    this.markets = const {},
    this.allClosed,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? serverTimeUtc;

  Map<String, MarketStatusItem> markets;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  bool? allClosed;

  @override
  bool operator ==(Object other) => identical(this, other) || other is MarketStatusResponse &&
    other.serverTimeUtc == serverTimeUtc &&
    _deepEquality.equals(other.markets, markets) &&
    other.allClosed == allClosed;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (serverTimeUtc == null ? 0 : serverTimeUtc!.hashCode) +
    (markets.hashCode) +
    (allClosed == null ? 0 : allClosed!.hashCode);

  @override
  String toString() => 'MarketStatusResponse[serverTimeUtc=$serverTimeUtc, markets=$markets, allClosed=$allClosed]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.serverTimeUtc != null) {
      json[r'server_time_utc'] = this.serverTimeUtc;
    } else {
      json[r'server_time_utc'] = null;
    }
      json[r'markets'] = this.markets;
    if (this.allClosed != null) {
      json[r'all_closed'] = this.allClosed;
    } else {
      json[r'all_closed'] = null;
    }
    return json;
  }

  /// Returns a new [MarketStatusResponse] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static MarketStatusResponse? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "MarketStatusResponse[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "MarketStatusResponse[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return MarketStatusResponse(
        serverTimeUtc: mapValueOfType<String>(json, r'server_time_utc'),
        markets: MarketStatusItem.mapFromJson(json[r'markets']),
        allClosed: mapValueOfType<bool>(json, r'all_closed'),
      );
    }
    return null;
  }

  static List<MarketStatusResponse> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <MarketStatusResponse>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = MarketStatusResponse.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, MarketStatusResponse> mapFromJson(dynamic json) {
    final map = <String, MarketStatusResponse>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = MarketStatusResponse.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of MarketStatusResponse-objects as value to a dart map
  static Map<String, List<MarketStatusResponse>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<MarketStatusResponse>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = MarketStatusResponse.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

