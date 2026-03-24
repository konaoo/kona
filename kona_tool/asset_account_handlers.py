"""
资产账户 / 交易记录处理函数
"""
from __future__ import annotations

from typing import Callable

from flask import g, jsonify, request
from core.request_trace import trace_request_stage


def create_asset_account_payload_handlers(
    *,
    db,
    logger,
    snapshot_saver_async: Callable[[str | None], None],
):
    def _current_user_id():
        return getattr(g, "user_id", None)

    def _save_snapshot_async(user_id, stage_prefix: str) -> None:
        with trace_request_stage(f"{stage_prefix}.snapshot"):
            snapshot_saver_async(user_id)

    def _handle_asset_add(add_func, asset_type, user_id=None):
        data = request.json

        with trace_request_stage("asset.add.payload", asset_type=asset_type):
            if not data or 'name' not in data or 'amount' not in data:
                logger.warning(
                    "[asset_add_invalid_request] type=%s user_id=%s reason=missing_required_fields payload=%s",
                    asset_type,
                    user_id,
                    data,
                )
                return jsonify({"error": "Missing required fields", "code": "MISSING_REQUIRED_FIELDS"}), 400

        try:
            logger.info(
                "[asset_add_request] type=%s user_id=%s name=%s amount=%s curr=%s",
                asset_type,
                user_id,
                data.get('name'),
                data.get('amount'),
                data.get('curr', 'CNY'),
            )
            with trace_request_stage("asset.add.validate", asset_type=asset_type):
                amount = float(data['amount'])
                allow_zero = asset_type == "cash asset"
                if amount < 0 or (not allow_zero and amount <= 0):
                    logger.warning(
                        "[asset_add_invalid_amount] type=%s user_id=%s amount=%s",
                        asset_type,
                        user_id,
                        data.get('amount'),
                    )
                    return jsonify({"error": "Invalid amount", "code": "INVALID_AMOUNT"}), 400
            with trace_request_stage("asset.add.write", asset_type=asset_type):
                success = add_func(
                    data['name'],
                    amount,
                    data.get('curr', 'CNY'),
                    user_id,
                    str(data.get('icon', '') or '').strip(),
                )
            if success:
                _save_snapshot_async(user_id, "asset.add")
                logger.info("[asset_add_success] type=%s user_id=%s", asset_type, user_id)
                return jsonify({"status": "ok"})
            logger.error("[asset_add_failed] type=%s user_id=%s", asset_type, user_id)
            return jsonify({"error": f"Failed to add {asset_type}", "code": "ASSET_ADD_FAILED"}), 500
        except ValueError:
            logger.warning(
                "[asset_add_invalid_amount] type=%s user_id=%s amount=%s",
                asset_type,
                user_id,
                data.get('amount'),
            )
            return jsonify({"error": "Invalid amount", "code": "INVALID_AMOUNT"}), 400
        except Exception as exc:
            logger.exception(
                "[asset_add_exception] type=%s user_id=%s error=%s",
                asset_type,
                user_id,
                exc,
            )
            return jsonify({"error": f"Failed to add {asset_type}", "code": "ASSET_ADD_EXCEPTION"}), 500

    def _handle_asset_delete(delete_func, asset_type, user_id=None):
        data = request.json

        with trace_request_stage("asset.delete.payload", asset_type=asset_type):
            if not data or 'id' not in data:
                logger.warning(
                    "[asset_delete_invalid_request] type=%s user_id=%s reason=missing_id payload=%s",
                    asset_type,
                    user_id,
                    data,
                )
                return jsonify({"error": "Missing id", "code": "MISSING_ID"}), 400

        try:
            with trace_request_stage("asset.delete.validate", asset_type=asset_type):
                asset_id = int(data['id'])
            logger.info(
                "[asset_delete_request] type=%s user_id=%s id=%s",
                asset_type,
                user_id,
                asset_id,
            )
            with trace_request_stage("asset.delete.write", asset_type=asset_type):
                success = delete_func(asset_id, user_id)
            if success:
                _save_snapshot_async(user_id, "asset.delete")
                logger.info(
                    "[asset_delete_success] type=%s user_id=%s id=%s",
                    asset_type,
                    user_id,
                    asset_id,
                )
                return jsonify({"status": "ok"})
            logger.error(
                "[asset_delete_failed] type=%s user_id=%s id=%s",
                asset_type,
                user_id,
                asset_id,
            )
            return jsonify({"error": f"Failed to delete {asset_type}", "code": "ASSET_DELETE_FAILED"}), 500
        except ValueError:
            logger.warning(
                "[asset_delete_invalid_id] type=%s user_id=%s id=%s",
                asset_type,
                user_id,
                data.get('id'),
            )
            return jsonify({"error": "Invalid id", "code": "INVALID_ID"}), 400
        except Exception as exc:
            logger.exception(
                "[asset_delete_exception] type=%s user_id=%s error=%s",
                asset_type,
                user_id,
                exc,
            )
            return jsonify({"error": f"Failed to delete {asset_type}", "code": "ASSET_DELETE_EXCEPTION"}), 500

    def _handle_asset_update(update_func, asset_type, user_id=None):
        data = request.json

        with trace_request_stage("asset.update.payload", asset_type=asset_type):
            if not data or 'id' not in data or 'name' not in data or 'amount' not in data:
                logger.warning(
                    "[asset_update_invalid_request] type=%s user_id=%s reason=missing_required_fields payload=%s",
                    asset_type,
                    user_id,
                    data,
                )
                return jsonify({"error": "Missing required fields", "code": "MISSING_REQUIRED_FIELDS"}), 400

        try:
            with trace_request_stage("asset.update.validate", asset_type=asset_type):
                asset_id = int(data['id'])
                amount = float(data['amount'])
                allow_zero = asset_type == "cash asset"
                if amount < 0 or (not allow_zero and amount <= 0):
                    logger.warning(
                        "[asset_update_invalid_amount] type=%s user_id=%s id=%s amount=%s",
                        asset_type,
                        user_id,
                        data.get('id'),
                        data.get('amount'),
                    )
                    return jsonify({"error": "Invalid amount", "code": "INVALID_VALUE"}), 400
            logger.info(
                "[asset_update_request] type=%s user_id=%s id=%s name=%s amount=%s curr=%s",
                asset_type,
                user_id,
                asset_id,
                data.get('name'),
                amount,
                data.get('curr', 'CNY'),
            )
            with trace_request_stage("asset.update.write", asset_type=asset_type):
                success = update_func(
                    asset_id,
                    data['name'],
                    amount,
                    data.get('curr', 'CNY'),
                    user_id,
                    str(data.get('icon', '') or '').strip(),
                )
            if success:
                _save_snapshot_async(user_id, "asset.update")
                logger.info(
                    "[asset_update_success] type=%s user_id=%s id=%s",
                    asset_type,
                    user_id,
                    asset_id,
                )
                return jsonify({"status": "ok"})
            logger.error(
                "[asset_update_failed] type=%s user_id=%s id=%s",
                asset_type,
                user_id,
                asset_id,
            )
            return jsonify({"error": f"Failed to update {asset_type}", "code": "ASSET_UPDATE_FAILED"}), 500
        except ValueError:
            logger.warning(
                "[asset_update_invalid_value] type=%s user_id=%s id=%s amount=%s",
                asset_type,
                user_id,
                data.get('id'),
                data.get('amount'),
            )
            return jsonify({"error": "Invalid value", "code": "INVALID_VALUE"}), 400
        except Exception as exc:
            logger.exception(
                "[asset_update_exception] type=%s user_id=%s error=%s",
                asset_type,
                user_id,
                exc,
            )
            return jsonify({"error": f"Failed to update {asset_type}", "code": "ASSET_UPDATE_EXCEPTION"}), 500

    def build_transactions_payload():
        limit = request.args.get('limit', 100, type=int)
        user_id = _current_user_id()
        return db.get_transactions(limit, user_id)

    def build_cash_assets_payload():
        user_id = _current_user_id()
        return db.get_cash_assets(user_id)

    def handle_cash_asset_add():
        user_id = _current_user_id()
        return _handle_asset_add(db.add_cash_asset, "cash asset", user_id)

    def handle_cash_asset_delete():
        user_id = _current_user_id()
        return _handle_asset_delete(db.delete_cash_asset, "cash asset", user_id)

    def handle_cash_asset_update():
        user_id = _current_user_id()
        return _handle_asset_update(db.update_cash_asset, "cash asset", user_id)

    def build_other_assets_payload():
        user_id = _current_user_id()
        return db.get_other_assets(user_id)

    def handle_other_asset_add():
        user_id = _current_user_id()
        return _handle_asset_add(db.add_other_asset, "other asset", user_id)

    def handle_other_asset_delete():
        user_id = _current_user_id()
        return _handle_asset_delete(db.delete_other_asset, "other asset", user_id)

    def handle_other_asset_update():
        user_id = _current_user_id()
        return _handle_asset_update(db.update_other_asset, "other asset", user_id)

    def build_liabilities_payload():
        user_id = _current_user_id()
        return db.get_liabilities(user_id)

    def handle_liability_add():
        user_id = _current_user_id()
        return _handle_asset_add(db.add_liability, "liability", user_id)

    def handle_liability_delete():
        user_id = _current_user_id()
        return _handle_asset_delete(db.delete_liability, "liability", user_id)

    def handle_liability_update():
        user_id = _current_user_id()
        return _handle_asset_update(db.update_liability, "liability", user_id)

    return {
        "transactions": build_transactions_payload,
        "cash_assets": build_cash_assets_payload,
        "cash_asset_add": handle_cash_asset_add,
        "cash_asset_delete": handle_cash_asset_delete,
        "cash_asset_update": handle_cash_asset_update,
        "other_assets": build_other_assets_payload,
        "other_asset_add": handle_other_asset_add,
        "other_asset_delete": handle_other_asset_delete,
        "other_asset_update": handle_other_asset_update,
        "liabilities": build_liabilities_payload,
        "liability_add": handle_liability_add,
        "liability_delete": handle_liability_delete,
        "liability_update": handle_liability_update,
    }
