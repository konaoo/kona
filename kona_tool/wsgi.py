"""
WSGI entrypoint for gunicorn.
"""

from app import app
import config
from core.price import PricePreloader

# 启动行情预取后台线程（gunicorn 模式）
_preloader = PricePreloader.get_instance(
    db_path=str(config.DATABASE_PATH),
    interval=config.PRELOAD_INTERVAL_SECONDS,
)
_preloader.start()
