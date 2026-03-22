//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class PnlOverviewItem {
  /// Returns a new [PnlOverviewItem] instance.
  PnlOverviewItem({
    this.pnl,
    this.pnlRate,
    this.baseValue,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? pnl;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? pnlRate;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? baseValue;

  @override
  bool operator ==(Object other) => identical(this, other) || other is PnlOverviewItem &&
    other.pnl == pnl &&
    other.pnlRate == pnlRate &&
    other.baseValue == baseValue;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (pnl == null ? 0 : pnl!.hashCode) +
    (pnlRate == null ? 0 : pnlRate!.hashCode) +
    (baseValue == null ? 0 : baseValue!.hashCode);

  @override
  String toString() => 'PnlOverviewItem[pnl=$pnl, pnlRate=$pnlRate, baseValue=$baseValue]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.pnl != null) {
      json[r'pnl'] = this.pnl;
    } else {
      json[r'pnl'] = null;
    }
    if (this.pnlRate != null) {
      json[r'pnl_rate'] = this.pnlRate;
    } else {
      json[r'pnl_rate'] = null;
    }
    if (this.baseValue != null) {
      json[r'base_value'] = this.baseValue;
    } else {
      json[r'base_value'] = null;
    }
    return json;
  }

  /// Returns a new [PnlOverviewItem] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static PnlOverviewItem? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "PnlOverviewItem[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "PnlOverviewItem[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return PnlOverviewItem(
        pnl: num.parse('${json[r'pnl']}'),
        pnlRate: num.parse('${json[r'pnl_rate']}'),
        baseValue: num.parse('${json[r'base_value']}'),
      );
    }
    return null;
  }

  static List<PnlOverviewItem> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <PnlOverviewItem>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = PnlOverviewItem.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, PnlOverviewItem> mapFromJson(dynamic json) {
    final map = <String, PnlOverviewItem>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = PnlOverviewItem.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of PnlOverviewItem-objects as value to a dart map
  static Map<String, List<PnlOverviewItem>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<PnlOverviewItem>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = PnlOverviewItem.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

