//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AppVersionResponse {
  /// Returns a new [AppVersionResponse] instance.
  AppVersionResponse({
    this.version,
    this.buildNumber,
    this.releaseNotes,
    this.downloadUrl,
    this.forceUpdate,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? version;

  /// 构建号，服务端历史上可能返回整数，这里统一按字符串描述以兼容类型生成
  String? buildNumber;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? releaseNotes;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? downloadUrl;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  bool? forceUpdate;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AppVersionResponse &&
    other.version == version &&
    other.buildNumber == buildNumber &&
    other.releaseNotes == releaseNotes &&
    other.downloadUrl == downloadUrl &&
    other.forceUpdate == forceUpdate;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (version == null ? 0 : version!.hashCode) +
    (buildNumber == null ? 0 : buildNumber!.hashCode) +
    (releaseNotes == null ? 0 : releaseNotes!.hashCode) +
    (downloadUrl == null ? 0 : downloadUrl!.hashCode) +
    (forceUpdate == null ? 0 : forceUpdate!.hashCode);

  @override
  String toString() => 'AppVersionResponse[version=$version, buildNumber=$buildNumber, releaseNotes=$releaseNotes, downloadUrl=$downloadUrl, forceUpdate=$forceUpdate]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.version != null) {
      json[r'version'] = this.version;
    } else {
      json[r'version'] = null;
    }
    if (this.buildNumber != null) {
      json[r'buildNumber'] = this.buildNumber;
    } else {
      json[r'buildNumber'] = null;
    }
    if (this.releaseNotes != null) {
      json[r'releaseNotes'] = this.releaseNotes;
    } else {
      json[r'releaseNotes'] = null;
    }
    if (this.downloadUrl != null) {
      json[r'downloadUrl'] = this.downloadUrl;
    } else {
      json[r'downloadUrl'] = null;
    }
    if (this.forceUpdate != null) {
      json[r'forceUpdate'] = this.forceUpdate;
    } else {
      json[r'forceUpdate'] = null;
    }
    return json;
  }

  /// Returns a new [AppVersionResponse] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AppVersionResponse? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AppVersionResponse[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AppVersionResponse[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AppVersionResponse(
        version: mapValueOfType<String>(json, r'version'),
        buildNumber: mapValueOfType<String>(json, r'buildNumber'),
        releaseNotes: mapValueOfType<String>(json, r'releaseNotes'),
        downloadUrl: mapValueOfType<String>(json, r'downloadUrl'),
        forceUpdate: mapValueOfType<bool>(json, r'forceUpdate'),
      );
    }
    return null;
  }

  static List<AppVersionResponse> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AppVersionResponse>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AppVersionResponse.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AppVersionResponse> mapFromJson(dynamic json) {
    final map = <String, AppVersionResponse>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AppVersionResponse.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AppVersionResponse-objects as value to a dart map
  static Map<String, List<AppVersionResponse>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AppVersionResponse>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AppVersionResponse.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

