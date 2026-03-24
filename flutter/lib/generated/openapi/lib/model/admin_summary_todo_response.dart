//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AdminSummaryTodoResponse {
  /// Returns a new [AdminSummaryTodoResponse] instance.
  AdminSummaryTodoResponse({
    this.items = const [],
    this.snapshot,
  });

  List<AdminTodoItem> items;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  AdminSummaryTodoResponseSnapshot? snapshot;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AdminSummaryTodoResponse &&
    _deepEquality.equals(other.items, items) &&
    other.snapshot == snapshot;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (items.hashCode) +
    (snapshot == null ? 0 : snapshot!.hashCode);

  @override
  String toString() => 'AdminSummaryTodoResponse[items=$items, snapshot=$snapshot]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
      json[r'items'] = this.items;
    if (this.snapshot != null) {
      json[r'snapshot'] = this.snapshot;
    } else {
      json[r'snapshot'] = null;
    }
    return json;
  }

  /// Returns a new [AdminSummaryTodoResponse] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AdminSummaryTodoResponse? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AdminSummaryTodoResponse[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AdminSummaryTodoResponse[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AdminSummaryTodoResponse(
        items: AdminTodoItem.listFromJson(json[r'items']),
        snapshot: AdminSummaryTodoResponseSnapshot.fromJson(json[r'snapshot']),
      );
    }
    return null;
  }

  static List<AdminSummaryTodoResponse> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AdminSummaryTodoResponse>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AdminSummaryTodoResponse.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AdminSummaryTodoResponse> mapFromJson(dynamic json) {
    final map = <String, AdminSummaryTodoResponse>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AdminSummaryTodoResponse.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AdminSummaryTodoResponse-objects as value to a dart map
  static Map<String, List<AdminSummaryTodoResponse>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AdminSummaryTodoResponse>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AdminSummaryTodoResponse.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

