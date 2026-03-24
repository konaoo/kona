//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class ApiAdminUsersUpdatePostRequest {
  /// Returns a new [ApiAdminUsersUpdatePostRequest] instance.
  ApiAdminUsersUpdatePostRequest({
    this.userId,
    this.isAdmin,
    this.status,
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
  bool? isAdmin;

  ApiAdminUsersUpdatePostRequestStatusEnum? status;

  @override
  bool operator ==(Object other) => identical(this, other) || other is ApiAdminUsersUpdatePostRequest &&
    other.userId == userId &&
    other.isAdmin == isAdmin &&
    other.status == status;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (userId == null ? 0 : userId!.hashCode) +
    (isAdmin == null ? 0 : isAdmin!.hashCode) +
    (status == null ? 0 : status!.hashCode);

  @override
  String toString() => 'ApiAdminUsersUpdatePostRequest[userId=$userId, isAdmin=$isAdmin, status=$status]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.userId != null) {
      json[r'user_id'] = this.userId;
    } else {
      json[r'user_id'] = null;
    }
    if (this.isAdmin != null) {
      json[r'is_admin'] = this.isAdmin;
    } else {
      json[r'is_admin'] = null;
    }
    if (this.status != null) {
      json[r'status'] = this.status;
    } else {
      json[r'status'] = null;
    }
    return json;
  }

  /// Returns a new [ApiAdminUsersUpdatePostRequest] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static ApiAdminUsersUpdatePostRequest? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "ApiAdminUsersUpdatePostRequest[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "ApiAdminUsersUpdatePostRequest[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return ApiAdminUsersUpdatePostRequest(
        userId: mapValueOfType<String>(json, r'user_id'),
        isAdmin: mapValueOfType<bool>(json, r'is_admin'),
        status: ApiAdminUsersUpdatePostRequestStatusEnum.fromJson(json[r'status']),
      );
    }
    return null;
  }

  static List<ApiAdminUsersUpdatePostRequest> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <ApiAdminUsersUpdatePostRequest>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = ApiAdminUsersUpdatePostRequest.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, ApiAdminUsersUpdatePostRequest> mapFromJson(dynamic json) {
    final map = <String, ApiAdminUsersUpdatePostRequest>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = ApiAdminUsersUpdatePostRequest.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of ApiAdminUsersUpdatePostRequest-objects as value to a dart map
  static Map<String, List<ApiAdminUsersUpdatePostRequest>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<ApiAdminUsersUpdatePostRequest>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = ApiAdminUsersUpdatePostRequest.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}


class ApiAdminUsersUpdatePostRequestStatusEnum {
  /// Instantiate a new enum with the provided [value].
  const ApiAdminUsersUpdatePostRequestStatusEnum._(this.value);

  /// The underlying value of this enum member.
  final String value;

  @override
  String toString() => value;

  String toJson() => value;

  static const active = ApiAdminUsersUpdatePostRequestStatusEnum._(r'active');
  static const disabled = ApiAdminUsersUpdatePostRequestStatusEnum._(r'disabled');

  /// List of all possible values in this [enum][ApiAdminUsersUpdatePostRequestStatusEnum].
  static const values = <ApiAdminUsersUpdatePostRequestStatusEnum>[
    active,
    disabled,
  ];

  static ApiAdminUsersUpdatePostRequestStatusEnum? fromJson(dynamic value) => ApiAdminUsersUpdatePostRequestStatusEnumTypeTransformer().decode(value);

  static List<ApiAdminUsersUpdatePostRequestStatusEnum> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <ApiAdminUsersUpdatePostRequestStatusEnum>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = ApiAdminUsersUpdatePostRequestStatusEnum.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }
}

/// Transformation class that can [encode] an instance of [ApiAdminUsersUpdatePostRequestStatusEnum] to String,
/// and [decode] dynamic data back to [ApiAdminUsersUpdatePostRequestStatusEnum].
class ApiAdminUsersUpdatePostRequestStatusEnumTypeTransformer {
  factory ApiAdminUsersUpdatePostRequestStatusEnumTypeTransformer() => _instance ??= const ApiAdminUsersUpdatePostRequestStatusEnumTypeTransformer._();

  const ApiAdminUsersUpdatePostRequestStatusEnumTypeTransformer._();

  String encode(ApiAdminUsersUpdatePostRequestStatusEnum data) => data.value;

  /// Decodes a [dynamic value][data] to a ApiAdminUsersUpdatePostRequestStatusEnum.
  ///
  /// If [allowNull] is true and the [dynamic value][data] cannot be decoded successfully,
  /// then null is returned. However, if [allowNull] is false and the [dynamic value][data]
  /// cannot be decoded successfully, then an [UnimplementedError] is thrown.
  ///
  /// The [allowNull] is very handy when an API changes and a new enum value is added or removed,
  /// and users are still using an old app with the old code.
  ApiAdminUsersUpdatePostRequestStatusEnum? decode(dynamic data, {bool allowNull = true}) {
    if (data != null) {
      switch (data) {
        case r'active': return ApiAdminUsersUpdatePostRequestStatusEnum.active;
        case r'disabled': return ApiAdminUsersUpdatePostRequestStatusEnum.disabled;
        default:
          if (!allowNull) {
            throw ArgumentError('Unknown enum value to decode: $data');
          }
      }
    }
    return null;
  }

  /// Singleton [ApiAdminUsersUpdatePostRequestStatusEnumTypeTransformer] instance.
  static ApiAdminUsersUpdatePostRequestStatusEnumTypeTransformer? _instance;
}


