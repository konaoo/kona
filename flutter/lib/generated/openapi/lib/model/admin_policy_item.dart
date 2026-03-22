//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AdminPolicyItem {
  /// Returns a new [AdminPolicyItem] instance.
  AdminPolicyItem({
    this.id,
    this.scopeKey,
    this.scopeType,
    this.enabled,
    this.limitPerMin,
    this.note,
    this.updatedBy,
    this.updatedAt,
    this.displayName,
    this.impact,
    this.scopeTypeLabel,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? id;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? scopeKey;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? scopeType;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  bool? enabled;

  int? limitPerMin;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? note;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? updatedBy;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? updatedAt;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? displayName;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? impact;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? scopeTypeLabel;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AdminPolicyItem &&
    other.id == id &&
    other.scopeKey == scopeKey &&
    other.scopeType == scopeType &&
    other.enabled == enabled &&
    other.limitPerMin == limitPerMin &&
    other.note == note &&
    other.updatedBy == updatedBy &&
    other.updatedAt == updatedAt &&
    other.displayName == displayName &&
    other.impact == impact &&
    other.scopeTypeLabel == scopeTypeLabel;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (id == null ? 0 : id!.hashCode) +
    (scopeKey == null ? 0 : scopeKey!.hashCode) +
    (scopeType == null ? 0 : scopeType!.hashCode) +
    (enabled == null ? 0 : enabled!.hashCode) +
    (limitPerMin == null ? 0 : limitPerMin!.hashCode) +
    (note == null ? 0 : note!.hashCode) +
    (updatedBy == null ? 0 : updatedBy!.hashCode) +
    (updatedAt == null ? 0 : updatedAt!.hashCode) +
    (displayName == null ? 0 : displayName!.hashCode) +
    (impact == null ? 0 : impact!.hashCode) +
    (scopeTypeLabel == null ? 0 : scopeTypeLabel!.hashCode);

  @override
  String toString() => 'AdminPolicyItem[id=$id, scopeKey=$scopeKey, scopeType=$scopeType, enabled=$enabled, limitPerMin=$limitPerMin, note=$note, updatedBy=$updatedBy, updatedAt=$updatedAt, displayName=$displayName, impact=$impact, scopeTypeLabel=$scopeTypeLabel]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.id != null) {
      json[r'id'] = this.id;
    } else {
      json[r'id'] = null;
    }
    if (this.scopeKey != null) {
      json[r'scope_key'] = this.scopeKey;
    } else {
      json[r'scope_key'] = null;
    }
    if (this.scopeType != null) {
      json[r'scope_type'] = this.scopeType;
    } else {
      json[r'scope_type'] = null;
    }
    if (this.enabled != null) {
      json[r'enabled'] = this.enabled;
    } else {
      json[r'enabled'] = null;
    }
    if (this.limitPerMin != null) {
      json[r'limit_per_min'] = this.limitPerMin;
    } else {
      json[r'limit_per_min'] = null;
    }
    if (this.note != null) {
      json[r'note'] = this.note;
    } else {
      json[r'note'] = null;
    }
    if (this.updatedBy != null) {
      json[r'updated_by'] = this.updatedBy;
    } else {
      json[r'updated_by'] = null;
    }
    if (this.updatedAt != null) {
      json[r'updated_at'] = this.updatedAt;
    } else {
      json[r'updated_at'] = null;
    }
    if (this.displayName != null) {
      json[r'display_name'] = this.displayName;
    } else {
      json[r'display_name'] = null;
    }
    if (this.impact != null) {
      json[r'impact'] = this.impact;
    } else {
      json[r'impact'] = null;
    }
    if (this.scopeTypeLabel != null) {
      json[r'scope_type_label'] = this.scopeTypeLabel;
    } else {
      json[r'scope_type_label'] = null;
    }
    return json;
  }

  /// Returns a new [AdminPolicyItem] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AdminPolicyItem? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AdminPolicyItem[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AdminPolicyItem[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AdminPolicyItem(
        id: mapValueOfType<int>(json, r'id'),
        scopeKey: mapValueOfType<String>(json, r'scope_key'),
        scopeType: mapValueOfType<String>(json, r'scope_type'),
        enabled: mapValueOfType<bool>(json, r'enabled'),
        limitPerMin: mapValueOfType<int>(json, r'limit_per_min'),
        note: mapValueOfType<String>(json, r'note'),
        updatedBy: mapValueOfType<String>(json, r'updated_by'),
        updatedAt: mapValueOfType<String>(json, r'updated_at'),
        displayName: mapValueOfType<String>(json, r'display_name'),
        impact: mapValueOfType<String>(json, r'impact'),
        scopeTypeLabel: mapValueOfType<String>(json, r'scope_type_label'),
      );
    }
    return null;
  }

  static List<AdminPolicyItem> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AdminPolicyItem>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AdminPolicyItem.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AdminPolicyItem> mapFromJson(dynamic json) {
    final map = <String, AdminPolicyItem>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AdminPolicyItem.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AdminPolicyItem-objects as value to a dart map
  static Map<String, List<AdminPolicyItem>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AdminPolicyItem>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AdminPolicyItem.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

