"""
股票数据获取模块
提供A股、港股、美股、指数等价格数据的获取功能
"""
import re
import logging
import requests
from typing import Tuple, Optional
from bs4 import BeautifulSoup

import config
from .utils import safe_float, retry_on_failure, get_first_valid_price

logger = logging.getLogger(__name__)


@retry_on_failure(max_retries=2, delay=0.5)
def get_nasdaq_price() -> Tuple[float, float, float, float]:
    """
    获取纳斯达克指数价格
    
    Returns:
        (当前价格, 昨收, 涨跌额, 涨跌幅%)
    """
    try:
        url = config.API_ENDPOINTS["sina_stock"].format(code="gb_ixic")
        r = requests.get(url, headers=config.HEADERS, timeout=config.API_TIMEOUT)
        
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
        r = requests.get(url, timeout=config.API_TIMEOUT)
        
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
        
        r = requests.get(url, headers=headers, timeout=config.API_TIMEOUT)
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
        r = requests.get(url, headers=config.HEADERS, timeout=config.API_TIMEOUT)
        
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
            r = requests.get(url, headers={'User-Agent': config.HEADERS['User-Agent']}, timeout=config.API_TIMEOUT)
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
    
    return 0.0, 0.0, 0.0, 0.0


@retry_on_failure(max_retries=2, delay=0.5)
def get_hstech_price() -> Tuple[float, float, float, float]:
    """
    获取恒生科技指数价格
    
    Returns:
        (当前价格, 昨收, 涨跌额, 涨跌幅%)
    """
    try:
        r = requests.get("http://qt.gtimg.cn/q=hkHSTECH", timeout=config.API_TIMEOUT)
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
        elif '.hk' in s:
            s = 'hk' + s.replace('.hk', '')
        elif not any(x in s for x in ['sh', 'sz', 'hk', 'gb_', 's_', 'f_', 'of']):
            s = 'gb_' + s
        
        # 美股（包含 gb_ 前缀）- 直接调用美股专用函数
        if 'gb_' in s:
            return get_us_stock_price(s)
        
        # 对于指数、港股和A股，优先使用腾讯API
        try:
            url = config.API_ENDPOINTS["tencent_stock"].format(code=s)
            r = requests.get(url, timeout=config.API_TIMEOUT)

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
        
        # 新浪API
        url = config.API_ENDPOINTS["sina_stock"].format(code=s)
        r = requests.get(url, headers=config.HEADERS, timeout=config.API_TIMEOUT)
        
        if '="' in r.text:
            match = re.search(r'="(.+)"', r.text)
            if match:
                data = match.group(1).split(',')
            else:
                return 0.0, 0.0, 0.0, 0.0
            curr, yclose = 0.0, 0.0
            
            if 's_' in s:  # 指数
                if len(data) > 3:
                    curr = safe_float(data[1])
                    yclose = curr - safe_float(data[2])
            elif 'gb_' in s:  # 美股
                yclose = safe_float(data[26])
                curr = safe_float(data[1])
                if curr == 0:
                    curr = safe_float(data[21])
                if curr == 0:
                    curr = yclose
            elif 'rt_hk' in s:  # 港股
                curr = safe_float(data[6])
                yclose = safe_float(data[3])
            else:  # A股
                curr = safe_float(data[3])
                yclose = safe_float(data[2])
            
            if curr > 0 and yclose > 0:
                return curr, yclose, curr - yclose, (curr - yclose) / yclose * 100
                
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
    
    # 通用接口
    return get_sina_stock_price(code)