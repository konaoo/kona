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
        realtime_adjustment = self._build_realtime_adjustment(
            realtime_today=realtime_today,
            local_now=local_now,
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
            realtime_adjustment=realtime_adjustment,
        )
        overview = self._build_overview(
            realtime_today=realtime_today,
            user_id=user_id,
            ledger_id=ledger_id,
            realtime_adjustment=realtime_adjustment,
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
        realtime_adjustment: Dict[str, Any],
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

        overview = {
            "day": day_payload,
            "month": self.db.get_pnl_overview("month", user_id, ledger_id=ledger_id),
            "year": self.db.get_pnl_overview("year", user_id, ledger_id=ledger_id),
            "all": self.db.get_pnl_overview("all", user_id, ledger_id=ledger_id),
        }
        if not realtime_adjustment.get("applied"):
            return overview

        for period in ("month", "year"):
            overview[period] = self._apply_delta_to_pnl_payload(
                overview[period],
                realtime_adjustment["delta"],
            )
        if realtime_adjustment.get("total_pnl") is not None:
            overview["all"] = self._apply_exact_pnl_to_payload(
                overview["all"],
                realtime_adjustment["total_pnl"],
            )
        return overview

    def _build_realtime_adjustment(
        self,
        *,
        realtime_today: Dict[str, Any],
        local_now: datetime,
        user_id: str | None,
        ledger_id: int | None,
    ) -> Dict[str, Any]:
        """只让真正属于今天的实时值覆盖当天快照。"""
        totals = realtime_today.get("totals") or {}
        effective_date = str(realtime_today.get("effective_date") or "").strip()[:10]
        if not effective_date or effective_date != local_now.strftime("%Y-%m-%d"):
            return {"applied": False}
        try:
            realtime_day_pnl = round(float(totals.get("day_pnl") or 0.0), 2)
        except (TypeError, ValueError):
            return {"applied": False}

        snapshot_day = self.db.get_pnl_overview("day", user_id, ledger_id=ledger_id)
        snapshot_day_pnl = round(float(snapshot_day.get("pnl") or 0.0), 2)
        try:
            total_pnl = round(float(totals["total_pnl"]), 2) if totals.get("total_pnl") is not None else None
        except (TypeError, ValueError):
            total_pnl = None
        return {
            "applied": True,
            "effective_date": effective_date,
            "delta": round(realtime_day_pnl - snapshot_day_pnl, 2),
            "total_pnl": total_pnl,
        }

    @staticmethod
    def _apply_delta_to_pnl_payload(payload: Dict[str, Any], delta: float) -> Dict[str, Any]:
        result = dict(payload or {})
        pnl = round(float(result.get("pnl") or 0.0) + float(delta or 0.0), 2)
        base = float(result.get("base_value") or 0.0)
        result.update({"pnl": pnl, "pnl_rate": round(pnl / base * 100, 2) if base > 0 else 0.0, "source": "realtime_adjusted"})
        return result

    @staticmethod
    def _apply_exact_pnl_to_payload(payload: Dict[str, Any], pnl: float) -> Dict[str, Any]:
        result = dict(payload or {})
        base = float(result.get("base_value") or 0.0)
        value = round(float(pnl or 0.0), 2)
        result.update({"pnl": value, "pnl_rate": round(value / base * 100, 2) if base > 0 else 0.0, "source": "realtime"})
        return result

    def _normalize_calendar(
        self,
        *,
        payload: Dict[str, Any],
        realtime_today: Dict[str, Any],
        local_now: datetime,
        time_type: str,
        realtime_adjustment: Dict[str, Any],
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

        if realtime_adjustment.get("applied"):
            result = self._apply_realtime_today_to_calendar(
                payload=result,
                summary=summary,
                time_type=time_type,
                realtime_adjustment=realtime_adjustment,
            )
        else:
            result["summary"] = summary

        return result

    def _apply_realtime_today_to_calendar(
        self,
        *,
        payload: Dict[str, Any],
        summary: Dict[str, Any],
        time_type: str,
        realtime_adjustment: Dict[str, Any],
    ) -> Dict[str, Any]:
        period = payload.get("period") or {}
        period_year = int(period.get("year") or 0)
        period_month = int(period.get("month") or 0)
        effective_date = str(realtime_adjustment.get("effective_date") or "").strip()
        if not effective_date:
            payload["summary"] = summary
            return payload

        try:
            effective_local = datetime.strptime(effective_date[:10], "%Y-%m-%d")
        except ValueError:
            payload["summary"] = summary
            return payload

        items = list(payload.get("items") or [])
        delta = float(realtime_adjustment.get("delta") or 0.0)
        if time_type == "day":
            if effective_local.year != period_year or effective_local.month != period_month:
                payload["summary"] = summary
                return payload
            target_label = f"{period_month}-{effective_local.day}"
            for item in items:
                if str(item.get("label") or "") == target_label:
                    item["pnl"] = round(float(item.get("pnl") or 0.0) + delta, 2)
                    break
            else:
                items.append({"label": target_label, "pnl": round(delta, 2)})
        elif time_type == "month":
            if effective_local.year != period_year:
                payload["summary"] = summary
                return payload
            target_label = f"{effective_local.month}月"
            for item in items:
                if str(item.get("label") or "") == target_label:
                    item["pnl"] = round(float(item.get("pnl") or 0.0) + delta, 2)
                    break
        elif time_type == "year":
            target_label = str(effective_local.year)
            for item in items:
                if str(item.get("label") or "") == target_label:
                    item["pnl"] = round(float(item.get("pnl") or 0.0) + delta, 2)
                    break
        else:
            payload["summary"] = summary
            return payload

        base_value = float(payload.get("base_value") or 0.0)
        adjusted_total = round(float(payload.get("total_pnl") or 0.0) + delta, 2)
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
            "status": "ready",
            "delta": delta,
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
