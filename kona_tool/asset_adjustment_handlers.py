"""
资产调整记录处理函数
"""
from __future__ import annotations

from typing import Callable

from flask import g, jsonify, request
from core.request_trace import trace_request_stage

_VALID_ASSET_TYPES = {'cash', 'other', 'liability'}
_VALID_MODES = {'add', 'sub', 'correct'}


def create_asset_adjustment_handlers(
    *,
    db,
    logger,
    snapshot_saver_async: Callable[[str | None], None],
):
    def _current_user_id():
        return getattr(g, "user_id", None)

    def adjustment_add_handler(asset_type, asset_id):
        if asset_type not in _VALID_ASSET_TYPES:
            return jsonify({"error": "Invalid asset type", "code": "INVALID_ASSET_TYPE"}), 400

        data = request.json
        if not data:
            return jsonify({"error": "Missing request body", "code": "MISSING_BODY"}), 400

        mode = data.get("mode")
        if mode not in _VALID_MODES:
            return jsonify({"error": "mode must be 'add', 'sub' or 'correct'", "code": "INVALID_MODE"}), 400

        target_amount = None
        if mode == "correct":
            try:
                target_amount = float(data["target_amount"])
            except (KeyError, ValueError, TypeError):
                return jsonify({"error": "Invalid target amount", "code": "INVALID_TARGET_AMOUNT"}), 400
            allow_zero = asset_type == "cash"
            if target_amount < 0 or (not allow_zero and target_amount <= 0):
                return jsonify({"error": "Invalid target amount", "code": "INVALID_TARGET_AMOUNT"}), 400
            delta = 1.0
        else:
            try:
                delta = float(data["delta"])
            except (KeyError, ValueError, TypeError):
                return jsonify({"error": "Invalid delta", "code": "INVALID_DELTA"}), 400

        if delta <= 0:
            return jsonify({"error": "delta must be positive", "code": "INVALID_DELTA"}), 400

        name = str(data.get("name") or "").strip() or None
        raw_curr = str(data.get("curr") or "").strip().upper()
        curr = raw_curr if raw_curr in {"CNY", "USD", "HKD"} else None
        note = str(data.get("note") or "").strip()
        user_id = _current_user_id()

        with trace_request_stage("asset_adjustment.write"):
            result = db.add_asset_adjustment(
                asset_type=asset_type,
                asset_id=asset_id,
                mode=mode,
                delta=delta,
                note=note,
                name=name,
                curr=curr,
                user_id=user_id,
                target_amount=target_amount,
            )

        if result is None:
            logger.warning(
                "[asset_adjustment_add_failed] type=%s id=%s user=%s",
                asset_type, asset_id, user_id,
            )
            return jsonify({"error": "Failed to save adjustment", "code": "ADJUSTMENT_FAILED"}), 400

        snapshot_saver_async(user_id)

        return jsonify({
            "status": "ok",
            "balance_after": result["balance_after"],
            "adjustment_id": result["id"],
        })

    def adjustments_list_handler(asset_type, asset_id):
        if asset_type not in _VALID_ASSET_TYPES:
            return jsonify({"error": "Invalid asset type", "code": "INVALID_ASSET_TYPE"}), 400

        user_id = _current_user_id()
        with trace_request_stage("asset_adjustment.list"):
            records = db.get_asset_adjustments(
                asset_type=asset_type,
                asset_id=asset_id,
                user_id=user_id,
            )

        return jsonify({"adjustments": records})

    return {
        "adjustment_add": adjustment_add_handler,
        "adjustments_list": adjustments_list_handler,
    }
