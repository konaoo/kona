"""
价格缓存和统一获取模块
提供价格数据的缓存和统一获取接口
"""
import time
import logging
import re
import threading
from typing import Dict, Tuple, Optional, List, Any
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED, as_completed

import config
from .stock import get_stock_price
from .fund import get_fund_price
from .source_health import source_health
from .utils import monitored_http_get
from .utils import safe_float
from .policy_runtime import is_policy_enabled

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
    if not is_policy_enabled("upstream.price", default=True):
        logger.warning("Price upstream disabled by admin policy")
        if stale_fallback:
            _mark_metric("stale_hits")
            return stale_fallback
        return (0.0, 0.0, 0.0, 0.0)

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


class PricePreloader:
    """
    后台预取线程：定时收集所有用户持有的证券代码，
    批量拉取行情并写入 PriceCache，确保 API 请求始终命中缓存。
    """

    _instance = None

    def __init__(self, db_path: str, interval: int = 30):
        self._db_path = db_path
        self._interval = interval
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    @classmethod
    def get_instance(cls, db_path: str = '', interval: int = 30) -> 'PricePreloader':
        if cls._instance is None:
            cls._instance = cls(db_path, interval)
        return cls._instance

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            logger.info("PricePreloader already running, skip.")
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info(
            f"PricePreloader started (interval={self._interval}s)"
        )

    def stop(self) -> None:
        self._stop_event.set()
        logger.info("PricePreloader stopping...")

    def _collect_codes(self) -> List[str]:
        """从数据库收集所有用户持有的唯一证券代码"""
        import sqlite3
        codes: List[str] = []
        try:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT code FROM portfolio")
            codes = [row[0] for row in cursor.fetchall() if row[0]]
            conn.close()
        except Exception as e:
            logger.error(f"PricePreloader failed to collect codes: {e}")
        return codes

    def _run(self) -> None:
        logger.info("PricePreloader thread started.")
        while not self._stop_event.is_set():
            try:
                codes = self._collect_codes()
                if codes:
                    logger.info(
                        f"PricePreloader: refreshing {len(codes)} codes..."
                    )
                    batch_get_prices(codes, use_cache=False)
                    logger.info(
                        f"PricePreloader: done, {len(codes)} codes cached."
                    )
                else:
                    logger.debug("PricePreloader: no codes to refresh.")
            except Exception as e:
                logger.error(f"PricePreloader error: {e}")

            # 等待指定间隔，支持提前停止
            self._stop_event.wait(timeout=self._interval)


def get_forex_rates() -> Dict[str, float]:
    """
    获取实时汇率

    优先使用 exchangerate-api.com（免费、无需注册），
    回退到新浪外汇接口，最终兜底使用 config 默认值。

    Returns:
        汇率字典 {'USD': 7.0, 'HKD': 0.9, 'CNY': 1.0}
    """
    rates = config.DEFAULT_FOREX_RATES.copy()

    if not is_policy_enabled("upstream.rate", default=True):
        logger.warning("Rate upstream disabled by admin policy")
        return rates

    # 主数据源：exchangerate-api.com
    try:
        url = "https://open.er-api.com/v6/latest/USD"
        r = monitored_http_get("exchangerate_api", url, headers=config.API_HEADERS["default"], timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data.get("result") == "success" and "rates" in data:
                api_rates = data["rates"]
                cny = safe_float(api_rates.get("CNY", 0))
                hkd_per_usd = safe_float(api_rates.get("HKD", 0))
                if cny > 0:
                    rates["USD"] = round(cny, 4)
                    logger.debug(f"Updated USD rate from exchangerate-api: {cny}")
                if hkd_per_usd > 0 and cny > 0:
                    rates["HKD"] = round(cny / hkd_per_usd, 4)
                    logger.debug(f"Updated HKD rate from exchangerate-api: {rates['HKD']}")
                return rates
    except Exception as e:
        logger.warning(f"exchangerate-api failed: {e}, trying sina fallback")

    # 备用数据源：新浪外汇
    try:
        url = config.API_ENDPOINTS["sina_forex"]
        r = monitored_http_get("sina_forex", url, headers=config.HEADERS, timeout=config.API_TIMEOUT)
        if r.status_code == 200:
            text = r.text
            matches = re.findall(r'hf_([A-Z]+)CNY.*?=([0-9.]+)', text)
            for curr, price_str in matches:
                p = safe_float(price_str)
                if p > 0:
                    rates[curr] = p
                    logger.debug(f"Updated {curr} rate from sina: {p}")
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
             
        r = monitored_http_get(
            "sina_search",
            url,
            headers=config.HEADERS,
            timeout=_search_source_timeout_seconds(),
        )
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
            timeout=_search_source_timeout_seconds(),
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
    started_at = time.monotonic()
    results = []
    seen_codes = set()
    max_wait_seconds = _search_aggregate_timeout_seconds()
    deadline = time.monotonic() + max_wait_seconds

    executor = ThreadPoolExecutor(max_workers=4)
    futures = {
        executor.submit(_search_sina, query, '11'): 'a',
        executor.submit(_search_sina, query, '31'): 'hk',
        executor.submit(_search_sina, query, '41'): 'us',
        executor.submit(_search_fund, query): 'fund',
    }
    pending = set(futures.keys())
    timed_out_sources = []

    try:
        while pending:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                timed_out_sources.extend(futures[f] for f in pending)
                break

            done, pending = wait(
                pending,
                timeout=remaining,
                return_when=FIRST_COMPLETED,
            )
            if not done:
                timed_out_sources.extend(futures[f] for f in pending)
                break

            for future in done:
                try:
                    items = future.result()
                    for item in items:
                        code = str(item.get('code', '') or '').strip()
                        if _is_invalid_letter_fund_code(code):
                            continue
                        if code and code not in seen_codes:
                            seen_codes.add(code)
                            results.append(item)
                except Exception as e:
                    logger.error(f"Search task failed: {e}")
    finally:
        if timed_out_sources:
            logger.info(
                "search_stocks timeout for query=%s sources=%s",
                query,
                ",".join(sorted(set(timed_out_sources))),
            )
        executor.shutdown(wait=False, cancel_futures=True)
                
    final_results = []
    query_lower = query.lower()

    for item in results:
        code = str(item.get('code', '') or '')
        asset_type = _asset_type_from_type_name(item.get('type_name', ''), code)
        item['asset_type'] = asset_type
        final_results.append(item)

    # 排序逻辑：完全匹配代码的优先，然后是名字前置匹配，然后默认顺序
    def _sort_key(item):
        code = (item.get('code') or '').lower()
        name = (item.get('name') or '').lower()
        # 清除代码前缀后缀来进行更准确的比较
        clean_code = code.replace('gb_', '').replace('.hk', '').replace('f_', '').replace('ft_', '')
        
        # 优先级：
        # 1. 代码完全匹配 (包括去前缀后的)
        if query_lower == code or query_lower == clean_code:
            return 0
        # 2. 名字前置匹配
        if name.startswith(query_lower):
            return 1
        # 3. 代码包含
        if query_lower in code or query_lower in clean_code:
            return 2
        # 4. 其他
        return 3

    final_results.sort(key=_sort_key)
    final_results = final_results[:15]

    elapsed_ms = int((time.monotonic() - started_at) * 1000)
    logger.info(
        "search_stocks done query=%s elapsed_ms=%s result_count=%s timed_out_sources=%s",
        query,
        elapsed_ms,
        len(final_results),
        ",".join(sorted(set(timed_out_sources))) if timed_out_sources else "-",
    )
    return final_results


def _search_aggregate_timeout_seconds() -> float:
    return max(
        0.5,
        float(getattr(config, "SEARCH_AGGREGATE_TIMEOUT_SECONDS", 1.8)),
    )


def _search_source_timeout_seconds() -> float:
    timeout = float(
        getattr(
            config,
            "SEARCH_SOURCE_TIMEOUT_SECONDS",
            getattr(config, "API_TIMEOUT", 3),
        )
    )
    return max(0.3, timeout)


def _is_invalid_letter_fund_code(code: str) -> bool:
    lower = str(code or "").lower()
    if not lower.startswith("f_"):
        return False
    suffix = lower[2:].strip()
    return bool(suffix) and not suffix.isdigit()


def _asset_type_from_type_name(type_name: str, code: str = "") -> str:
    lower_code = str(code or "").lower()
    if lower_code.startswith("gb_"):
        return "us"
    if lower_code.startswith("ft_"):
        return "fund"
    if lower_code.startswith("f_"):
        suffix = lower_code[2:].strip()
        return "fund" if suffix.isdigit() else "us"
    if ".hk" in lower_code or lower_code.startswith("hk"):
        return "hk"
    if lower_code.startswith(("sh", "sz", "bj")):
        return "a"

    normalized = str(type_name or "").strip()
    if normalized == "港股":
        return "hk"
    if normalized == "美股":
        return "us"
    if normalized == "基金":
        return "fund"
    return "a"
