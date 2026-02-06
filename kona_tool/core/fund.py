"""
基金数据获取模块
提供场外基金、互认基金等基金数据的获取功能
"""
import re
import logging
import requests
from typing import Tuple, Optional

import config
from .utils import safe_float, retry_on_failure, monitored_http_get

logger = logging.getLogger(__name__)


@retry_on_failure(max_retries=2, delay=0.5)
def get_fund_tiantian_price(fund_code: str) -> Tuple[float, float, float, float]:
    """
    从天天基金获取场外基金估值
    
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
            
            price = safe_float(data.get('dwjz', 0))
            gsz = safe_float(data.get('gsz', 0))
            gszzl = safe_float(data.get('gszzl', 0))
            
            current_price = gsz if gsz > 0 else price
            
            if current_price > 0:
                yclose = current_price / (1 + gszzl/100) if (1 + gszzl/100) != 0 else current_price
                amt = current_price - yclose
                
                return current_price, yclose, amt, gszzl
                
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
        url = config.API_ENDPOINTS["eastmoney_fund_f10"]
        params = {"fundCode": clean_code, "pageIndex": 1, "pageSize": 2}
        headers = config.API_HEADERS["eastmoney"]
        
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
    clean_code = re.sub(r'[^0-9]', '', str(code))
    
    if not clean_code:
        return 0.0, 0.0, 0.0, 0.0
    
    logger.debug(f"Fetching fund price for {code}")
    
    # 1. 优先使用天天基金（适合场外基金）
    if code.startswith('f_'):
        price, yclose, amt, chg = get_fund_tiantian_price(code)
        if price > 0:
            return price, yclose, amt, chg
    
    # 2. 尝试东方财富F10接口
    price, yclose, amt, chg = get_fund_eastmoney_f10(clean_code)
    if price > 0:
        return price, yclose, amt, chg
    
    # 3. 尝试东方财富手机端接口（适合互认基金）
    price, yclose, amt, chg = get_fund_eastmoney_mobile(clean_code)
    if price > 0:
        return price, yclose, amt, chg
    
    # 4. 尝试海外基金网页（适合968xxx等海外基金）
    if clean_code.startswith('968'):
        price, yclose, amt, chg = get_fund_overseas_html(clean_code)
        if price > 0:
            return price, yclose, amt, chg
    
    logger.warning(f"Failed to get price for fund {code}")
    return 0.0, 0.0, 0.0, 0.0
