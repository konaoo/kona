"""
同步引导处理函数
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Callable, Dict

from flask import g, request

from core.request_trace import trace_request_stage
from sync_contract import QUOTE_POLICY_DEFAULT, SYNC_BOOTSTRAP_DOMAINS


def create_sync_payload_handlers(
    *,
    db,
    rates_getter: Callable[[], Dict[str, Any]],
    market_status_refresh_getter: Callable[..., Dict[str, Any]],
    market_scope: list[str],
    portfolio_metrics_builder: Callable[..., Any] | None = None,
):
    def _sync_rates_version(rates: Dict[str, Any]) -> str:
        try:
            normalized = {
                str(key): float(value)
                for key, value in sorted((rates or {}).items(), key=lambda item: str(item[0]))
            }
        except Exception:
            normalized = {}
        raw = json.dumps(normalized, ensure_ascii=False, sort_keys=True)
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]

    def _normalize_sync_include(raw_include: Any) -> list[str]:
        if not isinstance(raw_include, list):
            return list(SYNC_BOOTSTRAP_DOMAINS)
        include: list[str] = []
        for item in raw_include:
            key = str(item or "").strip().lower()
            if key in SYNC_BOOTSTRAP_DOMAINS and key not in include:
                include.append(key)
        return include or list(SYNC_BOOTSTRAP_DOMAINS)

    def _parse_bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        text = str(value or "").strip().lower()
        return text in {"1", "true", "yes", "y", "on"}

    def _build_sync_domain_data(
        domain: str,
        user_id: str = None,
        *,
        with_portfolio_metrics: bool = False,
        now_utc: datetime | None = None,
    ) -> Any:
        with trace_request_stage(f"sync.domain.{domain}"):
            if domain == "portfolio":
                if with_portfolio_metrics and portfolio_metrics_builder is not None:
                    return portfolio_metrics_builder(user_id=user_id, now_utc=now_utc)
                return db.get_portfolio(user_id=user_id)
            if domain == "cash_assets":
                return db.get_cash_assets(user_id=user_id)
            if domain == "other_assets":
                return db.get_other_assets(user_id=user_id)
            if domain == "liabilities":
                return db.get_liabilities(user_id=user_id)
            if domain == "history":
                return db.get_history(5000, user_id=user_id)
            if domain == "overview_all":
                return {
                    "day": db.get_pnl_overview("day", user_id),
                    "month": db.get_pnl_overview("month", user_id),
                    "year": db.get_pnl_overview("year", user_id),
                    "all": db.get_pnl_overview("all", user_id),
                }
            if domain == "rates":
                return rates_getter()
        return None

    def build_sync_bootstrap_payload() -> Dict[str, Any]:
        body = request.get_json(silent=True) or {}
        include = _normalize_sync_include(body.get("include"))
        client_versions_raw = body.get("client_versions")
        client_versions = client_versions_raw if isinstance(client_versions_raw, dict) else {}
        include_portfolio_metrics = _parse_bool(body.get("portfolio_metrics"))

        user_id = getattr(g, "user_id", None)
        now_utc = datetime.now(timezone.utc)
        with trace_request_stage("sync.rates"):
            rates = rates_getter()

        with trace_request_stage("sync.versions"):
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
                data[domain] = _build_sync_domain_data(
                    domain,
                    user_id=user_id,
                    with_portfolio_metrics=include_portfolio_metrics,
                    now_utc=now_utc,
                )

        with trace_request_stage("sync.market_status"):
            market_payload = market_status_refresh_getter(now_utc=now_utc, force_refresh=True)
        markets = market_payload.get("markets", {})
        return {
            "server_time": now_utc.isoformat(),
            "versions": {key: versions[key] for key in SYNC_BOOTSTRAP_DOMAINS},
            "changed": changed,
            "data": data,
            "market_statuses": markets,
            "market_status": {key: bool((markets.get(key) or {}).get("open")) for key in market_scope},
            "quote_policy": dict(QUOTE_POLICY_DEFAULT),
        }

    return {
        "bootstrap": build_sync_bootstrap_payload,
    }
