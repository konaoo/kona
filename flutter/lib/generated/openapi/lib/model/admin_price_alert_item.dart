//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AdminPriceAlertItem {
  /// Returns a new [AdminPriceAlertItem] instance.
  AdminPriceAlertItem({
    this.code,
    this.name,
    this.curr,
    this.userCount,
    this.usernames = const [],
    this.currentPrice,
    this.currentYclose,
    this.baselinePrice,
    this.baselineYclose,
    this.baselineSource,
    this.baselineSourceKey,
    this.deltaPct,
    this.severity,
    this.alertType,
    this.reason,
    this.suggestion,
    this.sources = const [],
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
  String? curr;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? userCount;

  List<String> usernames;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? currentPrice;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? currentYclose;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? baselinePrice;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? baselineYclose;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? baselineSource;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? baselineSourceKey;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? deltaPct;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? severity;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? alertType;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? reason;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? suggestion;

  List<AdminPriceAlertSourceItem> sources;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AdminPriceAlertItem &&
    other.code == code &&
    other.name == name &&
    other.curr == curr &&
    other.userCount == userCount &&
    _deepEquality.equals(other.usernames, usernames) &&
    other.currentPrice == currentPrice &&
    other.currentYclose == currentYclose &&
    other.baselinePrice == baselinePrice &&
    other.baselineYclose == baselineYclose &&
    other.baselineSource == baselineSource &&
    other.baselineSourceKey == baselineSourceKey &&
    other.deltaPct == deltaPct &&
    other.severity == severity &&
    other.alertType == alertType &&
    other.reason == reason &&
    other.suggestion == suggestion &&
    _deepEquality.equals(other.sources, sources);

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (code == null ? 0 : code!.hashCode) +
    (name == null ? 0 : name!.hashCode) +
    (curr == null ? 0 : curr!.hashCode) +
    (userCount == null ? 0 : userCount!.hashCode) +
    (usernames.hashCode) +
    (currentPrice == null ? 0 : currentPrice!.hashCode) +
    (currentYclose == null ? 0 : currentYclose!.hashCode) +
    (baselinePrice == null ? 0 : baselinePrice!.hashCode) +
    (baselineYclose == null ? 0 : baselineYclose!.hashCode) +
    (baselineSource == null ? 0 : baselineSource!.hashCode) +
    (baselineSourceKey == null ? 0 : baselineSourceKey!.hashCode) +
    (deltaPct == null ? 0 : deltaPct!.hashCode) +
    (severity == null ? 0 : severity!.hashCode) +
    (alertType == null ? 0 : alertType!.hashCode) +
    (reason == null ? 0 : reason!.hashCode) +
    (suggestion == null ? 0 : suggestion!.hashCode) +
    (sources.hashCode);

  @override
  String toString() => 'AdminPriceAlertItem[code=$code, name=$name, curr=$curr, userCount=$userCount, usernames=$usernames, currentPrice=$currentPrice, currentYclose=$currentYclose, baselinePrice=$baselinePrice, baselineYclose=$baselineYclose, baselineSource=$baselineSource, baselineSourceKey=$baselineSourceKey, deltaPct=$deltaPct, severity=$severity, alertType=$alertType, reason=$reason, suggestion=$suggestion, sources=$sources]';

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
    if (this.curr != null) {
      json[r'curr'] = this.curr;
    } else {
      json[r'curr'] = null;
    }
    if (this.userCount != null) {
      json[r'user_count'] = this.userCount;
    } else {
      json[r'user_count'] = null;
    }
      json[r'usernames'] = this.usernames;
    if (this.currentPrice != null) {
      json[r'current_price'] = this.currentPrice;
    } else {
      json[r'current_price'] = null;
    }
    if (this.currentYclose != null) {
      json[r'current_yclose'] = this.currentYclose;
    } else {
      json[r'current_yclose'] = null;
    }
    if (this.baselinePrice != null) {
      json[r'baseline_price'] = this.baselinePrice;
    } else {
      json[r'baseline_price'] = null;
    }
    if (this.baselineYclose != null) {
      json[r'baseline_yclose'] = this.baselineYclose;
    } else {
      json[r'baseline_yclose'] = null;
    }
    if (this.baselineSource != null) {
      json[r'baseline_source'] = this.baselineSource;
    } else {
      json[r'baseline_source'] = null;
    }
    if (this.baselineSourceKey != null) {
      json[r'baseline_source_key'] = this.baselineSourceKey;
    } else {
      json[r'baseline_source_key'] = null;
    }
    if (this.deltaPct != null) {
      json[r'delta_pct'] = this.deltaPct;
    } else {
      json[r'delta_pct'] = null;
    }
    if (this.severity != null) {
      json[r'severity'] = this.severity;
    } else {
      json[r'severity'] = null;
    }
    if (this.alertType != null) {
      json[r'alert_type'] = this.alertType;
    } else {
      json[r'alert_type'] = null;
    }
    if (this.reason != null) {
      json[r'reason'] = this.reason;
    } else {
      json[r'reason'] = null;
    }
    if (this.suggestion != null) {
      json[r'suggestion'] = this.suggestion;
    } else {
      json[r'suggestion'] = null;
    }
      json[r'sources'] = this.sources;
    return json;
  }

  /// Returns a new [AdminPriceAlertItem] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AdminPriceAlertItem? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AdminPriceAlertItem[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AdminPriceAlertItem[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AdminPriceAlertItem(
        code: mapValueOfType<String>(json, r'code'),
        name: mapValueOfType<String>(json, r'name'),
        curr: mapValueOfType<String>(json, r'curr'),
        userCount: mapValueOfType<int>(json, r'user_count'),
        usernames: json[r'usernames'] is Iterable
            ? (json[r'usernames'] as Iterable).cast<String>().toList(growable: false)
            : const [],
        currentPrice: num.parse('${json[r'current_price']}'),
        currentYclose: num.parse('${json[r'current_yclose']}'),
        baselinePrice: num.parse('${json[r'baseline_price']}'),
        baselineYclose: num.parse('${json[r'baseline_yclose']}'),
        baselineSource: mapValueOfType<String>(json, r'baseline_source'),
        baselineSourceKey: mapValueOfType<String>(json, r'baseline_source_key'),
        deltaPct: num.parse('${json[r'delta_pct']}'),
        severity: mapValueOfType<String>(json, r'severity'),
        alertType: mapValueOfType<String>(json, r'alert_type'),
        reason: mapValueOfType<String>(json, r'reason'),
        suggestion: mapValueOfType<String>(json, r'suggestion'),
        sources: AdminPriceAlertSourceItem.listFromJson(json[r'sources']),
      );
    }
    return null;
  }

  static List<AdminPriceAlertItem> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AdminPriceAlertItem>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AdminPriceAlertItem.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AdminPriceAlertItem> mapFromJson(dynamic json) {
    final map = <String, AdminPriceAlertItem>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AdminPriceAlertItem.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AdminPriceAlertItem-objects as value to a dart map
  static Map<String, List<AdminPriceAlertItem>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AdminPriceAlertItem>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AdminPriceAlertItem.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

