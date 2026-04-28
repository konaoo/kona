"""投资交易运行时基础设施。

负责承接：
- 持仓身份标准化
- 幂等请求记录
- 撤销令牌与撤销记录
- 多币种金额换算
"""

from __future__ import annotations

from datetime import datetime, timezone
import re
import secrets
import threading
import time
from typing import Any, Callable, Dict

from flask import jsonify


class PortfolioRuntime:
    """封装投资交易链的运行时工具。"""

    def __init__(
        self,
        *,
        parse_code: Callable[[str, str], dict],
        infer_asset_type: Callable[[str, str], str],
        batch_get_prices_getter: Callable[[list[str]], dict],
        exchange_fund_probe_ttl_seconds: float = 300.0,
        idempotency_window_seconds: float = 20.0,
        undo_window_seconds: float = 15.0,
        time_getter: Callable[[], float] | None = None,
        token_factory: Callable[[int], str] | None = None,
        logger: Any | None = None,
    ) -> None:
        self.parse_code = parse_code
        self.infer_asset_type = infer_asset_type
        self.batch_get_prices_getter = batch_get_prices_getter
        self.exchange_fund_probe_ttl_seconds = exchange_fund_probe_ttl_seconds
        self.idempotency_window_seconds = idempotency_window_seconds
        self.undo_window_seconds = undo_window_seconds
        self.time_getter = time_getter or time.time
        self.token_factory = token_factory or secrets.token_urlsafe
        self.logger = logger

        self._idempotency_lock = threading.Lock()
        self._idempotency_records: dict[tuple[str, str, str], dict] = {}
        self._undo_lock = threading.Lock()
        self._undo_records: dict[tuple[str, str], dict] = {}
        self._exchange_fund_probe_lock = threading.Lock()
        self._exchange_fund_probe_cache: Dict[str, Dict[str, Any]] = {}

    def exchange_fund_candidates(self, code: str) -> list[str]:
        lower = str(code or "").strip().lower()
        if not lower.startswith("f_"):
            return []
        suffix = lower[2:].strip()
        if not re.fullmatch(r"\d{6}", suffix):
            return []
        if suffix.startswith("11") and not suffix.startswith(("511",)):
            return []
        if suffix.startswith(("15", "16", "18")):
            return [f"sz{suffix}"]
        if suffix.startswith(("50", "51", "52", "56", "58", "511")):
            return [f"sh{suffix}"]
        return []

    def resolve_exchange_tradable_fund_code(self, code: str) -> str:
        candidates = self.exchange_fund_candidates(code)
        if not candidates:
            return code

        now_ts = self.time_getter()
        cache_key = str(code or "").strip().lower()
        with self._exchange_fund_probe_lock:
            cached = self._exchange_fund_probe_cache.get(cache_key)
            if cached and (now_ts - float(cached.get("ts") or 0.0)) <= self.exchange_fund_probe_ttl_seconds:
                resolved = str(cached.get("code") or "").strip()
                return resolved or code

        resolved_code = code
        try:
            quotes = self.batch_get_prices_getter(candidates)
            for candidate in candidates:
                quote = quotes.get(candidate) or (0.0, 0.0, 0.0, 0.0)
                try:
                    price = float(quote[0] or 0.0)
                except Exception:
                    price = 0.0
                if price > 0:
                    resolved_code = candidate
                    break
        except Exception as exc:
            if self.logger is not None:
                self.logger.info("exchange fund probe failed code=%s error=%s", code, exc)

        with self._exchange_fund_probe_lock:
            self._exchange_fund_probe_cache[cache_key] = {"code": resolved_code, "ts": now_ts}
        return resolved_code

    def normalize_portfolio_identity(self, raw_code: str, raw_curr: str, raw_name: str) -> Dict[str, str]:
        parsed = self.parse_code(raw_code, raw_curr)
        code = str(parsed.get("code") or "").strip()
        curr = str(parsed.get("curr") or "").strip().upper()
        name = str(raw_name or "").strip() or code

        lower = code.lower()
        if lower.startswith("f_"):
            suffix = code[2:].strip()
            # 只有当 suffix 是非 ISIN 的纯字母代码时，才视为美股代码的误标
            from core.fund import is_isin_format
            if suffix and not suffix.isdigit() and re.fullmatch(r"[A-Za-z][A-Za-z0-9.\-]*", suffix) and not is_isin_format(suffix):
                code = f"gb_{suffix.lower()}"
                curr = "USD"
                lower = code.lower()
            else:
                resolved_code = self.resolve_exchange_tradable_fund_code(code)
                if resolved_code != code:
                    code = resolved_code
                    lower = code.lower()

        if lower.startswith("sh900"):
            curr = "USD"
        elif lower.startswith("sz200"):
            curr = "HKD"
        elif lower.startswith(("gb_", "ft_")):
            curr = "USD"
        elif lower.startswith("f_") or lower.startswith(("sh", "sz", "bj")):
            curr = "CNY"
        elif ".hk" in lower or lower.startswith("hk"):
            curr = "HKD"
        elif not curr:
            curr = "CNY"

        asset_type = self.infer_asset_type(code, name)
        return {
            "code": code,
            "curr": curr,
            "name": name,
            "asset_type": asset_type,
        }

    def idempotency_begin(self, action: str, user_id: str, request_id: str):
        request_id = (request_id or "").strip()
        if not request_id:
            return False, None, None
        now_ts = self.time_getter()
        key = (user_id or "", action, request_id)
        with self._idempotency_lock:
            expired = [item for item, value in self._idempotency_records.items() if value.get("expires_at", 0) < now_ts]
            for expired_key in expired:
                self._idempotency_records.pop(expired_key, None)
            record = self._idempotency_records.get(key)
            if record:
                if record.get("state") == "done":
                    return True, record.get("payload", {"status": "ok"}), int(record.get("status_code", 200))
                return True, {"status": "ok", "code": "REQUEST_DEDUP_IN_FLIGHT"}, 200
            self._idempotency_records[key] = {
                "state": "inflight",
                "expires_at": now_ts + self.idempotency_window_seconds,
            }
        return False, None, None

    def idempotency_finish(self, action: str, user_id: str, request_id: str, status_code: int, payload: dict) -> None:
        request_id = (request_id or "").strip()
        if not request_id:
            return
        key = (user_id or "", action, request_id)
        with self._idempotency_lock:
            self._idempotency_records[key] = {
                "state": "done",
                "status_code": int(status_code),
                "payload": payload,
                "expires_at": self.time_getter() + self.idempotency_window_seconds,
            }

    def idempotent_response(self, action: str, user_id: str, request_id: str, payload: dict, status_code: int = 200):
        self.idempotency_finish(action, user_id, request_id, status_code, payload)
        return jsonify(payload), status_code

    def undo_key(self, user_id: str, token: str):
        return (user_id or "", token)

    def cleanup_undo_records_locked(self, now_ts: float) -> None:
        expired = [item for item, value in self._undo_records.items() if value.get("expires_at", 0) < now_ts]
        for expired_key in expired:
            self._undo_records.pop(expired_key, None)

    def create_undo_record(self, user_id: str, operation: dict):
        token = self.token_factory(18)
        expires_at_ts = self.time_getter() + self.undo_window_seconds
        key = self.undo_key(user_id, token)
        with self._undo_lock:
            self.cleanup_undo_records_locked(self.time_getter())
            self._undo_records[key] = {
                "operation": operation,
                "expires_at": expires_at_ts,
                "used": False,
            }
        expires_at_iso = datetime.fromtimestamp(expires_at_ts, tz=timezone.utc).isoformat()
        return token, expires_at_iso

    def claim_undo_record(self, user_id: str, token: str):
        token = (token or "").strip()
        if not token:
            return None, ("UNDO_TOKEN_REQUIRED", "Missing undo token", 400)
        now_ts = self.time_getter()
        key = self.undo_key(user_id, token)
        with self._undo_lock:
            self.cleanup_undo_records_locked(now_ts)
            record = self._undo_records.get(key)
            if not record:
                return None, ("UNDO_TOKEN_EXPIRED", "Undo token is invalid or expired", 400)
            if record.get("used"):
                return None, ("UNDO_ALREADY_USED", "Undo token already used", 409)
            record["used"] = True
            return record.get("operation"), None

    def release_undo_claim(self, user_id: str, token: str) -> None:
        key = self.undo_key(user_id, token)
        with self._undo_lock:
            record = self._undo_records.get(key)
            if record:
                record["used"] = False

    def decorate_with_undo(self, payload: dict, user_id: str, operation: dict):
        undo_token, undo_expire_at = self.create_undo_record(user_id, operation)
        result = dict(payload)
        result["undo_token"] = undo_token
        result["undo_expire_at"] = undo_expire_at
        return result

    def to_float(self, value, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def rate_to_cny(self, curr: str, rates: dict) -> float:
        currency = (curr or "CNY").upper()
        if currency == "CNY":
            return 1.0
        raw = rates.get(currency) if isinstance(rates, dict) else None
        rate = self.to_float(raw, 0.0)
        return rate if rate > 0 else 1.0

    def convert_amount(self, amount: float, from_curr: str, to_curr: str, rates: dict) -> float:
        from_rate = self.rate_to_cny(from_curr, rates)
        to_rate = self.rate_to_cny(to_curr, rates)
        cny_amount = amount * from_rate
        return cny_amount / to_rate if to_rate > 0 else cny_amount


def create_portfolio_runtime(**kwargs) -> PortfolioRuntime:
    return PortfolioRuntime(**kwargs)
