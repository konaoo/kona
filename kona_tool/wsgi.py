"""
WSGI entrypoint for gunicorn.
"""

from app import app, price_runtime
import config

# 启动行情预取后台线程（gunicorn 模式）
price_runtime.start_preloader(config.PRELOAD_INTERVAL_SECONDS)
