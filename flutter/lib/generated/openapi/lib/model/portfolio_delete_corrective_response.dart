//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class PortfolioDeleteCorrectiveResponse {
  /// Returns a new [PortfolioDeleteCorrectiveResponse] instance.
  PortfolioDeleteCorrectiveResponse({
    this.status,
    this.code,
    this.deleted,
    this.fromDate,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? status;

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
  PortfolioDeleteCorrectiveResponseDeleted? deleted;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? fromDate;

  @override
  bool operator ==(Object other) => identical(this, other) || other is PortfolioDeleteCorrectiveResponse &&
    other.status == status &&
    other.code == code &&
    other.deleted == deleted &&
    other.fromDate == fromDate;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (status == null ? 0 : status!.hashCode) +
    (code == null ? 0 : code!.hashCode) +
    (deleted == null ? 0 : deleted!.hashCode) +
    (fromDate == null ? 0 : fromDate!.hashCode);

  @override
  String toString() => 'PortfolioDeleteCorrectiveResponse[status=$status, code=$code, deleted=$deleted, fromDate=$fromDate]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.status != null) {
      json[r'status'] = this.status;
    } else {
      json[r'status'] = null;
    }
    if (this.code != null) {
      json[r'code'] = this.code;
    } else {
      json[r'code'] = null;
    }
    if (this.deleted != null) {
      json[r'deleted'] = this.deleted;
    } else {
      json[r'deleted'] = null;
    }
    if (this.fromDate != null) {
      json[r'from_date'] = this.fromDate;
    } else {
      json[r'from_date'] = null;
    }
    return json;
  }

  /// Returns a new [PortfolioDeleteCorrectiveResponse] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static PortfolioDeleteCorrectiveResponse? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "PortfolioDeleteCorrectiveResponse[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "PortfolioDeleteCorrectiveResponse[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return PortfolioDeleteCorrectiveResponse(
        status: mapValueOfType<String>(json, r'status'),
        code: mapValueOfType<String>(json, r'code'),
        deleted: PortfolioDeleteCorrectiveResponseDeleted.fromJson(json[r'deleted']),
        fromDate: mapValueOfType<String>(json, r'from_date'),
      );
    }
    return null;
  }

  static List<PortfolioDeleteCorrectiveResponse> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <PortfolioDeleteCorrectiveResponse>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = PortfolioDeleteCorrectiveResponse.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, PortfolioDeleteCorrectiveResponse> mapFromJson(dynamic json) {
    final map = <String, PortfolioDeleteCorrectiveResponse>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = PortfolioDeleteCorrectiveResponse.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of PortfolioDeleteCorrectiveResponse-objects as value to a dart map
  static Map<String, List<PortfolioDeleteCorrectiveResponse>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<PortfolioDeleteCorrectiveResponse>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = PortfolioDeleteCorrectiveResponse.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

