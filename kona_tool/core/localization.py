"""
本地化与翻译引擎
提供基金名称、资产类型的翻译和中文化功能。
"""
import re
from typing import Dict, List, Tuple

# 常用基金品牌词典 (Fund House)
# 优先级从高到低排列
FUND_HOUSES: Dict[str, str] = {
    r"Allianz": "安联",
    r"BlackRock": "贝莱德",
    r"Blackrock": "贝莱德",
    r"J\.?P\.?\s?Morgan": "摩根大通",
    r"JPM": "摩根",
    r"Fidelity": "富达",
    r"Schroder": "施罗德",
    r"Templeton": "邓普顿",
    r"Franklin": "富兰克林",
    r"PIMCO": "品浩",
    r"Goldman\s?Sachs": "高盛",
    r"Morgan\s?Stanley": "摩根士丹利",
    r"Pictet": "百达",
    r"UBS": "瑞银",
    r"HSBC": "汇丰",
    r"Amundi": "东方汇理",
    r"Invesco": "景顺",
    r"Henderson": "亨德森",
    r"Janus": "骏利",
    r"First\s?Sentier": "首源",
    r"Principal": "信安",
    r"DWS": "德意志",
    r"Nomura": "野村",
    r"Aberdeen": "安本",
    r"M&G": "安安",
    r"Ninety One": "晋达",
    r"Jupiter": "木星",
}

# 投资策略与主题 (Strategy / Theme)
STRATEGIES: Dict[str, str] = {
    r"Income and Growth": "收益成长",
    r"Income & Growth": "收益成长",
    r"World Energy": "世界能源",
    r"World Gold": "世界黄金",
    r"World Mining": "世界矿业",
    r"Global Equity": "全球股票",
    r"Global Bond": "全球债券",
    r"China Equity": "中国股票",
    r"China Bond": "中国债券",
    r"US Growth": "美国成长",
    r"US Value": "美国价值",
    r"Emerging Markets": "新兴市场",
    r"Sustainable": "可持续",
    r"ESG": "ESG",
    r"Technology": "科技",
    r"Health\s?care": "医疗保健",
    r"Consumer": "消费",
    r"Financials": "金融",
    r"Real Estate": "房地产",
    r"Small Cap": "小盘股",
    r"Multi-Asset": "多元资产",
    r"Strategic Income": "战略收益",
}

# 份额类别与后缀 (Share Classes / Suffixes)
SHARE_CLASSES: Dict[str, str] = {
    r"Class AM": "AM类",
    r"Class AT": "AT类",
    r"Class A": "A类",
    r"Class C": "C类",
    r"Dis": "派息",
    r"Acc": "累积",
    r"Inc": "收益型",
    r"USD": "美元",
    r"HKD": "港币",
    r"CNH": "离岸人民币",
    r"EUR": "欧元",
    r"H2": "对冲",
    r"Stable": "稳定",
    r"Monthly": "月收",
}

def translate_fund_name(name: str) -> str:
    """
    将基金英文名称转换为中文。
    支持品牌、策略、份额类别的组合转换。
    """
    if not name or name.startswith("ISIN:"):
        return name
        
    original_name = name.strip()
    translated = original_name
    
    # 0. 清理冗余词
    translated = re.sub(r"Global Investors", "", translated, flags=re.IGNORECASE)
    translated = re.sub(r"Investment Funds", "", translated, flags=re.IGNORECASE)
    
    # 1. 替换品牌名 (Fund House)
    for pattern, cn in FUND_HOUSES.items():
        translated = re.sub(pattern, cn, translated, flags=re.IGNORECASE)
        
    # 2. 替换主要策略与主题
    for pattern, cn in STRATEGIES.items():
        translated = re.sub(pattern, cn, translated, flags=re.IGNORECASE)
        
    # 3. 替换份额与货币后缀
    for pattern, cn in SHARE_CLASSES.items():
        translated = re.sub(pattern, cn, translated, flags=re.IGNORECASE)
        
    # 4. 特殊清理 (如 "Fund" 后缀)
    translated = re.sub(r"Fund", "基金", translated, flags=re.IGNORECASE)
    
    # 移除多余空格和特殊符号
    translated = re.sub(r" - ", " ", translated)
    translated = re.sub(r"\s+", "", translated).strip()
    
    # 如果翻译后没变化或变化太小，返回原始名称，避免垃圾翻译
    if translated == original_name:
        return original_name
        
    return translated
