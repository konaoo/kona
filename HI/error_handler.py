"""
全局异常处理模块
"""
import logging
import traceback
import sys
from typing import Callable, Optional, Any
from functools import wraps
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app_error.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class AppError(Exception):
    """应用基础异常"""
    pass


class APIError(AppError):
    """API 请求异常"""
    def __init__(self, message: str, status_code: int = None, endpoint: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.endpoint = endpoint


class CacheError(AppError):
    """缓存异常"""
    pass


class NetworkError(AppError):
    """网络连接异常"""
    pass


def handle_exception(
    exc_type: type,
    exc_value: BaseException,
    exc_traceback: Any
):
    """全局异常处理器"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.error(
        f"Uncaught exception: {exc_type.__name__}: {str(exc_value)}",
        exc_info=(exc_type, exc_value, exc_traceback)
    )


def safe_execute(
    fallback: Any = None,
    error_message: str = None,
    log_error: bool = True
) -> Callable:
    """装饰器：安全执行函数，捕获所有异常"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except AppError as e:
                if log_error:
                    logger.error(f"AppError in {func.__name__}: {e}")
                if error_message:
                    print(error_message)
                return fallback
            except Exception as e:
                if log_error:
                    logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
                if error_message:
                    print(error_message)
                return fallback
        return wrapper
    return decorator


def log_exception(
    func: Callable = None,
    on_error: Callable[[Exception], Any] = None
):
    """装饰器：记录异常但不捕获"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {f.__name__}: {e}", exc_info=True)
                if on_error:
                    on_error(e)
                raise
        return wrapper
    return decorator

    if func:
        return decorator(func)
    return decorator


def setup_global_exception_handler():
    """设置全局异常处理器"""
    sys.excepthook = handle_exception


def log_api_error(endpoint: str, error: Exception, additional_info: str = None):
    """记录 API 错误"""
    error_info = {
        'timestamp': datetime.now().isoformat(),
        'endpoint': endpoint,
        'error_type': type(error).__name__,
        'error_message': str(error),
        'additional_info': additional_info
    }
    logger.error(f"API Error: {error_info}")
