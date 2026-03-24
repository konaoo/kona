//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AdminSnapshotCleanupPreviewResponse {
  /// Returns a new [AdminSnapshotCleanupPreviewResponse] instance.
  AdminSnapshotCleanupPreviewResponse({
    this.status,
    this.affected,
    this.markets = const [],
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
  int? affected;

  List<String> markets;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AdminSnapshotCleanupPreviewResponse &&
    other.status == status &&
    other.affected == affected &&
    _deepEquality.equals(other.markets, markets);

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (status == null ? 0 : status!.hashCode) +
    (affected == null ? 0 : affected!.hashCode) +
    (markets.hashCode);

  @override
  String toString() => 'AdminSnapshotCleanupPreviewResponse[status=$status, affected=$affected, markets=$markets]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.status != null) {
      json[r'status'] = this.status;
    } else {
      json[r'status'] = null;
    }
    if (this.affected != null) {
      json[r'affected'] = this.affected;
    } else {
      json[r'affected'] = null;
    }
      json[r'markets'] = this.markets;
    return json;
  }

  /// Returns a new [AdminSnapshotCleanupPreviewResponse] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AdminSnapshotCleanupPreviewResponse? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AdminSnapshotCleanupPreviewResponse[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AdminSnapshotCleanupPreviewResponse[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AdminSnapshotCleanupPreviewResponse(
        status: mapValueOfType<String>(json, r'status'),
        affected: mapValueOfType<int>(json, r'affected'),
        markets: json[r'markets'] is Iterable
            ? (json[r'markets'] as Iterable).cast<String>().toList(growable: false)
            : const [],
      );
    }
    return null;
  }

  static List<AdminSnapshotCleanupPreviewResponse> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AdminSnapshotCleanupPreviewResponse>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AdminSnapshotCleanupPreviewResponse.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AdminSnapshotCleanupPreviewResponse> mapFromJson(dynamic json) {
    final map = <String, AdminSnapshotCleanupPreviewResponse>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AdminSnapshotCleanupPreviewResponse.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AdminSnapshotCleanupPreviewResponse-objects as value to a dart map
  static Map<String, List<AdminSnapshotCleanupPreviewResponse>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AdminSnapshotCleanupPreviewResponse>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AdminSnapshotCleanupPreviewResponse.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

