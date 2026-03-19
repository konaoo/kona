"""
管理后台蓝图入口。
"""

from __future__ import annotations

from flask import Blueprint, g, request

import config
from core.admin import cache as admin_cache
from core.admin import common as admin_common
from core.admin import constants as admin_constants
from core.admin import dashboard as admin_dashboard
from core.admin import monitoring as admin_monitoring
from core.admin.policies import batch_update_policies, list_policies, update_policy
from core.admin.runtime_config import _DEFAULT_CONFIG_VALUES, _RUNTIME_CONFIG_OVERRIDES
from core.policy_runtime import invalidate_policy_cache
from core.price import batch_get_prices, get_forex_rates, get_price_runtime_metrics, get_price_source_health
from core.snapshot import take_snapshot
from core.system import system_manager


CONFIG_WHITELIST = admin_constants.CONFIG_WHITELIST
POLICY_LABELS = admin_constants.POLICY_LABELS
ACTION_LABELS = admin_constants.ACTION_LABELS
ERROR_LABELS = admin_constants.ERROR_LABELS
REGISTER_METHOD_LABELS = admin_constants.REGISTER_METHOD_LABELS
STATUS_LABELS = admin_constants.STATUS_LABELS
POLICY_TYPE_LABELS = admin_constants.POLICY_TYPE_LABELS

OPS_INVITE_ACQUIRE_TEXT_KEY = admin_constants.OPS_INVITE_ACQUIRE_TEXT_KEY
OPS_INVITE_ACQUIRE_IMAGE_URL_KEY = admin_constants.OPS_INVITE_ACQUIRE_IMAGE_URL_KEY
OPS_USER_GROUP_TEXT_KEY = admin_constants.OPS_USER_GROUP_TEXT_KEY
OPS_USER_GROUP_IMAGE_URL_KEY = admin_constants.OPS_USER_GROUP_IMAGE_URL_KEY
OPS_IOS_QR_TEXT_KEY = admin_constants.OPS_IOS_QR_TEXT_KEY
OPS_IOS_QR_IMAGE_URL_KEY = admin_constants.OPS_IOS_QR_IMAGE_URL_KEY
OPS_APP_UPDATE_TEXT_KEY = admin_constants.OPS_APP_UPDATE_TEXT_KEY
OPS_APP_UPDATE_DOWNLOAD_URL_KEY = admin_constants.OPS_APP_UPDATE_DOWNLOAD_URL_KEY
OPS_INVITE_ACQUIRE_TEXT_MAX_LENGTH = admin_constants.OPS_INVITE_ACQUIRE_TEXT_MAX_LENGTH
OPS_INVITE_ACQUIRE_IMAGE_URL_MAX_LENGTH = admin_constants.OPS_INVITE_ACQUIRE_IMAGE_URL_MAX_LENGTH
OPS_IOS_QR_TEXT_MAX_LENGTH = admin_constants.OPS_IOS_QR_TEXT_MAX_LENGTH
OPS_IOS_QR_IMAGE_URL_MAX_LENGTH = admin_constants.OPS_IOS_QR_IMAGE_URL_MAX_LENGTH
OPS_APP_UPDATE_TEXT_MAX_LENGTH = admin_constants.OPS_APP_UPDATE_TEXT_MAX_LENGTH
OPS_APP_UPDATE_DOWNLOAD_URL_MAX_LENGTH = admin_constants.OPS_APP_UPDATE_DOWNLOAD_URL_MAX_LENGTH
ADMIN_PORTFOLIO_CACHE_TTL_SECONDS = admin_constants.ADMIN_PORTFOLIO_CACHE_TTL_SECONDS
PRICE_ALERT_ROUTE_NAME = admin_constants.PRICE_ALERT_ROUTE_NAME

_admin_cache_clear = admin_cache.clear_admin_caches
_admin_cached_payload = admin_cache.cached_payload
_admin_cache_key = admin_cache.admin_cache_key
_admin_parse_force_arg = admin_cache.admin_parse_force_arg
_admin_log_read = admin_cache.log_admin_read

_make_invite_code = admin_common.make_invite_code
_load_script_module = admin_common.load_script_module
_coerce_bool = admin_common.coerce_bool
_json_body = admin_common.json_body
_admin_region_display = admin_common.admin_region_display
_real_user_where = admin_common.real_user_where
_has_local_anonymous_user = admin_common.has_local_anonymous_user

_get_user_ops_metrics = admin_dashboard.get_user_ops_metrics
_get_user_retention_rows = admin_dashboard.get_user_retention_rows
_build_mini_bars = admin_dashboard.build_mini_bars
_build_trend_text = admin_dashboard.build_trend_text
_recent_admin_audits = admin_dashboard.recent_admin_audits
_get_active_session_count = admin_dashboard.get_active_session_count
_build_admin_portfolio_payload = admin_dashboard.build_admin_portfolio_payload

_build_price_probe_payload = admin_monitoring.build_price_probe_payload
_load_price_alerts_payload = admin_monitoring.load_price_alerts_payload
_save_price_alert_report_snapshot = admin_monitoring.save_price_alert_report_snapshot
_get_latest_provider_test_report = admin_monitoring.get_latest_provider_test_report
_list_price_alert_report_history = admin_monitoring.list_price_alert_report_history
_get_latest_price_alert_report = admin_monitoring.get_latest_price_alert_report
_run_market_provider_test = admin_monitoring.run_market_provider_test
_run_forex_provider_test = admin_monitoring.run_forex_provider_test
_to_tencent_quote_code = admin_monitoring.to_tencent_quote_code

run_provider_test_report_job = admin_monitoring.run_provider_test_report_job


def create_admin_blueprint(db, admin_write_audit):
    admin_monitoring.set_admin_db(db)
    bp = Blueprint("admin_routes", __name__, url_prefix="/api/admin")

    from admin_routes_ai import register_admin_ai_routes
    from admin_routes_apis import register_admin_api_routes
    from admin_routes_config_ops import register_admin_config_ops_routes
    from admin_routes_dashboard import register_admin_dashboard_routes
    from admin_routes_data import register_admin_data_routes
    from admin_routes_invites import register_admin_invite_routes
    from admin_routes_user_write import register_admin_user_write_routes
    from admin_routes_users import register_admin_user_read_routes

    @bp.after_request
    def _admin_after_request(response):
        if request.method.upper() != "GET" and int(getattr(response, "status_code", 500) or 500) < 400:
            admin_cache.clear_admin_caches()
        return response

    register_admin_dashboard_routes(bp, db)
    register_admin_user_read_routes(bp, db)
    register_admin_user_write_routes(bp, db, admin_write_audit)
    register_admin_config_ops_routes(bp, db, admin_write_audit)
    register_admin_data_routes(bp, db, admin_write_audit)
    register_admin_api_routes(bp, db, admin_write_audit)
    register_admin_invite_routes(bp, db, admin_write_audit)
    register_admin_ai_routes(bp, db, admin_write_audit)
    return bp


__all__ = [
    "ACTION_LABELS",
    "ADMIN_PORTFOLIO_CACHE_TTL_SECONDS",
    "CONFIG_WHITELIST",
    "ERROR_LABELS",
    "POLICY_LABELS",
    "POLICY_TYPE_LABELS",
    "PRICE_ALERT_ROUTE_NAME",
    "REGISTER_METHOD_LABELS",
    "STATUS_LABELS",
    "_DEFAULT_CONFIG_VALUES",
    "_RUNTIME_CONFIG_OVERRIDES",
    "_admin_cache_clear",
    "_admin_cached_payload",
    "_admin_cache_key",
    "_admin_log_read",
    "_admin_parse_force_arg",
    "_admin_region_display",
    "_build_admin_portfolio_payload",
    "_build_mini_bars",
    "_build_price_probe_payload",
    "_build_trend_text",
    "_coerce_bool",
    "_get_active_session_count",
    "_get_latest_price_alert_report",
    "_get_latest_provider_test_report",
    "_get_user_ops_metrics",
    "_get_user_retention_rows",
    "_has_local_anonymous_user",
    "_json_body",
    "_list_price_alert_report_history",
    "_load_price_alerts_payload",
    "_load_script_module",
    "_make_invite_code",
    "_real_user_where",
    "_recent_admin_audits",
    "_run_forex_provider_test",
    "_run_market_provider_test",
    "_save_price_alert_report_snapshot",
    "_to_tencent_quote_code",
    "batch_get_prices",
    "batch_update_policies",
    "config",
    "create_admin_blueprint",
    "g",
    "get_forex_rates",
    "get_price_runtime_metrics",
    "get_price_source_health",
    "invalidate_policy_cache",
    "list_policies",
    "run_provider_test_report_job",
    "system_manager",
    "take_snapshot",
    "update_policy",
]
