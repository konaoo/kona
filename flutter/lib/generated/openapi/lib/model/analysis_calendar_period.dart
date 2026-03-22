//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AnalysisCalendarPeriod {
  /// Returns a new [AnalysisCalendarPeriod] instance.
  AnalysisCalendarPeriod({
    this.timeType,
    this.year,
    this.month,
  });

  AnalysisCalendarPeriodTimeTypeEnum? timeType;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? year;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? month;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AnalysisCalendarPeriod &&
    other.timeType == timeType &&
    other.year == year &&
    other.month == month;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (timeType == null ? 0 : timeType!.hashCode) +
    (year == null ? 0 : year!.hashCode) +
    (month == null ? 0 : month!.hashCode);

  @override
  String toString() => 'AnalysisCalendarPeriod[timeType=$timeType, year=$year, month=$month]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.timeType != null) {
      json[r'time_type'] = this.timeType;
    } else {
      json[r'time_type'] = null;
    }
    if (this.year != null) {
      json[r'year'] = this.year;
    } else {
      json[r'year'] = null;
    }
    if (this.month != null) {
      json[r'month'] = this.month;
    } else {
      json[r'month'] = null;
    }
    return json;
  }

  /// Returns a new [AnalysisCalendarPeriod] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AnalysisCalendarPeriod? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AnalysisCalendarPeriod[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AnalysisCalendarPeriod[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AnalysisCalendarPeriod(
        timeType: AnalysisCalendarPeriodTimeTypeEnum.fromJson(json[r'time_type']),
        year: mapValueOfType<int>(json, r'year'),
        month: mapValueOfType<int>(json, r'month'),
      );
    }
    return null;
  }

  static List<AnalysisCalendarPeriod> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AnalysisCalendarPeriod>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AnalysisCalendarPeriod.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AnalysisCalendarPeriod> mapFromJson(dynamic json) {
    final map = <String, AnalysisCalendarPeriod>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AnalysisCalendarPeriod.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AnalysisCalendarPeriod-objects as value to a dart map
  static Map<String, List<AnalysisCalendarPeriod>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AnalysisCalendarPeriod>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AnalysisCalendarPeriod.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}


class AnalysisCalendarPeriodTimeTypeEnum {
  /// Instantiate a new enum with the provided [value].
  const AnalysisCalendarPeriodTimeTypeEnum._(this.value);

  /// The underlying value of this enum member.
  final String value;

  @override
  String toString() => value;

  String toJson() => value;

  static const day = AnalysisCalendarPeriodTimeTypeEnum._(r'day');
  static const month = AnalysisCalendarPeriodTimeTypeEnum._(r'month');
  static const year = AnalysisCalendarPeriodTimeTypeEnum._(r'year');

  /// List of all possible values in this [enum][AnalysisCalendarPeriodTimeTypeEnum].
  static const values = <AnalysisCalendarPeriodTimeTypeEnum>[
    day,
    month,
    year,
  ];

  static AnalysisCalendarPeriodTimeTypeEnum? fromJson(dynamic value) => AnalysisCalendarPeriodTimeTypeEnumTypeTransformer().decode(value);

  static List<AnalysisCalendarPeriodTimeTypeEnum> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AnalysisCalendarPeriodTimeTypeEnum>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AnalysisCalendarPeriodTimeTypeEnum.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }
}

/// Transformation class that can [encode] an instance of [AnalysisCalendarPeriodTimeTypeEnum] to String,
/// and [decode] dynamic data back to [AnalysisCalendarPeriodTimeTypeEnum].
class AnalysisCalendarPeriodTimeTypeEnumTypeTransformer {
  factory AnalysisCalendarPeriodTimeTypeEnumTypeTransformer() => _instance ??= const AnalysisCalendarPeriodTimeTypeEnumTypeTransformer._();

  const AnalysisCalendarPeriodTimeTypeEnumTypeTransformer._();

  String encode(AnalysisCalendarPeriodTimeTypeEnum data) => data.value;

  /// Decodes a [dynamic value][data] to a AnalysisCalendarPeriodTimeTypeEnum.
  ///
  /// If [allowNull] is true and the [dynamic value][data] cannot be decoded successfully,
  /// then null is returned. However, if [allowNull] is false and the [dynamic value][data]
  /// cannot be decoded successfully, then an [UnimplementedError] is thrown.
  ///
  /// The [allowNull] is very handy when an API changes and a new enum value is added or removed,
  /// and users are still using an old app with the old code.
  AnalysisCalendarPeriodTimeTypeEnum? decode(dynamic data, {bool allowNull = true}) {
    if (data != null) {
      switch (data) {
        case r'day': return AnalysisCalendarPeriodTimeTypeEnum.day;
        case r'month': return AnalysisCalendarPeriodTimeTypeEnum.month;
        case r'year': return AnalysisCalendarPeriodTimeTypeEnum.year;
        default:
          if (!allowNull) {
            throw ArgumentError('Unknown enum value to decode: $data');
          }
      }
    }
    return null;
  }

  /// Singleton [AnalysisCalendarPeriodTimeTypeEnumTypeTransformer] instance.
  static AnalysisCalendarPeriodTimeTypeEnumTypeTransformer? _instance;
}


