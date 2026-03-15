"""
投资持仓 / 交易 / 快照处理函数
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Callable, Dict, Iterable, List, Tuple

from flask import g, jsonify, request

from core.market_calendar import market_from_asset


def _to_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _first_positive(values: Iterable[float]) -> float:
    for value in values:
        if value > 0:
            return value
    return 0.0


def _parse_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().lower()
    return text in {"1", "true", "yes", "y", "on"}


def _compute_display_cost_price(price: float, qty: float, adjustment: float) -> float:
    if abs(qty) <= 1e-9:
        return price
    return (price * qty - adjustment) / qty


def build_portfolio_items_with_metrics(
    items: List[Dict],
    quotes: Dict[str, Tuple[float, float, float, float]],
    rates: Dict[str, float],
    market_statuses: Dict[str, Dict[str, float]],
    convert_amount: Callable[[float, str, str, Dict[str, float]], float],
) -> List[Dict]:
    enriched: List[Dict] = []
    for item in items:
        code = str(item.get("code") or "").strip()
        qty = _to_float(item.get("qty"))
        raw_cost_price = _to_float(item.get("price"))
        adjustment = _to_float(item.get("adjustment"))
        curr = str(item.get("curr") or "CNY").strip().upper()

        market = str(item.get("category_type") or item.get("asset_type") or "").lower()
        if market not in {"a", "hk", "us", "fund"}:
            market = market_from_asset(item)

        status = market_statuses.get(market, {}) if isinstance(market_statuses, dict) else {}
        market_open = bool(status.get("open"))
        market_trading_day = bool(status.get("trading_day"))
        market_status_reason = str(status.get("reason") or "")

        quote = quotes.get(code) or (0.0, 0.0, 0.0, 0.0)
        quote_price = _to_float(quote[0])
        quote_yclose = _to_float(quote[1])
        quote_change = _to_float(quote[2])
        quote_change_pct = _to_float(quote[3])

        quoted_current_price = _first_positive([quote_price, quote_yclose])
        current_price = _first_positive([quoted_current_price, raw_cost_price])

        nav_update_pending = code.lower().startswith(("f_", "ft_"))
        quote_ready = quote_price > 0
        quote_pending = (not nav_update_pending) and (not quote_ready)

        display_cost_price = _compute_display_cost_price(raw_cost_price, qty, adjustment)
        cost = raw_cost_price * qty
        value = current_price * qty
        total_pnl = value - cost + adjustment
        total_pnl_rate = (total_pnl / abs(cost) * 100) if abs(cost) > 0 else 0.0

        day_pnl_display_enabled = (not nav_update_pending) and current_price > 0 and quote_yclose > 0
        if day_pnl_display_enabled:
            delta = current_price - quote_yclose
            day_pnl_display = delta * qty
            day_pnl_rate_display = (delta / quote_yclose) * 100
        else:
            day_pnl_display = 0.0
            day_pnl_rate_display = 0.0
        day_pnl_aggregate_enabled = day_pnl_display_enabled and market_trading_day
        day_pnl_aggregate = day_pnl_display if day_pnl_aggregate_enabled else 0.0
        day_pnl_rate_aggregate = day_pnl_rate_display if day_pnl_aggregate_enabled else 0.0

        rate_to_cny = convert_amount(1.0, curr, "CNY", rates)
        value_cny = value * rate_to_cny
        cost_cny = cost * rate_to_cny
        total_pnl_cny = total_pnl * rate_to_cny
        day_pnl_cny = day_pnl_display * rate_to_cny
        day_pnl_aggregate_cny = day_pnl_aggregate * rate_to_cny

        enriched.append(
            {
                **item,
                "market": market,
                "market_open": market_open,
                "market_trading_day": market_trading_day,
                "market_status_reason": market_status_reason,
                "current_price": current_price,
                "yclose": quote_yclose,
                "display_cost_price": display_cost_price,
                "cost": cost,
                "raw_cost_total": cost,
                "value": value,
                "total_pnl": total_pnl,
                "total_pnl_rate": total_pnl_rate,
                "day_pnl": day_pnl_display,
                "day_pnl_rate": day_pnl_rate_display,
                "day_pnl_display": day_pnl_display,
                "day_pnl_rate_display": day_pnl_rate_display,
                "day_pnl_aggregate": day_pnl_aggregate,
                "day_pnl_rate_aggregate": day_pnl_rate_aggregate,
                "nav_update_pending": nav_update_pending,
                "quote_ready": quote_ready,
                "quote_pending": quote_pending,
                "day_pnl_display_enabled": day_pnl_display_enabled,
                "day_pnl_aggregate_enabled": day_pnl_aggregate_enabled,
                "rate_to_cny": rate_to_cny,
                "value_cny": value_cny,
                "cost_cny": cost_cny,
                "total_pnl_cny": total_pnl_cny,
                "day_pnl_cny": day_pnl_cny,
                "day_pnl_aggregate_cny": day_pnl_aggregate_cny,
                "quote_price": quote_price,
                "quote_change": quote_change,
                "quote_change_pct": quote_change_pct,
            }
        )

    total_value_cny = sum(
        float(row.get("value_cny") or 0.0) for row in enriched
    )
    if total_value_cny > 0:
        for row in enriched:
            value_cny = row.get("value_cny")
            if value_cny is None:
                row["position_pct"] = None
            else:
                row["position_pct"] = round(
                    float(value_cny) / total_value_cny * 100, 6
                )
    else:
        for row in enriched:
            row["position_pct"] = None

    return enriched


def create_portfolio_payload_handlers(
    *,
    db,
    logger,
    snapshot_saver_async: Callable[[str | None], None],
    portfolio_identity_normalizer: Callable[[str, str, str], dict],
    idempotency_begin: Callable[[str, str, str], tuple[bool, dict, int]],
    idempotent_response: Callable[[str, str, str, dict, int], tuple],
    undo_decorator: Callable[[dict, str, dict], dict],
    undo_claim: Callable[[str, str], tuple[dict | None, tuple | None]],
    undo_release: Callable[[str, str], None],
    take_snapshot_func: Callable[[str | None], bool],
    batch_get_prices_getter: Callable[[List[str]], Dict[str, Tuple[float, float, float, float]]],
    rates_getter: Callable[[], dict],
    convert_amount: Callable[[float, str, str, dict], float],
    market_status_getter: Callable[..., Dict],
):
    def build_portfolio_payload():
        asset_type = request.args.get('type', 'all')
        with_metrics = _parse_bool(request.args.get('with_metrics'))
        user_id = g.user_id
        logger.info(f"API: get_portfolio called with type={asset_type}, user_id={user_id}")
        data = db.get_portfolio(asset_type, user_id)
        if with_metrics:
            codes = [item.get("code") for item in data if item.get("code")]
            quotes = batch_get_prices_getter(codes) if codes else {}
            rates = rates_getter() or {}
            now_utc = datetime.now(timezone.utc)
            market_payload = market_status_getter(now_utc=now_utc, force_refresh=False)
            market_statuses = (
                market_payload.get("markets", {})
                if isinstance(market_payload, dict)
                else {}
            )
            data = build_portfolio_items_with_metrics(
                data,
                quotes,
                rates,
                market_statuses,
                convert_amount,
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

        normalized = portfolio_identity_normalizer(
            data['code'],
            data.get('curr', ''),
            data.get('name', ''),
        )

        try:
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

        success = db.add_asset(data, user_id)
        if success:
            snapshot_saver_async(user_id)
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
            success = db.update_asset(data['code'], data['field'], val, user_id)
            if success:
                snapshot_saver_async(user_id)
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

        if not data or 'code' not in data or 'qty' not in data or 'price' not in data or 'adjustment' not in data:
            return jsonify({"error": "Missing required fields"}), 400

        dedup_hit, dedup_payload, dedup_status = idempotency_begin('portfolio_modify', user_id, request_id)
        if dedup_hit:
            return jsonify(dedup_payload), dedup_status

        try:
            qty = float(data['qty'])
            price = float(data['price'])
            adjustment = float(data['adjustment'])
            if (not math.isfinite(qty)) or (not math.isfinite(price)) or (not math.isfinite(adjustment)):
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
                snapshot_saver_async(user_id)
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

        success = db.delete_asset(data['code'], user_id)
        if success:
            snapshot_saver_async(user_id)
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

        result = db.delete_asset_corrective(data['code'], user_id)
        if result:
            snapshot_saver_async(user_id)
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
            detail = db.buy_asset(data['code'], price, qty, user_id, return_detail=True)

            if detail and detail.get('ok'):
                operation = {
                    'op_type': 'buy',
                    'code': data['code'],
                    'before_asset': detail.get('before_asset'),
                    'tx_id': detail.get('tx_id'),
                }
                payload = undo_decorator({"status": "ok"}, user_id, operation)
                snapshot_saver_async(user_id)
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

        normalized = portfolio_identity_normalizer(
            data['code'],
            data.get('curr', ''),
            data.get('name', ''),
        )
        code = normalized['code']
        curr = normalized['curr']
        name = normalized['name']
        asset_type = normalized['asset_type']

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
        )
        if detail and detail.get('ok'):
            operation = {
                'op_type': 'buy_with_cash',
                'code': code,
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
            snapshot_saver_async(user_id)
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
            detail = db.sell_asset(data['code'], price, qty, user_id, return_detail=True)

            if detail and detail.get('ok'):
                operation = {
                    'op_type': 'sell',
                    'code': data['code'],
                    'before_asset': detail.get('before_asset'),
                    'tx_id': detail.get('tx_id'),
                }
                payload = undo_decorator({"status": "ok"}, user_id, operation)
                snapshot_saver_async(user_id)
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

    def handle_portfolio_undo():
        data = request.json
        user_id = g.user_id
        undo_token = str((data or {}).get('undo_token', '')).strip()
        operation, error_info = undo_claim(user_id, undo_token)
        if error_info:
            code, message, status_code = error_info
            return jsonify({"error": message, "code": code}), status_code

        result = db.undo_invest_operation(operation, user_id)
        if result and result.get('ok'):
            snapshot_saver_async(user_id)
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
        "portfolio_undo": handle_portfolio_undo,
    }
