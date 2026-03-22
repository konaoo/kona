//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AdminRebindPreviewResponse {
  /// Returns a new [AdminRebindPreviewResponse] instance.
  AdminRebindPreviewResponse({
    this.targetUserId,
    this.targetUsername,
    this.tables = const {},
    this.sources = const {},
    this.total,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? targetUserId;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? targetUsername;

  Map<String, int> tables;

  /// 来源统计明细，键是来源名，值是各表计数明细
  Map<String, Object> sources;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? total;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AdminRebindPreviewResponse &&
    other.targetUserId == targetUserId &&
    other.targetUsername == targetUsername &&
    _deepEquality.equals(other.tables, tables) &&
    _deepEquality.equals(other.sources, sources) &&
    other.total == total;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (targetUserId == null ? 0 : targetUserId!.hashCode) +
    (targetUsername == null ? 0 : targetUsername!.hashCode) +
    (tables.hashCode) +
    (sources.hashCode) +
    (total == null ? 0 : total!.hashCode);

  @override
  String toString() => 'AdminRebindPreviewResponse[targetUserId=$targetUserId, targetUsername=$targetUsername, tables=$tables, sources=$sources, total=$total]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.targetUserId != null) {
      json[r'target_user_id'] = this.targetUserId;
    } else {
      json[r'target_user_id'] = null;
    }
    if (this.targetUsername != null) {
      json[r'target_username'] = this.targetUsername;
    } else {
      json[r'target_username'] = null;
    }
      json[r'tables'] = this.tables;
      json[r'sources'] = this.sources;
    if (this.total != null) {
      json[r'total'] = this.total;
    } else {
      json[r'total'] = null;
    }
    return json;
  }

  /// Returns a new [AdminRebindPreviewResponse] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AdminRebindPreviewResponse? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AdminRebindPreviewResponse[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AdminRebindPreviewResponse[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AdminRebindPreviewResponse(
        targetUserId: mapValueOfType<String>(json, r'target_user_id'),
        targetUsername: mapValueOfType<String>(json, r'target_username'),
        tables: mapCastOfType<String, int>(json, r'tables') ?? const {},
        sources: mapCastOfType<String, Object>(json, r'sources') ?? const {},
        total: mapValueOfType<int>(json, r'total'),
      );
    }
    return null;
  }

  static List<AdminRebindPreviewResponse> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AdminRebindPreviewResponse>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AdminRebindPreviewResponse.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AdminRebindPreviewResponse> mapFromJson(dynamic json) {
    final map = <String, AdminRebindPreviewResponse>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AdminRebindPreviewResponse.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AdminRebindPreviewResponse-objects as value to a dart map
  static Map<String, List<AdminRebindPreviewResponse>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AdminRebindPreviewResponse>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AdminRebindPreviewResponse.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

