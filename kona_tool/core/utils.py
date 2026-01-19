"""
工具函数模块
提供安全的数据转换和通用工具函数
"""
import re
import time
import logging
from typing import Optional, Dict, Any
from functools import wraps

logger = logging.getLogger(__name__)


def safe_float(value: Any) -> float:
    """
    安全地将任意值转换为浮点数
    
    Args:
        value: 要转换的值
        
    Returns:
        转换后的浮点数，失败返回0.0
    """
    try:
        if value is None:
            return 0.0
        s = str(value).replace(',', '').strip()
        if not s or s == '-' or s == '--':
            return 0.0
        match = re.search(r"[-+]?\d*\.\d+|\d+", s)
        return float(match.group()) if match else 0.0
    except Exception as e:
        logger.warning(f"Failed to convert {value} to float: {e}")
        return 0.0


def safe_int(value: Any) -> int:
    """
    安全地将任意值转换为整数
    
    Args:
        value: 要转换的值
        
    Returns:
        转换后的整数，失败返回0
    """
    return int(safe_float(value))


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, 
                     exceptions: tuple = (Exception,)):
    """
    重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 重试延迟（秒）
        exceptions: 需要重试的异常类型
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(f"Retry {attempt + 1}/{max_retries} for {func.__name__}: {e}")
                        time.sleep(delay)
                    else:
                        logger.error(f"Max retries ({max_retries}) reached for {func.__name__}")
            raise last_exception if last_exception else Exception("Unknown error")
        return wrapper
    return decorator


def get_first_valid_price(data_list: list, index_priority: list) -> float:
    """
    从数据列表中获取第一个有效的价格
    
    Args:
        data_list: 数据列表
        index_priority: 索引优先级列表
        
    Returns:
        第一个有效的价格，没有则返回0.0
    """
    for idx in index_priority:
        if idx < len(data_list):
            val = safe_float(data_list[idx])
            if val > 0:
                return val
    return 0.0


def format_number(value: float, precision: int = 2) -> str:
    """
    格式化数字显示
    
    Args:
        value: 要格式化的数字
        precision: 小数位数
        
    Returns:
        格式化后的字符串
    """
    try:
        return f"{value:.{precision}f}"
    except Exception:
        return str(value)


def calculate_percentage_change(current: float, previous: float) -> float:
    """
    计算百分比变化
    
    Args:
        current: 当前值
        previous: 之前的值
        
    Returns:
        百分比变化，previous为0时返回0.0
    """
    if previous == 0:
        return 0.0
    try:
        return ((current - previous) / previous) * 100
    except Exception:
        return 0.0


def normalize_code(code: str) -> str:
    """
    标准化证券代码
    
    Args:
        code: 原始代码
        
    Returns:
        标准化后的代码（小写，去除空格）
    """
    if not code:
        return ""
    return code.strip().lower()