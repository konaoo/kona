"""
后端主入口（薄入口）。

对外约定：
- gunicorn / wsgi 仍然可以用 `from app import app`
- 单测仍然可以 `import app as app_module` 并 patch `app_module.batch_get_prices / WEB_APP_DIST_DIR / WEB_ADMIN_DIST_DIR / take_snapshot ...`

所以这里会保留一批“单测需要 patch 的全局符号”，同时把实际组装交给 `app_factory.py`。
"""

from __future__ import annotations

import time

import config
from auth_routes import _issue_auth_tokens as _issue_auth_tokens_impl
from app_factory import AppWiring, create_app_components
from runtime_bootstrap import run_dev_server

# 这些 import 会被单测 patch，所以必须保留在 app.py 全局符号上
from core.asset_type import infer_asset_type
from core.auth import (
    optional_auth,
    verify_token,
    generate_token,
    hash_password,
    hash_refresh_token,
)
from core.ip_region import resolve_ip_region
from core.market_calendar import all_markets_closed, get_market_statuses
from core.news import news_fetcher
from core.parser import parse_code
from core.policy_runtime import is_policy_enabled, get_policy_limit_per_min
from core.fund import get_fund_latest_nav_date
from core.price import (
    batch_get_prices,
    batch_get_prices_fast,
    get_forex_rates,
    get_price,
    get_price_runtime_metrics,
    get_price_source_health,
    search_stocks,
)
from core.snapshot import calculate_portfolio_stats, take_snapshot
from core.stock import get_hstech_price, get_us_extended_quotes
from core.system import system_manager
from core.trend import batch_get_asset_trends


# 允许单测 patch：test_web_entry_api.py 会改这个路径来喂 index.html
WEB_APP_DIST_DIR = config.BASE_DIR / "static" / "web" / "app"
WEB_ADMIN_DIST_DIR = config.BASE_DIR / "static" / "web" / "admin"


def _issue_auth_tokens(user_id: str, username: str, device_id: str = "") -> dict:
    """兼容旧测试入口，内部实现已迁到 auth_routes.py。"""
    return _issue_auth_tokens_impl(db, user_id, username, device_id=device_id)


_wiring = AppWiring(
    database_path=config.DATABASE_PATH,
    backup_csv_path=config.BACKUP_CSV_PATH,
    ratelimit_storage_url=config.RATELIMIT_STORAGE_URL,
    request_runtime_storage_url=config.REQUEST_RUNTIME_STORAGE_URL,
    request_runtime_storage_prefix=config.REQUEST_RUNTIME_STORAGE_PREFIX,
    web_app_dist_dir_getter=lambda: WEB_APP_DIST_DIR,
    web_admin_dist_dir_getter=lambda: WEB_ADMIN_DIST_DIR,
    app_version=config.APP_VERSION,
    price_health_token_getter=lambda: config.PRICE_HEALTH_TOKEN,
    time_getter=lambda: time.time(),
    verify_token=verify_token,
    optional_auth=optional_auth,
    is_policy_enabled=is_policy_enabled,
    get_policy_limit_per_min=get_policy_limit_per_min,
    resolve_ip_region=resolve_ip_region,
    get_price_getter=lambda code, **kwargs: get_price(code, **kwargs),
    batch_get_prices_getter=lambda codes: batch_get_prices(codes),
    batch_get_prices_fast_getter=lambda codes, timeout_seconds=None: batch_get_prices_fast(
        codes,
        timeout_seconds=timeout_seconds,
    ),
    forex_rates_getter=lambda: get_forex_rates(),
    search_stocks_getter=lambda query: search_stocks(query),
    us_extended_quotes_getter=lambda symbols: get_us_extended_quotes(symbols),
    hstech_price_getter=lambda: get_hstech_price(),
    asset_trends_getter=lambda items, points: batch_get_asset_trends(items, points=points),
    price_runtime_metrics_getter=lambda: get_price_runtime_metrics(),
    price_source_health_getter=lambda: get_price_source_health(),
    fund_latest_nav_date_getter=lambda code: get_fund_latest_nav_date(code),
    calculate_portfolio_stats=calculate_portfolio_stats,
    background_snapshot_runner=lambda: take_snapshot(),
    take_snapshot_for_user=lambda user_id: take_snapshot(user_id),
    parse_code=parse_code,
    infer_asset_type=infer_asset_type,
    market_statuses_getter=lambda *args, **kwargs: get_market_statuses(*args, **kwargs),
    all_markets_closed_getter=all_markets_closed,
    system_manager=system_manager,
    news_fetcher=news_fetcher,
)

_components = create_app_components(wiring=_wiring)

logger = _components["logger"]
app = _components["app"]
db = _components["db"]
limiter = _components["limiter"]
request_runtime = _components["request_runtime"]
snapshot_runtime = _components["snapshot_runtime"]
portfolio_runtime = _components["portfolio_runtime"]
market_runtime = _components["market_runtime"]
startup_runtime = _components["startup_runtime"]
price_runtime = _components["price_runtime"]
run_provider_test_report_job = _components.get("run_provider_test_report_job")


if __name__ == "__main__":
    run_dev_server(components=_components)
