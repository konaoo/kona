"""
运行时启动入口（只在 `python app.py` 这种开发启动下用）。

约束：
- 这里可以启动后台线程/调度器；
- 但不要在 import 时就启动（否则 gunicorn / 单测导入会被副作用污染）。
"""

from __future__ import annotations

from typing import Any, Dict

import config
from core.price import PricePreloader


def run_dev_server(*, components: Dict[str, Any]) -> None:
    """
    复刻 app.py 原有 __main__ 行为：
    - 打印启动日志
    - 启动后台 scheduler / startup snapshot / 行情预取
    - app.run()
    """
    logger = components["logger"]
    app = components["app"]
    snapshot_runtime = components["snapshot_runtime"]
    startup_runtime = components["startup_runtime"]
    run_provider_test_report_job = components.get("run_provider_test_report_job")

    logger.info("Starting Portfolio Management System v10.0...")
    logger.info("Database: %s", config.DATABASE_PATH)
    logger.info("Server: http://%s:%s", config.HOST, config.PORT)

    startup_runtime.launch_runtime_services(
        enable_background_scheduler=bool(
            config.ENABLE_BACKGROUND_SNAPSHOT
            or (
                getattr(config, "ENABLE_BACKGROUND_PROVIDER_TEST", True)
                and run_provider_test_report_job is not None
            )
        ),
        background_scheduler_target=lambda: snapshot_runtime.background_scheduler(
            enable_background_snapshot_getter=lambda: bool(
                getattr(config, "ENABLE_BACKGROUND_SNAPSHOT", False)
            ),
            enable_background_provider_test_getter=lambda: bool(
                getattr(config, "ENABLE_BACKGROUND_PROVIDER_TEST", True)
                and run_provider_test_report_job is not None
            ),
        ),
        enable_startup_snapshot=bool(config.ENABLE_STARTUP_SNAPSHOT),
        startup_snapshot_target=lambda: snapshot_runtime.background_snapshot_runner(),
        preloader_factory=lambda db_path, interval: PricePreloader.get_instance(
            db_path=db_path,
            interval=interval,
        ),
        db_path=str(config.DATABASE_PATH),
        preload_interval=config.PRELOAD_INTERVAL_SECONDS,
        open_browser_target=lambda: startup_runtime.open_browser(
            f"http://{config.HOST}:{config.PORT}"
        ),
    )

    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)

