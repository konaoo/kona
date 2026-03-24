//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class WebConfigResponse {
  /// Returns a new [WebConfigResponse] instance.
  WebConfigResponse({
    this.portalTitle,
    this.apkDownloadUrl,
    this.appVersion,
    this.inviteAcquireText,
    this.inviteAcquireImageUrl,
    this.userGroupText,
    this.userGroupImageUrl,
    this.iosQrText,
    this.iosQrImageUrl,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? portalTitle;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? apkDownloadUrl;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? appVersion;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? inviteAcquireText;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? inviteAcquireImageUrl;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? userGroupText;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? userGroupImageUrl;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? iosQrText;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? iosQrImageUrl;

  @override
  bool operator ==(Object other) => identical(this, other) || other is WebConfigResponse &&
    other.portalTitle == portalTitle &&
    other.apkDownloadUrl == apkDownloadUrl &&
    other.appVersion == appVersion &&
    other.inviteAcquireText == inviteAcquireText &&
    other.inviteAcquireImageUrl == inviteAcquireImageUrl &&
    other.userGroupText == userGroupText &&
    other.userGroupImageUrl == userGroupImageUrl &&
    other.iosQrText == iosQrText &&
    other.iosQrImageUrl == iosQrImageUrl;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (portalTitle == null ? 0 : portalTitle!.hashCode) +
    (apkDownloadUrl == null ? 0 : apkDownloadUrl!.hashCode) +
    (appVersion == null ? 0 : appVersion!.hashCode) +
    (inviteAcquireText == null ? 0 : inviteAcquireText!.hashCode) +
    (inviteAcquireImageUrl == null ? 0 : inviteAcquireImageUrl!.hashCode) +
    (userGroupText == null ? 0 : userGroupText!.hashCode) +
    (userGroupImageUrl == null ? 0 : userGroupImageUrl!.hashCode) +
    (iosQrText == null ? 0 : iosQrText!.hashCode) +
    (iosQrImageUrl == null ? 0 : iosQrImageUrl!.hashCode);

  @override
  String toString() => 'WebConfigResponse[portalTitle=$portalTitle, apkDownloadUrl=$apkDownloadUrl, appVersion=$appVersion, inviteAcquireText=$inviteAcquireText, inviteAcquireImageUrl=$inviteAcquireImageUrl, userGroupText=$userGroupText, userGroupImageUrl=$userGroupImageUrl, iosQrText=$iosQrText, iosQrImageUrl=$iosQrImageUrl]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.portalTitle != null) {
      json[r'portal_title'] = this.portalTitle;
    } else {
      json[r'portal_title'] = null;
    }
    if (this.apkDownloadUrl != null) {
      json[r'apk_download_url'] = this.apkDownloadUrl;
    } else {
      json[r'apk_download_url'] = null;
    }
    if (this.appVersion != null) {
      json[r'app_version'] = this.appVersion;
    } else {
      json[r'app_version'] = null;
    }
    if (this.inviteAcquireText != null) {
      json[r'invite_acquire_text'] = this.inviteAcquireText;
    } else {
      json[r'invite_acquire_text'] = null;
    }
    if (this.inviteAcquireImageUrl != null) {
      json[r'invite_acquire_image_url'] = this.inviteAcquireImageUrl;
    } else {
      json[r'invite_acquire_image_url'] = null;
    }
    if (this.userGroupText != null) {
      json[r'user_group_text'] = this.userGroupText;
    } else {
      json[r'user_group_text'] = null;
    }
    if (this.userGroupImageUrl != null) {
      json[r'user_group_image_url'] = this.userGroupImageUrl;
    } else {
      json[r'user_group_image_url'] = null;
    }
    if (this.iosQrText != null) {
      json[r'ios_qr_text'] = this.iosQrText;
    } else {
      json[r'ios_qr_text'] = null;
    }
    if (this.iosQrImageUrl != null) {
      json[r'ios_qr_image_url'] = this.iosQrImageUrl;
    } else {
      json[r'ios_qr_image_url'] = null;
    }
    return json;
  }

  /// Returns a new [WebConfigResponse] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static WebConfigResponse? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "WebConfigResponse[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "WebConfigResponse[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return WebConfigResponse(
        portalTitle: mapValueOfType<String>(json, r'portal_title'),
        apkDownloadUrl: mapValueOfType<String>(json, r'apk_download_url'),
        appVersion: mapValueOfType<String>(json, r'app_version'),
        inviteAcquireText: mapValueOfType<String>(json, r'invite_acquire_text'),
        inviteAcquireImageUrl: mapValueOfType<String>(json, r'invite_acquire_image_url'),
        userGroupText: mapValueOfType<String>(json, r'user_group_text'),
        userGroupImageUrl: mapValueOfType<String>(json, r'user_group_image_url'),
        iosQrText: mapValueOfType<String>(json, r'ios_qr_text'),
        iosQrImageUrl: mapValueOfType<String>(json, r'ios_qr_image_url'),
      );
    }
    return null;
  }

  static List<WebConfigResponse> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <WebConfigResponse>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = WebConfigResponse.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, WebConfigResponse> mapFromJson(dynamic json) {
    final map = <String, WebConfigResponse>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = WebConfigResponse.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of WebConfigResponse-objects as value to a dart map
  static Map<String, List<WebConfigResponse>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<WebConfigResponse>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = WebConfigResponse.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

