//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class MarketStatusItem {
  /// Returns a new [MarketStatusItem] instance.
  MarketStatusItem({
    this.open,
    this.tradingDay,
    this.reason,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  bool? open;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  bool? tradingDay;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? reason;

  @override
  bool operator ==(Object other) => identical(this, other) || other is MarketStatusItem &&
    other.open == open &&
    other.tradingDay == tradingDay &&
    other.reason == reason;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (open == null ? 0 : open!.hashCode) +
    (tradingDay == null ? 0 : tradingDay!.hashCode) +
    (reason == null ? 0 : reason!.hashCode);

  @override
  String toString() => 'MarketStatusItem[open=$open, tradingDay=$tradingDay, reason=$reason]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.open != null) {
      json[r'open'] = this.open;
    } else {
      json[r'open'] = null;
    }
    if (this.tradingDay != null) {
      json[r'trading_day'] = this.tradingDay;
    } else {
      json[r'trading_day'] = null;
    }
    if (this.reason != null) {
      json[r'reason'] = this.reason;
    } else {
      json[r'reason'] = null;
    }
    return json;
  }

  /// Returns a new [MarketStatusItem] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static MarketStatusItem? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "MarketStatusItem[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "MarketStatusItem[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return MarketStatusItem(
        open: mapValueOfType<bool>(json, r'open'),
        tradingDay: mapValueOfType<bool>(json, r'trading_day'),
        reason: mapValueOfType<String>(json, r'reason'),
      );
    }
    return null;
  }

  static List<MarketStatusItem> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <MarketStatusItem>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = MarketStatusItem.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, MarketStatusItem> mapFromJson(dynamic json) {
    final map = <String, MarketStatusItem>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = MarketStatusItem.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of MarketStatusItem-objects as value to a dart map
  static Map<String, List<MarketStatusItem>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<MarketStatusItem>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = MarketStatusItem.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

