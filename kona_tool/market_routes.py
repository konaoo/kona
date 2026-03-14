"""
市场状态 / 首页指数 / 同步引导路由
"""
from __future__ import annotations

from flask import Blueprint, jsonify


def create_market_blueprint(
    *,
    optional_auth,
    market_status_payload_getter,
    market_indices_payload_getter,
    sync_bootstrap_payload_getter,
):
    bp = Blueprint("market_routes", __name__)

    @bp.route("/api/market/status")
    def api_market_status():
        """主流市场开休市状态。"""
        return jsonify(market_status_payload_getter())

    @bp.route("/api/market/indices")
    def api_market_indices():
        """获取首页顶部的指数和汇率数据。"""
        return jsonify(market_indices_payload_getter())

    @bp.route("/api/sync/bootstrap", methods=["POST"])
    @optional_auth
    def api_sync_bootstrap():
        """客户端增量同步引导接口。"""
        return jsonify(sync_bootstrap_payload_getter())

    return bp
