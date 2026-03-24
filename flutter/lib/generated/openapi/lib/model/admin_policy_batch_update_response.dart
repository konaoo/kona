//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AdminPolicyBatchUpdateResponse {
  /// Returns a new [AdminPolicyBatchUpdateResponse] instance.
  AdminPolicyBatchUpdateResponse({
    this.status,
    this.updatedCount,
    this.items = const [],
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
  int? updatedCount;

  List<AdminPolicyItem> items;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AdminPolicyBatchUpdateResponse &&
    other.status == status &&
    other.updatedCount == updatedCount &&
    _deepEquality.equals(other.items, items);

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (status == null ? 0 : status!.hashCode) +
    (updatedCount == null ? 0 : updatedCount!.hashCode) +
    (items.hashCode);

  @override
  String toString() => 'AdminPolicyBatchUpdateResponse[status=$status, updatedCount=$updatedCount, items=$items]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.status != null) {
      json[r'status'] = this.status;
    } else {
      json[r'status'] = null;
    }
    if (this.updatedCount != null) {
      json[r'updated_count'] = this.updatedCount;
    } else {
      json[r'updated_count'] = null;
    }
      json[r'items'] = this.items;
    return json;
  }

  /// Returns a new [AdminPolicyBatchUpdateResponse] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AdminPolicyBatchUpdateResponse? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AdminPolicyBatchUpdateResponse[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AdminPolicyBatchUpdateResponse[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AdminPolicyBatchUpdateResponse(
        status: mapValueOfType<String>(json, r'status'),
        updatedCount: mapValueOfType<int>(json, r'updated_count'),
        items: AdminPolicyItem.listFromJson(json[r'items']),
      );
    }
    return null;
  }

  static List<AdminPolicyBatchUpdateResponse> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AdminPolicyBatchUpdateResponse>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AdminPolicyBatchUpdateResponse.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AdminPolicyBatchUpdateResponse> mapFromJson(dynamic json) {
    final map = <String, AdminPolicyBatchUpdateResponse>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AdminPolicyBatchUpdateResponse.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AdminPolicyBatchUpdateResponse-objects as value to a dart map
  static Map<String, List<AdminPolicyBatchUpdateResponse>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AdminPolicyBatchUpdateResponse>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AdminPolicyBatchUpdateResponse.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

