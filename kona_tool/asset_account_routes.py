"""
现金 / 其他资产 / 负债 / 交易记录路由
"""
from __future__ import annotations

from flask import Blueprint, Response, jsonify


def _jsonify_result(result):
    if isinstance(result, Response):
        response = result
    elif isinstance(result, tuple) and len(result) == 2:
        payload, status = result
        if isinstance(payload, Response):
            response = payload
        else:
            response = jsonify(payload)
    else:
        response = jsonify(result)
        
    # 统一注入禁止强缓存的头部，保证接口数据实时正确
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0, private'
    response.headers['Pragma'] = 'no-cache'
    
    if isinstance(result, tuple) and len(result) == 2:
        return response, result[1]
    return response


def create_asset_account_blueprint(
    *,
    optional_auth,
    transactions_payload_getter,
    cash_assets_payload_getter,
    cash_asset_add_handler,
    cash_asset_delete_handler,
    cash_asset_update_handler,
    other_assets_payload_getter,
    other_asset_add_handler,
    other_asset_delete_handler,
    other_asset_update_handler,
    liabilities_payload_getter,
    liability_add_handler,
    liability_delete_handler,
    liability_update_handler,
):
    bp = Blueprint("asset_account_routes", __name__)

    @bp.route("/api/transactions", methods=["GET"])
    @optional_auth
    def get_transactions():
        return _jsonify_result(transactions_payload_getter())

    @bp.route("/api/cash_assets", methods=["GET"])
    @optional_auth
    def get_cash_assets():
        return _jsonify_result(cash_assets_payload_getter())

    @bp.route("/api/cash_assets/add", methods=["POST"])
    @optional_auth
    def add_cash_asset():
        return _jsonify_result(cash_asset_add_handler())

    @bp.route("/api/cash_assets/delete", methods=["POST"])
    @optional_auth
    def delete_cash_asset():
        return _jsonify_result(cash_asset_delete_handler())

    @bp.route("/api/cash_assets/update", methods=["POST"])
    @optional_auth
    def update_cash_asset():
        return _jsonify_result(cash_asset_update_handler())

    @bp.route("/api/other_assets", methods=["GET"])
    @optional_auth
    def get_other_assets():
        return _jsonify_result(other_assets_payload_getter())

    @bp.route("/api/other_assets/add", methods=["POST"])
    @optional_auth
    def add_other_asset():
        return _jsonify_result(other_asset_add_handler())

    @bp.route("/api/other_assets/delete", methods=["POST"])
    @optional_auth
    def delete_other_asset():
        return _jsonify_result(other_asset_delete_handler())

    @bp.route("/api/other_assets/update", methods=["POST"])
    @optional_auth
    def update_other_asset():
        return _jsonify_result(other_asset_update_handler())

    @bp.route("/api/liabilities", methods=["GET"])
    @optional_auth
    def get_liabilities():
        return _jsonify_result(liabilities_payload_getter())

    @bp.route("/api/liabilities/add", methods=["POST"])
    @optional_auth
    def add_liability():
        return _jsonify_result(liability_add_handler())

    @bp.route("/api/liabilities/delete", methods=["POST"])
    @optional_auth
    def delete_liability():
        return _jsonify_result(liability_delete_handler())

    @bp.route("/api/liabilities/update", methods=["POST"])
    @optional_auth
    def update_liability():
        return _jsonify_result(liability_update_handler())

    return bp
