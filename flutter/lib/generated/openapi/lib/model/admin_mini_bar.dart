//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AdminMiniBar {
  /// Returns a new [AdminMiniBar] instance.
  AdminMiniBar({
    this.date,
    this.value,
    this.height,
    this.isLatest,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? date;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? value;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? height;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  bool? isLatest;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AdminMiniBar &&
    other.date == date &&
    other.value == value &&
    other.height == height &&
    other.isLatest == isLatest;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (date == null ? 0 : date!.hashCode) +
    (value == null ? 0 : value!.hashCode) +
    (height == null ? 0 : height!.hashCode) +
    (isLatest == null ? 0 : isLatest!.hashCode);

  @override
  String toString() => 'AdminMiniBar[date=$date, value=$value, height=$height, isLatest=$isLatest]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.date != null) {
      json[r'date'] = this.date;
    } else {
      json[r'date'] = null;
    }
    if (this.value != null) {
      json[r'value'] = this.value;
    } else {
      json[r'value'] = null;
    }
    if (this.height != null) {
      json[r'height'] = this.height;
    } else {
      json[r'height'] = null;
    }
    if (this.isLatest != null) {
      json[r'is_latest'] = this.isLatest;
    } else {
      json[r'is_latest'] = null;
    }
    return json;
  }

  /// Returns a new [AdminMiniBar] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AdminMiniBar? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AdminMiniBar[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AdminMiniBar[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AdminMiniBar(
        date: mapValueOfType<String>(json, r'date'),
        value: mapValueOfType<int>(json, r'value'),
        height: mapValueOfType<String>(json, r'height'),
        isLatest: mapValueOfType<bool>(json, r'is_latest'),
      );
    }
    return null;
  }

  static List<AdminMiniBar> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AdminMiniBar>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AdminMiniBar.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AdminMiniBar> mapFromJson(dynamic json) {
    final map = <String, AdminMiniBar>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AdminMiniBar.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AdminMiniBar-objects as value to a dart map
  static Map<String, List<AdminMiniBar>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AdminMiniBar>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AdminMiniBar.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

