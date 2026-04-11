"""
投资持仓 / 交易 / 快照处理函数
"""
from datetime import datetime
import math
import os
from typing import Callable

from flask import g, jsonify, request
from werkzeug.datastructures import FileStorage

from core import portfolio_ocr
from core.request_trace import trace_request_stage


def _parse_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().lower()
    return text in {"1", "true", "yes", "y", "on"}


def _normalize_ocr_candidate_code(value: str) -> str:
    code = str(value or "").strip()
    if not code:
        return ""
    upper = code.upper()
    if upper.endswith(".HK"):
        return f"hk{upper[:-3]}".lower()
    lower = code.lower()
    if lower.startswith(("sh", "sz", "bj", "hk", "gb_", "f_", "ft_")):
        return lower
    return code


def _allow_local_ocr_demo() -> bool:
    return str(os.getenv("ALLOW_LOCAL_OCR_DEMO", "") or "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _is_local_request() -> bool:
    remote_addr = str(request.remote_addr or "").strip()
    return remote_addr in {"127.0.0.1", "::1", "localhost"}


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
    class InvalidLedgerIdError(ValueError):
        """请求里的 ledger_id 不合法。"""

    def _save_snapshot_async(user_id: str | None, stage_prefix: str) -> None:
        with trace_request_stage(f"{stage_prefix}.snapshot"):
            snapshot_saver_async(user_id)

    def _resolve_ledger_id(raw_value) -> int | None:
        """从请求中解析 ledger_id。None 表示不过滤（返回全部账本）。"""
        if raw_value is None or str(raw_value).strip() == '':
            return None
        try:
            ledger_id = int(raw_value)
        except (TypeError, ValueError):
            raise InvalidLedgerIdError("INVALID_LEDGER_ID")
        if ledger_id <= 0:
            raise InvalidLedgerIdError("INVALID_LEDGER_ID")
        return ledger_id

    def _invalid_ledger_response():
        return jsonify({"error": "Invalid ledger_id", "code": "INVALID_LEDGER_ID"}), 400

    def handle_ledgers_list():
        user_id = g.user_id
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401
        ledgers = db.get_ledgers(user_id)
        if not ledgers:
            default_id = db.get_default_ledger_id(user_id)
            ledgers = db.get_ledgers(user_id)
        return jsonify(ledgers)

    def handle_ledger_create():
        data = request.json
        user_id = g.user_id
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401
        if not data or not data.get('name'):
            return jsonify({"error": "Missing name"}), 400
        result = db.create_ledger(user_id, data['name'], data.get('description', ''))
        if result.get('ok'):
            return jsonify(result)
        status = 409 if result.get('code') == 'DUPLICATE_NAME' else 400
        return jsonify(result), status

    def handle_ledger_reorder():
        data = request.json or {}
        user_id = g.user_id
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401
        raw_ids = data.get('ledger_ids')
        if not isinstance(raw_ids, list) or not raw_ids:
            return jsonify({
                "ok": False,
                "code": "INVALID_LEDGER_IDS",
                "error": "ledger_ids 必须是非空数组",
            }), 400
        try:
            ledger_ids = [int(item) for item in raw_ids]
        except (TypeError, ValueError):
            return jsonify({
                "ok": False,
                "code": "INVALID_LEDGER_IDS",
                "error": "ledger_ids 只能包含正整数",
            }), 400
        if any(ledger_id <= 0 for ledger_id in ledger_ids):
            return jsonify({
                "ok": False,
                "code": "INVALID_LEDGER_IDS",
                "error": "ledger_ids 只能包含正整数",
            }), 400
        result = db.reorder_ledgers(user_id, ledger_ids)
        if result.get('ok'):
            return jsonify(result)
        status_map = {'INVALID_LEDGER_IDS': 400}
        return jsonify(result), status_map.get(result.get('code'), 400)

    def handle_ledger_update(ledger_id: int):
        data = request.json
        user_id = g.user_id
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401
        if not data or not data.get('name'):
            return jsonify({"error": "Missing name"}), 400
        result = db.update_ledger(ledger_id, user_id, data['name'], data.get('description', ''))
        if result.get('ok'):
            return jsonify(result)
        status_map = {'NOT_FOUND': 404, 'DUPLICATE_NAME': 409}
        return jsonify(result), status_map.get(result.get('code'), 400)

    def handle_ledger_delete(ledger_id: int):
        user_id = g.user_id
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401
        result = db.delete_ledger(ledger_id, user_id)
        if result.get('ok'):
            return jsonify(result)
        status_map = {'NOT_FOUND': 404, 'IS_DEFAULT': 400, 'HAS_HOLDINGS': 400}
        return jsonify(result), status_map.get(result.get('code'), 400)

    def build_portfolio_payload():
        asset_type = request.args.get('type', 'all')
        with_metrics = _parse_bool(request.args.get('with_metrics'))
        user_id = g.user_id
        try:
            ledger_id = _resolve_ledger_id(request.args.get('ledger_id'))
        except InvalidLedgerIdError:
            return _invalid_ledger_response()
        logger.info(f"API: get_portfolio called with type={asset_type}, user_id={user_id}, ledger_id={ledger_id}")
        data = portfolio_read_service.build_portfolio_payload(
            asset_type=asset_type,
            user_id=user_id,
            with_metrics=with_metrics,
            ledger_id=ledger_id,
        )
        logger.info(f"API: returning {len(data)} records")
        response = jsonify(data)
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0, private'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        response.headers['Vary'] = '*'
        return response

    def handle_portfolio_transactions():
        code = request.args.get('code', '').strip()
        user_id = g.user_id
        try:
            ledger_id = _resolve_ledger_id(request.args.get('ledger_id'))
        except InvalidLedgerIdError:
            return _invalid_ledger_response()
        if not code:
            return {"error": "Missing required parameter: code", "code": "MISSING_CODE"}, 400
        records = db.get_portfolio_transactions(code=code, user_id=user_id, ledger_id=ledger_id)
        return {"records": records}

    def handle_portfolio_ocr_parse():
        uploaded = request.files.get("file")
        if not isinstance(uploaded, FileStorage):
            return {
                "error": "请先上传截图文件",
                "code": "OCR_FILE_REQUIRED",
            }, 400
        if not uploaded.filename:
            return {
                "error": "请先选择截图文件",
                "code": "OCR_FILE_REQUIRED",
            }, 400

        try:
            with trace_request_stage("portfolio.ocr.read_file"):
                image_bytes = uploaded.stream.read()
            with trace_request_stage("portfolio.ocr.parse"):
                parsed = portfolio_ocr.parse_portfolio_asset_candidates(
                    db=db,
                    image_bytes=image_bytes,
                    filename=uploaded.filename or "",
                    content_type=uploaded.mimetype or uploaded.content_type or "",
                )
        except portfolio_ocr.PortfolioOcrError as exc:
            if _allow_local_ocr_demo() and _is_local_request():
                logger.warning(
                    "portfolio ocr fallback to local demo: code=%s message=%s",
                    exc.code,
                    exc.message,
                )
                parsed = portfolio_ocr.build_local_demo_result()
            else:
                return {"error": exc.message, "code": exc.code}, exc.status_code
        except Exception as exc:
            logger.exception("portfolio ocr parse failed: %s", exc)
            return {
                "error": "截图识别失败，请稍后重试",
                "code": "OCR_PARSE_FAILED",
            }, 500

        normalized_items = []
        for item in parsed.items:
            code = str(item.get("code") or "").strip()
            name = str(item.get("name") or "").strip()
            normalized = (
                portfolio_identity_normalizer(code, "", name)
                if code
                else {"code": "", "name": name}
            )
            normalized_items.append(
                {
                    "name": normalized.get("name") or name,
                    "code": _normalize_ocr_candidate_code(normalized.get("code") or code),
                    "qty": item.get("qty"),
                    "price": item.get("price"),
                    "confidence": item.get("confidence") or 0.0,
                    "note": item.get("note") or "",
                }
            )

        return {
            "items": normalized_items,
            "warnings": parsed.warnings,
            "raw_text": parsed.raw_text,
        }

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
        except (TypeError, ValueError):
            return idempotent_response(
                'portfolio_add',
                user_id,
                request_id,
                {"error": "Invalid value", "code": "INVALID_VALUE"},
                400,
            )

        if (not math.isfinite(qty)) or (not math.isfinite(price)):
            return idempotent_response(
                'portfolio_add',
                user_id,
                request_id,
                {"error": "Invalid value", "code": "INVALID_VALUE"},
                400,
            )
        if qty <= 0:
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
        data['adjustment'] = 0.0
        data['asset_type'] = normalized['asset_type']
        try:
            ledger_id = _resolve_ledger_id(data.get('ledger_id'))
        except InvalidLedgerIdError:
            return _invalid_ledger_response()
        if ledger_id is None and user_id:
            ledger_id = db.get_default_ledger_id(user_id)

        with trace_request_stage("portfolio.add.write", asset_type=data.get('asset_type')):
            success = db.add_asset(data, user_id, ledger_id=ledger_id)
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
                if field == 'adjustment':
                    return idempotent_response(
                        'portfolio_update',
                        user_id,
                        request_id,
                        {"error": "Legacy adjustment updates are disabled", "code": "UNSUPPORTED_FIELD"},
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
                if (not math.isfinite(qty)) or (not math.isfinite(price)):
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
            mod_ledger_id = _resolve_ledger_id(data.get('ledger_id'))
            if mod_ledger_id is None and user_id:
                mod_ledger_id = db.get_default_ledger_id(user_id)

            with trace_request_stage("portfolio.modify.write"):
                detail = db.modify_asset(
                    data['code'],
                    qty,
                    price,
                    None,
                    note=str(data.get('note') or '').strip(),
                    user_id=user_id,
                    return_detail=True,
                    ledger_id=mod_ledger_id,
                )
            if detail and detail.get('ok'):
                operation = {
                    'op_type': 'modify',
                    'code': data['code'],
                    'before_asset': detail.get('before_asset'),
                    'tx_id': None,
                    'ledger_event_id': None,
                    'correction_log_id': detail.get('correction_log_id'),
                    'ledger_id': mod_ledger_id,
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
        except InvalidLedgerIdError:
            return _invalid_ledger_response()
        except ValueError:
            return idempotent_response(
                'portfolio_modify',
                user_id,
                request_id,
                {"error": "Invalid value", "code": "INVALID_VALUE"},
                400,
            )

    def handle_portfolio_adjustment_event():
        data = request.json
        user_id = g.user_id
        request_id = str((data or {}).get('request_id', '')).strip()

        if not data or 'code' not in data or 'event_type' not in data or 'amount' not in data:
            return jsonify({"error": "Missing required fields"}), 400

        dedup_hit, dedup_payload, dedup_status = idempotency_begin(
            'portfolio_adjustment_event',
            user_id,
            request_id,
        )
        if dedup_hit:
            return jsonify(dedup_payload), dedup_status

        try:
            with trace_request_stage("portfolio.adjustment_event.validate"):
                event_type = str(data.get('event_type') or '').strip()
                note = str(data.get('note') or '').strip()
                raw_amount = float(data.get('amount'))
                if not math.isfinite(raw_amount):
                    return idempotent_response(
                        'portfolio_adjustment_event',
                        user_id,
                        request_id,
                        {"error": "Invalid value", "code": "INVALID_VALUE"},
                        400,
                    )
                if event_type not in {'dividend', 'fee', 'tax'}:
                    return idempotent_response(
                        'portfolio_adjustment_event',
                        user_id,
                        request_id,
                        {"error": "Unsupported adjustment event type", "code": "UNSUPPORTED_EVENT_TYPE"},
                        400,
                    )
                if raw_amount <= 0:
                    return idempotent_response(
                        'portfolio_adjustment_event',
                        user_id,
                        request_id,
                        {"error": "Invalid value", "code": "INVALID_VALUE"},
                        400,
                    )
                amount = raw_amount if event_type == 'dividend' else -raw_amount

            adj_ledger_id = _resolve_ledger_id(data.get('ledger_id'))
            if adj_ledger_id is None and user_id:
                adj_ledger_id = db.get_default_ledger_id(user_id)

            with trace_request_stage("portfolio.adjustment_event.write", event_type=event_type):
                detail = db.add_portfolio_adjustment_event(
                    code=str(data.get('code') or '').strip(),
                    event_type=event_type,
                    amount=amount,
                    note=note,
                    curr=data.get('curr'),
                    user_id=user_id,
                    return_detail=True,
                    ledger_id=adj_ledger_id,
                )

            if detail and detail.get('ok'):
                operation = {
                    'op_type': 'adjustment_event',
                    'code': data['code'],
                    'before_asset': detail.get('before_asset'),
                    'tx_id': None,
                    'ledger_event_id': detail.get('ledger_event_id'),
                    'ledger_id': adj_ledger_id,
                }
                payload = undo_decorator({"status": "ok"}, user_id, operation)
                _save_snapshot_async(user_id, "portfolio.adjustment_event")
                return idempotent_response(
                    'portfolio_adjustment_event',
                    user_id,
                    request_id,
                    payload,
                )

            error_code = (detail or {}).get('code', 'PORTFOLIO_ADJUSTMENT_EVENT_FAILED')
            error_message = (detail or {}).get('error', 'Failed to add portfolio adjustment event')
            status_code = 404 if error_code == 'ASSET_NOT_FOUND' else 500
            return idempotent_response(
                'portfolio_adjustment_event',
                user_id,
                request_id,
                {"error": error_message, "code": error_code},
                status_code,
            )
        except InvalidLedgerIdError:
            return _invalid_ledger_response()
        except ValueError:
            return idempotent_response(
                'portfolio_adjustment_event',
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

        snapshot_payload = {
            **data,
            "day_pnl": float(data.get("snapshot_day_pnl", data.get("day_pnl", 0.0)) or 0.0),
        }
        with trace_request_stage("snapshot.save.write"):
            success = db.save_daily_snapshot(snapshot_payload, user_id)
        if success:
            snapshot_date = str(data.get("date") or data.get("snapshot_date") or "").strip() or datetime.now().strftime('%Y-%m-%d')
            source = str(data.get("market_breakdown_source") or "exact")
            confidence_raw = data.get("market_breakdown_confidence", 1.0)
            try:
                confidence = float(confidence_raw)
            except Exception:
                confidence = 1.0
            meta_by_market = data.get("market_breakdown_meta")
            if not isinstance(meta_by_market, dict):
                meta_by_market = None
            day_pnl_by_market = data.get("snapshot_day_pnl_by_market") or data.get("day_pnl_by_market")
            if isinstance(day_pnl_by_market, dict):
                with trace_request_stage("snapshot.save.market_breakdown", item_count=len(day_pnl_by_market)):
                    breakdown_ok = db.save_daily_snapshot_market_breakdown(
                        date_str=snapshot_date,
                        day_pnl_by_market=day_pnl_by_market,
                        total_day_pnl=float(snapshot_payload.get("day_pnl", 0.0) or 0.0),
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

        try:
            del_ledger_id = _resolve_ledger_id((data or {}).get('ledger_id'))
        except InvalidLedgerIdError:
            return _invalid_ledger_response()
        if del_ledger_id is None and user_id:
            del_ledger_id = db.get_default_ledger_id(user_id)

        with trace_request_stage("portfolio.delete.write"):
            success = db.delete_asset(data['code'], user_id, ledger_id=del_ledger_id)
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

        try:
            delc_ledger_id = _resolve_ledger_id((data or {}).get('ledger_id'))
        except InvalidLedgerIdError:
            return _invalid_ledger_response()
        if delc_ledger_id is None and user_id:
            delc_ledger_id = db.get_default_ledger_id(user_id)

        with trace_request_stage("portfolio.delete_corrective.write"):
            result = db.delete_asset_corrective(data['code'], user_id, ledger_id=delc_ledger_id)
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
            buy_ledger_id = _resolve_ledger_id(data.get('ledger_id'))
            if buy_ledger_id is None and user_id:
                buy_ledger_id = db.get_default_ledger_id(user_id)

            with trace_request_stage("portfolio.buy.write"):
                detail = db.buy_asset(data['code'], price, qty, user_id, return_detail=True, ledger_id=buy_ledger_id)

            if detail and detail.get('ok'):
                operation = {
                    'op_type': 'buy',
                    'code': data['code'],
                    'before_asset': detail.get('before_asset'),
                    'tx_id': detail.get('tx_id'),
                    'ledger_id': buy_ledger_id,
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
        except InvalidLedgerIdError:
            return _invalid_ledger_response()
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

        if qty <= 0:
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

        try:
            bwc_ledger_id = _resolve_ledger_id(data.get('ledger_id'))
        except InvalidLedgerIdError:
            return _invalid_ledger_response()
        if bwc_ledger_id is None and user_id:
            bwc_ledger_id = db.get_default_ledger_id(user_id)

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
                ledger_id=bwc_ledger_id,
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
                'ledger_id': bwc_ledger_id,
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
            sell_ledger_id = _resolve_ledger_id(data.get('ledger_id'))
            if sell_ledger_id is None and user_id:
                sell_ledger_id = db.get_default_ledger_id(user_id)

            with trace_request_stage("portfolio.sell.write"):
                detail = db.sell_asset(data['code'], price, qty, user_id, return_detail=True, ledger_id=sell_ledger_id)

            if detail and detail.get('ok'):
                operation = {
                    'op_type': 'sell',
                    'code': data['code'],
                    'before_asset': detail.get('before_asset'),
                    'tx_id': detail.get('tx_id'),
                    'ledger_event_id': detail.get('ledger_event_id'),
                    'ledger_id': sell_ledger_id,
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
        except InvalidLedgerIdError:
            return _invalid_ledger_response()
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

        try:
            stc_ledger_id = _resolve_ledger_id(data.get('ledger_id'))
        except InvalidLedgerIdError:
            return _invalid_ledger_response()
        if stc_ledger_id is None and user_id:
            stc_ledger_id = db.get_default_ledger_id(user_id)

        with trace_request_stage("portfolio.sell_to_cash.asset_lookup"):
            asset = db.get_asset(code, user_id, ledger_id=stc_ledger_id)
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
                ledger_id=stc_ledger_id,
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
                'ledger_id': stc_ledger_id,
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
        "portfolio_adjustment_event": handle_portfolio_adjustment_event,
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
        "portfolio_transactions": handle_portfolio_transactions,
        "portfolio_ocr_parse": handle_portfolio_ocr_parse,
        "ledgers_list": handle_ledgers_list,
        "ledger_create": handle_ledger_create,
        "ledger_reorder": handle_ledger_reorder,
        "ledger_update": handle_ledger_update,
        "ledger_delete": handle_ledger_delete,
    }
