//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AdminConfigItem {
  /// Returns a new [AdminConfigItem] instance.
  AdminConfigItem({
    this.key,
    this.displayName,
    this.value,
    this.defaultValue,
    this.type,
    this.description,
    this.min,
    this.max,
    this.choices = const [],
    this.recommended,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? key;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? displayName;

  /// 配置当前值，服务端真实值可能是字符串、数字或布尔，这里统一按字符串描述以兼容类型生成
  String? value;

  /// 配置默认值，服务端真实值可能是字符串、数字或布尔，这里统一按字符串描述以兼容类型生成
  String? defaultValue;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? type;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? description;

  num? min;

  num? max;

  List<String> choices;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? recommended;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AdminConfigItem &&
    other.key == key &&
    other.displayName == displayName &&
    other.value == value &&
    other.defaultValue == defaultValue &&
    other.type == type &&
    other.description == description &&
    other.min == min &&
    other.max == max &&
    _deepEquality.equals(other.choices, choices) &&
    other.recommended == recommended;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (key == null ? 0 : key!.hashCode) +
    (displayName == null ? 0 : displayName!.hashCode) +
    (value == null ? 0 : value!.hashCode) +
    (defaultValue == null ? 0 : defaultValue!.hashCode) +
    (type == null ? 0 : type!.hashCode) +
    (description == null ? 0 : description!.hashCode) +
    (min == null ? 0 : min!.hashCode) +
    (max == null ? 0 : max!.hashCode) +
    (choices.hashCode) +
    (recommended == null ? 0 : recommended!.hashCode);

  @override
  String toString() => 'AdminConfigItem[key=$key, displayName=$displayName, value=$value, defaultValue=$defaultValue, type=$type, description=$description, min=$min, max=$max, choices=$choices, recommended=$recommended]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.key != null) {
      json[r'key'] = this.key;
    } else {
      json[r'key'] = null;
    }
    if (this.displayName != null) {
      json[r'display_name'] = this.displayName;
    } else {
      json[r'display_name'] = null;
    }
    if (this.value != null) {
      json[r'value'] = this.value;
    } else {
      json[r'value'] = null;
    }
    if (this.defaultValue != null) {
      json[r'default_value'] = this.defaultValue;
    } else {
      json[r'default_value'] = null;
    }
    if (this.type != null) {
      json[r'type'] = this.type;
    } else {
      json[r'type'] = null;
    }
    if (this.description != null) {
      json[r'description'] = this.description;
    } else {
      json[r'description'] = null;
    }
    if (this.min != null) {
      json[r'min'] = this.min;
    } else {
      json[r'min'] = null;
    }
    if (this.max != null) {
      json[r'max'] = this.max;
    } else {
      json[r'max'] = null;
    }
      json[r'choices'] = this.choices;
    if (this.recommended != null) {
      json[r'recommended'] = this.recommended;
    } else {
      json[r'recommended'] = null;
    }
    return json;
  }

  /// Returns a new [AdminConfigItem] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AdminConfigItem? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AdminConfigItem[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AdminConfigItem[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AdminConfigItem(
        key: mapValueOfType<String>(json, r'key'),
        displayName: mapValueOfType<String>(json, r'display_name'),
        value: mapValueOfType<String>(json, r'value'),
        defaultValue: mapValueOfType<String>(json, r'default_value'),
        type: mapValueOfType<String>(json, r'type'),
        description: mapValueOfType<String>(json, r'description'),
        min: json[r'min'] == null
            ? null
            : num.parse('${json[r'min']}'),
        max: json[r'max'] == null
            ? null
            : num.parse('${json[r'max']}'),
        choices: json[r'choices'] is Iterable
            ? (json[r'choices'] as Iterable).cast<String>().toList(growable: false)
            : const [],
        recommended: mapValueOfType<String>(json, r'recommended'),
      );
    }
    return null;
  }

  static List<AdminConfigItem> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AdminConfigItem>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AdminConfigItem.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AdminConfigItem> mapFromJson(dynamic json) {
    final map = <String, AdminConfigItem>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AdminConfigItem.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AdminConfigItem-objects as value to a dart map
  static Map<String, List<AdminConfigItem>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AdminConfigItem>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AdminConfigItem.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

