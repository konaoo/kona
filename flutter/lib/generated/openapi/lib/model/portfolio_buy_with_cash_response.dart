//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class PortfolioBuyWithCashResponse {
  /// Returns a new [PortfolioBuyWithCashResponse] instance.
  PortfolioBuyWithCashResponse({
    this.status,
    this.cashDeducted,
    this.cashCurr,
    this.undoToken,
    this.undoExpireAt,
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
  num? cashDeducted;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? cashCurr;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? undoToken;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? undoExpireAt;

  @override
  bool operator ==(Object other) => identical(this, other) || other is PortfolioBuyWithCashResponse &&
    other.status == status &&
    other.cashDeducted == cashDeducted &&
    other.cashCurr == cashCurr &&
    other.undoToken == undoToken &&
    other.undoExpireAt == undoExpireAt;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (status == null ? 0 : status!.hashCode) +
    (cashDeducted == null ? 0 : cashDeducted!.hashCode) +
    (cashCurr == null ? 0 : cashCurr!.hashCode) +
    (undoToken == null ? 0 : undoToken!.hashCode) +
    (undoExpireAt == null ? 0 : undoExpireAt!.hashCode);

  @override
  String toString() => 'PortfolioBuyWithCashResponse[status=$status, cashDeducted=$cashDeducted, cashCurr=$cashCurr, undoToken=$undoToken, undoExpireAt=$undoExpireAt]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.status != null) {
      json[r'status'] = this.status;
    } else {
      json[r'status'] = null;
    }
    if (this.cashDeducted != null) {
      json[r'cash_deducted'] = this.cashDeducted;
    } else {
      json[r'cash_deducted'] = null;
    }
    if (this.cashCurr != null) {
      json[r'cash_curr'] = this.cashCurr;
    } else {
      json[r'cash_curr'] = null;
    }
    if (this.undoToken != null) {
      json[r'undo_token'] = this.undoToken;
    } else {
      json[r'undo_token'] = null;
    }
    if (this.undoExpireAt != null) {
      json[r'undo_expire_at'] = this.undoExpireAt;
    } else {
      json[r'undo_expire_at'] = null;
    }
    return json;
  }

  /// Returns a new [PortfolioBuyWithCashResponse] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static PortfolioBuyWithCashResponse? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "PortfolioBuyWithCashResponse[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "PortfolioBuyWithCashResponse[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return PortfolioBuyWithCashResponse(
        status: mapValueOfType<String>(json, r'status'),
        cashDeducted: num.parse('${json[r'cash_deducted']}'),
        cashCurr: mapValueOfType<String>(json, r'cash_curr'),
        undoToken: mapValueOfType<String>(json, r'undo_token'),
        undoExpireAt: mapValueOfType<String>(json, r'undo_expire_at'),
      );
    }
    return null;
  }

  static List<PortfolioBuyWithCashResponse> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <PortfolioBuyWithCashResponse>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = PortfolioBuyWithCashResponse.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, PortfolioBuyWithCashResponse> mapFromJson(dynamic json) {
    final map = <String, PortfolioBuyWithCashResponse>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = PortfolioBuyWithCashResponse.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of PortfolioBuyWithCashResponse-objects as value to a dart map
  static Map<String, List<PortfolioBuyWithCashResponse>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<PortfolioBuyWithCashResponse>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = PortfolioBuyWithCashResponse.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

