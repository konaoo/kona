# kaka_openapi.api.DefaultApi

## Load the API package
```dart
import 'package:kaka_openapi/api.dart';
```

All URIs are relative to *http://114.132.238.12*

Method | HTTP request | Description
------------- | ------------- | -------------
[**addCashAsset**](DefaultApi.md#addcashasset) | **POST** /api/cash_assets/add | Add cash asset
[**addLiability**](DefaultApi.md#addliability) | **POST** /api/liabilities/add | Add liability
[**addOtherAsset**](DefaultApi.md#addotherasset) | **POST** /api/other_assets/add | Add other asset
[**addPortfolioAdjustmentEvent**](DefaultApi.md#addportfolioadjustmentevent) | **POST** /api/portfolio/adjustment_event | Add portfolio cash event
[**addPortfolioAsset**](DefaultApi.md#addportfolioasset) | **POST** /api/portfolio/add | Add asset
[**apiAdminApisHealthGet**](DefaultApi.md#apiadminapishealthget) | **GET** /api/admin/apis/health | 后台接口健康与策略汇总
[**apiAdminApisPoliciesBatchUpdatePost**](DefaultApi.md#apiadminapispoliciesbatchupdatepost) | **POST** /api/admin/apis/policies/batch_update | 批量更新后台接口策略
[**apiAdminApisPoliciesGet**](DefaultApi.md#apiadminapispoliciesget) | **GET** /api/admin/apis/policies | 后台接口策略列表
[**apiAdminApisPoliciesUpdatePost**](DefaultApi.md#apiadminapispoliciesupdatepost) | **POST** /api/admin/apis/policies/update | 更新单条后台接口策略
[**apiAdminApisPriceAlertsGet**](DefaultApi.md#apiadminapispricealertsget) | **GET** /api/admin/apis/price_alerts | 行情价格告警与历史快照
[**apiAdminApisPriceProbePost**](DefaultApi.md#apiadminapispriceprobepost) | **POST** /api/admin/apis/price_probe | 单资产价格诊断
[**apiAdminApisProviderTestPost**](DefaultApi.md#apiadminapisprovidertestpost) | **POST** /api/admin/apis/provider_test | 单个行情/汇率源测试
[**apiAdminApisProviderTestsLatestGet**](DefaultApi.md#apiadminapisprovidertestslatestget) | **GET** /api/admin/apis/provider_tests/latest | 最近一次行情源测试报告
[**apiAdminApisProviderTestsRunPost**](DefaultApi.md#apiadminapisprovidertestsrunpost) | **POST** /api/admin/apis/provider_tests/run | 运行行情源测试并保存报告
[**apiAdminApisSmokeTestPost**](DefaultApi.md#apiadminapissmoketestpost) | **POST** /api/admin/apis/smoke_test | 后台冒烟测试
[**apiAdminConfigGet**](DefaultApi.md#apiadminconfigget) | **GET** /api/admin/config | 后台系统配置白名单
[**apiAdminConfigResetPost**](DefaultApi.md#apiadminconfigresetpost) | **POST** /api/admin/config/reset | 恢复系统配置默认值
[**apiAdminConfigUpdatePost**](DefaultApi.md#apiadminconfigupdatepost) | **POST** /api/admin/config/update | 更新系统配置
[**apiAdminDataBackupLatestGet**](DefaultApi.md#apiadmindatabackuplatestget) | **GET** /api/admin/data/backup/latest | 获取最近一次备份信息
[**apiAdminDataBackupPost**](DefaultApi.md#apiadmindatabackuppost) | **POST** /api/admin/data/backup | 创建数据库备份
[**apiAdminDataRebindExecutePost**](DefaultApi.md#apiadmindatarebindexecutepost) | **POST** /api/admin/data/rebind/execute | 执行历史数据归属迁移
[**apiAdminDataRebindPreviewGet**](DefaultApi.md#apiadmindatarebindpreviewget) | **GET** /api/admin/data/rebind/preview | 预览历史数据归属迁移
[**apiAdminDataRestorePost**](DefaultApi.md#apiadmindatarestorepost) | **POST** /api/admin/data/restore | 恢复数据库备份
[**apiAdminDataSnapshotCleanupMarketClosedPost**](DefaultApi.md#apiadmindatasnapshotcleanupmarketclosedpost) | **POST** /api/admin/data/snapshot/cleanup_market_closed | 清理休市日快照日盈亏
[**apiAdminDataSnapshotCleanupMarketClosedPreviewPost**](DefaultApi.md#apiadmindatasnapshotcleanupmarketclosedpreviewpost) | **POST** /api/admin/data/snapshot/cleanup_market_closed/preview | 预览休市日清理影响范围
[**apiAdminDataSnapshotCleanupWeekendPost**](DefaultApi.md#apiadmindatasnapshotcleanupweekendpost) | **POST** /api/admin/data/snapshot/cleanup_weekend | 清理周末快照日盈亏
[**apiAdminDataSnapshotCleanupWeekendPreviewPost**](DefaultApi.md#apiadmindatasnapshotcleanupweekendpreviewpost) | **POST** /api/admin/data/snapshot/cleanup_weekend/preview | 预览周末清理影响范围
[**apiAdminDataSnapshotHealthGet**](DefaultApi.md#apiadmindatasnapshothealthget) | **GET** /api/admin/data/snapshot/health | 快照任务健康检查
[**apiAdminDataSnapshotTriggerPost**](DefaultApi.md#apiadmindatasnapshottriggerpost) | **POST** /api/admin/data/snapshot/trigger | 手动触发快照
[**apiAdminDataSnapshotsGet**](DefaultApi.md#apiadmindatasnapshotsget) | **GET** /api/admin/data/snapshots | 查询快照明细
[**apiAdminInvitesExportGet**](DefaultApi.md#apiadmininvitesexportget) | **GET** /api/admin/invites/export | 导出邀请码 CSV
[**apiAdminInvitesGeneratePost**](DefaultApi.md#apiadmininvitesgeneratepost) | **POST** /api/admin/invites/generate | 生成邀请码
[**apiAdminInvitesGet**](DefaultApi.md#apiadmininvitesget) | **GET** /api/admin/invites | 邀请码列表
[**apiAdminInvitesRevokePost**](DefaultApi.md#apiadmininvitesrevokepost) | **POST** /api/admin/invites/revoke | 作废邀请码
[**apiAdminInvitesStatsGet**](DefaultApi.md#apiadmininvitesstatsget) | **GET** /api/admin/invites/stats | 邀请码统计
[**apiAdminMetaDictionariesGet**](DefaultApi.md#apiadminmetadictionariesget) | **GET** /api/admin/meta/dictionaries | 后台字典与标签
[**apiAdminOpsAppUpdateGet**](DefaultApi.md#apiadminopsappupdateget) | **GET** /api/admin/ops/app_update | 运营配置-更新提示
[**apiAdminOpsAppUpdateUpdatePost**](DefaultApi.md#apiadminopsappupdateupdatepost) | **POST** /api/admin/ops/app_update/update | 更新运营配置-更新提示
[**apiAdminOpsInviteAcquireGet**](DefaultApi.md#apiadminopsinviteacquireget) | **GET** /api/admin/ops/invite_acquire | 运营配置-邀请码获取页
[**apiAdminOpsInviteAcquireUpdatePost**](DefaultApi.md#apiadminopsinviteacquireupdatepost) | **POST** /api/admin/ops/invite_acquire/update | 更新运营配置-邀请码获取页
[**apiAdminOpsIosQrGet**](DefaultApi.md#apiadminopsiosqrget) | **GET** /api/admin/ops/ios_qr | 运营配置-iOS 下载二维码
[**apiAdminOpsIosQrUpdatePost**](DefaultApi.md#apiadminopsiosqrupdatepost) | **POST** /api/admin/ops/ios_qr/update | 更新运营配置-iOS 下载二维码
[**apiAdminOpsUserGroupGet**](DefaultApi.md#apiadminopsusergroupget) | **GET** /api/admin/ops/user_group | 运营配置-用户群页
[**apiAdminOpsUserGroupUpdatePost**](DefaultApi.md#apiadminopsusergroupupdatepost) | **POST** /api/admin/ops/user_group/update | 更新运营配置-用户群页
[**apiAdminOverviewGet**](DefaultApi.md#apiadminoverviewget) | **GET** /api/admin/overview | 后台概览看板
[**apiAdminSummaryTodoGet**](DefaultApi.md#apiadminsummarytodoget) | **GET** /api/admin/summary/todo | 后台待办与巡检摘要
[**apiAdminUsersDisablePost**](DefaultApi.md#apiadminusersdisablepost) | **POST** /api/admin/users/disable | 停用用户
[**apiAdminUsersEnablePost**](DefaultApi.md#apiadminusersenablepost) | **POST** /api/admin/users/enable | 启用用户
[**apiAdminUsersGet**](DefaultApi.md#apiadminusersget) | **GET** /api/admin/users | 后台用户列表
[**apiAdminUsersMetricsGet**](DefaultApi.md#apiadminusersmetricsget) | **GET** /api/admin/users/metrics | 用户运营指标
[**apiAdminUsersPasswordResetPost**](DefaultApi.md#apiadminuserspasswordresetpost) | **POST** /api/admin/users/password/reset | 重置用户密码
[**apiAdminUsersSessionsCountGet**](DefaultApi.md#apiadminuserssessionscountget) | **GET** /api/admin/users/sessions/count | 用户在线会话数
[**apiAdminUsersSessionsRevokePost**](DefaultApi.md#apiadminuserssessionsrevokepost) | **POST** /api/admin/users/sessions/revoke | 强制用户下线
[**apiAdminUsersStatusPost**](DefaultApi.md#apiadminusersstatuspost) | **POST** /api/admin/users/status | 设置用户状态
[**apiAdminUsersUpdatePost**](DefaultApi.md#apiadminusersupdatepost) | **POST** /api/admin/users/update | 更新用户信息
[**apiAdminUsersUserIdGet**](DefaultApi.md#apiadminusersuseridget) | **GET** /api/admin/users/{user_id} | 用户详情
[**apiAdminUsersUserIdPortfolioGet**](DefaultApi.md#apiadminusersuseridportfolioget) | **GET** /api/admin/users/{user_id}/portfolio | 用户持仓与资产概览
[**apiSnapshotFixPost**](DefaultApi.md#apisnapshotfixpost) | **POST** /api/snapshot/fix | Fix snapshot day_pnl
[**apiSnapshotSavePost**](DefaultApi.md#apisnapshotsavepost) | **POST** /api/snapshot/save | Save daily snapshot
[**apiSnapshotTriggerPost**](DefaultApi.md#apisnapshottriggerpost) | **POST** /api/snapshot/trigger | Trigger snapshot
[**bootstrapCredentials**](DefaultApi.md#bootstrapcredentials) | **POST** /api/auth/bootstrap_credentials | Bootstrap username/password for legacy users
[**bootstrapSync**](DefaultApi.md#bootstrapsync) | **POST** /api/sync/bootstrap | 客户端增量同步引导
[**buyPortfolioAsset**](DefaultApi.md#buyportfolioasset) | **POST** /api/portfolio/buy | Buy asset
[**buyPortfolioAssetWithCash**](DefaultApi.md#buyportfolioassetwithcash) | **POST** /api/portfolio/buy_with_cash | 现金账户买入资产
[**changePassword**](DefaultApi.md#changepassword) | **POST** /api/auth/password/change | Change password
[**checkSettingsApi**](DefaultApi.md#checksettingsapi) | **GET** /api/settings/check_api | Check API status
[**deleteCashAsset**](DefaultApi.md#deletecashasset) | **POST** /api/cash_assets/delete | Delete cash asset
[**deleteLiability**](DefaultApi.md#deleteliability) | **POST** /api/liabilities/delete | Delete liability
[**deleteOtherAsset**](DefaultApi.md#deleteotherasset) | **POST** /api/other_assets/delete | Delete other asset
[**deletePortfolioAsset**](DefaultApi.md#deleteportfolioasset) | **POST** /api/portfolio/delete | Delete asset
[**deletePortfolioAssetCorrective**](DefaultApi.md#deleteportfolioassetcorrective) | **POST** /api/portfolio/delete_corrective | 纠正性删除资产及历史记录
[**downloadSettingsBackup**](DefaultApi.md#downloadsettingsbackup) | **GET** /api/settings/backup | Download DB backup
[**getAnalysisCalendar**](DefaultApi.md#getanalysiscalendar) | **GET** /api/analysis/calendar | PnL calendar
[**getAnalysisMarketBreakdown**](DefaultApi.md#getanalysismarketbreakdown) | **GET** /api/analysis/calendar/market_breakdown | 收益日历按市场拆分
[**getAnalysisOverview**](DefaultApi.md#getanalysisoverview) | **GET** /api/analysis/overview | PnL overview
[**getAnalysisRank**](DefaultApi.md#getanalysisrank) | **GET** /api/analysis/rank | PnL rank
[**getAppVersion**](DefaultApi.md#getappversion) | **GET** /api/app/version | 获取客户端更新配置
[**getAssetTrends**](DefaultApi.md#getassettrends) | **POST** /api/asset/trends | 批量资产趋势线
[**getBatchPrices**](DefaultApi.md#getbatchprices) | **POST** /api/prices/batch | Get batch prices
[**getCashAssets**](DefaultApi.md#getcashassets) | **GET** /api/cash_assets | Get cash assets
[**getCurrentUser**](DefaultApi.md#getcurrentuser) | **GET** /api/auth/me | Current user
[**getHealth**](DefaultApi.md#gethealth) | **GET** /health | Health check
[**getHistory**](DefaultApi.md#gethistory) | **GET** /api/history | Get history
[**getLatestNews**](DefaultApi.md#getlatestnews) | **GET** /api/news/latest | Latest news
[**getLiabilities**](DefaultApi.md#getliabilities) | **GET** /api/liabilities | Get liabilities
[**getMarketIndices**](DefaultApi.md#getmarketindices) | **GET** /api/market/indices | 首页指数与汇率
[**getMarketStatus**](DefaultApi.md#getmarketstatus) | **GET** /api/market/status | 市场开休市状态
[**getOtherAssets**](DefaultApi.md#getotherassets) | **GET** /api/other_assets | Get other assets
[**getPortfolio**](DefaultApi.md#getportfolio) | **GET** /api/portfolio | Get portfolio
[**getPortfolioTransactions**](DefaultApi.md#getportfoliotransactions) | **GET** /api/portfolio/transactions | Get portfolio transaction and correction records
[**getPrice**](DefaultApi.md#getprice) | **GET** /api/price | Get a single price
[**getRates**](DefaultApi.md#getrates) | **GET** /api/rates | Get FX rates
[**getSettingsInfo**](DefaultApi.md#getsettingsinfo) | **GET** /api/settings/info | System info
[**getSystemPriceHealth**](DefaultApi.md#getsystempricehealth) | **GET** /api/system/price_health | 行情运行健康指标
[**getTransactions**](DefaultApi.md#gettransactions) | **GET** /api/transactions | Get transactions
[**getWebConfig**](DefaultApi.md#getwebconfig) | **GET** /api/web/config | Web 门户公开配置
[**login**](DefaultApi.md#login) | **POST** /api/auth/login | Login
[**logout**](DefaultApi.md#logout) | **POST** /api/auth/logout | Logout
[**modifyPortfolioAsset**](DefaultApi.md#modifyportfolioasset) | **POST** /api/portfolio/modify | Modify asset qty/price
[**refreshSession**](DefaultApi.md#refreshsession) | **POST** /api/auth/refresh | Refresh access token
[**register**](DefaultApi.md#register) | **POST** /api/auth/register | Register with invite code
[**restoreSettingsBackup**](DefaultApi.md#restoresettingsbackup) | **POST** /api/settings/restore | Restore DB
[**searchSecurities**](DefaultApi.md#searchsecurities) | **GET** /api/search | Search securities
[**sellPortfolioAsset**](DefaultApi.md#sellportfolioasset) | **POST** /api/portfolio/sell | Sell asset
[**sendAuthCode**](DefaultApi.md#sendauthcode) | **POST** /api/auth/send_code | Deprecated endpoint, returns 410
[**undoPortfolioOperation**](DefaultApi.md#undoportfoliooperation) | **POST** /api/portfolio/undo | 撤销最近一次投资操作
[**updateCashAsset**](DefaultApi.md#updatecashasset) | **POST** /api/cash_assets/update | Update cash asset
[**updateLiability**](DefaultApi.md#updateliability) | **POST** /api/liabilities/update | Update liability
[**updateOtherAsset**](DefaultApi.md#updateotherasset) | **POST** /api/other_assets/update | Update other asset
[**updatePortfolioAssetField**](DefaultApi.md#updateportfolioassetfield) | **POST** /api/portfolio/update | Update asset field
[**updateProfile**](DefaultApi.md#updateprofile) | **POST** /api/auth/profile | Update user profile
[**validateInviteCode**](DefaultApi.md#validateinvitecode) | **POST** /api/auth/invite/validate | Validate invite code


# **addCashAsset**
> StatusOk addCashAsset(addCashAssetRequest)

Add cash asset

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final addCashAssetRequest = AddCashAssetRequest(); // AddCashAssetRequest | 

try {
    final result = api_instance.addCashAsset(addCashAssetRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->addCashAsset: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **addCashAssetRequest** | [**AddCashAssetRequest**](AddCashAssetRequest.md)|  | 

### Return type

[**StatusOk**](StatusOk.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **addLiability**
> StatusOk addLiability(addCashAssetRequest)

Add liability

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final addCashAssetRequest = AddCashAssetRequest(); // AddCashAssetRequest | 

try {
    final result = api_instance.addLiability(addCashAssetRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->addLiability: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **addCashAssetRequest** | [**AddCashAssetRequest**](AddCashAssetRequest.md)|  | 

### Return type

[**StatusOk**](StatusOk.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **addOtherAsset**
> StatusOk addOtherAsset(addCashAssetRequest)

Add other asset

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final addCashAssetRequest = AddCashAssetRequest(); // AddCashAssetRequest | 

try {
    final result = api_instance.addOtherAsset(addCashAssetRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->addOtherAsset: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **addCashAssetRequest** | [**AddCashAssetRequest**](AddCashAssetRequest.md)|  | 

### Return type

[**StatusOk**](StatusOk.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **addPortfolioAdjustmentEvent**
> StatusOk addPortfolioAdjustmentEvent(addPortfolioAdjustmentEventRequest)

Add portfolio cash event

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final addPortfolioAdjustmentEventRequest = AddPortfolioAdjustmentEventRequest(); // AddPortfolioAdjustmentEventRequest | 

try {
    final result = api_instance.addPortfolioAdjustmentEvent(addPortfolioAdjustmentEventRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->addPortfolioAdjustmentEvent: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **addPortfolioAdjustmentEventRequest** | [**AddPortfolioAdjustmentEventRequest**](AddPortfolioAdjustmentEventRequest.md)|  | 

### Return type

[**StatusOk**](StatusOk.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **addPortfolioAsset**
> StatusOk addPortfolioAsset(addPortfolioAssetRequest)

Add asset

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final addPortfolioAssetRequest = AddPortfolioAssetRequest(); // AddPortfolioAssetRequest | 

try {
    final result = api_instance.addPortfolioAsset(addPortfolioAssetRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->addPortfolioAsset: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **addPortfolioAssetRequest** | [**AddPortfolioAssetRequest**](AddPortfolioAssetRequest.md)|  | 

### Return type

[**StatusOk**](StatusOk.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminApisHealthGet**
> AdminApiHealthResponse apiAdminApisHealthGet()

后台接口健康与策略汇总

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();

try {
    final result = api_instance.apiAdminApisHealthGet();
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminApisHealthGet: $e\n');
}
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**AdminApiHealthResponse**](AdminApiHealthResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminApisPoliciesBatchUpdatePost**
> AdminPolicyBatchUpdateResponse apiAdminApisPoliciesBatchUpdatePost(adminPolicyBatchUpdateRequest)

批量更新后台接口策略

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final adminPolicyBatchUpdateRequest = AdminPolicyBatchUpdateRequest(); // AdminPolicyBatchUpdateRequest | 

try {
    final result = api_instance.apiAdminApisPoliciesBatchUpdatePost(adminPolicyBatchUpdateRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminApisPoliciesBatchUpdatePost: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **adminPolicyBatchUpdateRequest** | [**AdminPolicyBatchUpdateRequest**](AdminPolicyBatchUpdateRequest.md)|  | 

### Return type

[**AdminPolicyBatchUpdateResponse**](AdminPolicyBatchUpdateResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminApisPoliciesGet**
> AdminPoliciesResponse apiAdminApisPoliciesGet(scopeType)

后台接口策略列表

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final scopeType = scopeType_example; // String | 

try {
    final result = api_instance.apiAdminApisPoliciesGet(scopeType);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminApisPoliciesGet: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **scopeType** | **String**|  | [optional] 

### Return type

[**AdminPoliciesResponse**](AdminPoliciesResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminApisPoliciesUpdatePost**
> AdminPolicyUpdateResponse apiAdminApisPoliciesUpdatePost(adminPolicyUpdateRequest)

更新单条后台接口策略

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final adminPolicyUpdateRequest = AdminPolicyUpdateRequest(); // AdminPolicyUpdateRequest | 

try {
    final result = api_instance.apiAdminApisPoliciesUpdatePost(adminPolicyUpdateRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminApisPoliciesUpdatePost: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **adminPolicyUpdateRequest** | [**AdminPolicyUpdateRequest**](AdminPolicyUpdateRequest.md)|  | 

### Return type

[**AdminPolicyUpdateResponse**](AdminPolicyUpdateResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminApisPriceAlertsGet**
> AdminPriceAlertsResponse apiAdminApisPriceAlertsGet(force)

行情价格告警与历史快照

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final force = true; // bool | 

try {
    final result = api_instance.apiAdminApisPriceAlertsGet(force);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminApisPriceAlertsGet: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **force** | **bool**|  | [optional] 

### Return type

[**AdminPriceAlertsResponse**](AdminPriceAlertsResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminApisPriceProbePost**
> AdminPriceProbeResponse apiAdminApisPriceProbePost(adminPriceProbeRequest)

单资产价格诊断

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final adminPriceProbeRequest = AdminPriceProbeRequest(); // AdminPriceProbeRequest | 

try {
    final result = api_instance.apiAdminApisPriceProbePost(adminPriceProbeRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminApisPriceProbePost: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **adminPriceProbeRequest** | [**AdminPriceProbeRequest**](AdminPriceProbeRequest.md)|  | 

### Return type

[**AdminPriceProbeResponse**](AdminPriceProbeResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminApisProviderTestPost**
> AdminProviderTestResponse apiAdminApisProviderTestPost(apiAdminApisProviderTestPostRequest)

单个行情/汇率源测试

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final apiAdminApisProviderTestPostRequest = ApiAdminApisProviderTestPostRequest(); // ApiAdminApisProviderTestPostRequest | 

try {
    final result = api_instance.apiAdminApisProviderTestPost(apiAdminApisProviderTestPostRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminApisProviderTestPost: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **apiAdminApisProviderTestPostRequest** | [**ApiAdminApisProviderTestPostRequest**](ApiAdminApisProviderTestPostRequest.md)|  | 

### Return type

[**AdminProviderTestResponse**](AdminProviderTestResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminApisProviderTestsLatestGet**
> AdminProviderTestReport apiAdminApisProviderTestsLatestGet()

最近一次行情源测试报告

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();

try {
    final result = api_instance.apiAdminApisProviderTestsLatestGet();
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminApisProviderTestsLatestGet: $e\n');
}
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**AdminProviderTestReport**](AdminProviderTestReport.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminApisProviderTestsRunPost**
> AdminProviderTestReportRun apiAdminApisProviderTestsRunPost()

运行行情源测试并保存报告

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();

try {
    final result = api_instance.apiAdminApisProviderTestsRunPost();
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminApisProviderTestsRunPost: $e\n');
}
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**AdminProviderTestReportRun**](AdminProviderTestReportRun.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminApisSmokeTestPost**
> AdminSmokeTestResponse apiAdminApisSmokeTestPost()

后台冒烟测试

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();

try {
    final result = api_instance.apiAdminApisSmokeTestPost();
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminApisSmokeTestPost: $e\n');
}
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**AdminSmokeTestResponse**](AdminSmokeTestResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminConfigGet**
> AdminConfigListResponse apiAdminConfigGet()

后台系统配置白名单

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();

try {
    final result = api_instance.apiAdminConfigGet();
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminConfigGet: $e\n');
}
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**AdminConfigListResponse**](AdminConfigListResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminConfigResetPost**
> AdminConfigUpdateResponse apiAdminConfigResetPost(apiAdminConfigResetPostRequest)

恢复系统配置默认值

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final apiAdminConfigResetPostRequest = ApiAdminConfigResetPostRequest(); // ApiAdminConfigResetPostRequest | 

try {
    final result = api_instance.apiAdminConfigResetPost(apiAdminConfigResetPostRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminConfigResetPost: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **apiAdminConfigResetPostRequest** | [**ApiAdminConfigResetPostRequest**](ApiAdminConfigResetPostRequest.md)|  | [optional] 

### Return type

[**AdminConfigUpdateResponse**](AdminConfigUpdateResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminConfigUpdatePost**
> AdminConfigUpdateResponse apiAdminConfigUpdatePost(adminConfigUpdateRequest)

更新系统配置

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final adminConfigUpdateRequest = AdminConfigUpdateRequest(); // AdminConfigUpdateRequest | 

try {
    final result = api_instance.apiAdminConfigUpdatePost(adminConfigUpdateRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminConfigUpdatePost: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **adminConfigUpdateRequest** | [**AdminConfigUpdateRequest**](AdminConfigUpdateRequest.md)|  | 

### Return type

[**AdminConfigUpdateResponse**](AdminConfigUpdateResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminDataBackupLatestGet**
> AdminBackupLatestResponse apiAdminDataBackupLatestGet(backupDir)

获取最近一次备份信息

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final backupDir = backupDir_example; // String | 

try {
    final result = api_instance.apiAdminDataBackupLatestGet(backupDir);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminDataBackupLatestGet: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **backupDir** | **String**|  | [optional] 

### Return type

[**AdminBackupLatestResponse**](AdminBackupLatestResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminDataBackupPost**
> AdminBackupResponse apiAdminDataBackupPost(adminBackupRequest)

创建数据库备份

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final adminBackupRequest = AdminBackupRequest(); // AdminBackupRequest | 

try {
    final result = api_instance.apiAdminDataBackupPost(adminBackupRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminDataBackupPost: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **adminBackupRequest** | [**AdminBackupRequest**](AdminBackupRequest.md)|  | [optional] 

### Return type

[**AdminBackupResponse**](AdminBackupResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminDataRebindExecutePost**
> AdminRebindExecuteResponse apiAdminDataRebindExecutePost(apiAdminDataRebindExecutePostRequest)

执行历史数据归属迁移

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final apiAdminDataRebindExecutePostRequest = ApiAdminDataRebindExecutePostRequest(); // ApiAdminDataRebindExecutePostRequest | 

try {
    final result = api_instance.apiAdminDataRebindExecutePost(apiAdminDataRebindExecutePostRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminDataRebindExecutePost: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **apiAdminDataRebindExecutePostRequest** | [**ApiAdminDataRebindExecutePostRequest**](ApiAdminDataRebindExecutePostRequest.md)|  | 

### Return type

[**AdminRebindExecuteResponse**](AdminRebindExecuteResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminDataRebindPreviewGet**
> AdminRebindPreviewResponse apiAdminDataRebindPreviewGet(targetUserId)

预览历史数据归属迁移

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final targetUserId = targetUserId_example; // String | 

try {
    final result = api_instance.apiAdminDataRebindPreviewGet(targetUserId);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminDataRebindPreviewGet: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **targetUserId** | **String**|  | 

### Return type

[**AdminRebindPreviewResponse**](AdminRebindPreviewResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminDataRestorePost**
> AdminRestoreResponse apiAdminDataRestorePost(adminRestoreRequest)

恢复数据库备份

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final adminRestoreRequest = AdminRestoreRequest(); // AdminRestoreRequest | 

try {
    final result = api_instance.apiAdminDataRestorePost(adminRestoreRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminDataRestorePost: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **adminRestoreRequest** | [**AdminRestoreRequest**](AdminRestoreRequest.md)|  | [optional] 

### Return type

[**AdminRestoreResponse**](AdminRestoreResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminDataSnapshotCleanupMarketClosedPost**
> AdminSnapshotCleanupResponse apiAdminDataSnapshotCleanupMarketClosedPost(apiAdminDataSnapshotCleanupMarketClosedPostRequest)

清理休市日快照日盈亏

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final apiAdminDataSnapshotCleanupMarketClosedPostRequest = ApiAdminDataSnapshotCleanupMarketClosedPostRequest(); // ApiAdminDataSnapshotCleanupMarketClosedPostRequest | 

try {
    final result = api_instance.apiAdminDataSnapshotCleanupMarketClosedPost(apiAdminDataSnapshotCleanupMarketClosedPostRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminDataSnapshotCleanupMarketClosedPost: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **apiAdminDataSnapshotCleanupMarketClosedPostRequest** | [**ApiAdminDataSnapshotCleanupMarketClosedPostRequest**](ApiAdminDataSnapshotCleanupMarketClosedPostRequest.md)|  | [optional] 

### Return type

[**AdminSnapshotCleanupResponse**](AdminSnapshotCleanupResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminDataSnapshotCleanupMarketClosedPreviewPost**
> AdminSnapshotCleanupPreviewResponse apiAdminDataSnapshotCleanupMarketClosedPreviewPost(apiAdminDataSnapshotCleanupMarketClosedPreviewPostRequest)

预览休市日清理影响范围

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final apiAdminDataSnapshotCleanupMarketClosedPreviewPostRequest = ApiAdminDataSnapshotCleanupMarketClosedPreviewPostRequest(); // ApiAdminDataSnapshotCleanupMarketClosedPreviewPostRequest | 

try {
    final result = api_instance.apiAdminDataSnapshotCleanupMarketClosedPreviewPost(apiAdminDataSnapshotCleanupMarketClosedPreviewPostRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminDataSnapshotCleanupMarketClosedPreviewPost: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **apiAdminDataSnapshotCleanupMarketClosedPreviewPostRequest** | [**ApiAdminDataSnapshotCleanupMarketClosedPreviewPostRequest**](ApiAdminDataSnapshotCleanupMarketClosedPreviewPostRequest.md)|  | [optional] 

### Return type

[**AdminSnapshotCleanupPreviewResponse**](AdminSnapshotCleanupPreviewResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminDataSnapshotCleanupWeekendPost**
> AdminSnapshotCleanupResponse apiAdminDataSnapshotCleanupWeekendPost(apiAdminDataSnapshotCleanupWeekendPostRequest)

清理周末快照日盈亏

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final apiAdminDataSnapshotCleanupWeekendPostRequest = ApiAdminDataSnapshotCleanupWeekendPostRequest(); // ApiAdminDataSnapshotCleanupWeekendPostRequest | 

try {
    final result = api_instance.apiAdminDataSnapshotCleanupWeekendPost(apiAdminDataSnapshotCleanupWeekendPostRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminDataSnapshotCleanupWeekendPost: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **apiAdminDataSnapshotCleanupWeekendPostRequest** | [**ApiAdminDataSnapshotCleanupWeekendPostRequest**](ApiAdminDataSnapshotCleanupWeekendPostRequest.md)|  | [optional] 

### Return type

[**AdminSnapshotCleanupResponse**](AdminSnapshotCleanupResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminDataSnapshotCleanupWeekendPreviewPost**
> AdminSnapshotCleanupPreviewResponse apiAdminDataSnapshotCleanupWeekendPreviewPost(apiAdminDataSnapshotCleanupWeekendPostRequest)

预览周末清理影响范围

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final apiAdminDataSnapshotCleanupWeekendPostRequest = ApiAdminDataSnapshotCleanupWeekendPostRequest(); // ApiAdminDataSnapshotCleanupWeekendPostRequest | 

try {
    final result = api_instance.apiAdminDataSnapshotCleanupWeekendPreviewPost(apiAdminDataSnapshotCleanupWeekendPostRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminDataSnapshotCleanupWeekendPreviewPost: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **apiAdminDataSnapshotCleanupWeekendPostRequest** | [**ApiAdminDataSnapshotCleanupWeekendPostRequest**](ApiAdminDataSnapshotCleanupWeekendPostRequest.md)|  | [optional] 

### Return type

[**AdminSnapshotCleanupPreviewResponse**](AdminSnapshotCleanupPreviewResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminDataSnapshotHealthGet**
> AdminSnapshotHealthResponse apiAdminDataSnapshotHealthGet()

快照任务健康检查

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();

try {
    final result = api_instance.apiAdminDataSnapshotHealthGet();
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminDataSnapshotHealthGet: $e\n');
}
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**AdminSnapshotHealthResponse**](AdminSnapshotHealthResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminDataSnapshotTriggerPost**
> ApiSnapshotTriggerPost200Response apiAdminDataSnapshotTriggerPost()

手动触发快照

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();

try {
    final result = api_instance.apiAdminDataSnapshotTriggerPost();
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminDataSnapshotTriggerPost: $e\n');
}
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**ApiSnapshotTriggerPost200Response**](ApiSnapshotTriggerPost200Response.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminDataSnapshotsGet**
> AdminDataSnapshotsResponse apiAdminDataSnapshotsGet(userId, startDate, endDate, limit, offset)

查询快照明细

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final userId = userId_example; // String | 
final startDate = startDate_example; // String | 
final endDate = endDate_example; // String | 
final limit = 56; // int | 
final offset = 56; // int | 

try {
    final result = api_instance.apiAdminDataSnapshotsGet(userId, startDate, endDate, limit, offset);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminDataSnapshotsGet: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **userId** | **String**|  | [optional] 
 **startDate** | **String**|  | [optional] 
 **endDate** | **String**|  | [optional] 
 **limit** | **int**|  | [optional] [default to 100]
 **offset** | **int**|  | [optional] [default to 0]

### Return type

[**AdminDataSnapshotsResponse**](AdminDataSnapshotsResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminInvitesExportGet**
> String apiAdminInvitesExportGet(status, batchId)

导出邀请码 CSV

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final status = status_example; // String | 
final batchId = batchId_example; // String | 

try {
    final result = api_instance.apiAdminInvitesExportGet(status, batchId);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminInvitesExportGet: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **status** | **String**|  | [optional] 
 **batchId** | **String**|  | [optional] 

### Return type

**String**

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: text/csv, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminInvitesGeneratePost**
> AdminInvitesGenerateResponse apiAdminInvitesGeneratePost(adminInvitesGenerateRequest)

生成邀请码

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final adminInvitesGenerateRequest = AdminInvitesGenerateRequest(); // AdminInvitesGenerateRequest | 

try {
    final result = api_instance.apiAdminInvitesGeneratePost(adminInvitesGenerateRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminInvitesGeneratePost: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **adminInvitesGenerateRequest** | [**AdminInvitesGenerateRequest**](AdminInvitesGenerateRequest.md)|  | 

### Return type

[**AdminInvitesGenerateResponse**](AdminInvitesGenerateResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminInvitesGet**
> AdminInvitesListResponse apiAdminInvitesGet(status, batchId, limit, offset, random)

邀请码列表

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final status = status_example; // String | 
final batchId = batchId_example; // String | 
final limit = 56; // int | 
final offset = 56; // int | 
final random = random_example; // String | 

try {
    final result = api_instance.apiAdminInvitesGet(status, batchId, limit, offset, random);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminInvitesGet: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **status** | **String**|  | [optional] 
 **batchId** | **String**|  | [optional] 
 **limit** | **int**|  | [optional] [default to 200]
 **offset** | **int**|  | [optional] [default to 0]
 **random** | **String**|  | [optional] 

### Return type

[**AdminInvitesListResponse**](AdminInvitesListResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminInvitesRevokePost**
> AdminInvitesRevokeResponse apiAdminInvitesRevokePost(adminInvitesRevokeRequest)

作废邀请码

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final adminInvitesRevokeRequest = AdminInvitesRevokeRequest(); // AdminInvitesRevokeRequest | 

try {
    final result = api_instance.apiAdminInvitesRevokePost(adminInvitesRevokeRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminInvitesRevokePost: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **adminInvitesRevokeRequest** | [**AdminInvitesRevokeRequest**](AdminInvitesRevokeRequest.md)|  | 

### Return type

[**AdminInvitesRevokeResponse**](AdminInvitesRevokeResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminInvitesStatsGet**
> AdminInvitesStatsResponse apiAdminInvitesStatsGet(batchId)

邀请码统计

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final batchId = batchId_example; // String | 

try {
    final result = api_instance.apiAdminInvitesStatsGet(batchId);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminInvitesStatsGet: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **batchId** | **String**|  | [optional] 

### Return type

[**AdminInvitesStatsResponse**](AdminInvitesStatsResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminMetaDictionariesGet**
> AdminMetaDictionariesResponse apiAdminMetaDictionariesGet()

后台字典与标签

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();

try {
    final result = api_instance.apiAdminMetaDictionariesGet();
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminMetaDictionariesGet: $e\n');
}
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**AdminMetaDictionariesResponse**](AdminMetaDictionariesResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminOpsAppUpdateGet**
> AdminOpsAppUpdateResponse apiAdminOpsAppUpdateGet()

运营配置-更新提示

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();

try {
    final result = api_instance.apiAdminOpsAppUpdateGet();
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminOpsAppUpdateGet: $e\n');
}
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**AdminOpsAppUpdateResponse**](AdminOpsAppUpdateResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminOpsAppUpdateUpdatePost**
> AdminOpsAppUpdateUpdateResponse apiAdminOpsAppUpdateUpdatePost(apiAdminOpsAppUpdateUpdatePostRequest)

更新运营配置-更新提示

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final apiAdminOpsAppUpdateUpdatePostRequest = ApiAdminOpsAppUpdateUpdatePostRequest(); // ApiAdminOpsAppUpdateUpdatePostRequest | 

try {
    final result = api_instance.apiAdminOpsAppUpdateUpdatePost(apiAdminOpsAppUpdateUpdatePostRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminOpsAppUpdateUpdatePost: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **apiAdminOpsAppUpdateUpdatePostRequest** | [**ApiAdminOpsAppUpdateUpdatePostRequest**](ApiAdminOpsAppUpdateUpdatePostRequest.md)|  | 

### Return type

[**AdminOpsAppUpdateUpdateResponse**](AdminOpsAppUpdateUpdateResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminOpsInviteAcquireGet**
> AdminOpsTextImageResponse apiAdminOpsInviteAcquireGet()

运营配置-邀请码获取页

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();

try {
    final result = api_instance.apiAdminOpsInviteAcquireGet();
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminOpsInviteAcquireGet: $e\n');
}
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**AdminOpsTextImageResponse**](AdminOpsTextImageResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminOpsInviteAcquireUpdatePost**
> AdminOpsTextImageUpdateResponse apiAdminOpsInviteAcquireUpdatePost(apiAdminOpsInviteAcquireUpdatePostRequest)

更新运营配置-邀请码获取页

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final apiAdminOpsInviteAcquireUpdatePostRequest = ApiAdminOpsInviteAcquireUpdatePostRequest(); // ApiAdminOpsInviteAcquireUpdatePostRequest | 

try {
    final result = api_instance.apiAdminOpsInviteAcquireUpdatePost(apiAdminOpsInviteAcquireUpdatePostRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminOpsInviteAcquireUpdatePost: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **apiAdminOpsInviteAcquireUpdatePostRequest** | [**ApiAdminOpsInviteAcquireUpdatePostRequest**](ApiAdminOpsInviteAcquireUpdatePostRequest.md)|  | 

### Return type

[**AdminOpsTextImageUpdateResponse**](AdminOpsTextImageUpdateResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminOpsIosQrGet**
> AdminOpsTextImageResponse apiAdminOpsIosQrGet()

运营配置-iOS 下载二维码

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();

try {
    final result = api_instance.apiAdminOpsIosQrGet();
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminOpsIosQrGet: $e\n');
}
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**AdminOpsTextImageResponse**](AdminOpsTextImageResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminOpsIosQrUpdatePost**
> AdminOpsTextImageUpdateResponse apiAdminOpsIosQrUpdatePost(apiAdminOpsInviteAcquireUpdatePostRequest)

更新运营配置-iOS 下载二维码

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final apiAdminOpsInviteAcquireUpdatePostRequest = ApiAdminOpsInviteAcquireUpdatePostRequest(); // ApiAdminOpsInviteAcquireUpdatePostRequest | 

try {
    final result = api_instance.apiAdminOpsIosQrUpdatePost(apiAdminOpsInviteAcquireUpdatePostRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminOpsIosQrUpdatePost: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **apiAdminOpsInviteAcquireUpdatePostRequest** | [**ApiAdminOpsInviteAcquireUpdatePostRequest**](ApiAdminOpsInviteAcquireUpdatePostRequest.md)|  | 

### Return type

[**AdminOpsTextImageUpdateResponse**](AdminOpsTextImageUpdateResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminOpsUserGroupGet**
> AdminOpsTextImageResponse apiAdminOpsUserGroupGet()

运营配置-用户群页

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();

try {
    final result = api_instance.apiAdminOpsUserGroupGet();
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminOpsUserGroupGet: $e\n');
}
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**AdminOpsTextImageResponse**](AdminOpsTextImageResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminOpsUserGroupUpdatePost**
> AdminOpsTextImageUpdateResponse apiAdminOpsUserGroupUpdatePost(apiAdminOpsInviteAcquireUpdatePostRequest)

更新运营配置-用户群页

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final apiAdminOpsInviteAcquireUpdatePostRequest = ApiAdminOpsInviteAcquireUpdatePostRequest(); // ApiAdminOpsInviteAcquireUpdatePostRequest | 

try {
    final result = api_instance.apiAdminOpsUserGroupUpdatePost(apiAdminOpsInviteAcquireUpdatePostRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminOpsUserGroupUpdatePost: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **apiAdminOpsInviteAcquireUpdatePostRequest** | [**ApiAdminOpsInviteAcquireUpdatePostRequest**](ApiAdminOpsInviteAcquireUpdatePostRequest.md)|  | 

### Return type

[**AdminOpsTextImageUpdateResponse**](AdminOpsTextImageUpdateResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminOverviewGet**
> AdminOverviewResponse apiAdminOverviewGet(force)

后台概览看板

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final force = true; // bool | 

try {
    final result = api_instance.apiAdminOverviewGet(force);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminOverviewGet: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **force** | **bool**|  | [optional] 

### Return type

[**AdminOverviewResponse**](AdminOverviewResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminSummaryTodoGet**
> AdminSummaryTodoResponse apiAdminSummaryTodoGet(inviteThreshold)

后台待办与巡检摘要

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final inviteThreshold = 56; // int | 

try {
    final result = api_instance.apiAdminSummaryTodoGet(inviteThreshold);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminSummaryTodoGet: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **inviteThreshold** | **int**|  | [optional] [default to 200]

### Return type

[**AdminSummaryTodoResponse**](AdminSummaryTodoResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminUsersDisablePost**
> AdminUserStatusResponse apiAdminUsersDisablePost(apiAdminUsersDisablePostRequest)

停用用户

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final apiAdminUsersDisablePostRequest = ApiAdminUsersDisablePostRequest(); // ApiAdminUsersDisablePostRequest | 

try {
    final result = api_instance.apiAdminUsersDisablePost(apiAdminUsersDisablePostRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminUsersDisablePost: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **apiAdminUsersDisablePostRequest** | [**ApiAdminUsersDisablePostRequest**](ApiAdminUsersDisablePostRequest.md)|  | 

### Return type

[**AdminUserStatusResponse**](AdminUserStatusResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminUsersEnablePost**
> AdminUserStatusResponse apiAdminUsersEnablePost(apiAdminUsersDisablePostRequest)

启用用户

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final apiAdminUsersDisablePostRequest = ApiAdminUsersDisablePostRequest(); // ApiAdminUsersDisablePostRequest | 

try {
    final result = api_instance.apiAdminUsersEnablePost(apiAdminUsersDisablePostRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminUsersEnablePost: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **apiAdminUsersDisablePostRequest** | [**ApiAdminUsersDisablePostRequest**](ApiAdminUsersDisablePostRequest.md)|  | 

### Return type

[**AdminUserStatusResponse**](AdminUserStatusResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminUsersGet**
> AdminUsersListResponse apiAdminUsersGet(q, status, sortBy, sortDir, includeLocal, limit, offset, force)

后台用户列表

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final q = q_example; // String | 
final status = status_example; // String | 
final sortBy = sortBy_example; // String | 
final sortDir = sortDir_example; // String | 
final includeLocal = true; // bool | 
final limit = 56; // int | 
final offset = 56; // int | 
final force = true; // bool | 

try {
    final result = api_instance.apiAdminUsersGet(q, status, sortBy, sortDir, includeLocal, limit, offset, force);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminUsersGet: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **q** | **String**|  | [optional] 
 **status** | **String**|  | [optional] 
 **sortBy** | **String**|  | [optional] 
 **sortDir** | **String**|  | [optional] 
 **includeLocal** | **bool**|  | [optional] 
 **limit** | **int**|  | [optional] [default to 100]
 **offset** | **int**|  | [optional] [default to 0]
 **force** | **bool**|  | [optional] 

### Return type

[**AdminUsersListResponse**](AdminUsersListResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminUsersMetricsGet**
> AdminUserMetricsResponse apiAdminUsersMetricsGet()

用户运营指标

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();

try {
    final result = api_instance.apiAdminUsersMetricsGet();
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminUsersMetricsGet: $e\n');
}
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**AdminUserMetricsResponse**](AdminUserMetricsResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminUsersPasswordResetPost**
> AdminUserPasswordResetResponse apiAdminUsersPasswordResetPost(apiAdminUsersPasswordResetPostRequest)

重置用户密码

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final apiAdminUsersPasswordResetPostRequest = ApiAdminUsersPasswordResetPostRequest(); // ApiAdminUsersPasswordResetPostRequest | 

try {
    final result = api_instance.apiAdminUsersPasswordResetPost(apiAdminUsersPasswordResetPostRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminUsersPasswordResetPost: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **apiAdminUsersPasswordResetPostRequest** | [**ApiAdminUsersPasswordResetPostRequest**](ApiAdminUsersPasswordResetPostRequest.md)|  | 

### Return type

[**AdminUserPasswordResetResponse**](AdminUserPasswordResetResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminUsersSessionsCountGet**
> AdminUserSessionsCountResponse apiAdminUsersSessionsCountGet(userId)

用户在线会话数

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final userId = userId_example; // String | 

try {
    final result = api_instance.apiAdminUsersSessionsCountGet(userId);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminUsersSessionsCountGet: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **userId** | **String**|  | 

### Return type

[**AdminUserSessionsCountResponse**](AdminUserSessionsCountResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminUsersSessionsRevokePost**
> AdminUserSessionsRevokeResponse apiAdminUsersSessionsRevokePost(apiAdminUsersDisablePostRequest)

强制用户下线

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final apiAdminUsersDisablePostRequest = ApiAdminUsersDisablePostRequest(); // ApiAdminUsersDisablePostRequest | 

try {
    final result = api_instance.apiAdminUsersSessionsRevokePost(apiAdminUsersDisablePostRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminUsersSessionsRevokePost: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **apiAdminUsersDisablePostRequest** | [**ApiAdminUsersDisablePostRequest**](ApiAdminUsersDisablePostRequest.md)|  | 

### Return type

[**AdminUserSessionsRevokeResponse**](AdminUserSessionsRevokeResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminUsersStatusPost**
> AdminUserStatusResponse apiAdminUsersStatusPost(apiAdminUsersStatusPostRequest)

设置用户状态

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final apiAdminUsersStatusPostRequest = ApiAdminUsersStatusPostRequest(); // ApiAdminUsersStatusPostRequest | 

try {
    final result = api_instance.apiAdminUsersStatusPost(apiAdminUsersStatusPostRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminUsersStatusPost: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **apiAdminUsersStatusPostRequest** | [**ApiAdminUsersStatusPostRequest**](ApiAdminUsersStatusPostRequest.md)|  | 

### Return type

[**AdminUserStatusResponse**](AdminUserStatusResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminUsersUpdatePost**
> AdminUserUpdateResponse apiAdminUsersUpdatePost(apiAdminUsersUpdatePostRequest)

更新用户信息

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final apiAdminUsersUpdatePostRequest = ApiAdminUsersUpdatePostRequest(); // ApiAdminUsersUpdatePostRequest | 

try {
    final result = api_instance.apiAdminUsersUpdatePost(apiAdminUsersUpdatePostRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminUsersUpdatePost: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **apiAdminUsersUpdatePostRequest** | [**ApiAdminUsersUpdatePostRequest**](ApiAdminUsersUpdatePostRequest.md)|  | 

### Return type

[**AdminUserUpdateResponse**](AdminUserUpdateResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminUsersUserIdGet**
> AdminUserDetail apiAdminUsersUserIdGet(userId)

用户详情

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final userId = userId_example; // String | 

try {
    final result = api_instance.apiAdminUsersUserIdGet(userId);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminUsersUserIdGet: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **userId** | **String**|  | 

### Return type

[**AdminUserDetail**](AdminUserDetail.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiAdminUsersUserIdPortfolioGet**
> AdminUserPortfolioResponse apiAdminUsersUserIdPortfolioGet(userId, force)

用户持仓与资产概览

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final userId = userId_example; // String | 
final force = true; // bool | 

try {
    final result = api_instance.apiAdminUsersUserIdPortfolioGet(userId, force);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiAdminUsersUserIdPortfolioGet: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **userId** | **String**|  | 
 **force** | **bool**|  | [optional] 

### Return type

[**AdminUserPortfolioResponse**](AdminUserPortfolioResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiSnapshotFixPost**
> ApiSnapshotTriggerPost200Response apiSnapshotFixPost(snapshotFixRequest)

Fix snapshot day_pnl

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final snapshotFixRequest = SnapshotFixRequest(); // SnapshotFixRequest | 

try {
    final result = api_instance.apiSnapshotFixPost(snapshotFixRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiSnapshotFixPost: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **snapshotFixRequest** | [**SnapshotFixRequest**](SnapshotFixRequest.md)|  | 

### Return type

[**ApiSnapshotTriggerPost200Response**](ApiSnapshotTriggerPost200Response.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiSnapshotSavePost**
> StatusOk apiSnapshotSavePost(snapshotSaveRequest)

Save daily snapshot

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final snapshotSaveRequest = SnapshotSaveRequest(); // SnapshotSaveRequest | 

try {
    final result = api_instance.apiSnapshotSavePost(snapshotSaveRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiSnapshotSavePost: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **snapshotSaveRequest** | [**SnapshotSaveRequest**](SnapshotSaveRequest.md)|  | 

### Return type

[**StatusOk**](StatusOk.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **apiSnapshotTriggerPost**
> ApiSnapshotTriggerPost200Response apiSnapshotTriggerPost()

Trigger snapshot

### Example
```dart
import 'package:kaka_openapi/api.dart';

final api_instance = DefaultApi();

try {
    final result = api_instance.apiSnapshotTriggerPost();
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->apiSnapshotTriggerPost: $e\n');
}
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**ApiSnapshotTriggerPost200Response**](ApiSnapshotTriggerPost200Response.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **bootstrapCredentials**
> bootstrapCredentials(bootstrapCredentialsRequest)

Bootstrap username/password for legacy users

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final bootstrapCredentialsRequest = BootstrapCredentialsRequest(); // BootstrapCredentialsRequest | 

try {
    api_instance.bootstrapCredentials(bootstrapCredentialsRequest);
} catch (e) {
    print('Exception when calling DefaultApi->bootstrapCredentials: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **bootstrapCredentialsRequest** | [**BootstrapCredentialsRequest**](BootstrapCredentialsRequest.md)|  | 

### Return type

void (empty response body)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **bootstrapSync**
> SyncBootstrapResponse bootstrapSync(syncBootstrapRequest)

客户端增量同步引导

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final syncBootstrapRequest = SyncBootstrapRequest(); // SyncBootstrapRequest | 

try {
    final result = api_instance.bootstrapSync(syncBootstrapRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->bootstrapSync: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **syncBootstrapRequest** | [**SyncBootstrapRequest**](SyncBootstrapRequest.md)|  | [optional] 

### Return type

[**SyncBootstrapResponse**](SyncBootstrapResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **buyPortfolioAsset**
> StatusOk buyPortfolioAsset(buyPortfolioAssetRequest)

Buy asset

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final buyPortfolioAssetRequest = BuyPortfolioAssetRequest(); // BuyPortfolioAssetRequest | 

try {
    final result = api_instance.buyPortfolioAsset(buyPortfolioAssetRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->buyPortfolioAsset: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **buyPortfolioAssetRequest** | [**BuyPortfolioAssetRequest**](BuyPortfolioAssetRequest.md)|  | 

### Return type

[**StatusOk**](StatusOk.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **buyPortfolioAssetWithCash**
> PortfolioBuyWithCashResponse buyPortfolioAssetWithCash(portfolioBuyWithCashRequest)

现金账户买入资产

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final portfolioBuyWithCashRequest = PortfolioBuyWithCashRequest(); // PortfolioBuyWithCashRequest | 

try {
    final result = api_instance.buyPortfolioAssetWithCash(portfolioBuyWithCashRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->buyPortfolioAssetWithCash: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **portfolioBuyWithCashRequest** | [**PortfolioBuyWithCashRequest**](PortfolioBuyWithCashRequest.md)|  | 

### Return type

[**PortfolioBuyWithCashResponse**](PortfolioBuyWithCashResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **changePassword**
> changePassword(changePasswordRequest)

Change password

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final changePasswordRequest = ChangePasswordRequest(); // ChangePasswordRequest | 

try {
    api_instance.changePassword(changePasswordRequest);
} catch (e) {
    print('Exception when calling DefaultApi->changePassword: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **changePasswordRequest** | [**ChangePasswordRequest**](ChangePasswordRequest.md)|  | 

### Return type

void (empty response body)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **checkSettingsApi**
> Object checkSettingsApi()

Check API status

### Example
```dart
import 'package:kaka_openapi/api.dart';

final api_instance = DefaultApi();

try {
    final result = api_instance.checkSettingsApi();
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->checkSettingsApi: $e\n');
}
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**Object**](Object.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **deleteCashAsset**
> StatusOk deleteCashAsset(deleteCashAssetRequest)

Delete cash asset

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final deleteCashAssetRequest = DeleteCashAssetRequest(); // DeleteCashAssetRequest | 

try {
    final result = api_instance.deleteCashAsset(deleteCashAssetRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->deleteCashAsset: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **deleteCashAssetRequest** | [**DeleteCashAssetRequest**](DeleteCashAssetRequest.md)|  | 

### Return type

[**StatusOk**](StatusOk.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **deleteLiability**
> StatusOk deleteLiability(deleteCashAssetRequest)

Delete liability

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final deleteCashAssetRequest = DeleteCashAssetRequest(); // DeleteCashAssetRequest | 

try {
    final result = api_instance.deleteLiability(deleteCashAssetRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->deleteLiability: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **deleteCashAssetRequest** | [**DeleteCashAssetRequest**](DeleteCashAssetRequest.md)|  | 

### Return type

[**StatusOk**](StatusOk.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **deleteOtherAsset**
> StatusOk deleteOtherAsset(deleteCashAssetRequest)

Delete other asset

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final deleteCashAssetRequest = DeleteCashAssetRequest(); // DeleteCashAssetRequest | 

try {
    final result = api_instance.deleteOtherAsset(deleteCashAssetRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->deleteOtherAsset: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **deleteCashAssetRequest** | [**DeleteCashAssetRequest**](DeleteCashAssetRequest.md)|  | 

### Return type

[**StatusOk**](StatusOk.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **deletePortfolioAsset**
> StatusOk deletePortfolioAsset(deletePortfolioAssetRequest)

Delete asset

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final deletePortfolioAssetRequest = DeletePortfolioAssetRequest(); // DeletePortfolioAssetRequest | 

try {
    final result = api_instance.deletePortfolioAsset(deletePortfolioAssetRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->deletePortfolioAsset: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **deletePortfolioAssetRequest** | [**DeletePortfolioAssetRequest**](DeletePortfolioAssetRequest.md)|  | 

### Return type

[**StatusOk**](StatusOk.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **deletePortfolioAssetCorrective**
> PortfolioDeleteCorrectiveResponse deletePortfolioAssetCorrective(portfolioDeleteCorrectiveRequest)

纠正性删除资产及历史记录

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final portfolioDeleteCorrectiveRequest = PortfolioDeleteCorrectiveRequest(); // PortfolioDeleteCorrectiveRequest | 

try {
    final result = api_instance.deletePortfolioAssetCorrective(portfolioDeleteCorrectiveRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->deletePortfolioAssetCorrective: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **portfolioDeleteCorrectiveRequest** | [**PortfolioDeleteCorrectiveRequest**](PortfolioDeleteCorrectiveRequest.md)|  | 

### Return type

[**PortfolioDeleteCorrectiveResponse**](PortfolioDeleteCorrectiveResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **downloadSettingsBackup**
> downloadSettingsBackup()

Download DB backup

### Example
```dart
import 'package:kaka_openapi/api.dart';

final api_instance = DefaultApi();

try {
    api_instance.downloadSettingsBackup();
} catch (e) {
    print('Exception when calling DefaultApi->downloadSettingsBackup: $e\n');
}
```

### Parameters
This endpoint does not need any parameter.

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getAnalysisCalendar**
> AnalysisCalendarResponse getAnalysisCalendar(type, year, month)

PnL calendar

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final type = type_example; // String | 
final year = 56; // int | day/month 视图可选，指定年份
final month = 56; // int | day 视图可选，指定月份

try {
    final result = api_instance.getAnalysisCalendar(type, year, month);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->getAnalysisCalendar: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **type** | **String**|  | [optional] 
 **year** | **int**| day/month 视图可选，指定年份 | [optional] 
 **month** | **int**| day 视图可选，指定月份 | [optional] 

### Return type

[**AnalysisCalendarResponse**](AnalysisCalendarResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getAnalysisMarketBreakdown**
> AnalysisMarketBreakdownResponse getAnalysisMarketBreakdown(type, timeType, year, month)

收益日历按市场拆分

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final type = type_example; // String | 
final timeType = timeType_example; // String | 
final year = 56; // int | 
final month = 56; // int | 

try {
    final result = api_instance.getAnalysisMarketBreakdown(type, timeType, year, month);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->getAnalysisMarketBreakdown: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **type** | **String**|  | [optional] 
 **timeType** | **String**|  | [optional] 
 **year** | **int**|  | [optional] 
 **month** | **int**|  | [optional] 

### Return type

[**AnalysisMarketBreakdownResponse**](AnalysisMarketBreakdownResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getAnalysisOverview**
> AnalysisOverviewResponse getAnalysisOverview(period)

PnL overview

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final period = period_example; // String | 

try {
    final result = api_instance.getAnalysisOverview(period);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->getAnalysisOverview: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **period** | **String**|  | [optional] 

### Return type

[**AnalysisOverviewResponse**](AnalysisOverviewResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getAnalysisRank**
> AnalysisRankResponse getAnalysisRank(type, market)

PnL rank

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final type = type_example; // String | 
final market = market_example; // String | 

try {
    final result = api_instance.getAnalysisRank(type, market);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->getAnalysisRank: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **type** | **String**|  | [optional] 
 **market** | **String**|  | [optional] 

### Return type

[**AnalysisRankResponse**](AnalysisRankResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getAppVersion**
> AppVersionResponse getAppVersion()

获取客户端更新配置

### Example
```dart
import 'package:kaka_openapi/api.dart';

final api_instance = DefaultApi();

try {
    final result = api_instance.getAppVersion();
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->getAppVersion: $e\n');
}
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**AppVersionResponse**](AppVersionResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getAssetTrends**
> AssetTrendsResponse getAssetTrends(assetTrendsRequest)

批量资产趋势线

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final assetTrendsRequest = AssetTrendsRequest(); // AssetTrendsRequest | 

try {
    final result = api_instance.getAssetTrends(assetTrendsRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->getAssetTrends: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **assetTrendsRequest** | [**AssetTrendsRequest**](AssetTrendsRequest.md)|  | 

### Return type

[**AssetTrendsResponse**](AssetTrendsResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getBatchPrices**
> Map<String, GetPrice200Response> getBatchPrices(getBatchPricesRequest)

Get batch prices

### Example
```dart
import 'package:kaka_openapi/api.dart';

final api_instance = DefaultApi();
final getBatchPricesRequest = GetBatchPricesRequest(); // GetBatchPricesRequest | 

try {
    final result = api_instance.getBatchPrices(getBatchPricesRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->getBatchPrices: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **getBatchPricesRequest** | [**GetBatchPricesRequest**](GetBatchPricesRequest.md)|  | 

### Return type

[**Map<String, GetPrice200Response>**](GetPrice200Response.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getCashAssets**
> getCashAssets()

Get cash assets

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();

try {
    api_instance.getCashAssets();
} catch (e) {
    print('Exception when calling DefaultApi->getCashAssets: $e\n');
}
```

### Parameters
This endpoint does not need any parameter.

### Return type

void (empty response body)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getCurrentUser**
> getCurrentUser()

Current user

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();

try {
    api_instance.getCurrentUser();
} catch (e) {
    print('Exception when calling DefaultApi->getCurrentUser: $e\n');
}
```

### Parameters
This endpoint does not need any parameter.

### Return type

void (empty response body)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getHealth**
> GetHealth200Response getHealth()

Health check

### Example
```dart
import 'package:kaka_openapi/api.dart';

final api_instance = DefaultApi();

try {
    final result = api_instance.getHealth();
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->getHealth: $e\n');
}
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**GetHealth200Response**](GetHealth200Response.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getHistory**
> List<Object> getHistory(days)

Get history

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final days = 56; // int | 

try {
    final result = api_instance.getHistory(days);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->getHistory: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **days** | **int**|  | [optional] [default to 365]

### Return type

[**List<Object>**](Object.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getLatestNews**
> List<Object> getLatestNews()

Latest news

### Example
```dart
import 'package:kaka_openapi/api.dart';

final api_instance = DefaultApi();

try {
    final result = api_instance.getLatestNews();
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->getLatestNews: $e\n');
}
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**List<Object>**](Object.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getLiabilities**
> getLiabilities()

Get liabilities

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();

try {
    api_instance.getLiabilities();
} catch (e) {
    print('Exception when calling DefaultApi->getLiabilities: $e\n');
}
```

### Parameters
This endpoint does not need any parameter.

### Return type

void (empty response body)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getMarketIndices**
> List<MarketIndexItem> getMarketIndices()

首页指数与汇率

### Example
```dart
import 'package:kaka_openapi/api.dart';

final api_instance = DefaultApi();

try {
    final result = api_instance.getMarketIndices();
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->getMarketIndices: $e\n');
}
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**List<MarketIndexItem>**](MarketIndexItem.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getMarketStatus**
> MarketStatusResponse getMarketStatus()

市场开休市状态

### Example
```dart
import 'package:kaka_openapi/api.dart';

final api_instance = DefaultApi();

try {
    final result = api_instance.getMarketStatus();
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->getMarketStatus: $e\n');
}
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**MarketStatusResponse**](MarketStatusResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getOtherAssets**
> getOtherAssets()

Get other assets

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();

try {
    api_instance.getOtherAssets();
} catch (e) {
    print('Exception when calling DefaultApi->getOtherAssets: $e\n');
}
```

### Parameters
This endpoint does not need any parameter.

### Return type

void (empty response body)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getPortfolio**
> List<PortfolioItem> getPortfolio(type, withMetrics)

Get portfolio

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final type = type_example; // String | 
final withMetrics = true; // bool | 

try {
    final result = api_instance.getPortfolio(type, withMetrics);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->getPortfolio: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **type** | **String**|  | [optional] 
 **withMetrics** | **bool**|  | [optional] 

### Return type

[**List<PortfolioItem>**](PortfolioItem.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getPortfolioTransactions**
> PortfolioTransactionsResponse getPortfolioTransactions(code)

Get portfolio transaction and correction records

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final code = code_example; // String | 

try {
    final result = api_instance.getPortfolioTransactions(code);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->getPortfolioTransactions: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **code** | **String**|  | 

### Return type

[**PortfolioTransactionsResponse**](PortfolioTransactionsResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getPrice**
> GetPrice200Response getPrice(code)

Get a single price

### Example
```dart
import 'package:kaka_openapi/api.dart';

final api_instance = DefaultApi();
final code = code_example; // String | 

try {
    final result = api_instance.getPrice(code);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->getPrice: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **code** | **String**|  | 

### Return type

[**GetPrice200Response**](GetPrice200Response.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getRates**
> Map<String, num> getRates()

Get FX rates

### Example
```dart
import 'package:kaka_openapi/api.dart';

final api_instance = DefaultApi();

try {
    final result = api_instance.getRates();
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->getRates: $e\n');
}
```

### Parameters
This endpoint does not need any parameter.

### Return type

**Map<String, num>**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getSettingsInfo**
> Object getSettingsInfo()

System info

### Example
```dart
import 'package:kaka_openapi/api.dart';

final api_instance = DefaultApi();

try {
    final result = api_instance.getSettingsInfo();
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->getSettingsInfo: $e\n');
}
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**Object**](Object.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getSystemPriceHealth**
> PriceHealthResponse getSystemPriceHealth()

行情运行健康指标

### Example
```dart
import 'package:kaka_openapi/api.dart';

final api_instance = DefaultApi();

try {
    final result = api_instance.getSystemPriceHealth();
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->getSystemPriceHealth: $e\n');
}
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**PriceHealthResponse**](PriceHealthResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getTransactions**
> List<Object> getTransactions(limit)

Get transactions

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final limit = 56; // int | 

try {
    final result = api_instance.getTransactions(limit);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->getTransactions: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **limit** | **int**|  | [optional] [default to 100]

### Return type

[**List<Object>**](Object.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getWebConfig**
> WebConfigResponse getWebConfig()

Web 门户公开配置

### Example
```dart
import 'package:kaka_openapi/api.dart';

final api_instance = DefaultApi();

try {
    final result = api_instance.getWebConfig();
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->getWebConfig: $e\n');
}
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**WebConfigResponse**](WebConfigResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **login**
> login(loginRequest)

Login

### Example
```dart
import 'package:kaka_openapi/api.dart';

final api_instance = DefaultApi();
final loginRequest = LoginRequest(); // LoginRequest | 

try {
    api_instance.login(loginRequest);
} catch (e) {
    print('Exception when calling DefaultApi->login: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **loginRequest** | [**LoginRequest**](LoginRequest.md)|  | 

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **logout**
> logout(logoutRequest)

Logout

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final logoutRequest = LogoutRequest(); // LogoutRequest | 

try {
    api_instance.logout(logoutRequest);
} catch (e) {
    print('Exception when calling DefaultApi->logout: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **logoutRequest** | [**LogoutRequest**](LogoutRequest.md)|  | [optional] 

### Return type

void (empty response body)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **modifyPortfolioAsset**
> StatusOk modifyPortfolioAsset(modifyPortfolioAssetRequest)

Modify asset qty/price

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final modifyPortfolioAssetRequest = ModifyPortfolioAssetRequest(); // ModifyPortfolioAssetRequest | 

try {
    final result = api_instance.modifyPortfolioAsset(modifyPortfolioAssetRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->modifyPortfolioAsset: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **modifyPortfolioAssetRequest** | [**ModifyPortfolioAssetRequest**](ModifyPortfolioAssetRequest.md)|  | 

### Return type

[**StatusOk**](StatusOk.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **refreshSession**
> refreshSession(refreshSessionRequest)

Refresh access token

### Example
```dart
import 'package:kaka_openapi/api.dart';

final api_instance = DefaultApi();
final refreshSessionRequest = RefreshSessionRequest(); // RefreshSessionRequest | 

try {
    api_instance.refreshSession(refreshSessionRequest);
} catch (e) {
    print('Exception when calling DefaultApi->refreshSession: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **refreshSessionRequest** | [**RefreshSessionRequest**](RefreshSessionRequest.md)|  | 

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **register**
> register(registerRequest)

Register with invite code

### Example
```dart
import 'package:kaka_openapi/api.dart';

final api_instance = DefaultApi();
final registerRequest = RegisterRequest(); // RegisterRequest | 

try {
    api_instance.register(registerRequest);
} catch (e) {
    print('Exception when calling DefaultApi->register: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **registerRequest** | [**RegisterRequest**](RegisterRequest.md)|  | 

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **restoreSettingsBackup**
> StatusOk restoreSettingsBackup(file)

Restore DB

### Example
```dart
import 'package:kaka_openapi/api.dart';

final api_instance = DefaultApi();
final file = BINARY_DATA_HERE; // MultipartFile | 

try {
    final result = api_instance.restoreSettingsBackup(file);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->restoreSettingsBackup: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **file** | **MultipartFile**|  | [optional] 

### Return type

[**StatusOk**](StatusOk.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: multipart/form-data
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **searchSecurities**
> List<Object> searchSecurities(q)

Search securities

### Example
```dart
import 'package:kaka_openapi/api.dart';

final api_instance = DefaultApi();
final q = q_example; // String | 

try {
    final result = api_instance.searchSecurities(q);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->searchSecurities: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **q** | **String**|  | 

### Return type

[**List<Object>**](Object.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **sellPortfolioAsset**
> StatusOk sellPortfolioAsset(buyPortfolioAssetRequest)

Sell asset

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final buyPortfolioAssetRequest = BuyPortfolioAssetRequest(); // BuyPortfolioAssetRequest | 

try {
    final result = api_instance.sellPortfolioAsset(buyPortfolioAssetRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->sellPortfolioAsset: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **buyPortfolioAssetRequest** | [**BuyPortfolioAssetRequest**](BuyPortfolioAssetRequest.md)|  | 

### Return type

[**StatusOk**](StatusOk.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **sendAuthCode**
> sendAuthCode()

Deprecated endpoint, returns 410

### Example
```dart
import 'package:kaka_openapi/api.dart';

final api_instance = DefaultApi();

try {
    api_instance.sendAuthCode();
} catch (e) {
    print('Exception when calling DefaultApi->sendAuthCode: $e\n');
}
```

### Parameters
This endpoint does not need any parameter.

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **undoPortfolioOperation**
> PortfolioUndoResponse undoPortfolioOperation(portfolioUndoRequest)

撤销最近一次投资操作

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final portfolioUndoRequest = PortfolioUndoRequest(); // PortfolioUndoRequest | 

try {
    final result = api_instance.undoPortfolioOperation(portfolioUndoRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->undoPortfolioOperation: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **portfolioUndoRequest** | [**PortfolioUndoRequest**](PortfolioUndoRequest.md)|  | 

### Return type

[**PortfolioUndoResponse**](PortfolioUndoResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **updateCashAsset**
> StatusOk updateCashAsset(updateCashAssetRequest)

Update cash asset

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final updateCashAssetRequest = UpdateCashAssetRequest(); // UpdateCashAssetRequest | 

try {
    final result = api_instance.updateCashAsset(updateCashAssetRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->updateCashAsset: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **updateCashAssetRequest** | [**UpdateCashAssetRequest**](UpdateCashAssetRequest.md)|  | 

### Return type

[**StatusOk**](StatusOk.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **updateLiability**
> StatusOk updateLiability(updateCashAssetRequest)

Update liability

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final updateCashAssetRequest = UpdateCashAssetRequest(); // UpdateCashAssetRequest | 

try {
    final result = api_instance.updateLiability(updateCashAssetRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->updateLiability: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **updateCashAssetRequest** | [**UpdateCashAssetRequest**](UpdateCashAssetRequest.md)|  | 

### Return type

[**StatusOk**](StatusOk.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **updateOtherAsset**
> StatusOk updateOtherAsset(updateCashAssetRequest)

Update other asset

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final updateCashAssetRequest = UpdateCashAssetRequest(); // UpdateCashAssetRequest | 

try {
    final result = api_instance.updateOtherAsset(updateCashAssetRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->updateOtherAsset: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **updateCashAssetRequest** | [**UpdateCashAssetRequest**](UpdateCashAssetRequest.md)|  | 

### Return type

[**StatusOk**](StatusOk.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **updatePortfolioAssetField**
> StatusOk updatePortfolioAssetField(updatePortfolioAssetFieldRequest)

Update asset field

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final updatePortfolioAssetFieldRequest = UpdatePortfolioAssetFieldRequest(); // UpdatePortfolioAssetFieldRequest | 

try {
    final result = api_instance.updatePortfolioAssetField(updatePortfolioAssetFieldRequest);
    print(result);
} catch (e) {
    print('Exception when calling DefaultApi->updatePortfolioAssetField: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **updatePortfolioAssetFieldRequest** | [**UpdatePortfolioAssetFieldRequest**](UpdatePortfolioAssetFieldRequest.md)|  | 

### Return type

[**StatusOk**](StatusOk.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **updateProfile**
> updateProfile(updateProfileRequest)

Update user profile

### Example
```dart
import 'package:kaka_openapi/api.dart';
// TODO Configure HTTP Bearer authorization: bearerAuth
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('bearerAuth').setAccessToken(yourTokenGeneratorFunction);

final api_instance = DefaultApi();
final updateProfileRequest = UpdateProfileRequest(); // UpdateProfileRequest | 

try {
    api_instance.updateProfile(updateProfileRequest);
} catch (e) {
    print('Exception when calling DefaultApi->updateProfile: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **updateProfileRequest** | [**UpdateProfileRequest**](UpdateProfileRequest.md)|  | 

### Return type

void (empty response body)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **validateInviteCode**
> validateInviteCode(validateInviteCodeRequest)

Validate invite code

### Example
```dart
import 'package:kaka_openapi/api.dart';

final api_instance = DefaultApi();
final validateInviteCodeRequest = ValidateInviteCodeRequest(); // ValidateInviteCodeRequest | 

try {
    api_instance.validateInviteCode(validateInviteCodeRequest);
} catch (e) {
    print('Exception when calling DefaultApi->validateInviteCode: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **validateInviteCodeRequest** | [**ValidateInviteCodeRequest**](ValidateInviteCodeRequest.md)|  | 

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

