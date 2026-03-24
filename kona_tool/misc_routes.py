"""
旧页面兼容跳转 / 历史数据 / 资产趋势 / 健康检查路由
"""
from __future__ import annotations

from flask import Blueprint, jsonify, redirect


def _jsonify_result(result):
    if isinstance(result, tuple) and len(result) == 2:
        payload, status = result
        return jsonify(payload), status
    return jsonify(result)


def create_misc_blueprint(
    *,
    optional_auth,
    history_payload_getter,
    asset_trends_payload_getter,
    price_health_payload_getter,
    health_payload_getter,
):
    bp = Blueprint("misc_routes", __name__)

    @bp.route("/analysis")
    def analysis_page():
        """旧分析页入口兼容跳转。"""
        return redirect("/app/analysis", code=302)

    @bp.route("/settings")
    def settings_page():
        """旧设置页入口兼容跳转。"""
        return redirect("/app/profile", code=302)

    @bp.route("/api/history")
    @optional_auth
    def get_history():
        """获取历史资产数据。"""
        return _jsonify_result(history_payload_getter())

    @bp.route("/api/asset/trends", methods=["POST"])
    @optional_auth
    def get_asset_trends():
        """批量获取持仓趋势线数据。"""
        return _jsonify_result(asset_trends_payload_getter())

    @bp.route("/health")
    def health():
        """健康检查。"""
        return _jsonify_result(health_payload_getter())

    @bp.route("/api/system/price_health")
    def api_price_health():
        """行情运行健康指标。"""
        return _jsonify_result(price_health_payload_getter())

    return bp
