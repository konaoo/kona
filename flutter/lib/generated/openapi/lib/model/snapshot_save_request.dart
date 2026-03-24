//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class SnapshotSaveRequest {
  /// Returns a new [SnapshotSaveRequest] instance.
  SnapshotSaveRequest({
    this.date,
    this.totalAsset,
    this.totalInvest,
    this.totalCash,
    this.totalOther,
    this.totalLiability,
    this.totalPnl,
    this.dayPnl,
    this.dayPnlByMarket = const {},
    this.marketBreakdownSource,
    this.marketBreakdownConfidence,
    this.marketBreakdownMeta = const {},
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? date;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? totalAsset;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? totalInvest;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? totalCash;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? totalOther;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? totalLiability;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? totalPnl;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? dayPnl;

  Map<String, num> dayPnlByMarket;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? marketBreakdownSource;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? marketBreakdownConfidence;

  Map<String, Object> marketBreakdownMeta;

  @override
  bool operator ==(Object other) => identical(this, other) || other is SnapshotSaveRequest &&
    other.date == date &&
    other.totalAsset == totalAsset &&
    other.totalInvest == totalInvest &&
    other.totalCash == totalCash &&
    other.totalOther == totalOther &&
    other.totalLiability == totalLiability &&
    other.totalPnl == totalPnl &&
    other.dayPnl == dayPnl &&
    _deepEquality.equals(other.dayPnlByMarket, dayPnlByMarket) &&
    other.marketBreakdownSource == marketBreakdownSource &&
    other.marketBreakdownConfidence == marketBreakdownConfidence &&
    _deepEquality.equals(other.marketBreakdownMeta, marketBreakdownMeta);

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (date == null ? 0 : date!.hashCode) +
    (totalAsset == null ? 0 : totalAsset!.hashCode) +
    (totalInvest == null ? 0 : totalInvest!.hashCode) +
    (totalCash == null ? 0 : totalCash!.hashCode) +
    (totalOther == null ? 0 : totalOther!.hashCode) +
    (totalLiability == null ? 0 : totalLiability!.hashCode) +
    (totalPnl == null ? 0 : totalPnl!.hashCode) +
    (dayPnl == null ? 0 : dayPnl!.hashCode) +
    (dayPnlByMarket.hashCode) +
    (marketBreakdownSource == null ? 0 : marketBreakdownSource!.hashCode) +
    (marketBreakdownConfidence == null ? 0 : marketBreakdownConfidence!.hashCode) +
    (marketBreakdownMeta.hashCode);

  @override
  String toString() => 'SnapshotSaveRequest[date=$date, totalAsset=$totalAsset, totalInvest=$totalInvest, totalCash=$totalCash, totalOther=$totalOther, totalLiability=$totalLiability, totalPnl=$totalPnl, dayPnl=$dayPnl, dayPnlByMarket=$dayPnlByMarket, marketBreakdownSource=$marketBreakdownSource, marketBreakdownConfidence=$marketBreakdownConfidence, marketBreakdownMeta=$marketBreakdownMeta]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.date != null) {
      json[r'date'] = this.date;
    } else {
      json[r'date'] = null;
    }
    if (this.totalAsset != null) {
      json[r'total_asset'] = this.totalAsset;
    } else {
      json[r'total_asset'] = null;
    }
    if (this.totalInvest != null) {
      json[r'total_invest'] = this.totalInvest;
    } else {
      json[r'total_invest'] = null;
    }
    if (this.totalCash != null) {
      json[r'total_cash'] = this.totalCash;
    } else {
      json[r'total_cash'] = null;
    }
    if (this.totalOther != null) {
      json[r'total_other'] = this.totalOther;
    } else {
      json[r'total_other'] = null;
    }
    if (this.totalLiability != null) {
      json[r'total_liability'] = this.totalLiability;
    } else {
      json[r'total_liability'] = null;
    }
    if (this.totalPnl != null) {
      json[r'total_pnl'] = this.totalPnl;
    } else {
      json[r'total_pnl'] = null;
    }
    if (this.dayPnl != null) {
      json[r'day_pnl'] = this.dayPnl;
    } else {
      json[r'day_pnl'] = null;
    }
      json[r'day_pnl_by_market'] = this.dayPnlByMarket;
    if (this.marketBreakdownSource != null) {
      json[r'market_breakdown_source'] = this.marketBreakdownSource;
    } else {
      json[r'market_breakdown_source'] = null;
    }
    if (this.marketBreakdownConfidence != null) {
      json[r'market_breakdown_confidence'] = this.marketBreakdownConfidence;
    } else {
      json[r'market_breakdown_confidence'] = null;
    }
      json[r'market_breakdown_meta'] = this.marketBreakdownMeta;
    return json;
  }

  /// Returns a new [SnapshotSaveRequest] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static SnapshotSaveRequest? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "SnapshotSaveRequest[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "SnapshotSaveRequest[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return SnapshotSaveRequest(
        date: mapValueOfType<String>(json, r'date'),
        totalAsset: num.parse('${json[r'total_asset']}'),
        totalInvest: num.parse('${json[r'total_invest']}'),
        totalCash: num.parse('${json[r'total_cash']}'),
        totalOther: num.parse('${json[r'total_other']}'),
        totalLiability: num.parse('${json[r'total_liability']}'),
        totalPnl: num.parse('${json[r'total_pnl']}'),
        dayPnl: num.parse('${json[r'day_pnl']}'),
        dayPnlByMarket: mapCastOfType<String, num>(json, r'day_pnl_by_market') ?? const {},
        marketBreakdownSource: mapValueOfType<String>(json, r'market_breakdown_source'),
        marketBreakdownConfidence: num.parse('${json[r'market_breakdown_confidence']}'),
        marketBreakdownMeta: mapCastOfType<String, Object>(json, r'market_breakdown_meta') ?? const {},
      );
    }
    return null;
  }

  static List<SnapshotSaveRequest> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <SnapshotSaveRequest>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = SnapshotSaveRequest.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, SnapshotSaveRequest> mapFromJson(dynamic json) {
    final map = <String, SnapshotSaveRequest>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = SnapshotSaveRequest.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of SnapshotSaveRequest-objects as value to a dart map
  static Map<String, List<SnapshotSaveRequest>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<SnapshotSaveRequest>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = SnapshotSaveRequest.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

