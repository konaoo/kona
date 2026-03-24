//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class SyncBootstrapResponseVersions {
  /// Returns a new [SyncBootstrapResponseVersions] instance.
  SyncBootstrapResponseVersions({
    this.portfolio,
    this.cashAssets,
    this.otherAssets,
    this.liabilities,
    this.history,
    this.overviewAll,
    this.rates,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? portfolio;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? cashAssets;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? otherAssets;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? liabilities;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? history;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? overviewAll;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? rates;

  @override
  bool operator ==(Object other) => identical(this, other) || other is SyncBootstrapResponseVersions &&
    other.portfolio == portfolio &&
    other.cashAssets == cashAssets &&
    other.otherAssets == otherAssets &&
    other.liabilities == liabilities &&
    other.history == history &&
    other.overviewAll == overviewAll &&
    other.rates == rates;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (portfolio == null ? 0 : portfolio!.hashCode) +
    (cashAssets == null ? 0 : cashAssets!.hashCode) +
    (otherAssets == null ? 0 : otherAssets!.hashCode) +
    (liabilities == null ? 0 : liabilities!.hashCode) +
    (history == null ? 0 : history!.hashCode) +
    (overviewAll == null ? 0 : overviewAll!.hashCode) +
    (rates == null ? 0 : rates!.hashCode);

  @override
  String toString() => 'SyncBootstrapResponseVersions[portfolio=$portfolio, cashAssets=$cashAssets, otherAssets=$otherAssets, liabilities=$liabilities, history=$history, overviewAll=$overviewAll, rates=$rates]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.portfolio != null) {
      json[r'portfolio'] = this.portfolio;
    } else {
      json[r'portfolio'] = null;
    }
    if (this.cashAssets != null) {
      json[r'cash_assets'] = this.cashAssets;
    } else {
      json[r'cash_assets'] = null;
    }
    if (this.otherAssets != null) {
      json[r'other_assets'] = this.otherAssets;
    } else {
      json[r'other_assets'] = null;
    }
    if (this.liabilities != null) {
      json[r'liabilities'] = this.liabilities;
    } else {
      json[r'liabilities'] = null;
    }
    if (this.history != null) {
      json[r'history'] = this.history;
    } else {
      json[r'history'] = null;
    }
    if (this.overviewAll != null) {
      json[r'overview_all'] = this.overviewAll;
    } else {
      json[r'overview_all'] = null;
    }
    if (this.rates != null) {
      json[r'rates'] = this.rates;
    } else {
      json[r'rates'] = null;
    }
    return json;
  }

  /// Returns a new [SyncBootstrapResponseVersions] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static SyncBootstrapResponseVersions? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "SyncBootstrapResponseVersions[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "SyncBootstrapResponseVersions[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return SyncBootstrapResponseVersions(
        portfolio: mapValueOfType<String>(json, r'portfolio'),
        cashAssets: mapValueOfType<String>(json, r'cash_assets'),
        otherAssets: mapValueOfType<String>(json, r'other_assets'),
        liabilities: mapValueOfType<String>(json, r'liabilities'),
        history: mapValueOfType<String>(json, r'history'),
        overviewAll: mapValueOfType<String>(json, r'overview_all'),
        rates: mapValueOfType<String>(json, r'rates'),
      );
    }
    return null;
  }

  static List<SyncBootstrapResponseVersions> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <SyncBootstrapResponseVersions>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = SyncBootstrapResponseVersions.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, SyncBootstrapResponseVersions> mapFromJson(dynamic json) {
    final map = <String, SyncBootstrapResponseVersions>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = SyncBootstrapResponseVersions.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of SyncBootstrapResponseVersions-objects as value to a dart map
  static Map<String, List<SyncBootstrapResponseVersions>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<SyncBootstrapResponseVersions>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = SyncBootstrapResponseVersions.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

