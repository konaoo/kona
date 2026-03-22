"""
投资持仓 / 交易 / 快照路由
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


def create_portfolio_blueprint(
    *,
    optional_auth,
    portfolio_payload_getter,
    portfolio_add_handler,
    portfolio_update_handler,
    portfolio_modify_handler,
    portfolio_adjustment_event_handler,
    portfolio_ocr_parse_handler,
    snapshot_save_handler,
    snapshot_trigger_handler,
    snapshot_fix_handler,
    portfolio_delete_handler,
    portfolio_delete_corrective_handler,
    portfolio_buy_handler,
    portfolio_buy_with_cash_handler,
    portfolio_sell_handler,
    portfolio_sell_to_cash_handler,
    portfolio_undo_handler,
    portfolio_transactions_handler,
    ledgers_list_handler=None,
    ledger_create_handler=None,
    ledger_update_handler=None,
    ledger_delete_handler=None,
):
    bp = Blueprint("portfolio_routes", __name__)

    @bp.route("/api/portfolio", methods=["GET"])
    @optional_auth
    def get_portfolio():
        return _jsonify_result(portfolio_payload_getter())

    @bp.route("/api/portfolio/add", methods=["POST"])
    @optional_auth
    def add_asset():
        return _jsonify_result(portfolio_add_handler())

    @bp.route("/api/portfolio/update", methods=["POST"])
    @optional_auth
    def update_asset():
        return _jsonify_result(portfolio_update_handler())

    @bp.route("/api/portfolio/modify", methods=["POST"])
    @optional_auth
    def modify_asset():
        return _jsonify_result(portfolio_modify_handler())

    @bp.route("/api/portfolio/adjustment_event", methods=["POST"])
    @optional_auth
    def add_adjustment_event():
        return _jsonify_result(portfolio_adjustment_event_handler())

    @bp.route("/api/portfolio/ocr_parse_asset", methods=["POST"])
    @optional_auth
    def parse_asset_from_screenshot():
        return _jsonify_result(portfolio_ocr_parse_handler())

    @bp.route("/api/snapshot/save", methods=["POST"])
    @optional_auth
    def save_snapshot():
        return _jsonify_result(snapshot_save_handler())

    @bp.route("/api/snapshot/trigger", methods=["POST"])
    @optional_auth
    def trigger_snapshot():
        return _jsonify_result(snapshot_trigger_handler())

    @bp.route("/api/snapshot/fix", methods=["POST"])
    @optional_auth
    def fix_snapshot():
        return _jsonify_result(snapshot_fix_handler())

    @bp.route("/api/portfolio/delete", methods=["POST"])
    @optional_auth
    def delete_asset():
        return _jsonify_result(portfolio_delete_handler())

    @bp.route("/api/portfolio/delete_corrective", methods=["POST"])
    @optional_auth
    def delete_asset_corrective():
        return _jsonify_result(portfolio_delete_corrective_handler())

    @bp.route("/api/portfolio/buy", methods=["POST"])
    @optional_auth
    def buy_asset():
        return _jsonify_result(portfolio_buy_handler())

    @bp.route("/api/portfolio/buy_with_cash", methods=["POST"])
    @optional_auth
    def buy_asset_with_cash():
        return _jsonify_result(portfolio_buy_with_cash_handler())

    @bp.route("/api/portfolio/sell", methods=["POST"])
    @optional_auth
    def sell_asset():
        return _jsonify_result(portfolio_sell_handler())

    @bp.route("/api/portfolio/sell_to_cash", methods=["POST"])
    @optional_auth
    def sell_asset_to_cash():
        return _jsonify_result(portfolio_sell_to_cash_handler())

    @bp.route("/api/portfolio/undo", methods=["POST"])
    @optional_auth
    def undo_portfolio_operation():
        return _jsonify_result(portfolio_undo_handler())

    @bp.route("/api/portfolio/transactions", methods=["GET"])
    @optional_auth
    def get_portfolio_transactions():
        return _jsonify_result(portfolio_transactions_handler())

    if ledgers_list_handler:
        @bp.route("/api/portfolio/ledgers", methods=["GET"])
        @optional_auth
        def list_ledgers():
            return _jsonify_result(ledgers_list_handler())

    if ledger_create_handler:
        @bp.route("/api/portfolio/ledgers", methods=["POST"])
        @optional_auth
        def create_ledger():
            return _jsonify_result(ledger_create_handler())

    if ledger_update_handler:
        @bp.route("/api/portfolio/ledgers/<int:ledger_id>", methods=["PUT"])
        @optional_auth
        def update_ledger(ledger_id):
            return _jsonify_result(ledger_update_handler(ledger_id))

    if ledger_delete_handler:
        @bp.route("/api/portfolio/ledgers/<int:ledger_id>", methods=["DELETE"])
        @optional_auth
        def delete_ledger(ledger_id):
            return _jsonify_result(ledger_delete_handler(ledger_id))

    return bp
