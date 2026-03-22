//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

library openapi.api;

import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:collection/collection.dart';
import 'package:http/http.dart';
import 'package:intl/intl.dart';
import 'package:meta/meta.dart';

part 'api_client.dart';
part 'api_helper.dart';
part 'api_exception.dart';
part 'auth/authentication.dart';
part 'auth/api_key_auth.dart';
part 'auth/oauth.dart';
part 'auth/http_basic_auth.dart';
part 'auth/http_bearer_auth.dart';

part 'api/default_api.dart';

part 'model/add_cash_asset_request.dart';
part 'model/add_portfolio_adjustment_event_request.dart';
part 'model/add_portfolio_asset_request.dart';
part 'model/admin_api_health_response.dart';
part 'model/admin_api_health_response_db.dart';
part 'model/admin_api_health_response_version_info.dart';
part 'model/admin_audit_item.dart';
part 'model/admin_backup_latest_response.dart';
part 'model/admin_backup_request.dart';
part 'model/admin_backup_response.dart';
part 'model/admin_config_item.dart';
part 'model/admin_config_list_response.dart';
part 'model/admin_config_update_request.dart';
part 'model/admin_config_update_request_items_inner.dart';
part 'model/admin_config_update_response.dart';
part 'model/admin_config_update_response_updated_inner.dart';
part 'model/admin_data_snapshots_response.dart';
part 'model/admin_invite_item.dart';
part 'model/admin_invites_generate_request.dart';
part 'model/admin_invites_generate_response.dart';
part 'model/admin_invites_list_response.dart';
part 'model/admin_invites_revoke_request.dart';
part 'model/admin_invites_revoke_response.dart';
part 'model/admin_invites_stats_response.dart';
part 'model/admin_meta_dictionaries_response.dart';
part 'model/admin_mini_bar.dart';
part 'model/admin_ops_app_update_response.dart';
part 'model/admin_ops_app_update_update_response.dart';
part 'model/admin_ops_text_image_response.dart';
part 'model/admin_ops_text_image_update_response.dart';
part 'model/admin_overview_response.dart';
part 'model/admin_overview_response_dashboard.dart';
part 'model/admin_overview_response_snapshots.dart';
part 'model/admin_overview_response_users.dart';
part 'model/admin_policies_response.dart';
part 'model/admin_policy_batch_update_request.dart';
part 'model/admin_policy_batch_update_response.dart';
part 'model/admin_policy_item.dart';
part 'model/admin_policy_update_request.dart';
part 'model/admin_policy_update_response.dart';
part 'model/admin_price_alert_item.dart';
part 'model/admin_price_alert_report_summary.dart';
part 'model/admin_price_alert_source_item.dart';
part 'model/admin_price_alert_summary.dart';
part 'model/admin_price_alerts_response.dart';
part 'model/admin_price_alerts_response_cache.dart';
part 'model/admin_price_probe_current.dart';
part 'model/admin_price_probe_diagnosis.dart';
part 'model/admin_price_probe_request.dart';
part 'model/admin_price_probe_response.dart';
part 'model/admin_provider_test_item.dart';
part 'model/admin_provider_test_report.dart';
part 'model/admin_provider_test_report_run.dart';
part 'model/admin_provider_test_response.dart';
part 'model/admin_provider_test_summary.dart';
part 'model/admin_rebind_execute_response.dart';
part 'model/admin_rebind_execute_response_result.dart';
part 'model/admin_rebind_preview_response.dart';
part 'model/admin_restore_request.dart';
part 'model/admin_restore_response.dart';
part 'model/admin_retention_row.dart';
part 'model/admin_smoke_test_item.dart';
part 'model/admin_smoke_test_response.dart';
part 'model/admin_snapshot_cleanup_preview_response.dart';
part 'model/admin_snapshot_cleanup_response.dart';
part 'model/admin_snapshot_health_response.dart';
part 'model/admin_snapshot_health_user.dart';
part 'model/admin_snapshot_row.dart';
part 'model/admin_summary_todo_response.dart';
part 'model/admin_summary_todo_response_snapshot.dart';
part 'model/admin_todo_item.dart';
part 'model/admin_upstream_status_item.dart';
part 'model/admin_user_detail.dart';
part 'model/admin_user_metrics_response.dart';
part 'model/admin_user_ops_metrics.dart';
part 'model/admin_user_ops_metrics_last_login_distribution.dart';
part 'model/admin_user_password_reset_response.dart';
part 'model/admin_user_portfolio_item.dart';
part 'model/admin_user_portfolio_response.dart';
part 'model/admin_user_portfolio_response_cache.dart';
part 'model/admin_user_portfolio_response_summary.dart';
part 'model/admin_user_sessions_count_response.dart';
part 'model/admin_user_sessions_revoke_response.dart';
part 'model/admin_user_status_response.dart';
part 'model/admin_user_summary.dart';
part 'model/admin_user_update_response.dart';
part 'model/admin_user_update_response_user.dart';
part 'model/admin_users_list_response.dart';
part 'model/analysis_calendar_error_response.dart';
part 'model/analysis_calendar_item.dart';
part 'model/analysis_calendar_period.dart';
part 'model/analysis_calendar_response.dart';
part 'model/analysis_calendar_selectable.dart';
part 'model/analysis_calendar_selectable_day.dart';
part 'model/analysis_calendar_selectable_month.dart';
part 'model/analysis_market_breakdown_item.dart';
part 'model/analysis_market_breakdown_item_markets.dart';
part 'model/analysis_market_breakdown_response.dart';
part 'model/analysis_overview_response.dart';
part 'model/analysis_rank_item.dart';
part 'model/analysis_rank_response.dart';
part 'model/api_admin_apis_provider_test_post_request.dart';
part 'model/api_admin_config_reset_post_request.dart';
part 'model/api_admin_data_rebind_execute_post_request.dart';
part 'model/api_admin_data_snapshot_cleanup_market_closed_post_request.dart';
part 'model/api_admin_data_snapshot_cleanup_market_closed_preview_post_request.dart';
part 'model/api_admin_data_snapshot_cleanup_weekend_post_request.dart';
part 'model/api_admin_ops_app_update_update_post_request.dart';
part 'model/api_admin_ops_invite_acquire_update_post_request.dart';
part 'model/api_admin_users_disable_post_request.dart';
part 'model/api_admin_users_password_reset_post_request.dart';
part 'model/api_admin_users_status_post_request.dart';
part 'model/api_admin_users_update_post_request.dart';
part 'model/api_snapshot_trigger_post200_response.dart';
part 'model/app_version_response.dart';
part 'model/asset_trend_item.dart';
part 'model/asset_trend_point.dart';
part 'model/asset_trends_request.dart';
part 'model/asset_trends_request_item.dart';
part 'model/asset_trends_response.dart';
part 'model/bootstrap_credentials_request.dart';
part 'model/buy_portfolio_asset_request.dart';
part 'model/change_password_request.dart';
part 'model/delete_cash_asset_request.dart';
part 'model/delete_portfolio_asset_request.dart';
part 'model/error.dart';
part 'model/get_batch_prices_request.dart';
part 'model/get_health200_response.dart';
part 'model/get_price200_response.dart';
part 'model/login_request.dart';
part 'model/logout_request.dart';
part 'model/market_index_item.dart';
part 'model/market_status_item.dart';
part 'model/market_status_response.dart';
part 'model/modify_portfolio_asset_request.dart';
part 'model/pnl_overview_item.dart';
part 'model/portfolio_buy_with_cash_request.dart';
part 'model/portfolio_buy_with_cash_response.dart';
part 'model/portfolio_delete_corrective_request.dart';
part 'model/portfolio_delete_corrective_response.dart';
part 'model/portfolio_delete_corrective_response_deleted.dart';
part 'model/portfolio_item.dart';
part 'model/portfolio_transaction_record.dart';
part 'model/portfolio_transactions_response.dart';
part 'model/portfolio_undo_request.dart';
part 'model/portfolio_undo_response.dart';
part 'model/price_cache_stats.dart';
part 'model/price_health_response.dart';
part 'model/price_runtime_metrics.dart';
part 'model/price_source_health_item.dart';
part 'model/refresh_session_request.dart';
part 'model/register_request.dart';
part 'model/request_runtime_metrics.dart';
part 'model/request_runtime_metrics_storage.dart';
part 'model/snapshot_fix_request.dart';
part 'model/snapshot_save_request.dart';
part 'model/status_ok.dart';
part 'model/sync_bootstrap_request.dart';
part 'model/sync_bootstrap_response.dart';
part 'model/sync_bootstrap_response_quote_policy.dart';
part 'model/sync_bootstrap_response_versions.dart';
part 'model/update_cash_asset_request.dart';
part 'model/update_portfolio_asset_field_request.dart';
part 'model/update_profile_request.dart';
part 'model/validate_invite_code_request.dart';
part 'model/web_config_response.dart';


/// An [ApiClient] instance that uses the default values obtained from
/// the OpenAPI specification file.
var defaultApiClient = ApiClient();

const _delimiters = {'csv': ',', 'ssv': ' ', 'tsv': '\t', 'pipes': '|'};
const _dateEpochMarker = 'epoch';
const _deepEquality = DeepCollectionEquality();
final _dateFormatter = DateFormat('yyyy-MM-dd');
final _regList = RegExp(r'^List<(.*)>$');
final _regSet = RegExp(r'^Set<(.*)>$');
final _regMap = RegExp(r'^Map<String,(.*)>$');

bool _isEpochMarker(String? pattern) => pattern == _dateEpochMarker || pattern == '/$_dateEpochMarker/';
