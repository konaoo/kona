//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AssetTrendPoint {
  /// Returns a new [AssetTrendPoint] instance.
  AssetTrendPoint({
    this.date,
    this.value,
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
  num? value;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AssetTrendPoint &&
    other.date == date &&
    other.value == value;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (date == null ? 0 : date!.hashCode) +
    (value == null ? 0 : value!.hashCode);

  @override
  String toString() => 'AssetTrendPoint[date=$date, value=$value]';

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
    return json;
  }

  /// Returns a new [AssetTrendPoint] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AssetTrendPoint? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AssetTrendPoint[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AssetTrendPoint[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AssetTrendPoint(
        date: mapValueOfType<String>(json, r'date'),
        value: num.parse('${json[r'value']}'),
      );
    }
    return null;
  }

  static List<AssetTrendPoint> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AssetTrendPoint>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AssetTrendPoint.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AssetTrendPoint> mapFromJson(dynamic json) {
    final map = <String, AssetTrendPoint>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AssetTrendPoint.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AssetTrendPoint-objects as value to a dart map
  static Map<String, List<AssetTrendPoint>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AssetTrendPoint>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AssetTrendPoint.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

