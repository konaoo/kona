//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AdminProviderTestItem {
  /// Returns a new [AdminProviderTestItem] instance.
  AdminProviderTestItem({
    this.name,
    this.code,
    this.assetType,
    this.ok,
    this.status,
    this.price,
    this.yclose,
    this.change,
    this.changePct,
    this.rate,
    this.latencyMs,
    this.detail,
  });

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? name;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? code;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? assetType;

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
  String? status;

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
  num? change;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? changePct;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  num? rate;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  int? latencyMs;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? detail;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AdminProviderTestItem &&
    other.name == name &&
    other.code == code &&
    other.assetType == assetType &&
    other.ok == ok &&
    other.status == status &&
    other.price == price &&
    other.yclose == yclose &&
    other.change == change &&
    other.changePct == changePct &&
    other.rate == rate &&
    other.latencyMs == latencyMs &&
    other.detail == detail;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (name == null ? 0 : name!.hashCode) +
    (code == null ? 0 : code!.hashCode) +
    (assetType == null ? 0 : assetType!.hashCode) +
    (ok == null ? 0 : ok!.hashCode) +
    (status == null ? 0 : status!.hashCode) +
    (price == null ? 0 : price!.hashCode) +
    (yclose == null ? 0 : yclose!.hashCode) +
    (change == null ? 0 : change!.hashCode) +
    (changePct == null ? 0 : changePct!.hashCode) +
    (rate == null ? 0 : rate!.hashCode) +
    (latencyMs == null ? 0 : latencyMs!.hashCode) +
    (detail == null ? 0 : detail!.hashCode);

  @override
  String toString() => 'AdminProviderTestItem[name=$name, code=$code, assetType=$assetType, ok=$ok, status=$status, price=$price, yclose=$yclose, change=$change, changePct=$changePct, rate=$rate, latencyMs=$latencyMs, detail=$detail]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.name != null) {
      json[r'name'] = this.name;
    } else {
      json[r'name'] = null;
    }
    if (this.code != null) {
      json[r'code'] = this.code;
    } else {
      json[r'code'] = null;
    }
    if (this.assetType != null) {
      json[r'asset_type'] = this.assetType;
    } else {
      json[r'asset_type'] = null;
    }
    if (this.ok != null) {
      json[r'ok'] = this.ok;
    } else {
      json[r'ok'] = null;
    }
    if (this.status != null) {
      json[r'status'] = this.status;
    } else {
      json[r'status'] = null;
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
    if (this.change != null) {
      json[r'change'] = this.change;
    } else {
      json[r'change'] = null;
    }
    if (this.changePct != null) {
      json[r'change_pct'] = this.changePct;
    } else {
      json[r'change_pct'] = null;
    }
    if (this.rate != null) {
      json[r'rate'] = this.rate;
    } else {
      json[r'rate'] = null;
    }
    if (this.latencyMs != null) {
      json[r'latency_ms'] = this.latencyMs;
    } else {
      json[r'latency_ms'] = null;
    }
    if (this.detail != null) {
      json[r'detail'] = this.detail;
    } else {
      json[r'detail'] = null;
    }
    return json;
  }

  /// Returns a new [AdminProviderTestItem] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AdminProviderTestItem? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AdminProviderTestItem[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AdminProviderTestItem[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AdminProviderTestItem(
        name: mapValueOfType<String>(json, r'name'),
        code: mapValueOfType<String>(json, r'code'),
        assetType: mapValueOfType<String>(json, r'asset_type'),
        ok: mapValueOfType<bool>(json, r'ok'),
        status: mapValueOfType<String>(json, r'status'),
        price: num.parse('${json[r'price']}'),
        yclose: num.parse('${json[r'yclose']}'),
        change: num.parse('${json[r'change']}'),
        changePct: num.parse('${json[r'change_pct']}'),
        rate: num.parse('${json[r'rate']}'),
        latencyMs: mapValueOfType<int>(json, r'latency_ms'),
        detail: mapValueOfType<String>(json, r'detail'),
      );
    }
    return null;
  }

  static List<AdminProviderTestItem> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AdminProviderTestItem>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AdminProviderTestItem.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AdminProviderTestItem> mapFromJson(dynamic json) {
    final map = <String, AdminProviderTestItem>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AdminProviderTestItem.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AdminProviderTestItem-objects as value to a dart map
  static Map<String, List<AdminProviderTestItem>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AdminProviderTestItem>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AdminProviderTestItem.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

