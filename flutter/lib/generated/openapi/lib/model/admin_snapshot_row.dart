//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AdminSnapshotRow {
  /// Returns a new [AdminSnapshotRow] instance.
  AdminSnapshotRow({
    this.id,
    this.date,
    this.userId,
    this.username,
    this.userNumber,
    this.totalAsset,
    this.totalInvest,
    this.totalCash,
    this.totalOther,
    this.totalLiability,
    this.totalPnl,
    this.dayPnl,
    this.updatedAt,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? id;

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
  String? userId;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? username;

  int? userNumber;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? totalAsset;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? totalInvest;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? totalCash;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? totalOther;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? totalLiability;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? totalPnl;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? dayPnl;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? updatedAt;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AdminSnapshotRow &&
    other.id == id &&
    other.date == date &&
    other.userId == userId &&
    other.username == username &&
    other.userNumber == userNumber &&
    other.totalAsset == totalAsset &&
    other.totalInvest == totalInvest &&
    other.totalCash == totalCash &&
    other.totalOther == totalOther &&
    other.totalLiability == totalLiability &&
    other.totalPnl == totalPnl &&
    other.dayPnl == dayPnl &&
    other.updatedAt == updatedAt;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (id == null ? 0 : id!.hashCode) +
    (date == null ? 0 : date!.hashCode) +
    (userId == null ? 0 : userId!.hashCode) +
    (username == null ? 0 : username!.hashCode) +
    (userNumber == null ? 0 : userNumber!.hashCode) +
    (totalAsset == null ? 0 : totalAsset!.hashCode) +
    (totalInvest == null ? 0 : totalInvest!.hashCode) +
    (totalCash == null ? 0 : totalCash!.hashCode) +
    (totalOther == null ? 0 : totalOther!.hashCode) +
    (totalLiability == null ? 0 : totalLiability!.hashCode) +
    (totalPnl == null ? 0 : totalPnl!.hashCode) +
    (dayPnl == null ? 0 : dayPnl!.hashCode) +
    (updatedAt == null ? 0 : updatedAt!.hashCode);

  @override
  String toString() => 'AdminSnapshotRow[id=$id, date=$date, userId=$userId, username=$username, userNumber=$userNumber, totalAsset=$totalAsset, totalInvest=$totalInvest, totalCash=$totalCash, totalOther=$totalOther, totalLiability=$totalLiability, totalPnl=$totalPnl, dayPnl=$dayPnl, updatedAt=$updatedAt]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.id != null) {
      json[r'id'] = this.id;
    } else {
      json[r'id'] = null;
    }
    if (this.date != null) {
      json[r'date'] = this.date;
    } else {
      json[r'date'] = null;
    }
    if (this.userId != null) {
      json[r'user_id'] = this.userId;
    } else {
      json[r'user_id'] = null;
    }
    if (this.username != null) {
      json[r'username'] = this.username;
    } else {
      json[r'username'] = null;
    }
    if (this.userNumber != null) {
      json[r'user_number'] = this.userNumber;
    } else {
      json[r'user_number'] = null;
    }
    if (this.totalAsset != null) {
      json[r'total_asset'] = this.totalAsset;
    } else {
      json[r'total_asset'] = null;
    }
    if (this.totalInvest != null) {
      json[r'total_invest'] = this.totalInvest;
    } else {
      json[r'total_invest'] = null;
    }
    if (this.totalCash != null) {
      json[r'total_cash'] = this.totalCash;
    } else {
      json[r'total_cash'] = null;
    }
    if (this.totalOther != null) {
      json[r'total_other'] = this.totalOther;
    } else {
      json[r'total_other'] = null;
    }
    if (this.totalLiability != null) {
      json[r'total_liability'] = this.totalLiability;
    } else {
      json[r'total_liability'] = null;
    }
    if (this.totalPnl != null) {
      json[r'total_pnl'] = this.totalPnl;
    } else {
      json[r'total_pnl'] = null;
    }
    if (this.dayPnl != null) {
      json[r'day_pnl'] = this.dayPnl;
    } else {
      json[r'day_pnl'] = null;
    }
    if (this.updatedAt != null) {
      json[r'updated_at'] = this.updatedAt;
    } else {
      json[r'updated_at'] = null;
    }
    return json;
  }

  /// Returns a new [AdminSnapshotRow] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AdminSnapshotRow? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AdminSnapshotRow[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AdminSnapshotRow[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AdminSnapshotRow(
        id: mapValueOfType<int>(json, r'id'),
        date: mapValueOfType<String>(json, r'date'),
        userId: mapValueOfType<String>(json, r'user_id'),
        username: mapValueOfType<String>(json, r'username'),
        userNumber: mapValueOfType<int>(json, r'user_number'),
        totalAsset: num.parse('${json[r'total_asset']}'),
        totalInvest: num.parse('${json[r'total_invest']}'),
        totalCash: num.parse('${json[r'total_cash']}'),
        totalOther: num.parse('${json[r'total_other']}'),
        totalLiability: num.parse('${json[r'total_liability']}'),
        totalPnl: num.parse('${json[r'total_pnl']}'),
        dayPnl: num.parse('${json[r'day_pnl']}'),
        updatedAt: mapValueOfType<String>(json, r'updated_at'),
      );
    }
    return null;
  }

  static List<AdminSnapshotRow> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AdminSnapshotRow>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AdminSnapshotRow.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AdminSnapshotRow> mapFromJson(dynamic json) {
    final map = <String, AdminSnapshotRow>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AdminSnapshotRow.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AdminSnapshotRow-objects as value to a dart map
  static Map<String, List<AdminSnapshotRow>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AdminSnapshotRow>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AdminSnapshotRow.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

