//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AdminPriceAlertsResponse {
  /// Returns a new [AdminPriceAlertsResponse] instance.
  AdminPriceAlertsResponse({
    this.testedAtUtc,
    this.totalAssets,
    this.alertCount,
    this.summary,
    this.items = const [],
    this.reportDate,
    this.history = const [],
    this.cache,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? testedAtUtc;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? totalAssets;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? alertCount;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  AdminPriceAlertSummary? summary;

  List<AdminPriceAlertItem> items;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? reportDate;

  List<AdminPriceAlertReportSummary> history;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  AdminPriceAlertsResponseCache? cache;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AdminPriceAlertsResponse &&
    other.testedAtUtc == testedAtUtc &&
    other.totalAssets == totalAssets &&
    other.alertCount == alertCount &&
    other.summary == summary &&
    _deepEquality.equals(other.items, items) &&
    other.reportDate == reportDate &&
    _deepEquality.equals(other.history, history) &&
    other.cache == cache;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (testedAtUtc == null ? 0 : testedAtUtc!.hashCode) +
    (totalAssets == null ? 0 : totalAssets!.hashCode) +
    (alertCount == null ? 0 : alertCount!.hashCode) +
    (summary == null ? 0 : summary!.hashCode) +
    (items.hashCode) +
    (reportDate == null ? 0 : reportDate!.hashCode) +
    (history.hashCode) +
    (cache == null ? 0 : cache!.hashCode);

  @override
  String toString() => 'AdminPriceAlertsResponse[testedAtUtc=$testedAtUtc, totalAssets=$totalAssets, alertCount=$alertCount, summary=$summary, items=$items, reportDate=$reportDate, history=$history, cache=$cache]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.testedAtUtc != null) {
      json[r'tested_at_utc'] = this.testedAtUtc;
    } else {
      json[r'tested_at_utc'] = null;
    }
    if (this.totalAssets != null) {
      json[r'total_assets'] = this.totalAssets;
    } else {
      json[r'total_assets'] = null;
    }
    if (this.alertCount != null) {
      json[r'alert_count'] = this.alertCount;
    } else {
      json[r'alert_count'] = null;
    }
    if (this.summary != null) {
      json[r'summary'] = this.summary;
    } else {
      json[r'summary'] = null;
    }
      json[r'items'] = this.items;
    if (this.reportDate != null) {
      json[r'report_date'] = this.reportDate;
    } else {
      json[r'report_date'] = null;
    }
      json[r'history'] = this.history;
    if (this.cache != null) {
      json[r'cache'] = this.cache;
    } else {
      json[r'cache'] = null;
    }
    return json;
  }

  /// Returns a new [AdminPriceAlertsResponse] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AdminPriceAlertsResponse? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AdminPriceAlertsResponse[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AdminPriceAlertsResponse[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AdminPriceAlertsResponse(
        testedAtUtc: mapValueOfType<String>(json, r'tested_at_utc'),
        totalAssets: mapValueOfType<int>(json, r'total_assets'),
        alertCount: mapValueOfType<int>(json, r'alert_count'),
        summary: AdminPriceAlertSummary.fromJson(json[r'summary']),
        items: AdminPriceAlertItem.listFromJson(json[r'items']),
        reportDate: mapValueOfType<String>(json, r'report_date'),
        history: AdminPriceAlertReportSummary.listFromJson(json[r'history']),
        cache: AdminPriceAlertsResponseCache.fromJson(json[r'cache']),
      );
    }
    return null;
  }

  static List<AdminPriceAlertsResponse> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AdminPriceAlertsResponse>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AdminPriceAlertsResponse.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AdminPriceAlertsResponse> mapFromJson(dynamic json) {
    final map = <String, AdminPriceAlertsResponse>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AdminPriceAlertsResponse.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AdminPriceAlertsResponse-objects as value to a dart map
  static Map<String, List<AdminPriceAlertsResponse>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AdminPriceAlertsResponse>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AdminPriceAlertsResponse.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

