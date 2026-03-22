//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AdminPriceAlertSourceItem {
  /// Returns a new [AdminPriceAlertSourceItem] instance.
  AdminPriceAlertSourceItem({
    this.sourceKey,
    this.sourceLabel,
    this.price,
    this.yclose,
    this.amt,
    this.chg,
    this.ok,
    this.deltaPct,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? sourceKey;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? sourceLabel;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? price;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? yclose;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? amt;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? chg;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  bool? ok;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? deltaPct;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AdminPriceAlertSourceItem &&
    other.sourceKey == sourceKey &&
    other.sourceLabel == sourceLabel &&
    other.price == price &&
    other.yclose == yclose &&
    other.amt == amt &&
    other.chg == chg &&
    other.ok == ok &&
    other.deltaPct == deltaPct;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (sourceKey == null ? 0 : sourceKey!.hashCode) +
    (sourceLabel == null ? 0 : sourceLabel!.hashCode) +
    (price == null ? 0 : price!.hashCode) +
    (yclose == null ? 0 : yclose!.hashCode) +
    (amt == null ? 0 : amt!.hashCode) +
    (chg == null ? 0 : chg!.hashCode) +
    (ok == null ? 0 : ok!.hashCode) +
    (deltaPct == null ? 0 : deltaPct!.hashCode);

  @override
  String toString() => 'AdminPriceAlertSourceItem[sourceKey=$sourceKey, sourceLabel=$sourceLabel, price=$price, yclose=$yclose, amt=$amt, chg=$chg, ok=$ok, deltaPct=$deltaPct]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.sourceKey != null) {
      json[r'source_key'] = this.sourceKey;
    } else {
      json[r'source_key'] = null;
    }
    if (this.sourceLabel != null) {
      json[r'source_label'] = this.sourceLabel;
    } else {
      json[r'source_label'] = null;
    }
    if (this.price != null) {
      json[r'price'] = this.price;
    } else {
      json[r'price'] = null;
    }
    if (this.yclose != null) {
      json[r'yclose'] = this.yclose;
    } else {
      json[r'yclose'] = null;
    }
    if (this.amt != null) {
      json[r'amt'] = this.amt;
    } else {
      json[r'amt'] = null;
    }
    if (this.chg != null) {
      json[r'chg'] = this.chg;
    } else {
      json[r'chg'] = null;
    }
    if (this.ok != null) {
      json[r'ok'] = this.ok;
    } else {
      json[r'ok'] = null;
    }
    if (this.deltaPct != null) {
      json[r'delta_pct'] = this.deltaPct;
    } else {
      json[r'delta_pct'] = null;
    }
    return json;
  }

  /// Returns a new [AdminPriceAlertSourceItem] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AdminPriceAlertSourceItem? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AdminPriceAlertSourceItem[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AdminPriceAlertSourceItem[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AdminPriceAlertSourceItem(
        sourceKey: mapValueOfType<String>(json, r'source_key'),
        sourceLabel: mapValueOfType<String>(json, r'source_label'),
        price: num.parse('${json[r'price']}'),
        yclose: num.parse('${json[r'yclose']}'),
        amt: num.parse('${json[r'amt']}'),
        chg: num.parse('${json[r'chg']}'),
        ok: mapValueOfType<bool>(json, r'ok'),
        deltaPct: num.parse('${json[r'delta_pct']}'),
      );
    }
    return null;
  }

  static List<AdminPriceAlertSourceItem> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AdminPriceAlertSourceItem>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AdminPriceAlertSourceItem.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AdminPriceAlertSourceItem> mapFromJson(dynamic json) {
    final map = <String, AdminPriceAlertSourceItem>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AdminPriceAlertSourceItem.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AdminPriceAlertSourceItem-objects as value to a dart map
  static Map<String, List<AdminPriceAlertSourceItem>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AdminPriceAlertSourceItem>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AdminPriceAlertSourceItem.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

