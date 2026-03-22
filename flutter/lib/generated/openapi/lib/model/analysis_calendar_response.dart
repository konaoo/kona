//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AnalysisCalendarResponse {
  /// Returns a new [AnalysisCalendarResponse] instance.
  AnalysisCalendarResponse({
    this.items = const [],
    this.totalPnl,
    this.totalRate,
    this.title,
    this.period,
    this.selectable,
  });

  List<AnalysisCalendarItem> items;

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
  num? totalRate;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? title;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  AnalysisCalendarPeriod? period;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  AnalysisCalendarSelectable? selectable;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AnalysisCalendarResponse &&
    _deepEquality.equals(other.items, items) &&
    other.totalPnl == totalPnl &&
    other.totalRate == totalRate &&
    other.title == title &&
    other.period == period &&
    other.selectable == selectable;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (items.hashCode) +
    (totalPnl == null ? 0 : totalPnl!.hashCode) +
    (totalRate == null ? 0 : totalRate!.hashCode) +
    (title == null ? 0 : title!.hashCode) +
    (period == null ? 0 : period!.hashCode) +
    (selectable == null ? 0 : selectable!.hashCode);

  @override
  String toString() => 'AnalysisCalendarResponse[items=$items, totalPnl=$totalPnl, totalRate=$totalRate, title=$title, period=$period, selectable=$selectable]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
      json[r'items'] = this.items;
    if (this.totalPnl != null) {
      json[r'total_pnl'] = this.totalPnl;
    } else {
      json[r'total_pnl'] = null;
    }
    if (this.totalRate != null) {
      json[r'total_rate'] = this.totalRate;
    } else {
      json[r'total_rate'] = null;
    }
    if (this.title != null) {
      json[r'title'] = this.title;
    } else {
      json[r'title'] = null;
    }
    if (this.period != null) {
      json[r'period'] = this.period;
    } else {
      json[r'period'] = null;
    }
    if (this.selectable != null) {
      json[r'selectable'] = this.selectable;
    } else {
      json[r'selectable'] = null;
    }
    return json;
  }

  /// Returns a new [AnalysisCalendarResponse] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AnalysisCalendarResponse? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AnalysisCalendarResponse[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AnalysisCalendarResponse[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AnalysisCalendarResponse(
        items: AnalysisCalendarItem.listFromJson(json[r'items']),
        totalPnl: num.parse('${json[r'total_pnl']}'),
        totalRate: num.parse('${json[r'total_rate']}'),
        title: mapValueOfType<String>(json, r'title'),
        period: AnalysisCalendarPeriod.fromJson(json[r'period']),
        selectable: AnalysisCalendarSelectable.fromJson(json[r'selectable']),
      );
    }
    return null;
  }

  static List<AnalysisCalendarResponse> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AnalysisCalendarResponse>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AnalysisCalendarResponse.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AnalysisCalendarResponse> mapFromJson(dynamic json) {
    final map = <String, AnalysisCalendarResponse>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AnalysisCalendarResponse.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AnalysisCalendarResponse-objects as value to a dart map
  static Map<String, List<AnalysisCalendarResponse>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AnalysisCalendarResponse>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AnalysisCalendarResponse.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

