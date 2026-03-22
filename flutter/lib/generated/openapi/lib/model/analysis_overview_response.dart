//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AnalysisOverviewResponse {
  /// Returns a new [AnalysisOverviewResponse] instance.
  AnalysisOverviewResponse({
    this.day,
    this.month,
    this.year,
    this.all,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  PnlOverviewItem? day;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  PnlOverviewItem? month;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  PnlOverviewItem? year;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  PnlOverviewItem? all;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AnalysisOverviewResponse &&
    other.day == day &&
    other.month == month &&
    other.year == year &&
    other.all == all;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (day == null ? 0 : day!.hashCode) +
    (month == null ? 0 : month!.hashCode) +
    (year == null ? 0 : year!.hashCode) +
    (all == null ? 0 : all!.hashCode);

  @override
  String toString() => 'AnalysisOverviewResponse[day=$day, month=$month, year=$year, all=$all]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.day != null) {
      json[r'day'] = this.day;
    } else {
      json[r'day'] = null;
    }
    if (this.month != null) {
      json[r'month'] = this.month;
    } else {
      json[r'month'] = null;
    }
    if (this.year != null) {
      json[r'year'] = this.year;
    } else {
      json[r'year'] = null;
    }
    if (this.all != null) {
      json[r'all'] = this.all;
    } else {
      json[r'all'] = null;
    }
    return json;
  }

  /// Returns a new [AnalysisOverviewResponse] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AnalysisOverviewResponse? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AnalysisOverviewResponse[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AnalysisOverviewResponse[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AnalysisOverviewResponse(
        day: PnlOverviewItem.fromJson(json[r'day']),
        month: PnlOverviewItem.fromJson(json[r'month']),
        year: PnlOverviewItem.fromJson(json[r'year']),
        all: PnlOverviewItem.fromJson(json[r'all']),
      );
    }
    return null;
  }

  static List<AnalysisOverviewResponse> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AnalysisOverviewResponse>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AnalysisOverviewResponse.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AnalysisOverviewResponse> mapFromJson(dynamic json) {
    final map = <String, AnalysisOverviewResponse>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AnalysisOverviewResponse.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AnalysisOverviewResponse-objects as value to a dart map
  static Map<String, List<AnalysisOverviewResponse>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AnalysisOverviewResponse>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AnalysisOverviewResponse.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

