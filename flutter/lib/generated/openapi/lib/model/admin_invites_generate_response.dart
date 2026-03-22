//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AdminInvitesGenerateResponse {
  /// Returns a new [AdminInvitesGenerateResponse] instance.
  AdminInvitesGenerateResponse({
    this.status,
    this.batchId,
    this.requested,
    this.inserted,
    this.codes = const [],
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
  String? batchId;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? requested;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? inserted;

  List<String> codes;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AdminInvitesGenerateResponse &&
    other.status == status &&
    other.batchId == batchId &&
    other.requested == requested &&
    other.inserted == inserted &&
    _deepEquality.equals(other.codes, codes);

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (status == null ? 0 : status!.hashCode) +
    (batchId == null ? 0 : batchId!.hashCode) +
    (requested == null ? 0 : requested!.hashCode) +
    (inserted == null ? 0 : inserted!.hashCode) +
    (codes.hashCode);

  @override
  String toString() => 'AdminInvitesGenerateResponse[status=$status, batchId=$batchId, requested=$requested, inserted=$inserted, codes=$codes]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.status != null) {
      json[r'status'] = this.status;
    } else {
      json[r'status'] = null;
    }
    if (this.batchId != null) {
      json[r'batch_id'] = this.batchId;
    } else {
      json[r'batch_id'] = null;
    }
    if (this.requested != null) {
      json[r'requested'] = this.requested;
    } else {
      json[r'requested'] = null;
    }
    if (this.inserted != null) {
      json[r'inserted'] = this.inserted;
    } else {
      json[r'inserted'] = null;
    }
      json[r'codes'] = this.codes;
    return json;
  }

  /// Returns a new [AdminInvitesGenerateResponse] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AdminInvitesGenerateResponse? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AdminInvitesGenerateResponse[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AdminInvitesGenerateResponse[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AdminInvitesGenerateResponse(
        status: mapValueOfType<String>(json, r'status'),
        batchId: mapValueOfType<String>(json, r'batch_id'),
        requested: mapValueOfType<int>(json, r'requested'),
        inserted: mapValueOfType<int>(json, r'inserted'),
        codes: json[r'codes'] is Iterable
            ? (json[r'codes'] as Iterable).cast<String>().toList(growable: false)
            : const [],
      );
    }
    return null;
  }

  static List<AdminInvitesGenerateResponse> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AdminInvitesGenerateResponse>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AdminInvitesGenerateResponse.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AdminInvitesGenerateResponse> mapFromJson(dynamic json) {
    final map = <String, AdminInvitesGenerateResponse>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AdminInvitesGenerateResponse.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AdminInvitesGenerateResponse-objects as value to a dart map
  static Map<String, List<AdminInvitesGenerateResponse>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AdminInvitesGenerateResponse>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AdminInvitesGenerateResponse.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

