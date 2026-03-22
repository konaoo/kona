//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class ApiClient {
  ApiClient({this.basePath = 'http://114.132.238.12', this.authentication,});

  final String basePath;
  final Authentication? authentication;

  var _client = Client();
  final _defaultHeaderMap = <String, String>{};

  /// Returns the current HTTP [Client] instance to use in this class.
  ///
  /// The return value is guaranteed to never be null.
  Client get client => _client;

  /// Requests to use a new HTTP [Client] in this class.
  set client(Client newClient) {
    _client = newClient;
  }

  Map<String, String> get defaultHeaderMap => _defaultHeaderMap;

  void addDefaultHeader(String key, String value) {
     _defaultHeaderMap[key] = value;
  }

  // We don't use a Map<String, String> for queryParams.
  // If collectionFormat is 'multi', a key might appear multiple times.
  Future<Response> invokeAPI(
    String path,
    String method,
    List<QueryParam> queryParams,
    Object? body,
    Map<String, String> headerParams,
    Map<String, String> formParams,
    String? contentType,
  ) async {
    await authentication?.applyToParams(queryParams, headerParams);

    headerParams.addAll(_defaultHeaderMap);
    if (contentType != null) {
      headerParams['Content-Type'] = contentType;
    }

    final urlEncodedQueryParams = queryParams.map((param) => '$param');
    final queryString = urlEncodedQueryParams.isNotEmpty ? '?${urlEncodedQueryParams.join('&')}' : '';
    final uri = Uri.parse('$basePath$path$queryString');

    try {
      // Special case for uploading a single file which isn't a 'multipart/form-data'.
      if (
        body is MultipartFile && (contentType == null ||
        !contentType.toLowerCase().startsWith('multipart/form-data'))
      ) {
        final request = StreamedRequest(method, uri);
        request.headers.addAll(headerParams);
        request.contentLength = body.length;
        body.finalize().listen(
          request.sink.add,
          onDone: request.sink.close,
          // ignore: avoid_types_on_closure_parameters
          onError: (Object error, StackTrace trace) => request.sink.close(),
          cancelOnError: true,
        );
        final response = await _client.send(request);
        return Response.fromStream(response);
      }

      if (body is MultipartRequest) {
        final request = MultipartRequest(method, uri);
        request.fields.addAll(body.fields);
        request.files.addAll(body.files);
        request.headers.addAll(body.headers);
        request.headers.addAll(headerParams);
        final response = await _client.send(request);
        return Response.fromStream(response);
      }

      final msgBody = contentType == 'application/x-www-form-urlencoded'
        ? formParams
        : await serializeAsync(body);
      final nullableHeaderParams = headerParams.isEmpty ? null : headerParams;

      switch(method) {
        case 'POST': return await _client.post(uri, headers: nullableHeaderParams, body: msgBody,);
        case 'PUT': return await _client.put(uri, headers: nullableHeaderParams, body: msgBody,);
        case 'DELETE': return await _client.delete(uri, headers: nullableHeaderParams, body: msgBody,);
        case 'PATCH': return await _client.patch(uri, headers: nullableHeaderParams, body: msgBody,);
        case 'HEAD': return await _client.head(uri, headers: nullableHeaderParams,);
        case 'GET': return await _client.get(uri, headers: nullableHeaderParams,);
      }
    } on SocketException catch (error, trace) {
      throw ApiException.withInner(
        HttpStatus.badRequest,
        'Socket operation failed: $method $path',
        error,
        trace,
      );
    } on TlsException catch (error, trace) {
      throw ApiException.withInner(
        HttpStatus.badRequest,
        'TLS/SSL communication failed: $method $path',
        error,
        trace,
      );
    } on IOException catch (error, trace) {
      throw ApiException.withInner(
        HttpStatus.badRequest,
        'I/O operation failed: $method $path',
        error,
        trace,
      );
    } on ClientException catch (error, trace) {
      throw ApiException.withInner(
        HttpStatus.badRequest,
        'HTTP connection failed: $method $path',
        error,
        trace,
      );
    } on Exception catch (error, trace) {
      throw ApiException.withInner(
        HttpStatus.badRequest,
        'Exception occurred: $method $path',
        error,
        trace,
      );
    }

    throw ApiException(
      HttpStatus.badRequest,
      'Invalid HTTP operation: $method $path',
    );
  }

  Future<dynamic> deserializeAsync(String value, String targetType, {bool growable = false,}) async =>
    // ignore: deprecated_member_use_from_same_package
    deserialize(value, targetType, growable: growable);

  @Deprecated('Scheduled for removal in OpenAPI Generator 6.x. Use deserializeAsync() instead.')
  dynamic deserialize(String value, String targetType, {bool growable = false,}) {
    // Remove all spaces. Necessary for regular expressions as well.
    targetType = targetType.replaceAll(' ', ''); // ignore: parameter_assignments

    // If the expected target type is String, nothing to do...
    return targetType == 'String'
      ? value
      : fromJson(json.decode(value), targetType, growable: growable);
  }

  // ignore: deprecated_member_use_from_same_package
  Future<String> serializeAsync(Object? value) async => serialize(value);

  @Deprecated('Scheduled for removal in OpenAPI Generator 6.x. Use serializeAsync() instead.')
  String serialize(Object? value) => value == null ? '' : json.encode(value);

  /// Returns a native instance of an OpenAPI class matching the [specified type][targetType].
  static dynamic fromJson(dynamic value, String targetType, {bool growable = false,}) {
    try {
      switch (targetType) {
        case 'String':
          return value is String ? value : value.toString();
        case 'int':
          return value is int ? value : int.parse('$value');
        case 'double':
          return value is double ? value : double.parse('$value');
        case 'bool':
          if (value is bool) {
            return value;
          }
          final valueString = '$value'.toLowerCase();
          return valueString == 'true' || valueString == '1';
        case 'DateTime':
          return value is DateTime ? value : DateTime.tryParse(value);
        case 'AddCashAssetRequest':
          return AddCashAssetRequest.fromJson(value);
        case 'AddPortfolioAdjustmentEventRequest':
          return AddPortfolioAdjustmentEventRequest.fromJson(value);
        case 'AddPortfolioAssetRequest':
          return AddPortfolioAssetRequest.fromJson(value);
        case 'AdminApiHealthResponse':
          return AdminApiHealthResponse.fromJson(value);
        case 'AdminApiHealthResponseDb':
          return AdminApiHealthResponseDb.fromJson(value);
        case 'AdminApiHealthResponseVersionInfo':
          return AdminApiHealthResponseVersionInfo.fromJson(value);
        case 'AdminAuditItem':
          return AdminAuditItem.fromJson(value);
        case 'AdminBackupLatestResponse':
          return AdminBackupLatestResponse.fromJson(value);
        case 'AdminBackupRequest':
          return AdminBackupRequest.fromJson(value);
        case 'AdminBackupResponse':
          return AdminBackupResponse.fromJson(value);
        case 'AdminConfigItem':
          return AdminConfigItem.fromJson(value);
        case 'AdminConfigListResponse':
          return AdminConfigListResponse.fromJson(value);
        case 'AdminConfigUpdateRequest':
          return AdminConfigUpdateRequest.fromJson(value);
        case 'AdminConfigUpdateRequestItemsInner':
          return AdminConfigUpdateRequestItemsInner.fromJson(value);
        case 'AdminConfigUpdateResponse':
          return AdminConfigUpdateResponse.fromJson(value);
        case 'AdminConfigUpdateResponseUpdatedInner':
          return AdminConfigUpdateResponseUpdatedInner.fromJson(value);
        case 'AdminDataSnapshotsResponse':
          return AdminDataSnapshotsResponse.fromJson(value);
        case 'AdminInviteItem':
          return AdminInviteItem.fromJson(value);
        case 'AdminInvitesGenerateRequest':
          return AdminInvitesGenerateRequest.fromJson(value);
        case 'AdminInvitesGenerateResponse':
          return AdminInvitesGenerateResponse.fromJson(value);
        case 'AdminInvitesListResponse':
          return AdminInvitesListResponse.fromJson(value);
        case 'AdminInvitesRevokeRequest':
          return AdminInvitesRevokeRequest.fromJson(value);
        case 'AdminInvitesRevokeResponse':
          return AdminInvitesRevokeResponse.fromJson(value);
        case 'AdminInvitesStatsResponse':
          return AdminInvitesStatsResponse.fromJson(value);
        case 'AdminMetaDictionariesResponse':
          return AdminMetaDictionariesResponse.fromJson(value);
        case 'AdminMiniBar':
          return AdminMiniBar.fromJson(value);
        case 'AdminOpsAppUpdateResponse':
          return AdminOpsAppUpdateResponse.fromJson(value);
        case 'AdminOpsAppUpdateUpdateResponse':
          return AdminOpsAppUpdateUpdateResponse.fromJson(value);
        case 'AdminOpsTextImageResponse':
          return AdminOpsTextImageResponse.fromJson(value);
        case 'AdminOpsTextImageUpdateResponse':
          return AdminOpsTextImageUpdateResponse.fromJson(value);
        case 'AdminOverviewResponse':
          return AdminOverviewResponse.fromJson(value);
        case 'AdminOverviewResponseDashboard':
          return AdminOverviewResponseDashboard.fromJson(value);
        case 'AdminOverviewResponseSnapshots':
          return AdminOverviewResponseSnapshots.fromJson(value);
        case 'AdminOverviewResponseUsers':
          return AdminOverviewResponseUsers.fromJson(value);
        case 'AdminPoliciesResponse':
          return AdminPoliciesResponse.fromJson(value);
        case 'AdminPolicyBatchUpdateRequest':
          return AdminPolicyBatchUpdateRequest.fromJson(value);
        case 'AdminPolicyBatchUpdateResponse':
          return AdminPolicyBatchUpdateResponse.fromJson(value);
        case 'AdminPolicyItem':
          return AdminPolicyItem.fromJson(value);
        case 'AdminPolicyUpdateRequest':
          return AdminPolicyUpdateRequest.fromJson(value);
        case 'AdminPolicyUpdateResponse':
          return AdminPolicyUpdateResponse.fromJson(value);
        case 'AdminPriceAlertItem':
          return AdminPriceAlertItem.fromJson(value);
        case 'AdminPriceAlertReportSummary':
          return AdminPriceAlertReportSummary.fromJson(value);
        case 'AdminPriceAlertSourceItem':
          return AdminPriceAlertSourceItem.fromJson(value);
        case 'AdminPriceAlertSummary':
          return AdminPriceAlertSummary.fromJson(value);
        case 'AdminPriceAlertsResponse':
          return AdminPriceAlertsResponse.fromJson(value);
        case 'AdminPriceAlertsResponseCache':
          return AdminPriceAlertsResponseCache.fromJson(value);
        case 'AdminPriceProbeCurrent':
          return AdminPriceProbeCurrent.fromJson(value);
        case 'AdminPriceProbeDiagnosis':
          return AdminPriceProbeDiagnosis.fromJson(value);
        case 'AdminPriceProbeRequest':
          return AdminPriceProbeRequest.fromJson(value);
        case 'AdminPriceProbeResponse':
          return AdminPriceProbeResponse.fromJson(value);
        case 'AdminProviderTestItem':
          return AdminProviderTestItem.fromJson(value);
        case 'AdminProviderTestReport':
          return AdminProviderTestReport.fromJson(value);
        case 'AdminProviderTestReportRun':
          return AdminProviderTestReportRun.fromJson(value);
        case 'AdminProviderTestResponse':
          return AdminProviderTestResponse.fromJson(value);
        case 'AdminProviderTestSummary':
          return AdminProviderTestSummary.fromJson(value);
        case 'AdminRebindExecuteResponse':
          return AdminRebindExecuteResponse.fromJson(value);
        case 'AdminRebindExecuteResponseResult':
          return AdminRebindExecuteResponseResult.fromJson(value);
        case 'AdminRebindPreviewResponse':
          return AdminRebindPreviewResponse.fromJson(value);
        case 'AdminRestoreRequest':
          return AdminRestoreRequest.fromJson(value);
        case 'AdminRestoreResponse':
          return AdminRestoreResponse.fromJson(value);
        case 'AdminRetentionRow':
          return AdminRetentionRow.fromJson(value);
        case 'AdminSmokeTestItem':
          return AdminSmokeTestItem.fromJson(value);
        case 'AdminSmokeTestResponse':
          return AdminSmokeTestResponse.fromJson(value);
        case 'AdminSnapshotCleanupPreviewResponse':
          return AdminSnapshotCleanupPreviewResponse.fromJson(value);
        case 'AdminSnapshotCleanupResponse':
          return AdminSnapshotCleanupResponse.fromJson(value);
        case 'AdminSnapshotHealthResponse':
          return AdminSnapshotHealthResponse.fromJson(value);
        case 'AdminSnapshotHealthUser':
          return AdminSnapshotHealthUser.fromJson(value);
        case 'AdminSnapshotRow':
          return AdminSnapshotRow.fromJson(value);
        case 'AdminSummaryTodoResponse':
          return AdminSummaryTodoResponse.fromJson(value);
        case 'AdminSummaryTodoResponseSnapshot':
          return AdminSummaryTodoResponseSnapshot.fromJson(value);
        case 'AdminTodoItem':
          return AdminTodoItem.fromJson(value);
        case 'AdminUpstreamStatusItem':
          return AdminUpstreamStatusItem.fromJson(value);
        case 'AdminUserDetail':
          return AdminUserDetail.fromJson(value);
        case 'AdminUserMetricsResponse':
          return AdminUserMetricsResponse.fromJson(value);
        case 'AdminUserOpsMetrics':
          return AdminUserOpsMetrics.fromJson(value);
        case 'AdminUserOpsMetricsLastLoginDistribution':
          return AdminUserOpsMetricsLastLoginDistribution.fromJson(value);
        case 'AdminUserPasswordResetResponse':
          return AdminUserPasswordResetResponse.fromJson(value);
        case 'AdminUserPortfolioItem':
          return AdminUserPortfolioItem.fromJson(value);
        case 'AdminUserPortfolioResponse':
          return AdminUserPortfolioResponse.fromJson(value);
        case 'AdminUserPortfolioResponseCache':
          return AdminUserPortfolioResponseCache.fromJson(value);
        case 'AdminUserPortfolioResponseSummary':
          return AdminUserPortfolioResponseSummary.fromJson(value);
        case 'AdminUserSessionsCountResponse':
          return AdminUserSessionsCountResponse.fromJson(value);
        case 'AdminUserSessionsRevokeResponse':
          return AdminUserSessionsRevokeResponse.fromJson(value);
        case 'AdminUserStatusResponse':
          return AdminUserStatusResponse.fromJson(value);
        case 'AdminUserSummary':
          return AdminUserSummary.fromJson(value);
        case 'AdminUserUpdateResponse':
          return AdminUserUpdateResponse.fromJson(value);
        case 'AdminUserUpdateResponseUser':
          return AdminUserUpdateResponseUser.fromJson(value);
        case 'AdminUsersListResponse':
          return AdminUsersListResponse.fromJson(value);
        case 'AnalysisCalendarErrorResponse':
          return AnalysisCalendarErrorResponse.fromJson(value);
        case 'AnalysisCalendarItem':
          return AnalysisCalendarItem.fromJson(value);
        case 'AnalysisCalendarPeriod':
          return AnalysisCalendarPeriod.fromJson(value);
        case 'AnalysisCalendarResponse':
          return AnalysisCalendarResponse.fromJson(value);
        case 'AnalysisCalendarSelectable':
          return AnalysisCalendarSelectable.fromJson(value);
        case 'AnalysisCalendarSelectableDay':
          return AnalysisCalendarSelectableDay.fromJson(value);
        case 'AnalysisCalendarSelectableMonth':
          return AnalysisCalendarSelectableMonth.fromJson(value);
        case 'AnalysisMarketBreakdownItem':
          return AnalysisMarketBreakdownItem.fromJson(value);
        case 'AnalysisMarketBreakdownItemMarkets':
          return AnalysisMarketBreakdownItemMarkets.fromJson(value);
        case 'AnalysisMarketBreakdownResponse':
          return AnalysisMarketBreakdownResponse.fromJson(value);
        case 'AnalysisOverviewResponse':
          return AnalysisOverviewResponse.fromJson(value);
        case 'AnalysisRankItem':
          return AnalysisRankItem.fromJson(value);
        case 'AnalysisRankResponse':
          return AnalysisRankResponse.fromJson(value);
        case 'ApiAdminApisProviderTestPostRequest':
          return ApiAdminApisProviderTestPostRequest.fromJson(value);
        case 'ApiAdminConfigResetPostRequest':
          return ApiAdminConfigResetPostRequest.fromJson(value);
        case 'ApiAdminDataRebindExecutePostRequest':
          return ApiAdminDataRebindExecutePostRequest.fromJson(value);
        case 'ApiAdminDataSnapshotCleanupMarketClosedPostRequest':
          return ApiAdminDataSnapshotCleanupMarketClosedPostRequest.fromJson(value);
        case 'ApiAdminDataSnapshotCleanupMarketClosedPreviewPostRequest':
          return ApiAdminDataSnapshotCleanupMarketClosedPreviewPostRequest.fromJson(value);
        case 'ApiAdminDataSnapshotCleanupWeekendPostRequest':
          return ApiAdminDataSnapshotCleanupWeekendPostRequest.fromJson(value);
        case 'ApiAdminOpsAppUpdateUpdatePostRequest':
          return ApiAdminOpsAppUpdateUpdatePostRequest.fromJson(value);
        case 'ApiAdminOpsInviteAcquireUpdatePostRequest':
          return ApiAdminOpsInviteAcquireUpdatePostRequest.fromJson(value);
        case 'ApiAdminUsersDisablePostRequest':
          return ApiAdminUsersDisablePostRequest.fromJson(value);
        case 'ApiAdminUsersPasswordResetPostRequest':
          return ApiAdminUsersPasswordResetPostRequest.fromJson(value);
        case 'ApiAdminUsersStatusPostRequest':
          return ApiAdminUsersStatusPostRequest.fromJson(value);
        case 'ApiAdminUsersUpdatePostRequest':
          return ApiAdminUsersUpdatePostRequest.fromJson(value);
        case 'ApiSnapshotTriggerPost200Response':
          return ApiSnapshotTriggerPost200Response.fromJson(value);
        case 'AppVersionResponse':
          return AppVersionResponse.fromJson(value);
        case 'AssetTrendItem':
          return AssetTrendItem.fromJson(value);
        case 'AssetTrendPoint':
          return AssetTrendPoint.fromJson(value);
        case 'AssetTrendsRequest':
          return AssetTrendsRequest.fromJson(value);
        case 'AssetTrendsRequestItem':
          return AssetTrendsRequestItem.fromJson(value);
        case 'AssetTrendsResponse':
          return AssetTrendsResponse.fromJson(value);
        case 'BootstrapCredentialsRequest':
          return BootstrapCredentialsRequest.fromJson(value);
        case 'BuyPortfolioAssetRequest':
          return BuyPortfolioAssetRequest.fromJson(value);
        case 'ChangePasswordRequest':
          return ChangePasswordRequest.fromJson(value);
        case 'DeleteCashAssetRequest':
          return DeleteCashAssetRequest.fromJson(value);
        case 'DeletePortfolioAssetRequest':
          return DeletePortfolioAssetRequest.fromJson(value);
        case 'Error':
          return Error.fromJson(value);
        case 'GetBatchPricesRequest':
          return GetBatchPricesRequest.fromJson(value);
        case 'GetHealth200Response':
          return GetHealth200Response.fromJson(value);
        case 'GetPrice200Response':
          return GetPrice200Response.fromJson(value);
        case 'LoginRequest':
          return LoginRequest.fromJson(value);
        case 'LogoutRequest':
          return LogoutRequest.fromJson(value);
        case 'MarketIndexItem':
          return MarketIndexItem.fromJson(value);
        case 'MarketStatusItem':
          return MarketStatusItem.fromJson(value);
        case 'MarketStatusResponse':
          return MarketStatusResponse.fromJson(value);
        case 'ModifyPortfolioAssetRequest':
          return ModifyPortfolioAssetRequest.fromJson(value);
        case 'PnlOverviewItem':
          return PnlOverviewItem.fromJson(value);
        case 'PortfolioBuyWithCashRequest':
          return PortfolioBuyWithCashRequest.fromJson(value);
        case 'PortfolioBuyWithCashResponse':
          return PortfolioBuyWithCashResponse.fromJson(value);
        case 'PortfolioDeleteCorrectiveRequest':
          return PortfolioDeleteCorrectiveRequest.fromJson(value);
        case 'PortfolioDeleteCorrectiveResponse':
          return PortfolioDeleteCorrectiveResponse.fromJson(value);
        case 'PortfolioDeleteCorrectiveResponseDeleted':
          return PortfolioDeleteCorrectiveResponseDeleted.fromJson(value);
        case 'PortfolioItem':
          return PortfolioItem.fromJson(value);
        case 'PortfolioTransactionRecord':
          return PortfolioTransactionRecord.fromJson(value);
        case 'PortfolioTransactionsResponse':
          return PortfolioTransactionsResponse.fromJson(value);
        case 'PortfolioUndoRequest':
          return PortfolioUndoRequest.fromJson(value);
        case 'PortfolioUndoResponse':
          return PortfolioUndoResponse.fromJson(value);
        case 'PriceCacheStats':
          return PriceCacheStats.fromJson(value);
        case 'PriceHealthResponse':
          return PriceHealthResponse.fromJson(value);
        case 'PriceRuntimeMetrics':
          return PriceRuntimeMetrics.fromJson(value);
        case 'PriceSourceHealthItem':
          return PriceSourceHealthItem.fromJson(value);
        case 'RefreshSessionRequest':
          return RefreshSessionRequest.fromJson(value);
        case 'RegisterRequest':
          return RegisterRequest.fromJson(value);
        case 'RequestRuntimeMetrics':
          return RequestRuntimeMetrics.fromJson(value);
        case 'RequestRuntimeMetricsStorage':
          return RequestRuntimeMetricsStorage.fromJson(value);
        case 'SnapshotFixRequest':
          return SnapshotFixRequest.fromJson(value);
        case 'SnapshotSaveRequest':
          return SnapshotSaveRequest.fromJson(value);
        case 'StatusOk':
          return StatusOk.fromJson(value);
        case 'SyncBootstrapRequest':
          return SyncBootstrapRequest.fromJson(value);
        case 'SyncBootstrapResponse':
          return SyncBootstrapResponse.fromJson(value);
        case 'SyncBootstrapResponseQuotePolicy':
          return SyncBootstrapResponseQuotePolicy.fromJson(value);
        case 'SyncBootstrapResponseVersions':
          return SyncBootstrapResponseVersions.fromJson(value);
        case 'UpdateCashAssetRequest':
          return UpdateCashAssetRequest.fromJson(value);
        case 'UpdatePortfolioAssetFieldRequest':
          return UpdatePortfolioAssetFieldRequest.fromJson(value);
        case 'UpdateProfileRequest':
          return UpdateProfileRequest.fromJson(value);
        case 'ValidateInviteCodeRequest':
          return ValidateInviteCodeRequest.fromJson(value);
        case 'WebConfigResponse':
          return WebConfigResponse.fromJson(value);
        default:
          dynamic match;
          if (value is List && (match = _regList.firstMatch(targetType)?.group(1)) != null) {
            return value
              .map<dynamic>((dynamic v) => fromJson(v, match, growable: growable,))
              .toList(growable: growable);
          }
          if (value is Set && (match = _regSet.firstMatch(targetType)?.group(1)) != null) {
            return value
              .map<dynamic>((dynamic v) => fromJson(v, match, growable: growable,))
              .toSet();
          }
          if (value is Map && (match = _regMap.firstMatch(targetType)?.group(1)) != null) {
            return Map<String, dynamic>.fromIterables(
              value.keys.cast<String>(),
              value.values.map<dynamic>((dynamic v) => fromJson(v, match, growable: growable,)),
            );
          }
      }
    } on Exception catch (error, trace) {
      throw ApiException.withInner(HttpStatus.internalServerError, 'Exception during deserialization.', error, trace,);
    }
    throw ApiException(HttpStatus.internalServerError, 'Could not find a suitable class for deserialization',);
  }
}

/// Primarily intended for use in an isolate.
class DeserializationMessage {
  const DeserializationMessage({
    required this.json,
    required this.targetType,
    this.growable = false,
  });

  /// The JSON value to deserialize.
  final String json;

  /// Target type to deserialize to.
  final String targetType;

  /// Whether to make deserialized lists or maps growable.
  final bool growable;
}

/// Primarily intended for use in an isolate.
Future<dynamic> decodeAsync(DeserializationMessage message) async {
  // Remove all spaces. Necessary for regular expressions as well.
  final targetType = message.targetType.replaceAll(' ', '');

  // If the expected target type is String, nothing to do...
  return targetType == 'String'
    ? message.json
    : json.decode(message.json);
}

/// Primarily intended for use in an isolate.
Future<dynamic> deserializeAsync(DeserializationMessage message) async {
  // Remove all spaces. Necessary for regular expressions as well.
  final targetType = message.targetType.replaceAll(' ', '');

  // If the expected target type is String, nothing to do...
  return targetType == 'String'
    ? message.json
    : ApiClient.fromJson(
        json.decode(message.json),
        targetType,
        growable: message.growable,
      );
}

/// Primarily intended for use in an isolate.
Future<String> serializeAsync(Object? value) async => value == null ? '' : json.encode(value);
