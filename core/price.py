"""
价格缓存和统一获取模块
提供价格数据的缓存和统一获取接口
"""
import time
import logging
from typing import Dict, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import config
from .stock import get_stock_price
from .fund import get_fund_price

logger = logging.getLogger(__name__)


class PriceCache:
    """价格缓存类"""
    
    def __init__(self, ttl: int = 60):
        """
        初始化缓存
        
        Args:
            ttl: 缓存过期时间（秒）
        """
        self.cache: Dict[str, Tuple[Tuple[float, float, float, float], float]] = {}
        self.ttl = ttl
    
    def get(self, code: str) -> Optional[Tuple[float, float, float, float]]:
        """
        从缓存获取价格
        
        Args:
            code: 证券代码
            
        Returns:
            (价格, 昨收, 涨跌额, 涨跌幅%) 或 None
        """
        if code in self.cache:
            price_data, timestamp = self.cache[code]
            if time.time() - timestamp < self.ttl:
                logger.debug(f"Cache hit for {code}")
                return price_data
            else:
                del self.cache[code]
                logger.debug(f"Cache expired for {code}")
        return None
    
    def set(self, code: str, price_data: Tuple[float, float, float, float]):
        """
        设置缓存
        
        Args:
            code: 证券代码
            price_data: 价格数据
        """
        self.cache[code] = (price_data, time.time())
        logger.debug(f"Cache set for {code}")
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
        logger.info("Cache cleared")


# 全局缓存实例
price_cache = PriceCache(ttl=60)


def get_price(code: str, use_cache: bool = True) -> Tuple[float, float, float, float]:
    """
    统一的价格获取接口（自动判断类型并缓存）
    
    Args:
        code: 证券代码
        use_cache: 是否使用缓存
        
    Returns:
        (价格, 昨收, 涨跌额, 涨跌幅%)
    """
    logger.debug(f"Getting price for {code}")
    
    # 检查缓存
    if use_cache:
        cached = price_cache.get(code)
        if cached:
            return cached
    
    # 根据代码类型选择获取方式
    price_data = None
    
    # 场外基金
    if code.startswith('f_'):
        price_data = get_fund_price(code)
    
    # 其他（股票、指数等）
    else:
        price_data = get_stock_price(code)
    
    # 如果获取成功，更新缓存
    if price_data and price_data[0] > 0:
        price_cache.set(code, price_data)
    
    return price_data if price_data else (0.0, 0.0, 0.0, 0.0)


def batch_get_prices(codes: list, use_cache: bool = True) -> Dict[str, Tuple[float, float, float, float]]:
    """
    批量获取价格（并发获取）
    
    Args:
        codes: 证券代码列表
        use_cache: 是否使用缓存
        
    Returns:
        代码到价格数据的映射
    """
    results = {}
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_code = {
            executor.submit(get_price, code, use_cache): code 
            for code in codes
        }
        for future in as_completed(future_to_code):
            code = future_to_code[future]
            try:
                results[code] = future.result()
            except Exception as e:
                logger.warning(f"Failed to get price for {code}: {e}")
                results[code] = (0.0, 0.0, 0.0, 0.0)
    
    return results


def get_forex_rates() -> Dict[str, float]:
    """
    获取实时汇率
    
    Returns:
        汇率字典 {'USD': 7.25, 'HKD': 0.93, 'CNY': 1.0}
    """
    from .utils import safe_float
    import requests
    
    rates = config.DEFAULT_FOREX_RATES.copy()
    
    try:
        url = config.API_ENDPOINTS["sina_forex"]
        r = requests.get(url, headers=config.HEADERS, timeout=config.API_TIMEOUT)
        
        if r.status_code == 200:
            text = r.text
            if 'hf_USDCNY' in text:
                p = safe_float(text.split('hf_USDCNY')[1].split(',')[0].split('=')[-1])
                if p > 0:
                    rates['USD'] = p
                    logger.debug(f"Updated USD rate: {p}")
            if 'hf_HKDCNY' in text:
                p = safe_float(text.split('hf_HKDCNY')[1].split(',')[0].split('=')[-1])
                if p > 0:
                    rates['HKD'] = p
                    logger.debug(f"Updated HKD rate: {p}")
    except Exception as e:
        logger.warning(f"Failed to get forex rates: {e}, using defaults")
    
    return rates


def search_stocks(query: str) -> list:
    """
    搜索股票
    
    Args:
        query: 搜索关键词
        
    Returns:
        搜索结果列表 [{'code': '...', 'name': '...', 'type_name': '...', 'currency': '...'}, ...]
    """
    import requests
    
    results = []
    
    try:
        url = config.API_ENDPOINTS["sina_search"].format(query=query, timestamp=time.time())
        r = requests.get(url, headers=config.HEADERS, timeout=config.API_TIMEOUT)
        
        if r.status_code == 200:
            content = r.text
            if '"' in content:
                items = content.split('"')[1].split(';')
                for item in items:
                    parts = item.split(',')
                    if len(parts) > 4:
                        results.append({
                            'code': parts[3],
                            'name': parts[4],
                            'type_name': '股票',
                            'currency': 'CNY'
                        })
    except Exception as e:
        logger.warning(f"Failed to search stocks: {e}")
    
    return results[:10]