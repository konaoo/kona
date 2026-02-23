"""
主程序文件
整合所有功能，提供Web API
"""
import logging
import threading
import webbrowser
import time
import secrets
import json
import hashlib
from functools import wraps
from collections import defaultdict
from flask import Flask, render_template, jsonify, request, make_response, send_file, send_from_directory, g, redirect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pathlib import Path
import os

import config
try:
    from admin_routes import create_admin_blueprint
except ModuleNotFoundError:
    create_admin_blueprint = None
from core.db import DatabaseManager
from core.price import (
    get_price,
    batch_get_prices,
    get_forex_rates,
    search_stocks,
    get_price_runtime_metrics,
    get_price_source_health,
)
from core.parser import parse_code, get_display_code
from core.asset_type import infer_asset_type
from core.stock import get_us_extended_quotes
from core.market_calendar import all_markets_closed, get_market_statuses
from core.snapshot import take_snapshot, calculate_portfolio_stats
from core.news import news_fetcher
from core.system import system_manager
from core.policy_runtime import (
    is_policy_enabled,
    get_policy_limit_per_min,
)
from core.auth import (
    login_required,
    optional_auth,
    generate_token,
    verify_token,
    get_user_profile,
    normalize_username,
    is_valid_username,
    validate_password,
    verify_password,
    hash_password,
    generate_refresh_token,
    hash_refresh_token,
)
import re
from typing import Any, Dict
from datetime import datetime, timedelta, timezone

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
_snapshot_lock = threading.Lock()
_snapshot_inflight = set()
_snapshot_last_run_ts = {}
_SNAPSHOT_MIN_INTERVAL_SECONDS = 3.0
_MARKET_SCOPE = ["a", "hk", "us", "fund"]
_SYNC_BOOTSTRAP_DOMAINS = (
    "portfolio",
    "cash_assets",
    "other_assets",
    "liabilities",
    "history",
    "overview_all",
    "rates",
)
_QUOTE_POLICY_DEFAULT = {
    "interval_open_sec": 5,
    "interval_closed_sec": 120,
    "interval_us_extended_sec": 10,
}
_idempotency_lock = threading.Lock()
_idempotency_records = {}
_IDEMPOTENCY_WINDOW_SECONDS = 20.0
_undo_lock = threading.Lock()
_undo_records = {}
_UNDO_WINDOW_SECONDS = 15.0
_policy_rate_lock = threading.Lock()
_policy_rate_counters = defaultdict(int)
_PASSWORD_CHANGE_ALLOWED_PATHS = {
    "/api/auth/password/change",
    "/api/auth/logout",
    "/api/auth/me",
}


def _client_ip() -> str:
    """获取客户端 IP，优先读取反向代理头。"""
    xff = request.headers.get('X-Forwarded-For', '')
    if xff:
        return xff.split(',')[0].strip()
    xri = request.headers.get('X-Real-IP')
    if xri:
        return xri.strip()
    return request.remote_addr or 'unknown'


def _rate_limit_key() -> str:
    return _client_ip() or get_remote_address()


def _idempotency_begin(action: str, user_id: str, request_id: str):
    request_id = (request_id or '').strip()
    if not request_id:
        return False, None, None
    now = time.time()
    key = (user_id or '', action, request_id)
    with _idempotency_lock:
        expired = [k for k, v in _idempotency_records.items() if v.get('expires_at', 0) < now]
        for k in expired:
            _idempotency_records.pop(k, None)
        record = _idempotency_records.get(key)
        if record:
            if record.get('state') == 'done':
                return True, record.get('payload', {"status": "ok"}), int(record.get('status_code', 200))
            return True, {"status": "ok", "code": "REQUEST_DEDUP_IN_FLIGHT"}, 200
        _idempotency_records[key] = {
            'state': 'inflight',
            'expires_at': now + _IDEMPOTENCY_WINDOW_SECONDS,
        }
    return False, None, None


def _idempotency_finish(action: str, user_id: str, request_id: str, status_code: int, payload: dict):
    request_id = (request_id or '').strip()
    if not request_id:
        return
    key = (user_id or '', action, request_id)
    with _idempotency_lock:
        _idempotency_records[key] = {
            'state': 'done',
            'status_code': int(status_code),
            'payload': payload,
            'expires_at': time.time() + _IDEMPOTENCY_WINDOW_SECONDS,
        }


def _idempotent_response(action: str, user_id: str, request_id: str, payload: dict, status_code: int = 200):
    _idempotency_finish(action, user_id, request_id, status_code, payload)
    return jsonify(payload), status_code


def _undo_key(user_id: str, token: str):
    return (user_id or '', token)


def _cleanup_undo_records_locked(now_ts: float):
    expired = [k for k, v in _undo_records.items() if v.get('expires_at', 0) < now_ts]
    for k in expired:
        _undo_records.pop(k, None)


def _create_undo_record(user_id: str, operation: dict):
    token = secrets.token_urlsafe(18)
    expires_at_ts = time.time() + _UNDO_WINDOW_SECONDS
    key = _undo_key(user_id, token)
    with _undo_lock:
        _cleanup_undo_records_locked(time.time())
        _undo_records[key] = {
            'operation': operation,
            'expires_at': expires_at_ts,
            'used': False,
        }
    expires_at_iso = datetime.fromtimestamp(expires_at_ts, tz=timezone.utc).isoformat()
    return token, expires_at_iso


def _claim_undo_record(user_id: str, token: str):
    token = (token or '').strip()
    if not token:
        return None, ('UNDO_TOKEN_REQUIRED', 'Missing undo token', 400)
    now = time.time()
    key = _undo_key(user_id, token)
    with _undo_lock:
        _cleanup_undo_records_locked(now)
        record = _undo_records.get(key)
        if not record:
            return None, ('UNDO_TOKEN_EXPIRED', 'Undo token is invalid or expired', 400)
        if record.get('used'):
            return None, ('UNDO_ALREADY_USED', 'Undo token already used', 409)
        record['used'] = True
        return record.get('operation'), None


def _release_undo_claim(user_id: str, token: str):
    key = _undo_key(user_id, token)
    with _undo_lock:
        record = _undo_records.get(key)
        if record:
            record['used'] = False


def _decorate_with_undo(payload: dict, user_id: str, operation: dict):
    undo_token, undo_expire_at = _create_undo_record(user_id, operation)
    result = dict(payload)
    result['undo_token'] = undo_token
    result['undo_expire_at'] = undo_expire_at
    return result


def _to_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _rate_to_cny(curr: str, rates: dict) -> float:
    c = (curr or 'CNY').upper()
    if c == 'CNY':
        return 1.0
    raw = rates.get(c) if isinstance(rates, dict) else None
    rate = _to_float(raw, 0.0)
    return rate if rate > 0 else 1.0


def _convert_amount(amount: float, from_curr: str, to_curr: str, rates: dict) -> float:
    from_rate = _rate_to_cny(from_curr, rates)
    to_rate = _rate_to_cny(to_curr, rates)
    cny_amount = amount * from_rate
    return cny_amount / to_rate if to_rate > 0 else cny_amount


def _sync_rates_version(rates: Dict[str, Any]) -> str:
    try:
        normalized = {
            str(k): float(v)
            for k, v in sorted((rates or {}).items(), key=lambda item: str(item[0]))
        }
    except Exception:
        normalized = {}
    raw = json.dumps(normalized, ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _normalize_sync_include(raw_include: Any) -> list[str]:
    if not isinstance(raw_include, list):
        return list(_SYNC_BOOTSTRAP_DOMAINS)
    include: list[str] = []
    for item in raw_include:
        key = str(item or "").strip().lower()
        if key in _SYNC_BOOTSTRAP_DOMAINS and key not in include:
            include.append(key)
    return include or list(_SYNC_BOOTSTRAP_DOMAINS)


def _build_sync_domain_data(domain: str, user_id: str = None) -> Any:
    if domain == "portfolio":
        return db.get_portfolio(user_id=user_id)
    if domain == "cash_assets":
        return db.get_cash_assets(user_id=user_id)
    if domain == "other_assets":
        return db.get_other_assets(user_id=user_id)
    if domain == "liabilities":
        return db.get_liabilities(user_id=user_id)
    if domain == "history":
        return db.get_history(365, user_id=user_id)
    if domain == "overview_all":
        return {
            "day": db.get_pnl_overview("day", user_id),
            "month": db.get_pnl_overview("month", user_id),
            "year": db.get_pnl_overview("year", user_id),
            "all": db.get_pnl_overview("all", user_id),
        }
    if domain == "rates":
        return get_forex_rates()
    return None


def _username_limit_key() -> str:
    data = request.get_json(silent=True) or {}
    username = normalize_username(str(data.get('username', '')))
    return f"username:{username}" if username else f"ip:{_rate_limit_key()}"


limiter = Limiter(
    key_func=_rate_limit_key,
    app=app,
    default_limits=[],
    headers_enabled=True,
    storage_uri=config.RATELIMIT_STORAGE_URL,
)

# 应用版本号，用于强制刷新缓存
APP_VERSION = config.APP_VERSION
WEB_DIST_DIR = config.BASE_DIR / "static" / "web"


def _is_long_cache_asset(path: str) -> bool:
    normalized = (path or "").strip().lower()
    if not normalized:
        return False

    if normalized in {"index.html", "manifest.json"}:
        return False

    suffix = Path(normalized).suffix.lower()
    if suffix in {".html", ".json"}:
        return False
    return suffix in {".js", ".css", ".png", ".jpg", ".jpeg", ".svg", ".webp", ".ico", ".map", ".woff", ".woff2", ".ttf"}


def _serve_web_asset(asset_path: str = ""):
    web_dir = WEB_DIST_DIR
    index_file = web_dir / "index.html"
    if not index_file.exists():
        return jsonify({"error": "Web bundle not found"}), 404

    normalized_path = (asset_path or "").strip().lstrip("/")
    target_file = web_dir / normalized_path if normalized_path else index_file

    if normalized_path and target_file.exists() and target_file.is_file():
        response = make_response(send_from_directory(str(web_dir), normalized_path))
        if _is_long_cache_asset(normalized_path):
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        else:
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

    response = make_response(send_from_directory(str(web_dir), "index.html"))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# 初始化数据库（从CSV导入备份数据）
if not config.DATABASE_PATH.exists() and config.BACKUP_CSV_PATH.exists():
    logger.info("Importing backup data from CSV...")
    db.backup_from_csv(str(config.BACKUP_CSV_PATH))


def _mask_username(username: str) -> str:
    """用户名脱敏，避免日志暴露完整标识。"""
    u = (username or "").strip().lower()
    if not u:
        return ''
    if len(u) <= 2:
        return f"{u[0]}*"
    return f"{u[:2]}***"


def _auth_audit(event: str, outcome: str, username: str = '', reason: str = '', level: str = 'info'):
    """认证相关安全审计日志。"""
    msg = (
        f"SECURITY event={event} outcome={outcome} "
        f"ip={_client_ip()} username={_mask_username(username)} reason={reason} "
        f"path={request.path} ua={request.headers.get('User-Agent', '-')[:120]}"
    )
    if level == 'warning':
        logger.warning(msg)
    else:
        logger.info(msg)


def _resolve_api_policy_scope(path: str) -> str:
    p = (path or "").strip()
    if p.startswith("/api/auth/"):
        return "api.auth"
    if p.startswith("/api/news"):
        return "api.news"
    if p.startswith(
        (
            "/api/portfolio",
            "/api/cash_assets",
            "/api/other_assets",
            "/api/liabilities",
            "/api/transactions",
            "/api/history",
            "/api/analysis",
            "/api/snapshot",
        )
    ):
        return "api.portfolio"
    return ""


def _apply_policy_rate_limit(scope_key: str, limit_per_min: int) -> bool:
    if limit_per_min <= 0:
        return True
    now_minute = int(time.time() // 60)
    key = (scope_key, _client_ip(), now_minute)
    with _policy_rate_lock:
        stale_keys = [k for k in _policy_rate_counters.keys() if k[2] < now_minute - 1]
        for stale_key in stale_keys:
            _policy_rate_counters.pop(stale_key, None)
        _policy_rate_counters[key] += 1
        return _policy_rate_counters[key] <= limit_per_min


@app.before_request
def _enforce_api_group_policy():
    path = request.path or ""
    if not path.startswith("/api/"):
        return None
    if path.startswith("/api/admin/"):
        return None

    scope_key = _resolve_api_policy_scope(path)
    if not scope_key:
        return None

    auth_header = request.headers.get("Authorization", "")
    parts = auth_header.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        valid, payload = verify_token(parts[1])
        if valid and payload and payload.get("user_id"):
            user = db.get_user_by_id(payload.get("user_id"))
            if user and str(user.get("status") or "active").lower() != "active":
                return jsonify({"error": "User is disabled"}), 403
            if user and bool(user.get("must_change_password")) and path not in _PASSWORD_CHANGE_ALLOWED_PATHS:
                return (
                    jsonify(
                        {
                            "error": "Password change required",
                            "code": "PASSWORD_CHANGE_REQUIRED",
                        }
                    ),
                    403,
                )

    if not is_policy_enabled(scope_key, default=True):
        return (
            jsonify(
                {
                    "error": "Service temporarily disabled",
                    "code": "API_SCOPE_DISABLED",
                    "scope_key": scope_key,
                }
            ),
            503,
        )

    limit_per_min = get_policy_limit_per_min(scope_key)
    if limit_per_min and not _apply_policy_rate_limit(scope_key, limit_per_min):
        return (
            jsonify(
                {
                    "error": "Rate limit exceeded",
                    "code": "API_SCOPE_RATE_LIMITED",
                    "scope_key": scope_key,
                }
            ),
            429,
        )
    return None


def _refresh_token_expiry_days() -> int:
    return int(getattr(config, "AUTH_REFRESH_TOKEN_DAYS", 365))


def _is_refresh_token_valid(token_row: dict) -> bool:
    if not token_row:
        return False
    if token_row.get("revoked_at"):
        return False
    expires_at = token_row.get("expires_at")
    if not expires_at:
        return False
    try:
        expire_dt = datetime.fromisoformat(str(expires_at))
    except Exception:
        return False
    if expire_dt.tzinfo is not None:
        expire_dt = expire_dt.astimezone(timezone.utc).replace(tzinfo=None)
    return expire_dt > datetime.utcnow()


def _issue_auth_tokens(user_id: str, username: str, device_id: str = "") -> dict:
    access_token = generate_token(user_id, username)
    refresh_token = generate_refresh_token()
    refresh_hash = hash_refresh_token(refresh_token)
    expires_at = datetime.utcnow() + timedelta(days=_refresh_token_expiry_days())
    db.create_refresh_token(
        user_id=user_id,
        token_hash=refresh_hash,
        expires_at=expires_at,
        device_id=device_id,
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "refresh_expires_at": expires_at.isoformat(),
    }


def _generate_invite_code(length: int = 10) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _record_admin_audit(
    action: str,
    status_code: int,
    result: str,
    target_type: str = '',
    target_id: str = '',
    error: str = '',
):
    """写入后台审计日志。"""
    try:
        payload = request.get_json(silent=True)
        request_body = json.dumps(payload, ensure_ascii=False)[:4000] if payload is not None else ''
        admin_user_id = getattr(g, 'user_id', '') or ''
        db.add_admin_audit_log(
            admin_user_id=admin_user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            method=request.method,
            path=request.path,
            ip=_client_ip(),
            request_body=request_body,
            status_code=status_code,
            result=result,
            error=(error or '')[:500],
        )
    except Exception as e:
        logger.error(f"Failed to record admin audit: {e}")


def admin_write_audit(action: str, target_type: str = ''):
    """后台写操作审计装饰器。"""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            payload = request.get_json(silent=True) or {}
            target_id = ''
            if isinstance(payload, dict):
                for key in ('id', 'user_id', 'key', 'date'):
                    if payload.get(key) is not None:
                        target_id = str(payload.get(key))[:128]
                        break
            try:
                response = f(*args, **kwargs)
                resp = make_response(response)
                status_code = resp.status_code
                result = 'success' if 200 <= status_code < 400 else 'failed'
                error = ''
                if status_code >= 400:
                    body = resp.get_json(silent=True) or {}
                    if isinstance(body, dict):
                        error = str(body.get('error', ''))[:500]
                _record_admin_audit(
                    action=action,
                    target_type=target_type,
                    target_id=target_id,
                    status_code=status_code,
                    result=result,
                    error=error,
                )
                return response
            except Exception as e:
                _record_admin_audit(
                    action=action,
                    target_type=target_type,
                    target_id=target_id,
                    status_code=500,
                    result='failed',
                    error=str(e),
                )
                raise
        return wrapped
    return decorator


if create_admin_blueprint is not None:
    app.register_blueprint(create_admin_blueprint(db, admin_write_audit))
else:
    logger.warning("admin_routes module not found; admin APIs are disabled")


def _metrics_token_ok() -> bool:
    """校验运行指标接口访问令牌。"""
    expected = config.PRICE_HEALTH_TOKEN
    if not expected:
        return True
    token = request.headers.get('X-Kona-Metrics-Token', '').strip()
    if not token:
        auth_header = request.headers.get('Authorization', '')
        if auth_header.lower().startswith('bearer '):
            token = auth_header.split(' ', 1)[1].strip()
    if not token:
        return False
    return secrets.compare_digest(token, expected)


@app.errorhandler(429)
def ratelimit_handler(e):
    """限流统一返回与审计日志。"""
    _auth_audit(
        event='rate_limit',
        outcome='blocked',
        reason=str(getattr(e, 'description', 'too many requests'))[:120],
        level='warning'
    )
    return jsonify({"error": "Too many requests"}), 429


def open_browser():
    """自动打开浏览器"""
    time.sleep(1.5)
    webbrowser.open(f'http://{config.HOST}:{config.PORT}')


@app.route('/')
def index():
    """新 Web 门户入口。"""
    return _serve_web_asset()


@app.route('/app')
@app.route('/app/')
@app.route('/app/<path:asset_path>')
def web_app_route(asset_path: str = ""):
    """业务端 SPA 入口与深链回退。"""
    return _serve_web_asset(asset_path)


@app.route('/admin')
@app.route('/admin/')
@app.route('/admin/<path:asset_path>')
def web_admin_route(asset_path: str = ""):
    """管理端 SPA 入口与深链回退。"""
    return _serve_web_asset(asset_path)


@app.route('/assets/<path:asset_path>')
def web_assets(asset_path: str):
    """独立 H5 静态资源目录（Vite 默认 /assets/*）。"""
    return _serve_web_asset(f"assets/{asset_path}")


@app.route('/assets')
def assets():
    """旧资产页入口兼容跳转。"""
    if config.WEB_ENABLE_LEGACY_REDIRECT:
        return redirect('/app/invest', code=302)
    response = make_response(render_template('assets.html', version=APP_VERSION))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['X-App-Version'] = APP_VERSION
    return response


@app.route('/test')
def test_page():
    """测试页面"""
    return make_response(render_template('test_api.html'))


@app.route('/compare')
def compare_page():
    """主页面JavaScript测试"""
    with open(config.BASE_DIR / 'static_compare.html', 'r', encoding='utf-8') as f:
        return f.read()


@app.route('/direct_test')
def direct_test_page():
    """直接测试页面"""
    with open(config.BASE_DIR / 'direct_test.html', 'r', encoding='utf-8') as f:
        return f.read()
 


@app.route('/api/price')
def api_price():
    """获取单个价格"""
    code = request.args.get('code', '')
    if not code:
        return jsonify({"error": "Missing code"}), 400
    
    price, yclose, amt, chg = get_price(code)
    
    return jsonify({
        "price": price,
        "yclose": yclose,
        "amt": amt,
        "chg": chg
    })


@app.route('/api/prices/batch', methods=['POST'])
def api_prices_batch():
    """批量获取价格"""
    data = request.json
    codes = data.get('codes', [])
    
    if not codes:
        return jsonify({"error": "Missing codes"}), 400
    
    results = batch_get_prices(codes)
    
    # 将元组转换为对象，便于前端使用
    formatted_results = {}
    for code, (price, yclose, amt, chg) in results.items():
        formatted_results[code] = {
            "price": price,
            "yclose": yclose,
            "amt": amt,
            "chg": chg
        }

    us_codes = []
    symbol_by_code = {}
    for code in codes:
        code_text = str(code or '').strip()
        if not code_text:
            continue
        lower = code_text.lower()
        is_us_code = lower.startswith('gb_') or bool(re.fullmatch(r'[A-Za-z][A-Za-z\.\-]*', code_text))
        if not is_us_code:
            continue
        symbol = code_text[3:] if code_text.lower().startswith('gb_') else code_text
        symbol = symbol.strip().upper()
        if not symbol:
            continue
        us_codes.append(code_text)
        symbol_by_code[code_text] = symbol

    if symbol_by_code:
        try:
            us_quotes = get_us_extended_quotes(list(set(symbol_by_code.values())))
            for code in us_codes:
                symbol = symbol_by_code.get(code)
                quote = us_quotes.get(symbol or '', {})
                if not quote:
                    continue
                base = dict(formatted_results.get(code, {}))
                yclose = quote.get('yclose', base.get('yclose', 0))
                if quote.get('price', 0) > 0:
                    base['price'] = quote.get('price', 0)
                if yclose:
                    base['yclose'] = yclose
                base['amt'] = quote.get('amt', base.get('amt', 0))
                base['chg'] = quote.get('chg', base.get('chg', 0))
                base['regular_price'] = quote.get('regular_price', 0)
                base['premarket_price'] = quote.get('premarket_price', 0)
                base['after_hours_price'] = quote.get('after_hours_price', 0)
                base['session'] = quote.get('session', 'closed')
                base['effective_session'] = quote.get('effective_session', base['session'])
                base['extended_active'] = bool(quote.get('extended_active', False))
                formatted_results[code] = base
        except Exception as exc:
            logger.warning("US extended quote merge failed: %s", exc)
    
    return jsonify(formatted_results)


@app.route('/api/rates')
def api_rates():
    """获取汇率"""
    rates = get_forex_rates()
    return jsonify(rates)


@app.route('/api/portfolio', methods=['GET'])
@optional_auth
def get_portfolio():
    """获取持仓数据，支持按类型筛选"""
    asset_type = request.args.get('type', 'all')
    user_id = g.user_id  # 从认证中间件获取
    logger.info(f"API: get_portfolio called with type={asset_type}, user_id={user_id}")
    data = db.get_portfolio(asset_type, user_id)
    logger.info(f"API: returning {len(data)} records")
    response = jsonify(data)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0, private'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['Vary'] = '*'
    return response


@app.route('/api/portfolio/add', methods=['POST'])
@optional_auth
def add_asset():
    """添加资产"""
    data = request.json
    user_id = g.user_id
    request_id = str((data or {}).get('request_id', '')).strip()
    
    if not data or 'code' not in data or 'qty' not in data or 'price' not in data:
        return jsonify({"error": "Missing required fields"}), 400

    dedup_hit, dedup_payload, dedup_status = _idempotency_begin('portfolio_add', user_id, request_id)
    if dedup_hit:
        return jsonify(dedup_payload), dedup_status
    
    # 解析代码
    parsed = parse_code(data['code'], data.get('curr', ''))
    data['code'] = parsed['code']
    data['curr'] = parsed['curr']
    data['name'] = data.get('name', parsed['code'])
    data['adjustment'] = data.get('adjustment', 0.0)
    # 资产类型（基金/港股/美股/A股）
    provided_type = data.get('asset_type', '').strip()
    inferred_type = infer_asset_type(data['code'], data.get('name', ''))
    if not provided_type:
        data['asset_type'] = inferred_type
    else:
        data['asset_type'] = inferred_type if (provided_type == 'us' and inferred_type == 'fund') else provided_type
    
    success = db.add_asset(data, user_id)
    
    if success:
        _save_snapshot_for_user_async(user_id)
        return _idempotent_response('portfolio_add', user_id, request_id, {"status": "ok"})
    else:
        return _idempotent_response(
            'portfolio_add',
            user_id,
            request_id,
            {"error": "Failed to add asset", "code": "ASSET_ADD_FAILED"},
            500,
        )


@app.route('/api/portfolio/update', methods=['POST'])
@optional_auth
def update_asset():
    """更新资产"""
    data = request.json
    user_id = g.user_id
    request_id = str((data or {}).get('request_id', '')).strip()
    
    if not data or 'code' not in data or 'field' not in data or 'val' not in data:
        return jsonify({"error": "Missing required fields"}), 400

    dedup_hit, dedup_payload, dedup_status = _idempotency_begin('portfolio_update', user_id, request_id)
    if dedup_hit:
        return jsonify(dedup_payload), dedup_status
    
    try:
        val = float(data['val'])
        success = db.update_asset(data['code'], data['field'], val, user_id)
        
        if success:
            _save_snapshot_for_user_async(user_id)
            return _idempotent_response('portfolio_update', user_id, request_id, {"status": "ok"})
        else:
            return _idempotent_response(
                'portfolio_update',
                user_id,
                request_id,
                {"error": "Asset not found", "code": "ASSET_NOT_FOUND"},
                404,
            )
    except ValueError:
        return _idempotent_response(
            'portfolio_update',
            user_id,
            request_id,
            {"error": "Invalid value", "code": "INVALID_VALUE"},
            400,
        )


@app.route('/analysis')
def analysis():
    """旧分析页入口兼容跳转。"""
    if config.WEB_ENABLE_LEGACY_REDIRECT:
        return redirect('/app/analysis', code=302)
    return make_response(render_template('analysis.html', version=APP_VERSION))


@app.route('/news')
def news_page():
    """旧快讯页入口兼容跳转。"""
    if config.WEB_ENABLE_LEGACY_REDIRECT:
        return redirect('/app/news', code=302)
    return make_response(render_template('news.html', version=APP_VERSION))


@app.route('/settings')
def settings_page():
    """旧设置页入口兼容跳转。"""
    if config.WEB_ENABLE_LEGACY_REDIRECT:
        return redirect('/app/profile', code=302)
    return make_response(render_template('settings.html', version=APP_VERSION))


@app.route('/api/settings/info')
def get_system_info():
    """获取系统版本信息"""
    info = system_manager.get_version_info()
    return jsonify(info)


@app.route('/api/web/config')
def get_web_config():
    """公开 Web 门户配置（无需鉴权）。"""
    return jsonify(
        {
            "portal_title": config.WEB_PORTAL_TITLE,
            "apk_download_url": config.WEB_APK_DOWNLOAD_URL,
            "app_version": APP_VERSION,
        }
    )


@app.route('/api/settings/check_api')
def check_api_status():
    """检测API状态"""
    status = system_manager.check_api_status()
    return jsonify(status)


@app.route('/api/settings/backup')
def backup_database():
    """下载数据库备份"""
    if config.DATABASE_PATH.exists():
        return send_file(
            config.DATABASE_PATH,
            as_attachment=True,
            download_name=f"portfolio_backup_{int(time.time())}.db",
            mimetype='application/x-sqlite3'
        )
    return jsonify({"error": "Database not found"}), 404


@app.route('/api/settings/restore', methods=['POST'])
def restore_database():
    """恢复数据库"""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
        
    # 保存到临时文件
    temp_path = config.BASE_DIR / "temp_restore.db"
    try:
        file.save(temp_path)
        
        # 执行恢复
        success = system_manager.restore_database(str(temp_path))
        
        if success:
            return jsonify({"status": "ok", "message": "Restore successful"})
        else:
            return jsonify({"error": "Restore failed or invalid file"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # 清理临时文件
        if temp_path.exists():
            try:
                os.remove(temp_path)
            except:
                pass


@app.route('/api/news/latest')
def get_latest_news():
    """获取最新快讯 API"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 30, type=int)
    data = news_fetcher.fetch_latest(page=page, page_size=page_size)
    return jsonify({
        "items": data,
        "page": page,
        "page_size": page_size,
        "has_more": len(data) >= page_size
    })


@app.route('/api/history')
@optional_auth
def get_history():
    """获取历史资产数据"""
    days = request.args.get('days', 365, type=int)
    user_id = g.user_id
    history = db.get_history(days, user_id)
    return jsonify(history)


@app.route('/api/portfolio/modify', methods=['POST'])
@optional_auth
def modify_asset():
    """修正资产（数量、成本、调整值）"""
    data = request.json
    user_id = g.user_id
    request_id = str((data or {}).get('request_id', '')).strip()
    
    if not data or 'code' not in data or 'qty' not in data or 'price' not in data or 'adjustment' not in data:
        return jsonify({"error": "Missing required fields"}), 400

    dedup_hit, dedup_payload, dedup_status = _idempotency_begin('portfolio_modify', user_id, request_id)
    if dedup_hit:
        return jsonify(dedup_payload), dedup_status
    
    try:
        qty = float(data['qty'])
        price = float(data['price'])
        adjustment = float(data['adjustment'])
        detail = db.modify_asset(
            data['code'],
            qty,
            price,
            adjustment,
            user_id,
            return_detail=True,
        )
        if detail and detail.get('ok'):
            operation = {
                'op_type': 'modify',
                'code': data['code'],
                'before_asset': detail.get('before_asset'),
                'tx_id': None,
            }
            payload = _decorate_with_undo({"status": "ok"}, user_id, operation)
            _save_snapshot_for_user_async(user_id)
            return _idempotent_response('portfolio_modify', user_id, request_id, payload)

        error_code = (detail or {}).get('code', 'ASSET_NOT_FOUND')
        error_message = (detail or {}).get('error', 'Asset not found')
        status_code = 404 if error_code == 'ASSET_NOT_FOUND' else 500
        return _idempotent_response(
            'portfolio_modify',
            user_id,
            request_id,
            {"error": error_message, "code": error_code},
            status_code,
        )
    except ValueError:
        return _idempotent_response(
            'portfolio_modify',
            user_id,
            request_id,
            {"error": "Invalid value", "code": "INVALID_VALUE"},
            400,
        )


@app.route('/api/snapshot/save', methods=['POST'])
@optional_auth
def save_snapshot():
    """保存每日资产快照（前端触发）"""
    data = request.json
    user_id = g.user_id
    if not data:
        return jsonify({"error": "No data provided"}), 400
        
    success = db.save_daily_snapshot(data, user_id)
    if success:
        day_pnl_by_market = data.get("day_pnl_by_market")
        if isinstance(day_pnl_by_market, dict):
            snapshot_date = str(data.get("date") or "").strip() or datetime.now().strftime('%Y-%m-%d')
            source = str(data.get("market_breakdown_source") or "exact")
            confidence_raw = data.get("market_breakdown_confidence", 1.0)
            try:
                confidence = float(confidence_raw)
            except Exception:
                confidence = 1.0
            meta_by_market = data.get("market_breakdown_meta")
            if not isinstance(meta_by_market, dict):
                meta_by_market = None
            breakdown_ok = db.save_daily_snapshot_market_breakdown(
                date_str=snapshot_date,
                day_pnl_by_market=day_pnl_by_market,
                total_day_pnl=float(data.get("day_pnl", 0.0) or 0.0),
                user_id=user_id,
                source=source,
                confidence=confidence,
                meta_by_market=meta_by_market,
            )
            if not breakdown_ok:
                logger.warning(
                    "Failed to save market breakdown in /api/snapshot/save: user_id=%s date=%s",
                    user_id,
                    snapshot_date,
                )
        return jsonify({"status": "ok"})
    else:
        return jsonify({"error": "Failed to save snapshot"}), 500


@app.route('/api/snapshot/trigger', methods=['POST'])
@optional_auth
def trigger_snapshot():
    """手动触发后台快照计算"""
    user_id = g.user_id
    success = take_snapshot(user_id)
    if success:
        return jsonify({"status": "ok", "message": "Snapshot taken successfully"})
    else:
        return jsonify({"error": "Failed to take snapshot"}), 500


@app.route('/api/snapshot/fix', methods=['POST'])
@optional_auth
def fix_snapshot():
    """
    修复指定日期的 day_pnl 为 0（用于修正休市日错误记录的数据）
    
    请求体:
        {"dates": ["2026-01-17", "2026-01-18"]}
    """
    data = request.json
    user_id = g.user_id
    if not data or 'dates' not in data:
        return jsonify({"error": "Missing dates"}), 400
    
    dates = data['dates']
    if not isinstance(dates, list):
        return jsonify({"error": "dates must be a list"}), 400
    
    success = db.fix_snapshot_day_pnl(dates, user_id)
    if success:
        return jsonify({"status": "ok", "message": f"Fixed {len(dates)} records"})
    else:
        return jsonify({"error": "Failed to fix snapshots"}), 500


@app.route('/api/portfolio/delete', methods=['POST'])
@optional_auth
def delete_asset():
    """删除资产"""
    data = request.json
    user_id = g.user_id
    request_id = str((data or {}).get('request_id', '')).strip()
    
    if not data or 'code' not in data:
        return jsonify({"error": "Missing code"}), 400

    dedup_hit, dedup_payload, dedup_status = _idempotency_begin('portfolio_delete', user_id, request_id)
    if dedup_hit:
        return jsonify(dedup_payload), dedup_status
    
    success = db.delete_asset(data['code'], user_id)
    
    if success:
        _save_snapshot_for_user_async(user_id)
        return _idempotent_response('portfolio_delete', user_id, request_id, {"status": "ok"})
    else:
        return _idempotent_response(
            'portfolio_delete',
            user_id,
            request_id,
            {"error": "Failed to delete asset", "code": "ASSET_DELETE_FAILED"},
            500,
        )


@app.route('/api/portfolio/delete_corrective', methods=['POST'])
@optional_auth
def delete_asset_corrective():
    """删除资产并清理历史交易和快照污染"""
    data = request.json
    user_id = g.user_id
    request_id = str((data or {}).get('request_id', '')).strip()

    if not data or 'code' not in data:
        return jsonify({"error": "Missing code"}), 400

    dedup_hit, dedup_payload, dedup_status = _idempotency_begin('portfolio_delete_corrective', user_id, request_id)
    if dedup_hit:
        return jsonify(dedup_payload), dedup_status

    result = db.delete_asset_corrective(data['code'], user_id)
    if result:
        _save_snapshot_for_user_async(user_id)
        payload = {
            "status": "ok",
            "code": "CORRECTIVE_DELETE_DONE",
            "deleted": {
                "portfolio": result.get('portfolio', 0),
                "transactions": result.get('transactions', 0),
                "snapshots": result.get('snapshots', 0),
            },
            "from_date": result.get('from_date'),
        }
        return _idempotent_response('portfolio_delete_corrective', user_id, request_id, payload)
    return _idempotent_response(
        'portfolio_delete_corrective',
        user_id,
        request_id,
        {"error": "Failed to delete asset corrective", "code": "ASSET_CORRECTIVE_DELETE_FAILED"},
        500,
    )


@app.route('/api/portfolio/buy', methods=['POST'])
@optional_auth
def buy_asset():
    """加仓"""
    data = request.json
    user_id = g.user_id
    request_id = str((data or {}).get('request_id', '')).strip()
    
    if not data or 'code' not in data or 'price' not in data or 'qty' not in data:
        return jsonify({"error": "Missing required fields"}), 400

    dedup_hit, dedup_payload, dedup_status = _idempotency_begin('portfolio_buy', user_id, request_id)
    if dedup_hit:
        return jsonify(dedup_payload), dedup_status
    
    try:
        price = float(data['price'])
        qty = float(data['qty'])
        detail = db.buy_asset(data['code'], price, qty, user_id, return_detail=True)

        if detail and detail.get('ok'):
            operation = {
                'op_type': 'buy',
                'code': data['code'],
                'before_asset': detail.get('before_asset'),
                'tx_id': detail.get('tx_id'),
            }
            payload = _decorate_with_undo({"status": "ok"}, user_id, operation)
            _save_snapshot_for_user_async(user_id)
            return _idempotent_response('portfolio_buy', user_id, request_id, payload)

        error_code = (detail or {}).get('code', 'ASSET_BUY_FAILED')
        error_message = (detail or {}).get('error', 'Failed to buy asset')
        status_code = 404 if error_code == 'ASSET_NOT_FOUND' else 500
        return _idempotent_response(
            'portfolio_buy',
            user_id,
            request_id,
            {"error": error_message, "code": error_code},
            status_code,
        )
    except ValueError:
        return _idempotent_response(
            'portfolio_buy',
            user_id,
            request_id,
            {"error": "Invalid value", "code": "INVALID_VALUE"},
            400,
        )


@app.route('/api/portfolio/buy_with_cash', methods=['POST'])
@optional_auth
def buy_asset_with_cash():
    """从指定现金账户买入（同一事务扣现金+加持仓）"""
    data = request.json
    user_id = g.user_id
    request_id = str((data or {}).get('request_id', '')).strip()

    required = ('code', 'price', 'qty', 'cash_asset_id')
    if not data or any(field not in data for field in required):
        return jsonify({"error": "Missing required fields"}), 400

    dedup_hit, dedup_payload, dedup_status = _idempotency_begin('portfolio_buy_with_cash', user_id, request_id)
    if dedup_hit:
        return jsonify(dedup_payload), dedup_status

    try:
        price = float(data['price'])
        qty = float(data['qty'])
        cash_asset_id = int(data['cash_asset_id'])
    except (TypeError, ValueError):
        return _idempotent_response(
            'portfolio_buy_with_cash',
            user_id,
            request_id,
            {"error": "Invalid value", "code": "INVALID_VALUE"},
            400,
        )

    if price <= 0 or qty <= 0:
        return _idempotent_response(
            'portfolio_buy_with_cash',
            user_id,
            request_id,
            {"error": "Invalid value", "code": "INVALID_VALUE"},
            400,
        )

    parsed = parse_code(data['code'], data.get('curr', ''))
    code = parsed['code']
    curr = parsed['curr']
    name = data.get('name', code)
    provided_type = str(data.get('asset_type', '') or '').strip()
    inferred_type = infer_asset_type(code, name)
    asset_type = inferred_type if (provided_type == 'us' and inferred_type == 'fund') else (provided_type or inferred_type)

    cash_asset = db.get_cash_asset_by_id(cash_asset_id, user_id)
    if not cash_asset:
        return _idempotent_response(
            'portfolio_buy_with_cash',
            user_id,
            request_id,
            {"error": "Cash account not found", "code": "CASH_ASSET_NOT_FOUND"},
            404,
        )

    invest_amount = price * qty
    cash_curr = cash_asset.get('curr', 'CNY')
    if str(curr).upper() == str(cash_curr).upper():
        cash_deduct_amount = invest_amount
    else:
        rates = get_forex_rates()
        cash_deduct_amount = _convert_amount(invest_amount, curr, cash_curr, rates)
    if cash_deduct_amount <= 0:
        return _idempotent_response(
            'portfolio_buy_with_cash',
            user_id,
            request_id,
            {"error": "Invalid cash deduction amount", "code": "INVALID_CASH_AMOUNT"},
            400,
        )

    detail = db.buy_asset_with_cash(
        code=code,
        name=name,
        price=price,
        qty=qty,
        curr=curr,
        asset_type=asset_type,
        cash_asset_id=cash_asset_id,
        cash_deduct_amount=cash_deduct_amount,
        user_id=user_id,
    )
    if detail and detail.get('ok'):
        operation = {
            'op_type': 'buy_with_cash',
            'code': code,
            'before_asset': detail.get('before_asset'),
            'tx_id': detail.get('tx_id'),
            'cash_asset_id': detail.get('cash_asset_id'),
            'cash_before_amount': detail.get('cash_before_amount'),
        }
        payload = _decorate_with_undo(
            {
                "status": "ok",
                "cash_deducted": detail.get('cash_deduct_amount'),
                "cash_curr": detail.get('cash_curr'),
            },
            user_id,
            operation,
        )
        _save_snapshot_for_user_async(user_id)
        return _idempotent_response('portfolio_buy_with_cash', user_id, request_id, payload)

    error_code = (detail or {}).get('code', 'ASSET_BUY_WITH_CASH_FAILED')
    error_message = (detail or {}).get('error', 'Failed to buy asset with cash')
    status_code = 500
    if error_code in ('INVALID_VALUE', 'INVALID_CASH_AMOUNT'):
        status_code = 400
    elif error_code == 'INSUFFICIENT_CASH':
        status_code = 400
    elif error_code == 'CASH_ASSET_NOT_FOUND':
        status_code = 404
    payload = {"error": error_message, "code": error_code}
    if detail and 'available' in detail:
        payload['available'] = detail.get('available')
    if detail and 'required' in detail:
        payload['required'] = detail.get('required')
    if detail and 'cash_curr' in detail:
        payload['cash_curr'] = detail.get('cash_curr')
    return _idempotent_response(
        'portfolio_buy_with_cash',
        user_id,
        request_id,
        payload,
        status_code,
    )


@app.route('/api/portfolio/sell', methods=['POST'])
@optional_auth
def sell_asset():
    """减仓"""
    data = request.json
    user_id = g.user_id
    request_id = str((data or {}).get('request_id', '')).strip()
    
    if not data or 'code' not in data or 'price' not in data or 'qty' not in data:
        return jsonify({"error": "Missing required fields"}), 400

    dedup_hit, dedup_payload, dedup_status = _idempotency_begin('portfolio_sell', user_id, request_id)
    if dedup_hit:
        return jsonify(dedup_payload), dedup_status
    
    try:
        price = float(data['price'])
        qty = float(data['qty'])
        detail = db.sell_asset(data['code'], price, qty, user_id, return_detail=True)

        if detail and detail.get('ok'):
            operation = {
                'op_type': 'sell',
                'code': data['code'],
                'before_asset': detail.get('before_asset'),
                'tx_id': detail.get('tx_id'),
            }
            payload = _decorate_with_undo({"status": "ok"}, user_id, operation)
            _save_snapshot_for_user_async(user_id)
            return _idempotent_response('portfolio_sell', user_id, request_id, payload)

        error_code = (detail or {}).get('code', 'ASSET_SELL_FAILED')
        error_message = (detail or {}).get('error', 'Failed to sell asset')
        if error_code in ('OVERSELL', 'INVALID_VALUE'):
            status_code = 400
        elif error_code == 'ASSET_NOT_FOUND':
            status_code = 404
        else:
            status_code = 500
        return _idempotent_response(
            'portfolio_sell',
            user_id,
            request_id,
            {"error": error_message, "code": error_code},
            status_code,
        )
    except ValueError:
        return _idempotent_response(
            'portfolio_sell',
            user_id,
            request_id,
            {"error": "Invalid value", "code": "INVALID_VALUE"},
            400,
        )


@app.route('/api/portfolio/undo', methods=['POST'])
@optional_auth
def undo_portfolio_operation():
    """撤销最近投资操作（限时）"""
    data = request.json
    user_id = g.user_id
    undo_token = str((data or {}).get('undo_token', '')).strip()
    operation, error_info = _claim_undo_record(user_id, undo_token)
    if error_info:
        code, message, status_code = error_info
        return jsonify({"error": message, "code": code}), status_code

    result = db.undo_invest_operation(operation, user_id)
    if result and result.get('ok'):
        _save_snapshot_for_user_async(user_id)
        return jsonify({"status": "ok", "code": "UNDO_DONE"})

    _release_undo_claim(user_id, undo_token)
    return jsonify({
        "error": (result or {}).get('error', 'Failed to undo operation'),
        "code": (result or {}).get('code', 'UNDO_FAILED'),
    }), 500


@app.route('/api/transactions', methods=['GET'])
@optional_auth
def get_transactions():
    """获取交易记录"""
    limit = request.args.get('limit', 100, type=int)
    user_id = g.user_id
    data = db.get_transactions(limit, user_id)
    return jsonify(data)


@app.route('/api/search')
def search():
    """搜索股票"""
    query = request.args.get('q', '')
    results = search_stocks(query)
    return jsonify(results)

@app.route('/api/cash_assets', methods=['GET'])
@optional_auth
def get_cash_assets():
    """获取现金资产"""
    user_id = g.user_id
    data = db.get_cash_assets(user_id)
    return jsonify(data)

@app.route('/api/cash_assets/add', methods=['POST'])
@optional_auth
def add_cash_asset():
    """添加现金资产"""
    user_id = g.user_id
    return _handle_asset_add(db.add_cash_asset, "cash asset", user_id)

@app.route('/api/cash_assets/delete', methods=['POST'])
@optional_auth
def delete_cash_asset():
    """删除现金资产"""
    user_id = g.user_id
    return _handle_asset_delete(db.delete_cash_asset, "cash asset", user_id)

@app.route('/api/cash_assets/update', methods=['POST'])
@optional_auth
def update_cash_asset():
    """更新现金资产"""
    user_id = g.user_id
    return _handle_asset_update(db.update_cash_asset, "cash asset", user_id)

@app.route('/api/other_assets', methods=['GET'])
@optional_auth
def get_other_assets():
    """获取其他资产"""
    user_id = g.user_id
    data = db.get_other_assets(user_id)
    return jsonify(data)

@app.route('/api/other_assets/add', methods=['POST'])
@optional_auth
def add_other_asset():
    """添加其他资产"""
    user_id = g.user_id
    return _handle_asset_add(db.add_other_asset, "other asset", user_id)

@app.route('/api/other_assets/delete', methods=['POST'])
@optional_auth
def delete_other_asset():
    """删除其他资产"""
    user_id = g.user_id
    return _handle_asset_delete(db.delete_other_asset, "other asset", user_id)

@app.route('/api/other_assets/update', methods=['POST'])
@optional_auth
def update_other_asset():
    """更新其他资产"""
    user_id = g.user_id
    return _handle_asset_update(db.update_other_asset, "other asset", user_id)

@app.route('/api/liabilities', methods=['GET'])
@optional_auth
def get_liabilities():
    """获取负债"""
    user_id = g.user_id
    data = db.get_liabilities(user_id)
    return jsonify(data)

@app.route('/api/liabilities/add', methods=['POST'])
@optional_auth
def add_liability():
    """添加负债"""
    user_id = g.user_id
    return _handle_asset_add(db.add_liability, "liability", user_id)

@app.route('/api/liabilities/delete', methods=['POST'])
@optional_auth
def delete_liability():
    """删除负债"""
    user_id = g.user_id
    return _handle_asset_delete(db.delete_liability, "liability", user_id)

@app.route('/api/liabilities/update', methods=['POST'])
@optional_auth
def update_liability():
    """更新负债"""
    user_id = g.user_id
    return _handle_asset_update(db.update_liability, "liability", user_id)


def _save_snapshot_for_user(user_id=None):
    """保存用户当日快照（更实时）"""
    try:
        stats = calculate_portfolio_stats(user_id)
        saved = db.save_daily_snapshot(stats, user_id)
        if saved:
            snapshot_date = str(stats.get("snapshot_date") or datetime.now().strftime('%Y-%m-%d'))
            breakdown_ok = db.save_daily_snapshot_market_breakdown(
                date_str=snapshot_date,
                day_pnl_by_market=stats.get("day_pnl_by_market") or {},
                total_day_pnl=float(stats.get("day_pnl", 0.0) or 0.0),
                user_id=user_id,
                source="exact",
                confidence=1.0,
            )
            if not breakdown_ok:
                logger.warning("Snapshot market breakdown save failed: user_id=%s date=%s", user_id, snapshot_date)
    except Exception as e:
        logger.warning(f"Snapshot save failed: {e}")


def _save_snapshot_for_user_async(user_id=None):
    """异步保存用户快照，避免阻塞资产接口响应。"""
    uid = user_id or ''
    now = time.time()
    with _snapshot_lock:
        last_run = _snapshot_last_run_ts.get(uid, 0.0)
        if uid in _snapshot_inflight:
            logger.info("[snapshot_skip_inflight] user_id=%s", uid)
            return
        if now - last_run < _SNAPSHOT_MIN_INTERVAL_SECONDS:
            logger.info("[snapshot_skip_throttle] user_id=%s interval=%.2fs", uid, now - last_run)
            return
        _snapshot_inflight.add(uid)

    def _worker():
        try:
            _save_snapshot_for_user(user_id if uid else None)
        finally:
            with _snapshot_lock:
                _snapshot_inflight.discard(uid)
                _snapshot_last_run_ts[uid] = time.time()

    threading.Thread(target=_worker, daemon=True).start()


def _handle_asset_add(add_func, asset_type, user_id=None):
    """处理资产添加的通用函数"""
    data = request.json
    
    if not data or 'name' not in data or 'amount' not in data:
        logger.warning(
            "[asset_add_invalid_request] type=%s user_id=%s reason=missing_required_fields payload=%s",
            asset_type,
            user_id,
            data,
        )
        return jsonify({"error": "Missing required fields", "code": "MISSING_REQUIRED_FIELDS"}), 400
    
    try:
        logger.info(
            "[asset_add_request] type=%s user_id=%s name=%s amount=%s curr=%s",
            asset_type,
            user_id,
            data.get('name'),
            data.get('amount'),
            data.get('curr', 'CNY'),
        )
        amount = float(data['amount'])
        if amount <= 0:
            logger.warning(
                "[asset_add_invalid_amount] type=%s user_id=%s amount=%s",
                asset_type,
                user_id,
                data.get('amount'),
            )
            return jsonify({"error": "Invalid amount", "code": "INVALID_AMOUNT"}), 400
        success = add_func(data['name'], amount, data.get('curr', 'CNY'), user_id)
        if success:
            _save_snapshot_for_user_async(user_id)
            logger.info("[asset_add_success] type=%s user_id=%s", asset_type, user_id)
            return jsonify({"status": "ok"})
        logger.error("[asset_add_failed] type=%s user_id=%s", asset_type, user_id)
        return jsonify({"error": f"Failed to add {asset_type}", "code": "ASSET_ADD_FAILED"}), 500
    except ValueError:
        logger.warning(
            "[asset_add_invalid_amount] type=%s user_id=%s amount=%s",
            asset_type,
            user_id,
            data.get('amount'),
        )
        return jsonify({"error": "Invalid amount", "code": "INVALID_AMOUNT"}), 400
    except Exception as e:
        logger.exception(
            "[asset_add_exception] type=%s user_id=%s error=%s",
            asset_type,
            user_id,
            e,
        )
        return jsonify({"error": f"Failed to add {asset_type}", "code": "ASSET_ADD_EXCEPTION"}), 500


def _handle_asset_delete(delete_func, asset_type, user_id=None):
    """处理资产删除的通用函数"""
    data = request.json
    
    if not data or 'id' not in data:
        logger.warning(
            "[asset_delete_invalid_request] type=%s user_id=%s reason=missing_id payload=%s",
            asset_type,
            user_id,
            data,
        )
        return jsonify({"error": "Missing id", "code": "MISSING_ID"}), 400
    
    try:
        asset_id = int(data['id'])
        logger.info(
            "[asset_delete_request] type=%s user_id=%s id=%s",
            asset_type,
            user_id,
            asset_id,
        )
        success = delete_func(asset_id, user_id)
        if success:
            _save_snapshot_for_user_async(user_id)
            logger.info(
                "[asset_delete_success] type=%s user_id=%s id=%s",
                asset_type,
                user_id,
                asset_id,
            )
            return jsonify({"status": "ok"})
        logger.error(
            "[asset_delete_failed] type=%s user_id=%s id=%s",
            asset_type,
            user_id,
            asset_id,
        )
        return jsonify({"error": f"Failed to delete {asset_type}", "code": "ASSET_DELETE_FAILED"}), 500
    except ValueError:
        logger.warning(
            "[asset_delete_invalid_id] type=%s user_id=%s id=%s",
            asset_type,
            user_id,
            data.get('id'),
        )
        return jsonify({"error": "Invalid id", "code": "INVALID_ID"}), 400
    except Exception as e:
        logger.exception(
            "[asset_delete_exception] type=%s user_id=%s error=%s",
            asset_type,
            user_id,
            e,
        )
        return jsonify({"error": f"Failed to delete {asset_type}", "code": "ASSET_DELETE_EXCEPTION"}), 500


def _handle_asset_update(update_func, asset_type, user_id=None):
    """处理资产更新的通用函数"""
    data = request.json
    
    if not data or 'id' not in data or 'name' not in data or 'amount' not in data:
        logger.warning(
            "[asset_update_invalid_request] type=%s user_id=%s reason=missing_required_fields payload=%s",
            asset_type,
            user_id,
            data,
        )
        return jsonify({"error": "Missing required fields", "code": "MISSING_REQUIRED_FIELDS"}), 400
    
    try:
        asset_id = int(data['id'])
        amount = float(data['amount'])
        if amount <= 0:
            logger.warning(
                "[asset_update_invalid_amount] type=%s user_id=%s id=%s amount=%s",
                asset_type,
                user_id,
                data.get('id'),
                data.get('amount'),
            )
            return jsonify({"error": "Invalid amount", "code": "INVALID_VALUE"}), 400
        logger.info(
            "[asset_update_request] type=%s user_id=%s id=%s name=%s amount=%s curr=%s",
            asset_type,
            user_id,
            asset_id,
            data.get('name'),
            amount,
            data.get('curr', 'CNY'),
        )
        success = update_func(asset_id, data['name'], amount, data.get('curr', 'CNY'), user_id)
        if success:
            _save_snapshot_for_user_async(user_id)
            logger.info(
                "[asset_update_success] type=%s user_id=%s id=%s",
                asset_type,
                user_id,
                asset_id,
            )
            return jsonify({"status": "ok"})
        logger.error(
            "[asset_update_failed] type=%s user_id=%s id=%s",
            asset_type,
            user_id,
            asset_id,
        )
        return jsonify({"error": f"Failed to update {asset_type}", "code": "ASSET_UPDATE_FAILED"}), 500
    except ValueError:
        logger.warning(
            "[asset_update_invalid_value] type=%s user_id=%s id=%s amount=%s",
            asset_type,
            user_id,
            data.get('id'),
            data.get('amount'),
        )
        return jsonify({"error": "Invalid value", "code": "INVALID_VALUE"}), 400
    except Exception as e:
        logger.exception(
            "[asset_update_exception] type=%s user_id=%s error=%s",
            asset_type,
            user_id,
            e,
        )
        return jsonify({"error": f"Failed to update {asset_type}", "code": "ASSET_UPDATE_EXCEPTION"}), 500


# ============================================================
# 认证 API
# ============================================================

@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("20 per 10 minute")
@limiter.limit("8 per 10 minute", key_func=_username_limit_key)
def auth_login():
    data = request.get_json(silent=True)
    if not data:
        _auth_audit(event='auth_login', outcome='failed', reason='missing_payload', level='warning')
        return jsonify({"error": "Missing payload"}), 400

    username = normalize_username(data.get("username", ""))
    password = str(data.get("password", ""))
    device_id = str(data.get("device_id", "")).strip()[:128]
    if not username or not password:
        _auth_audit(event='auth_login', outcome='failed', username=username, reason='missing_credentials', level='warning')
        return jsonify({"error": "Missing username or password"}), 400

    user = db.get_user_by_username(username)
    if not user:
        _auth_audit(event='auth_login', outcome='failed', username=username, reason='user_not_found', level='warning')
        return jsonify({"error": "Invalid username or password"}), 401
    if str(user.get("status") or "active").lower() != "active":
        _auth_audit(event='auth_login', outcome='failed', username=username, reason='user_disabled', level='warning')
        return jsonify({"error": "User is disabled"}), 403
    if user.get("legacy_needs_password_setup") or not user.get("password_hash"):
        _auth_audit(event='auth_login', outcome='failed', username=username, reason='password_not_setup', level='warning')
        return jsonify({"error": "Password not set. Please bootstrap credentials."}), 403
    if not verify_password(password, str(user.get("password_hash") or "")):
        _auth_audit(event='auth_login', outcome='failed', username=username, reason='bad_password', level='warning')
        return jsonify({"error": "Invalid username or password"}), 401

    db.update_last_login(user["id"])
    tokens = _issue_auth_tokens(user["id"], username, device_id=device_id)
    profile = get_user_profile(db, user["id"]) or {}
    _auth_audit(event='auth_login', outcome='success', username=username, reason=f"user_id={user['id']}")
    return jsonify({
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "refresh_expires_at": tokens["refresh_expires_at"],
        "user": profile,
    })


@app.route('/api/auth/register', methods=['POST'])
@limiter.limit("10 per 10 minute")
@limiter.limit("5 per 10 minute", key_func=_username_limit_key)
def auth_register():
    data = request.get_json(silent=True) or {}
    username = normalize_username(data.get("username", ""))
    password = str(data.get("password", ""))
    invite_code = str(data.get("invite_code", "")).strip().upper()
    device_id = str(data.get("device_id", "")).strip()[:128]

    if not is_valid_username(username):
        _auth_audit(event='auth_register', outcome='failed', username=username, reason='invalid_username', level='warning')
        return jsonify({"error": "Invalid username"}), 400
    ok, msg = validate_password(password)
    if not ok:
        _auth_audit(event='auth_register', outcome='failed', username=username, reason='weak_password', level='warning')
        return jsonify({"error": msg}), 400
    if not invite_code:
        _auth_audit(event='auth_register', outcome='failed', username=username, reason='missing_invite', level='warning')
        return jsonify({"error": "Missing invite code"}), 400
    if db.get_user_by_username(username):
        _auth_audit(event='auth_register', outcome='failed', username=username, reason='username_exists', level='warning')
        return jsonify({"error": "Username already exists"}), 409
    invite = db.get_invite_code(invite_code)
    if not invite or invite.get("status") != "active" or invite.get("used_by_user_id"):
        _auth_audit(event='auth_register', outcome='failed', username=username, reason='invalid_invite', level='warning')
        return jsonify({"error": "Invite code invalid or already used"}), 400

    conn = db.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(1) AS c FROM users WHERE COALESCE(password_hash, '') != ''")
        pwd_user_count = int(cursor.fetchone()["c"] or 0)
    finally:
        conn.close()
    is_first_password_user = pwd_user_count == 0

    user_id = secrets.token_hex(16)
    password_h = hash_password(password)
    try:
        created = db.create_user(
            username=username,
            password_hash=password_h,
            register_method="password_invite",
            is_admin=is_first_password_user,
            user_id=user_id,
        )
    except Exception:
        _auth_audit(event='auth_register', outcome='failed', username=username, reason='create_user_failed', level='warning')
        return jsonify({"error": "Registration failed"}), 500

    consumed, reason = db.consume_invite_code(invite_code, created["id"])
    if not consumed:
        db.delete_user(created["id"])
        _auth_audit(event='auth_register', outcome='failed', username=username, reason='consume_invite_failed', level='warning')
        return jsonify({"error": reason or "Invite code invalid or already used"}), 400

    db.update_last_login(created["id"])
    tokens = _issue_auth_tokens(created["id"], username, device_id=device_id)
    profile = get_user_profile(db, created["id"]) or {}
    _auth_audit(event='auth_register', outcome='success', username=username, reason=f"user_id={created['id']}")
    return jsonify({
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "refresh_expires_at": tokens["refresh_expires_at"],
        "user": profile,
    })


@app.route('/api/auth/invite/validate', methods=['POST'])
@limiter.limit("30 per 10 minute")
def auth_validate_invite():
    data = request.get_json(silent=True) or {}
    invite_code = str(data.get("invite_code", "")).strip().upper()
    if not re.match(r"^[A-Z0-9]{8,16}$", invite_code):
        return jsonify({"valid": False, "error": "Invalid invite code format"}), 400
    invite = db.get_invite_code(invite_code)
    if not invite or invite.get("status") != "active" or invite.get("used_by_user_id"):
        return jsonify({"valid": False, "error": "Invite code invalid or already used"}), 404
    return jsonify({"valid": True, "code": invite_code, "batch_id": invite.get("batch_id")})


@app.route('/api/auth/me', methods=['GET'])
@login_required
def auth_me():
    """获取当前登录用户信息"""
    profile = get_user_profile(db, g.user_id)
    if profile:
        return jsonify(profile)
    return jsonify({
        "user_id": g.user_id,
        "username": g.username
    })


@app.route('/api/auth/profile', methods=['POST'])
@login_required
@limiter.limit("30 per 10 minute")
def update_profile():
    """更新用户资料（昵称/头像）"""
    data = request.json or {}
    nickname = data.get('nickname')
    avatar = data.get('avatar')

    if nickname is None and avatar is None:
        _auth_audit(event='auth_profile_update', outcome='failed', username=g.username, reason='no_fields', level='warning')
        return jsonify({"error": "No fields to update"}), 400

    if isinstance(nickname, str):
        nickname = nickname.strip()

    # 简单大小限制，避免超大头像
    if isinstance(avatar, str) and len(avatar) > 1_500_000:
        _auth_audit(event='auth_profile_update', outcome='failed', username=g.username, reason='avatar_too_large', level='warning')
        return jsonify({"error": "Avatar too large"}), 400

    ok = db.update_user_profile(g.user_id, nickname=nickname, avatar=avatar)
    if not ok:
        _auth_audit(event='auth_profile_update', outcome='failed', username=g.username, reason='db_update_failed', level='warning')
        return jsonify({"error": "Update failed"}), 500
    _auth_audit(event='auth_profile_update', outcome='success', username=g.username, reason=f'user_id={g.user_id}')

    profile = get_user_profile(db, g.user_id) or {}
    return jsonify(profile)


@app.route('/api/auth/bootstrap_credentials', methods=['POST'])
@login_required
@limiter.limit("8 per 10 minute")
def auth_bootstrap_credentials():
    data = request.get_json(silent=True) or {}
    username = normalize_username(data.get("username", ""))
    new_password = str(data.get("password", ""))
    if not is_valid_username(username):
        _auth_audit(event='auth_bootstrap', outcome='failed', username=username, reason='invalid_username', level='warning')
        return jsonify({"error": "Invalid username"}), 400
    ok, msg = validate_password(new_password)
    if not ok:
        _auth_audit(event='auth_bootstrap', outcome='failed', username=username, reason='weak_password', level='warning')
        return jsonify({"error": msg}), 400
    success, reason = db.bootstrap_credentials(g.user_id, username, hash_password(new_password))
    if not success:
        _auth_audit(event='auth_bootstrap', outcome='failed', username=username, reason=reason or 'bootstrap_failed', level='warning')
        return jsonify({"error": reason or "Bootstrap failed"}), 400
    db.revoke_all_refresh_tokens(g.user_id)
    db.update_last_login(g.user_id)
    tokens = _issue_auth_tokens(g.user_id, username)
    profile = get_user_profile(db, g.user_id) or {}
    _auth_audit(event='auth_bootstrap', outcome='success', username=username, reason=f'user_id={g.user_id}')
    return jsonify({
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "refresh_expires_at": tokens["refresh_expires_at"],
        "user": profile,
    })


@app.route('/api/auth/password/change', methods=['POST'])
@login_required
@limiter.limit("10 per 10 minute")
def auth_change_password():
    data = request.get_json(silent=True) or {}
    old_password = str(data.get("old_password", ""))
    new_password = str(data.get("new_password", ""))
    if not old_password or not new_password:
        return jsonify({"error": "Missing old_password or new_password"}), 400
    ok, msg = validate_password(new_password)
    if not ok:
        return jsonify({"error": msg}), 400
    user = db.get_user_by_id(g.user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    if not verify_password(old_password, str(user.get("password_hash") or "")):
        _auth_audit(event='auth_password_change', outcome='failed', username=user.get("username") or g.username, reason='bad_old_password', level='warning')
        return jsonify({"error": "Old password is incorrect"}), 400
    if not db.set_user_password(g.user_id, hash_password(new_password)):
        return jsonify({"error": "Failed to update password"}), 500
    revoked = db.revoke_all_refresh_tokens(g.user_id)
    _auth_audit(event='auth_password_change', outcome='success', username=user.get("username") or g.username, reason=f'revoked={revoked}')
    return jsonify({"status": "ok", "revoked_refresh_tokens": revoked})


@app.route('/api/auth/refresh', methods=['POST'])
@limiter.limit("20 per 10 minute")
def auth_refresh():
    data = request.get_json(silent=True) or {}
    refresh_token = str(data.get("refresh_token", "")).strip()
    device_id = str(data.get("device_id", "")).strip()[:128]
    if not refresh_token:
        return jsonify({"error": "Missing refresh_token"}), 400
    token_hash = hash_refresh_token(refresh_token)
    token_row = db.get_refresh_token(token_hash)
    if not _is_refresh_token_valid(token_row):
        _auth_audit(event='auth_refresh', outcome='failed', reason='invalid_refresh_token', level='warning')
        return jsonify({"error": "Invalid refresh token"}), 401
    user = db.get_user_by_id(token_row.get("user_id"))
    if not user or str(user.get("status") or "active").lower() != "active":
        _auth_audit(event='auth_refresh', outcome='failed', reason='user_disabled_or_missing', level='warning')
        return jsonify({"error": "User not available"}), 403
    db.revoke_refresh_token(token_hash)
    db.touch_refresh_token(token_hash)
    tokens = _issue_auth_tokens(user["id"], user["username"], device_id=device_id or (token_row.get("device_id") or ""))
    db.update_last_login(user["id"])
    _auth_audit(event='auth_refresh', outcome='success', username=user["username"], reason=f'user_id={user["id"]}')
    return jsonify({
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "refresh_expires_at": tokens["refresh_expires_at"],
        "user": get_user_profile(db, user["id"]) or {},
    })


@app.route('/api/auth/logout', methods=['POST'])
@login_required
def auth_logout():
    data = request.get_json(silent=True) or {}
    refresh_token = str(data.get("refresh_token", "")).strip()
    revoked = 0
    if refresh_token:
        if db.revoke_refresh_token(hash_refresh_token(refresh_token)):
            revoked = 1
    else:
        revoked = db.revoke_all_refresh_tokens(g.user_id)
    _auth_audit(event='auth_logout', outcome='success', username=g.username, reason=f'revoked={revoked}')
    return jsonify({"status": "ok", "revoked_refresh_tokens": revoked})


@app.route('/api/auth/send_code', methods=['POST'])
def auth_send_code():
    """Deprecated: email verification login has been removed."""
    return jsonify({"error": "Deprecated endpoint", "code": "AUTH_EMAIL_OTP_REMOVED"}), 410


@app.route('/health')
def health():
    """健康检查"""
    return jsonify({"status": "ok", "version": config.APP_VERSION})


@app.route('/api/market/status')
def api_market_status():
    """主流市场开休市状态。"""
    now_utc = datetime.now(timezone.utc)
    markets = get_market_statuses(_MARKET_SCOPE, now=now_utc)
    return jsonify(
        {
            "server_time_utc": now_utc.isoformat(),
            "markets": markets,
            "all_closed": all_markets_closed(_MARKET_SCOPE, now=now_utc),
        }
    )


@app.route('/api/sync/bootstrap', methods=['POST'])
@optional_auth
def api_sync_bootstrap():
    """
    客户端增量同步引导接口。

    请求体:
    {
      "client_versions": {"portfolio":"...", ...},
      "include": ["portfolio", "cash_assets", ...]
    }
    """
    body = request.get_json(silent=True) or {}
    include = _normalize_sync_include(body.get("include"))
    client_versions_raw = body.get("client_versions")
    client_versions = client_versions_raw if isinstance(client_versions_raw, dict) else {}

    user_id = g.user_id
    now_utc = datetime.now(timezone.utc)
    rates = get_forex_rates()

    versions = db.get_sync_versions(user_id=user_id)
    versions["rates"] = _sync_rates_version(rates)

    changed: list[str] = []
    data: Dict[str, Any] = {}
    for domain in include:
        client_v = str(client_versions.get(domain, "") or "")
        server_v = str(versions.get(domain, "") or "")
        if client_v == server_v:
            continue
        changed.append(domain)
        if domain == "rates":
            data[domain] = rates
        else:
            data[domain] = _build_sync_domain_data(domain, user_id=user_id)

    markets = get_market_statuses(_MARKET_SCOPE, now=now_utc)
    return jsonify(
        {
            "server_time": now_utc.isoformat(),
            "versions": {k: versions[k] for k in _SYNC_BOOTSTRAP_DOMAINS},
            "changed": changed,
            "data": data,
            "market_statuses": markets,
            "market_status": {k: bool((markets.get(k) or {}).get("open")) for k in _MARKET_SCOPE},
            "quote_policy": dict(_QUOTE_POLICY_DEFAULT),
        }
    )


@app.route('/api/system/price_health')
def api_price_health():
    """行情运行健康指标。"""
    if not _metrics_token_ok():
        _auth_audit(
            event='metrics_access',
            outcome='blocked',
            reason='invalid_or_missing_token',
            level='warning',
        )
        return jsonify({"error": "Unauthorized"}), 401

    return jsonify({
        "status": "ok",
        "version": config.APP_VERSION,
        "server_time_utc": datetime.now(timezone.utc).isoformat(),
        "runtime": get_price_runtime_metrics(),
        "sources": get_price_source_health(),
    })


# ============================================================
# 分析 API
# ============================================================

@app.route('/api/analysis/overview')
@optional_auth
def analysis_overview():
    """
    盈亏概览
    
    参数:
        period: day|month|year|all (默认 all)
    
    返回:
        {day: {pnl, pnl_rate}, month: {...}, year: {...}, all: {...}}
    """
    period = request.args.get('period', 'all')
    user_id = g.user_id

    if period == 'all':
        # 返回所有周期的数据
        result = {
            'day': db.get_pnl_overview('day', user_id),
            'month': db.get_pnl_overview('month', user_id),
            'year': db.get_pnl_overview('year', user_id),
            'all': db.get_pnl_overview('all', user_id)
        }
    else:
        # 返回指定周期的数据
        result = {period: db.get_pnl_overview(period, user_id)}

    return jsonify(result)


@app.route('/api/analysis/calendar')
@optional_auth
def analysis_calendar():
    """
    收益日历
    
    参数:
        type: day|month|year (默认 day)
    
    返回:
        {items: [{label, pnl}], total_pnl, total_rate, title}
    """
    time_type = request.args.get('type', 'day')
    if time_type not in ('day', 'month', 'year'):
        return jsonify({"error": "Invalid calendar type", "code": "INVALID_CALENDAR_PERIOD"}), 400

    def _parse_positive_int_arg(name):
        raw = request.args.get(name)
        if raw is None:
            return None
        raw = str(raw).strip()
        if not raw:
            return None
        try:
            val = int(raw)
        except ValueError:
            raise ValueError(name)
        if val <= 0:
            raise ValueError(name)
        return val

    year = None
    month = None
    try:
        if time_type == 'day':
            year = _parse_positive_int_arg('year')
            month = _parse_positive_int_arg('month')
            if month is not None and not 1 <= month <= 12:
                return jsonify({"error": "Invalid month", "code": "INVALID_CALENDAR_PERIOD"}), 400
        elif time_type == 'month':
            year = _parse_positive_int_arg('year')
    except ValueError:
        return jsonify({"error": "Invalid year or month", "code": "INVALID_CALENDAR_PERIOD"}), 400

    user_id = g.user_id
    result = db.get_calendar_data(time_type, user_id, year=year, month=month)
    if result.get('code') == 'INVALID_CALENDAR_PERIOD':
        return jsonify(result), 400
    return jsonify(result)


@app.route('/api/analysis/calendar/market_breakdown')
@optional_auth
def analysis_calendar_market_breakdown():
    """
    收益日历（按市场拆分）

    参数:
        time_type|type: day（首期仅支持 day）
        year: 可选年份
        month: 可选月份
    """
    time_type = request.args.get('time_type') or request.args.get('type', 'day')
    if time_type != 'day':
        return jsonify({"error": "Invalid calendar type", "code": "INVALID_CALENDAR_PERIOD"}), 400

    def _parse_positive_int_arg(name):
        raw = request.args.get(name)
        if raw is None:
            return None
        raw = str(raw).strip()
        if not raw:
            return None
        try:
            val = int(raw)
        except ValueError:
            raise ValueError(name)
        if val <= 0:
            raise ValueError(name)
        return val

    try:
        year = _parse_positive_int_arg('year')
        month = _parse_positive_int_arg('month')
        if month is not None and not 1 <= month <= 12:
            return jsonify({"error": "Invalid month", "code": "INVALID_CALENDAR_PERIOD"}), 400
    except ValueError:
        return jsonify({"error": "Invalid year or month", "code": "INVALID_CALENDAR_PERIOD"}), 400

    user_id = g.user_id
    result = db.get_market_breakdown_calendar_data(
        time_type='day',
        user_id=user_id,
        year=year,
        month=month,
    )
    if result.get('code') == 'INVALID_CALENDAR_PERIOD':
        return jsonify(result), 400
    return jsonify(result)


@app.route('/api/analysis/rank')
@optional_auth
def analysis_rank():
    """
    盈亏排行
    
    参数:
        type: gain|loss|all (默认 all)
        market: all|a|us|hk|fund (默认 all)
    
    返回:
        {gain: [{code, name, pnl, pnl_rate, market}], loss: [...]}
    """
    rank_type = request.args.get('type', 'all')
    market = request.args.get('market', 'all')
    user_id = g.user_id
    
    # 获取持仓数据
    portfolio_data = db.get_rank_data('gain', market, user_id)
    
    if not portfolio_data:
        return jsonify({'gain': [], 'loss': []})
    
    # 获取实时价格
    codes = [item['code'] for item in portfolio_data]
    prices = batch_get_prices(codes)
    
    # 计算盈亏
    result_items = []
    for item in portfolio_data:
        code = item['code']
        price_info = prices.get(code, (0, 0, 0, 0))
        current_price = price_info[0] if price_info[0] else item['cost_price']
        
        # 计算盈亏
        qty = item['qty']
        cost = item['cost_price'] * qty
        current_value = current_price * qty
        pnl = current_value - cost + item['adjustment']
        pnl_rate = (pnl / cost * 100) if cost > 0 else 0
        
        result_items.append({
            'code': code,
            'name': item['name'],
            'pnl': round(pnl, 2),
            'pnl_rate': round(pnl_rate, 2),
            'market': item['market']
        })
    
    # 分类排序
    gain_list = sorted([x for x in result_items if x['pnl'] > 0], key=lambda x: x['pnl'], reverse=True)
    loss_list = sorted([x for x in result_items if x['pnl'] < 0], key=lambda x: x['pnl'])
    
    if rank_type == 'gain':
        return jsonify({'gain': gain_list, 'loss': []})
    elif rank_type == 'loss':
        return jsonify({'gain': [], 'loss': loss_list})
    else:
        return jsonify({'gain': gain_list, 'loss': loss_list})


def background_scheduler():
    """后台任务调度"""
    logger.info("Scheduler started")
    while True:
        try:
            # 每小时执行一次快照
            take_snapshot()
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
        
        # 休眠 1 小时 (3600秒)
        # 实际生产中建议使用 APScheduler，这里用简单 sleep 即可
        time.sleep(3600)

if __name__ == '__main__':
    logger.info("Starting Portfolio Management System v10.0...")
    logger.info(f"Database: {config.DATABASE_PATH}")
    logger.info(f"Server: http://{config.HOST}:{config.PORT}")
    
    # 启动后台快照任务（默认关闭，建议用 cron 固定时间触发）
    if config.ENABLE_BACKGROUND_SNAPSHOT:
        threading.Thread(target=background_scheduler, daemon=True).start()
    else:
        logger.info("Background snapshot disabled (cron preferred).")
    
    # 启动时立即执行一次快照（默认关闭）
    if config.ENABLE_STARTUP_SNAPSHOT:
        threading.Thread(target=take_snapshot, daemon=True).start()
    
    # 自动打开浏览器
    threading.Thread(target=open_browser, daemon=True).start()
    
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
