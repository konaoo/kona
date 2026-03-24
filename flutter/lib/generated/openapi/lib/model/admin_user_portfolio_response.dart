//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AdminUserPortfolioResponse {
  /// Returns a new [AdminUserPortfolioResponse] instance.
  AdminUserPortfolioResponse({
    this.userId,
    this.total,
    this.summary,
    this.items = const [],
    this.cache,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? userId;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? total;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  AdminUserPortfolioResponseSummary? summary;

  List<AdminUserPortfolioItem> items;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  AdminUserPortfolioResponseCache? cache;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AdminUserPortfolioResponse &&
    other.userId == userId &&
    other.total == total &&
    other.summary == summary &&
    _deepEquality.equals(other.items, items) &&
    other.cache == cache;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (userId == null ? 0 : userId!.hashCode) +
    (total == null ? 0 : total!.hashCode) +
    (summary == null ? 0 : summary!.hashCode) +
    (items.hashCode) +
    (cache == null ? 0 : cache!.hashCode);

  @override
  String toString() => 'AdminUserPortfolioResponse[userId=$userId, total=$total, summary=$summary, items=$items, cache=$cache]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.userId != null) {
      json[r'user_id'] = this.userId;
    } else {
      json[r'user_id'] = null;
    }
    if (this.total != null) {
      json[r'total'] = this.total;
    } else {
      json[r'total'] = null;
    }
    if (this.summary != null) {
      json[r'summary'] = this.summary;
    } else {
      json[r'summary'] = null;
    }
      json[r'items'] = this.items;
    if (this.cache != null) {
      json[r'cache'] = this.cache;
    } else {
      json[r'cache'] = null;
    }
    return json;
  }

  /// Returns a new [AdminUserPortfolioResponse] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AdminUserPortfolioResponse? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AdminUserPortfolioResponse[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AdminUserPortfolioResponse[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AdminUserPortfolioResponse(
        userId: mapValueOfType<String>(json, r'user_id'),
        total: mapValueOfType<int>(json, r'total'),
        summary: AdminUserPortfolioResponseSummary.fromJson(json[r'summary']),
        items: AdminUserPortfolioItem.listFromJson(json[r'items']),
        cache: AdminUserPortfolioResponseCache.fromJson(json[r'cache']),
      );
    }
    return null;
  }

  static List<AdminUserPortfolioResponse> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AdminUserPortfolioResponse>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AdminUserPortfolioResponse.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AdminUserPortfolioResponse> mapFromJson(dynamic json) {
    final map = <String, AdminUserPortfolioResponse>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AdminUserPortfolioResponse.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AdminUserPortfolioResponse-objects as value to a dart map
  static Map<String, List<AdminUserPortfolioResponse>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AdminUserPortfolioResponse>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AdminUserPortfolioResponse.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

