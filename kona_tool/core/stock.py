"""
股票数据获取模块
提供A股、港股、美股、指数等价格数据的获取功能
"""
import re
import logging
import time
import threading
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Tuple, Optional, Dict, Any, List
from bs4 import BeautifulSoup

import config
from .utils import safe_float, retry_on_failure, get_first_valid_price, monitored_http_get
from .fund import is_isin_format, normalize_nav_date
from .localization import translate_fund_name

logger = logging.getLogger(__name__)
_warn_throttle_lock = threading.Lock()
_warn_throttle_last: Dict[str, float] = {}


def _log_warn_throttled(key: str, message: str, interval_seconds: float = 60.0) -> None:
    now = time.monotonic()
    with _warn_throttle_lock:
        last = float(_warn_throttle_last.get(key, 0.0))
        if now - last < interval_seconds:
            return
        _warn_throttle_last[key] = now
    logger.warning(message)


def _sina_headers() -> Dict[str, Any]:
    headers = dict(config.HEADERS)
    headers.setdefault("Referer", "https://finance.sina.com.cn")
    return headers


def _normalize_quote_code(code: str) -> str:
    s = str(code or "").strip().lower()
    if s.isdigit() and len(s) == 6:
        return ('sh' if s[0] in ['5', '6', '9'] else 'sz') + s
    if s.isdigit() and len(s) == 5:
        return 'hk' + s
    if '.hk' in s:
        return 'hk' + s.replace('.hk', '')
    if s.startswith("hk"):
        digits = re.sub(r"\D", "", s)
        if digits:
            return "hk" + digits.zfill(5)
    if not any(x in s for x in ['sh', 'sz', 'hk', 'gb_', 's_', 'f_', 'of']):
        return 'gb_' + s
    return s


def _parse_locale_decimal(value: Any) -> float:
    text = str(value or "").strip()
    if not text:
        return 0.0
    text = text.replace("\xa0", "").replace(" ", "")
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        text = text.replace(",", ".")
    return safe_float(text)


def _get_eastmoney_cn_hk_price(code: str) -> Tuple[float, float, float, float, Optional[str]]:
    """
    东财 A/HK 行情（本地市场回退链路）。
    """
    s = str(code or "").strip().lower()
    secid = ""
    if s.startswith("sh") and len(s) >= 8:
        secid = f"1.{s[2:8]}"
    elif s.startswith("sz") and len(s) >= 8:
        secid = f"0.{s[2:8]}"
    elif s.startswith("hk"):
        digits = re.sub(r"\D", "", s)
        if digits:
            secid = f"116.{digits.zfill(5)}"
    if not secid:
        return 0.0, 0.0, 0.0, 0.0, None

    try:
        url = (
            "https://push2.eastmoney.com/api/qt/stock/get"
            f"?invt=2&fltt=2&fields=f43,f60&secid={secid}"
        )
        r = monitored_http_get(
            "eastmoney_cn_hk_stock",
            url,
            headers={"User-Agent": config.HEADERS.get("User-Agent", "Mozilla/5.0")},
            timeout=config.API_TIMEOUT,
        )
        data = (r.json() or {}).get("data") or {}
        curr = safe_float(data.get("f43"))
        yclose = safe_float(data.get("f60"))
        if curr <= 0:
            curr = yclose
        if curr > 0:
            if yclose <= 0:
                yclose = curr
            amt = curr - yclose
            chg = (amt / yclose * 100) if yclose > 0 else 0.0
            return curr, yclose, amt, chg, None
    except Exception as exc:
        logger.debug(f"Eastmoney CN/HK API error for {code}: {exc}")

    return 0.0, 0.0, 0.0, 0.0, None


def _normalize_us_symbol(code: str) -> str:
    return code.upper().replace('GB_', '').replace('US.', '').strip()


def _us_symbol_candidates(code: str) -> List[str]:
    primary = _normalize_us_symbol(code)
    if not primary:
        return []
    candidates: List[str] = []
    for symbol in [primary, primary.replace('.', '-'), primary.replace('-', '.')]:
        normalized = str(symbol or '').strip().upper()
        if normalized and normalized not in candidates:
            candidates.append(normalized)
    return candidates


def _normalize_market_state(raw_state: Any) -> str:
    state = str(raw_state or '').strip().lower()
    if 'pre' in state:
        return 'pre'
    if 'after' in state or 'post' in state:
        return 'post'
    if 'regular' in state:
        return 'regular'
    return 'closed'


def _build_nasdaq_effective_quote(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    primary = data.get("primaryData") or {}
    secondary = data.get("secondaryData") or {}
    summary = data.get("summaryData") or {}

    market_status = data.get("marketStatus")
    session = _normalize_market_state(market_status)

    primary_price = safe_float(primary.get("lastSalePrice"))
    primary_change = safe_float(primary.get("netChange"))
    primary_chg = safe_float(primary.get("percentageChange"))

    secondary_price = safe_float(secondary.get("lastSalePrice"))
    secondary_change = safe_float(secondary.get("netChange"))

    yclose = safe_float((summary.get("PreviousClose") or {}).get("value"))
    if yclose <= 0:
        if session in ("pre", "post") and secondary_price > 0 and secondary_change != 0:
            yclose = secondary_price - secondary_change
        elif primary_price > 0 and primary_change != 0:
            yclose = primary_price - primary_change
        elif secondary_price > 0:
            yclose = secondary_price
        elif primary_price > 0:
            yclose = primary_price

    regular_price = (
        secondary_price
        if session in ("pre", "post") and secondary_price > 0
        else primary_price
    )
    if regular_price <= 0 and yclose > 0:
        regular_price = yclose

    if regular_price <= 0 and primary_price <= 0:
        return None

    effective_price = regular_price
    effective_amt = (regular_price - yclose) if yclose > 0 else 0.0
    effective_chg = (
        (effective_amt / yclose * 100) if yclose > 0 else 0.0
    )
    effective_session = session
    extended_active = False
    pre_price = 0.0
    post_price = 0.0

    if session == 'pre' and primary_price > 0:
        pre_price = primary_price
        effective_price = primary_price
        effective_amt = (
            primary_change if primary_change != 0 else (primary_price - yclose)
        )
        effective_chg = primary_chg if primary_chg != 0 else (
            (effective_amt / yclose * 100) if yclose > 0 else 0.0
        )
        effective_session = 'pre'
        extended_active = True
    elif session == 'post' and primary_price > 0:
        post_price = primary_price
        effective_price = primary_price
        effective_amt = (
            primary_change if primary_change != 0 else (primary_price - yclose)
        )
        effective_chg = primary_chg if primary_chg != 0 else (
            (effective_amt / yclose * 100) if yclose > 0 else 0.0
        )
        effective_session = 'post'
        extended_active = True
    elif primary_price > 0:
        effective_price = primary_price
        effective_amt = (
            primary_change if primary_change != 0 else (primary_price - yclose)
        )
        effective_chg = primary_chg if primary_chg != 0 else (
            (effective_amt / yclose * 100) if yclose > 0 else 0.0
        )

    return {
        'price': effective_price,
        'yclose': yclose,
        'amt': effective_amt,
        'chg': effective_chg,
        'regular_price': regular_price,
        'premarket_price': pre_price,
        'after_hours_price': post_price,
        'session': session,
        'effective_session': effective_session,
        'extended_active': extended_active,
    }


def _get_nasdaq_extended_quote(symbol: str) -> Optional[Dict[str, Any]]:
    url = f"https://api.nasdaq.com/api/quote/{symbol}/info?assetclass=stocks"
    headers = config.API_HEADERS.get("default", config.HEADERS)
    r = monitored_http_get("nasdaq_quote", url, headers=headers, timeout=config.API_TIMEOUT)
    if r.status_code != 200:
        return None
    payload = r.json()
    data = payload.get("data") or {}
    if not isinstance(data, dict):
        return None
    return _build_nasdaq_effective_quote(data)


def get_us_extended_quotes(symbols: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    批量获取美股盘中/盘前/盘后报价（Nasdaq）。

    返回键使用规范化后的 symbol（大写，无 gb_ 前缀）。
    """
    normalized = []
    seen = set()
    for raw in symbols or []:
        symbol = _normalize_us_symbol(str(raw or ''))
        if not symbol or symbol in seen:
            continue
        seen.add(symbol)
        normalized.append(symbol)

    if not normalized:
        return {}

    result: Dict[str, Dict[str, Any]] = {}
    max_workers = min(6, len(normalized))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_symbol = {
            executor.submit(_get_nasdaq_extended_quote, symbol): symbol
            for symbol in normalized
        }
        for future in as_completed(future_to_symbol):
            symbol = future_to_symbol[future]
            try:
                quote = future.result()
            except Exception as exc:
                _log_warn_throttled(
                    "nasdaq_extended_quote",
                    f"Nasdaq extended quote API error: {exc}",
                )
                continue
            if quote:
                result[symbol] = quote
    return result


@retry_on_failure(max_retries=2, delay=0.5)
def get_nasdaq_price() -> Tuple[float, float, float, float, Optional[str]]:
    """
    获取纳斯达克指数价格
    
    Returns:
        (当前价格, 昨收, 涨跌额, 涨跌幅%)
    """
    try:
        url = config.API_ENDPOINTS["sina_stock"].format(code="gb_ixic")
        r = monitored_http_get("sina_us_index", url, headers=_sina_headers(), timeout=config.API_TIMEOUT)
        
        if '="' in r.text:
            data = r.text.split('="')[1].split(',')
            if len(data) > 1:
                curr = safe_float(data[1])
                yclose = safe_float(data[26])
                
                if curr <= 0:
                    curr = yclose
                if yclose <= 0 and len(data) > 2:
                    yclose = curr - safe_float(data[2])
                
                    return curr, yclose, curr - yclose, (curr - yclose) / yclose * 100, None
                    
    except Exception as e:
        logger.warning(f"Sina NASDAQ API error: {e}")
    
    try:
        url = "http://qt.gtimg.cn/q=us.IXIC"
        r = monitored_http_get("tencent_us_index", url, timeout=config.API_TIMEOUT)
        
        if r.status_code == 200 and '="' in r.text:
            data = r.text.split('="')[1].split('~')
            if len(data) > 3:
                curr = safe_float(data[3])
                yclose = safe_float(data[4])
                
                if curr <= 0:
                    curr = yclose
                if curr > 0 and yclose > 0:
                    return curr, yclose, curr - yclose, (curr - yclose) / yclose * 100, None
                    
    except Exception as e:
        logger.warning(f"Tencent NASDAQ API error: {e}")
    
    return 0.0, 0.0, 0.0, 0.0, None


@retry_on_failure(max_retries=2, delay=0.5)
def get_ft_fund_price(isin: str) -> Tuple[float, float, float, float, Optional[str]]:
    """
    从 Financial Times 获取基金/资产行情。
    支持自动处理 ISIN -> 基金/ETF 的页面重定向。
    """
    try:
        url = config.API_ENDPOINTS["ft_fund"].format(isin=isin.upper())
        headers = config.API_HEADERS["ft"]
        
        r = monitored_http_get("ft_fund", url, headers=headers, timeout=config.API_TIMEOUT)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # 1. 抓取现价
            # 优先尝试 tearsheet 详情页通用样式
            price_tag = soup.find('span', class_='mod-tearsheet-overview__quote__value') or \
                        soup.find('span', class_='mod-ui-data-list__value')
            
            if price_tag:
                curr = safe_float(price_tag.text)
                if curr > 0:
                    # 2. 抓取涨跌
                    chg_pct = 0.0
                    
                    # 尝试 tearsheet 样式
                    chg_tag = soup.find('span', class_='mod-tearsheet-overview__quote__chg')
                    if chg_tag:
                        # 格式可能是 " -0.083 / -1.01% "
                        chg_text = str(chg_tag.text or "").strip()
                        if '/' in chg_text:
                            pct_part = chg_text.split('/')[-1].replace('%', '').strip()
                            chg_pct = safe_float(pct_part)
                        else:
                            chg_pct = safe_float(chg_text.replace('%', ''))
                    else:
                        # 尝试 data-list 样式 (常见于重定向后的新布局)
                        # 寻找 Today's Change 标签附近的数值
                        labels = soup.find_all('span', class_='mod-ui-data-list__label')
                        for label in labels:
                            if "Today's Change" in label.text:
                                value_tag = label.find_next_sibling('span', class_='mod-ui-data-list__value')
                                if value_tag:
                                    chg_text = str(value_tag.text or "").strip()
                                    if '/' in chg_text:
                                        pct_part = chg_text.split('/')[-1].replace('%', '').strip()
                                        chg_pct = safe_float(pct_part)
                                    else:
                                        chg_pct = safe_float(chg_text.replace('%', ''))
                                break
                    
                    # 3. 抓取日期 (NAV as of)
                    price_date = None
                    # 尝试多种可能的标签和类名
                    date_tag = soup.find('span', class_='mod-ui-data-delay__date') or \
                                soup.find('span', class_='mod-tearsheet-overview__quote__date') or \
                                soup.find('div', class_='mod-ui-data-delay')
                    
                    if date_tag:
                        price_date = str(date_tag.text or "").strip()
                        # 清理前缀如 "as of " 或 "Data delayed at least 15 minutes, as of "
                        if "as of " in price_date:
                            price_date = price_date.split("as of ")[-1].strip()
                        if price_date.endswith('.'):
                            price_date = price_date[:-1]
                    
                    if not price_date:
                        # 备选：正则匹配常见日期格式 如 "Mar 26 2026"
                        date_match = re.search(r'as of ([A-Z][a-z]{2}\s+\d{1,2}\s+\d{4})', r.text)
                        if date_match:
                            price_date = date_match.group(1)
                    
                    yclose = curr / (1 + chg_pct / 100) if abs(1 + chg_pct / 100) > 1e-9 else curr
                    return curr, yclose, curr - yclose, chg_pct, normalize_nav_date(price_date)
                    
    except Exception as e:
        _log_warn_throttled("ft_fund_api", f"FT fund API error for {isin}: {e}")
    
    return 0.0, 0.0, 0.0, 0.0, None


def get_ft_metadata(isin: str) -> Dict[str, str]:
    """
    通过 ISIN 获取基金/资产的元数据（名称、币种）。
    """
    try:
        url = config.API_ENDPOINTS["ft_fund"].format(isin=isin.upper())
        headers = config.API_HEADERS["ft"]
        
        r = monitored_http_get("ft_metadata", url, headers=headers, timeout=config.API_TIMEOUT)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # 1. 抓取名称
            name_tag = soup.find('h1', class_='mod-tearsheet-overview__header__name') or \
                       soup.find('h1', class_='mod-tearsheet-add-to-watchlist__title') or \
                       soup.find('h1', class_='mod-tearsheet-overview__header__title')
            raw_name = str(name_tag.text or "").strip() if name_tag else f"ISIN: {isin.upper()}"
            name = translate_fund_name(raw_name)
            
            # 2. 抓取币种
            currency = "USD"  # 默认
            curr_tag = soup.find('span', class_='mod-tearsheet-overview__header__price-currency')
            if curr_tag:
                currency = str(curr_tag.text or "").strip().replace('Price (', '').replace(')', '').upper()
            else:
                # 从 Data List 标签中尝试解析，如 "Price (HKD)"
                labels = soup.find_all('span', class_='mod-ui-data-list__label')
                for label in labels:
                    if "Price (" in label.text:
                        match = re.search(r'Price \(([A-Z]+)\)', label.text)
                        if match:
                            currency = match.group(1).upper()
                            break
            
            # 3. 抓取价格与涨跌
            price = 0.0
            chg_pct = 0.0
            
            price_tag = soup.find('span', class_='mod-tearsheet-overview__quote__value') or \
                        soup.find('span', class_='mod-ui-data-list__value')
            if price_tag:
                price = safe_float(price_tag.text)
                
            chg_tag = soup.find('span', class_='mod-tearsheet-overview__quote__chg')
            if chg_tag:
                chg_text = str(chg_tag.text or "").strip()
                if '/' in chg_text:
                    pct_part = chg_text.split('/')[-1].replace('%', '').strip()
                    chg_pct = safe_float(pct_part)
                else:
                    chg_pct = safe_float(chg_text.replace('%', ''))
            else:
                # 备选路径：从 mod-ui-data-list__label 查找
                labels = soup.find_all('span', class_='mod-ui-data-list__label')
                for label in labels:
                    if "Today's Change" in label.text:
                        value_tag = label.find_next_sibling('span', class_='mod-ui-data-list__value')
                        if value_tag:
                            chg_text = str(value_tag.text or "").strip()
                            if '/' in chg_text:
                                pct_part = chg_text.split('/')[-1].replace('%', '').strip()
                                chg_pct = safe_float(pct_part)
                            else:
                                chg_pct = safe_float(chg_text.replace('%', ''))
                        break
            
            return {
                "name": name,
                "currency": currency,
                "isin": isin.upper(),
                "price": price,
                "chg_pct": chg_pct
            }
    except Exception as e:
        logger.debug(f"FT metadata fetch error for {isin}: {e}")
    
    return {}


@retry_on_failure(max_retries=2, delay=0.5)
def get_us_stock_price(code: str) -> Tuple[float, float, float, float, Optional[str]]:
    """
    获取美股价格
    
    Args:
        code: 美股代码（如 gb_bili）
        
    Returns:
        (当前价格, 昨收, 涨跌额, 涨跌幅%)
    """
    symbols = _us_symbol_candidates(code)
    if not symbols:
        return 0.0, 0.0, 0.0, 0.0, None

    # 对 BRK.B 这类带点号/横杠的美股，优先走更宽松的 Nasdaq，
    # 避免先被新浪/东财这些符号兼容差的链路拖慢或拿空。
    if any(('.' in symbol or '-' in symbol) for symbol in symbols):
        for symbol in symbols:
            for assetclass in ["stocks", "etf"]:
                quote = _get_nasdaq_quote_relaxed(symbol, assetclass)
                if quote:
                    curr, yclose, amt, pct, quote_date = quote
                    return curr, yclose, amt, pct, quote_date

    for symbol in symbols:
        try:
            url = config.API_ENDPOINTS["sina_stock"].format(code=f"gb_{symbol.lower()}")
            r = monitored_http_get("sina_us_stock", url, headers=_sina_headers(), timeout=config.API_TIMEOUT)

            if '="' in r.text:
                data = r.text.split('="')[1].split(',')
                curr = safe_float(data[1])
                yclose = safe_float(data[26])

                if curr == 0:
                    curr = safe_float(data[21])  # 盘后价

                if curr > 0:
                    if yclose <= 0:
                        yclose = curr
                        return curr, yclose, curr - yclose, (curr - yclose) / yclose * 100, None

        except Exception as e:
            _log_warn_throttled("sina_us_stock", f"Sina US stock API error: {e}")

    for symbol in symbols:
        try:
            for secid in [f"105.{symbol}", f"106.{symbol}"]:
                url = f"https://push2.eastmoney.com/api/qt/stock/get?invt=2&fltt=2&fields=f43,f60&secid={secid}"
                r = monitored_http_get(
                    "eastmoney_us_stock",
                    url,
                    headers={'User-Agent': config.HEADERS['User-Agent']},
                    timeout=config.API_TIMEOUT,
                )
                data = r.json().get('data')

                if data:
                    curr = safe_float(data.get('f43'))
                    yclose = safe_float(data.get('f60'))
                    if curr <= 0:
                        curr = yclose
                    if curr > 0:
                        return curr, yclose, curr - yclose, (curr - yclose) / yclose * 100, None

        except Exception as e:
            _log_warn_throttled("eastmoney_us_stock", f"Eastmoney US stock API error: {e}")

    # Nasdaq 备用接口（美股股票优先，ETF 次之）
    try:
        for symbol in symbols:
            for assetclass in ["stocks", "etf"]:
                quote = _get_nasdaq_quote(symbol, assetclass)
                if quote:
                    curr, yclose, amt, pct, quote_date = quote
                    return curr, yclose, amt, pct, quote_date
    except Exception as e:
        _log_warn_throttled("nasdaq_quote", f"Nasdaq quote API error: {e}")

    # 对 BRK.B 这类带点号/横杠的美股，再给一次更宽松的纳斯达克兜底。
    if any(('.' in symbol or '-' in symbol) for symbol in symbols):
        for symbol in symbols:
            for assetclass in ["stocks", "etf"]:
                quote = _get_nasdaq_quote_relaxed(symbol, assetclass)
                if quote:
                    curr, yclose, amt, pct, quote_date = quote
                    return curr, yclose, amt, pct, quote_date

    return 0.0, 0.0, 0.0, 0.0, None


@retry_on_failure(max_retries=2, delay=0.5)
def get_boursorama_fund_price(isin: str) -> Tuple[float, float, float, float, Optional[str]]:
    """
    通过 Boursorama 搜索页按 ISIN 解析海外基金净值。
    """
    try:
        query = str(isin or "").strip().upper()
        if not query:
            return 0.0, 0.0, 0.0, 0.0, None

        url = f"https://www.boursorama.com/recherche/?query={query}"
        headers = dict(config.HEADERS)
        headers.setdefault("Referer", "https://www.boursorama.com/")

        r = monitored_http_get("boursorama_fund", url, headers=headers, timeout=config.API_TIMEOUT)
        if r.status_code != 200:
            return 0.0, 0.0, 0.0, 0.0, None

        final_url = str(getattr(r, "url", "") or "")
        if "/bourse/opcvm/cours/" not in final_url:
            return 0.0, 0.0, 0.0, 0.0, None

        text = str(r.text or "")
        price_match = re.search(r'data-ist-last>\s*([^<]+)\s*<', text, re.I)
        if not price_match:
            return 0.0, 0.0, 0.0, 0.0, None

        curr = _parse_locale_decimal(price_match.group(1))
        if curr <= 0:
            return 0.0, 0.0, 0.0, 0.0, None

        variation_match = re.search(r'data-ist-variation>\s*([^<]+)\s*<', text, re.I)
        chg = _parse_locale_decimal(variation_match.group(1)) if variation_match else 0.0
        yclose = curr
        base = 1 + chg / 100
        if abs(chg) > 1e-9 and abs(base) > 1e-9:
            inferred = curr / base
            if inferred > 0:
                yclose = inferred

        amt = curr - yclose
        chg_pct = (amt / yclose * 100) if yclose > 0 else 0.0
        return curr, yclose, amt, chg_pct, None
    except Exception as e:
        _log_warn_throttled("boursorama_fund_api", f"Boursorama fund API error: {e}")

    return 0.0, 0.0, 0.0, 0.0, None


@retry_on_failure(max_retries=2, delay=0.5)
def get_marketscreener_fund_price(isin: str) -> Tuple[float, float, float, float, Optional[str]]:
    """
    通过 MarketScreener 搜索页按 ISIN 解析海外基金净值。

    这里优先拿 schema.org 的 Offer price，通常比 Boursorama 更接近基金公司确认净值。
    若页面未暴露昨收/涨跌，则保守回填为 0，避免伪造日涨跌。
    """
    try:
        query = str(isin or "").strip().upper()
        if not query:
            return 0.0, 0.0, 0.0, 0.0, None

        url = f"https://www.marketscreener.com/search/?q={query}"
        headers = {
            "User-Agent": config.HEADERS.get("User-Agent", "Mozilla/5.0"),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.marketscreener.com/",
        }

        r = monitored_http_get(
            "marketscreener_fund",
            url,
            headers=headers,
            timeout=config.API_TIMEOUT,
        )
        if r.status_code != 200:
            return 0.0, 0.0, 0.0, 0.0, None

        text = str(r.text or "")
        link_match = re.search(r'(/quote/fund/[^"\']+)', text, re.I)
        if not link_match:
            return 0.0, 0.0, 0.0, 0.0, None

        detail_url = f"https://www.marketscreener.com{link_match.group(1)}"
        detail = monitored_http_get(
            "marketscreener_fund",
            detail_url,
            headers=headers,
            timeout=config.API_TIMEOUT,
        )
        if detail.status_code != 200:
            return 0.0, 0.0, 0.0, 0.0, None

        detail_text = str(detail.text or "")
        identifier_pattern = re.compile(
            r'"identifier"\s*:\s*"%s"' % re.escape(query),
            re.I,
        )
        match = identifier_pattern.search(detail_text)
        if not match:
            return 0.0, 0.0, 0.0, 0.0, None

        window_start = max(0, match.start() - 600)
        window_end = min(len(detail_text), match.end() + 1200)
        window = detail_text[window_start:window_end]

        price_match = re.search(r'"price"\s*:\s*"([^"]+)"', window, re.I)
        curr = safe_float(price_match.group(1)) if price_match else 0.0
        if curr <= 0:
            return 0.0, 0.0, 0.0, 0.0, None

        prev_match = re.search(
            r'"(?:previousClose|previous_close|yclose)"\s*:\s*"([^"]+)"',
            window,
            re.I,
        )
        yclose = safe_float(prev_match.group(1)) if prev_match else curr
        if yclose <= 0:
            yclose = curr

        amt = curr - yclose
        chg_pct = (amt / yclose * 100) if yclose > 0 else 0.0
        return curr, yclose, amt, chg_pct, None
    except Exception as e:
        _log_warn_throttled(
            "marketscreener_fund_api",
            f"MarketScreener fund API error: {e}",
        )

    return 0.0, 0.0, 0.0, 0.0, None


@retry_on_failure(max_retries=2, delay=0.5)
def get_blackrock_fund_price(isin: str) -> Tuple[float, float, float, float, Optional[str]]:
    """
    解析贝莱德官方产品页的基金净值。

    目前先覆盖线上已持有、且官方页面可稳定访问的 ISIN。
    官方页有明确“净值截至”与“一天净值变动”字段，优先级应高于三方站点。
    """
    pages = {
        "LU1116320737": "https://www.blackrock.com/cn/products/270404/bgf-global-enhanced-equity-yield-fund-a6-usd",
    }
    try:
        query = str(isin or "").strip().upper()
        url = pages.get(query)
        if not url:
            return 0.0, 0.0, 0.0, 0.0, None

        headers = {
            "User-Agent": config.HEADERS.get("User-Agent", "Mozilla/5.0"),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://www.blackrock.com/",
        }

        r = requests.get(url, headers=headers, timeout=max(5, int(config.API_TIMEOUT)))
        if r.status_code != 200:
            return 0.0, 0.0, 0.0, 0.0, None

        text = str(r.text or "")
        amount_match = re.search(
            r'<span class="header-nav-label navAmount">\s*(净值截至\s*[^<]*)</span>\s*'
            r'<span class="header-nav-data">\s*([^<]*?)\s*([0-9]+(?:\.[0-9]+)?)\s*</span>',
            text,
            re.I | re.S,
        )
        if not amount_match:
            return 0.0, 0.0, 0.0, 0.0, None

        raw_date = amount_match.group(1)
        curr = safe_float(amount_match.group(3))
        if curr <= 0:
            return 0.0, 0.0, 0.0, 0.0, None

        change_match = re.search(
            r'<li class="navAmountChange[^"]*"[^>]*>.*?'
            r'<span class="header-nav-data">\s*[^<]*?\s*([+-]?[0-9]+(?:\.[0-9]+)?)\s*'
            r'\(\s*([+-]?[0-9]+(?:\.[0-9]+)?)%\s*\)\s*</span>',
            text,
            re.I | re.S,
        )
        amt = safe_float(change_match.group(1)) if change_match else 0.0
        chg_pct = safe_float(change_match.group(2)) if change_match else 0.0
        yclose = curr - amt
        if yclose <= 0:
            yclose = curr
            amt = 0.0
            chg_pct = 0.0
        
        # 规格化日期
        price_date = normalize_nav_date(raw_date)
        return curr, yclose, amt, chg_pct, price_date

    except Exception as e:
        _log_warn_throttled("blackrock_fund_api", f"BlackRock fund API error: {e}")

    return 0.0, 0.0, 0.0, 0.0, None


def get_us_asset_type(code: str) -> Optional[str]:
    """
    判断美股资产类型：ETF -> fund / 股票 -> us
    """
    s = code.upper().replace('GB_', '').replace('US.', '')
    try:
        quote = _get_nasdaq_quote(s, "etf")
        if quote:
            return "fund"
    except Exception as e:
        logger.debug(f"Nasdaq ETF detect error for {code}: {e}")
    try:
        quote = _get_nasdaq_quote(s, "stocks")
        if quote:
            return "us"
    except Exception as e:
        logger.debug(f"Nasdaq stock detect error for {code}: {e}")
    return None


def _get_nasdaq_quote(symbol: str, assetclass: str) -> Optional[Tuple[float, float, float, float, Optional[str]]]:
    url = f"https://api.nasdaq.com/api/quote/{symbol}/info?assetclass={assetclass}"
    headers = config.API_HEADERS.get("default", config.HEADERS)
    r = monitored_http_get("nasdaq_quote", url, headers=headers, timeout=config.API_TIMEOUT)
    if r.status_code != 200:
        return None
    data = r.json().get("data") or {}
    primary = data.get("primaryData") or {}
    curr = safe_float(primary.get("lastSalePrice"))
    net_change = safe_float(primary.get("netChange"))
    pct = safe_float(primary.get("percentageChange"))
    if curr <= 0:
        return None
    yclose = 0.0
    summary = data.get("summaryData") or {}
    if isinstance(summary, dict):
        yclose = safe_float((summary.get("PreviousClose") or {}).get("value"))
    if yclose <= 0 and net_change != 0:
        yclose = curr - net_change
    if yclose <= 0:
        yclose = curr
    amt = curr - yclose
    if pct == 0 and yclose > 0:
        pct = amt / yclose * 100
    return curr, yclose, amt, pct, None


def _get_nasdaq_quote_relaxed(symbol: str, assetclass: str) -> Optional[Tuple[float, float, float, float, Optional[str]]]:
    url = f"https://api.nasdaq.com/api/quote/{symbol}/info?assetclass={assetclass}"
    headers = config.API_HEADERS.get("default", config.HEADERS)
    for _ in range(2):
        try:
            r = requests.get(url, headers=headers, timeout=max(4.0, float(config.API_TIMEOUT)))
            if r.status_code != 200:
                continue
            data = (r.json() or {}).get("data") or {}
            primary = data.get("primaryData") or {}
            curr = safe_float(primary.get("lastSalePrice"))
            net_change = safe_float(primary.get("netChange"))
            pct = safe_float(primary.get("percentageChange"))
            if curr <= 0:
                continue
            yclose = 0.0
            summary = data.get("summaryData") or {}
            if isinstance(summary, dict):
                yclose = safe_float((summary.get("PreviousClose") or {}).get("value"))
            if yclose <= 0 and net_change != 0:
                yclose = curr - net_change
            if yclose <= 0:
                yclose = curr
            amt = curr - yclose
            if pct == 0 and yclose > 0:
                pct = amt / yclose * 100
            return curr, yclose, amt, pct, None
        except Exception:
            continue
    return None


@retry_on_failure(max_retries=2, delay=0.5)
def get_hstech_price() -> Tuple[float, float, float, float, Optional[str]]:
    """
    获取恒生科技指数价格
    
    Returns:
        (当前价格, 昨收, 涨跌额, 涨跌幅%)
    """
    try:
        r = monitored_http_get("tencent_hstech", "http://qt.gtimg.cn/q=hkHSTECH", timeout=config.API_TIMEOUT)
        if r.status_code == 200 and 'v_hkHSTECH=' in r.text:
            data = r.text.split('="')[1].split('~')
            curr = safe_float(data[3])
            yclose = safe_float(data[4])
            
            if curr <= 0:
                curr = yclose
            return curr, yclose, curr - yclose, (curr - yclose) / yclose * 100, None
            
    except Exception as e:
        logger.warning(f"HSTECH API error: {e}")
    
    return 0.0, 0.0, 0.0, 0.0, None


def get_sina_stock_price(code: str) -> Tuple[float, float, float, float, Optional[str]]:
    """
    通过新浪接口获取股票价格（通用接口）
    
    Args:
        code: 证券代码
        
    Returns:
        (当前价格, 昨收, 涨跌额, 涨跌幅%)
    """
    try:
        s = _normalize_quote_code(code)
        
        # 美股（包含 gb_ 前缀）- 直接调用美股专用函数
        if 'gb_' in s:
            return get_us_stock_price(s)
        
        is_hk = s.startswith("hk") or "rt_hk" in s
        is_a = s.startswith("sh") or s.startswith("sz")
        is_index = s.startswith("s_")

        tencent = get_tencent_stock_price(s)
        if tencent[0] > 0:
            return tencent

        # 第二步及后续：按市场顺序回退
        if is_hk:
            # 港股：腾讯 -> 东财 -> 新浪
            east = get_eastmoney_stock_price(s)
            if east[0] > 0:
                return east
            sina = get_sina_direct_stock_price(s)
            if sina[0] > 0:
                return sina
        elif is_a:
            # A股：腾讯 -> 新浪 -> 东财
            sina = get_sina_direct_stock_price(s)
            if sina[0] > 0:
                return sina
            east = get_eastmoney_stock_price(s)
            if east[0] > 0:
                return east
        elif is_index:
            # 指数：腾讯 -> 新浪
            sina = get_sina_direct_stock_price(s)
            if sina[0] > 0:
                return sina
                
    except Exception as e:
        logger.warning(f"Sina stock API error for {code}: {e}")
    
    return 0.0, 0.0, 0.0, 0.0, None


def get_tencent_stock_price(code: str) -> Tuple[float, float, float, float, Optional[str]]:
    s = _normalize_quote_code(code)
    if 'gb_' in s:
        return 0.0, 0.0, 0.0, 0.0, None
    try:
        url = config.API_ENDPOINTS["tencent_stock"].format(code=s)
        r = monitored_http_get("tencent_stock", url, timeout=config.API_TIMEOUT)
        if 'v_' + s + '=' not in r.text:
            return 0.0, 0.0, 0.0, 0.0, None
        data = r.text.split('=\"')[1].split(';')[0].split('~')
        if 's_' in s and len(data) > 5:
            curr = safe_float(data[3])
            change = safe_float(data[4])
            if curr > 0:
                yclose = curr - change
                return curr, yclose, change, (change / yclose * 100) if yclose > 0 else 0.0, None
        if ('hk' in s or 'sh' in s or 'sz' in s) and len(data) > 4:
            curr = safe_float(data[3])
            yclose = safe_float(data[4])
            if curr > 0:
                return curr, yclose, curr - yclose, (curr - yclose) / yclose * 100, None
    except Exception as e:
        logger.debug(f"Tencent API error for {code}: {e}")
    return 0.0, 0.0, 0.0, 0.0, None


def get_sina_direct_stock_price(code: str) -> Tuple[float, float, float, float, Optional[str]]:
    s = _normalize_quote_code(code)
    if 'gb_' in s:
        return get_us_stock_price(s)
    try:
        url = config.API_ENDPOINTS["sina_stock"].format(code=s)
        r = monitored_http_get("sina_stock", url, headers=_sina_headers(), timeout=config.API_TIMEOUT)
        if '="' not in r.text:
            return 0.0, 0.0, 0.0, 0.0, None
        match = re.search(r'="(.+)"', r.text)
        if not match:
            return 0.0, 0.0, 0.0, 0.0, None
        data = match.group(1).split(',')
        curr, yclose = 0.0, 0.0
        if 's_' in s:
            if len(data) > 3:
                curr = safe_float(data[1])
                yclose = curr - safe_float(data[2])
        elif s.startswith('hk') or 'rt_hk' in s:
            curr = safe_float(data[6])
            yclose = safe_float(data[3])
        else:
            curr = safe_float(data[3])
            yclose = safe_float(data[2])
        if curr > 0 and yclose > 0:
            return curr, yclose, curr - yclose, (curr - yclose) / yclose * 100, None
    except Exception as e:
        logger.debug(f"Sina API error for {code}: {e}")
    return 0.0, 0.0, 0.0, 0.0, None


def get_eastmoney_stock_price(code: str) -> Tuple[float, float, float, float, Optional[str]]:
    s = _normalize_quote_code(code)
    if s.startswith(('sh', 'sz', 'hk')):
        return _get_eastmoney_cn_hk_price(s)
    if s.startswith('gb_'):
        symbol = s.upper().replace('GB_', '').replace('US.', '')
        try:
            for secid in [f"105.{symbol}", f"106.{symbol}"]:
                url = f"https://push2.eastmoney.com/api/qt/stock/get?invt=2&fltt=2&fields=f43,f60&secid={secid}"
                r = monitored_http_get(
                    "eastmoney_us_stock",
                    url,
                    headers={'User-Agent': config.HEADERS['User-Agent']},
                    timeout=config.API_TIMEOUT,
                )
                data = (r.json() or {}).get('data')
                if data:
                    curr = safe_float(data.get('f43'))
                    yclose = safe_float(data.get('f60'))
                    if curr <= 0:
                        curr = yclose
                    if curr > 0:
                        return curr, yclose, curr - yclose, (curr - yclose) / yclose * 100, None
        except Exception as e:
            logger.debug(f"Eastmoney API error for {code}: {e}")
    return 0.0, 0.0, 0.0, 0.0, None


def get_stock_price(code: str) -> Tuple[float, float, float, float, Optional[str]]:
    """
    获取股票价格（根据代码类型自动选择接口）
    """
    logger.debug(f"Fetching stock price for {code}")
    
    # 1. 特殊指数处理
    if 'ixic' in code.lower():
        return get_nasdaq_price()
    
    if code == 'rt_hkHSTECH' or 'HSTECH' in code:
        return get_hstech_price()
    
    # 2. 自动识别 ISIN 格式 (如 LU..., IE...)
    if is_isin_format(code) or str(code or "").startswith(('ft_', 'gb_')):
        isin = str(code or "").replace('ft_', '').replace('gb_', '').strip().upper()
        if is_isin_format(isin):
            # A) 优先 BlackRock (官方页) - 既然用户要求高保真，官方源权重应最高
            curr, yclose, amt, chg, price_date = get_blackrock_fund_price(isin)
            if curr > 0:
                return curr, yclose, amt, chg, price_date
            
            # B) 次选 Financial Times
            curr, yclose, amt, chg, price_date = get_ft_fund_price(isin)
            if curr > 0:
                return curr, yclose, amt, chg, price_date
        # C) 其他备选
        curr, yclose, amt, chg, price_date = get_marketscreener_fund_price(isin)
        if curr > 0:
            return curr, yclose, amt, chg, price_date
        return get_boursorama_fund_price(isin)
    
    # 3. 美股 (gb_ 前缀)
    if code.startswith('gb_'):
        return get_us_stock_price(code)

    # 4. 可能是美股代码（纯字母/点），优先走美股逻辑
    if re.fullmatch(r'[A-Za-z\\.]+', code or ''):
        return get_us_stock_price(code)
    
    # 5. 通用接口 (A股/港股/Sina/Tencent)
    return get_sina_stock_price(code)
