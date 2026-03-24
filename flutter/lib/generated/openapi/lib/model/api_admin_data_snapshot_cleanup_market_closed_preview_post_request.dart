//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class ApiAdminDataSnapshotCleanupMarketClosedPreviewPostRequest {
  /// Returns a new [ApiAdminDataSnapshotCleanupMarketClosedPreviewPostRequest] instance.
  ApiAdminDataSnapshotCleanupMarketClosedPreviewPostRequest({
    this.userId,
    this.startDate,
    this.endDate,
    this.markets = const [],
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
  String? startDate;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? endDate;

  /// 要预览的市场列表；服务端历史上也兼容单个字符串
  List<String> markets;

  @override
  bool operator ==(Object other) => identical(this, other) || other is ApiAdminDataSnapshotCleanupMarketClosedPreviewPostRequest &&
    other.userId == userId &&
    other.startDate == startDate &&
    other.endDate == endDate &&
    _deepEquality.equals(other.markets, markets);

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (userId == null ? 0 : userId!.hashCode) +
    (startDate == null ? 0 : startDate!.hashCode) +
    (endDate == null ? 0 : endDate!.hashCode) +
    (markets.hashCode);

  @override
  String toString() => 'ApiAdminDataSnapshotCleanupMarketClosedPreviewPostRequest[userId=$userId, startDate=$startDate, endDate=$endDate, markets=$markets]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.userId != null) {
      json[r'user_id'] = this.userId;
    } else {
      json[r'user_id'] = null;
    }
    if (this.startDate != null) {
      json[r'start_date'] = this.startDate;
    } else {
      json[r'start_date'] = null;
    }
    if (this.endDate != null) {
      json[r'end_date'] = this.endDate;
    } else {
      json[r'end_date'] = null;
    }
      json[r'markets'] = this.markets;
    return json;
  }

  /// Returns a new [ApiAdminDataSnapshotCleanupMarketClosedPreviewPostRequest] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static ApiAdminDataSnapshotCleanupMarketClosedPreviewPostRequest? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "ApiAdminDataSnapshotCleanupMarketClosedPreviewPostRequest[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "ApiAdminDataSnapshotCleanupMarketClosedPreviewPostRequest[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return ApiAdminDataSnapshotCleanupMarketClosedPreviewPostRequest(
        userId: mapValueOfType<String>(json, r'user_id'),
        startDate: mapValueOfType<String>(json, r'start_date'),
        endDate: mapValueOfType<String>(json, r'end_date'),
        markets: json[r'markets'] is Iterable
            ? (json[r'markets'] as Iterable).cast<String>().toList(growable: false)
            : const [],
      );
    }
    return null;
  }

  static List<ApiAdminDataSnapshotCleanupMarketClosedPreviewPostRequest> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <ApiAdminDataSnapshotCleanupMarketClosedPreviewPostRequest>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = ApiAdminDataSnapshotCleanupMarketClosedPreviewPostRequest.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, ApiAdminDataSnapshotCleanupMarketClosedPreviewPostRequest> mapFromJson(dynamic json) {
    final map = <String, ApiAdminDataSnapshotCleanupMarketClosedPreviewPostRequest>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = ApiAdminDataSnapshotCleanupMarketClosedPreviewPostRequest.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of ApiAdminDataSnapshotCleanupMarketClosedPreviewPostRequest-objects as value to a dart map
  static Map<String, List<ApiAdminDataSnapshotCleanupMarketClosedPreviewPostRequest>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<ApiAdminDataSnapshotCleanupMarketClosedPreviewPostRequest>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = ApiAdminDataSnapshotCleanupMarketClosedPreviewPostRequest.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

