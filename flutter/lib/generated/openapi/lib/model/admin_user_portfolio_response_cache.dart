//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AdminUserPortfolioResponseCache {
  /// Returns a new [AdminUserPortfolioResponseCache] instance.
  AdminUserPortfolioResponseCache({
    this.cachedAt,
    this.expiresAt,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? cachedAt;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? expiresAt;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AdminUserPortfolioResponseCache &&
    other.cachedAt == cachedAt &&
    other.expiresAt == expiresAt;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (cachedAt == null ? 0 : cachedAt!.hashCode) +
    (expiresAt == null ? 0 : expiresAt!.hashCode);

  @override
  String toString() => 'AdminUserPortfolioResponseCache[cachedAt=$cachedAt, expiresAt=$expiresAt]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.cachedAt != null) {
      json[r'cached_at'] = this.cachedAt;
    } else {
      json[r'cached_at'] = null;
    }
    if (this.expiresAt != null) {
      json[r'expires_at'] = this.expiresAt;
    } else {
      json[r'expires_at'] = null;
    }
    return json;
  }

  /// Returns a new [AdminUserPortfolioResponseCache] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AdminUserPortfolioResponseCache? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AdminUserPortfolioResponseCache[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AdminUserPortfolioResponseCache[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AdminUserPortfolioResponseCache(
        cachedAt: mapValueOfType<String>(json, r'cached_at'),
        expiresAt: mapValueOfType<String>(json, r'expires_at'),
      );
    }
    return null;
  }

  static List<AdminUserPortfolioResponseCache> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AdminUserPortfolioResponseCache>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AdminUserPortfolioResponseCache.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AdminUserPortfolioResponseCache> mapFromJson(dynamic json) {
    final map = <String, AdminUserPortfolioResponseCache>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AdminUserPortfolioResponseCache.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AdminUserPortfolioResponseCache-objects as value to a dart map
  static Map<String, List<AdminUserPortfolioResponseCache>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AdminUserPortfolioResponseCache>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AdminUserPortfolioResponseCache.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

