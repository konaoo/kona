//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class ApiAdminApisProviderTestPostRequest {
  /// Returns a new [ApiAdminApisProviderTestPostRequest] instance.
  ApiAdminApisProviderTestPostRequest({
    this.providerKey,
  });

  ApiAdminApisProviderTestPostRequestProviderKeyEnum? providerKey;

  @override
  bool operator ==(Object other) => identical(this, other) || other is ApiAdminApisProviderTestPostRequest &&
    other.providerKey == providerKey;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (providerKey == null ? 0 : providerKey!.hashCode);

  @override
  String toString() => 'ApiAdminApisProviderTestPostRequest[providerKey=$providerKey]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.providerKey != null) {
      json[r'provider_key'] = this.providerKey;
    } else {
      json[r'provider_key'] = null;
    }
    return json;
  }

  /// Returns a new [ApiAdminApisProviderTestPostRequest] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static ApiAdminApisProviderTestPostRequest? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "ApiAdminApisProviderTestPostRequest[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "ApiAdminApisProviderTestPostRequest[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return ApiAdminApisProviderTestPostRequest(
        providerKey: ApiAdminApisProviderTestPostRequestProviderKeyEnum.fromJson(json[r'provider_key']),
      );
    }
    return null;
  }

  static List<ApiAdminApisProviderTestPostRequest> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <ApiAdminApisProviderTestPostRequest>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = ApiAdminApisProviderTestPostRequest.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, ApiAdminApisProviderTestPostRequest> mapFromJson(dynamic json) {
    final map = <String, ApiAdminApisProviderTestPostRequest>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = ApiAdminApisProviderTestPostRequest.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of ApiAdminApisProviderTestPostRequest-objects as value to a dart map
  static Map<String, List<ApiAdminApisProviderTestPostRequest>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<ApiAdminApisProviderTestPostRequest>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = ApiAdminApisProviderTestPostRequest.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}


class ApiAdminApisProviderTestPostRequestProviderKeyEnum {
  /// Instantiate a new enum with the provided [value].
  const ApiAdminApisProviderTestPostRequestProviderKeyEnum._(this.value);

  /// The underlying value of this enum member.
  final String value;

  @override
  String toString() => value;

  String toJson() => value;

  static const sinaQuote = ApiAdminApisProviderTestPostRequestProviderKeyEnum._(r'sina_quote');
  static const tencentQuote = ApiAdminApisProviderTestPostRequestProviderKeyEnum._(r'tencent_quote');
  static const eastmoneyQuote = ApiAdminApisProviderTestPostRequestProviderKeyEnum._(r'eastmoney_quote');
  static const forexRate = ApiAdminApisProviderTestPostRequestProviderKeyEnum._(r'forex_rate');

  /// List of all possible values in this [enum][ApiAdminApisProviderTestPostRequestProviderKeyEnum].
  static const values = <ApiAdminApisProviderTestPostRequestProviderKeyEnum>[
    sinaQuote,
    tencentQuote,
    eastmoneyQuote,
    forexRate,
  ];

  static ApiAdminApisProviderTestPostRequestProviderKeyEnum? fromJson(dynamic value) => ApiAdminApisProviderTestPostRequestProviderKeyEnumTypeTransformer().decode(value);

  static List<ApiAdminApisProviderTestPostRequestProviderKeyEnum> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <ApiAdminApisProviderTestPostRequestProviderKeyEnum>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = ApiAdminApisProviderTestPostRequestProviderKeyEnum.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }
}

/// Transformation class that can [encode] an instance of [ApiAdminApisProviderTestPostRequestProviderKeyEnum] to String,
/// and [decode] dynamic data back to [ApiAdminApisProviderTestPostRequestProviderKeyEnum].
class ApiAdminApisProviderTestPostRequestProviderKeyEnumTypeTransformer {
  factory ApiAdminApisProviderTestPostRequestProviderKeyEnumTypeTransformer() => _instance ??= const ApiAdminApisProviderTestPostRequestProviderKeyEnumTypeTransformer._();

  const ApiAdminApisProviderTestPostRequestProviderKeyEnumTypeTransformer._();

  String encode(ApiAdminApisProviderTestPostRequestProviderKeyEnum data) => data.value;

  /// Decodes a [dynamic value][data] to a ApiAdminApisProviderTestPostRequestProviderKeyEnum.
  ///
  /// If [allowNull] is true and the [dynamic value][data] cannot be decoded successfully,
  /// then null is returned. However, if [allowNull] is false and the [dynamic value][data]
  /// cannot be decoded successfully, then an [UnimplementedError] is thrown.
  ///
  /// The [allowNull] is very handy when an API changes and a new enum value is added or removed,
  /// and users are still using an old app with the old code.
  ApiAdminApisProviderTestPostRequestProviderKeyEnum? decode(dynamic data, {bool allowNull = true}) {
    if (data != null) {
      switch (data) {
        case r'sina_quote': return ApiAdminApisProviderTestPostRequestProviderKeyEnum.sinaQuote;
        case r'tencent_quote': return ApiAdminApisProviderTestPostRequestProviderKeyEnum.tencentQuote;
        case r'eastmoney_quote': return ApiAdminApisProviderTestPostRequestProviderKeyEnum.eastmoneyQuote;
        case r'forex_rate': return ApiAdminApisProviderTestPostRequestProviderKeyEnum.forexRate;
        default:
          if (!allowNull) {
            throw ArgumentError('Unknown enum value to decode: $data');
          }
      }
    }
    return null;
  }

  /// Singleton [ApiAdminApisProviderTestPostRequestProviderKeyEnumTypeTransformer] instance.
  static ApiAdminApisProviderTestPostRequestProviderKeyEnumTypeTransformer? _instance;
}


