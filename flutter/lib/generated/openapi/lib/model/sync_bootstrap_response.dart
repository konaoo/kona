//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class SyncBootstrapResponse {
  /// Returns a new [SyncBootstrapResponse] instance.
  SyncBootstrapResponse({
    this.serverTime,
    this.versions,
    this.changed = const [],
    this.data = const {},
    this.marketStatuses = const {},
    this.marketStatus = const {},
    this.quotePolicy,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? serverTime;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  SyncBootstrapResponseVersions? versions;

  List<String> changed;

  Map<String, Object> data;

  Map<String, MarketStatusItem> marketStatuses;

  Map<String, bool> marketStatus;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  SyncBootstrapResponseQuotePolicy? quotePolicy;

  @override
  bool operator ==(Object other) => identical(this, other) || other is SyncBootstrapResponse &&
    other.serverTime == serverTime &&
    other.versions == versions &&
    _deepEquality.equals(other.changed, changed) &&
    _deepEquality.equals(other.data, data) &&
    _deepEquality.equals(other.marketStatuses, marketStatuses) &&
    _deepEquality.equals(other.marketStatus, marketStatus) &&
    other.quotePolicy == quotePolicy;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (serverTime == null ? 0 : serverTime!.hashCode) +
    (versions == null ? 0 : versions!.hashCode) +
    (changed.hashCode) +
    (data.hashCode) +
    (marketStatuses.hashCode) +
    (marketStatus.hashCode) +
    (quotePolicy == null ? 0 : quotePolicy!.hashCode);

  @override
  String toString() => 'SyncBootstrapResponse[serverTime=$serverTime, versions=$versions, changed=$changed, data=$data, marketStatuses=$marketStatuses, marketStatus=$marketStatus, quotePolicy=$quotePolicy]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.serverTime != null) {
      json[r'server_time'] = this.serverTime;
    } else {
      json[r'server_time'] = null;
    }
    if (this.versions != null) {
      json[r'versions'] = this.versions;
    } else {
      json[r'versions'] = null;
    }
      json[r'changed'] = this.changed;
      json[r'data'] = this.data;
      json[r'market_statuses'] = this.marketStatuses;
      json[r'market_status'] = this.marketStatus;
    if (this.quotePolicy != null) {
      json[r'quote_policy'] = this.quotePolicy;
    } else {
      json[r'quote_policy'] = null;
    }
    return json;
  }

  /// Returns a new [SyncBootstrapResponse] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static SyncBootstrapResponse? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "SyncBootstrapResponse[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "SyncBootstrapResponse[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return SyncBootstrapResponse(
        serverTime: mapValueOfType<String>(json, r'server_time'),
        versions: SyncBootstrapResponseVersions.fromJson(json[r'versions']),
        changed: json[r'changed'] is Iterable
            ? (json[r'changed'] as Iterable).cast<String>().toList(growable: false)
            : const [],
        data: mapCastOfType<String, Object>(json, r'data') ?? const {},
        marketStatuses: MarketStatusItem.mapFromJson(json[r'market_statuses']),
        marketStatus: mapCastOfType<String, bool>(json, r'market_status') ?? const {},
        quotePolicy: SyncBootstrapResponseQuotePolicy.fromJson(json[r'quote_policy']),
      );
    }
    return null;
  }

  static List<SyncBootstrapResponse> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <SyncBootstrapResponse>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = SyncBootstrapResponse.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, SyncBootstrapResponse> mapFromJson(dynamic json) {
    final map = <String, SyncBootstrapResponse>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = SyncBootstrapResponse.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of SyncBootstrapResponse-objects as value to a dart map
  static Map<String, List<SyncBootstrapResponse>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<SyncBootstrapResponse>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = SyncBootstrapResponse.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

