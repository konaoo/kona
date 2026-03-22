# kaka_openapi.model.AdminConfigItem

## Load the model package
```dart
import 'package:kaka_openapi/api.dart';
```

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**key** | **String** |  | [optional] 
**displayName** | **String** |  | [optional] 
**value** | **String** | 配置当前值，服务端真实值可能是字符串、数字或布尔，这里统一按字符串描述以兼容类型生成 | [optional] 
**defaultValue** | **String** | 配置默认值，服务端真实值可能是字符串、数字或布尔，这里统一按字符串描述以兼容类型生成 | [optional] 
**type** | **String** |  | [optional] 
**description** | **String** |  | [optional] 
**min** | **num** |  | [optional] 
**max** | **num** |  | [optional] 
**choices** | **List<String>** |  | [optional] [default to const []]
**recommended** | **String** |  | [optional] 

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


