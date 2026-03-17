"""
历史数据 / 资产趋势 / 健康检查处理函数
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Dict

from flask import g, request


def create_misc_payload_handlers(
    *,
    history_read_service,
    asset_trends_getter: Callable[[list[dict[str, str]], int], Any],
    app_version: str,
    metrics_token_ok_getter: Callable[[], bool],
    auth_audit: Callable[..., None],
    price_runtime_metrics_getter: Callable[[], Dict[str, Any]],
    price_source_health_getter: Callable[[], Dict[str, Any]],
    request_runtime_metrics_getter: Callable[[], Dict[str, Any]],
):
    def build_history_payload():
        days = request.args.get('days', 365, type=int)
        user_id = g.user_id
        return history_read_service.get_history(days=days, user_id=user_id)

    def build_asset_trends_payload() -> Dict[str, Any]:
        payload = request.json or {}
        raw_items = payload.get('items') or payload.get('codes') or []
        points = int(payload.get('points') or 20)

        items = []
        if isinstance(raw_items, list):
            for item in raw_items:
                if isinstance(item, dict):
                    items.append({
                        "code": str(item.get("code") or "").strip(),
                        "name": str(item.get("name") or "").strip(),
                        "market": str(item.get("market") or "").strip(),
                    })
                else:
                    items.append({
                        "code": str(item or "").strip(),
                        "name": "",
                        "market": "",
                    })

        trends = asset_trends_getter(items, points=points)
        return {
            "items": trends,
            "points": max(2, min(points, 60)),
            "label": "近期估值趋势",
        }

    def build_health_payload() -> Dict[str, Any]:
        return {
            "status": "ok",
            "version": app_version,
            "request_runtime": request_runtime_metrics_getter(),
        }

    def build_price_health_payload():
        if not metrics_token_ok_getter():
            auth_audit(
                event='metrics_access',
                outcome='blocked',
                reason='invalid_or_missing_token',
                level='warning',
            )
            return {"error": "Unauthorized"}, 401

        return {
            "status": "ok",
            "version": app_version,
            "server_time_utc": datetime.now(timezone.utc).isoformat(),
            "runtime": price_runtime_metrics_getter(),
            "sources": price_source_health_getter(),
        }

    return {
        "history": build_history_payload,
        "asset_trends": build_asset_trends_payload,
        "health": build_health_payload,
        "price_health": build_price_health_payload,
    }
