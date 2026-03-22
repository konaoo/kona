//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;


class DefaultApi {
  DefaultApi([ApiClient? apiClient]) : apiClient = apiClient ?? defaultApiClient;

  final ApiClient apiClient;

  /// Add cash asset
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [AddCashAssetRequest] addCashAssetRequest (required):
  Future<Response> addCashAssetWithHttpInfo(AddCashAssetRequest addCashAssetRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/cash_assets/add';

    // ignore: prefer_final_locals
    Object? postBody = addCashAssetRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Add cash asset
  ///
  /// Parameters:
  ///
  /// * [AddCashAssetRequest] addCashAssetRequest (required):
  Future<StatusOk?> addCashAsset(AddCashAssetRequest addCashAssetRequest,) async {
    final response = await addCashAssetWithHttpInfo(addCashAssetRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'StatusOk',) as StatusOk;
    
    }
    return null;
  }

  /// Add liability
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [AddCashAssetRequest] addCashAssetRequest (required):
  Future<Response> addLiabilityWithHttpInfo(AddCashAssetRequest addCashAssetRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/liabilities/add';

    // ignore: prefer_final_locals
    Object? postBody = addCashAssetRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Add liability
  ///
  /// Parameters:
  ///
  /// * [AddCashAssetRequest] addCashAssetRequest (required):
  Future<StatusOk?> addLiability(AddCashAssetRequest addCashAssetRequest,) async {
    final response = await addLiabilityWithHttpInfo(addCashAssetRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'StatusOk',) as StatusOk;
    
    }
    return null;
  }

  /// Add other asset
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [AddCashAssetRequest] addCashAssetRequest (required):
  Future<Response> addOtherAssetWithHttpInfo(AddCashAssetRequest addCashAssetRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/other_assets/add';

    // ignore: prefer_final_locals
    Object? postBody = addCashAssetRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Add other asset
  ///
  /// Parameters:
  ///
  /// * [AddCashAssetRequest] addCashAssetRequest (required):
  Future<StatusOk?> addOtherAsset(AddCashAssetRequest addCashAssetRequest,) async {
    final response = await addOtherAssetWithHttpInfo(addCashAssetRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'StatusOk',) as StatusOk;
    
    }
    return null;
  }

  /// Add portfolio cash event
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [AddPortfolioAdjustmentEventRequest] addPortfolioAdjustmentEventRequest (required):
  Future<Response> addPortfolioAdjustmentEventWithHttpInfo(AddPortfolioAdjustmentEventRequest addPortfolioAdjustmentEventRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/portfolio/adjustment_event';

    // ignore: prefer_final_locals
    Object? postBody = addPortfolioAdjustmentEventRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Add portfolio cash event
  ///
  /// Parameters:
  ///
  /// * [AddPortfolioAdjustmentEventRequest] addPortfolioAdjustmentEventRequest (required):
  Future<StatusOk?> addPortfolioAdjustmentEvent(AddPortfolioAdjustmentEventRequest addPortfolioAdjustmentEventRequest,) async {
    final response = await addPortfolioAdjustmentEventWithHttpInfo(addPortfolioAdjustmentEventRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'StatusOk',) as StatusOk;
    
    }
    return null;
  }

  /// Add asset
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [AddPortfolioAssetRequest] addPortfolioAssetRequest (required):
  Future<Response> addPortfolioAssetWithHttpInfo(AddPortfolioAssetRequest addPortfolioAssetRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/portfolio/add';

    // ignore: prefer_final_locals
    Object? postBody = addPortfolioAssetRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Add asset
  ///
  /// Parameters:
  ///
  /// * [AddPortfolioAssetRequest] addPortfolioAssetRequest (required):
  Future<StatusOk?> addPortfolioAsset(AddPortfolioAssetRequest addPortfolioAssetRequest,) async {
    final response = await addPortfolioAssetWithHttpInfo(addPortfolioAssetRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'StatusOk',) as StatusOk;
    
    }
    return null;
  }

  /// 后台接口健康与策略汇总
  ///
  /// Note: This method returns the HTTP [Response].
  Future<Response> apiAdminApisHealthGetWithHttpInfo() async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/apis/health';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 后台接口健康与策略汇总
  Future<AdminApiHealthResponse?> apiAdminApisHealthGet() async {
    final response = await apiAdminApisHealthGetWithHttpInfo();
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminApiHealthResponse',) as AdminApiHealthResponse;
    
    }
    return null;
  }

  /// 批量更新后台接口策略
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [AdminPolicyBatchUpdateRequest] adminPolicyBatchUpdateRequest (required):
  Future<Response> apiAdminApisPoliciesBatchUpdatePostWithHttpInfo(AdminPolicyBatchUpdateRequest adminPolicyBatchUpdateRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/apis/policies/batch_update';

    // ignore: prefer_final_locals
    Object? postBody = adminPolicyBatchUpdateRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 批量更新后台接口策略
  ///
  /// Parameters:
  ///
  /// * [AdminPolicyBatchUpdateRequest] adminPolicyBatchUpdateRequest (required):
  Future<AdminPolicyBatchUpdateResponse?> apiAdminApisPoliciesBatchUpdatePost(AdminPolicyBatchUpdateRequest adminPolicyBatchUpdateRequest,) async {
    final response = await apiAdminApisPoliciesBatchUpdatePostWithHttpInfo(adminPolicyBatchUpdateRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminPolicyBatchUpdateResponse',) as AdminPolicyBatchUpdateResponse;
    
    }
    return null;
  }

  /// 后台接口策略列表
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] scopeType:
  Future<Response> apiAdminApisPoliciesGetWithHttpInfo({ String? scopeType, }) async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/apis/policies';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    if (scopeType != null) {
      queryParams.addAll(_queryParams('', 'scope_type', scopeType));
    }

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 后台接口策略列表
  ///
  /// Parameters:
  ///
  /// * [String] scopeType:
  Future<AdminPoliciesResponse?> apiAdminApisPoliciesGet({ String? scopeType, }) async {
    final response = await apiAdminApisPoliciesGetWithHttpInfo( scopeType: scopeType, );
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminPoliciesResponse',) as AdminPoliciesResponse;
    
    }
    return null;
  }

  /// 更新单条后台接口策略
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [AdminPolicyUpdateRequest] adminPolicyUpdateRequest (required):
  Future<Response> apiAdminApisPoliciesUpdatePostWithHttpInfo(AdminPolicyUpdateRequest adminPolicyUpdateRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/apis/policies/update';

    // ignore: prefer_final_locals
    Object? postBody = adminPolicyUpdateRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 更新单条后台接口策略
  ///
  /// Parameters:
  ///
  /// * [AdminPolicyUpdateRequest] adminPolicyUpdateRequest (required):
  Future<AdminPolicyUpdateResponse?> apiAdminApisPoliciesUpdatePost(AdminPolicyUpdateRequest adminPolicyUpdateRequest,) async {
    final response = await apiAdminApisPoliciesUpdatePostWithHttpInfo(adminPolicyUpdateRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminPolicyUpdateResponse',) as AdminPolicyUpdateResponse;
    
    }
    return null;
  }

  /// 行情价格告警与历史快照
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [bool] force:
  Future<Response> apiAdminApisPriceAlertsGetWithHttpInfo({ bool? force, }) async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/apis/price_alerts';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    if (force != null) {
      queryParams.addAll(_queryParams('', 'force', force));
    }

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 行情价格告警与历史快照
  ///
  /// Parameters:
  ///
  /// * [bool] force:
  Future<AdminPriceAlertsResponse?> apiAdminApisPriceAlertsGet({ bool? force, }) async {
    final response = await apiAdminApisPriceAlertsGetWithHttpInfo( force: force, );
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminPriceAlertsResponse',) as AdminPriceAlertsResponse;
    
    }
    return null;
  }

  /// 单资产价格诊断
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [AdminPriceProbeRequest] adminPriceProbeRequest (required):
  Future<Response> apiAdminApisPriceProbePostWithHttpInfo(AdminPriceProbeRequest adminPriceProbeRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/apis/price_probe';

    // ignore: prefer_final_locals
    Object? postBody = adminPriceProbeRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 单资产价格诊断
  ///
  /// Parameters:
  ///
  /// * [AdminPriceProbeRequest] adminPriceProbeRequest (required):
  Future<AdminPriceProbeResponse?> apiAdminApisPriceProbePost(AdminPriceProbeRequest adminPriceProbeRequest,) async {
    final response = await apiAdminApisPriceProbePostWithHttpInfo(adminPriceProbeRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminPriceProbeResponse',) as AdminPriceProbeResponse;
    
    }
    return null;
  }

  /// 单个行情/汇率源测试
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [ApiAdminApisProviderTestPostRequest] apiAdminApisProviderTestPostRequest (required):
  Future<Response> apiAdminApisProviderTestPostWithHttpInfo(ApiAdminApisProviderTestPostRequest apiAdminApisProviderTestPostRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/apis/provider_test';

    // ignore: prefer_final_locals
    Object? postBody = apiAdminApisProviderTestPostRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 单个行情/汇率源测试
  ///
  /// Parameters:
  ///
  /// * [ApiAdminApisProviderTestPostRequest] apiAdminApisProviderTestPostRequest (required):
  Future<AdminProviderTestResponse?> apiAdminApisProviderTestPost(ApiAdminApisProviderTestPostRequest apiAdminApisProviderTestPostRequest,) async {
    final response = await apiAdminApisProviderTestPostWithHttpInfo(apiAdminApisProviderTestPostRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminProviderTestResponse',) as AdminProviderTestResponse;
    
    }
    return null;
  }

  /// 最近一次行情源测试报告
  ///
  /// Note: This method returns the HTTP [Response].
  Future<Response> apiAdminApisProviderTestsLatestGetWithHttpInfo() async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/apis/provider_tests/latest';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 最近一次行情源测试报告
  Future<AdminProviderTestReport?> apiAdminApisProviderTestsLatestGet() async {
    final response = await apiAdminApisProviderTestsLatestGetWithHttpInfo();
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminProviderTestReport',) as AdminProviderTestReport;
    
    }
    return null;
  }

  /// 运行行情源测试并保存报告
  ///
  /// Note: This method returns the HTTP [Response].
  Future<Response> apiAdminApisProviderTestsRunPostWithHttpInfo() async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/apis/provider_tests/run';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 运行行情源测试并保存报告
  Future<AdminProviderTestReportRun?> apiAdminApisProviderTestsRunPost() async {
    final response = await apiAdminApisProviderTestsRunPostWithHttpInfo();
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminProviderTestReportRun',) as AdminProviderTestReportRun;
    
    }
    return null;
  }

  /// 后台冒烟测试
  ///
  /// Note: This method returns the HTTP [Response].
  Future<Response> apiAdminApisSmokeTestPostWithHttpInfo() async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/apis/smoke_test';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 后台冒烟测试
  Future<AdminSmokeTestResponse?> apiAdminApisSmokeTestPost() async {
    final response = await apiAdminApisSmokeTestPostWithHttpInfo();
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminSmokeTestResponse',) as AdminSmokeTestResponse;
    
    }
    return null;
  }

  /// 后台系统配置白名单
  ///
  /// Note: This method returns the HTTP [Response].
  Future<Response> apiAdminConfigGetWithHttpInfo() async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/config';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 后台系统配置白名单
  Future<AdminConfigListResponse?> apiAdminConfigGet() async {
    final response = await apiAdminConfigGetWithHttpInfo();
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminConfigListResponse',) as AdminConfigListResponse;
    
    }
    return null;
  }

  /// 恢复系统配置默认值
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [ApiAdminConfigResetPostRequest] apiAdminConfigResetPostRequest:
  Future<Response> apiAdminConfigResetPostWithHttpInfo({ ApiAdminConfigResetPostRequest? apiAdminConfigResetPostRequest, }) async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/config/reset';

    // ignore: prefer_final_locals
    Object? postBody = apiAdminConfigResetPostRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 恢复系统配置默认值
  ///
  /// Parameters:
  ///
  /// * [ApiAdminConfigResetPostRequest] apiAdminConfigResetPostRequest:
  Future<AdminConfigUpdateResponse?> apiAdminConfigResetPost({ ApiAdminConfigResetPostRequest? apiAdminConfigResetPostRequest, }) async {
    final response = await apiAdminConfigResetPostWithHttpInfo( apiAdminConfigResetPostRequest: apiAdminConfigResetPostRequest, );
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminConfigUpdateResponse',) as AdminConfigUpdateResponse;
    
    }
    return null;
  }

  /// 更新系统配置
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [AdminConfigUpdateRequest] adminConfigUpdateRequest (required):
  Future<Response> apiAdminConfigUpdatePostWithHttpInfo(AdminConfigUpdateRequest adminConfigUpdateRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/config/update';

    // ignore: prefer_final_locals
    Object? postBody = adminConfigUpdateRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 更新系统配置
  ///
  /// Parameters:
  ///
  /// * [AdminConfigUpdateRequest] adminConfigUpdateRequest (required):
  Future<AdminConfigUpdateResponse?> apiAdminConfigUpdatePost(AdminConfigUpdateRequest adminConfigUpdateRequest,) async {
    final response = await apiAdminConfigUpdatePostWithHttpInfo(adminConfigUpdateRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminConfigUpdateResponse',) as AdminConfigUpdateResponse;
    
    }
    return null;
  }

  /// 获取最近一次备份信息
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] backupDir:
  Future<Response> apiAdminDataBackupLatestGetWithHttpInfo({ String? backupDir, }) async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/data/backup/latest';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    if (backupDir != null) {
      queryParams.addAll(_queryParams('', 'backup_dir', backupDir));
    }

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 获取最近一次备份信息
  ///
  /// Parameters:
  ///
  /// * [String] backupDir:
  Future<AdminBackupLatestResponse?> apiAdminDataBackupLatestGet({ String? backupDir, }) async {
    final response = await apiAdminDataBackupLatestGetWithHttpInfo( backupDir: backupDir, );
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminBackupLatestResponse',) as AdminBackupLatestResponse;
    
    }
    return null;
  }

  /// 创建数据库备份
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [AdminBackupRequest] adminBackupRequest:
  Future<Response> apiAdminDataBackupPostWithHttpInfo({ AdminBackupRequest? adminBackupRequest, }) async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/data/backup';

    // ignore: prefer_final_locals
    Object? postBody = adminBackupRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 创建数据库备份
  ///
  /// Parameters:
  ///
  /// * [AdminBackupRequest] adminBackupRequest:
  Future<AdminBackupResponse?> apiAdminDataBackupPost({ AdminBackupRequest? adminBackupRequest, }) async {
    final response = await apiAdminDataBackupPostWithHttpInfo( adminBackupRequest: adminBackupRequest, );
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminBackupResponse',) as AdminBackupResponse;
    
    }
    return null;
  }

  /// 执行历史数据归属迁移
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [ApiAdminDataRebindExecutePostRequest] apiAdminDataRebindExecutePostRequest (required):
  Future<Response> apiAdminDataRebindExecutePostWithHttpInfo(ApiAdminDataRebindExecutePostRequest apiAdminDataRebindExecutePostRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/data/rebind/execute';

    // ignore: prefer_final_locals
    Object? postBody = apiAdminDataRebindExecutePostRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 执行历史数据归属迁移
  ///
  /// Parameters:
  ///
  /// * [ApiAdminDataRebindExecutePostRequest] apiAdminDataRebindExecutePostRequest (required):
  Future<AdminRebindExecuteResponse?> apiAdminDataRebindExecutePost(ApiAdminDataRebindExecutePostRequest apiAdminDataRebindExecutePostRequest,) async {
    final response = await apiAdminDataRebindExecutePostWithHttpInfo(apiAdminDataRebindExecutePostRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminRebindExecuteResponse',) as AdminRebindExecuteResponse;
    
    }
    return null;
  }

  /// 预览历史数据归属迁移
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] targetUserId (required):
  Future<Response> apiAdminDataRebindPreviewGetWithHttpInfo(String targetUserId,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/data/rebind/preview';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

      queryParams.addAll(_queryParams('', 'target_user_id', targetUserId));

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 预览历史数据归属迁移
  ///
  /// Parameters:
  ///
  /// * [String] targetUserId (required):
  Future<AdminRebindPreviewResponse?> apiAdminDataRebindPreviewGet(String targetUserId,) async {
    final response = await apiAdminDataRebindPreviewGetWithHttpInfo(targetUserId,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminRebindPreviewResponse',) as AdminRebindPreviewResponse;
    
    }
    return null;
  }

  /// 恢复数据库备份
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [AdminRestoreRequest] adminRestoreRequest:
  Future<Response> apiAdminDataRestorePostWithHttpInfo({ AdminRestoreRequest? adminRestoreRequest, }) async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/data/restore';

    // ignore: prefer_final_locals
    Object? postBody = adminRestoreRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 恢复数据库备份
  ///
  /// Parameters:
  ///
  /// * [AdminRestoreRequest] adminRestoreRequest:
  Future<AdminRestoreResponse?> apiAdminDataRestorePost({ AdminRestoreRequest? adminRestoreRequest, }) async {
    final response = await apiAdminDataRestorePostWithHttpInfo( adminRestoreRequest: adminRestoreRequest, );
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminRestoreResponse',) as AdminRestoreResponse;
    
    }
    return null;
  }

  /// 清理休市日快照日盈亏
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [ApiAdminDataSnapshotCleanupMarketClosedPostRequest] apiAdminDataSnapshotCleanupMarketClosedPostRequest:
  Future<Response> apiAdminDataSnapshotCleanupMarketClosedPostWithHttpInfo({ ApiAdminDataSnapshotCleanupMarketClosedPostRequest? apiAdminDataSnapshotCleanupMarketClosedPostRequest, }) async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/data/snapshot/cleanup_market_closed';

    // ignore: prefer_final_locals
    Object? postBody = apiAdminDataSnapshotCleanupMarketClosedPostRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 清理休市日快照日盈亏
  ///
  /// Parameters:
  ///
  /// * [ApiAdminDataSnapshotCleanupMarketClosedPostRequest] apiAdminDataSnapshotCleanupMarketClosedPostRequest:
  Future<AdminSnapshotCleanupResponse?> apiAdminDataSnapshotCleanupMarketClosedPost({ ApiAdminDataSnapshotCleanupMarketClosedPostRequest? apiAdminDataSnapshotCleanupMarketClosedPostRequest, }) async {
    final response = await apiAdminDataSnapshotCleanupMarketClosedPostWithHttpInfo( apiAdminDataSnapshotCleanupMarketClosedPostRequest: apiAdminDataSnapshotCleanupMarketClosedPostRequest, );
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminSnapshotCleanupResponse',) as AdminSnapshotCleanupResponse;
    
    }
    return null;
  }

  /// 预览休市日清理影响范围
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [ApiAdminDataSnapshotCleanupMarketClosedPreviewPostRequest] apiAdminDataSnapshotCleanupMarketClosedPreviewPostRequest:
  Future<Response> apiAdminDataSnapshotCleanupMarketClosedPreviewPostWithHttpInfo({ ApiAdminDataSnapshotCleanupMarketClosedPreviewPostRequest? apiAdminDataSnapshotCleanupMarketClosedPreviewPostRequest, }) async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/data/snapshot/cleanup_market_closed/preview';

    // ignore: prefer_final_locals
    Object? postBody = apiAdminDataSnapshotCleanupMarketClosedPreviewPostRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 预览休市日清理影响范围
  ///
  /// Parameters:
  ///
  /// * [ApiAdminDataSnapshotCleanupMarketClosedPreviewPostRequest] apiAdminDataSnapshotCleanupMarketClosedPreviewPostRequest:
  Future<AdminSnapshotCleanupPreviewResponse?> apiAdminDataSnapshotCleanupMarketClosedPreviewPost({ ApiAdminDataSnapshotCleanupMarketClosedPreviewPostRequest? apiAdminDataSnapshotCleanupMarketClosedPreviewPostRequest, }) async {
    final response = await apiAdminDataSnapshotCleanupMarketClosedPreviewPostWithHttpInfo( apiAdminDataSnapshotCleanupMarketClosedPreviewPostRequest: apiAdminDataSnapshotCleanupMarketClosedPreviewPostRequest, );
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminSnapshotCleanupPreviewResponse',) as AdminSnapshotCleanupPreviewResponse;
    
    }
    return null;
  }

  /// 清理周末快照日盈亏
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [ApiAdminDataSnapshotCleanupWeekendPostRequest] apiAdminDataSnapshotCleanupWeekendPostRequest:
  Future<Response> apiAdminDataSnapshotCleanupWeekendPostWithHttpInfo({ ApiAdminDataSnapshotCleanupWeekendPostRequest? apiAdminDataSnapshotCleanupWeekendPostRequest, }) async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/data/snapshot/cleanup_weekend';

    // ignore: prefer_final_locals
    Object? postBody = apiAdminDataSnapshotCleanupWeekendPostRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 清理周末快照日盈亏
  ///
  /// Parameters:
  ///
  /// * [ApiAdminDataSnapshotCleanupWeekendPostRequest] apiAdminDataSnapshotCleanupWeekendPostRequest:
  Future<AdminSnapshotCleanupResponse?> apiAdminDataSnapshotCleanupWeekendPost({ ApiAdminDataSnapshotCleanupWeekendPostRequest? apiAdminDataSnapshotCleanupWeekendPostRequest, }) async {
    final response = await apiAdminDataSnapshotCleanupWeekendPostWithHttpInfo( apiAdminDataSnapshotCleanupWeekendPostRequest: apiAdminDataSnapshotCleanupWeekendPostRequest, );
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminSnapshotCleanupResponse',) as AdminSnapshotCleanupResponse;
    
    }
    return null;
  }

  /// 预览周末清理影响范围
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [ApiAdminDataSnapshotCleanupWeekendPostRequest] apiAdminDataSnapshotCleanupWeekendPostRequest:
  Future<Response> apiAdminDataSnapshotCleanupWeekendPreviewPostWithHttpInfo({ ApiAdminDataSnapshotCleanupWeekendPostRequest? apiAdminDataSnapshotCleanupWeekendPostRequest, }) async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/data/snapshot/cleanup_weekend/preview';

    // ignore: prefer_final_locals
    Object? postBody = apiAdminDataSnapshotCleanupWeekendPostRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 预览周末清理影响范围
  ///
  /// Parameters:
  ///
  /// * [ApiAdminDataSnapshotCleanupWeekendPostRequest] apiAdminDataSnapshotCleanupWeekendPostRequest:
  Future<AdminSnapshotCleanupPreviewResponse?> apiAdminDataSnapshotCleanupWeekendPreviewPost({ ApiAdminDataSnapshotCleanupWeekendPostRequest? apiAdminDataSnapshotCleanupWeekendPostRequest, }) async {
    final response = await apiAdminDataSnapshotCleanupWeekendPreviewPostWithHttpInfo( apiAdminDataSnapshotCleanupWeekendPostRequest: apiAdminDataSnapshotCleanupWeekendPostRequest, );
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminSnapshotCleanupPreviewResponse',) as AdminSnapshotCleanupPreviewResponse;
    
    }
    return null;
  }

  /// 快照任务健康检查
  ///
  /// Note: This method returns the HTTP [Response].
  Future<Response> apiAdminDataSnapshotHealthGetWithHttpInfo() async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/data/snapshot/health';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 快照任务健康检查
  Future<AdminSnapshotHealthResponse?> apiAdminDataSnapshotHealthGet() async {
    final response = await apiAdminDataSnapshotHealthGetWithHttpInfo();
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminSnapshotHealthResponse',) as AdminSnapshotHealthResponse;
    
    }
    return null;
  }

  /// 手动触发快照
  ///
  /// Note: This method returns the HTTP [Response].
  Future<Response> apiAdminDataSnapshotTriggerPostWithHttpInfo() async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/data/snapshot/trigger';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 手动触发快照
  Future<ApiSnapshotTriggerPost200Response?> apiAdminDataSnapshotTriggerPost() async {
    final response = await apiAdminDataSnapshotTriggerPostWithHttpInfo();
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'ApiSnapshotTriggerPost200Response',) as ApiSnapshotTriggerPost200Response;
    
    }
    return null;
  }

  /// 查询快照明细
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] userId:
  ///
  /// * [String] startDate:
  ///
  /// * [String] endDate:
  ///
  /// * [int] limit:
  ///
  /// * [int] offset:
  Future<Response> apiAdminDataSnapshotsGetWithHttpInfo({ String? userId, String? startDate, String? endDate, int? limit, int? offset, }) async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/data/snapshots';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    if (userId != null) {
      queryParams.addAll(_queryParams('', 'user_id', userId));
    }
    if (startDate != null) {
      queryParams.addAll(_queryParams('', 'start_date', startDate));
    }
    if (endDate != null) {
      queryParams.addAll(_queryParams('', 'end_date', endDate));
    }
    if (limit != null) {
      queryParams.addAll(_queryParams('', 'limit', limit));
    }
    if (offset != null) {
      queryParams.addAll(_queryParams('', 'offset', offset));
    }

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 查询快照明细
  ///
  /// Parameters:
  ///
  /// * [String] userId:
  ///
  /// * [String] startDate:
  ///
  /// * [String] endDate:
  ///
  /// * [int] limit:
  ///
  /// * [int] offset:
  Future<AdminDataSnapshotsResponse?> apiAdminDataSnapshotsGet({ String? userId, String? startDate, String? endDate, int? limit, int? offset, }) async {
    final response = await apiAdminDataSnapshotsGetWithHttpInfo( userId: userId, startDate: startDate, endDate: endDate, limit: limit, offset: offset, );
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminDataSnapshotsResponse',) as AdminDataSnapshotsResponse;
    
    }
    return null;
  }

  /// 导出邀请码 CSV
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] status:
  ///
  /// * [String] batchId:
  Future<Response> apiAdminInvitesExportGetWithHttpInfo({ String? status, String? batchId, }) async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/invites/export';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    if (status != null) {
      queryParams.addAll(_queryParams('', 'status', status));
    }
    if (batchId != null) {
      queryParams.addAll(_queryParams('', 'batch_id', batchId));
    }

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 导出邀请码 CSV
  ///
  /// Parameters:
  ///
  /// * [String] status:
  ///
  /// * [String] batchId:
  Future<String?> apiAdminInvitesExportGet({ String? status, String? batchId, }) async {
    final response = await apiAdminInvitesExportGetWithHttpInfo( status: status, batchId: batchId, );
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'String',) as String;
    
    }
    return null;
  }

  /// 生成邀请码
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [AdminInvitesGenerateRequest] adminInvitesGenerateRequest (required):
  Future<Response> apiAdminInvitesGeneratePostWithHttpInfo(AdminInvitesGenerateRequest adminInvitesGenerateRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/invites/generate';

    // ignore: prefer_final_locals
    Object? postBody = adminInvitesGenerateRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 生成邀请码
  ///
  /// Parameters:
  ///
  /// * [AdminInvitesGenerateRequest] adminInvitesGenerateRequest (required):
  Future<AdminInvitesGenerateResponse?> apiAdminInvitesGeneratePost(AdminInvitesGenerateRequest adminInvitesGenerateRequest,) async {
    final response = await apiAdminInvitesGeneratePostWithHttpInfo(adminInvitesGenerateRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminInvitesGenerateResponse',) as AdminInvitesGenerateResponse;
    
    }
    return null;
  }

  /// 邀请码列表
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] status:
  ///
  /// * [String] batchId:
  ///
  /// * [int] limit:
  ///
  /// * [int] offset:
  ///
  /// * [String] random:
  Future<Response> apiAdminInvitesGetWithHttpInfo({ String? status, String? batchId, int? limit, int? offset, String? random, }) async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/invites';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    if (status != null) {
      queryParams.addAll(_queryParams('', 'status', status));
    }
    if (batchId != null) {
      queryParams.addAll(_queryParams('', 'batch_id', batchId));
    }
    if (limit != null) {
      queryParams.addAll(_queryParams('', 'limit', limit));
    }
    if (offset != null) {
      queryParams.addAll(_queryParams('', 'offset', offset));
    }
    if (random != null) {
      queryParams.addAll(_queryParams('', 'random', random));
    }

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 邀请码列表
  ///
  /// Parameters:
  ///
  /// * [String] status:
  ///
  /// * [String] batchId:
  ///
  /// * [int] limit:
  ///
  /// * [int] offset:
  ///
  /// * [String] random:
  Future<AdminInvitesListResponse?> apiAdminInvitesGet({ String? status, String? batchId, int? limit, int? offset, String? random, }) async {
    final response = await apiAdminInvitesGetWithHttpInfo( status: status, batchId: batchId, limit: limit, offset: offset, random: random, );
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminInvitesListResponse',) as AdminInvitesListResponse;
    
    }
    return null;
  }

  /// 作废邀请码
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [AdminInvitesRevokeRequest] adminInvitesRevokeRequest (required):
  Future<Response> apiAdminInvitesRevokePostWithHttpInfo(AdminInvitesRevokeRequest adminInvitesRevokeRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/invites/revoke';

    // ignore: prefer_final_locals
    Object? postBody = adminInvitesRevokeRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 作废邀请码
  ///
  /// Parameters:
  ///
  /// * [AdminInvitesRevokeRequest] adminInvitesRevokeRequest (required):
  Future<AdminInvitesRevokeResponse?> apiAdminInvitesRevokePost(AdminInvitesRevokeRequest adminInvitesRevokeRequest,) async {
    final response = await apiAdminInvitesRevokePostWithHttpInfo(adminInvitesRevokeRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminInvitesRevokeResponse',) as AdminInvitesRevokeResponse;
    
    }
    return null;
  }

  /// 邀请码统计
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] batchId:
  Future<Response> apiAdminInvitesStatsGetWithHttpInfo({ String? batchId, }) async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/invites/stats';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    if (batchId != null) {
      queryParams.addAll(_queryParams('', 'batch_id', batchId));
    }

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 邀请码统计
  ///
  /// Parameters:
  ///
  /// * [String] batchId:
  Future<AdminInvitesStatsResponse?> apiAdminInvitesStatsGet({ String? batchId, }) async {
    final response = await apiAdminInvitesStatsGetWithHttpInfo( batchId: batchId, );
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminInvitesStatsResponse',) as AdminInvitesStatsResponse;
    
    }
    return null;
  }

  /// 后台字典与标签
  ///
  /// Note: This method returns the HTTP [Response].
  Future<Response> apiAdminMetaDictionariesGetWithHttpInfo() async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/meta/dictionaries';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 后台字典与标签
  Future<AdminMetaDictionariesResponse?> apiAdminMetaDictionariesGet() async {
    final response = await apiAdminMetaDictionariesGetWithHttpInfo();
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminMetaDictionariesResponse',) as AdminMetaDictionariesResponse;
    
    }
    return null;
  }

  /// 运营配置-更新提示
  ///
  /// Note: This method returns the HTTP [Response].
  Future<Response> apiAdminOpsAppUpdateGetWithHttpInfo() async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/ops/app_update';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 运营配置-更新提示
  Future<AdminOpsAppUpdateResponse?> apiAdminOpsAppUpdateGet() async {
    final response = await apiAdminOpsAppUpdateGetWithHttpInfo();
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminOpsAppUpdateResponse',) as AdminOpsAppUpdateResponse;
    
    }
    return null;
  }

  /// 更新运营配置-更新提示
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [ApiAdminOpsAppUpdateUpdatePostRequest] apiAdminOpsAppUpdateUpdatePostRequest (required):
  Future<Response> apiAdminOpsAppUpdateUpdatePostWithHttpInfo(ApiAdminOpsAppUpdateUpdatePostRequest apiAdminOpsAppUpdateUpdatePostRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/ops/app_update/update';

    // ignore: prefer_final_locals
    Object? postBody = apiAdminOpsAppUpdateUpdatePostRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 更新运营配置-更新提示
  ///
  /// Parameters:
  ///
  /// * [ApiAdminOpsAppUpdateUpdatePostRequest] apiAdminOpsAppUpdateUpdatePostRequest (required):
  Future<AdminOpsAppUpdateUpdateResponse?> apiAdminOpsAppUpdateUpdatePost(ApiAdminOpsAppUpdateUpdatePostRequest apiAdminOpsAppUpdateUpdatePostRequest,) async {
    final response = await apiAdminOpsAppUpdateUpdatePostWithHttpInfo(apiAdminOpsAppUpdateUpdatePostRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminOpsAppUpdateUpdateResponse',) as AdminOpsAppUpdateUpdateResponse;
    
    }
    return null;
  }

  /// 运营配置-邀请码获取页
  ///
  /// Note: This method returns the HTTP [Response].
  Future<Response> apiAdminOpsInviteAcquireGetWithHttpInfo() async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/ops/invite_acquire';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 运营配置-邀请码获取页
  Future<AdminOpsTextImageResponse?> apiAdminOpsInviteAcquireGet() async {
    final response = await apiAdminOpsInviteAcquireGetWithHttpInfo();
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminOpsTextImageResponse',) as AdminOpsTextImageResponse;
    
    }
    return null;
  }

  /// 更新运营配置-邀请码获取页
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [ApiAdminOpsInviteAcquireUpdatePostRequest] apiAdminOpsInviteAcquireUpdatePostRequest (required):
  Future<Response> apiAdminOpsInviteAcquireUpdatePostWithHttpInfo(ApiAdminOpsInviteAcquireUpdatePostRequest apiAdminOpsInviteAcquireUpdatePostRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/ops/invite_acquire/update';

    // ignore: prefer_final_locals
    Object? postBody = apiAdminOpsInviteAcquireUpdatePostRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 更新运营配置-邀请码获取页
  ///
  /// Parameters:
  ///
  /// * [ApiAdminOpsInviteAcquireUpdatePostRequest] apiAdminOpsInviteAcquireUpdatePostRequest (required):
  Future<AdminOpsTextImageUpdateResponse?> apiAdminOpsInviteAcquireUpdatePost(ApiAdminOpsInviteAcquireUpdatePostRequest apiAdminOpsInviteAcquireUpdatePostRequest,) async {
    final response = await apiAdminOpsInviteAcquireUpdatePostWithHttpInfo(apiAdminOpsInviteAcquireUpdatePostRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminOpsTextImageUpdateResponse',) as AdminOpsTextImageUpdateResponse;
    
    }
    return null;
  }

  /// 运营配置-iOS 下载二维码
  ///
  /// Note: This method returns the HTTP [Response].
  Future<Response> apiAdminOpsIosQrGetWithHttpInfo() async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/ops/ios_qr';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 运营配置-iOS 下载二维码
  Future<AdminOpsTextImageResponse?> apiAdminOpsIosQrGet() async {
    final response = await apiAdminOpsIosQrGetWithHttpInfo();
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminOpsTextImageResponse',) as AdminOpsTextImageResponse;
    
    }
    return null;
  }

  /// 更新运营配置-iOS 下载二维码
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [ApiAdminOpsInviteAcquireUpdatePostRequest] apiAdminOpsInviteAcquireUpdatePostRequest (required):
  Future<Response> apiAdminOpsIosQrUpdatePostWithHttpInfo(ApiAdminOpsInviteAcquireUpdatePostRequest apiAdminOpsInviteAcquireUpdatePostRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/ops/ios_qr/update';

    // ignore: prefer_final_locals
    Object? postBody = apiAdminOpsInviteAcquireUpdatePostRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 更新运营配置-iOS 下载二维码
  ///
  /// Parameters:
  ///
  /// * [ApiAdminOpsInviteAcquireUpdatePostRequest] apiAdminOpsInviteAcquireUpdatePostRequest (required):
  Future<AdminOpsTextImageUpdateResponse?> apiAdminOpsIosQrUpdatePost(ApiAdminOpsInviteAcquireUpdatePostRequest apiAdminOpsInviteAcquireUpdatePostRequest,) async {
    final response = await apiAdminOpsIosQrUpdatePostWithHttpInfo(apiAdminOpsInviteAcquireUpdatePostRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminOpsTextImageUpdateResponse',) as AdminOpsTextImageUpdateResponse;
    
    }
    return null;
  }

  /// 运营配置-用户群页
  ///
  /// Note: This method returns the HTTP [Response].
  Future<Response> apiAdminOpsUserGroupGetWithHttpInfo() async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/ops/user_group';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 运营配置-用户群页
  Future<AdminOpsTextImageResponse?> apiAdminOpsUserGroupGet() async {
    final response = await apiAdminOpsUserGroupGetWithHttpInfo();
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminOpsTextImageResponse',) as AdminOpsTextImageResponse;
    
    }
    return null;
  }

  /// 更新运营配置-用户群页
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [ApiAdminOpsInviteAcquireUpdatePostRequest] apiAdminOpsInviteAcquireUpdatePostRequest (required):
  Future<Response> apiAdminOpsUserGroupUpdatePostWithHttpInfo(ApiAdminOpsInviteAcquireUpdatePostRequest apiAdminOpsInviteAcquireUpdatePostRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/ops/user_group/update';

    // ignore: prefer_final_locals
    Object? postBody = apiAdminOpsInviteAcquireUpdatePostRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 更新运营配置-用户群页
  ///
  /// Parameters:
  ///
  /// * [ApiAdminOpsInviteAcquireUpdatePostRequest] apiAdminOpsInviteAcquireUpdatePostRequest (required):
  Future<AdminOpsTextImageUpdateResponse?> apiAdminOpsUserGroupUpdatePost(ApiAdminOpsInviteAcquireUpdatePostRequest apiAdminOpsInviteAcquireUpdatePostRequest,) async {
    final response = await apiAdminOpsUserGroupUpdatePostWithHttpInfo(apiAdminOpsInviteAcquireUpdatePostRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminOpsTextImageUpdateResponse',) as AdminOpsTextImageUpdateResponse;
    
    }
    return null;
  }

  /// 后台概览看板
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [bool] force:
  Future<Response> apiAdminOverviewGetWithHttpInfo({ bool? force, }) async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/overview';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    if (force != null) {
      queryParams.addAll(_queryParams('', 'force', force));
    }

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 后台概览看板
  ///
  /// Parameters:
  ///
  /// * [bool] force:
  Future<AdminOverviewResponse?> apiAdminOverviewGet({ bool? force, }) async {
    final response = await apiAdminOverviewGetWithHttpInfo( force: force, );
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminOverviewResponse',) as AdminOverviewResponse;
    
    }
    return null;
  }

  /// 后台待办与巡检摘要
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [int] inviteThreshold:
  Future<Response> apiAdminSummaryTodoGetWithHttpInfo({ int? inviteThreshold, }) async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/summary/todo';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    if (inviteThreshold != null) {
      queryParams.addAll(_queryParams('', 'invite_threshold', inviteThreshold));
    }

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 后台待办与巡检摘要
  ///
  /// Parameters:
  ///
  /// * [int] inviteThreshold:
  Future<AdminSummaryTodoResponse?> apiAdminSummaryTodoGet({ int? inviteThreshold, }) async {
    final response = await apiAdminSummaryTodoGetWithHttpInfo( inviteThreshold: inviteThreshold, );
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminSummaryTodoResponse',) as AdminSummaryTodoResponse;
    
    }
    return null;
  }

  /// 停用用户
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [ApiAdminUsersDisablePostRequest] apiAdminUsersDisablePostRequest (required):
  Future<Response> apiAdminUsersDisablePostWithHttpInfo(ApiAdminUsersDisablePostRequest apiAdminUsersDisablePostRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/users/disable';

    // ignore: prefer_final_locals
    Object? postBody = apiAdminUsersDisablePostRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 停用用户
  ///
  /// Parameters:
  ///
  /// * [ApiAdminUsersDisablePostRequest] apiAdminUsersDisablePostRequest (required):
  Future<AdminUserStatusResponse?> apiAdminUsersDisablePost(ApiAdminUsersDisablePostRequest apiAdminUsersDisablePostRequest,) async {
    final response = await apiAdminUsersDisablePostWithHttpInfo(apiAdminUsersDisablePostRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminUserStatusResponse',) as AdminUserStatusResponse;
    
    }
    return null;
  }

  /// 启用用户
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [ApiAdminUsersDisablePostRequest] apiAdminUsersDisablePostRequest (required):
  Future<Response> apiAdminUsersEnablePostWithHttpInfo(ApiAdminUsersDisablePostRequest apiAdminUsersDisablePostRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/users/enable';

    // ignore: prefer_final_locals
    Object? postBody = apiAdminUsersDisablePostRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 启用用户
  ///
  /// Parameters:
  ///
  /// * [ApiAdminUsersDisablePostRequest] apiAdminUsersDisablePostRequest (required):
  Future<AdminUserStatusResponse?> apiAdminUsersEnablePost(ApiAdminUsersDisablePostRequest apiAdminUsersDisablePostRequest,) async {
    final response = await apiAdminUsersEnablePostWithHttpInfo(apiAdminUsersDisablePostRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminUserStatusResponse',) as AdminUserStatusResponse;
    
    }
    return null;
  }

  /// 后台用户列表
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] q:
  ///
  /// * [String] status:
  ///
  /// * [String] sortBy:
  ///
  /// * [String] sortDir:
  ///
  /// * [bool] includeLocal:
  ///
  /// * [int] limit:
  ///
  /// * [int] offset:
  ///
  /// * [bool] force:
  Future<Response> apiAdminUsersGetWithHttpInfo({ String? q, String? status, String? sortBy, String? sortDir, bool? includeLocal, int? limit, int? offset, bool? force, }) async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/users';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    if (q != null) {
      queryParams.addAll(_queryParams('', 'q', q));
    }
    if (status != null) {
      queryParams.addAll(_queryParams('', 'status', status));
    }
    if (sortBy != null) {
      queryParams.addAll(_queryParams('', 'sort_by', sortBy));
    }
    if (sortDir != null) {
      queryParams.addAll(_queryParams('', 'sort_dir', sortDir));
    }
    if (includeLocal != null) {
      queryParams.addAll(_queryParams('', 'include_local', includeLocal));
    }
    if (limit != null) {
      queryParams.addAll(_queryParams('', 'limit', limit));
    }
    if (offset != null) {
      queryParams.addAll(_queryParams('', 'offset', offset));
    }
    if (force != null) {
      queryParams.addAll(_queryParams('', 'force', force));
    }

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 后台用户列表
  ///
  /// Parameters:
  ///
  /// * [String] q:
  ///
  /// * [String] status:
  ///
  /// * [String] sortBy:
  ///
  /// * [String] sortDir:
  ///
  /// * [bool] includeLocal:
  ///
  /// * [int] limit:
  ///
  /// * [int] offset:
  ///
  /// * [bool] force:
  Future<AdminUsersListResponse?> apiAdminUsersGet({ String? q, String? status, String? sortBy, String? sortDir, bool? includeLocal, int? limit, int? offset, bool? force, }) async {
    final response = await apiAdminUsersGetWithHttpInfo( q: q, status: status, sortBy: sortBy, sortDir: sortDir, includeLocal: includeLocal, limit: limit, offset: offset, force: force, );
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminUsersListResponse',) as AdminUsersListResponse;
    
    }
    return null;
  }

  /// 用户运营指标
  ///
  /// Note: This method returns the HTTP [Response].
  Future<Response> apiAdminUsersMetricsGetWithHttpInfo() async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/users/metrics';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 用户运营指标
  Future<AdminUserMetricsResponse?> apiAdminUsersMetricsGet() async {
    final response = await apiAdminUsersMetricsGetWithHttpInfo();
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminUserMetricsResponse',) as AdminUserMetricsResponse;
    
    }
    return null;
  }

  /// 重置用户密码
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [ApiAdminUsersPasswordResetPostRequest] apiAdminUsersPasswordResetPostRequest (required):
  Future<Response> apiAdminUsersPasswordResetPostWithHttpInfo(ApiAdminUsersPasswordResetPostRequest apiAdminUsersPasswordResetPostRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/users/password/reset';

    // ignore: prefer_final_locals
    Object? postBody = apiAdminUsersPasswordResetPostRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 重置用户密码
  ///
  /// Parameters:
  ///
  /// * [ApiAdminUsersPasswordResetPostRequest] apiAdminUsersPasswordResetPostRequest (required):
  Future<AdminUserPasswordResetResponse?> apiAdminUsersPasswordResetPost(ApiAdminUsersPasswordResetPostRequest apiAdminUsersPasswordResetPostRequest,) async {
    final response = await apiAdminUsersPasswordResetPostWithHttpInfo(apiAdminUsersPasswordResetPostRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminUserPasswordResetResponse',) as AdminUserPasswordResetResponse;
    
    }
    return null;
  }

  /// 用户在线会话数
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] userId (required):
  Future<Response> apiAdminUsersSessionsCountGetWithHttpInfo(String userId,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/users/sessions/count';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

      queryParams.addAll(_queryParams('', 'user_id', userId));

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 用户在线会话数
  ///
  /// Parameters:
  ///
  /// * [String] userId (required):
  Future<AdminUserSessionsCountResponse?> apiAdminUsersSessionsCountGet(String userId,) async {
    final response = await apiAdminUsersSessionsCountGetWithHttpInfo(userId,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminUserSessionsCountResponse',) as AdminUserSessionsCountResponse;
    
    }
    return null;
  }

  /// 强制用户下线
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [ApiAdminUsersDisablePostRequest] apiAdminUsersDisablePostRequest (required):
  Future<Response> apiAdminUsersSessionsRevokePostWithHttpInfo(ApiAdminUsersDisablePostRequest apiAdminUsersDisablePostRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/users/sessions/revoke';

    // ignore: prefer_final_locals
    Object? postBody = apiAdminUsersDisablePostRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 强制用户下线
  ///
  /// Parameters:
  ///
  /// * [ApiAdminUsersDisablePostRequest] apiAdminUsersDisablePostRequest (required):
  Future<AdminUserSessionsRevokeResponse?> apiAdminUsersSessionsRevokePost(ApiAdminUsersDisablePostRequest apiAdminUsersDisablePostRequest,) async {
    final response = await apiAdminUsersSessionsRevokePostWithHttpInfo(apiAdminUsersDisablePostRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminUserSessionsRevokeResponse',) as AdminUserSessionsRevokeResponse;
    
    }
    return null;
  }

  /// 设置用户状态
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [ApiAdminUsersStatusPostRequest] apiAdminUsersStatusPostRequest (required):
  Future<Response> apiAdminUsersStatusPostWithHttpInfo(ApiAdminUsersStatusPostRequest apiAdminUsersStatusPostRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/users/status';

    // ignore: prefer_final_locals
    Object? postBody = apiAdminUsersStatusPostRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 设置用户状态
  ///
  /// Parameters:
  ///
  /// * [ApiAdminUsersStatusPostRequest] apiAdminUsersStatusPostRequest (required):
  Future<AdminUserStatusResponse?> apiAdminUsersStatusPost(ApiAdminUsersStatusPostRequest apiAdminUsersStatusPostRequest,) async {
    final response = await apiAdminUsersStatusPostWithHttpInfo(apiAdminUsersStatusPostRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminUserStatusResponse',) as AdminUserStatusResponse;
    
    }
    return null;
  }

  /// 更新用户信息
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [ApiAdminUsersUpdatePostRequest] apiAdminUsersUpdatePostRequest (required):
  Future<Response> apiAdminUsersUpdatePostWithHttpInfo(ApiAdminUsersUpdatePostRequest apiAdminUsersUpdatePostRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/users/update';

    // ignore: prefer_final_locals
    Object? postBody = apiAdminUsersUpdatePostRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 更新用户信息
  ///
  /// Parameters:
  ///
  /// * [ApiAdminUsersUpdatePostRequest] apiAdminUsersUpdatePostRequest (required):
  Future<AdminUserUpdateResponse?> apiAdminUsersUpdatePost(ApiAdminUsersUpdatePostRequest apiAdminUsersUpdatePostRequest,) async {
    final response = await apiAdminUsersUpdatePostWithHttpInfo(apiAdminUsersUpdatePostRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminUserUpdateResponse',) as AdminUserUpdateResponse;
    
    }
    return null;
  }

  /// 用户详情
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] userId (required):
  Future<Response> apiAdminUsersUserIdGetWithHttpInfo(String userId,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/users/{user_id}'
      .replaceAll('{user_id}', userId);

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 用户详情
  ///
  /// Parameters:
  ///
  /// * [String] userId (required):
  Future<AdminUserDetail?> apiAdminUsersUserIdGet(String userId,) async {
    final response = await apiAdminUsersUserIdGetWithHttpInfo(userId,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminUserDetail',) as AdminUserDetail;
    
    }
    return null;
  }

  /// 用户持仓与资产概览
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] userId (required):
  ///
  /// * [bool] force:
  Future<Response> apiAdminUsersUserIdPortfolioGetWithHttpInfo(String userId, { bool? force, }) async {
    // ignore: prefer_const_declarations
    final path = r'/api/admin/users/{user_id}/portfolio'
      .replaceAll('{user_id}', userId);

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    if (force != null) {
      queryParams.addAll(_queryParams('', 'force', force));
    }

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 用户持仓与资产概览
  ///
  /// Parameters:
  ///
  /// * [String] userId (required):
  ///
  /// * [bool] force:
  Future<AdminUserPortfolioResponse?> apiAdminUsersUserIdPortfolioGet(String userId, { bool? force, }) async {
    final response = await apiAdminUsersUserIdPortfolioGetWithHttpInfo(userId,  force: force, );
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AdminUserPortfolioResponse',) as AdminUserPortfolioResponse;
    
    }
    return null;
  }

  /// Fix snapshot day_pnl
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [SnapshotFixRequest] snapshotFixRequest (required):
  Future<Response> apiSnapshotFixPostWithHttpInfo(SnapshotFixRequest snapshotFixRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/snapshot/fix';

    // ignore: prefer_final_locals
    Object? postBody = snapshotFixRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Fix snapshot day_pnl
  ///
  /// Parameters:
  ///
  /// * [SnapshotFixRequest] snapshotFixRequest (required):
  Future<ApiSnapshotTriggerPost200Response?> apiSnapshotFixPost(SnapshotFixRequest snapshotFixRequest,) async {
    final response = await apiSnapshotFixPostWithHttpInfo(snapshotFixRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'ApiSnapshotTriggerPost200Response',) as ApiSnapshotTriggerPost200Response;
    
    }
    return null;
  }

  /// Save daily snapshot
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [SnapshotSaveRequest] snapshotSaveRequest (required):
  Future<Response> apiSnapshotSavePostWithHttpInfo(SnapshotSaveRequest snapshotSaveRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/snapshot/save';

    // ignore: prefer_final_locals
    Object? postBody = snapshotSaveRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Save daily snapshot
  ///
  /// Parameters:
  ///
  /// * [SnapshotSaveRequest] snapshotSaveRequest (required):
  Future<StatusOk?> apiSnapshotSavePost(SnapshotSaveRequest snapshotSaveRequest,) async {
    final response = await apiSnapshotSavePostWithHttpInfo(snapshotSaveRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'StatusOk',) as StatusOk;
    
    }
    return null;
  }

  /// Trigger snapshot
  ///
  /// Note: This method returns the HTTP [Response].
  Future<Response> apiSnapshotTriggerPostWithHttpInfo() async {
    // ignore: prefer_const_declarations
    final path = r'/api/snapshot/trigger';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Trigger snapshot
  Future<ApiSnapshotTriggerPost200Response?> apiSnapshotTriggerPost() async {
    final response = await apiSnapshotTriggerPostWithHttpInfo();
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'ApiSnapshotTriggerPost200Response',) as ApiSnapshotTriggerPost200Response;
    
    }
    return null;
  }

  /// Bootstrap username/password for legacy users
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [BootstrapCredentialsRequest] bootstrapCredentialsRequest (required):
  Future<Response> bootstrapCredentialsWithHttpInfo(BootstrapCredentialsRequest bootstrapCredentialsRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/auth/bootstrap_credentials';

    // ignore: prefer_final_locals
    Object? postBody = bootstrapCredentialsRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Bootstrap username/password for legacy users
  ///
  /// Parameters:
  ///
  /// * [BootstrapCredentialsRequest] bootstrapCredentialsRequest (required):
  Future<void> bootstrapCredentials(BootstrapCredentialsRequest bootstrapCredentialsRequest,) async {
    final response = await bootstrapCredentialsWithHttpInfo(bootstrapCredentialsRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
  }

  /// 客户端增量同步引导
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [SyncBootstrapRequest] syncBootstrapRequest:
  Future<Response> bootstrapSyncWithHttpInfo({ SyncBootstrapRequest? syncBootstrapRequest, }) async {
    // ignore: prefer_const_declarations
    final path = r'/api/sync/bootstrap';

    // ignore: prefer_final_locals
    Object? postBody = syncBootstrapRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 客户端增量同步引导
  ///
  /// Parameters:
  ///
  /// * [SyncBootstrapRequest] syncBootstrapRequest:
  Future<SyncBootstrapResponse?> bootstrapSync({ SyncBootstrapRequest? syncBootstrapRequest, }) async {
    final response = await bootstrapSyncWithHttpInfo( syncBootstrapRequest: syncBootstrapRequest, );
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'SyncBootstrapResponse',) as SyncBootstrapResponse;
    
    }
    return null;
  }

  /// Buy asset
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [BuyPortfolioAssetRequest] buyPortfolioAssetRequest (required):
  Future<Response> buyPortfolioAssetWithHttpInfo(BuyPortfolioAssetRequest buyPortfolioAssetRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/portfolio/buy';

    // ignore: prefer_final_locals
    Object? postBody = buyPortfolioAssetRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Buy asset
  ///
  /// Parameters:
  ///
  /// * [BuyPortfolioAssetRequest] buyPortfolioAssetRequest (required):
  Future<StatusOk?> buyPortfolioAsset(BuyPortfolioAssetRequest buyPortfolioAssetRequest,) async {
    final response = await buyPortfolioAssetWithHttpInfo(buyPortfolioAssetRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'StatusOk',) as StatusOk;
    
    }
    return null;
  }

  /// 现金账户买入资产
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [PortfolioBuyWithCashRequest] portfolioBuyWithCashRequest (required):
  Future<Response> buyPortfolioAssetWithCashWithHttpInfo(PortfolioBuyWithCashRequest portfolioBuyWithCashRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/portfolio/buy_with_cash';

    // ignore: prefer_final_locals
    Object? postBody = portfolioBuyWithCashRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 现金账户买入资产
  ///
  /// Parameters:
  ///
  /// * [PortfolioBuyWithCashRequest] portfolioBuyWithCashRequest (required):
  Future<PortfolioBuyWithCashResponse?> buyPortfolioAssetWithCash(PortfolioBuyWithCashRequest portfolioBuyWithCashRequest,) async {
    final response = await buyPortfolioAssetWithCashWithHttpInfo(portfolioBuyWithCashRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'PortfolioBuyWithCashResponse',) as PortfolioBuyWithCashResponse;
    
    }
    return null;
  }

  /// Change password
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [ChangePasswordRequest] changePasswordRequest (required):
  Future<Response> changePasswordWithHttpInfo(ChangePasswordRequest changePasswordRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/auth/password/change';

    // ignore: prefer_final_locals
    Object? postBody = changePasswordRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Change password
  ///
  /// Parameters:
  ///
  /// * [ChangePasswordRequest] changePasswordRequest (required):
  Future<void> changePassword(ChangePasswordRequest changePasswordRequest,) async {
    final response = await changePasswordWithHttpInfo(changePasswordRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
  }

  /// Check API status
  ///
  /// Note: This method returns the HTTP [Response].
  Future<Response> checkSettingsApiWithHttpInfo() async {
    // ignore: prefer_const_declarations
    final path = r'/api/settings/check_api';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Check API status
  Future<Object?> checkSettingsApi() async {
    final response = await checkSettingsApiWithHttpInfo();
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'Object',) as Object;
    
    }
    return null;
  }

  /// Delete cash asset
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [DeleteCashAssetRequest] deleteCashAssetRequest (required):
  Future<Response> deleteCashAssetWithHttpInfo(DeleteCashAssetRequest deleteCashAssetRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/cash_assets/delete';

    // ignore: prefer_final_locals
    Object? postBody = deleteCashAssetRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Delete cash asset
  ///
  /// Parameters:
  ///
  /// * [DeleteCashAssetRequest] deleteCashAssetRequest (required):
  Future<StatusOk?> deleteCashAsset(DeleteCashAssetRequest deleteCashAssetRequest,) async {
    final response = await deleteCashAssetWithHttpInfo(deleteCashAssetRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'StatusOk',) as StatusOk;
    
    }
    return null;
  }

  /// Delete liability
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [DeleteCashAssetRequest] deleteCashAssetRequest (required):
  Future<Response> deleteLiabilityWithHttpInfo(DeleteCashAssetRequest deleteCashAssetRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/liabilities/delete';

    // ignore: prefer_final_locals
    Object? postBody = deleteCashAssetRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Delete liability
  ///
  /// Parameters:
  ///
  /// * [DeleteCashAssetRequest] deleteCashAssetRequest (required):
  Future<StatusOk?> deleteLiability(DeleteCashAssetRequest deleteCashAssetRequest,) async {
    final response = await deleteLiabilityWithHttpInfo(deleteCashAssetRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'StatusOk',) as StatusOk;
    
    }
    return null;
  }

  /// Delete other asset
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [DeleteCashAssetRequest] deleteCashAssetRequest (required):
  Future<Response> deleteOtherAssetWithHttpInfo(DeleteCashAssetRequest deleteCashAssetRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/other_assets/delete';

    // ignore: prefer_final_locals
    Object? postBody = deleteCashAssetRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Delete other asset
  ///
  /// Parameters:
  ///
  /// * [DeleteCashAssetRequest] deleteCashAssetRequest (required):
  Future<StatusOk?> deleteOtherAsset(DeleteCashAssetRequest deleteCashAssetRequest,) async {
    final response = await deleteOtherAssetWithHttpInfo(deleteCashAssetRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'StatusOk',) as StatusOk;
    
    }
    return null;
  }

  /// Delete asset
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [DeletePortfolioAssetRequest] deletePortfolioAssetRequest (required):
  Future<Response> deletePortfolioAssetWithHttpInfo(DeletePortfolioAssetRequest deletePortfolioAssetRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/portfolio/delete';

    // ignore: prefer_final_locals
    Object? postBody = deletePortfolioAssetRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Delete asset
  ///
  /// Parameters:
  ///
  /// * [DeletePortfolioAssetRequest] deletePortfolioAssetRequest (required):
  Future<StatusOk?> deletePortfolioAsset(DeletePortfolioAssetRequest deletePortfolioAssetRequest,) async {
    final response = await deletePortfolioAssetWithHttpInfo(deletePortfolioAssetRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'StatusOk',) as StatusOk;
    
    }
    return null;
  }

  /// 纠正性删除资产及历史记录
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [PortfolioDeleteCorrectiveRequest] portfolioDeleteCorrectiveRequest (required):
  Future<Response> deletePortfolioAssetCorrectiveWithHttpInfo(PortfolioDeleteCorrectiveRequest portfolioDeleteCorrectiveRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/portfolio/delete_corrective';

    // ignore: prefer_final_locals
    Object? postBody = portfolioDeleteCorrectiveRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 纠正性删除资产及历史记录
  ///
  /// Parameters:
  ///
  /// * [PortfolioDeleteCorrectiveRequest] portfolioDeleteCorrectiveRequest (required):
  Future<PortfolioDeleteCorrectiveResponse?> deletePortfolioAssetCorrective(PortfolioDeleteCorrectiveRequest portfolioDeleteCorrectiveRequest,) async {
    final response = await deletePortfolioAssetCorrectiveWithHttpInfo(portfolioDeleteCorrectiveRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'PortfolioDeleteCorrectiveResponse',) as PortfolioDeleteCorrectiveResponse;
    
    }
    return null;
  }

  /// Download DB backup
  ///
  /// Note: This method returns the HTTP [Response].
  Future<Response> downloadSettingsBackupWithHttpInfo() async {
    // ignore: prefer_const_declarations
    final path = r'/api/settings/backup';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Download DB backup
  Future<void> downloadSettingsBackup() async {
    final response = await downloadSettingsBackupWithHttpInfo();
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
  }

  /// PnL calendar
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] type:
  ///
  /// * [int] year:
  ///   day/month 视图可选，指定年份
  ///
  /// * [int] month:
  ///   day 视图可选，指定月份
  Future<Response> getAnalysisCalendarWithHttpInfo({ String? type, int? year, int? month, }) async {
    // ignore: prefer_const_declarations
    final path = r'/api/analysis/calendar';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    if (type != null) {
      queryParams.addAll(_queryParams('', 'type', type));
    }
    if (year != null) {
      queryParams.addAll(_queryParams('', 'year', year));
    }
    if (month != null) {
      queryParams.addAll(_queryParams('', 'month', month));
    }

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// PnL calendar
  ///
  /// Parameters:
  ///
  /// * [String] type:
  ///
  /// * [int] year:
  ///   day/month 视图可选，指定年份
  ///
  /// * [int] month:
  ///   day 视图可选，指定月份
  Future<AnalysisCalendarResponse?> getAnalysisCalendar({ String? type, int? year, int? month, }) async {
    final response = await getAnalysisCalendarWithHttpInfo( type: type, year: year, month: month, );
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AnalysisCalendarResponse',) as AnalysisCalendarResponse;
    
    }
    return null;
  }

  /// 收益日历按市场拆分
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] type:
  ///
  /// * [String] timeType:
  ///
  /// * [int] year:
  ///
  /// * [int] month:
  Future<Response> getAnalysisMarketBreakdownWithHttpInfo({ String? type, String? timeType, int? year, int? month, }) async {
    // ignore: prefer_const_declarations
    final path = r'/api/analysis/calendar/market_breakdown';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    if (type != null) {
      queryParams.addAll(_queryParams('', 'type', type));
    }
    if (timeType != null) {
      queryParams.addAll(_queryParams('', 'time_type', timeType));
    }
    if (year != null) {
      queryParams.addAll(_queryParams('', 'year', year));
    }
    if (month != null) {
      queryParams.addAll(_queryParams('', 'month', month));
    }

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 收益日历按市场拆分
  ///
  /// Parameters:
  ///
  /// * [String] type:
  ///
  /// * [String] timeType:
  ///
  /// * [int] year:
  ///
  /// * [int] month:
  Future<AnalysisMarketBreakdownResponse?> getAnalysisMarketBreakdown({ String? type, String? timeType, int? year, int? month, }) async {
    final response = await getAnalysisMarketBreakdownWithHttpInfo( type: type, timeType: timeType, year: year, month: month, );
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AnalysisMarketBreakdownResponse',) as AnalysisMarketBreakdownResponse;
    
    }
    return null;
  }

  /// PnL overview
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] period:
  Future<Response> getAnalysisOverviewWithHttpInfo({ String? period, }) async {
    // ignore: prefer_const_declarations
    final path = r'/api/analysis/overview';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    if (period != null) {
      queryParams.addAll(_queryParams('', 'period', period));
    }

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// PnL overview
  ///
  /// Parameters:
  ///
  /// * [String] period:
  Future<AnalysisOverviewResponse?> getAnalysisOverview({ String? period, }) async {
    final response = await getAnalysisOverviewWithHttpInfo( period: period, );
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AnalysisOverviewResponse',) as AnalysisOverviewResponse;
    
    }
    return null;
  }

  /// PnL rank
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] type:
  ///
  /// * [String] market:
  Future<Response> getAnalysisRankWithHttpInfo({ String? type, String? market, }) async {
    // ignore: prefer_const_declarations
    final path = r'/api/analysis/rank';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    if (type != null) {
      queryParams.addAll(_queryParams('', 'type', type));
    }
    if (market != null) {
      queryParams.addAll(_queryParams('', 'market', market));
    }

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// PnL rank
  ///
  /// Parameters:
  ///
  /// * [String] type:
  ///
  /// * [String] market:
  Future<AnalysisRankResponse?> getAnalysisRank({ String? type, String? market, }) async {
    final response = await getAnalysisRankWithHttpInfo( type: type, market: market, );
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AnalysisRankResponse',) as AnalysisRankResponse;
    
    }
    return null;
  }

  /// 获取客户端更新配置
  ///
  /// Note: This method returns the HTTP [Response].
  Future<Response> getAppVersionWithHttpInfo() async {
    // ignore: prefer_const_declarations
    final path = r'/api/app/version';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 获取客户端更新配置
  Future<AppVersionResponse?> getAppVersion() async {
    final response = await getAppVersionWithHttpInfo();
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AppVersionResponse',) as AppVersionResponse;
    
    }
    return null;
  }

  /// 批量资产趋势线
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [AssetTrendsRequest] assetTrendsRequest (required):
  Future<Response> getAssetTrendsWithHttpInfo(AssetTrendsRequest assetTrendsRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/asset/trends';

    // ignore: prefer_final_locals
    Object? postBody = assetTrendsRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 批量资产趋势线
  ///
  /// Parameters:
  ///
  /// * [AssetTrendsRequest] assetTrendsRequest (required):
  Future<AssetTrendsResponse?> getAssetTrends(AssetTrendsRequest assetTrendsRequest,) async {
    final response = await getAssetTrendsWithHttpInfo(assetTrendsRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'AssetTrendsResponse',) as AssetTrendsResponse;
    
    }
    return null;
  }

  /// Get batch prices
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [GetBatchPricesRequest] getBatchPricesRequest (required):
  Future<Response> getBatchPricesWithHttpInfo(GetBatchPricesRequest getBatchPricesRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/prices/batch';

    // ignore: prefer_final_locals
    Object? postBody = getBatchPricesRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Get batch prices
  ///
  /// Parameters:
  ///
  /// * [GetBatchPricesRequest] getBatchPricesRequest (required):
  Future<Map<String, GetPrice200Response>?> getBatchPrices(GetBatchPricesRequest getBatchPricesRequest,) async {
    final response = await getBatchPricesWithHttpInfo(getBatchPricesRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return Map<String, GetPrice200Response>.from(await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'Map<String, GetPrice200Response>'),);

    }
    return null;
  }

  /// Get cash assets
  ///
  /// Note: This method returns the HTTP [Response].
  Future<Response> getCashAssetsWithHttpInfo() async {
    // ignore: prefer_const_declarations
    final path = r'/api/cash_assets';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Get cash assets
  Future<void> getCashAssets() async {
    final response = await getCashAssetsWithHttpInfo();
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
  }

  /// Current user
  ///
  /// Note: This method returns the HTTP [Response].
  Future<Response> getCurrentUserWithHttpInfo() async {
    // ignore: prefer_const_declarations
    final path = r'/api/auth/me';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Current user
  Future<void> getCurrentUser() async {
    final response = await getCurrentUserWithHttpInfo();
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
  }

  /// Health check
  ///
  /// Note: This method returns the HTTP [Response].
  Future<Response> getHealthWithHttpInfo() async {
    // ignore: prefer_const_declarations
    final path = r'/health';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Health check
  Future<GetHealth200Response?> getHealth() async {
    final response = await getHealthWithHttpInfo();
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'GetHealth200Response',) as GetHealth200Response;
    
    }
    return null;
  }

  /// Get history
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [int] days:
  Future<Response> getHistoryWithHttpInfo({ int? days, }) async {
    // ignore: prefer_const_declarations
    final path = r'/api/history';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    if (days != null) {
      queryParams.addAll(_queryParams('', 'days', days));
    }

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Get history
  ///
  /// Parameters:
  ///
  /// * [int] days:
  Future<List<Object>?> getHistory({ int? days, }) async {
    final response = await getHistoryWithHttpInfo( days: days, );
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      final responseBody = await _decodeBodyBytes(response);
      return (await apiClient.deserializeAsync(responseBody, 'List<Object>') as List)
        .cast<Object>()
        .toList(growable: false);

    }
    return null;
  }

  /// Latest news
  ///
  /// Note: This method returns the HTTP [Response].
  Future<Response> getLatestNewsWithHttpInfo() async {
    // ignore: prefer_const_declarations
    final path = r'/api/news/latest';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Latest news
  Future<List<Object>?> getLatestNews() async {
    final response = await getLatestNewsWithHttpInfo();
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      final responseBody = await _decodeBodyBytes(response);
      return (await apiClient.deserializeAsync(responseBody, 'List<Object>') as List)
        .cast<Object>()
        .toList(growable: false);

    }
    return null;
  }

  /// Get liabilities
  ///
  /// Note: This method returns the HTTP [Response].
  Future<Response> getLiabilitiesWithHttpInfo() async {
    // ignore: prefer_const_declarations
    final path = r'/api/liabilities';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Get liabilities
  Future<void> getLiabilities() async {
    final response = await getLiabilitiesWithHttpInfo();
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
  }

  /// 首页指数与汇率
  ///
  /// Note: This method returns the HTTP [Response].
  Future<Response> getMarketIndicesWithHttpInfo() async {
    // ignore: prefer_const_declarations
    final path = r'/api/market/indices';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 首页指数与汇率
  Future<List<MarketIndexItem>?> getMarketIndices() async {
    final response = await getMarketIndicesWithHttpInfo();
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      final responseBody = await _decodeBodyBytes(response);
      return (await apiClient.deserializeAsync(responseBody, 'List<MarketIndexItem>') as List)
        .cast<MarketIndexItem>()
        .toList(growable: false);

    }
    return null;
  }

  /// 市场开休市状态
  ///
  /// Note: This method returns the HTTP [Response].
  Future<Response> getMarketStatusWithHttpInfo() async {
    // ignore: prefer_const_declarations
    final path = r'/api/market/status';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 市场开休市状态
  Future<MarketStatusResponse?> getMarketStatus() async {
    final response = await getMarketStatusWithHttpInfo();
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'MarketStatusResponse',) as MarketStatusResponse;
    
    }
    return null;
  }

  /// Get other assets
  ///
  /// Note: This method returns the HTTP [Response].
  Future<Response> getOtherAssetsWithHttpInfo() async {
    // ignore: prefer_const_declarations
    final path = r'/api/other_assets';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Get other assets
  Future<void> getOtherAssets() async {
    final response = await getOtherAssetsWithHttpInfo();
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
  }

  /// Get portfolio
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] type:
  ///
  /// * [bool] withMetrics:
  Future<Response> getPortfolioWithHttpInfo({ String? type, bool? withMetrics, }) async {
    // ignore: prefer_const_declarations
    final path = r'/api/portfolio';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    if (type != null) {
      queryParams.addAll(_queryParams('', 'type', type));
    }
    if (withMetrics != null) {
      queryParams.addAll(_queryParams('', 'with_metrics', withMetrics));
    }

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Get portfolio
  ///
  /// Parameters:
  ///
  /// * [String] type:
  ///
  /// * [bool] withMetrics:
  Future<List<PortfolioItem>?> getPortfolio({ String? type, bool? withMetrics, }) async {
    final response = await getPortfolioWithHttpInfo( type: type, withMetrics: withMetrics, );
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      final responseBody = await _decodeBodyBytes(response);
      return (await apiClient.deserializeAsync(responseBody, 'List<PortfolioItem>') as List)
        .cast<PortfolioItem>()
        .toList(growable: false);

    }
    return null;
  }

  /// Get portfolio transaction and correction records
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] code (required):
  Future<Response> getPortfolioTransactionsWithHttpInfo(String code,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/portfolio/transactions';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

      queryParams.addAll(_queryParams('', 'code', code));

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Get portfolio transaction and correction records
  ///
  /// Parameters:
  ///
  /// * [String] code (required):
  Future<PortfolioTransactionsResponse?> getPortfolioTransactions(String code,) async {
    final response = await getPortfolioTransactionsWithHttpInfo(code,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'PortfolioTransactionsResponse',) as PortfolioTransactionsResponse;
    
    }
    return null;
  }

  /// Get a single price
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] code (required):
  Future<Response> getPriceWithHttpInfo(String code,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/price';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

      queryParams.addAll(_queryParams('', 'code', code));

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Get a single price
  ///
  /// Parameters:
  ///
  /// * [String] code (required):
  Future<GetPrice200Response?> getPrice(String code,) async {
    final response = await getPriceWithHttpInfo(code,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'GetPrice200Response',) as GetPrice200Response;
    
    }
    return null;
  }

  /// Get FX rates
  ///
  /// Note: This method returns the HTTP [Response].
  Future<Response> getRatesWithHttpInfo() async {
    // ignore: prefer_const_declarations
    final path = r'/api/rates';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Get FX rates
  Future<Map<String, num>?> getRates() async {
    final response = await getRatesWithHttpInfo();
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return Map<String, num>.from(await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'Map<String, num>'),);

    }
    return null;
  }

  /// System info
  ///
  /// Note: This method returns the HTTP [Response].
  Future<Response> getSettingsInfoWithHttpInfo() async {
    // ignore: prefer_const_declarations
    final path = r'/api/settings/info';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// System info
  Future<Object?> getSettingsInfo() async {
    final response = await getSettingsInfoWithHttpInfo();
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'Object',) as Object;
    
    }
    return null;
  }

  /// 行情运行健康指标
  ///
  /// Note: This method returns the HTTP [Response].
  Future<Response> getSystemPriceHealthWithHttpInfo() async {
    // ignore: prefer_const_declarations
    final path = r'/api/system/price_health';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 行情运行健康指标
  Future<PriceHealthResponse?> getSystemPriceHealth() async {
    final response = await getSystemPriceHealthWithHttpInfo();
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'PriceHealthResponse',) as PriceHealthResponse;
    
    }
    return null;
  }

  /// Get transactions
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [int] limit:
  Future<Response> getTransactionsWithHttpInfo({ int? limit, }) async {
    // ignore: prefer_const_declarations
    final path = r'/api/transactions';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    if (limit != null) {
      queryParams.addAll(_queryParams('', 'limit', limit));
    }

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Get transactions
  ///
  /// Parameters:
  ///
  /// * [int] limit:
  Future<List<Object>?> getTransactions({ int? limit, }) async {
    final response = await getTransactionsWithHttpInfo( limit: limit, );
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      final responseBody = await _decodeBodyBytes(response);
      return (await apiClient.deserializeAsync(responseBody, 'List<Object>') as List)
        .cast<Object>()
        .toList(growable: false);

    }
    return null;
  }

  /// Web 门户公开配置
  ///
  /// Note: This method returns the HTTP [Response].
  Future<Response> getWebConfigWithHttpInfo() async {
    // ignore: prefer_const_declarations
    final path = r'/api/web/config';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Web 门户公开配置
  Future<WebConfigResponse?> getWebConfig() async {
    final response = await getWebConfigWithHttpInfo();
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'WebConfigResponse',) as WebConfigResponse;
    
    }
    return null;
  }

  /// Login
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [LoginRequest] loginRequest (required):
  Future<Response> loginWithHttpInfo(LoginRequest loginRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/auth/login';

    // ignore: prefer_final_locals
    Object? postBody = loginRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Login
  ///
  /// Parameters:
  ///
  /// * [LoginRequest] loginRequest (required):
  Future<void> login(LoginRequest loginRequest,) async {
    final response = await loginWithHttpInfo(loginRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
  }

  /// Logout
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [LogoutRequest] logoutRequest:
  Future<Response> logoutWithHttpInfo({ LogoutRequest? logoutRequest, }) async {
    // ignore: prefer_const_declarations
    final path = r'/api/auth/logout';

    // ignore: prefer_final_locals
    Object? postBody = logoutRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Logout
  ///
  /// Parameters:
  ///
  /// * [LogoutRequest] logoutRequest:
  Future<void> logout({ LogoutRequest? logoutRequest, }) async {
    final response = await logoutWithHttpInfo( logoutRequest: logoutRequest, );
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
  }

  /// Modify asset qty/price
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [ModifyPortfolioAssetRequest] modifyPortfolioAssetRequest (required):
  Future<Response> modifyPortfolioAssetWithHttpInfo(ModifyPortfolioAssetRequest modifyPortfolioAssetRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/portfolio/modify';

    // ignore: prefer_final_locals
    Object? postBody = modifyPortfolioAssetRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Modify asset qty/price
  ///
  /// Parameters:
  ///
  /// * [ModifyPortfolioAssetRequest] modifyPortfolioAssetRequest (required):
  Future<StatusOk?> modifyPortfolioAsset(ModifyPortfolioAssetRequest modifyPortfolioAssetRequest,) async {
    final response = await modifyPortfolioAssetWithHttpInfo(modifyPortfolioAssetRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'StatusOk',) as StatusOk;
    
    }
    return null;
  }

  /// Refresh access token
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [RefreshSessionRequest] refreshSessionRequest (required):
  Future<Response> refreshSessionWithHttpInfo(RefreshSessionRequest refreshSessionRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/auth/refresh';

    // ignore: prefer_final_locals
    Object? postBody = refreshSessionRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Refresh access token
  ///
  /// Parameters:
  ///
  /// * [RefreshSessionRequest] refreshSessionRequest (required):
  Future<void> refreshSession(RefreshSessionRequest refreshSessionRequest,) async {
    final response = await refreshSessionWithHttpInfo(refreshSessionRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
  }

  /// Register with invite code
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [RegisterRequest] registerRequest (required):
  Future<Response> registerWithHttpInfo(RegisterRequest registerRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/auth/register';

    // ignore: prefer_final_locals
    Object? postBody = registerRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Register with invite code
  ///
  /// Parameters:
  ///
  /// * [RegisterRequest] registerRequest (required):
  Future<void> register(RegisterRequest registerRequest,) async {
    final response = await registerWithHttpInfo(registerRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
  }

  /// Restore DB
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [MultipartFile] file:
  Future<Response> restoreSettingsBackupWithHttpInfo({ MultipartFile? file, }) async {
    // ignore: prefer_const_declarations
    final path = r'/api/settings/restore';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['multipart/form-data'];

    bool hasFields = false;
    final mp = MultipartRequest('POST', Uri.parse(path));
    if (file != null) {
      hasFields = true;
      mp.fields[r'file'] = file.field;
      mp.files.add(file);
    }
    if (hasFields) {
      postBody = mp;
    }

    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Restore DB
  ///
  /// Parameters:
  ///
  /// * [MultipartFile] file:
  Future<StatusOk?> restoreSettingsBackup({ MultipartFile? file, }) async {
    final response = await restoreSettingsBackupWithHttpInfo( file: file, );
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'StatusOk',) as StatusOk;
    
    }
    return null;
  }

  /// Search securities
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] q (required):
  Future<Response> searchSecuritiesWithHttpInfo(String q,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/search';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

      queryParams.addAll(_queryParams('', 'q', q));

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Search securities
  ///
  /// Parameters:
  ///
  /// * [String] q (required):
  Future<List<Object>?> searchSecurities(String q,) async {
    final response = await searchSecuritiesWithHttpInfo(q,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      final responseBody = await _decodeBodyBytes(response);
      return (await apiClient.deserializeAsync(responseBody, 'List<Object>') as List)
        .cast<Object>()
        .toList(growable: false);

    }
    return null;
  }

  /// Sell asset
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [BuyPortfolioAssetRequest] buyPortfolioAssetRequest (required):
  Future<Response> sellPortfolioAssetWithHttpInfo(BuyPortfolioAssetRequest buyPortfolioAssetRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/portfolio/sell';

    // ignore: prefer_final_locals
    Object? postBody = buyPortfolioAssetRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Sell asset
  ///
  /// Parameters:
  ///
  /// * [BuyPortfolioAssetRequest] buyPortfolioAssetRequest (required):
  Future<StatusOk?> sellPortfolioAsset(BuyPortfolioAssetRequest buyPortfolioAssetRequest,) async {
    final response = await sellPortfolioAssetWithHttpInfo(buyPortfolioAssetRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'StatusOk',) as StatusOk;
    
    }
    return null;
  }

  /// Deprecated endpoint, returns 410
  ///
  /// Note: This method returns the HTTP [Response].
  Future<Response> sendAuthCodeWithHttpInfo() async {
    // ignore: prefer_const_declarations
    final path = r'/api/auth/send_code';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Deprecated endpoint, returns 410
  Future<void> sendAuthCode() async {
    final response = await sendAuthCodeWithHttpInfo();
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
  }

  /// 撤销最近一次投资操作
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [PortfolioUndoRequest] portfolioUndoRequest (required):
  Future<Response> undoPortfolioOperationWithHttpInfo(PortfolioUndoRequest portfolioUndoRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/portfolio/undo';

    // ignore: prefer_final_locals
    Object? postBody = portfolioUndoRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// 撤销最近一次投资操作
  ///
  /// Parameters:
  ///
  /// * [PortfolioUndoRequest] portfolioUndoRequest (required):
  Future<PortfolioUndoResponse?> undoPortfolioOperation(PortfolioUndoRequest portfolioUndoRequest,) async {
    final response = await undoPortfolioOperationWithHttpInfo(portfolioUndoRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'PortfolioUndoResponse',) as PortfolioUndoResponse;
    
    }
    return null;
  }

  /// Update cash asset
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [UpdateCashAssetRequest] updateCashAssetRequest (required):
  Future<Response> updateCashAssetWithHttpInfo(UpdateCashAssetRequest updateCashAssetRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/cash_assets/update';

    // ignore: prefer_final_locals
    Object? postBody = updateCashAssetRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Update cash asset
  ///
  /// Parameters:
  ///
  /// * [UpdateCashAssetRequest] updateCashAssetRequest (required):
  Future<StatusOk?> updateCashAsset(UpdateCashAssetRequest updateCashAssetRequest,) async {
    final response = await updateCashAssetWithHttpInfo(updateCashAssetRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'StatusOk',) as StatusOk;
    
    }
    return null;
  }

  /// Update liability
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [UpdateCashAssetRequest] updateCashAssetRequest (required):
  Future<Response> updateLiabilityWithHttpInfo(UpdateCashAssetRequest updateCashAssetRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/liabilities/update';

    // ignore: prefer_final_locals
    Object? postBody = updateCashAssetRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Update liability
  ///
  /// Parameters:
  ///
  /// * [UpdateCashAssetRequest] updateCashAssetRequest (required):
  Future<StatusOk?> updateLiability(UpdateCashAssetRequest updateCashAssetRequest,) async {
    final response = await updateLiabilityWithHttpInfo(updateCashAssetRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'StatusOk',) as StatusOk;
    
    }
    return null;
  }

  /// Update other asset
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [UpdateCashAssetRequest] updateCashAssetRequest (required):
  Future<Response> updateOtherAssetWithHttpInfo(UpdateCashAssetRequest updateCashAssetRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/other_assets/update';

    // ignore: prefer_final_locals
    Object? postBody = updateCashAssetRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Update other asset
  ///
  /// Parameters:
  ///
  /// * [UpdateCashAssetRequest] updateCashAssetRequest (required):
  Future<StatusOk?> updateOtherAsset(UpdateCashAssetRequest updateCashAssetRequest,) async {
    final response = await updateOtherAssetWithHttpInfo(updateCashAssetRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'StatusOk',) as StatusOk;
    
    }
    return null;
  }

  /// Update asset field
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [UpdatePortfolioAssetFieldRequest] updatePortfolioAssetFieldRequest (required):
  Future<Response> updatePortfolioAssetFieldWithHttpInfo(UpdatePortfolioAssetFieldRequest updatePortfolioAssetFieldRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/portfolio/update';

    // ignore: prefer_final_locals
    Object? postBody = updatePortfolioAssetFieldRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Update asset field
  ///
  /// Parameters:
  ///
  /// * [UpdatePortfolioAssetFieldRequest] updatePortfolioAssetFieldRequest (required):
  Future<StatusOk?> updatePortfolioAssetField(UpdatePortfolioAssetFieldRequest updatePortfolioAssetFieldRequest,) async {
    final response = await updatePortfolioAssetFieldWithHttpInfo(updatePortfolioAssetFieldRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'StatusOk',) as StatusOk;
    
    }
    return null;
  }

  /// Update user profile
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [UpdateProfileRequest] updateProfileRequest (required):
  Future<Response> updateProfileWithHttpInfo(UpdateProfileRequest updateProfileRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/auth/profile';

    // ignore: prefer_final_locals
    Object? postBody = updateProfileRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Update user profile
  ///
  /// Parameters:
  ///
  /// * [UpdateProfileRequest] updateProfileRequest (required):
  Future<void> updateProfile(UpdateProfileRequest updateProfileRequest,) async {
    final response = await updateProfileWithHttpInfo(updateProfileRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
  }

  /// Validate invite code
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [ValidateInviteCodeRequest] validateInviteCodeRequest (required):
  Future<Response> validateInviteCodeWithHttpInfo(ValidateInviteCodeRequest validateInviteCodeRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/api/auth/invite/validate';

    // ignore: prefer_final_locals
    Object? postBody = validateInviteCodeRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Validate invite code
  ///
  /// Parameters:
  ///
  /// * [ValidateInviteCodeRequest] validateInviteCodeRequest (required):
  Future<void> validateInviteCode(ValidateInviteCodeRequest validateInviteCodeRequest,) async {
    final response = await validateInviteCodeWithHttpInfo(validateInviteCodeRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
  }
}
