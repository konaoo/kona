"""
全局数据缓存管理器
- 应用启动时预加载数据
- 缓存 API 响应，减少网络请求
- 后台自动刷新数据
"""
import threading
import time
from typing import Dict, List, Any, Optional, Callable
from api import api


class DataCache:
    """全局数据缓存"""
    
    # 缓存过期时间（秒）
    CACHE_TTL = {
        "history": 300,      # 5 分钟
        "portfolio": 60,     # 1 分钟
        "prices": 30,        # 30 秒
        "news": 120,         # 2 分钟
        "analysis": 60,      # 1 分钟
    }
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._timestamps: Dict[str, float] = {}
        self._loading: Dict[str, bool] = {}
        self._callbacks: Dict[str, List[Callable]] = {}
        self._lock = threading.Lock()
    
    def _is_expired(self, key: str, ttl_key: str = None) -> bool:
        """检查缓存是否过期"""
        if key not in self._timestamps:
            return True
        ttl = self.CACHE_TTL.get(ttl_key or key.split("_")[0], 60)
        return time.time() - self._timestamps[key] > ttl
    
    def _set_cache(self, key: str, data: Any):
        """设置缓存"""
        with self._lock:
            self._cache[key] = data
            self._timestamps[key] = time.time()
            self._loading[key] = False
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存数据"""
        return self._cache.get(key)
    
    def has_valid_cache(self, key: str, ttl_key: str = None) -> bool:
        """检查是否有有效缓存"""
        return key in self._cache and not self._is_expired(key, ttl_key)
    
    # ============================================================
    # 历史数据（首页）
    # ============================================================
    
    def get_history(self, callback: Callable = None, force_refresh: bool = False):
        """获取历史数据"""
        key = "history"
        
        # 有缓存且未过期，直接返回
        if not force_refresh and self.has_valid_cache(key):
            if callback:
                callback(self._cache[key])
            return
        
        # 正在加载中，添加回调
        if self._loading.get(key):
            if callback:
                self._callbacks.setdefault(key, []).append(callback)
            return
        
        self._loading[key] = True
        
        def on_success(data):
            self._set_cache(key, data)
            if callback:
                callback(data)
            # 执行等待中的回调
            for cb in self._callbacks.pop(key, []):
                cb(data)
        
        def on_error(err):
            self._loading[key] = False
            print(f"Cache: history load failed: {err}")
        
        api.get_history(on_success=on_success, on_error=on_error)
    
    # ============================================================
    # 投资组合
    # ============================================================
    
    def get_portfolio_sync(self, force_refresh: bool = False) -> tuple:
        """同步获取投资组合（带缓存）"""
        key_portfolio = "portfolio"
        key_prices = "prices"
        
        # 有缓存且未过期
        if not force_refresh:
            if self.has_valid_cache(key_portfolio) and self.has_valid_cache(key_prices):
                return self._cache[key_portfolio], self._cache[key_prices]
        
        # 同步获取
        portfolio, prices = api.get_portfolio_sync()
        
        if portfolio:
            self._set_cache(key_portfolio, portfolio)
        if prices:
            self._set_cache(key_prices, prices)
        
        return portfolio, prices
    
    # ============================================================
    # 快讯
    # ============================================================
    
    def get_news(self, callback: Callable = None, force_refresh: bool = False):
        """获取快讯（带缓存）"""
        key = "news"
        
        # 有缓存且未过期，直接返回
        if not force_refresh and self.has_valid_cache(key):
            if callback:
                callback(self._cache[key])
            return
        
        # 正在加载中
        if self._loading.get(key):
            if callback:
                self._callbacks.setdefault(key, []).append(callback)
            return
        
        self._loading[key] = True
        
        def on_success(data):
            self._set_cache(key, data)
            if callback:
                callback(data)
            for cb in self._callbacks.pop(key, []):
                cb(data)
        
        def on_error(err):
            self._loading[key] = False
            if callback:
                callback(None)
        
        api.get_news(on_success=on_success, on_error=on_error)
    
    # ============================================================
    # 分析数据
    # ============================================================
    
    def get_analysis_overview(self) -> Dict:
        """获取分析概览（带缓存）"""
        key = "analysis_overview"
        
        if self.has_valid_cache(key, "analysis"):
            return self._cache[key]
        
        data = api.get_analysis_overview_sync()
        if data:
            self._set_cache(key, data)
        return data or {}
    
    def get_analysis_calendar(self, time_type: str) -> Dict:
        """获取收益日历（带缓存）"""
        key = f"analysis_calendar_{time_type}"
        
        if self.has_valid_cache(key, "analysis"):
            return self._cache[key]
        
        data = api.get_analysis_calendar_sync(time_type)
        if data:
            self._set_cache(key, data)
        return data or {}
    
    def get_analysis_rank(self, market: str = "all") -> Dict:
        """获取盈亏排行（带缓存）"""
        key = f"analysis_rank_{market}"
        
        if self.has_valid_cache(key, "analysis"):
            return self._cache[key]
        
        data = api.get_analysis_rank_sync(market)
        if data:
            self._set_cache(key, data)
        return data or {}
    
    # ============================================================
    # 预加载
    # ============================================================
    
    def preload_all(self):
        """预加载所有常用数据（后台执行）"""
        def do_preload():
            print("Cache: preloading data...")
            
            # 预加载历史数据
            self.get_history()
            
            # 预加载投资组合 (这会解决首次加载慢的问题)
            self.get_portfolio_sync(force_refresh=True)
            
            # 预加载快讯
            self.get_news()
            
            # 预加载分析数据
            self.get_analysis_overview()
            
            print("Cache: preload complete")
        
        threading.Thread(target=do_preload, daemon=True).start()
    
    def clear(self):
        """清除所有缓存"""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()


# 全局缓存实例
cache = DataCache()
