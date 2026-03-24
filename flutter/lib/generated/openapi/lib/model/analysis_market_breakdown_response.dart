//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AnalysisMarketBreakdownResponse {
  /// Returns a new [AnalysisMarketBreakdownResponse] instance.
  AnalysisMarketBreakdownResponse({
    this.timeType,
    this.year,
    this.month,
    this.items = const [],
    this.error,
    this.code,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? timeType;

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

  List<AnalysisMarketBreakdownItem> items;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? error;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? code;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AnalysisMarketBreakdownResponse &&
    other.timeType == timeType &&
    other.year == year &&
    other.month == month &&
    _deepEquality.equals(other.items, items) &&
    other.error == error &&
    other.code == code;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (timeType == null ? 0 : timeType!.hashCode) +
    (year == null ? 0 : year!.hashCode) +
    (month == null ? 0 : month!.hashCode) +
    (items.hashCode) +
    (error == null ? 0 : error!.hashCode) +
    (code == null ? 0 : code!.hashCode);

  @override
  String toString() => 'AnalysisMarketBreakdownResponse[timeType=$timeType, year=$year, month=$month, items=$items, error=$error, code=$code]';

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
      json[r'items'] = this.items;
    if (this.error != null) {
      json[r'error'] = this.error;
    } else {
      json[r'error'] = null;
    }
    if (this.code != null) {
      json[r'code'] = this.code;
    } else {
      json[r'code'] = null;
    }
    return json;
  }

  /// Returns a new [AnalysisMarketBreakdownResponse] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AnalysisMarketBreakdownResponse? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AnalysisMarketBreakdownResponse[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AnalysisMarketBreakdownResponse[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AnalysisMarketBreakdownResponse(
        timeType: mapValueOfType<String>(json, r'time_type'),
        year: mapValueOfType<int>(json, r'year'),
        month: mapValueOfType<int>(json, r'month'),
        items: AnalysisMarketBreakdownItem.listFromJson(json[r'items']),
        error: mapValueOfType<String>(json, r'error'),
        code: mapValueOfType<String>(json, r'code'),
      );
    }
    return null;
  }

  static List<AnalysisMarketBreakdownResponse> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AnalysisMarketBreakdownResponse>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AnalysisMarketBreakdownResponse.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AnalysisMarketBreakdownResponse> mapFromJson(dynamic json) {
    final map = <String, AnalysisMarketBreakdownResponse>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AnalysisMarketBreakdownResponse.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AnalysisMarketBreakdownResponse-objects as value to a dart map
  static Map<String, List<AnalysisMarketBreakdownResponse>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AnalysisMarketBreakdownResponse>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AnalysisMarketBreakdownResponse.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

