"""
基金数据获取模块
提供场外基金、互认基金等基金数据的获取功能
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

import config
from .utils import monitored_http_get, retry_on_failure, safe_float

logger = logging.getLogger(__name__)


_FIDELITY_HISTORY_SHARE_CLASS_IDS = {
    "LU1116320737": "GBESU/G",
}


def normalize_nav_date(value: Any) -> Optional[str]:
    """
    标准化日期格式为 YYYY-MM-DD。
    支持：
    - 2026-03-26
    - 2026/03/26
    - Mar 26 2026
    - 26 Mar 2026
    """
    text = str(value or "").strip()
    if not text:
        return None
    
    # 1. 尝试直接匹配 YYYY-MM-DD
    text_cleaned = text.replace("/", "-")
    iso_match = re.search(r"(\d{4}-\d{2}-\d{2})", text_cleaned)
    if iso_match:
        return iso_match.group(1)
    
    # 2. 尝试匹配带英文月份的格式，如 "Mar 26 2026" 或 "26 Mar 2026"
    months_map = {
        "jan": "01", "feb": "02", "mar": "03", "apr": "04", "may": "05", "jun": "06",
        "jul": "07", "aug": "08", "sep": "09", "oct": "10", "nov": "11", "dec": "12"
    }
    
    # 查找月份
    found_month = None
    for m_name, m_val in months_map.items():
        if m_name in text.lower():
            found_month = m_val
            break
            
    # 3. 尝试匹配中文格式，如 "2026年3月26日"
    cn_match = re.search(r"(\d{4})年\s*(\d{1,2})月\s*(\d{1,2})日", text)
    if cn_match:
        y, m, d = cn_match.groups()
        return f"{y}-{int(m):02d}-{int(d):02d}"

    if found_month:
        # 寻找日期和年份
        nums = re.findall(r"\d+", text)
        if len(nums) >= 2:
            # 简单假设较大的数字是年份 (>= 1900)，较小的是日期
            year = None
            day = None
            for num in nums:
                n = int(num)
                if n >= 1900:
                    year = num
                elif 1 <= n <= 31:
                    day = f"{n:02d}"
            
            if year and day:
                return f"{year}-{found_month}-{day}"

    return None



def _derive_yclose_from_price_and_change(curr: float, chg_pct: float) -> float:
    if curr <= 0:
        return 0.0
    base = 1 + chg_pct / 100
    if abs(base) <= 1e-9:
        return 0.0
    inferred = curr / base
    return inferred if inferred > 0 else 0.0


def _is_plausible_fund_yclose(curr: float, yclose: float) -> bool:
    if curr <= 0 or yclose <= 0:
        return False
    ratio = yclose / curr
    # 场外基金单日涨跌通常很小；放宽到 20% 作为脏数据保护，避免把累计净值当昨收。
    return 0.8 <= ratio <= 1.2


def is_isin_format(code: str) -> bool:
    return bool(re.fullmatch(r"[A-Z]{2}[A-Z0-9]{10}", str(code or "").strip().upper()))


def get_fidelity_history_points(clean_code: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    从 Fidelity 香港基金详情页接口读取历史净值。

    目前先只覆盖已经确认能稳定映射的 share class。
    """
    isin = str(clean_code or "").strip().upper()
    share_class_id = _FIDELITY_HISTORY_SHARE_CLASS_IDS.get(isin)
    if not share_class_id:
        return []

    try:
        r = monitored_http_get(
            "fidelity_fund_history",
            "https://www.fidelity.com.hk/api/ce/fdh/HistoricalNav.json",
            params={
                "id": share_class_id,
                "countries": "hk",
                "country": "hk",
                "languages": "zh,en",
                "language": "zh",
                "channels": "ce.private-investor",
                "channel": "ce.private-investor",
            },
            headers={
                "User-Agent": config.HEADERS.get("User-Agent", "Mozilla/5.0"),
                "Referer": f"https://www.fidelity.com.hk/zh/funds/factsheet/{share_class_id}",
                "Accept": "application/json, text/plain, */*",
            },
            timeout=config.API_TIMEOUT,
        )
        if r.status_code != 200:
            return []

        payload = r.json() or {}
        items = payload.get("items") or []
        points: List[Dict[str, Any]] = []
        for item in reversed(items):
            date = normalize_nav_date((item or {}).get("date"))
            value = safe_float((item or {}).get("nav"))
            if not date or value <= 0:
                continue
            points.append({"date": date, "value": value})
        return points[-max(2, int(limit)) :] if points else []
    except Exception as e:
        logger.warning(f"Fidelity fund history API error for {clean_code}: {e}")
        return []


@retry_on_failure(max_retries=2, delay=0.5)
def get_fund_tiantian_price(fund_code: str) -> Tuple[float, float, float, float, Optional[str]]:
    """
    从天天基金获取场外基金净值

    Args:
        fund_code: 基金代码（已包含f_前缀）

    Returns:
        (当前价格, 昨收, 涨跌额, 涨跌幅%)
    """
    try:
        clean_code = fund_code.replace("f_", "")
        url = config.API_ENDPOINTS["tiantian_fund"].format(code=clean_code)

        r = monitored_http_get("tiantian_fund", url, headers=config.HEADERS, timeout=config.API_TIMEOUT)
        content = str(r.text or "")

        match = re.search(r"jsonpgz\((.*?)\);", content)
        if match:
            import json

            data = json.loads(match.group(1))

            # 口径约束：优先返回确认净值(dwjz)，仅在缺失时回退估算净值(gsz)
            dwjz = safe_float(data.get("dwjz", 0))
            gsz = safe_float(data.get("gsz", 0))
            gszzl = safe_float(data.get("gszzl", 0))

            current_price = dwjz if dwjz > 0 else gsz

            if current_price > 0:
                yclose = current_price
                # 天天接口未直接给昨收，若估算涨幅可用则反推昨收；否则退化为平盘。
                if gsz > 0 and abs(gszzl) > 1e-9:
                    base = 1 + gszzl / 100
                    if abs(base) > 1e-9:
                        inferred_yclose = gsz / base
                        if inferred_yclose > 0:
                            yclose = inferred_yclose

                amt = current_price - yclose
                chg = (amt / yclose * 100) if yclose > 0 else 0.0

                return current_price, yclose, amt, chg, None

    except Exception as e:
        logger.warning(f"Tiantian fund API error for {fund_code}: {e}")

    return 0.0, 0.0, 0.0, 0.0, None, None


@retry_on_failure(max_retries=2, delay=0.5)
def get_fund_tiantian_latest_nav_date(fund_code: str) -> Optional[str]:
    try:
        clean_code = fund_code.replace("f_", "")
        url = config.API_ENDPOINTS["tiantian_fund"].format(code=clean_code)
        r = monitored_http_get("tiantian_fund", url, headers=config.HEADERS, timeout=config.API_TIMEOUT)
        content = str(r.text or "")

        match = re.search(r"jsonpgz\((.*?)\);", content)
        if not match:
            return None

        import json

        data = json.loads(match.group(1))
        return normalize_nav_date(data.get("jzrq") or data.get("gztime"))
    except Exception as e:
        logger.warning(f"Tiantian fund latest nav date API error for {fund_code}: {e}")
        return None


@retry_on_failure(max_retries=2, delay=0.5)
def get_fund_eastmoney_f10(clean_code: str) -> Tuple[float, float, float, float, Optional[str]]:
    """
    从东方财富F10接口获取基金净值（适合场外基金）

    Args:
        clean_code: 清理后的基金代码（不含前缀）

    Returns:
        (当前价格, 昨收, 涨跌额, 涨跌幅%)
    """
    try:
        # 新版可用接口（返回 JSON），老 F10DataApi 在部分环境返回非 JSON
        url = "https://api.fund.eastmoney.com/f10/lsjz"
        params = {"fundCode": clean_code, "pageIndex": 1, "pageSize": 2}
        headers = dict(config.API_HEADERS["eastmoney"])
        headers["Referer"] = "https://fundf10.eastmoney.com/"

        r = monitored_http_get("eastmoney_fund_f10", url, params=params, headers=headers, timeout=config.API_TIMEOUT)
        if r.status_code == 200:
            data = r.json()
            lsjz = data.get("Data", {}).get("LSJZList", [])

            if lsjz:
                curr = safe_float(lsjz[0]["DWJZ"])
                yclose = safe_float(lsjz[1]["DWJZ"]) if len(lsjz) > 1 else curr

                if curr > 0:
                    amt = curr - yclose
                    chg_api = safe_float(lsjz[0].get("JZZZL", ""))
                    chg = chg_api if chg_api != 0 else (amt / yclose * 100 if yclose > 0 else 0)

                    return curr, yclose, amt, chg, None

    except Exception as e:
        logger.warning(f"Eastmoney F10 API error for {clean_code}: {e}")

    return 0.0, 0.0, 0.0, 0.0, None


@retry_on_failure(max_retries=2, delay=0.5)
def get_fund_eastmoney_f10_latest_nav_date(clean_code: str) -> Optional[str]:
    try:
        url = "https://api.fund.eastmoney.com/f10/lsjz"
        params = {"fundCode": clean_code, "pageIndex": 1, "pageSize": 1}
        headers = dict(config.API_HEADERS["eastmoney"])
        headers["Referer"] = "https://fundf10.eastmoney.com/"

        r = monitored_http_get("eastmoney_fund_f10", url, params=params, headers=headers, timeout=config.API_TIMEOUT)
        if r.status_code != 200:
            return None

        data = r.json()
        lsjz = data.get("Data", {}).get("LSJZList", [])
        if not lsjz:
            return None
        return normalize_nav_date(lsjz[0].get("FSRQ"))
    except Exception as e:
        logger.warning(f"Eastmoney F10 latest nav date API error for {clean_code}: {e}")
        return None


@retry_on_failure(max_retries=2, delay=0.5)
def get_fund_tencent_jj(clean_code: str) -> Tuple[float, float, float, float, Optional[str]]:
    """
    从腾讯基金接口获取场外基金净值（备源）

    Args:
        clean_code: 清理后的基金代码（不含前缀）

    Returns:
        (当前价格, 昨收, 涨跌额, 涨跌幅%)
    """
    try:
        symbol = f"jj{clean_code}"
        url = f"https://qt.gtimg.cn/q={symbol}"
        r = monitored_http_get("tencent_fund_jj", url, headers=config.HEADERS, timeout=config.API_TIMEOUT)
        if r.status_code != 200:
            return 0.0, 0.0, 0.0, 0.0

        text = str(r.text or "")
        match = re.search(r'v_[^=]+="([^"]*)"', text)
        if not match:
            return 0.0, 0.0, 0.0, 0.0

        fields = match.group(1).split("~")
        if len(fields) < 9:
            return 0.0, 0.0, 0.0, 0.0

        curr = safe_float(fields[5]) if len(fields) > 5 else 0.0
        yclose_from_feed = safe_float(fields[6]) if len(fields) > 6 else 0.0
        chg = safe_float(fields[7]) if len(fields) > 7 else 0.0

        if curr <= 0:
            return 0.0, 0.0, 0.0, 0.0, None

        yclose = 0.0
        if abs(chg) > 1e-9:
            yclose = _derive_yclose_from_price_and_change(curr, chg)
        if yclose <= 0 and _is_plausible_fund_yclose(curr, yclose_from_feed):
            yclose = yclose_from_feed
        if yclose <= 0:
            yclose = curr

        amt = curr - yclose
        chg_pct = (amt / yclose * 100) if yclose > 0 else 0.0
        nav_date = str(fields[8] or "").strip() if len(fields) > 8 else None
        return curr, yclose, amt, chg_pct, nav_date
    except Exception as e:
        logger.warning(f"Tencent fund API error for {clean_code}: {e}")

    return 0.0, 0.0, 0.0, 0.0, None


@retry_on_failure(max_retries=2, delay=0.5)
def get_fund_eastmoney_mobile(clean_code: str) -> Tuple[float, float, float, float, Optional[str]]:
    """
    从东方财富手机端接口获取基金净值（适合互认基金）

    Args:
        clean_code: 清理后的基金代码（不含前缀）

    Returns:
        (当前价格, 昨收, 涨跌额, 涨跌幅%)
    """
    try:
        url = config.API_ENDPOINTS["eastmoney_fund_mobile"]
        params = {"symbol": clean_code, "pageIndex": 1, "pageSize": 2}
        headers = config.API_HEADERS["eastmoney_mobile"]

        r = monitored_http_get(
            "eastmoney_fund_mobile",
            url,
            params=params,
            headers=headers,
            timeout=config.API_TIMEOUT,
        )
        if r.status_code == 200:
            res = r.json()
            datas = res.get("Datas", [])

            if datas and len(datas) > 0:
                curr = safe_float(datas[0]["DWJZ"])
                yclose = safe_float(datas[1]["DWJZ"]) if len(datas) > 1 else curr

                if curr > 0:
                    amt = curr - yclose
                    chg = (amt / yclose * 100) if yclose > 0 else 0

                    return curr, yclose, amt, chg, str(datas[0].get("FSRQ") or "").strip() or None

    except Exception as e:
        logger.warning(f"Eastmoney Mobile API error for {clean_code}: {e}")

    return 0.0, 0.0, 0.0, 0.0, None


@retry_on_failure(max_retries=2, delay=0.5)
def get_fund_eastmoney_mobile_latest_nav_date(clean_code: str) -> Optional[str]:
    try:
        url = config.API_ENDPOINTS["eastmoney_fund_mobile"]
        params = {"symbol": clean_code, "pageIndex": 1, "pageSize": 1}
        headers = config.API_HEADERS["eastmoney_mobile"]

        r = monitored_http_get(
            "eastmoney_fund_mobile",
            url,
            params=params,
            headers=headers,
            timeout=config.API_TIMEOUT,
        )
        if r.status_code != 200:
            return None

        res = r.json()
        datas = res.get("Datas", [])
        if not datas:
            return None
        row = datas[0]
        return normalize_nav_date(
            row.get("FSRQ") or row.get("JZRQ") or row.get("PDATE") or row.get("GZRQ")
        )
    except Exception as e:
        logger.warning(f"Eastmoney Mobile latest nav date API error for {clean_code}: {e}")
        return None


@retry_on_failure(max_retries=2, delay=0.5)
def get_fund_overseas_html(clean_code: str) -> Tuple[float, float, float, float, Optional[str]]:
    """
    从海外基金网页获取基金净值（适合968xxx等海外基金）

    Args:
        clean_code: 清理后的基金代码（不含前缀）

    Returns:
        (当前价格, 昨收, 涨跌额, 涨跌幅%)
    """
    try:
        url = f"https://overseas.1234567.com.cn/{clean_code}.html"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://overseas.1234567.com.cn/",
        }

        r = monitored_http_get("overseas_fund_html", url, headers=headers, timeout=config.API_TIMEOUT)
        if r.status_code == 200:
            html = r.text

            patterns = [
                r"fix_dwjz[^>]*>([\d.]+)",
                r'class="dwjz"[^>]*>([\d.]+)',
                r">([\d.]+)元",
                r"([\d.]+)\(([-\d.]+)，",
                r"单位净值[^>]*>([\d.]+)",
            ]

            for pattern in patterns:
                match = re.search(pattern, html)
                if match:
                    curr = safe_float(match.group(1))
                    if curr > 0:
                        chg_patterns = [
                            r"\(([-\d.]+)，([-\d.]+)%\)",
                            r"fix_zzl[^>]*>([-\d.]+)%",
                            r"涨跌幅[^>]*>([-\d.]+)%",
                        ]

                        yclose = curr
                        amt = 0.0
                        chg = 0.0

                        for chg_pattern in chg_patterns:
                            chg_match = re.search(chg_pattern, html)
                            if chg_match:
                                if len(chg_match.groups()) == 2:
                                    amt = safe_float(chg_match.group(1))
                                    chg = safe_float(chg_match.group(2))
                                else:
                                    chg = safe_float(chg_match.group(1))
                                    amt = curr * chg / 100 if chg != 0 else 0
                                yclose = curr - amt
                                break

                        nav_date = None
                        date_patterns = [
                            r"(\d{4}-\d{2}-\d{2})",
                            r"(\d{4}年\d{1,2}月\d{1,2}日)",
                            r"净值日期[^>]*>(\d{4}-\d{2}-\d{2})",
                        ]
                        for dp in date_patterns:
                            dm = re.search(dp, html)
                            if dm:
                                nav_date = dm.group(1)
                                break

                        return curr, yclose, amt, chg, nav_date

    except Exception as e:
        logger.warning(f"Overseas HTML error for {clean_code}: {e}")

    return 0.0, 0.0, 0.0, 0.0, None


@retry_on_failure(max_retries=2, delay=0.5)
def get_fund_overseas_history_points(clean_code: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    从海外基金历史净值页提取最近若干个确认净值点。

    主要用于 968xxx 这类 F10 历史接口回空的海外基金。
    """
    try:
        url = f"https://overseas.1234567.com.cn/f10/FundJz/{clean_code}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": f"https://overseas.1234567.com.cn/{clean_code}.html",
        }
        r = monitored_http_get("overseas_fund_history", url, headers=headers, timeout=config.API_TIMEOUT)
        if r.status_code != 200:
            return []

        html = str(r.text or "")
        rows = re.findall(
            r"<tr>\s*<td[^>]*>\s*(\d{4}-\d{2}-\d{2})\s*</td>\s*<td[^>]*>\s*([\d.]+)\s*</td>",
            html,
            re.S,
        )
        if not rows:
            return get_fidelity_history_points(clean_code, limit) if is_isin_format(clean_code) else []

        points: List[Dict[str, Any]] = []
        for date, nav in rows:
            value = safe_float(nav)
            if not date or value <= 0:
                continue
            points.append({"date": date, "value": value})

        points.reverse()
        return points[-max(2, int(limit)) :]
    except Exception as e:
        logger.warning(f"Overseas fund history parser error for {clean_code}: {e}")
        return get_fidelity_history_points(clean_code, limit) if is_isin_format(clean_code) else []


# ── 基金净值日期缓存 ──────────────────────────────────────────
import threading as _threading
import time as _time

_nav_date_cache_lock = _threading.Lock()
_nav_date_cache: Dict[str, Tuple[Optional[str], float]] = {}
_NAV_DATE_CACHE_TTL = 300.0  # 5 分钟（净值日期一天最多变化一次）


def get_fund_latest_nav_date(code: str) -> Optional[str]:
    """获取基金最新净值确认日期（带 5 分钟内存缓存）。"""
    code_str = str(code or "").strip()
    if not code_str:
        return None

    now = _time.time()
    with _nav_date_cache_lock:
        if code_str in _nav_date_cache:
            cached_val, ts = _nav_date_cache[code_str]
            if (now - ts) < _NAV_DATE_CACHE_TTL:
                return cached_val

    result = _fetch_fund_latest_nav_date_uncached(code_str)

    with _nav_date_cache_lock:
        _nav_date_cache[code_str] = (result, _time.time())
    return result


def _fetch_fund_latest_nav_date_uncached(code_str: str) -> Optional[str]:
    """不带缓存地获取基金最新净值确认日期（内部实现）。"""
    normalized_code = str(code_str or "").strip()
    overseas_code = normalized_code.replace("ft_", "").strip().upper()
    if is_isin_format(overseas_code):
        points = get_fund_overseas_history_points(overseas_code, limit=1)
        if points:
            return normalize_nav_date(points[-1].get("date"))
        return None

    clean_code = re.sub(r"[^0-9]", "", code_str)

    if not clean_code:
        return None

    nav_date = get_fund_eastmoney_f10_latest_nav_date(clean_code)
    if nav_date:
        return nav_date

    if clean_code.startswith("968"):
        points = get_fund_overseas_history_points(clean_code, limit=1)
        if points:
            return normalize_nav_date(points[-1].get("date"))

    if code_str.startswith("f_"):
        nav_date = get_fund_tiantian_latest_nav_date(code_str)
        if nav_date:
            return nav_date

    nav_date = get_fund_eastmoney_mobile_latest_nav_date(clean_code)
    if nav_date:
        return nav_date

    return None


def get_fund_price(code: str) -> Tuple[float, float, float, float, Optional[str]]:
    """
    获取基金价格（多数据源自动切换）

    Args:
        code: 基金代码（可包含前缀）

    Returns:
        (当前价格, 昨收, 涨跌额, 涨跌幅%)
    """
    code_str = str(code or "").strip()
    clean_code = re.sub(r"[^0-9]", "", code_str)

    if not clean_code:
        return 0.0, 0.0, 0.0, 0.0

    logger.debug(f"Fetching fund price for {code}")

    # 1. 确认净值优先：东财 F10
    price, yclose, amt, chg, nav_date = get_fund_eastmoney_f10(clean_code)
    if price > 0:
        return price, yclose, amt, chg, nav_date

    # 2. 968xxx 海外基金优先走海外基金网页；天天/腾讯对这类基金经常滞后。
    if clean_code.startswith("968"):
        price, yclose, amt, chg, nav_date = get_fund_overseas_html(clean_code)
        if price > 0:
            return price, yclose, amt, chg, nav_date

    # 3. 兜底：天天基金（dwjz优先，gsz兜底）
    if code_str.startswith("f_"):
        price, yclose, amt, chg, nav_date = get_fund_tiantian_price(code_str)
        if price > 0:
            return price, yclose, amt, chg, nav_date

    # 4. 兜底：东财手机端（适合互认基金）
    price, yclose, amt, chg, nav_date = get_fund_eastmoney_mobile(clean_code)
    if price > 0:
        return price, yclose, amt, chg, nav_date

    # 5. 最后兜底：腾讯 jj，仅补现价，不再信任其累计净值字段为昨收。
    price, yclose, amt, chg, nav_date = get_fund_tencent_jj(clean_code)
    if price > 0:
        return price, yclose, amt, chg, nav_date

    logger.warning(f"Failed to get price for fund {code}")
    return 0.0, 0.0, 0.0, 0.0, None, None
