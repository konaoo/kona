//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class AddPortfolioAdjustmentEventRequest {
  /// Returns a new [AddPortfolioAdjustmentEventRequest] instance.
  AddPortfolioAdjustmentEventRequest({
    required this.code,
    required this.eventType,
    required this.amount,
    this.curr,
    this.note,
    this.requestId,
  });

  String code;

  AddPortfolioAdjustmentEventRequestEventTypeEnum eventType;

  num amount;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? curr;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? note;

  ///
  /// Please note: This property should have been non-nullable! Since the specification file
  /// does not include a default value (using the "default:" property), however, the generated
  /// source code must fall back to having a nullable type.
  /// Consider adding a "default:" property in the specification file to hide this note.
  ///
  String? requestId;

  @override
  bool operator ==(Object other) => identical(this, other) || other is AddPortfolioAdjustmentEventRequest &&
    other.code == code &&
    other.eventType == eventType &&
    other.amount == amount &&
    other.curr == curr &&
    other.note == note &&
    other.requestId == requestId;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (code.hashCode) +
    (eventType.hashCode) +
    (amount.hashCode) +
    (curr == null ? 0 : curr!.hashCode) +
    (note == null ? 0 : note!.hashCode) +
    (requestId == null ? 0 : requestId!.hashCode);

  @override
  String toString() => 'AddPortfolioAdjustmentEventRequest[code=$code, eventType=$eventType, amount=$amount, curr=$curr, note=$note, requestId=$requestId]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
      json[r'code'] = this.code;
      json[r'event_type'] = this.eventType;
      json[r'amount'] = this.amount;
    if (this.curr != null) {
      json[r'curr'] = this.curr;
    } else {
      json[r'curr'] = null;
    }
    if (this.note != null) {
      json[r'note'] = this.note;
    } else {
      json[r'note'] = null;
    }
    if (this.requestId != null) {
      json[r'request_id'] = this.requestId;
    } else {
      json[r'request_id'] = null;
    }
    return json;
  }

  /// Returns a new [AddPortfolioAdjustmentEventRequest] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static AddPortfolioAdjustmentEventRequest? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        requiredKeys.forEach((key) {
          assert(json.containsKey(key), 'Required key "AddPortfolioAdjustmentEventRequest[$key]" is missing from JSON.');
          assert(json[key] != null, 'Required key "AddPortfolioAdjustmentEventRequest[$key]" has a null value in JSON.');
        });
        return true;
      }());

      return AddPortfolioAdjustmentEventRequest(
        code: mapValueOfType<String>(json, r'code')!,
        eventType: AddPortfolioAdjustmentEventRequestEventTypeEnum.fromJson(json[r'event_type'])!,
        amount: num.parse('${json[r'amount']}'),
        curr: mapValueOfType<String>(json, r'curr'),
        note: mapValueOfType<String>(json, r'note'),
        requestId: mapValueOfType<String>(json, r'request_id'),
      );
    }
    return null;
  }

  static List<AddPortfolioAdjustmentEventRequest> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AddPortfolioAdjustmentEventRequest>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AddPortfolioAdjustmentEventRequest.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, AddPortfolioAdjustmentEventRequest> mapFromJson(dynamic json) {
    final map = <String, AddPortfolioAdjustmentEventRequest>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = AddPortfolioAdjustmentEventRequest.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of AddPortfolioAdjustmentEventRequest-objects as value to a dart map
  static Map<String, List<AddPortfolioAdjustmentEventRequest>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<AddPortfolioAdjustmentEventRequest>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = AddPortfolioAdjustmentEventRequest.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
    'code',
    'event_type',
    'amount',
  };
}


class AddPortfolioAdjustmentEventRequestEventTypeEnum {
  /// Instantiate a new enum with the provided [value].
  const AddPortfolioAdjustmentEventRequestEventTypeEnum._(this.value);

  /// The underlying value of this enum member.
  final String value;

  @override
  String toString() => value;

  String toJson() => value;

  static const dividend = AddPortfolioAdjustmentEventRequestEventTypeEnum._(r'dividend');
  static const fee = AddPortfolioAdjustmentEventRequestEventTypeEnum._(r'fee');
  static const tax = AddPortfolioAdjustmentEventRequestEventTypeEnum._(r'tax');

  /// List of all possible values in this [enum][AddPortfolioAdjustmentEventRequestEventTypeEnum].
  static const values = <AddPortfolioAdjustmentEventRequestEventTypeEnum>[
    dividend,
    fee,
    tax,
  ];

  static AddPortfolioAdjustmentEventRequestEventTypeEnum? fromJson(dynamic value) => AddPortfolioAdjustmentEventRequestEventTypeEnumTypeTransformer().decode(value);

  static List<AddPortfolioAdjustmentEventRequestEventTypeEnum> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <AddPortfolioAdjustmentEventRequestEventTypeEnum>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = AddPortfolioAdjustmentEventRequestEventTypeEnum.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }
}

/// Transformation class that can [encode] an instance of [AddPortfolioAdjustmentEventRequestEventTypeEnum] to String,
/// and [decode] dynamic data back to [AddPortfolioAdjustmentEventRequestEventTypeEnum].
class AddPortfolioAdjustmentEventRequestEventTypeEnumTypeTransformer {
  factory AddPortfolioAdjustmentEventRequestEventTypeEnumTypeTransformer() => _instance ??= const AddPortfolioAdjustmentEventRequestEventTypeEnumTypeTransformer._();

  const AddPortfolioAdjustmentEventRequestEventTypeEnumTypeTransformer._();

  String encode(AddPortfolioAdjustmentEventRequestEventTypeEnum data) => data.value;

  /// Decodes a [dynamic value][data] to a AddPortfolioAdjustmentEventRequestEventTypeEnum.
  ///
  /// If [allowNull] is true and the [dynamic value][data] cannot be decoded successfully,
  /// then null is returned. However, if [allowNull] is false and the [dynamic value][data]
  /// cannot be decoded successfully, then an [UnimplementedError] is thrown.
  ///
  /// The [allowNull] is very handy when an API changes and a new enum value is added or removed,
  /// and users are still using an old app with the old code.
  AddPortfolioAdjustmentEventRequestEventTypeEnum? decode(dynamic data, {bool allowNull = true}) {
    if (data != null) {
      switch (data) {
        case r'dividend': return AddPortfolioAdjustmentEventRequestEventTypeEnum.dividend;
        case r'fee': return AddPortfolioAdjustmentEventRequestEventTypeEnum.fee;
        case r'tax': return AddPortfolioAdjustmentEventRequestEventTypeEnum.tax;
        default:
          if (!allowNull) {
            throw ArgumentError('Unknown enum value to decode: $data');
          }
      }
    }
    return null;
  }

  /// Singleton [AddPortfolioAdjustmentEventRequestEventTypeEnumTypeTransformer] instance.
  static AddPortfolioAdjustmentEventRequestEventTypeEnumTypeTransformer? _instance;
}


