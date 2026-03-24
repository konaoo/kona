//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AdminPriceProbeResponse {
  /// Returns a new [AdminPriceProbeResponse] instance.
  AdminPriceProbeResponse({
    this.code,
    this.assetType,
    this.assetTypeLabel,
    this.current,
    this.sources = const [],
    this.diagnosis,
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
  String? assetType;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? assetTypeLabel;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  AdminPriceProbeCurrent? current;

  List<AdminPriceAlertSourceItem> sources;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  AdminPriceProbeDiagnosis? diagnosis;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AdminPriceProbeResponse &&
    other.code == code &&
    other.assetType == assetType &&
    other.assetTypeLabel == assetTypeLabel &&
    other.current == current &&
    _deepEquality.equals(other.sources, sources) &&
    other.diagnosis == diagnosis;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (code == null ? 0 : code!.hashCode) +
    (assetType == null ? 0 : assetType!.hashCode) +
    (assetTypeLabel == null ? 0 : assetTypeLabel!.hashCode) +
    (current == null ? 0 : current!.hashCode) +
    (sources.hashCode) +
    (diagnosis == null ? 0 : diagnosis!.hashCode);

  @override
  String toString() => 'AdminPriceProbeResponse[code=$code, assetType=$assetType, assetTypeLabel=$assetTypeLabel, current=$current, sources=$sources, diagnosis=$diagnosis]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.code != null) {
      json[r'code'] = this.code;
    } else {
      json[r'code'] = null;
    }
    if (this.assetType != null) {
      json[r'asset_type'] = this.assetType;
    } else {
      json[r'asset_type'] = null;
    }
    if (this.assetTypeLabel != null) {
      json[r'asset_type_label'] = this.assetTypeLabel;
    } else {
      json[r'asset_type_label'] = null;
    }
    if (this.current != null) {
      json[r'current'] = this.current;
    } else {
      json[r'current'] = null;
    }
      json[r'sources'] = this.sources;
    if (this.diagnosis != null) {
      json[r'diagnosis'] = this.diagnosis;
    } else {
      json[r'diagnosis'] = null;
    }
    return json;
  }

  /// Returns a new [AdminPriceProbeResponse] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AdminPriceProbeResponse? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AdminPriceProbeResponse[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AdminPriceProbeResponse[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AdminPriceProbeResponse(
        code: mapValueOfType<String>(json, r'code'),
        assetType: mapValueOfType<String>(json, r'asset_type'),
        assetTypeLabel: mapValueOfType<String>(json, r'asset_type_label'),
        current: AdminPriceProbeCurrent.fromJson(json[r'current']),
        sources: AdminPriceAlertSourceItem.listFromJson(json[r'sources']),
        diagnosis: AdminPriceProbeDiagnosis.fromJson(json[r'diagnosis']),
      );
    }
    return null;
  }

  static List<AdminPriceProbeResponse> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AdminPriceProbeResponse>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AdminPriceProbeResponse.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AdminPriceProbeResponse> mapFromJson(dynamic json) {
    final map = <String, AdminPriceProbeResponse>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AdminPriceProbeResponse.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AdminPriceProbeResponse-objects as value to a dart map
  static Map<String, List<AdminPriceProbeResponse>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AdminPriceProbeResponse>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AdminPriceProbeResponse.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

