"""
投资持仓 / 交易 / 快照处理函数
"""
from __future__ import annotations

from datetime import datetime
import math
from typing import Callable

from flask import g, jsonify, request
from core.request_trace import trace_request_stage

def _parse_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().lower()
    return text in {"1", "true", "yes", "y", "on"}


def create_portfolio_payload_handlers(
    *,
    db,
    logger,
    portfolio_read_service,
    rates_getter: Callable[[], dict],
    convert_amount: Callable[[float, str, str, dict], float],
    snapshot_saver_async: Callable[[str | None], None],
    portfolio_identity_normalizer: Callable[[str, str, str], dict],
    idempotency_begin: Callable[[str, str, str], tuple[bool, dict, int]],
    idempotent_response: Callable[[str, str, str, dict, int], tuple],
    undo_decorator: Callable[[dict, str, dict], dict],
    undo_claim: Callable[[str, str], tuple[dict | None, tuple | None]],
    undo_release: Callable[[str, str], None],
    take_snapshot_func: Callable[[str | None], bool],
):
    def _save_snapshot_async(user_id: str | None, stage_prefix: str) -> None:
        with trace_request_stage(f"{stage_prefix}.snapshot"):
            snapshot_saver_async(user_id)

    def build_portfolio_payload():
        asset_type = request.args.get('type', 'all')
        with_metrics = _parse_bool(request.args.get('with_metrics'))
        user_id = g.user_id
        logger.info(f"API: get_portfolio called with type={asset_type}, user_id={user_id}")
        data = portfolio_read_service.build_portfolio_payload(
            asset_type=asset_type,
            user_id=user_id,
            with_metrics=with_metrics,
        )
        logger.info(f"API: returning {len(data)} records")
        response = jsonify(data)
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0, private'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        response.headers['Vary'] = '*'
        return response

    def handle_portfolio_add():
        data = request.json
        user_id = g.user_id
        request_id = str((data or {}).get('request_id', '')).strip()

        if not data or 'code' not in data or 'qty' not in data or 'price' not in data:
            return jsonify({"error": "Missing required fields"}), 400

        dedup_hit, dedup_payload, dedup_status = idempotency_begin('portfolio_add', user_id, request_id)
        if dedup_hit:
            return jsonify(dedup_payload), dedup_status

        with trace_request_stage("portfolio.add.normalize"):
            normalized = portfolio_identity_normalizer(
                data['code'],
                data.get('curr', ''),
                data.get('name', ''),
            )

        try:
            with trace_request_stage("portfolio.add.validate"):
                qty = float(data.get('qty'))
                price = float(data.get('price'))
                adjustment = float(data.get('adjustment', 0.0))
        except (TypeError, ValueError):
            return idempotent_response(
                'portfolio_add',
                user_id,
                request_id,
                {"error": "Invalid value", "code": "INVALID_VALUE"},
                400,
            )

        if (not math.isfinite(qty)) or (not math.isfinite(price)) or (not math.isfinite(adjustment)):
            return idempotent_response(
                'portfolio_add',
                user_id,
                request_id,
                {"error": "Invalid value", "code": "INVALID_VALUE"},
                400,
            )
        if qty <= 0 or price <= 0:
            return idempotent_response(
                'portfolio_add',
                user_id,
                request_id,
                {"error": "Invalid value", "code": "INVALID_VALUE"},
                400,
            )

        data['code'] = normalized['code']
        data['curr'] = normalized['curr']
        data['name'] = normalized['name']
        data['qty'] = qty
        data['price'] = price
        data['adjustment'] = adjustment
        data['asset_type'] = normalized['asset_type']

        with trace_request_stage("portfolio.add.write", asset_type=data.get('asset_type')):
            success = db.add_asset(data, user_id)
        if success:
            _save_snapshot_async(user_id, "portfolio.add")
            return idempotent_response('portfolio_add', user_id, request_id, {"status": "ok"})
        return idempotent_response(
            'portfolio_add',
            user_id,
            request_id,
            {"error": "Failed to add asset", "code": "ASSET_ADD_FAILED"},
            500,
        )

    def handle_portfolio_update():
        data = request.json
        user_id = g.user_id
        request_id = str((data or {}).get('request_id', '')).strip()

        if not data or 'code' not in data or 'field' not in data or 'val' not in data:
            return jsonify({"error": "Missing required fields"}), 400

        dedup_hit, dedup_payload, dedup_status = idempotency_begin('portfolio_update', user_id, request_id)
        if dedup_hit:
            return jsonify(dedup_payload), dedup_status

        try:
            with trace_request_stage("portfolio.update.validate"):
                val = float(data['val'])
                if not math.isfinite(val):
                    return idempotent_response(
                        'portfolio_update',
                        user_id,
                        request_id,
                        {"error": "Invalid value", "code": "INVALID_VALUE"},
                        400,
                    )
                field = str(data.get('field') or '').strip()
                if field == 'price' and val <= 0:
                    return idempotent_response(
                        'portfolio_update',
                        user_id,
                        request_id,
                        {"error": "Invalid value", "code": "INVALID_VALUE"},
                        400,
                    )
                if field == 'qty' and val <= 0:
                    return idempotent_response(
                        'portfolio_update',
                        user_id,
                        request_id,
                        {"error": "Invalid value", "code": "INVALID_VALUE"},
                        400,
                    )
            with trace_request_stage("portfolio.update.write", field=data.get('field')):
                success = db.update_asset(data['code'], data['field'], val, user_id)
            if success:
                _save_snapshot_async(user_id, "portfolio.update")
                return idempotent_response('portfolio_update', user_id, request_id, {"status": "ok"})
            return idempotent_response(
                'portfolio_update',
                user_id,
                request_id,
                {"error": "Asset not found", "code": "ASSET_NOT_FOUND"},
                404,
            )
        except ValueError:
            return idempotent_response(
                'portfolio_update',
                user_id,
                request_id,
                {"error": "Invalid value", "code": "INVALID_VALUE"},
                400,
            )

    def handle_portfolio_modify():
        data = request.json
        user_id = g.user_id
        request_id = str((data or {}).get('request_id', '')).strip()

        if not data or 'code' not in data or 'qty' not in data or 'price' not in data:
            return jsonify({"error": "Missing required fields"}), 400

        dedup_hit, dedup_payload, dedup_status = idempotency_begin('portfolio_modify', user_id, request_id)
        if dedup_hit:
            return jsonify(dedup_payload), dedup_status

        try:
            with trace_request_stage("portfolio.modify.validate"):
                qty = float(data['qty'])
                price = float(data['price'])
                raw_adjustment = data.get('adjustment', None)
                adjustment = None if raw_adjustment is None else float(raw_adjustment)
                if (not math.isfinite(qty)) or (not math.isfinite(price)):
                    return idempotent_response(
                        'portfolio_modify',
                        user_id,
                        request_id,
                        {"error": "Invalid value", "code": "INVALID_VALUE"},
                        400,
                    )
                if adjustment is not None and (not math.isfinite(adjustment)):
                    return idempotent_response(
                        'portfolio_modify',
                        user_id,
                        request_id,
                        {"error": "Invalid value", "code": "INVALID_VALUE"},
                        400,
                    )
                if qty <= 0:
                    return idempotent_response(
                        'portfolio_modify',
                        user_id,
                        request_id,
                        {"error": "Invalid value", "code": "INVALID_VALUE"},
                        400,
                    )
            with trace_request_stage("portfolio.modify.write"):
                detail = db.modify_asset(
                    data['code'],
                    qty,
                    price,
                    adjustment,
                    user_id,
                    return_detail=True,
                )
            if detail and detail.get('ok'):
                operation = {
                    'op_type': 'modify',
                    'code': data['code'],
                    'before_asset': detail.get('before_asset'),
                    'tx_id': None,
                }
                payload = undo_decorator({"status": "ok"}, user_id, operation)
                _save_snapshot_async(user_id, "portfolio.modify")
                return idempotent_response('portfolio_modify', user_id, request_id, payload)

            error_code = (detail or {}).get('code', 'ASSET_NOT_FOUND')
            error_message = (detail or {}).get('error', 'Asset not found')
            status_code = 404 if error_code == 'ASSET_NOT_FOUND' else 500
            return idempotent_response(
                'portfolio_modify',
                user_id,
                request_id,
                {"error": error_message, "code": error_code},
                status_code,
            )
        except ValueError:
            return idempotent_response(
                'portfolio_modify',
                user_id,
                request_id,
                {"error": "Invalid value", "code": "INVALID_VALUE"},
                400,
            )

    def handle_snapshot_save():
        data = request.json
        user_id = g.user_id
        if not data:
            return jsonify({"error": "No data provided"}), 400

        with trace_request_stage("snapshot.save.write"):
            success = db.save_daily_snapshot(data, user_id)
        if success:
            day_pnl_by_market = data.get("day_pnl_by_market")
            if isinstance(day_pnl_by_market, dict):
                snapshot_date = str(data.get("date") or "").strip() or datetime.now().strftime('%Y-%m-%d')
                source = str(data.get("market_breakdown_source") or "exact")
                confidence_raw = data.get("market_breakdown_confidence", 1.0)
                try:
                    confidence = float(confidence_raw)
                except Exception:
                    confidence = 1.0
                meta_by_market = data.get("market_breakdown_meta")
                if not isinstance(meta_by_market, dict):
                    meta_by_market = None
                with trace_request_stage("snapshot.save.market_breakdown", item_count=len(day_pnl_by_market)):
                    breakdown_ok = db.save_daily_snapshot_market_breakdown(
                        date_str=snapshot_date,
                        day_pnl_by_market=day_pnl_by_market,
                        total_day_pnl=float(data.get("day_pnl", 0.0) or 0.0),
                        user_id=user_id,
                        source=source,
                        confidence=confidence,
                        meta_by_market=meta_by_market,
                    )
                if not breakdown_ok:
                    logger.warning(
                        "Failed to save market breakdown in /api/snapshot/save: user_id=%s date=%s",
                        user_id,
                        snapshot_date,
                    )
            return jsonify({"status": "ok"})
        return jsonify({"error": "Failed to save snapshot"}), 500

    def handle_snapshot_trigger():
        user_id = g.user_id
        with trace_request_stage("snapshot.trigger.write"):
            success = take_snapshot_func(user_id)
        if success:
            return jsonify({"status": "ok", "message": "Snapshot taken successfully"})
        return jsonify({"error": "Failed to take snapshot"}), 500

    def handle_snapshot_fix():
        data = request.json
        user_id = g.user_id
        if not data or 'dates' not in data:
            return jsonify({"error": "Missing dates"}), 400

        dates = data['dates']
        if not isinstance(dates, list):
            return jsonify({"error": "dates must be a list"}), 400

        with trace_request_stage("snapshot.fix.write", item_count=len(dates)):
            success = db.fix_snapshot_day_pnl(dates, user_id)
        if success:
            return jsonify({"status": "ok", "message": f"Fixed {len(dates)} records"})
        return jsonify({"error": "Failed to fix snapshots"}), 500

    def handle_portfolio_delete():
        data = request.json
        user_id = g.user_id
        request_id = str((data or {}).get('request_id', '')).strip()

        if not data or 'code' not in data:
            return jsonify({"error": "Missing code"}), 400

        dedup_hit, dedup_payload, dedup_status = idempotency_begin('portfolio_delete', user_id, request_id)
        if dedup_hit:
            return jsonify(dedup_payload), dedup_status

        with trace_request_stage("portfolio.delete.write"):
            success = db.delete_asset(data['code'], user_id)
        if success:
            _save_snapshot_async(user_id, "portfolio.delete")
            return idempotent_response('portfolio_delete', user_id, request_id, {"status": "ok"})
        return idempotent_response(
            'portfolio_delete',
            user_id,
            request_id,
            {"error": "Failed to delete asset", "code": "ASSET_DELETE_FAILED"},
            500,
        )

    def handle_portfolio_delete_corrective():
        data = request.json
        user_id = g.user_id
        request_id = str((data or {}).get('request_id', '')).strip()

        if not data or 'code' not in data:
            return jsonify({"error": "Missing code"}), 400

        dedup_hit, dedup_payload, dedup_status = idempotency_begin('portfolio_delete_corrective', user_id, request_id)
        if dedup_hit:
            return jsonify(dedup_payload), dedup_status

        with trace_request_stage("portfolio.delete_corrective.write"):
            result = db.delete_asset_corrective(data['code'], user_id)
        if result:
            _save_snapshot_async(user_id, "portfolio.delete_corrective")
            payload = {
                "status": "ok",
                "code": "CORRECTIVE_DELETE_DONE",
                "deleted": {
                    "portfolio": result.get('portfolio', 0),
                    "transactions": result.get('transactions', 0),
                    "snapshots": result.get('snapshots', 0),
                },
                "from_date": result.get('from_date'),
            }
            return idempotent_response('portfolio_delete_corrective', user_id, request_id, payload)
        return idempotent_response(
            'portfolio_delete_corrective',
            user_id,
            request_id,
            {"error": "Failed to delete asset corrective", "code": "ASSET_CORRECTIVE_DELETE_FAILED"},
            500,
        )

    def handle_portfolio_buy():
        data = request.json
        user_id = g.user_id
        request_id = str((data or {}).get('request_id', '')).strip()

        if not data or 'code' not in data or 'price' not in data or 'qty' not in data:
            return jsonify({"error": "Missing required fields"}), 400

        dedup_hit, dedup_payload, dedup_status = idempotency_begin('portfolio_buy', user_id, request_id)
        if dedup_hit:
            return jsonify(dedup_payload), dedup_status

        try:
            with trace_request_stage("portfolio.buy.validate"):
                price = float(data['price'])
                qty = float(data['qty'])
                if (not math.isfinite(price)) or (not math.isfinite(qty)) or price <= 0 or qty <= 0:
                    return idempotent_response(
                        'portfolio_buy',
                        user_id,
                        request_id,
                        {"error": "Invalid value", "code": "INVALID_VALUE"},
                        400,
                    )
            with trace_request_stage("portfolio.buy.write"):
                detail = db.buy_asset(data['code'], price, qty, user_id, return_detail=True)

            if detail and detail.get('ok'):
                operation = {
                    'op_type': 'buy',
                    'code': data['code'],
                    'before_asset': detail.get('before_asset'),
                    'tx_id': detail.get('tx_id'),
                }
                payload = undo_decorator({"status": "ok"}, user_id, operation)
                _save_snapshot_async(user_id, "portfolio.buy")
                return idempotent_response('portfolio_buy', user_id, request_id, payload)

            error_code = (detail or {}).get('code', 'ASSET_BUY_FAILED')
            error_message = (detail or {}).get('error', 'Failed to buy asset')
            status_code = 404 if error_code == 'ASSET_NOT_FOUND' else 500
            return idempotent_response(
                'portfolio_buy',
                user_id,
                request_id,
                {"error": error_message, "code": error_code},
                status_code,
            )
        except ValueError:
            return idempotent_response(
                'portfolio_buy',
                user_id,
                request_id,
                {"error": "Invalid value", "code": "INVALID_VALUE"},
                400,
            )

    def handle_portfolio_buy_with_cash():
        data = request.json
        user_id = g.user_id
        request_id = str((data or {}).get('request_id', '')).strip()
        raw_code = str((data or {}).get('code', '')).strip()

        required = ('code', 'price', 'qty', 'cash_asset_id')
        if not data or any(field not in data for field in required):
            return jsonify({"error": "Missing required fields"}), 400

        dedup_hit, dedup_payload, dedup_status = idempotency_begin('portfolio_buy_with_cash', user_id, request_id)
        if dedup_hit:
            return jsonify(dedup_payload), dedup_status

        try:
            price = float(data['price'])
            qty = float(data['qty'])
            cash_asset_id = int(data['cash_asset_id'])
        except (TypeError, ValueError):
            return idempotent_response(
                'portfolio_buy_with_cash',
                user_id,
                request_id,
                {"error": "Invalid value", "code": "INVALID_VALUE"},
                400,
            )

        if price <= 0 or qty <= 0:
            return idempotent_response(
                'portfolio_buy_with_cash',
                user_id,
                request_id,
                {"error": "Invalid value", "code": "INVALID_VALUE"},
                400,
            )

        with trace_request_stage("portfolio.buy_with_cash.normalize"):
            normalized = portfolio_identity_normalizer(
                data['code'],
                data.get('curr', ''),
                data.get('name', ''),
            )
        code = normalized['code']
        curr = normalized['curr']
        name = normalized['name']
        asset_type = normalized['asset_type']

        with trace_request_stage("portfolio.buy_with_cash.cash_lookup", cash_asset_id=cash_asset_id):
            cash_asset = db.get_cash_asset_by_id(cash_asset_id, user_id)
        if not cash_asset:
            return idempotent_response(
                'portfolio_buy_with_cash',
                user_id,
                request_id,
                {"error": "Cash account not found", "code": "CASH_ASSET_NOT_FOUND"},
                404,
            )

        invest_amount = price * qty
        cash_curr = cash_asset.get('curr', 'CNY')
        if str(curr).upper() == str(cash_curr).upper():
            cash_deduct_amount = invest_amount
        else:
            with trace_request_stage("portfolio.buy_with_cash.rates"):
                rates = rates_getter()
                cash_deduct_amount = convert_amount(invest_amount, curr, cash_curr, rates)
        if cash_deduct_amount <= 0:
            return idempotent_response(
                'portfolio_buy_with_cash',
                user_id,
                request_id,
                {"error": "Invalid cash deduction amount", "code": "INVALID_CASH_AMOUNT"},
                400,
            )

        with trace_request_stage("portfolio.buy_with_cash.write"):
            detail = db.buy_asset_with_cash(
                code=code,
                name=name,
                price=price,
                qty=qty,
                curr=curr,
                asset_type=asset_type,
                cash_asset_id=cash_asset_id,
                cash_deduct_amount=cash_deduct_amount,
                user_id=user_id,
                legacy_codes=[raw_code] if raw_code else None,
            )
        if detail and detail.get('ok'):
            operation_code = (
                ((detail.get('after_asset') or {}).get('code'))
                or ((detail.get('before_asset') or {}).get('code'))
                or code
            )
            operation = {
                'op_type': 'buy_with_cash',
                'code': operation_code,
                'before_asset': detail.get('before_asset'),
                'tx_id': detail.get('tx_id'),
                'cash_asset_id': detail.get('cash_asset_id'),
                'cash_before_amount': detail.get('cash_before_amount'),
            }
            payload = undo_decorator(
                {
                    "status": "ok",
                    "cash_deducted": detail.get('cash_deduct_amount'),
                    "cash_curr": detail.get('cash_curr'),
                },
                user_id,
                operation,
            )
            _save_snapshot_async(user_id, "portfolio.buy_with_cash")
            return idempotent_response('portfolio_buy_with_cash', user_id, request_id, payload)

        error_code = (detail or {}).get('code', 'ASSET_BUY_WITH_CASH_FAILED')
        error_message = (detail or {}).get('error', 'Failed to buy asset with cash')
        error_message_map = {
            'INVALID_VALUE': '数值不合法',
            'INVALID_CASH_AMOUNT': '扣款金额不合法',
            'INSUFFICIENT_CASH': '账户余额不足，请更换其他账户',
            'CASH_ASSET_NOT_FOUND': '现金账户不存在',
            'ASSET_BUY_WITH_CASH_FAILED': '现金买入失败，请稍后重试',
        }
        error_message = error_message_map.get(error_code, error_message)
        status_code = 500
        if error_code in ('INVALID_VALUE', 'INVALID_CASH_AMOUNT'):
            status_code = 400
        elif error_code == 'INSUFFICIENT_CASH':
            status_code = 400
        elif error_code == 'CASH_ASSET_NOT_FOUND':
            status_code = 404
        payload = {"error": error_message, "code": error_code}
        if detail and 'available' in detail:
            payload['available'] = detail.get('available')
        if detail and 'required' in detail:
            payload['required'] = detail.get('required')
        if detail and 'cash_curr' in detail:
            payload['cash_curr'] = detail.get('cash_curr')
        return idempotent_response(
            'portfolio_buy_with_cash',
            user_id,
            request_id,
            payload,
            status_code,
        )

    def handle_portfolio_sell():
        data = request.json
        user_id = g.user_id
        request_id = str((data or {}).get('request_id', '')).strip()

        if not data or 'code' not in data or 'price' not in data or 'qty' not in data:
            return jsonify({"error": "Missing required fields"}), 400

        dedup_hit, dedup_payload, dedup_status = idempotency_begin('portfolio_sell', user_id, request_id)
        if dedup_hit:
            return jsonify(dedup_payload), dedup_status

        try:
            with trace_request_stage("portfolio.sell.validate"):
                price = float(data['price'])
                qty = float(data['qty'])
                if (not math.isfinite(price)) or (not math.isfinite(qty)) or price <= 0 or qty <= 0:
                    return idempotent_response(
                        'portfolio_sell',
                        user_id,
                        request_id,
                        {"error": "Invalid value", "code": "INVALID_VALUE"},
                        400,
                    )
            with trace_request_stage("portfolio.sell.write"):
                detail = db.sell_asset(data['code'], price, qty, user_id, return_detail=True)

            if detail and detail.get('ok'):
                operation = {
                    'op_type': 'sell',
                    'code': data['code'],
                    'before_asset': detail.get('before_asset'),
                    'tx_id': detail.get('tx_id'),
                    'ledger_event_id': detail.get('ledger_event_id'),
                }
                payload = undo_decorator({"status": "ok"}, user_id, operation)
                _save_snapshot_async(user_id, "portfolio.sell")
                return idempotent_response('portfolio_sell', user_id, request_id, payload)

            error_code = (detail or {}).get('code', 'ASSET_SELL_FAILED')
            error_message = (detail or {}).get('error', 'Failed to sell asset')
            if error_code in ('OVERSELL', 'INVALID_VALUE'):
                status_code = 400
            elif error_code == 'ASSET_NOT_FOUND':
                status_code = 404
            else:
                status_code = 500
            return idempotent_response(
                'portfolio_sell',
                user_id,
                request_id,
                {"error": error_message, "code": error_code},
                status_code,
            )
        except ValueError:
            return idempotent_response(
                'portfolio_sell',
                user_id,
                request_id,
                {"error": "Invalid value", "code": "INVALID_VALUE"},
                400,
            )

    def handle_portfolio_sell_to_cash():
        data = request.json
        user_id = g.user_id
        request_id = str((data or {}).get('request_id', '')).strip()

        required = ('code', 'price', 'qty', 'cash_asset_id')
        if not data or any(field not in data for field in required):
            return jsonify({"error": "Missing required fields"}), 400

        dedup_hit, dedup_payload, dedup_status = idempotency_begin('portfolio_sell_to_cash', user_id, request_id)
        if dedup_hit:
            return jsonify(dedup_payload), dedup_status

        try:
            price = float(data['price'])
            qty = float(data['qty'])
            cash_asset_id = int(data['cash_asset_id'])
        except (TypeError, ValueError):
            return idempotent_response(
                'portfolio_sell_to_cash',
                user_id,
                request_id,
                {"error": "Invalid value", "code": "INVALID_VALUE"},
                400,
            )

        if price <= 0 or qty <= 0:
            return idempotent_response(
                'portfolio_sell_to_cash',
                user_id,
                request_id,
                {"error": "Invalid value", "code": "INVALID_VALUE"},
                400,
            )

        code = str(data.get('code') or '').strip()
        if not code:
            return idempotent_response(
                'portfolio_sell_to_cash',
                user_id,
                request_id,
                {"error": "Missing required fields", "code": "MISSING_CODE"},
                400,
            )

        with trace_request_stage("portfolio.sell_to_cash.cash_lookup", cash_asset_id=cash_asset_id):
            cash_asset = db.get_cash_asset_by_id(cash_asset_id, user_id)
        if not cash_asset:
            return idempotent_response(
                'portfolio_sell_to_cash',
                user_id,
                request_id,
                {"error": "Cash account not found", "code": "CASH_ASSET_NOT_FOUND"},
                404,
            )

        with trace_request_stage("portfolio.sell_to_cash.asset_lookup"):
            asset = db.get_asset(code, user_id)
        if not asset:
            return idempotent_response(
                'portfolio_sell_to_cash',
                user_id,
                request_id,
                {"error": "Asset not found", "code": "ASSET_NOT_FOUND"},
                404,
            )

        sell_amount = price * qty
        asset_curr = str(asset.get('curr') or 'CNY')
        cash_curr = str(cash_asset.get('curr') or 'CNY')
        if asset_curr.upper() == cash_curr.upper():
            cash_add_amount = sell_amount
        else:
            with trace_request_stage("portfolio.sell_to_cash.rates"):
                rates = rates_getter()
                cash_add_amount = convert_amount(sell_amount, asset_curr, cash_curr, rates)
        if cash_add_amount <= 0:
            return idempotent_response(
                'portfolio_sell_to_cash',
                user_id,
                request_id,
                {"error": "Invalid cash amount", "code": "INVALID_CASH_AMOUNT"},
                400,
            )

        with trace_request_stage("portfolio.sell_to_cash.write"):
            detail = db.sell_asset_to_cash(
                code=code,
                price=price,
                qty=qty,
                cash_asset_id=cash_asset_id,
                cash_add_amount=cash_add_amount,
                user_id=user_id,
                return_detail=True,
            )
        if detail and detail.get('ok'):
            operation = {
                'op_type': 'sell_to_cash',
                'code': ((detail.get('before_asset') or {}).get('code')) or code,
                'before_asset': detail.get('before_asset'),
                'tx_id': detail.get('tx_id'),
                'ledger_event_id': detail.get('ledger_event_id'),
                'cash_asset_id': detail.get('cash_asset_id'),
                'cash_before_amount': detail.get('cash_before_amount'),
            }
            payload = undo_decorator(
                {
                    "status": "ok",
                    "cash_added": detail.get('cash_add_amount'),
                    "cash_curr": detail.get('cash_curr'),
                },
                user_id,
                operation,
            )
            _save_snapshot_async(user_id, "portfolio.sell_to_cash")
            return idempotent_response('portfolio_sell_to_cash', user_id, request_id, payload)

        error_code = (detail or {}).get('code', 'ASSET_SELL_TO_CASH_FAILED')
        error_message = (detail or {}).get('error', 'Failed to sell asset to cash')
        error_message_map = {
            'INVALID_VALUE': '数值不合法',
            'INVALID_CASH_AMOUNT': '回款金额不合法',
            'CASH_ASSET_NOT_FOUND': '现金账户不存在',
            'ASSET_NOT_FOUND': '资产不存在',
            'OVERSELL': '卖出数量超过持仓',
            'ASSET_SELL_TO_CASH_FAILED': '卖出失败，请稍后重试',
        }
        status_code = 500
        if error_code in ('INVALID_VALUE', 'INVALID_CASH_AMOUNT', 'OVERSELL'):
            status_code = 400
        elif error_code in ('CASH_ASSET_NOT_FOUND', 'ASSET_NOT_FOUND'):
            status_code = 404
        return idempotent_response(
            'portfolio_sell_to_cash',
            user_id,
            request_id,
            {"error": error_message_map.get(error_code, error_message), "code": error_code},
            status_code,
        )

    def handle_portfolio_undo():
        data = request.json
        user_id = g.user_id
        undo_token = str((data or {}).get('undo_token', '')).strip()
        operation, error_info = undo_claim(user_id, undo_token)
        if error_info:
            code, message, status_code = error_info
            return jsonify({"error": message, "code": code}), status_code

        with trace_request_stage("portfolio.undo.write"):
            result = db.undo_invest_operation(operation, user_id)
        if result and result.get('ok'):
            _save_snapshot_async(user_id, "portfolio.undo")
            return jsonify({"status": "ok", "code": "UNDO_DONE"})

        undo_release(user_id, undo_token)
        return jsonify({
            "error": (result or {}).get('error', 'Failed to undo operation'),
            "code": (result or {}).get('code', 'UNDO_FAILED'),
        }), 500

    return {
        "portfolio": build_portfolio_payload,
        "portfolio_add": handle_portfolio_add,
        "portfolio_update": handle_portfolio_update,
        "portfolio_modify": handle_portfolio_modify,
        "snapshot_save": handle_snapshot_save,
        "snapshot_trigger": handle_snapshot_trigger,
        "snapshot_fix": handle_snapshot_fix,
        "portfolio_delete": handle_portfolio_delete,
        "portfolio_delete_corrective": handle_portfolio_delete_corrective,
        "portfolio_buy": handle_portfolio_buy,
        "portfolio_buy_with_cash": handle_portfolio_buy_with_cash,
        "portfolio_sell": handle_portfolio_sell,
        "portfolio_sell_to_cash": handle_portfolio_sell_to_cash,
        "portfolio_undo": handle_portfolio_undo,
    }
