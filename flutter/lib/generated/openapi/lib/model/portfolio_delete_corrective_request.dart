//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class PortfolioDeleteCorrectiveRequest {
  /// Returns a new [PortfolioDeleteCorrectiveRequest] instance.
  PortfolioDeleteCorrectiveRequest({
    this.code,
    this.requestId,
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
  String? requestId;

  @override
  bool operator ==(Object other) => identical(this, other) || other is PortfolioDeleteCorrectiveRequest &&
    other.code == code &&
    other.requestId == requestId;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (code == null ? 0 : code!.hashCode) +
    (requestId == null ? 0 : requestId!.hashCode);

  @override
  String toString() => 'PortfolioDeleteCorrectiveRequest[code=$code, requestId=$requestId]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.code != null) {
      json[r'code'] = this.code;
    } else {
      json[r'code'] = null;
    }
    if (this.requestId != null) {
      json[r'request_id'] = this.requestId;
    } else {
      json[r'request_id'] = null;
    }
    return json;
  }

  /// Returns a new [PortfolioDeleteCorrectiveRequest] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static PortfolioDeleteCorrectiveRequest? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "PortfolioDeleteCorrectiveRequest[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "PortfolioDeleteCorrectiveRequest[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return PortfolioDeleteCorrectiveRequest(
        code: mapValueOfType<String>(json, r'code'),
        requestId: mapValueOfType<String>(json, r'request_id'),
      );
    }
    return null;
  }

  static List<PortfolioDeleteCorrectiveRequest> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <PortfolioDeleteCorrectiveRequest>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = PortfolioDeleteCorrectiveRequest.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, PortfolioDeleteCorrectiveRequest> mapFromJson(dynamic json) {
    final map = <String, PortfolioDeleteCorrectiveRequest>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = PortfolioDeleteCorrectiveRequest.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of PortfolioDeleteCorrectiveRequest-objects as value to a dart map
  static Map<String, List<PortfolioDeleteCorrectiveRequest>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<PortfolioDeleteCorrectiveRequest>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = PortfolioDeleteCorrectiveRequest.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

