"""
资产调整记录路由

GET  /api/assets/<asset_type>/<asset_id>/adjustments  获取历史记录
POST /api/assets/<asset_type>/<asset_id>/adjustments  新增一条调整
"""
from __future__ import annotations

from flask import Blueprint, Response, jsonify


def _jsonify_result(result):
    if isinstance(result, Response):
        return result
    if isinstance(result, tuple) and len(result) == 2:
        payload, status = result
        if isinstance(payload, Response):
            return payload, status
        return jsonify(payload), status
    return jsonify(result)


def create_asset_adjustment_blueprint(
    *,
    optional_auth,
    adjustment_add_handler,
    adjustments_list_handler,
):
    bp = Blueprint("asset_adjustment_routes", __name__)

    @bp.route("/api/assets/<asset_type>/<int:asset_id>/adjustments", methods=["POST"])
    @optional_auth
    def add_adjustment(asset_type, asset_id):
        return _jsonify_result(adjustment_add_handler(asset_type, asset_id))

    @bp.route("/api/assets/<asset_type>/<int:asset_id>/adjustments", methods=["GET"])
    @optional_auth
    def list_adjustments(asset_type, asset_id):
        return _jsonify_result(adjustments_list_handler(asset_type, asset_id))

    return bp
