"""分析页统一读模型服务。"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Callable, Dict
from zoneinfo import ZoneInfo


class AnalysisScreenService:
    """统一产出分析页单屏数据，避免前端再二次拼装 today / calendar / overview。"""

    def __init__(
        self,
        *,
        db: Any,
        analysis_read_service: Any,
        realtime_today_service: Any | None = None,
        timezone_name: str = "Asia/Shanghai",
        now_getter: Callable[[], datetime] | None = None,
    ) -> None:
        self.db = db
        self.analysis_read_service = analysis_read_service
        self.realtime_today_service = realtime_today_service
        self.timezone_name = timezone_name
        self._has_explicit_now_getter = now_getter is not None
        self.now_getter = now_getter or (lambda: datetime.now(timezone.utc))

    def build_payload(
        self,
        *,
        time_type: str,
        user_id: str | None,
        year: int | None,
        month: int | None,
        ledger_id: int | None = None,
    ) -> Dict[str, Any]:
        now_utc = self.now_getter()
        if now_utc.tzinfo is None:
            now_utc = now_utc.replace(tzinfo=timezone.utc)
        local_now = self._resolve_local_now(now_utc)
        generated_at = now_utc.isoformat()
        analysis_version = f"{generated_at}|ledger={ledger_id or 'all'}|calendar={time_type}:{year or ''}:{month or ''}"

        realtime_today = self._load_realtime_today(
            user_id=user_id,
            ledger_id=ledger_id,
        )
        overview = self._build_overview(
            realtime_today=realtime_today,
            user_id=user_id,
            ledger_id=ledger_id,
        )
        rank = self.analysis_read_service.build_rank_payload(
            market="all",
            user_id=user_id,
            ledger_id=ledger_id,
        )
        raw_calendar = self.db.get_calendar_data(
            time_type,
            user_id,
            year=year,
            month=month,
            ledger_id=ledger_id,
        )
        calendar = self._normalize_calendar(
            payload=raw_calendar,
            realtime_today=realtime_today,
            local_now=local_now,
            time_type=time_type,
        )

        return {
            "meta": {
                "analysis_version": analysis_version,
                "generated_at": generated_at,
                "timezone": self.timezone_name,
                "ledger_id": ledger_id,
                "today_effective_date": str(realtime_today.get("effective_date") or ""),
                "today_status": self._resolve_today_status(
                    realtime_today=realtime_today,
                    local_now=local_now,
                ),
            },
            "overview": overview,
            "calendar": calendar,
            "rank": rank,
            "realtime_today": realtime_today,
        }

    def _load_realtime_today(
        self,
        *,
        user_id: str | None,
        ledger_id: int | None,
    ) -> Dict[str, Any]:
        if self.realtime_today_service is None:
            return {}
        try:
            return self.realtime_today_service.build_payload(
                user_id=user_id,
                ledger_id=ledger_id,
            ) or {}
        except Exception:
            return {}

    def _build_overview(
        self,
        *,
        realtime_today: Dict[str, Any],
        user_id: str | None,
        ledger_id: int | None,
    ) -> Dict[str, Any]:
        totals = realtime_today.get("totals") or {}
        day_payload: Dict[str, Any]
        if realtime_today:
            day_payload = {
                "pnl": round(float(totals.get("day_pnl") or 0.0), 2),
                "pnl_rate": round(float(totals.get("day_pnl_rate") or 0.0), 2),
                "base_value": round(float(totals.get("day_pnl_base") or 0.0), 2),
                "effective_date": realtime_today.get("effective_date"),
                "source": "realtime",
            }
        else:
            day_payload = self.db.get_pnl_overview("day", user_id, ledger_id=ledger_id)
            day_payload = {
                **day_payload,
                "source": "snapshot",
            }

        return {
            "day": day_payload,
            "month": self.db.get_pnl_overview("month", user_id, ledger_id=ledger_id),
            "year": self.db.get_pnl_overview("year", user_id, ledger_id=ledger_id),
            "all": self.db.get_pnl_overview("all", user_id, ledger_id=ledger_id),
        }

    def _normalize_calendar(
        self,
        *,
        payload: Dict[str, Any],
        realtime_today: Dict[str, Any],
        local_now: datetime,
        time_type: str,
    ) -> Dict[str, Any]:
        result = deepcopy(payload)
        result.setdefault("items", [])
        result.setdefault("period", {})
        if result.get("code") == "INVALID_CALENDAR_PERIOD":
            return result

        summary = {
            "label": self._calendar_summary_label(time_type),
            "total_pnl": result.get("total_pnl"),
            "total_rate": result.get("total_rate"),
        }

        if time_type == "day":
            result = self._apply_realtime_today_to_calendar(
                payload=result,
                summary=summary,
                realtime_today=realtime_today,
                local_now=local_now,
            )
        else:
            result["summary"] = summary

        return result

    def _apply_realtime_today_to_calendar(
        self,
        *,
        payload: Dict[str, Any],
        summary: Dict[str, Any],
        realtime_today: Dict[str, Any],
        local_now: datetime,
    ) -> Dict[str, Any]:
        period = payload.get("period") or {}
        period_year = int(period.get("year") or 0)
        period_month = int(period.get("month") or 0)
        effective_date = str(realtime_today.get("effective_date") or "").strip()
        if not realtime_today or not effective_date or period_year <= 0 or period_month <= 0:
            payload["summary"] = summary
            return payload

        try:
            effective_local = datetime.strptime(effective_date[:10], "%Y-%m-%d")
        except ValueError:
            payload["summary"] = summary
            return payload

        if effective_local.year != period_year or effective_local.month != period_month:
            payload["summary"] = summary
            return payload

        totals = realtime_today.get("totals") or {}
        realtime_pnl = round(float(totals.get("day_pnl") or 0.0), 2)
        items = list(payload.get("items") or [])
        target_label = f"{period_month}-{effective_local.day}"
        original_pnl = 0.0
        replaced = False
        for item in items:
            if str(item.get("label") or "") != target_label:
                continue
            original_pnl = float(item.get("pnl") or 0.0)
            item["pnl"] = realtime_pnl
            replaced = True
            break
        if not replaced:
            items.append({"label": target_label, "pnl": realtime_pnl})

        base_value = float(payload.get("base_value") or 0.0)
        raw_total = float(payload.get("total_pnl") or 0.0)
        adjusted_total = round(raw_total - original_pnl + realtime_pnl, 2)
        adjusted_rate = round(adjusted_total / base_value * 100, 2) if base_value > 0 else 0.0
        payload["items"] = items
        payload["total_pnl"] = adjusted_total
        payload["total_rate"] = adjusted_rate
        payload["summary"] = {
            **summary,
            "total_pnl": adjusted_total,
            "total_rate": adjusted_rate,
        }
        payload["today_override"] = {
            "applied": True,
            "effective_date": effective_date[:10],
            "status": self._resolve_today_status(
                realtime_today=realtime_today,
                local_now=local_now,
            ),
        }
        return payload

    def _resolve_today_status(
        self,
        *,
        realtime_today: Dict[str, Any],
        local_now: datetime,
    ) -> str:
        effective_date = str(realtime_today.get("effective_date") or "").strip()
        if not realtime_today or not effective_date:
            return "unavailable"
        today_str = local_now.strftime("%Y-%m-%d")
        if effective_date[:10] == today_str:
            return "ready"
        return "pending"

    def _resolve_local_now(self, now_utc: datetime) -> datetime:
        if self._has_explicit_now_getter:
            return now_utc.astimezone(ZoneInfo(self.timezone_name))

        try:
            try:
                from .db_analysis import _get_datetime_now
            except ImportError:  # pragma: no cover
                from core.db_analysis import _get_datetime_now

            local_now = _get_datetime_now()
            if isinstance(local_now, datetime):
                if local_now.tzinfo is None:
                    return local_now.replace(tzinfo=ZoneInfo(self.timezone_name))
                return local_now.astimezone(ZoneInfo(self.timezone_name))
        except Exception:
            pass

        return now_utc.astimezone(ZoneInfo(self.timezone_name))

    @staticmethod
    def _calendar_summary_label(time_type: str) -> str:
        if time_type == "day":
            return "本月盈亏"
        if time_type == "month":
            return "本年盈亏"
        return "累计盈亏"
