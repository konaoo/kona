"""
分析页概览 / 日历 / 排行路由
"""
from __future__ import annotations

from flask import Blueprint, jsonify


def _jsonify_result(result):
    if isinstance(result, tuple) and len(result) == 2:
        payload, status = result
        return jsonify(payload), status
    return jsonify(result)


def create_analysis_blueprint(
    *,
    optional_auth,
    analysis_overview_payload_getter,
    analysis_calendar_payload_getter,
    analysis_market_breakdown_payload_getter,
    analysis_asset_breakdown_payload_getter,
    analysis_rank_payload_getter,
    analysis_screen_payload_getter,
    realtime_today_payload_getter,
):
    bp = Blueprint("analysis_routes", __name__)

    @bp.route("/api/analysis/overview")
    @optional_auth
    def analysis_overview():
        """盈亏概览。"""
        return _jsonify_result(analysis_overview_payload_getter())

    @bp.route("/api/analysis/calendar")
    @optional_auth
    def analysis_calendar():
        """收益日历。"""
        return _jsonify_result(analysis_calendar_payload_getter())

    @bp.route("/api/analysis/calendar/market_breakdown")
    @optional_auth
    def analysis_calendar_market_breakdown():
        """收益日历按市场拆分。"""
        return _jsonify_result(analysis_market_breakdown_payload_getter())

    @bp.route("/api/analysis/calendar/asset_breakdown")
    @optional_auth
    def analysis_calendar_asset_breakdown():
        """收益日历按资产下钻。"""
        return _jsonify_result(analysis_asset_breakdown_payload_getter())

    @bp.route("/api/analysis/rank")
    @optional_auth
    def analysis_rank():
        """盈亏排行。"""
        return _jsonify_result(analysis_rank_payload_getter())

    @bp.route("/api/analysis/screen")
    @optional_auth
    def analysis_screen():
        """分析页统一屏幕数据。"""
        return _jsonify_result(analysis_screen_payload_getter())

    @bp.route("/api/realtime/today")
    @optional_auth
    def realtime_today():
        """全站统一 today realtime payload。"""
        return _jsonify_result(realtime_today_payload_getter())

    return bp
