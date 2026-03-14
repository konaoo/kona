"""
主程序文件
整合所有功能，提供Web API
"""
import logging
import time
from flask import Flask, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

import config
try:
    from admin_routes import create_admin_blueprint, run_provider_test_report_job
except ModuleNotFoundError:
    create_admin_blueprint = None
    run_provider_test_report_job = None
from analysis_handlers import create_analysis_payload_handlers
from analysis_routes import create_analysis_blueprint
from asset_account_handlers import create_asset_account_payload_handlers
from asset_account_routes import create_asset_account_blueprint
from auth_routes import create_auth_blueprint, _issue_auth_tokens as _issue_auth_tokens_impl
from market_handlers import create_market_payload_handlers
from market_routes import create_market_blueprint
from market_runtime import create_market_runtime
from misc_routes import create_misc_blueprint
from misc_handlers import create_misc_payload_handlers
from news_routes import create_news_blueprint
from portfolio_handlers import create_portfolio_payload_handlers
from portfolio_routes import create_portfolio_blueprint
from quote_handlers import create_quote_payload_handlers
from quote_routes import create_quote_blueprint
from sync_handlers import create_sync_payload_handlers
from system_routes import create_system_blueprint
from web_entry_handlers import create_web_entry_handlers
from web_entry_routes import create_web_entry_blueprint
from portfolio_runtime import create_portfolio_runtime
from request_runtime import create_request_runtime
from snapshot_runtime import create_snapshot_runtime
from startup_runtime import create_startup_runtime
from core.db import DatabaseManager
from core.price import (
    get_price,
    batch_get_prices,
    batch_get_prices_fast,
    get_forex_rates,
    search_stocks,
    get_price_runtime_metrics,
    get_price_source_health,
    PricePreloader,
)
from core.parser import parse_code
from core.asset_type import infer_asset_type
from core.stock import get_hstech_price, get_us_extended_quotes
from core.market_calendar import all_markets_closed, get_market_statuses
from core.snapshot import take_snapshot, calculate_portfolio_stats
from core.news import news_fetcher
from core.system import system_manager
from core.trend import batch_get_asset_trends
from core.policy_runtime import (
    is_policy_enabled,
    get_policy_limit_per_min,
)
from core.auth import (
    optional_auth,
    generate_token,
    verify_token,
    hash_password,
    hash_refresh_token,
)
from core.ip_region import resolve_ip_region

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT,
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
db = DatabaseManager(str(config.DATABASE_PATH))


def _issue_auth_tokens(user_id: str, username: str, device_id: str = "") -> dict:
    """兼容旧测试入口，内部实现已迁到 auth_routes.py。"""
    return _issue_auth_tokens_impl(db, user_id, username, device_id=device_id)


_MARKET_SCOPE = ["a", "hk", "us", "fund"]


def _client_ip() -> str:
    """获取客户端 IP，优先读取反向代理头。"""
    xff = request.headers.get('X-Forwarded-For', '')
    if xff:
        return xff.split(',')[0].strip()
    xri = request.headers.get('X-Real-IP')
    if xri:
        return xri.strip()
    return request.remote_addr or 'unknown'


def _resolve_ip_region(ip: str) -> str:
    safe_ip = str(ip or "").strip()
    if not safe_ip:
        return ""
    try:
        return resolve_ip_region(safe_ip)
    except Exception as exc:
        logger.info("IP region lookup failed ip=%s error=%s", safe_ip, exc)
        return ""


def _rate_limit_key() -> str:
    return _client_ip() or get_remote_address()


limiter = Limiter(
    key_func=_rate_limit_key,
    app=app,
    default_limits=[],
    headers_enabled=True,
    storage_uri=config.RATELIMIT_STORAGE_URL,
)

WEB_DIST_DIR = config.BASE_DIR / "static" / "web"

# 初始化数据库（从CSV导入备份数据）
if not config.DATABASE_PATH.exists() and config.BACKUP_CSV_PATH.exists():
    logger.info("Importing backup data from CSV...")
    db.backup_from_csv(str(config.BACKUP_CSV_PATH))
request_runtime = create_request_runtime(
    db=db,
    logger=logger,
    client_ip_getter=_client_ip,
    resolve_ip_region=_resolve_ip_region,
    verify_token=verify_token,
    is_policy_enabled=is_policy_enabled,
    get_policy_limit_per_min=get_policy_limit_per_min,
    time_getter=lambda: time.time(),
)
request_runtime.register_hooks(app)
snapshot_runtime = create_snapshot_runtime(
    db=db,
    logger=logger,
    calculate_portfolio_stats=calculate_portfolio_stats,
    app_testing_getter=lambda: app.testing,
    background_snapshot_runner=lambda: take_snapshot(),
    provider_test_runner=run_provider_test_report_job,
    time_getter=lambda: time.time(),
)
portfolio_runtime = create_portfolio_runtime(
    parse_code=parse_code,
    infer_asset_type=infer_asset_type,
    batch_get_prices_getter=lambda codes: batch_get_prices(codes),
    time_getter=lambda: time.time(),
    logger=logger,
)
market_runtime = create_market_runtime(
    market_scope=_MARKET_SCOPE,
    market_statuses_getter=get_market_statuses,
    all_markets_closed_getter=all_markets_closed,
    time_getter=lambda: time.time(),
)
startup_runtime = create_startup_runtime(logger=logger)

if create_admin_blueprint is not None:
    app.register_blueprint(create_admin_blueprint(db, request_runtime.admin_write_audit))
else:
    logger.warning("admin_routes module not found; admin APIs are disabled")

analysis_payload_handlers = create_analysis_payload_handlers(
    db=db,
    price_batch_getter=lambda codes: batch_get_prices(codes),
)
web_entry_handlers = create_web_entry_handlers(
    web_dist_dir_getter=lambda: WEB_DIST_DIR,
    base_dir=config.BASE_DIR,
)
market_payload_handlers = create_market_payload_handlers(
    market_status_getter=lambda now_utc, force_refresh=False: market_runtime.get_market_status_cached(
        now_utc=now_utc,
        force_refresh=force_refresh,
    ),
    prices_batch_getter=lambda codes: batch_get_prices(codes),
    rates_getter=lambda: get_forex_rates(),
    hstech_price_getter=lambda: get_hstech_price(),
)
sync_payload_handlers = create_sync_payload_handlers(
    db=db,
    rates_getter=lambda: get_forex_rates(),
    market_status_refresh_getter=lambda now_utc, force_refresh=False: market_runtime.get_market_status_cached(
        now_utc=now_utc,
        force_refresh=force_refresh,
    ),
    market_scope=_MARKET_SCOPE,
)
misc_payload_handlers = create_misc_payload_handlers(
    db=db,
    asset_trends_getter=lambda items, points: batch_get_asset_trends(items, points=points),
    app_version=config.APP_VERSION,
    metrics_token_ok_getter=lambda: startup_runtime.metrics_token_ok(config.PRICE_HEALTH_TOKEN, request.headers),
    auth_audit=request_runtime.auth_audit,
    price_runtime_metrics_getter=lambda: get_price_runtime_metrics(),
    price_source_health_getter=lambda: get_price_source_health(),
)
quote_payload_handlers = create_quote_payload_handlers(
    get_price_getter=lambda code, **kwargs: get_price(code, **kwargs),
    batch_get_prices_fast_getter=lambda codes, timeout_seconds=None: batch_get_prices_fast(
        codes,
        timeout_seconds=timeout_seconds,
    ),
    rates_getter=lambda: get_forex_rates(),
    search_getter=lambda query: search_stocks(query),
    us_extended_quotes_getter=lambda symbols: get_us_extended_quotes(symbols),
    logger=logger,
)
asset_account_payload_handlers = create_asset_account_payload_handlers(
    db=db,
    logger=logger,
    snapshot_saver_async=lambda user_id: snapshot_runtime.save_snapshot_for_user_async(user_id),
)
portfolio_payload_handlers = create_portfolio_payload_handlers(
    db=db,
    logger=logger,
    snapshot_saver_async=lambda user_id: snapshot_runtime.save_snapshot_for_user_async(user_id),
    portfolio_identity_normalizer=portfolio_runtime.normalize_portfolio_identity,
    idempotency_begin=portfolio_runtime.idempotency_begin,
    idempotent_response=portfolio_runtime.idempotent_response,
    undo_decorator=portfolio_runtime.decorate_with_undo,
    undo_claim=portfolio_runtime.claim_undo_record,
    undo_release=portfolio_runtime.release_undo_claim,
    take_snapshot_func=lambda user_id: take_snapshot(user_id),
    rates_getter=lambda: get_forex_rates(),
    convert_amount=portfolio_runtime.convert_amount,
)

app.register_blueprint(
    create_analysis_blueprint(
        optional_auth=optional_auth,
        analysis_overview_payload_getter=analysis_payload_handlers['overview'],
        analysis_calendar_payload_getter=analysis_payload_handlers['calendar'],
        analysis_market_breakdown_payload_getter=analysis_payload_handlers['market_breakdown'],
        analysis_rank_payload_getter=analysis_payload_handlers['rank'],
    )
)
app.register_blueprint(
    create_web_entry_blueprint(
        index_handler=web_entry_handlers['index'],
        web_app_handler=web_entry_handlers['web_app'],
        web_admin_handler=web_entry_handlers['web_admin'],
        web_assets_handler=web_entry_handlers['web_assets'],
        assets_redirect_handler=web_entry_handlers['assets_redirect'],
        test_redirect_handler=web_entry_handlers['test_redirect'],
        compare_page_handler=web_entry_handlers['compare_page'],
        direct_test_page_handler=web_entry_handlers['direct_test_page'],
    )
)
app.register_blueprint(
    create_auth_blueprint(
        db,
        limiter,
        client_ip_getter=_client_ip,
        resolve_ip_region=_resolve_ip_region,
        auth_audit=request_runtime.auth_audit,
    )
)
app.register_blueprint(
    create_market_blueprint(
        optional_auth=optional_auth,
        market_status_payload_getter=market_payload_handlers['status'],
        market_indices_payload_getter=market_payload_handlers['indices'],
        sync_bootstrap_payload_getter=sync_payload_handlers['bootstrap'],
    )
)
app.register_blueprint(
    create_misc_blueprint(
        optional_auth=optional_auth,
        history_payload_getter=misc_payload_handlers['history'],
        asset_trends_payload_getter=misc_payload_handlers['asset_trends'],
        price_health_payload_getter=misc_payload_handlers['price_health'],
        health_payload_getter=misc_payload_handlers['health'],
    )
)
app.register_blueprint(create_news_blueprint(news_fetcher))
app.register_blueprint(
    create_quote_blueprint(
        price_payload_getter=quote_payload_handlers['price'],
        prices_batch_payload_getter=quote_payload_handlers['prices_batch'],
        rates_payload_getter=quote_payload_handlers['rates'],
        search_payload_getter=quote_payload_handlers['search'],
    )
)
app.register_blueprint(
    create_asset_account_blueprint(
        optional_auth=optional_auth,
        transactions_payload_getter=asset_account_payload_handlers['transactions'],
        cash_assets_payload_getter=asset_account_payload_handlers['cash_assets'],
        cash_asset_add_handler=asset_account_payload_handlers['cash_asset_add'],
        cash_asset_delete_handler=asset_account_payload_handlers['cash_asset_delete'],
        cash_asset_update_handler=asset_account_payload_handlers['cash_asset_update'],
        other_assets_payload_getter=asset_account_payload_handlers['other_assets'],
        other_asset_add_handler=asset_account_payload_handlers['other_asset_add'],
        other_asset_delete_handler=asset_account_payload_handlers['other_asset_delete'],
        other_asset_update_handler=asset_account_payload_handlers['other_asset_update'],
        liabilities_payload_getter=asset_account_payload_handlers['liabilities'],
        liability_add_handler=asset_account_payload_handlers['liability_add'],
        liability_delete_handler=asset_account_payload_handlers['liability_delete'],
        liability_update_handler=asset_account_payload_handlers['liability_update'],
    )
)
app.register_blueprint(
    create_portfolio_blueprint(
        optional_auth=optional_auth,
        portfolio_payload_getter=portfolio_payload_handlers['portfolio'],
        portfolio_add_handler=portfolio_payload_handlers['portfolio_add'],
        portfolio_update_handler=portfolio_payload_handlers['portfolio_update'],
        portfolio_modify_handler=portfolio_payload_handlers['portfolio_modify'],
        snapshot_save_handler=portfolio_payload_handlers['snapshot_save'],
        snapshot_trigger_handler=portfolio_payload_handlers['snapshot_trigger'],
        snapshot_fix_handler=portfolio_payload_handlers['snapshot_fix'],
        portfolio_delete_handler=portfolio_payload_handlers['portfolio_delete'],
        portfolio_delete_corrective_handler=portfolio_payload_handlers['portfolio_delete_corrective'],
        portfolio_buy_handler=portfolio_payload_handlers['portfolio_buy'],
        portfolio_buy_with_cash_handler=portfolio_payload_handlers['portfolio_buy_with_cash'],
        portfolio_sell_handler=portfolio_payload_handlers['portfolio_sell'],
        portfolio_undo_handler=portfolio_payload_handlers['portfolio_undo'],
    )
)
app.register_blueprint(create_system_blueprint(db, system_manager))


@app.errorhandler(429)
def ratelimit_handler(e):
    """限流统一返回与审计日志。"""
    request_runtime.auth_audit(
        event='rate_limit',
        outcome='blocked',
        reason=str(getattr(e, 'description', 'too many requests'))[:120],
        level='warning'
    )
    return jsonify({"error": "请求过于频繁，请稍后再试"}), 429

if __name__ == '__main__':
    logger.info("Starting Portfolio Management System v10.0...")
    logger.info(f"Database: {config.DATABASE_PATH}")
    logger.info(f"Server: http://{config.HOST}:{config.PORT}")

    startup_runtime.launch_runtime_services(
        enable_background_scheduler=bool(
            config.ENABLE_BACKGROUND_SNAPSHOT
            or (getattr(config, "ENABLE_BACKGROUND_PROVIDER_TEST", True) and run_provider_test_report_job is not None)
        ),
        background_scheduler_target=lambda: snapshot_runtime.background_scheduler(
            enable_background_snapshot_getter=lambda: bool(getattr(config, "ENABLE_BACKGROUND_SNAPSHOT", False)),
            enable_background_provider_test_getter=lambda: bool(
                getattr(config, "ENABLE_BACKGROUND_PROVIDER_TEST", True) and run_provider_test_report_job is not None
            ),
        ),
        enable_startup_snapshot=bool(config.ENABLE_STARTUP_SNAPSHOT),
        startup_snapshot_target=lambda: take_snapshot(),
        preloader_factory=lambda db_path, interval: PricePreloader.get_instance(
            db_path=db_path,
            interval=interval,
        ),
        db_path=str(config.DATABASE_PATH),
        preload_interval=config.PRELOAD_INTERVAL_SECONDS,
        open_browser_target=lambda: startup_runtime.open_browser(f'http://{config.HOST}:{config.PORT}'),
    )

    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
