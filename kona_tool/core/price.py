"""
价格缓存和统一获取模块
提供价格数据的缓存和统一获取接口
"""
import time
import logging
import re
import threading
import os
from typing import Dict, Tuple, Optional, List, Any
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED, as_completed

import config
from .stock import get_stock_price
from .fund import get_fund_price
from .source_health import source_health
from .utils import monitored_http_get
from .utils import safe_float
from .policy_runtime import is_policy_enabled

try:
    import fcntl
except Exception:  # pragma: no cover
    fcntl = None

logger = logging.getLogger(__name__)


def _sina_headers() -> Dict[str, Any]:
    headers = dict(config.HEADERS)
    headers.setdefault("Referer", "https://finance.sina.com.cn")
    return headers


class PriceCache:
    """价格缓存类"""

    def __init__(self, ttl: int = 60, stale_ttl: int = 300, max_size: int = 0):
        """
        初始化缓存
        
        Args:
            ttl: 缓存过期时间（秒）
        """
        self.cache: Dict[str, Tuple[Tuple[float, float, float, float], float]] = {}
        self.ttl = ttl
        self.stale_ttl = max(stale_ttl, ttl)
        self.max_size = max(0, int(max_size or 0))
        self.evictions = 0
    
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
        self._evict_if_needed()
        logger.debug(f"Cache set for {code}")

    def _evict_if_needed(self) -> None:
        if self.max_size <= 0:
            return
        overflow = len(self.cache) - self.max_size
        if overflow <= 0:
            return
        items = sorted(self.cache.items(), key=lambda item: item[1][1])
        for idx in range(overflow):
            key = items[idx][0]
            if key in self.cache:
                del self.cache[key]
                self.evictions += 1

    def stats(self) -> Dict[str, Any]:
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "evictions": self.evictions,
            "ttl": self.ttl,
            "stale_ttl": self.stale_ttl,
        }
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
        logger.info("Cache cleared")


# 全局缓存实例
price_cache = PriceCache(
    ttl=config.CACHE_TTL,
    stale_ttl=config.CACHE_STALE_TTL,
    max_size=getattr(config, "PRICE_CACHE_MAX_SIZE", 0),
)

_runtime_lock = threading.Lock()
_runtime_metrics: Dict[str, Any] = {
    "cache_hits": 0,
    "stale_hits": 0,
    "network_fetch": 0,
    "network_fail": 0,
    "last_fetch_at": 0.0,
}

_FAST_BATCH_TIMEOUT_SECONDS = max(
    0.2,
    float(os.getenv("PRICE_BATCH_TIMEOUT_SECONDS", "0.6")),
)
_FAST_BATCH_MAX_WORKERS = max(
    4,
    int(os.getenv("PRICE_BATCH_MAX_WORKERS", "12")),
)
_FAST_BATCH_SLOW_CODE_EXTRA_TIMEOUT_SECONDS = max(
    0.2,
    float(os.getenv("PRICE_BATCH_SLOW_CODE_EXTRA_TIMEOUT_SECONDS", "1.6")),
)
_ASYNC_REFRESH_MAX_WORKERS = max(
    2,
    int(os.getenv("PRICE_ASYNC_REFRESH_WORKERS", "6")),
)
_async_refresh_executor = ThreadPoolExecutor(max_workers=_ASYNC_REFRESH_MAX_WORKERS)
_async_refresh_lock = threading.Lock()
_async_refresh_inflight: set[str] = set()


def _mark_metric(key: str, inc: int = 1) -> None:
    with _runtime_lock:
        _runtime_metrics[key] = int(_runtime_metrics.get(key, 0)) + inc
        _runtime_metrics["last_fetch_at"] = time.time()


def get_price_runtime_metrics() -> Dict[str, Any]:
    with _runtime_lock:
        metrics = dict(_runtime_metrics)
    metrics["cache"] = price_cache.stats()
    return metrics


def _normalize_code_key(code: Any) -> str:
    return str(code or "").strip()


def _unique_codes(codes: list) -> List[str]:
    seen = set()
    uniq: List[str] = []
    for raw in codes:
        code = _normalize_code_key(raw)
        if not code or code in seen:
            continue
        seen.add(code)
        uniq.append(code)
    return uniq


def _release_async_refresh(code: str) -> None:
    with _async_refresh_lock:
        _async_refresh_inflight.discard(code)


def _submit_async_refresh(code: str) -> None:
    normalized = _normalize_code_key(code)
    if not normalized:
        return
    with _async_refresh_lock:
        if normalized in _async_refresh_inflight:
            return
        _async_refresh_inflight.add(normalized)
    future = _async_refresh_executor.submit(get_price, normalized, False)
    future.add_done_callback(lambda _: _release_async_refresh(normalized))


def get_price_source_health() -> Dict[str, Dict[str, Any]]:
    return source_health.snapshot()


def _exchange_fund_candidates(code: str) -> List[str]:
    lower = str(code or "").strip().lower()
    if not lower.startswith("f_"):
        return []
    suffix = lower[2:].strip()
    if not re.fullmatch(r"\d{6}", suffix):
        return []
    # 11xxxx 里既有场外基金，也有沪市场内 ETF（如 511xxx）。
    # 只对已知场内段做交易所候选，避免把普通场外基金误纠正。
    if suffix.startswith("11") and not suffix.startswith(("511",)):
        return []
    if suffix.startswith(("15", "18")):
        return [f"sz{suffix}"]
    if suffix.startswith(("50", "51", "52", "56", "58", "511")):
        return [f"sh{suffix}"]
    return []


def is_exchange_fund_code(code: str) -> bool:
    """
    判断是否为“场内 ETF 的 f_ 代码”。

    仅针对 f_ 纯数字且落在场内 ETF 号段的代码返回 True。
    """
    return bool(_exchange_fund_candidates(code))


def _map_fund_code_to_exchange_if_tradable(code: str) -> str:
    candidates = _exchange_fund_candidates(code)
    if not candidates:
        return str(code or "")
    for candidate in candidates:
        try:
            price_data = get_stock_price(candidate)
        except Exception as exc:
            logger.debug("fund exchange probe failed code=%s candidate=%s error=%s", code, candidate, exc)
            continue
        if price_data and float(price_data[0] or 0.0) > 0:
            return candidate
    return str(code or "")


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
        mapped_code = _map_fund_code_to_exchange_if_tradable(code)
        if mapped_code != code:
            price_data = get_stock_price(mapped_code)
        else:
            price_data = get_fund_price(code)
            if not price_data or float(price_data[0] or 0.0) <= 0:
                # 场内 QDII/ETF 误标为 f_ 时，回退到交易所行情链路，避免长期显示无价。
                for candidate in _exchange_fund_candidates(code):
                    exchange_price = get_stock_price(candidate)
                    if exchange_price and float(exchange_price[0] or 0.0) > 0:
                        price_data = exchange_price
                        break
    
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


def batch_get_prices_fast(
    codes: list,
    timeout_seconds: Optional[float] = None,
) -> Dict[str, Tuple[float, float, float, float]]:
    """
    快速批量报价：
    - 优先返回 fresh cache
    - 对未命中的代码做短超时并发抓取
    - 超时后立即返回 stale/0，并异步继续刷新
    """
    normalized_codes = _unique_codes(codes)
    if not normalized_codes:
        return {}

    timeout_budget = (
        _FAST_BATCH_TIMEOUT_SECONDS if timeout_seconds is None else max(0.2, float(timeout_seconds))
    )
    max_workers = min(_FAST_BATCH_MAX_WORKERS, max(1, len(normalized_codes)))

    results: Dict[str, Tuple[float, float, float, float]] = {}
    stale_map: Dict[str, Tuple[float, float, float, float]] = {}
    missing_codes: List[str] = []

    for code in normalized_codes:
        cached = price_cache.get(code)
        if cached:
            results[code] = cached
            continue
        stale = price_cache.get_stale(code)
        if stale:
            stale_map[code] = stale
        missing_codes.append(code)

    if not missing_codes:
        return results

    executor = ThreadPoolExecutor(max_workers=max_workers)
    future_to_code = {
        executor.submit(get_price, code, False): code
        for code in missing_codes
    }
    done = set()
    not_done = set()
    unresolved_codes: List[str] = []
    try:
        done, not_done = wait(
            set(future_to_code.keys()),
            timeout=timeout_budget,
            return_when=FIRST_COMPLETED,
        )
        # 首轮有结果后继续尽量吃掉剩余已完成任务，直到超时预算结束。
        deadline = time.monotonic() + timeout_budget
        while done:
            current_done = list(done)
            done.clear()
            for future in current_done:
                code = future_to_code[future]
                try:
                    value = future.result()
                except Exception as exc:
                    logger.warning("fast batch get price failed code=%s err=%s", code, exc)
                    value = (0.0, 0.0, 0.0, 0.0)
                if value and float(value[0] or 0.0) > 0:
                    results[code] = value
                elif code in stale_map:
                    _mark_metric("stale_hits")
                    results[code] = stale_map[code]
                else:
                    results[code] = (0.0, 0.0, 0.0, 0.0)

            pending = {
                future
                for future, code in future_to_code.items()
                if code not in results and not future.done()
            }
            if not pending:
                break
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            done, not_done = wait(
                pending,
                timeout=remaining,
                return_when=FIRST_COMPLETED,
            )

        for future, code in future_to_code.items():
            if code in results:
                continue
            if future.done():
                try:
                    value = future.result()
                except Exception:
                    value = (0.0, 0.0, 0.0, 0.0)
                if value and float(value[0] or 0.0) > 0:
                    results[code] = value
                elif code in stale_map:
                    _mark_metric("stale_hits")
                    results[code] = stale_map[code]
                else:
                    results[code] = (0.0, 0.0, 0.0, 0.0)
            else:
                if _requires_extended_fast_wait(code):
                    try:
                        value = future.result(timeout=_FAST_BATCH_SLOW_CODE_EXTRA_TIMEOUT_SECONDS)
                    except Exception:
                        value = (0.0, 0.0, 0.0, 0.0)
                    if value and float(value[0] or 0.0) > 0:
                        results[code] = value
                        continue
                unresolved_codes.append(code)
                if code in stale_map:
                    _mark_metric("stale_hits")
                    results[code] = stale_map[code]
                else:
                    results[code] = (0.0, 0.0, 0.0, 0.0)
                future.cancel()
    finally:
        executor.shutdown(wait=False, cancel_futures=True)

    for code in unresolved_codes:
        _submit_async_refresh(code)

    return results


class PricePreloader:
    """
    后台预取线程：定时收集所有用户持有的证券代码，
    批量拉取行情并写入 PriceCache，确保 API 请求始终命中缓存。
    """

    _instance = None

    def __init__(self, db_manager: Any, interval: int = 30):
        self._db_manager = db_manager
        self._interval = interval
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock_file = str(
            getattr(
                config,
                "PRICE_PRELOADER_LOCK_FILE",
                "/tmp/kona_price_preloader.lock",
            )
        )
        self._lock_fd: Optional[int] = None

    @classmethod
    def get_instance(cls, db_manager: Any = None, interval: int = 30) -> 'PricePreloader':
        if cls._instance is None:
            cls._instance = cls(db_manager, interval)
        else:
            if db_manager is not None:
                cls._instance._db_manager = db_manager
            if interval:
                cls._instance._interval = interval
        return cls._instance

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            logger.info("PricePreloader already running, skip.")
            return
        if not getattr(config, "ENABLE_PRICE_PRELOADER", True):
            logger.info("PricePreloader disabled by config, skip.")
            return
        if not self._try_acquire_lock():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info(
            f"PricePreloader started (interval={self._interval}s)"
        )

    def stop(self) -> None:
        self._stop_event.set()
        self._release_lock()
        logger.info("PricePreloader stopping...")

    def _try_acquire_lock(self) -> bool:
        if fcntl is None:
            logger.info("PricePreloader lock unavailable; running without inter-process guard.")
            return True
        lock_path = self._lock_file or "/tmp/kona_price_preloader.lock"
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o644)
        except Exception as exc:
            logger.warning("PricePreloader lock open failed: %s", exc)
            return False
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            os.close(fd)
            logger.info("PricePreloader lock held by another process, skip.")
            return False
        except Exception as exc:
            os.close(fd)
            logger.warning("PricePreloader lock acquire failed: %s", exc)
            return False
        self._lock_fd = fd
        return True

    def _release_lock(self) -> None:
        if self._lock_fd is None:
            return
        try:
            if fcntl is not None:
                fcntl.flock(self._lock_fd, fcntl.LOCK_UN)
        except Exception:
            pass
        try:
            os.close(self._lock_fd)
        except Exception:
            pass
        self._lock_fd = None

    def _collect_codes(self) -> List[str]:
        """从数据库收集所有用户持有的唯一证券代码"""
        if self._db_manager is None:
            return []
        try:
            return self._db_manager.get_distinct_portfolio_codes()
        except Exception as exc:
            logger.error("PricePreloader failed to collect codes: %s", exc)
            return []

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
        r = monitored_http_get("sina_forex", url, headers=_sina_headers(), timeout=config.API_TIMEOUT)
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
            headers=_sina_headers(),
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
                        mapped = _map_fund_code_to_exchange_if_tradable(code)
                        result_code = mapped or code
                        results.append({
                            'code': result_code,
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
    alias_name_hints: Dict[str, str] = {}

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
                            mapped_code = _map_letter_fund_to_us_code(code)
                            alias_name = str(item.get('name', '') or '').strip()
                            if mapped_code and alias_name:
                                key = _code_key(mapped_code)
                                current = alias_name_hints.get(key, '')
                                alias_name_hints[key] = _pick_preferred_name(current, alias_name)
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
        key = _code_key(code)
        alias_name = alias_name_hints.get(key, '')
        if alias_name:
            item['name'] = _pick_preferred_name(str(item.get('name', '') or '').strip(), alias_name)
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

    quote_codes = [str(item.get('code', '') or '').strip() for item in final_results if str(item.get('code', '') or '').strip()]
    if quote_codes:
        elapsed_before_quote = time.monotonic() - started_at
        remaining_budget = max_wait_seconds - elapsed_before_quote
        # 搜索的第一优先级是尽快回结果，不要为了补右侧报价把 deadline 再拖满一轮。
        if remaining_budget >= 0.2:
            try:
                quote_timeout = min(0.8, remaining_budget)
                quote_map = batch_get_prices_fast(quote_codes, timeout_seconds=quote_timeout)
            except Exception as exc:
                logger.warning("search_stocks quote enrich failed query=%s error=%s", query, exc)
                quote_map = {}
        else:
            quote_map = {}

        for item in final_results:
            code = str(item.get('code', '') or '').strip()
            asset_type = str(item.get('asset_type') or '')
            if asset_type:
                item['market_type'] = asset_type
            if not code:
                continue
            quote = quote_map.get(code) or (0.0, 0.0, 0.0, 0.0)
            try:
                price = float(quote[0] or 0.0)
                yclose = float(quote[1] or 0.0)
                change = float(quote[2] or 0.0)
                change_pct = float(quote[3] or 0.0)
            except Exception:
                price, yclose, change, change_pct = 0.0, 0.0, 0.0, 0.0

            if price > 0:
                item['price'] = price
            if yclose > 0:
                item['yclose'] = yclose
            if price > 0 or yclose > 0 or change != 0.0:
                item['change'] = change
            if price > 0 or yclose > 0 or change_pct != 0.0:
                item['change_pct'] = change_pct

    def _final_sort_key(item):
        code = str(item.get('code') or '').lower()
        name = str(item.get('name') or '').lower()
        clean_code = code.replace('gb_', '').replace('.hk', '').replace('f_', '').replace('ft_', '')
        asset_type = str(item.get('asset_type') or '').lower()
        price = float(item.get('price') or 0.0)
        has_quote = 0 if price > 0 else 1
        fund_penalty = 1 if asset_type == 'fund' and price <= 0 else 0
        if query_lower == code or query_lower == clean_code:
            match_rank = 0
        elif name.startswith(query_lower):
            match_rank = 1
        elif query_lower in code or query_lower in clean_code:
            match_rank = 2
        else:
            match_rank = 3
        return (match_rank, has_quote, fund_penalty, 0 if asset_type != 'fund' else 1)

    final_results.sort(key=_final_sort_key)

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


def _map_letter_fund_to_us_code(code: str) -> str:
    lower = str(code or "").lower()
    if not lower.startswith("f_"):
        return ""
    suffix = lower[2:].strip()
    if not re.fullmatch(r"[a-z][a-z0-9.\-]*", suffix):
        return ""
    return f"gb_{suffix}"


def _code_key(code: str) -> str:
    return str(code or "").strip().lower()


def _pick_preferred_name(current: str, incoming: str) -> str:
    cur = str(current or "").strip()
    inc = str(incoming or "").strip()
    if not cur:
        return inc
    if not inc:
        return cur
    return inc if len(inc) > len(cur) else cur


def _requires_extended_fast_wait(code: str) -> bool:
    normalized = str(code or "").strip().lower()
    if normalized.startswith("ft_"):
        return True
    return normalized.startswith("gb_") and any(ch in normalized for ch in [".", "-"])


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
