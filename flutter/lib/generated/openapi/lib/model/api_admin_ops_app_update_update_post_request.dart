//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class ApiAdminOpsAppUpdateUpdatePostRequest {
  /// Returns a new [ApiAdminOpsAppUpdateUpdatePostRequest] instance.
  ApiAdminOpsAppUpdateUpdatePostRequest({
    this.text,
    this.downloadUrl,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? text;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? downloadUrl;

  @override
  bool operator ==(Object other) => identical(this, other) || other is ApiAdminOpsAppUpdateUpdatePostRequest &&
    other.text == text &&
    other.downloadUrl == downloadUrl;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (text == null ? 0 : text!.hashCode) +
    (downloadUrl == null ? 0 : downloadUrl!.hashCode);

  @override
  String toString() => 'ApiAdminOpsAppUpdateUpdatePostRequest[text=$text, downloadUrl=$downloadUrl]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.text != null) {
      json[r'text'] = this.text;
    } else {
      json[r'text'] = null;
    }
    if (this.downloadUrl != null) {
      json[r'download_url'] = this.downloadUrl;
    } else {
      json[r'download_url'] = null;
    }
    return json;
  }

  /// Returns a new [ApiAdminOpsAppUpdateUpdatePostRequest] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static ApiAdminOpsAppUpdateUpdatePostRequest? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "ApiAdminOpsAppUpdateUpdatePostRequest[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "ApiAdminOpsAppUpdateUpdatePostRequest[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return ApiAdminOpsAppUpdateUpdatePostRequest(
        text: mapValueOfType<String>(json, r'text'),
        downloadUrl: mapValueOfType<String>(json, r'download_url'),
      );
    }
    return null;
  }

  static List<ApiAdminOpsAppUpdateUpdatePostRequest> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <ApiAdminOpsAppUpdateUpdatePostRequest>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = ApiAdminOpsAppUpdateUpdatePostRequest.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, ApiAdminOpsAppUpdateUpdatePostRequest> mapFromJson(dynamic json) {
    final map = <String, ApiAdminOpsAppUpdateUpdatePostRequest>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = ApiAdminOpsAppUpdateUpdatePostRequest.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of ApiAdminOpsAppUpdateUpdatePostRequest-objects as value to a dart map
  static Map<String, List<ApiAdminOpsAppUpdateUpdatePostRequest>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<ApiAdminOpsAppUpdateUpdatePostRequest>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = ApiAdminOpsAppUpdateUpdatePostRequest.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

