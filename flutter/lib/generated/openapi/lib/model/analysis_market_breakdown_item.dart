//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AnalysisMarketBreakdownItem {
  /// Returns a new [AnalysisMarketBreakdownItem] instance.
  AnalysisMarketBreakdownItem({
    this.date,
    this.markets,
    this.totalPnl,
    this.source_,
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
  AnalysisMarketBreakdownItemMarkets? markets;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? totalPnl;

  AnalysisMarketBreakdownItemSource_Enum? source_;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AnalysisMarketBreakdownItem &&
    other.date == date &&
    other.markets == markets &&
    other.totalPnl == totalPnl &&
    other.source_ == source_;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (date == null ? 0 : date!.hashCode) +
    (markets == null ? 0 : markets!.hashCode) +
    (totalPnl == null ? 0 : totalPnl!.hashCode) +
    (source_ == null ? 0 : source_!.hashCode);

  @override
  String toString() => 'AnalysisMarketBreakdownItem[date=$date, markets=$markets, totalPnl=$totalPnl, source_=$source_]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.date != null) {
      json[r'date'] = this.date;
    } else {
      json[r'date'] = null;
    }
    if (this.markets != null) {
      json[r'markets'] = this.markets;
    } else {
      json[r'markets'] = null;
    }
    if (this.totalPnl != null) {
      json[r'total_pnl'] = this.totalPnl;
    } else {
      json[r'total_pnl'] = null;
    }
    if (this.source_ != null) {
      json[r'source'] = this.source_;
    } else {
      json[r'source'] = null;
    }
    return json;
  }

  /// Returns a new [AnalysisMarketBreakdownItem] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AnalysisMarketBreakdownItem? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AnalysisMarketBreakdownItem[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AnalysisMarketBreakdownItem[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AnalysisMarketBreakdownItem(
        date: mapValueOfType<String>(json, r'date'),
        markets: AnalysisMarketBreakdownItemMarkets.fromJson(json[r'markets']),
        totalPnl: num.parse('${json[r'total_pnl']}'),
        source_: AnalysisMarketBreakdownItemSource_Enum.fromJson(json[r'source']),
      );
    }
    return null;
  }

  static List<AnalysisMarketBreakdownItem> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AnalysisMarketBreakdownItem>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AnalysisMarketBreakdownItem.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AnalysisMarketBreakdownItem> mapFromJson(dynamic json) {
    final map = <String, AnalysisMarketBreakdownItem>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AnalysisMarketBreakdownItem.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AnalysisMarketBreakdownItem-objects as value to a dart map
  static Map<String, List<AnalysisMarketBreakdownItem>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AnalysisMarketBreakdownItem>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AnalysisMarketBreakdownItem.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}


class AnalysisMarketBreakdownItemSource_Enum {
  /// Instantiate a new enum with the provided [value].
  const AnalysisMarketBreakdownItemSource_Enum._(this.value);

  /// The underlying value of this enum member.
  final String value;

  @override
  String toString() => value;

  String toJson() => value;

  static const exact = AnalysisMarketBreakdownItemSource_Enum._(r'exact');
  static const estimated = AnalysisMarketBreakdownItemSource_Enum._(r'estimated');
  static const missing = AnalysisMarketBreakdownItemSource_Enum._(r'missing');

  /// List of all possible values in this [enum][AnalysisMarketBreakdownItemSource_Enum].
  static const values = <AnalysisMarketBreakdownItemSource_Enum>[
    exact,
    estimated,
    missing,
  ];

  static AnalysisMarketBreakdownItemSource_Enum? fromJson(dynamic value) => AnalysisMarketBreakdownItemSource_EnumTypeTransformer().decode(value);

  static List<AnalysisMarketBreakdownItemSource_Enum> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AnalysisMarketBreakdownItemSource_Enum>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AnalysisMarketBreakdownItemSource_Enum.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }
}

/// Transformation class that can [encode] an instance of [AnalysisMarketBreakdownItemSource_Enum] to String,
/// and [decode] dynamic data back to [AnalysisMarketBreakdownItemSource_Enum].
class AnalysisMarketBreakdownItemSource_EnumTypeTransformer {
  factory AnalysisMarketBreakdownItemSource_EnumTypeTransformer() => _instance ??= const AnalysisMarketBreakdownItemSource_EnumTypeTransformer._();

  const AnalysisMarketBreakdownItemSource_EnumTypeTransformer._();

  String encode(AnalysisMarketBreakdownItemSource_Enum data) => data.value;

  /// Decodes a [dynamic value][data] to a AnalysisMarketBreakdownItemSource_Enum.
  ///
  /// If [allowNull] is true and the [dynamic value][data] cannot be decoded successfully,
  /// then null is returned. However, if [allowNull] is false and the [dynamic value][data]
  /// cannot be decoded successfully, then an [UnimplementedError] is thrown.
  ///
  /// The [allowNull] is very handy when an API changes and a new enum value is added or removed,
  /// and users are still using an old app with the old code.
  AnalysisMarketBreakdownItemSource_Enum? decode(dynamic data, {bool allowNull = true}) {
    if (data != null) {
      switch (data) {
        case r'exact': return AnalysisMarketBreakdownItemSource_Enum.exact;
        case r'estimated': return AnalysisMarketBreakdownItemSource_Enum.estimated;
        case r'missing': return AnalysisMarketBreakdownItemSource_Enum.missing;
        default:
          if (!allowNull) {
            throw ArgumentError('Unknown enum value to decode: $data');
          }
      }
    }
    return null;
  }

  /// Singleton [AnalysisMarketBreakdownItemSource_EnumTypeTransformer] instance.
  static AnalysisMarketBreakdownItemSource_EnumTypeTransformer? _instance;
}


