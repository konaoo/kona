"""
资产类型识别模块
统一判断 A股 / 美股 / 港股 / 基金
"""
import re
import logging

logger = logging.getLogger(__name__)


def _name_hint_is_fund(name: str) -> bool:
    n = (name or '').upper()
    return 'ETF' in n or '基金' in name or 'FUND' in n


def _is_exchange_fund_code(code: str) -> bool:
    lower = (code or '').strip().lower()
    if not lower.startswith(('sh', 'sz', 'bj')):
        return False
    suffix = lower[2:]
    if not re.fullmatch(r'\d{6}', suffix):
        return False
    if suffix.startswith(('15', '16', '18')):
        return True
    if suffix.startswith(('50', '51', '52', '56', '58')):
        return True
    return False


def infer_asset_type(code: str, name: str = '') -> str:
    """
    根据代码 + 名称推断资产类型
    返回: a / us / hk / fund
    """
    c = (code or '').strip()
    if not c:
        return 'a'
    lower = c.lower()

    # FT 基金（ISIN）一律基金
    if lower.startswith('ft_'):
        return 'fund'

    # f_ 仅允许纯数字场外基金代码；字母型 f_ 视为误标，按美股处理
    if lower.startswith('f_'):
        suffix = c[2:].strip()
        if re.fullmatch(r'\d+', suffix):
            return 'fund'
        if re.fullmatch(r'[A-Za-z][A-Za-z0-9.\-]*', suffix):
            return 'us'
        return 'fund'

    # A 股（含场内基金/ETF）前缀
    if lower.startswith(('sh', 'sz', 'bj')):
        return 'a'

    # 美股代码前缀
    if lower.startswith('gb_'):
        return 'us'

    # 港股
    if '.HK' in c.upper() or c.lower().startswith('hk'):
        return 'hk'
    if re.fullmatch(r'\d{5}', c):
        return 'hk'
    if re.fullmatch(r'\d{6}', c):
        return 'a'

    # 美股（纯字母 / 点号 / 横杠）
    if re.fullmatch(r'[A-Za-z][A-Za-z0-9.\-]*', c):
        return 'us'

    # 无明确市场代码时，名称提示基金
    if _name_hint_is_fund(name):
        return 'fund'

    # 其他默认 A 股
    return 'a'


def infer_category_type(code: str, name: str = '', asset_type: str = '') -> str:
    """
    根据产品属性推断“统计/筛选分类”。

    这里和交易市场故意分开：
    - 交易代码仍可走 sh/sz 场内链路
    - 但场内 ETF / LOF / REIT 这类基金产品，统计时仍归到 fund
    """
    normalized_asset_type = str(asset_type or '').strip().lower()
    if normalized_asset_type in {'us', 'hk'}:
        return normalized_asset_type
    if normalized_asset_type == 'fund':
        return 'fund'

    if str(code or '').strip().lower().startswith(('f_', 'ft_')):
        return 'fund'

    if _is_exchange_fund_code(code) and _name_hint_is_fund(name):
        return 'fund'

    inferred = infer_asset_type(code, name)
    return 'fund' if inferred == 'fund' else inferred


def asset_type_label(asset_type: str) -> str:
    mapping = {
        'a': 'A股',
        'us': '美股',
        'hk': '港股',
        'fund': '基金',
    }
    return mapping.get(asset_type, 'A股')
