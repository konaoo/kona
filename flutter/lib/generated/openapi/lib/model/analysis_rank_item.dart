//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AnalysisRankItem {
  /// Returns a new [AnalysisRankItem] instance.
  AnalysisRankItem({
    this.code,
    this.name,
    this.pnl,
    this.pnlRate,
    this.market,
    this.curr,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? code;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? name;

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
  String? market;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? curr;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AnalysisRankItem &&
    other.code == code &&
    other.name == name &&
    other.pnl == pnl &&
    other.pnlRate == pnlRate &&
    other.market == market &&
    other.curr == curr;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (code == null ? 0 : code!.hashCode) +
    (name == null ? 0 : name!.hashCode) +
    (pnl == null ? 0 : pnl!.hashCode) +
    (pnlRate == null ? 0 : pnlRate!.hashCode) +
    (market == null ? 0 : market!.hashCode) +
    (curr == null ? 0 : curr!.hashCode);

  @override
  String toString() => 'AnalysisRankItem[code=$code, name=$name, pnl=$pnl, pnlRate=$pnlRate, market=$market, curr=$curr]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.code != null) {
      json[r'code'] = this.code;
    } else {
      json[r'code'] = null;
    }
    if (this.name != null) {
      json[r'name'] = this.name;
    } else {
      json[r'name'] = null;
    }
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
    if (this.market != null) {
      json[r'market'] = this.market;
    } else {
      json[r'market'] = null;
    }
    if (this.curr != null) {
      json[r'curr'] = this.curr;
    } else {
      json[r'curr'] = null;
    }
    return json;
  }

  /// Returns a new [AnalysisRankItem] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AnalysisRankItem? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AnalysisRankItem[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AnalysisRankItem[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AnalysisRankItem(
        code: mapValueOfType<String>(json, r'code'),
        name: mapValueOfType<String>(json, r'name'),
        pnl: num.parse('${json[r'pnl']}'),
        pnlRate: num.parse('${json[r'pnl_rate']}'),
        market: mapValueOfType<String>(json, r'market'),
        curr: mapValueOfType<String>(json, r'curr'),
      );
    }
    return null;
  }

  static List<AnalysisRankItem> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AnalysisRankItem>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AnalysisRankItem.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AnalysisRankItem> mapFromJson(dynamic json) {
    final map = <String, AnalysisRankItem>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AnalysisRankItem.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AnalysisRankItem-objects as value to a dart map
  static Map<String, List<AnalysisRankItem>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AnalysisRankItem>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AnalysisRankItem.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

