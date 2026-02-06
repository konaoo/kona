"""
价格缓存和统一获取模块
提供价格数据的缓存和统一获取接口
"""
import time
import logging
import re
import threading
from typing import Dict, Tuple, Optional, List, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

import config
from .stock import get_stock_price
from .asset_type import infer_asset_type, asset_type_label
from .fund import get_fund_price
from .source_health import source_health
from .utils import monitored_http_get
from .utils import safe_float

logger = logging.getLogger(__name__)


class PriceCache:
    """价格缓存类"""
    
    def __init__(self, ttl: int = 60, stale_ttl: int = 300):
        """
        初始化缓存
        
        Args:
            ttl: 缓存过期时间（秒）
        """
        self.cache: Dict[str, Tuple[Tuple[float, float, float, float], float]] = {}
        self.ttl = ttl
        self.stale_ttl = max(stale_ttl, ttl)
    
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

    def get_stale(self, code: str) -> Optional[Tuple[float, float, float, float]]:
        """
        获取过期但仍可回退使用的缓存值（stale-while-revalidate）。
        """
        if code not in self.cache:
            return None
        price_data, timestamp = self.cache[code]
        age = time.time() - timestamp
        if age <= self.stale_ttl:
            return price_data
        del self.cache[code]
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
price_cache = PriceCache(ttl=config.CACHE_TTL, stale_ttl=config.CACHE_STALE_TTL)

_runtime_lock = threading.Lock()
_runtime_metrics: Dict[str, Any] = {
    "cache_hits": 0,
    "stale_hits": 0,
    "network_fetch": 0,
    "network_fail": 0,
    "last_fetch_at": 0.0,
}


def _mark_metric(key: str, inc: int = 1) -> None:
    with _runtime_lock:
        _runtime_metrics[key] = int(_runtime_metrics.get(key, 0)) + inc
        _runtime_metrics["last_fetch_at"] = time.time()


def get_price_runtime_metrics() -> Dict[str, Any]:
    with _runtime_lock:
        return dict(_runtime_metrics)


def get_price_source_health() -> Dict[str, Dict[str, Any]]:
    return source_health.snapshot()


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
    
    stale_fallback = price_cache.get_stale(code)

    # 检查缓存
    if use_cache:
        cached = price_cache.get(code)
        if cached:
            _mark_metric("cache_hits")
            return cached
    
    # 根据代码类型选择获取方式
    price_data = None
    
    # 场外基金
    _mark_metric("network_fetch")

    if code.startswith('f_'):
        price_data = get_fund_price(code)
    
    # 其他（股票、指数等）
    else:
        price_data = get_stock_price(code)
    
    # 如果获取成功，更新缓存
    if price_data and price_data[0] > 0:
        price_cache.set(code, price_data)
        return price_data

    _mark_metric("network_fail")
    if stale_fallback:
        _mark_metric("stale_hits")
        logger.info(f"Price fallback to stale cache for {code}")
        return stale_fallback

    return (0.0, 0.0, 0.0, 0.0)


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
    missing_codes: List[str] = []
    seen_missing = set()

    if use_cache:
        for code in codes:
            cached = price_cache.get(code)
            if cached:
                results[code] = cached
            elif code not in seen_missing:
                missing_codes.append(code)
                seen_missing.add(code)
    else:
        for code in codes:
            if code not in seen_missing:
                missing_codes.append(code)
                seen_missing.add(code)

    if missing_codes:
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_code = {
                executor.submit(get_price, code, False): code
                for code in missing_codes
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
    rates = config.DEFAULT_FOREX_RATES.copy()
    
    try:
        url = config.API_ENDPOINTS["sina_forex"]
        r = monitored_http_get("sina_forex", url, headers=config.HEADERS, timeout=config.API_TIMEOUT)
        
        if r.status_code == 200:
            text = r.text
            # 使用正则匹配 hf_USDCNY=7.25, hf_HKDCNY=0.93
            matches = re.findall(r'hf_([A-Z]+)CNY.*?=([0-9.]+)', text)
            for curr, price_str in matches:
                p = safe_float(price_str)
                if p > 0:
                    rates[curr] = p
                    logger.debug(f"Updated {curr} rate: {p}")
                    
    except Exception as e:
        logger.warning(f"Failed to get forex rates: {e}, using defaults")
    
    return rates


def _parse_sina_response(content: str, type_code: str) -> List[dict]:
    """解析新浪搜索响应"""
    items = []
    if '"' in content:
        data = content.split('"')[1]
        if data:
            for item in data.split(';'):
                parts = item.split(',')
                if len(parts) > 4:
                    code = parts[3]
                    name = parts[4]
                    if code and name:
                        # 根据type确定类型和货币
                        if type_code == '11':  # A股
                            type_name = 'A股'
                            currency = 'CNY'
                        elif type_code == '31':  # 港股
                            type_name = '港股'
                            currency = 'HKD'
                            code = code + '.HK' if not code.endswith('.HK') else code
                        elif type_code == '41':  # 美股
                            type_name = '美股'
                            currency = 'USD'
                            code = 'gb_' + code.lower() if not code.startswith('gb_') else code
                        else:
                            type_name = '股票'
                            currency = 'CNY'
                        items.append({
                            'code': code,
                            'name': name,
                            'type_name': type_name,
                            'currency': currency
                        })
    return items

def _search_sina(query: str, type_code: str) -> List[dict]:
    """搜索新浪接口 (type_code: 11=A股, 31=港股, 41=美股)"""
    results = []
    try:
        url = ""
        if type_code == '11':
             url = config.API_ENDPOINTS["sina_search"].format(query=query, timestamp=time.time())
        else:
             url = f"http://suggest3.sinajs.cn/suggest/type={type_code}&key={query}&name=suggestdata_{int(time.time())}"
             
        r = monitored_http_get("sina_search", url, headers=config.HEADERS, timeout=config.API_TIMEOUT)
        r.encoding = 'gbk'
        if r.status_code == 200:
            results = _parse_sina_response(r.text, type_code)
    except Exception as e:
        logger.warning(f"Sina search error (type={type_code}): {e}")
    return results

def _search_fund(query: str) -> List[dict]:
    """搜索基金"""
    results = []
    try:
        fund_url = 'https://fundsuggest.eastmoney.com/FundSearch/api/FundSearchAPI.ashx'
        r = monitored_http_get(
            "eastmoney_fund_search",
            fund_url,
            params={'m': 1, 'key': query},
            timeout=config.API_TIMEOUT,
        )
        if r.status_code == 200:
            data = r.json()
            if data.get('Datas'):
                for fund in data['Datas'][:5]:
                    code = 'f_' + fund.get('CODE', '')
                    name = fund.get('NAME', '')
                    if code and name:
                        results.append({
                            'code': code,
                            'name': name,
                            'type_name': '基金',
                            'currency': 'CNY'
                        })
    except Exception as e:
        logger.warning(f"Fund search error: {e}")
    return results

def search_stocks(query: str) -> list:
    """
    搜索股票（支持A股、港股、美股、基金）- 并行搜索
    
    Args:
        query: 搜索关键词
        
    Returns:
        搜索结果列表 [{'code': '...', 'name': '...', 'type_name': '...', 'currency': '...'}, ...]
    """
    results = []
    seen_codes = set()
    
    # 并行执行搜索
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        # 1. A股
        futures.append(executor.submit(_search_sina, query, '11'))
        # 2. 港股
        futures.append(executor.submit(_search_sina, query, '31'))
        # 3. 美股
        futures.append(executor.submit(_search_sina, query, '41'))
        # 4. 基金
        futures.append(executor.submit(_search_fund, query))
        
        for future in as_completed(futures):
            try:
                items = future.result()
                for item in items:
                    if item['code'] not in seen_codes:
                        seen_codes.add(item['code'])
                        results.append(item)
            except Exception as e:
                logger.error(f"Search task failed: {e}")
                
    final_results = []
    for item in results:
        asset_type = infer_asset_type(item.get('code', ''), item.get('name', ''))
        item['asset_type'] = asset_type
        item['type_name'] = asset_type_label(asset_type)
        final_results.append(item)

    return final_results[:15]
