"""
代码解析模块
智能解析各种证券代码格式
"""
import logging
import re
from typing import Optional, Dict

logger = logging.getLogger(__name__)


def parse_code(raw_code: str, curr: str = "") -> Dict[str, str]:
    """
    解析证券代码，添加适当的前缀并确定货币
    
    Args:
        raw_code: 原始代码
        curr: 原始货币代码
        
    Returns:
        包含 code 和 curr 的字典
    """
    if not raw_code:
        return {"code": "", "curr": ""}
    
    code = raw_code.strip()
    curr = curr.strip().upper() if curr else ""
    
    # 如果是纯数字
    if code.isdigit():
        # 11开头 -> 场外基金
        if code.startswith('11'):
            code = f"f_{code}"
            if not curr:
                curr = 'CNY'
        # 沪市: 60, 51, 90
        elif code.startswith(('6', '5', '9')):
            code = f"sh{code}"
            if not curr:
                curr = 'CNY'
        # 深市: 00, 30, 15, 16, 20
        elif code.startswith(('0', '3', '1', '2')):
            code = f"sz{code}"
            if not curr:
                curr = 'CNY'
        # 北交所: 4, 8
        elif code.startswith(('4', '8')):
            code = f"bj{code}"
            if not curr:
                curr = 'CNY'
    
    # 港股
    elif '.HK' in code.upper():
        # 保持 00175.HK 格式
        code = code.upper()
        if not curr:
            curr = 'HKD'
    
    # 美股（纯字母）
    elif code.isalpha() and '_' not in code:
        code = f"gb_{code.lower()}"
        if not curr:
            curr = 'USD'
    
    # 默认货币推断
    if not curr:
        if '.HK' in code.upper() or 'hk' in code.lower():
            curr = 'HKD'
        elif 'gb_' in code or 'ft_' in code:
            curr = 'USD'
        else:
            curr = 'CNY'
    
    logger.debug(f"Parsed code: {raw_code} -> {code}, currency: {curr}")
    
    return {"code": code, "curr": curr}


def get_display_code(code: str) -> str:
    """
    获取用于显示的代码（移除前缀）
    
    Args:
        code: 完整代码
        
    Returns:
        显示代码
    """
    display = code
    display = display.replace('f_', '')
    display = display.replace('ft_', '')
    display = display.replace('gb_', '')
    display = re.sub(r'^(sh|sz|hk|bj)', '', display, flags=re.IGNORECASE)
    return display