"""
单价 / 批量报价 / 汇率 / 搜索路由
"""
from __future__ import annotations

from flask import Blueprint, jsonify


def _jsonify_result(result):
    if isinstance(result, tuple) and len(result) == 2:
        payload, status = result
        return jsonify(payload), status
    return jsonify(result)


def create_quote_blueprint(
    *,
    price_payload_getter,
    prices_batch_payload_getter,
    rates_payload_getter,
    search_payload_getter,
):
    bp = Blueprint("quote_routes", __name__)

    @bp.route("/api/price")
    def api_price():
        """获取单个价格。"""
        return _jsonify_result(price_payload_getter())

    @bp.route("/api/prices/batch", methods=["POST"])
    def api_prices_batch():
        """批量获取价格。"""
        return _jsonify_result(prices_batch_payload_getter())

    @bp.route("/api/rates")
    def api_rates():
        """获取汇率。"""
        return _jsonify_result(rates_payload_getter())

    @bp.route("/api/search")
    def search():
        """搜索股票。"""
        return _jsonify_result(search_payload_getter())

    return bp
