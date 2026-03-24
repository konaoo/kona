//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class SyncBootstrapRequest {
  /// Returns a new [SyncBootstrapRequest] instance.
  SyncBootstrapRequest({
    this.include = const [],
    this.clientVersions = const {},
    this.portfolioMetrics,
  });

  List<SyncBootstrapRequestIncludeEnum> include;

  Map<String, String> clientVersions;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  bool? portfolioMetrics;

  @override
  bool operator ==(Object other) => identical(this, other) || other is SyncBootstrapRequest &&
    _deepEquality.equals(other.include, include) &&
    _deepEquality.equals(other.clientVersions, clientVersions) &&
    other.portfolioMetrics == portfolioMetrics;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (include.hashCode) +
    (clientVersions.hashCode) +
    (portfolioMetrics == null ? 0 : portfolioMetrics!.hashCode);

  @override
  String toString() => 'SyncBootstrapRequest[include=$include, clientVersions=$clientVersions, portfolioMetrics=$portfolioMetrics]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
      json[r'include'] = this.include;
      json[r'client_versions'] = this.clientVersions;
    if (this.portfolioMetrics != null) {
      json[r'portfolio_metrics'] = this.portfolioMetrics;
    } else {
      json[r'portfolio_metrics'] = null;
    }
    return json;
  }

  /// Returns a new [SyncBootstrapRequest] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static SyncBootstrapRequest? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "SyncBootstrapRequest[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "SyncBootstrapRequest[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return SyncBootstrapRequest(
        include: SyncBootstrapRequestIncludeEnum.listFromJson(json[r'include']),
        clientVersions: mapCastOfType<String, String>(json, r'client_versions') ?? const {},
        portfolioMetrics: mapValueOfType<bool>(json, r'portfolio_metrics'),
      );
    }
    return null;
  }

  static List<SyncBootstrapRequest> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <SyncBootstrapRequest>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = SyncBootstrapRequest.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, SyncBootstrapRequest> mapFromJson(dynamic json) {
    final map = <String, SyncBootstrapRequest>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = SyncBootstrapRequest.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of SyncBootstrapRequest-objects as value to a dart map
  static Map<String, List<SyncBootstrapRequest>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<SyncBootstrapRequest>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = SyncBootstrapRequest.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}


class SyncBootstrapRequestIncludeEnum {
  /// Instantiate a new enum with the provided [value].
  const SyncBootstrapRequestIncludeEnum._(this.value);

  /// The underlying value of this enum member.
  final String value;

  @override
  String toString() => value;

  String toJson() => value;

  static const portfolio = SyncBootstrapRequestIncludeEnum._(r'portfolio');
  static const cashAssets = SyncBootstrapRequestIncludeEnum._(r'cash_assets');
  static const otherAssets = SyncBootstrapRequestIncludeEnum._(r'other_assets');
  static const liabilities = SyncBootstrapRequestIncludeEnum._(r'liabilities');
  static const history = SyncBootstrapRequestIncludeEnum._(r'history');
  static const overviewAll = SyncBootstrapRequestIncludeEnum._(r'overview_all');
  static const rates = SyncBootstrapRequestIncludeEnum._(r'rates');

  /// List of all possible values in this [enum][SyncBootstrapRequestIncludeEnum].
  static const values = <SyncBootstrapRequestIncludeEnum>[
    portfolio,
    cashAssets,
    otherAssets,
    liabilities,
    history,
    overviewAll,
    rates,
  ];

  static SyncBootstrapRequestIncludeEnum? fromJson(dynamic value) => SyncBootstrapRequestIncludeEnumTypeTransformer().decode(value);

  static List<SyncBootstrapRequestIncludeEnum> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <SyncBootstrapRequestIncludeEnum>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = SyncBootstrapRequestIncludeEnum.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }
}

/// Transformation class that can [encode] an instance of [SyncBootstrapRequestIncludeEnum] to String,
/// and [decode] dynamic data back to [SyncBootstrapRequestIncludeEnum].
class SyncBootstrapRequestIncludeEnumTypeTransformer {
  factory SyncBootstrapRequestIncludeEnumTypeTransformer() => _instance ??= const SyncBootstrapRequestIncludeEnumTypeTransformer._();

  const SyncBootstrapRequestIncludeEnumTypeTransformer._();

  String encode(SyncBootstrapRequestIncludeEnum data) => data.value;

  /// Decodes a [dynamic value][data] to a SyncBootstrapRequestIncludeEnum.
  ///
  /// If [allowNull] is true and the [dynamic value][data] cannot be decoded successfully,
  /// then null is returned. However, if [allowNull] is false and the [dynamic value][data]
  /// cannot be decoded successfully, then an [UnimplementedError] is thrown.
  ///
  /// The [allowNull] is very handy when an API changes and a new enum value is added or removed,
  /// and users are still using an old app with the old code.
  SyncBootstrapRequestIncludeEnum? decode(dynamic data, {bool allowNull = true}) {
    if (data != null) {
      switch (data) {
        case r'portfolio': return SyncBootstrapRequestIncludeEnum.portfolio;
        case r'cash_assets': return SyncBootstrapRequestIncludeEnum.cashAssets;
        case r'other_assets': return SyncBootstrapRequestIncludeEnum.otherAssets;
        case r'liabilities': return SyncBootstrapRequestIncludeEnum.liabilities;
        case r'history': return SyncBootstrapRequestIncludeEnum.history;
        case r'overview_all': return SyncBootstrapRequestIncludeEnum.overviewAll;
        case r'rates': return SyncBootstrapRequestIncludeEnum.rates;
        default:
          if (!allowNull) {
            throw ArgumentError('Unknown enum value to decode: $data');
          }
      }
    }
    return null;
  }

  /// Singleton [SyncBootstrapRequestIncludeEnumTypeTransformer] instance.
  static SyncBootstrapRequestIncludeEnumTypeTransformer? _instance;
}


