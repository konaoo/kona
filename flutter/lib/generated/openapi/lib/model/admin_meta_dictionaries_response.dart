//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AdminMetaDictionariesResponse {
  /// Returns a new [AdminMetaDictionariesResponse] instance.
  AdminMetaDictionariesResponse({
    this.statusLabels = const {},
    this.actionLabels = const {},
    this.policyLabels = const {},
    this.policyImpacts = const {},
    this.policyTypeLabels = const {},
    this.registerMethodLabels = const {},
    this.errorLabels = const {},
    this.configLabels = const {},
  });

  Map<String, String> statusLabels;

  Map<String, String> actionLabels;

  Map<String, String> policyLabels;

  Map<String, String> policyImpacts;

  Map<String, String> policyTypeLabels;

  Map<String, String> registerMethodLabels;

  Map<String, String> errorLabels;

  Map<String, String> configLabels;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AdminMetaDictionariesResponse &&
    _deepEquality.equals(other.statusLabels, statusLabels) &&
    _deepEquality.equals(other.actionLabels, actionLabels) &&
    _deepEquality.equals(other.policyLabels, policyLabels) &&
    _deepEquality.equals(other.policyImpacts, policyImpacts) &&
    _deepEquality.equals(other.policyTypeLabels, policyTypeLabels) &&
    _deepEquality.equals(other.registerMethodLabels, registerMethodLabels) &&
    _deepEquality.equals(other.errorLabels, errorLabels) &&
    _deepEquality.equals(other.configLabels, configLabels);

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (statusLabels.hashCode) +
    (actionLabels.hashCode) +
    (policyLabels.hashCode) +
    (policyImpacts.hashCode) +
    (policyTypeLabels.hashCode) +
    (registerMethodLabels.hashCode) +
    (errorLabels.hashCode) +
    (configLabels.hashCode);

  @override
  String toString() => 'AdminMetaDictionariesResponse[statusLabels=$statusLabels, actionLabels=$actionLabels, policyLabels=$policyLabels, policyImpacts=$policyImpacts, policyTypeLabels=$policyTypeLabels, registerMethodLabels=$registerMethodLabels, errorLabels=$errorLabels, configLabels=$configLabels]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
      json[r'status_labels'] = this.statusLabels;
      json[r'action_labels'] = this.actionLabels;
      json[r'policy_labels'] = this.policyLabels;
      json[r'policy_impacts'] = this.policyImpacts;
      json[r'policy_type_labels'] = this.policyTypeLabels;
      json[r'register_method_labels'] = this.registerMethodLabels;
      json[r'error_labels'] = this.errorLabels;
      json[r'config_labels'] = this.configLabels;
    return json;
  }

  /// Returns a new [AdminMetaDictionariesResponse] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AdminMetaDictionariesResponse? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AdminMetaDictionariesResponse[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AdminMetaDictionariesResponse[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AdminMetaDictionariesResponse(
        statusLabels: mapCastOfType<String, String>(json, r'status_labels') ?? const {},
        actionLabels: mapCastOfType<String, String>(json, r'action_labels') ?? const {},
        policyLabels: mapCastOfType<String, String>(json, r'policy_labels') ?? const {},
        policyImpacts: mapCastOfType<String, String>(json, r'policy_impacts') ?? const {},
        policyTypeLabels: mapCastOfType<String, String>(json, r'policy_type_labels') ?? const {},
        registerMethodLabels: mapCastOfType<String, String>(json, r'register_method_labels') ?? const {},
        errorLabels: mapCastOfType<String, String>(json, r'error_labels') ?? const {},
        configLabels: mapCastOfType<String, String>(json, r'config_labels') ?? const {},
      );
    }
    return null;
  }

  static List<AdminMetaDictionariesResponse> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AdminMetaDictionariesResponse>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AdminMetaDictionariesResponse.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AdminMetaDictionariesResponse> mapFromJson(dynamic json) {
    final map = <String, AdminMetaDictionariesResponse>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AdminMetaDictionariesResponse.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AdminMetaDictionariesResponse-objects as value to a dart map
  static Map<String, List<AdminMetaDictionariesResponse>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AdminMetaDictionariesResponse>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AdminMetaDictionariesResponse.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
  };
}

