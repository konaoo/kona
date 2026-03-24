"""价格预取运行时管理器。

统一收口行情预取线程的启动与关闭，避免散落在入口里。
"""

from __future__ import annotations

from typing import Any, Callable

from core.price import PricePreloader


class PriceRuntime:
    def __init__(
        self,
        *,
        logger: Any,
        db: Any,
        preloader_factory: Callable[[Any, int], Any] | None = None,
    ) -> None:
        self.logger = logger
        self.db = db
        self.preloader_factory = preloader_factory or (
            lambda db_manager, interval: PricePreloader.get_instance(
                db_manager=db_manager,
                interval=interval,
            )
        )
        self._preloader = None

    def start_preloader(self, interval: int) -> Any:
        if self._preloader is None:
            self._preloader = self.preloader_factory(self.db, interval)
        try:
            self._preloader.start()
        except Exception as exc:
            self.logger.warning("Price preloader start failed: %s", exc)
        return self._preloader

    def stop_preloader(self) -> None:
        if not self._preloader:
            return
        try:
            self._preloader.stop()
        except Exception as exc:
            self.logger.warning("Price preloader stop failed: %s", exc)


def create_price_runtime(**kwargs) -> PriceRuntime:
    return PriceRuntime(**kwargs)
