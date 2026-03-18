"""
Flask App 组装工厂（只做“组装”，不做“启动后台线程”）。

为什么要单独做一层工厂：
- 让 app.py 变薄：对外入口仍保持 `app:app / db / limiter` 等不变；
- 把“依赖组装 + blueprint 注册 + hook 注册”集中管理，后面加/改接口不需要在入口文件里翻半天；
- 兼容单测：很多测试会 `patch(app_module.batch_get_prices / get_forex_rates / WEB_APP_DIST_DIR / WEB_ADMIN_DIST_DIR / take_snapshot...)`，
  所以所有“可能被 patch 的 getter”必须从 app.py 传进来，不能在这里 import 后直接闭包成常量引用。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
import atexit
from typing import Any, Callable, Dict, Optional

from flask import Flask, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

import config

try:
    from admin_routes import create_admin_blueprint
except ModuleNotFoundError:  # pragma: no cover
    create_admin_blueprint = None
try:
    from core.admin.monitoring import run_provider_test_report_job
except ModuleNotFoundError:  # pragma: no cover
    run_provider_test_report_job = None

from analysis_handlers import create_analysis_payload_handlers
from analysis_routes import create_analysis_blueprint
from asset_account_handlers import create_asset_account_payload_handlers
from asset_account_routes import create_asset_account_blueprint
from auth_routes import create_auth_blueprint
from market_handlers import create_market_payload_handlers
from market_routes import create_market_blueprint
from market_runtime import create_market_runtime
from misc_handlers import create_misc_payload_handlers
from misc_routes import create_misc_blueprint
from news_routes import create_news_blueprint
from portfolio_handlers import create_portfolio_payload_handlers
from portfolio_routes import create_portfolio_blueprint
from portfolio_runtime import create_portfolio_runtime
from quote_handlers import create_quote_payload_handlers
from quote_routes import create_quote_blueprint
from request_runtime import create_request_runtime
from snapshot_runtime import create_snapshot_runtime
from startup_runtime import create_startup_runtime
from price_runtime import create_price_runtime
from sync_handlers import create_sync_payload_handlers
from system_routes import create_system_blueprint
from web_entry_handlers import create_web_entry_handlers
from web_entry_routes import create_web_entry_blueprint

from core.db import DatabaseManager
from core.analysis_read_service import AnalysisReadService
from core.history_read_service import HistoryReadService
from core.portfolio_read_service import PortfolioReadService
from core.price import PricePreloader


@dataclass(frozen=True)
class AppWiring:
    """
    一组“可注入依赖”，主要服务两个目标：

    1) 让 app_factory 不绑死具体实现，入口变薄但更可测。
    2) 让单测能 patch app.py 里的全局符号并生效。

    约定：
    - 所有 getter 都是函数；这些函数可以是 app.py 里定义的 lambda，
      从而在测试 patch app_module.xxx 后能动态读取到新值。
    """

    # 基础路径/配置
    database_path: Any
    backup_csv_path: Any
    ratelimit_storage_url: str
    request_runtime_storage_url: str
    request_runtime_storage_prefix: str
    web_app_dist_dir_getter: Callable[[], Any]
    web_admin_dist_dir_getter: Callable[[], Any]
    app_version: str
    price_health_token_getter: Callable[[], str]
    time_getter: Callable[[], float]

    # 认证/策略/审计
    verify_token: Callable[..., Any]
    optional_auth: Callable[..., Any]
    is_policy_enabled: Callable[..., bool]
    get_policy_limit_per_min: Callable[..., int]
    resolve_ip_region: Callable[[str], str]

    # 行情/汇率/搜索/趋势（注意：这些都是 getter，不是原函数）
    get_price_getter: Callable[..., Any]
    batch_get_prices_getter: Callable[[Any], Any]
    batch_get_prices_fast_getter: Callable[..., Any]
    forex_rates_getter: Callable[[], Any]
    search_stocks_getter: Callable[[str], Any]
    us_extended_quotes_getter: Callable[[Any], Any]
    hstech_price_getter: Callable[[], Any]
    asset_trends_getter: Callable[[Any, int], Any]
    price_runtime_metrics_getter: Callable[[], Any]
    price_source_health_getter: Callable[[], Any]

    # 快照/分析/组合
    calculate_portfolio_stats: Callable[..., Any]
    background_snapshot_runner: Callable[[], Any]
    take_snapshot_for_user: Callable[[str], Any]

    # 投资组合标准化依赖
    parse_code: Callable[[str], Any]
    infer_asset_type: Callable[..., Any]

    # 市场开闭市判断
    market_statuses_getter: Callable[..., Any]
    all_markets_closed_getter: Callable[..., Any]

    # 其他依赖（对象/模块）
    system_manager: Any
    news_fetcher: Any


def _setup_logger() -> logging.Logger:
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format=config.LOG_FORMAT,
        handlers=[
            logging.FileHandler(config.LOG_FILE),
            logging.StreamHandler(),
        ],
    )
    return logging.getLogger(__name__)


def _client_ip() -> str:
    """获取客户端 IP，优先读取反向代理头。"""
    xff = request.headers.get("X-Forwarded-For", "")
    if xff:
        return xff.split(",")[0].strip()
    xri = request.headers.get("X-Real-IP")
    if xri:
        return xri.strip()
    return request.remote_addr or "unknown"


def _rate_limit_key() -> str:
    return _client_ip() or get_remote_address()


def _resolve_ip_region(logger: logging.Logger, resolver: Callable[[str], str], ip: str) -> str:
    safe_ip = str(ip or "").strip()
    if not safe_ip:
        return ""
    try:
        return resolver(safe_ip)
    except Exception as exc:  # pragma: no cover
        logger.info("IP region lookup failed ip=%s error=%s", safe_ip, exc)
        return ""


def create_app_components(
    *,
    wiring: AppWiring,
    logger: Optional[logging.Logger] = None,
) -> Dict[str, Any]:
    """
    创建 app + db + limiter 以及所有运行时依赖与蓝图注册。

    注意：
    - 这里只负责“组装”，不启动后台线程（后台线程在 runtime_bootstrap 里启动）。
    - 单测常常会 patch app.py 全局符号，所以 wiring 里必须传入 getter（通常是 app.py 的 lambda）。
    """
    logger = logger or _setup_logger()

    app = Flask(__name__)
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

    db = DatabaseManager(str(wiring.database_path))

    limiter = Limiter(
        key_func=_rate_limit_key,
        app=app,
        default_limits=[],
        headers_enabled=True,
        storage_uri=wiring.ratelimit_storage_url,
    )

    # 初始化数据库（从CSV导入备份数据）
    if (not getattr(wiring.database_path, "exists", lambda: False)()) and getattr(
        wiring.backup_csv_path, "exists", lambda: False
    )():
        logger.info("Importing backup data from CSV...")
        db.backup_from_csv(str(wiring.backup_csv_path))

    request_runtime = create_request_runtime(
        db=db,
        logger=logger,
        client_ip_getter=_client_ip,
        resolve_ip_region=lambda ip: _resolve_ip_region(logger, wiring.resolve_ip_region, ip),
        verify_token=wiring.verify_token,
        is_policy_enabled=wiring.is_policy_enabled,
        get_policy_limit_per_min=wiring.get_policy_limit_per_min,
        time_getter=wiring.time_getter,
        storage_url=wiring.request_runtime_storage_url,
        storage_prefix=wiring.request_runtime_storage_prefix,
    )
    request_runtime.register_hooks(app)

    snapshot_runtime = create_snapshot_runtime(
        db=db,
        logger=logger,
        calculate_portfolio_stats=wiring.calculate_portfolio_stats,
        app_testing_getter=lambda: app.testing,
        background_snapshot_runner=wiring.background_snapshot_runner,
        provider_test_runner=run_provider_test_report_job,
        time_getter=wiring.time_getter,
    )

    portfolio_runtime = create_portfolio_runtime(
        parse_code=wiring.parse_code,
        infer_asset_type=wiring.infer_asset_type,
        batch_get_prices_getter=wiring.batch_get_prices_getter,
        time_getter=wiring.time_getter,
        logger=logger,
    )

    market_runtime = create_market_runtime(
        market_scope=["a", "hk", "us", "fund"],
        market_statuses_getter=wiring.market_statuses_getter,
        all_markets_closed_getter=wiring.all_markets_closed_getter,
        time_getter=wiring.time_getter,
    )

    startup_runtime = create_startup_runtime(logger=logger)
    price_runtime = create_price_runtime(
        logger=logger,
        db=db,
        preloader_factory=lambda db_manager, interval: PricePreloader.get_instance(
            db_manager=db_manager,
            interval=interval,
        ),
    )
    atexit.register(price_runtime.stop_preloader)

    if create_admin_blueprint is not None:
        app.register_blueprint(
            create_admin_blueprint(db, request_runtime.admin_write_audit)
        )
    else:
        logger.warning("admin_routes module not found; admin APIs are disabled")

    analysis_read_service = AnalysisReadService(
        db=db,
        price_batch_getter=wiring.batch_get_prices_getter,
        stats_getter=wiring.calculate_portfolio_stats,
    )
    analysis_payload_handlers = create_analysis_payload_handlers(
        analysis_read_service=analysis_read_service,
    )
    web_entry_handlers = create_web_entry_handlers(
        web_app_dist_dir_getter=wiring.web_app_dist_dir_getter,
        web_admin_dist_dir_getter=wiring.web_admin_dist_dir_getter,
        base_dir=config.BASE_DIR,
    )
    market_payload_handlers = create_market_payload_handlers(
        market_status_getter=lambda now_utc, force_refresh=False: market_runtime.get_market_status_cached(
            now_utc=now_utc,
            force_refresh=force_refresh,
        ),
        prices_batch_getter=wiring.batch_get_prices_getter,
        rates_getter=wiring.forex_rates_getter,
        hstech_price_getter=wiring.hstech_price_getter,
    )
    portfolio_read_service = PortfolioReadService(
        db=db,
        batch_get_prices_getter=wiring.batch_get_prices_getter,
        rates_getter=wiring.forex_rates_getter,
        convert_amount=portfolio_runtime.convert_amount,
        market_status_getter=lambda now_utc, force_refresh=False: market_runtime.get_market_status_cached(
            now_utc=now_utc,
            force_refresh=force_refresh,
        ),
    )

    sync_payload_handlers = create_sync_payload_handlers(
        db=db,
        rates_getter=wiring.forex_rates_getter,
        market_status_refresh_getter=lambda now_utc, force_refresh=False: market_runtime.get_market_status_cached(
            now_utc=now_utc,
            force_refresh=force_refresh,
        ),
        market_scope=["a", "hk", "us", "fund"],
        portfolio_metrics_builder=lambda user_id, now_utc=None: portfolio_read_service.build_metrics_payload(
            user_id=user_id,
            now_utc=now_utc,
        ),
    )
    history_read_service = HistoryReadService(db=db)
    misc_payload_handlers = create_misc_payload_handlers(
        history_read_service=history_read_service,
        asset_trends_getter=wiring.asset_trends_getter,
        app_version=wiring.app_version,
        metrics_token_ok_getter=lambda: startup_runtime.metrics_token_ok(
            wiring.price_health_token_getter(),
            request.headers,
        ),
        auth_audit=request_runtime.auth_audit,
        price_runtime_metrics_getter=wiring.price_runtime_metrics_getter,
        price_source_health_getter=wiring.price_source_health_getter,
        request_runtime_metrics_getter=request_runtime.get_runtime_metrics,
    )
    quote_payload_handlers = create_quote_payload_handlers(
        get_price_getter=wiring.get_price_getter,
        batch_get_prices_fast_getter=wiring.batch_get_prices_fast_getter,
        rates_getter=wiring.forex_rates_getter,
        search_getter=wiring.search_stocks_getter,
        us_extended_quotes_getter=wiring.us_extended_quotes_getter,
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
        portfolio_read_service=portfolio_read_service,
        rates_getter=wiring.forex_rates_getter,
        convert_amount=portfolio_runtime.convert_amount,
        snapshot_saver_async=lambda user_id: snapshot_runtime.save_snapshot_for_user_async(user_id),
        portfolio_identity_normalizer=portfolio_runtime.normalize_portfolio_identity,
        idempotency_begin=portfolio_runtime.idempotency_begin,
        idempotent_response=portfolio_runtime.idempotent_response,
        undo_decorator=portfolio_runtime.decorate_with_undo,
        undo_claim=portfolio_runtime.claim_undo_record,
        undo_release=portfolio_runtime.release_undo_claim,
        take_snapshot_func=wiring.take_snapshot_for_user,
    )

    app.register_blueprint(
        create_analysis_blueprint(
            optional_auth=wiring.optional_auth,
            analysis_overview_payload_getter=analysis_payload_handlers["overview"],
            analysis_calendar_payload_getter=analysis_payload_handlers["calendar"],
            analysis_market_breakdown_payload_getter=analysis_payload_handlers["market_breakdown"],
            analysis_rank_payload_getter=analysis_payload_handlers["rank"],
        )
    )
    app.register_blueprint(
        create_web_entry_blueprint(
            index_handler=web_entry_handlers["index"],
            web_app_handler=web_entry_handlers["web_app"],
            web_admin_handler=web_entry_handlers["web_admin"],
            web_assets_handler=web_entry_handlers["web_assets"],
            assets_redirect_handler=web_entry_handlers["assets_redirect"],
            test_redirect_handler=web_entry_handlers["test_redirect"],
            compare_page_handler=web_entry_handlers["compare_page"],
            direct_test_page_handler=web_entry_handlers["direct_test_page"],
        )
    )
    app.register_blueprint(
        create_auth_blueprint(
            db,
            limiter,
            client_ip_getter=_client_ip,
            resolve_ip_region=lambda ip: _resolve_ip_region(logger, wiring.resolve_ip_region, ip),
            auth_audit=request_runtime.auth_audit,
        )
    )
    app.register_blueprint(
        create_market_blueprint(
            optional_auth=wiring.optional_auth,
            market_status_payload_getter=market_payload_handlers["status"],
            market_indices_payload_getter=market_payload_handlers["indices"],
            sync_bootstrap_payload_getter=sync_payload_handlers["bootstrap"],
        )
    )
    app.register_blueprint(
        create_misc_blueprint(
            optional_auth=wiring.optional_auth,
            history_payload_getter=misc_payload_handlers["history"],
            asset_trends_payload_getter=misc_payload_handlers["asset_trends"],
            price_health_payload_getter=misc_payload_handlers["price_health"],
            health_payload_getter=misc_payload_handlers["health"],
        )
    )
    app.register_blueprint(create_news_blueprint(wiring.news_fetcher))
    app.register_blueprint(
        create_quote_blueprint(
            price_payload_getter=quote_payload_handlers["price"],
            prices_batch_payload_getter=quote_payload_handlers["prices_batch"],
            rates_payload_getter=quote_payload_handlers["rates"],
            search_payload_getter=quote_payload_handlers["search"],
        )
    )
    app.register_blueprint(
        create_asset_account_blueprint(
            optional_auth=wiring.optional_auth,
            transactions_payload_getter=asset_account_payload_handlers["transactions"],
            cash_assets_payload_getter=asset_account_payload_handlers["cash_assets"],
            cash_asset_add_handler=asset_account_payload_handlers["cash_asset_add"],
            cash_asset_delete_handler=asset_account_payload_handlers["cash_asset_delete"],
            cash_asset_update_handler=asset_account_payload_handlers["cash_asset_update"],
            other_assets_payload_getter=asset_account_payload_handlers["other_assets"],
            other_asset_add_handler=asset_account_payload_handlers["other_asset_add"],
            other_asset_delete_handler=asset_account_payload_handlers["other_asset_delete"],
            other_asset_update_handler=asset_account_payload_handlers["other_asset_update"],
            liabilities_payload_getter=asset_account_payload_handlers["liabilities"],
            liability_add_handler=asset_account_payload_handlers["liability_add"],
            liability_delete_handler=asset_account_payload_handlers["liability_delete"],
            liability_update_handler=asset_account_payload_handlers["liability_update"],
        )
    )
    app.register_blueprint(
        create_portfolio_blueprint(
            optional_auth=wiring.optional_auth,
            portfolio_payload_getter=portfolio_payload_handlers["portfolio"],
            portfolio_add_handler=portfolio_payload_handlers["portfolio_add"],
            portfolio_update_handler=portfolio_payload_handlers["portfolio_update"],
            portfolio_modify_handler=portfolio_payload_handlers["portfolio_modify"],
            snapshot_save_handler=portfolio_payload_handlers["snapshot_save"],
            snapshot_trigger_handler=portfolio_payload_handlers["snapshot_trigger"],
            snapshot_fix_handler=portfolio_payload_handlers["snapshot_fix"],
            portfolio_delete_handler=portfolio_payload_handlers["portfolio_delete"],
            portfolio_delete_corrective_handler=portfolio_payload_handlers["portfolio_delete_corrective"],
            portfolio_buy_handler=portfolio_payload_handlers["portfolio_buy"],
            portfolio_buy_with_cash_handler=portfolio_payload_handlers["portfolio_buy_with_cash"],
            portfolio_sell_handler=portfolio_payload_handlers["portfolio_sell"],
            portfolio_sell_to_cash_handler=portfolio_payload_handlers["portfolio_sell_to_cash"],
            portfolio_undo_handler=portfolio_payload_handlers["portfolio_undo"],
        )
    )
    app.register_blueprint(create_system_blueprint(db, wiring.system_manager))

    @app.errorhandler(429)
    def ratelimit_handler(e):  # noqa: ANN001
        """限流统一返回与审计日志。"""
        request_runtime.auth_audit(
            event="rate_limit",
            outcome="blocked",
            reason=str(getattr(e, "description", "too many requests"))[:120],
            level="warning",
        )
        return jsonify({"error": "请求过于频繁，请稍后再试"}), 429

    return {
        "app": app,
        "db": db,
        "limiter": limiter,
        "logger": logger,
        "request_runtime": request_runtime,
        "snapshot_runtime": snapshot_runtime,
        "portfolio_runtime": portfolio_runtime,
        "market_runtime": market_runtime,
        "startup_runtime": startup_runtime,
        "price_runtime": price_runtime,
        "run_provider_test_report_job": run_provider_test_report_job,
    }
