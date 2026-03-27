"""
单价 / 批量报价 / 汇率 / 搜索处理函数
"""
from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Any, Callable, Dict

from flask import request

from core.request_trace import trace_request_stage


def create_quote_payload_handlers(
    *,
    get_price_getter: Callable[..., tuple[Any, Any, Any, Any, Optional[str]]],
    batch_get_prices_fast_getter: Callable[..., Dict[str, tuple[Any, Any, Any, Any, Optional[str]]]],
    rates_getter: Callable[[], Dict[str, Any]],
    search_getter: Callable[[str], Any],
    us_extended_quotes_getter: Callable[[list[str]], Dict[str, Any]],
    logger,
):
    def build_price_payload():
        code = request.args.get('code', '')
        if not code:
            return {"error": "Missing code"}, 400

        with trace_request_stage("quote.price", code=code):
            price, yclose, amt, chg, nav_date = get_price_getter(code)
        return {
            "price": price,
            "yclose": yclose,
            "amt": amt,
            "chg": chg,
            "nav_date": nav_date,
        }

    def build_prices_batch_payload():
        data = request.json or {}
        codes = data.get('codes', [])

        if not codes:
            return {"error": "Missing codes"}, 400

        timeout_ms_raw = (data.get('timeout_ms') if isinstance(data, dict) else None)
        timeout_seconds = None
        try:
            if timeout_ms_raw is not None:
                timeout_seconds = max(0.2, min(float(timeout_ms_raw) / 1000.0, 5.0))
        except Exception:
            timeout_seconds = None

        with trace_request_stage("quote.batch.base", code_count=len(codes)):
            results = batch_get_prices_fast_getter(codes, timeout_seconds=timeout_seconds)

        formatted_results = {}
        for code, (price, yclose, amt, chg, nav_date) in results.items():
            formatted_results[code] = {
                "price": price,
                "yclose": yclose,
                "amt": amt,
                "chg": chg,
                "nav_date": nav_date,
            }

        ft_retry_codes = []
        for code in codes:
            code_text = str(code or '').strip()
            if not code_text.lower().startswith('ft_'):
                continue
            current = formatted_results.get(code_text, {})
            if float(current.get("price") or 0.0) > 0:
                continue
            ft_retry_codes.append(code_text)

        with trace_request_stage("quote.batch.ft_retry", code_count=len(ft_retry_codes)):
            for code in ft_retry_codes:
                try:
                    price, yclose, amt, chg, nav_date = get_price_getter(code, use_cache=False)
                except Exception:
                    continue
                if float(price or 0.0) <= 0:
                    continue
                formatted_results[code] = {
                    "price": price,
                    "yclose": yclose,
                    "amt": amt,
                    "chg": chg,
                    "nav_date": nav_date,
                }

        us_codes = []
        symbol_by_code = {}
        for code in codes:
            code_text = str(code or '').strip()
            if not code_text:
                continue
            lower = code_text.lower()
            is_us_code = lower.startswith('gb_') or bool(re.fullmatch(r'[A-Za-z][A-Za-z\.\-]*', code_text))
            if not is_us_code:
                continue
            symbol = code_text[3:] if code_text.lower().startswith('gb_') else code_text
            symbol = symbol.strip().upper()
            if not symbol:
                continue
            us_codes.append(code_text)
            symbol_by_code[code_text] = symbol

        if symbol_by_code:
            with trace_request_stage("quote.batch.us_extended", symbol_count=len(symbol_by_code)):
                try:
                    symbols = list(set(symbol_by_code.values()))
                    us_quote_timeout_sec = 0.35
                    us_quotes: Dict[str, Any] = {}
                    executor = ThreadPoolExecutor(max_workers=1)
                    fut = executor.submit(us_extended_quotes_getter, symbols)
                    try:
                        us_quotes = fut.result(timeout=us_quote_timeout_sec)
                    except FuturesTimeoutError:
                        fut.cancel()
                        logger.debug(
                            "US extended quote timed out (symbols=%s timeout=%.1fs)",
                            len(symbols),
                            us_quote_timeout_sec,
                        )
                    finally:
                        executor.shutdown(wait=False, cancel_futures=True)
                    for code in us_codes:
                        symbol = symbol_by_code.get(code)
                        quote = us_quotes.get(symbol or '', {})
                        if not quote:
                            continue
                        base = dict(formatted_results.get(code, {}))
                        yclose = quote.get('yclose', base.get('yclose', 0))
                        if quote.get('price', 0) > 0:
                            base['price'] = quote.get('price', 0)
                        if yclose:
                            base['yclose'] = yclose
                        base['amt'] = quote.get('amt', base.get('amt', 0))
                        base['chg'] = quote.get('chg', base.get('chg', 0))
                        base['regular_price'] = quote.get('regular_price', 0)
                        base['premarket_price'] = quote.get('premarket_price', 0)
                        base['after_hours_price'] = quote.get('after_hours_price', 0)
                        base['session'] = quote.get('session', 'closed')
                        base['effective_session'] = quote.get('effective_session', base['session'])
                        base['extended_active'] = bool(quote.get('extended_active', False))
                        formatted_results[code] = base
                except Exception as exc:
                    logger.warning("US extended quote merge failed: %s", exc)

        return formatted_results

    def build_rates_payload():
        with trace_request_stage("quote.rates"):
            return rates_getter()

    def build_search_payload():
        query = request.args.get('q', '')
        with trace_request_stage("quote.search", query=query):
            return search_getter(query)

    return {
        "price": build_price_payload,
        "prices_batch": build_prices_batch_payload,
        "rates": build_rates_payload,
        "search": build_search_payload,
    }
