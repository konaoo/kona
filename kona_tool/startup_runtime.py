"""启动期运行时支撑。

负责承接：
- 运行指标令牌校验
- 浏览器自动打开
- 启动时后台线程拉起
"""

from __future__ import annotations

import secrets
import threading
import time
import webbrowser
from typing import Any, Callable, Mapping


class StartupRuntime:
    """封装启动期零散支撑逻辑。"""

    def __init__(
        self,
        *,
        logger: Any,
        thread_factory: Callable[..., Any] | None = None,
        sleep_func: Callable[[float], None] | None = None,
        browser_open_func: Callable[[str], Any] | None = None,
    ) -> None:
        self.logger = logger
        self.thread_factory = thread_factory or threading.Thread
        self.sleep_func = sleep_func or time.sleep
        self.browser_open_func = browser_open_func or webbrowser.open

    def metrics_token_ok(self, expected_token: str, headers: Mapping[str, str]) -> bool:
        if not expected_token:
            return True
        token = str(headers.get("X-Kona-Metrics-Token", "") or "").strip()
        if not token:
            auth_header = str(headers.get("Authorization", "") or "").strip()
            if auth_header.lower().startswith("bearer "):
                token = auth_header.split(" ", 1)[1].strip()
        if not token:
            return False
        return secrets.compare_digest(token, expected_token)

    def open_browser(self, url: str, delay_seconds: float = 1.5) -> None:
        self.sleep_func(delay_seconds)
        self.browser_open_func(url)

    def start_thread(self, *, target: Callable[[], Any], daemon: bool = True):
        thread = self.thread_factory(target=target, daemon=daemon)
        thread.start()
        return thread

    def launch_runtime_services(
        self,
        *,
        enable_background_scheduler: bool,
        background_scheduler_target: Callable[[], Any],
        enable_startup_snapshot: bool,
        startup_snapshot_target: Callable[[], Any],
        preloader_start: Callable[[int], Any],
        preload_interval: int,
        open_browser_target: Callable[[], Any],
    ) -> Any:
        if enable_background_scheduler:
            self.start_thread(target=background_scheduler_target)
        else:
            self.logger.info("Background scheduler disabled.")

        if enable_startup_snapshot:
            self.start_thread(target=startup_snapshot_target)

        preloader = preloader_start(preload_interval)

        self.start_thread(target=open_browser_target)
        return preloader


def create_startup_runtime(**kwargs) -> StartupRuntime:
    return StartupRuntime(**kwargs)
