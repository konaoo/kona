"""统一 today 实时读侧服务。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Dict


class RealtimeTodayService:
    """产出全站唯一 today realtime payload。"""

    def __init__(
        self,
        *,
        stats_getter: Callable[..., Dict[str, Any]],
    ) -> None:
        self.stats_getter = stats_getter

    def build_payload(
        self,
        *,
        user_id: str | None,
        ledger_id: int | None = None,
    ) -> Dict[str, Any]:
        stats = self.stats_getter(user_id=user_id, ledger_id=ledger_id)
        generated_at = datetime.now(timezone.utc).isoformat()
        total_cost = float(stats.get("total_cost") or 0.0)
        total_pnl = float(stats.get("total_pnl") or 0.0)
        day_pnl = float(stats.get("day_pnl") or 0.0)
        day_pnl_base = float(stats.get("day_pnl_base") or 0.0)
        total_pnl_rate = round(total_pnl / total_cost * 100, 2) if total_cost > 0 else 0.0
        day_pnl_rate = round(day_pnl / day_pnl_base * 100, 2) if day_pnl_base > 0 else 0.0
        effective_date = str(stats.get("day_pnl_effective_date") or stats.get("snapshot_date") or "")
        breakdown = stats.get("day_pnl_by_market") or {}

        return {
            "effective_date": effective_date,
            "scope": {
                "ledger_id": ledger_id,
                "mode": "ledger" if ledger_id is not None else "global",
            },
            "source": "realtime",
            "totals": {
                "total_asset": round(float(stats.get("total_asset") or 0.0), 2),
                "total_market_value": round(float(stats.get("total_invest") or 0.0), 2),
                "total_cash": round(float(stats.get("total_cash") or 0.0), 2),
                "total_other": round(float(stats.get("total_other") or 0.0), 2),
                "total_liability": round(float(stats.get("total_liability") or 0.0), 2),
                "total_pnl": round(total_pnl, 2),
                "total_pnl_rate": total_pnl_rate,
                "day_pnl": round(day_pnl, 2),
                "day_pnl_base": round(day_pnl_base, 2),
                "day_pnl_rate": day_pnl_rate,
            },
            "breakdown_by_market": {
                "a": {
                    "day_pnl": round(float(breakdown.get("a") or 0.0), 2),
                    "day_pnl_base": 0.0,
                },
                "hk": {
                    "day_pnl": round(float(breakdown.get("hk") or 0.0), 2),
                    "day_pnl_base": 0.0,
                },
                "us": {
                    "day_pnl": round(float(breakdown.get("us") or 0.0), 2),
                    "day_pnl_base": 0.0,
                },
                "fund": {
                    "day_pnl": round(float(breakdown.get("fund") or 0.0), 2),
                    "day_pnl_base": 0.0,
                },
            },
            "generated_at": generated_at,
        }
