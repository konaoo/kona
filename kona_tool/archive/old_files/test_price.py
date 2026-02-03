import sys
import os
sys.path.append(os.getcwd())

from core.stock import get_stock_price
from core.price import get_price

# 测试用例
codes = [
    "00175.HK",   # 港股 - 吉利汽车
    "sh601088",   # A股 - 中国神华
    "gb_aapl",    # 美股 - 苹果
    "f_110011",   # 基金
    "hk00700"     # 港股 - 另一种格式
]

print("-" * 50)
print(f"{'Code':<15} {'Price':<10} {'PrevClose':<10} {'Change':<10}")
print("-" * 50)

for code in codes:
    try:
        # 使用 get_price (会自动分发)
        price, yclose, change, pct = get_price(code, use_cache=False)
        print(f"{code:<15} {price:<10.2f} {yclose:<10.2f} {change:<10.2f}")
    except Exception as e:
        print(f"{code:<15} Error: {e}")

print("-" * 50)
