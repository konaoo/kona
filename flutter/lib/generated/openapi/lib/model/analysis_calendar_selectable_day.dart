//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AnalysisCalendarSelectableDay {
  /// Returns a new [AnalysisCalendarSelectableDay] instance.
  AnalysisCalendarSelectableDay({
    this.years = const [],
    this.monthsByYear = const {},
  });

  List<int> years;

  /// 按年份分组的月份列表，键是年份字符串，值是月份数组
  Map<String, Object> monthsByYear;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AnalysisCalendarSelectableDay &&
    _deepEquality.equals(other.years, years) &&
    _deepEquality.equals(other.monthsByYear, monthsByYear);

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (years.hashCode) +
    (monthsByYear.hashCode);

  @override
  String toString() => 'AnalysisCalendarSelectableDay[years=$years, monthsByYear=$monthsByYear]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
      json[r'years'] = this.years;
      json[r'months_by_year'] = this.monthsByYear;
    return json;
  }

  /// Returns a new [AnalysisCalendarSelectableDay] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AnalysisCalendarSelectableDay? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AnalysisCalendarSelectableDay[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AnalysisCalendarSelectableDay[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AnalysisCalendarSelectableDay(
        years: json[r'years'] is Iterable
            ? (json[r'years'] as Iterable).cast<int>().toList(growable: false)
            : const [],
        monthsByYear: mapCastOfType<String, Object>(json, r'months_by_year') ?? const {},
      );
    }
    return null;
  }

  static List<AnalysisCalendarSelectableDay> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AnalysisCalendarSelectableDay>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AnalysisCalendarSelectableDay.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AnalysisCalendarSelectableDay> mapFromJson(dynamic json) {
    final map = <String, AnalysisCalendarSelectableDay>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AnalysisCalendarSelectableDay.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AnalysisCalendarSelectableDay-objects as value to a dart map
  static Map<String, List<AnalysisCalendarSelectableDay>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AnalysisCalendarSelectableDay>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AnalysisCalendarSelectableDay.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

