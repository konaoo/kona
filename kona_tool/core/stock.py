"""
股票数据获取模块
提供A股、港股、美股、指数等价格数据的获取功能
"""
import re
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Tuple, Optional, Dict, Any, List
from bs4 import BeautifulSoup

import config
from .utils import safe_float, retry_on_failure, get_first_valid_price, monitored_http_get

logger = logging.getLogger(__name__)


def _sina_headers() -> Dict[str, Any]:
    headers = dict(config.HEADERS)
    headers.setdefault("Referer", "https://finance.sina.com.cn")
    return headers


def _get_eastmoney_cn_hk_price(code: str) -> Tuple[float, float, float, float]:
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
        return 0.0, 0.0, 0.0, 0.0

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
            return curr, yclose, amt, chg
    except Exception as exc:
        logger.debug(f"Eastmoney CN/HK API error for {code}: {exc}")

    return 0.0, 0.0, 0.0, 0.0


def _normalize_us_symbol(code: str) -> str:
    return code.upper().replace('GB_', '').replace('US.', '').strip()


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
                logger.warning(f"Nasdaq extended quote API error for {symbol}: {exc}")
                continue
            if quote:
                result[symbol] = quote
    return result


@retry_on_failure(max_retries=2, delay=0.5)
def get_nasdaq_price() -> Tuple[float, float, float, float]:
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
                
                if curr > 0:
                    return curr, yclose, curr - yclose, (curr - yclose) / yclose * 100
                    
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
                    return curr, yclose, curr - yclose, (curr - yclose) / yclose * 100
                    
    except Exception as e:
        logger.warning(f"Tencent NASDAQ API error: {e}")
    
    return 0.0, 0.0, 0.0, 0.0


@retry_on_failure(max_retries=2, delay=0.5)
def get_ft_fund_price(isin: str) -> Tuple[float, float, float, float]:
    """
    从Financial Times获取基金价格
    
    Args:
        isin: 基金ISIN代码
        
    Returns:
        (当前价格, 昨收, 涨跌额, 涨跌幅%)
    """
    try:
        url = config.API_ENDPOINTS["ft_fund"].format(isin=isin.upper())
        headers = config.API_HEADERS["ft"]
        
        r = monitored_http_get("ft_fund", url, headers=headers, timeout=config.API_TIMEOUT)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            price_tag = soup.find('span', class_='mod-tearsheet-overview__quote__value') or \
                        soup.find('span', class_='mod-ui-data-list__value')
            
            if price_tag:
                curr = safe_float(price_tag.text)
                if curr > 0:
                    chg_tag = soup.find('span', class_='mod-tearsheet-overview__quote__chg')
                    chg = safe_float(chg_tag.text) if chg_tag else 0.0
                    yclose = curr / (1 + chg/100) if (1 + chg/100) != 0 else curr
                    return curr, yclose, curr - yclose, chg
                    
    except Exception as e:
        logger.warning(f"FT fund API error for {isin}: {e}")
    
    return 0.0, 0.0, 0.0, 0.0


@retry_on_failure(max_retries=2, delay=0.5)
def get_us_stock_price(code: str) -> Tuple[float, float, float, float]:
    """
    获取美股价格
    
    Args:
        code: 美股代码（如 gb_bili）
        
    Returns:
        (当前价格, 昨收, 涨跌额, 涨跌幅%)
    """
    s = code.upper().replace('GB_', '').replace('US.', '')
    
    try:
        url = config.API_ENDPOINTS["sina_stock"].format(code=f"gb_{s.lower()}")
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
                return curr, yclose, curr - yclose, (curr - yclose) / yclose * 100
                
    except Exception as e:
        logger.warning(f"Sina US stock API error for {code}: {e}")
    
    try:
        for secid in [f"105.{s}", f"106.{s}"]:
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
                    return curr, yclose, curr - yclose, (curr - yclose) / yclose * 100
                    
    except Exception as e:
        logger.warning(f"Eastmoney US stock API error for {code}: {e}")

    # Nasdaq 备用接口（ETF/US Stocks）
    try:
        for assetclass in ["etf", "stocks"]:
            quote = _get_nasdaq_quote(s, assetclass)
            if quote:
                curr, yclose, amt, pct = quote
                return curr, yclose, amt, pct
    except Exception as e:
        logger.warning(f"Nasdaq quote API error for {code}: {e}")

    return 0.0, 0.0, 0.0, 0.0


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


def _get_nasdaq_quote(symbol: str, assetclass: str) -> Optional[Tuple[float, float, float, float]]:
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
    return curr, yclose, amt, pct


@retry_on_failure(max_retries=2, delay=0.5)
def get_hstech_price() -> Tuple[float, float, float, float]:
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
            return curr, yclose, curr - yclose, (curr - yclose) / yclose * 100
            
    except Exception as e:
        logger.warning(f"HSTECH API error: {e}")
    
    return 0.0, 0.0, 0.0, 0.0


def get_sina_stock_price(code: str) -> Tuple[float, float, float, float]:
    """
    通过新浪接口获取股票价格（通用接口）
    
    Args:
        code: 证券代码
        
    Returns:
        (当前价格, 昨收, 涨跌额, 涨跌幅%)
    """
    try:
        s = code.lower()
        
        # 代码格式转换
        if s.isdigit() and len(s) == 6:
            s = ('sh' if s[0] in ['5', '6', '9'] else 'sz') + s
        elif s.isdigit() and len(s) == 5:
            # 5位纯数字按港股处理（如 00700 -> hk00700）
            s = 'hk' + s
        elif '.hk' in s:
            s = 'hk' + s.replace('.hk', '')
        elif s.startswith("hk"):
            digits = re.sub(r"\D", "", s)
            if digits:
                s = "hk" + digits.zfill(5)
        elif not any(x in s for x in ['sh', 'sz', 'hk', 'gb_', 's_', 'f_', 'of']):
            s = 'gb_' + s
        
        # 美股（包含 gb_ 前缀）- 直接调用美股专用函数
        if 'gb_' in s:
            return get_us_stock_price(s)
        
        is_hk = s.startswith("hk") or "rt_hk" in s
        is_a = s.startswith("sh") or s.startswith("sz")
        is_index = s.startswith("s_")

        # 第一步：腾讯优先（A/HK/指数）
        try:
            url = config.API_ENDPOINTS["tencent_stock"].format(code=s)
            r = monitored_http_get("tencent_stock", url, timeout=config.API_TIMEOUT)

            if 'v_' + s + '=' in r.text:
                data = r.text.split('=\"')[1].split(';')[0].split('~')

                if 's_' in s:  # 指数
                    if len(data) > 5:
                        curr = safe_float(data[3])
                        change = safe_float(data[4])  # 涨跌额
                        if curr > 0:
                            yclose = curr - change
                            return curr, yclose, change, (change / yclose * 100) if yclose > 0 else 0.0
                elif 'hk' in s:  # 港股
                    if len(data) > 4:
                        curr = safe_float(data[3])
                        yclose = safe_float(data[4])
                        if curr > 0:
                            return curr, yclose, curr - yclose, (curr - yclose) / yclose * 100 if yclose > 0 else 0.0
                elif 'sh' in s or 'sz' in s:  # A股
                    if len(data) > 4:
                        curr = safe_float(data[3])
                        yclose = safe_float(data[4])
                        if curr > 0:
                            return curr, yclose, curr - yclose, (curr - yclose) / yclose * 100 if yclose > 0 else 0.0
        except Exception as e:
            logger.debug(f"Tencent API error for {code}: {e}")

        def _fetch_from_sina() -> Tuple[float, float, float, float]:
            url = config.API_ENDPOINTS["sina_stock"].format(code=s)
            r = monitored_http_get("sina_stock", url, headers=_sina_headers(), timeout=config.API_TIMEOUT)
            if '="' not in r.text:
                return 0.0, 0.0, 0.0, 0.0
            match = re.search(r'="(.+)"', r.text)
            if not match:
                return 0.0, 0.0, 0.0, 0.0
            data = match.group(1).split(',')
            curr, yclose = 0.0, 0.0
            if 's_' in s:  # 指数
                if len(data) > 3:
                    curr = safe_float(data[1])
                    yclose = curr - safe_float(data[2])
            elif s.startswith('hk') or 'rt_hk' in s:  # 港股
                curr = safe_float(data[6])
                yclose = safe_float(data[3])
            else:  # A股
                curr = safe_float(data[3])
                yclose = safe_float(data[2])
            if curr > 0 and yclose > 0:
                return curr, yclose, curr - yclose, (curr - yclose) / yclose * 100
            return 0.0, 0.0, 0.0, 0.0

        # 第二步及后续：按市场顺序回退
        if is_hk:
            # 港股：腾讯 -> 东财 -> 新浪
            east = _get_eastmoney_cn_hk_price(s)
            if east[0] > 0:
                return east
            sina = _fetch_from_sina()
            if sina[0] > 0:
                return sina
        elif is_a:
            # A股：腾讯 -> 新浪 -> 东财
            sina = _fetch_from_sina()
            if sina[0] > 0:
                return sina
            east = _get_eastmoney_cn_hk_price(s)
            if east[0] > 0:
                return east
        elif is_index:
            # 指数：腾讯 -> 新浪
            sina = _fetch_from_sina()
            if sina[0] > 0:
                return sina
                
    except Exception as e:
        logger.warning(f"Sina stock API error for {code}: {e}")
    
    return 0.0, 0.0, 0.0, 0.0


def get_stock_price(code: str) -> Tuple[float, float, float, float]:
    """
    获取股票价格（根据代码类型自动选择接口）
    
    Args:
        code: 证券代码
        
    Returns:
        (当前价格, 昨收, 涨跌额, 涨跌幅%)
    """
    logger.debug(f"Fetching stock price for {code}")
    
    # 特殊处理
    if 'ixic' in code.lower():
        return get_nasdaq_price()
    
    if code == 'rt_hkHSTECH' or 'HSTECH' in code:
        return get_hstech_price()
    
    # FT基金
    if code.startswith('ft_'):
        return get_ft_fund_price(code.replace('ft_', ''))
    
    # 美股
    if code.startswith('gb_'):
        return get_us_stock_price(code)

    # 可能是美股代码（纯字母/点），优先走美股逻辑
    if re.fullmatch(r'[A-Za-z\\.]+', code or ''):
        return get_us_stock_price(code)
    
    # 通用接口
    return get_sina_stock_price(code)
