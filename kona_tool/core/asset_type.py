"""
资产类型识别模块
统一判断 A股 / 美股 / 港股 / 基金
"""
import re
import logging
from typing import Optional

from .stock import get_us_asset_type

logger = logging.getLogger(__name__)


def _name_hint_is_fund(name: str) -> bool:
    n = (name or '').upper()
    return 'ETF' in n or '基金' in name or 'FUND' in n


def infer_asset_type(code: str, name: str = '') -> str:
    """
    根据代码 + 名称推断资产类型
    返回: a / us / hk / fund
    """
    c = (code or '').strip()
    if not c:
        return 'a'

    # 明确基金前缀
    if c.lower().startswith(('f_', 'ft_')):
        return 'fund'

    # 港股
    if '.HK' in c.upper() or c.lower().startswith('hk'):
        return 'hk'

    # 名称包含 ETF / 基金
    if _name_hint_is_fund(name):
        return 'fund'

    # 美股（gb_ 或 纯字母/点）
    if c.lower().startswith('gb_') or re.fullmatch(r'[A-Za-z\\.]+', c):
        us_type = get_us_asset_type(c)
        if us_type == 'fund':
            return 'fund'
        return 'us'

    # 其他默认 A 股
    return 'a'


def asset_type_label(asset_type: str) -> str:
    mapping = {
        'a': 'A股',
        'us': '美股',
        'hk': '港股',
        'fund': '基金',
    }
    return mapping.get(asset_type, 'A股')
