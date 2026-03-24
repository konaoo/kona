# kaka_openapi.model.AdminApiHealthResponse

## Load the model package
```dart
import 'package:kaka_openapi/api.dart';
```

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **String** |  | [optional] 
**serverTimeUtc** | **String** |  | [optional] 
**db** | [**AdminApiHealthResponseDb**](AdminApiHealthResponseDb.md) |  | [optional] 
**upstream** | [**Map<String, AdminUpstreamStatusItem>**](AdminUpstreamStatusItem.md) |  | [optional] [default to const {}]
**policies** | [**List<AdminPolicyItem>**](AdminPolicyItem.md) |  | [optional] [default to const []]
**runtime** | [**PriceRuntimeMetrics**](PriceRuntimeMetrics.md) |  | [optional] 
**sources** | [**Map<String, PriceSourceHealthItem>**](PriceSourceHealthItem.md) |  | [optional] [default to const {}]
**versionInfo** | [**AdminApiHealthResponseVersionInfo**](AdminApiHealthResponseVersionInfo.md) |  | [optional] 

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


