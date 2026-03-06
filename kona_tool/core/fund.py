"""
基金数据获取模块
提供场外基金、互认基金等基金数据的获取功能
"""
import re
import logging
from typing import Tuple, Optional

import config
from .utils import safe_float, retry_on_failure, monitored_http_get

logger = logging.getLogger(__name__)


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


@retry_on_failure(max_retries=2, delay=0.5)
def get_fund_tiantian_price(fund_code: str) -> Tuple[float, float, float, float]:
    """
    从天天基金获取场外基金净值
    
    Args:
        fund_code: 基金代码（已包含f_前缀）
        
    Returns:
        (当前价格, 昨收, 涨跌额, 涨跌幅%)
    """
    try:
        clean_code = fund_code.replace('f_', '')
        url = config.API_ENDPOINTS["tiantian_fund"].format(code=clean_code)
        
        r = monitored_http_get("tiantian_fund", url, headers=config.HEADERS, timeout=config.API_TIMEOUT)
        content = r.text
        
        match = re.search(r'jsonpgz\((.*?)\);', content)
        if match:
            import json
            data = json.loads(match.group(1))
            
            # 口径约束：优先返回确认净值(dwjz)，仅在缺失时回退估算净值(gsz)
            dwjz = safe_float(data.get('dwjz', 0))
            gsz = safe_float(data.get('gsz', 0))
            gszzl = safe_float(data.get('gszzl', 0))

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

                return current_price, yclose, amt, chg
                
    except Exception as e:
        logger.warning(f"Tiantian fund API error for {fund_code}: {e}")
    
    return 0.0, 0.0, 0.0, 0.0


@retry_on_failure(max_retries=2, delay=0.5)
def get_fund_eastmoney_f10(clean_code: str) -> Tuple[float, float, float, float]:
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
            lsjz = data.get('Data', {}).get('LSJZList', [])
            
            if lsjz:
                curr = safe_float(lsjz[0]['DWJZ'])
                yclose = safe_float(lsjz[1]['DWJZ']) if len(lsjz) > 1 else curr
                
                if curr > 0:
                    amt = curr - yclose
                    chg_api = safe_float(lsjz[0].get('JZZZL', ''))
                    chg = chg_api if chg_api != 0 else (amt/yclose*100 if yclose>0 else 0)
                    
                    return curr, yclose, amt, chg
                    
    except Exception as e:
        logger.warning(f"Eastmoney F10 API error for {clean_code}: {e}")
    
    return 0.0, 0.0, 0.0, 0.0


@retry_on_failure(max_retries=2, delay=0.5)
def get_fund_tencent_jj(clean_code: str) -> Tuple[float, float, float, float]:
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
            return 0.0, 0.0, 0.0, 0.0

        yclose = 0.0
        if abs(chg) > 1e-9:
            yclose = _derive_yclose_from_price_and_change(curr, chg)
        if yclose <= 0 and _is_plausible_fund_yclose(curr, yclose_from_feed):
            yclose = yclose_from_feed
        if yclose <= 0:
            yclose = curr

        amt = curr - yclose
        chg_pct = (amt / yclose * 100) if yclose > 0 else 0.0
        return curr, yclose, amt, chg_pct
    except Exception as e:
        logger.warning(f"Tencent fund API error for {clean_code}: {e}")

    return 0.0, 0.0, 0.0, 0.0


@retry_on_failure(max_retries=2, delay=0.5)
def get_fund_eastmoney_mobile(clean_code: str) -> Tuple[float, float, float, float]:
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
                curr = safe_float(datas[0]['DWJZ'])
                yclose = safe_float(datas[1]['DWJZ']) if len(datas) > 1 else curr
                
                if curr > 0:
                    amt = curr - yclose
                    chg = (amt/yclose*100) if yclose > 0 else 0
                    
                    return curr, yclose, amt, chg
                    
    except Exception as e:
        logger.warning(f"Eastmoney Mobile API error for {clean_code}: {e}")
    
    return 0.0, 0.0, 0.0, 0.0


@retry_on_failure(max_retries=2, delay=0.5)
def get_fund_overseas_html(clean_code: str) -> Tuple[float, float, float, float]:
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
            "Referer": "https://overseas.1234567.com.cn/"
        }
        
        r = monitored_http_get("overseas_fund_html", url, headers=headers, timeout=config.API_TIMEOUT)
        
        url = f"https://overseas.1234567.com.cn/{clean_code}.html"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://overseas.1234567.com.cn/"
        }
        
        r = monitored_http_get("overseas_fund_html", url, headers=headers, timeout=config.API_TIMEOUT)
        if r.status_code == 200:
            html = r.text
            
            # Try to find price in multiple patterns (updated for actual HTML structure)
            patterns = [
                r'fix_dwjz[^>]*>([\d.]+)',  # Matches <span class="fix_dwjz ...">10.5000
                r'class="dwjz"[^>]*>([\d.]+)',  # Alternative class name
                r'>([\d.]+)元',  # Pattern for price with Chinese yuan symbol
                r'([\d.]+)\(([-\d.]+)，',  # Price followed by change
                r'单位净值[^>]*>([\d.]+)',  # Unit net value
            ]
            
            for pattern in patterns:
                match = re.search(pattern, html)
                if match:
                    curr = safe_float(match.group(1))
                    if curr > 0:
                        # Try to find yesterday close and change
                        chg_patterns = [
                            r'\(([-\d.]+)，([-\d.]+)%\)',  # Change format
                            r'fix_zzl[^>]*>([-\d.]+)%',  # Change percentage class
                            r'涨跌幅[^>]*>([-\d.]+)%',  # Change percentage text
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
                        
                        return curr, yclose, amt, chg
            
    except Exception as e:
        logger.warning(f"Overseas HTML error for {clean_code}: {e}")
    
    return 0.0, 0.0, 0.0, 0.0


def get_fund_price(code: str) -> Tuple[float, float, float, float]:
    """
    获取基金价格（多数据源自动切换）
    
    Args:
        code: 基金代码（可包含前缀）
        
    Returns:
        (当前价格, 昨收, 涨跌额, 涨跌幅%)
    """
    code_str = str(code or '').strip()
    clean_code = re.sub(r'[^0-9]', '', code_str)
    
    if not clean_code:
        return 0.0, 0.0, 0.0, 0.0
    
    logger.debug(f"Fetching fund price for {code}")
    
    # 1. 确认净值优先：东财 F10
    price, yclose, amt, chg = get_fund_eastmoney_f10(clean_code)
    if price > 0:
        return price, yclose, amt, chg

    # 2. 968xxx 海外基金优先走海外基金网页；天天/腾讯对这类基金经常滞后。
    if clean_code.startswith('968'):
        price, yclose, amt, chg = get_fund_overseas_html(clean_code)
        if price > 0:
            return price, yclose, amt, chg

    # 3. 兜底：天天基金（dwjz优先，gsz兜底）
    if code_str.startswith('f_'):
        price, yclose, amt, chg = get_fund_tiantian_price(code_str)
        if price > 0:
            return price, yclose, amt, chg

    # 4. 兜底：东财手机端（适合互认基金）
    price, yclose, amt, chg = get_fund_eastmoney_mobile(clean_code)
    if price > 0:
        return price, yclose, amt, chg

    # 5. 最后兜底：腾讯 jj，仅补现价，不再信任其累计净值字段为昨收。
    price, yclose, amt, chg = get_fund_tencent_jj(clean_code)
    if price > 0:
        return price, yclose, amt, chg
    
    logger.warning(f"Failed to get price for fund {code}")
    return 0.0, 0.0, 0.0, 0.0
