"""分析页概览 / 日历 / 排行处理函数。"""
from __future__ import annotations

from flask import g, request


def create_analysis_payload_handlers(
    *,
    analysis_read_service,
):
    def _parse_positive_int_arg(name: str):
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

    def build_analysis_overview_payload():
        """
        盈亏概览

        参数:
            period: day|month|year|all (默认 all)

        返回:
            {day: {pnl, pnl_rate}, month: {...}, year: {...}, all: {...}}
        """
        period = request.args.get('period', 'all')
        user_id = g.user_id
        return analysis_read_service.build_overview_payload(
            period=period,
            user_id=user_id,
        )

    def build_analysis_calendar_payload():
        """
        收益日历

        参数:
            type: day|month|year (默认 day)

        返回:
            {items: [{label, pnl}], total_pnl, total_rate, title}
        """
        time_type = request.args.get('type', 'day')
        if time_type not in ('day', 'month', 'year'):
            return {"error": "Invalid calendar type", "code": "INVALID_CALENDAR_PERIOD"}, 400

        year = None
        month = None
        try:
            if time_type == 'day':
                year = _parse_positive_int_arg('year')
                month = _parse_positive_int_arg('month')
                if month is not None and not 1 <= month <= 12:
                    return {"error": "Invalid month", "code": "INVALID_CALENDAR_PERIOD"}, 400
            elif time_type == 'month':
                year = _parse_positive_int_arg('year')
        except ValueError:
            return {"error": "Invalid year or month", "code": "INVALID_CALENDAR_PERIOD"}, 400

        user_id = g.user_id
        result = analysis_read_service.build_calendar_payload(
            time_type=time_type,
            user_id=user_id,
            year=year,
            month=month,
        )
        if result.get('code') == 'INVALID_CALENDAR_PERIOD':
            return result, 400
        return result

    def build_analysis_market_breakdown_payload():
        """
        收益日历（按市场拆分）

        参数:
            time_type|type: day（首期仅支持 day）
            year: 可选年份
            month: 可选月份
        """
        time_type = request.args.get('time_type') or request.args.get('type', 'day')
        if time_type != 'day':
            return {"error": "Invalid calendar type", "code": "INVALID_CALENDAR_PERIOD"}, 400

        try:
            year = _parse_positive_int_arg('year')
            month = _parse_positive_int_arg('month')
            if month is not None and not 1 <= month <= 12:
                return {"error": "Invalid month", "code": "INVALID_CALENDAR_PERIOD"}, 400
        except ValueError:
            return {"error": "Invalid year or month", "code": "INVALID_CALENDAR_PERIOD"}, 400

        user_id = g.user_id
        result = analysis_read_service.build_market_breakdown_payload(
            user_id=user_id,
            year=year,
            month=month,
        )
        if result.get('code') == 'INVALID_CALENDAR_PERIOD':
            return result, 400
        return result

    def build_analysis_rank_payload():
        """
        盈亏排行

        参数:
            type: gain|loss|all (默认 all)
            market: all|a|us|hk|fund (默认 all)

        返回:
            {gain: [{code, name, pnl, pnl_rate, market}], loss: [...]}
        """
        market = request.args.get('market', 'all')
        user_id = g.user_id
        return analysis_read_service.build_rank_payload(
            market=market,
            user_id=user_id,
        )

    return {
        'overview': build_analysis_overview_payload,
        'calendar': build_analysis_calendar_payload,
        'market_breakdown': build_analysis_market_breakdown_payload,
        'rank': build_analysis_rank_payload,
    }
