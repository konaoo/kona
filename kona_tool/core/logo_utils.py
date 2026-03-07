from typing import Optional
import re

# 常见 Ticker 到域名的映射表（用于提高准确度）
TICKER_DOMAIN_MAP = {
    'AAPL': 'apple.com',
    'MSFT': 'microsoft.com',
    'GOOGL': 'google.com',
    'GOOG': 'google.com',
    'AMZN': 'amazon.com',
    'TSLA': 'tesla.com',
    'META': 'meta.com',
    'NVDA': 'nvidia.com',
    'NFLX': 'netflix.com',
    'BRK.B': 'berkshirehathaway.com',
    'V': 'visa.com',
    'MA': 'mastercard.com',
    'DIS': 'disney.com',
    'PYPL': 'paypal.com',
    'ADBE': 'adobe.com',
    'CRM': 'salesforce.com',
    'INTC': 'intel.com',
    'CSCO': 'cisco.com',
    'PEP': 'pepsico.com',
    'KO': 'cocacola.com',
    'AMD': 'amd.com',
    'BABA': 'alibaba.com',
    '9988': 'alibaba.com',
    'PDD': 'pinduoduo.com',
    'JD': 'jd.com',
    'TENCENT': 'tencent.com',
    '0700': 'tencent.com',
    '700': 'tencent.com',
    'NTES': '163.com',
    '9999': '163.com',
    'BIDU': 'baidu.com',
    '9888': 'baidu.com',
}

def suggest_logo_url(code: str, name: Optional[str] = None) -> Optional[str]:
    """
    根据资产代码和名称猜测 Logo URL。
    主要针对美股和知名公司。
    """
    if not code:
        return None
    
    code = code.upper().strip()
    
    # 常用前缀剥离 (富途/雪球等常见格式: gb_aapl, hk09988, sh600519)
    # 1. 匹配 gb_ticker, us_ticker
    if code.startswith(('GB_', 'US_')):
        code = code[3:]
    # 2. 匹配 hk09988 -> 9988
    elif code.startswith('HK') and code[2:].isdigit():
        code = code[2:].lstrip('0')
    # 3. 匹配 sh600519 -> 600519
    elif code.startswith(('SH', 'SZ')) and code[2:].isdigit():
        code = code[2:].lstrip('0')
    
    # 1. 检查内置映射表
    if code in TICKER_DOMAIN_MAP:
        return f"https://logo.clearbit.com/{TICKER_DOMAIN_MAP[code]}"
    
    # 2. 移除后缀（如 .US, .HK, .SS）进行猜测
    main_ticker = re.split(r'[\.\:]', code)[0]
    
    # 再次检查映射（针对剥离后缀后的情况）
    if main_ticker in TICKER_DOMAIN_MAP:
        return f"https://logo.clearbit.com/{TICKER_DOMAIN_MAP[main_ticker]}"
    
    # 如果是纯字母且长度在 1-5 之间，大概率是美股 Ticker
    if main_ticker.isalpha() and 1 <= len(main_ticker) <= 5:
        domain = f"{main_ticker.lower()}.com"
        return f"https://logo.clearbit.com/{domain}"
    
    return None
