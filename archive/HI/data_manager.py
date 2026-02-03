"""
数据管理器 - 负责数据预加载、缓存和自动刷新

功能：
1. 登录后立即预加载所有数据
2. 数据缓存，避免重复请求
3. 每 30 秒自动刷新数据
4. 支持手动刷新
"""
import asyncio
import logging
import time
from typing import Optional, Callable, Dict, Any
from api import api
from state import AppState

logger = logging.getLogger(__name__)


class DataManager:
    """数据管理器 - 单例模式"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # 避免重复初始化
        if hasattr(self, '_initialized'):
            return

        self._initialized = True

        # 数据缓存
        self._home_data: Optional[Dict[str, Any]] = None
        self._portfolio_data: Optional[Dict[str, Any]] = None
        self._analysis_data: Optional[Dict[str, Any]] = None

        # 加载状态
        self._home_loading = False
        self._portfolio_loading = False
        self._analysis_loading = False

        # 数据时间戳
        self._home_timestamp = 0
        self._portfolio_timestamp = 0
        self._analysis_timestamp = 0

        # 自动刷新任务
        self._auto_refresh_task: Optional[asyncio.Task] = None
        self._is_auto_refresh_running = False

        # 回调函数
        self._on_home_updated: Optional[Callable] = None
        self._on_portfolio_updated: Optional[Callable] = None
        self._on_analysis_updated: Optional[Callable] = None

        # AppState 引用
        self._state: Optional[AppState] = None

    def set_state(self, state: AppState):
        """设置 AppState 引用"""
        self._state = state

    # ============================================================
    # 回调设置
    # ============================================================

    def set_on_home_updated(self, callback: Callable):
        """设置首页数据更新回调"""
        self._on_home_updated = callback

    def set_on_portfolio_updated(self, callback: Callable):
        """设置投资页数据更新回调"""
        self._on_portfolio_updated = callback

    def set_on_analysis_updated(self, callback: Callable):
        """设置分析页数据更新回调"""
        self._on_analysis_updated = callback

    # ============================================================
    # 数据获取（带缓存）
    # ============================================================

    def get_home_data(self) -> Optional[Dict[str, Any]]:
        """获取首页缓存数据"""
        return self._home_data

    def get_portfolio_data(self) -> Optional[Dict[str, Any]]:
        """获取投资页缓存数据"""
        return self._portfolio_data

    def get_analysis_data(self) -> Optional[Dict[str, Any]]:
        """获取分析页缓存数据"""
        return self._analysis_data

    # ============================================================
    # 数据加载
    # ============================================================

    async def load_home_data(self, force: bool = False) -> bool:
        """
        加载首页数据

        Args:
            force: 是否强制刷新（忽略缓存）

        Returns:
            是否成功
        """
        # 如果正在加载，避免重复请求
        if self._home_loading:
            return False

        # 如果有缓存且未强制刷新，直接返回
        if not force and self._home_data and (time.time() - self._home_timestamp < 30):
            logger.info("Using cached home data")
            return True

        self._home_loading = True

        try:
            # 使用 asyncio 包装同步 API 调用
            loop = asyncio.get_event_loop()

            def fetch_home():
                result = {"success": False, "data": None}

                def on_success(data):
                    result["success"] = True
                    result["data"] = data

                def on_error(error):
                    logger.error(f"Failed to load home data: {error}")

                # API 调用（在线程中执行）
                api.get_home_summary(on_success, on_error)

                # 等待回调完成（最多 5 秒）
                for _ in range(50):
                    if result["success"] or result["data"] is not None:
                        break
                    time.sleep(0.1)

                return result

            result = await loop.run_in_executor(None, fetch_home)

            if result["success"] and result["data"]:
                self._home_data = result["data"]
                self._home_timestamp = time.time()

                # 更新 AppState
                if self._state:
                    summary = result["data"].get("summary", {})
                    self._state.update_home_data(
                        total=summary.get("total_asset", 0),
                        cash=summary.get("total_cash", 0),
                        invest=summary.get("total_invest", 0),
                        other=summary.get("total_other", 0)
                    )

                # 触发回调
                if self._on_home_updated:
                    self._on_home_updated(self._home_data)

                logger.info("Home data loaded successfully")
                return True
            else:
                logger.warning("Failed to load home data")
                return False

        except Exception as e:
            logger.error(f"Error loading home data: {e}")
            return False
        finally:
            self._home_loading = False

    async def load_portfolio_data(self, force: bool = False) -> bool:
        """
        加载投资页数据

        Args:
            force: 是否强制刷新

        Returns:
            是否成功
        """
        if self._portfolio_loading:
            return False

        if not force and self._portfolio_data and (time.time() - self._portfolio_timestamp < 30):
            logger.info("Using cached portfolio data")
            return True

        self._portfolio_loading = True

        try:
            loop = asyncio.get_event_loop()

            def fetch_portfolio():
                result = {"success": False, "data": None, "prices": None}

                def on_success(data):
                    result["success"] = True
                    result["data"] = data.get("portfolio", [])
                    result["prices"] = data.get("prices", {})

                def on_error(error):
                    logger.error(f"Failed to load portfolio data: {error}")

                api.get_portfolio(on_success, on_error)

                for _ in range(50):
                    if result["success"] or result["data"] is not None:
                        break
                    time.sleep(0.1)

                return result

            result = await loop.run_in_executor(None, fetch_portfolio)

            if result["success"] and result["data"] is not None:
                self._portfolio_data = {
                    "portfolio": result["data"],
                    "prices": result["prices"]
                }
                self._portfolio_timestamp = time.time()

                # 更新 AppState
                if self._state:
                    self._state.update_portfolio(result["data"], result["prices"] or {})

                # 触发回调
                if self._on_portfolio_updated:
                    self._on_portfolio_updated(self._portfolio_data)

                logger.info("Portfolio data loaded successfully")
                return True
            else:
                logger.warning("Failed to load portfolio data")
                return False

        except Exception as e:
            logger.error(f"Error loading portfolio data: {e}")
            return False
        finally:
            self._portfolio_loading = False

    async def load_analysis_data(self, force: bool = False) -> bool:
        """
        加载分析页数据

        Args:
            force: 是否强制刷新

        Returns:
            是否成功
        """
        if self._analysis_loading:
            return False

        if not force and self._analysis_data and (time.time() - self._analysis_timestamp < 30):
            logger.info("Using cached analysis data")
            return True

        self._analysis_loading = True

        try:
            # 分析页数据加载逻辑（根据实际 API 调整）
            # TODO: 实现分析页数据加载
            logger.info("Analysis data loading not yet implemented")
            self._analysis_loading = False
            return False

        except Exception as e:
            logger.error(f"Error loading analysis data: {e}")
            return False
        finally:
            self._analysis_loading = False

    # ============================================================
    # 预加载和刷新
    # ============================================================

    async def preload_all(self):
        """
        预加载所有数据（登录后调用）

        并发加载首页、投资页、分析页数据
        """
        logger.info("Starting preload all data...")

        # 并发加载所有数据
        tasks = [
            self.load_home_data(force=True),
            self.load_portfolio_data(force=True),
            # self.load_analysis_data(force=True),  # 暂时注释，等实现后再开启
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        success_count = sum(1 for r in results if r is True)
        logger.info(f"Preload completed: {success_count}/{len(tasks)} succeeded")

    async def refresh_all(self):
        """
        刷新所有数据（手动刷新时调用）
        """
        logger.info("Refreshing all data...")
        await self.preload_all()

    # ============================================================
    # 自动刷新
    # ============================================================

    async def start_auto_refresh(self, interval: int = 30):
        """
        启动自动刷新（每 30 秒）

        Args:
            interval: 刷新间隔（秒）
        """
        if self._is_auto_refresh_running:
            logger.warning("Auto refresh already running")
            return

        self._is_auto_refresh_running = True
        logger.info(f"Starting auto refresh (interval: {interval}s)")

        async def auto_refresh_loop():
            while self._is_auto_refresh_running:
                await asyncio.sleep(interval)

                if self._is_auto_refresh_running:
                    logger.info("Auto refreshing data...")
                    await self.preload_all()

        self._auto_refresh_task = asyncio.create_task(auto_refresh_loop())

    def stop_auto_refresh(self):
        """停止自动刷新"""
        if self._auto_refresh_task:
            self._is_auto_refresh_running = False
            self._auto_refresh_task.cancel()
            logger.info("Auto refresh stopped")

    # ============================================================
    # 清理
    # ============================================================

    def clear_cache(self):
        """清除所有缓存"""
        self._home_data = None
        self._portfolio_data = None
        self._analysis_data = None

        self._home_timestamp = 0
        self._portfolio_timestamp = 0
        self._analysis_timestamp = 0

        logger.info("All cache cleared")


# 全局单例
data_manager = DataManager()
