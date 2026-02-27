# -*- coding: utf-8 -*-
from pytdx.hq import TdxHq_API
from pytdx.exhq import TdxExHq_API
import pandas as pd

def test_a_stock():
    print("-" * 30)
    print("正在测试 A 股行情...")
    api = TdxHq_API()
    # 连接到招商证券深圳行情服务器（通常比较快）
    if api.connect('119.147.212.81', 7709):
        print("✅ A 股服务器连接成功！")
        # 获取 000001 (平安银行) 的行情
        # market: 0=深圳, 1=上海
        data = api.get_security_quotes([(0, '000001')])
        if data:
            print(f"📊 平安银行 (000001): 现价 {data[0]['price']} / 昨收 {data[0]['last_close']}")
        else:
            print("❌ 获取数据失败")
        api.disconnect()
    else:
        print("❌ A 股服务器连接失败")

def test_hk_us_stock():
    print("-" * 30)
    print("正在测试 港/美 股扩展行情...")
    api = TdxExHq_API()
    # 连接到通达信扩展行情服务器
    # 这个IP是通达信官方的一个扩展行情节点
    if api.connect('106.120.74.86', 7709):
        print("✅ 扩展行情服务器连接成功！")
        
        # 港股: 腾讯控股 (00700)
        # market: 31=港股
        print("正在获取腾讯控股...")
        hk_data = api.get_instrument_quote(31, '00700')
        if hk_data:
            print(f"📊 腾讯控股 (00700): 现价 {hk_data[0]['price']} / 昨收 {hk_data[0]['last_close']}")
        else:
            print("❌ 获取港股数据失败")

        # 美股: 苹果 (AAPL)
        # 难点：通达信的美股代码通常需要查表，且市场ID可能不同 (74=美股?)
        # 我们先尝试获取市场列表看看
        # print("正在获取市场列表...")
        # markets = api.get_markets()
        # print(markets)
        
        # 直接尝试获取 AAPL (通常在市场 74)
        print("正在获取苹果(AAPL)...")
        # 注意：通达信美股代码可能不直接是 AAPL，暂且一试
        us_data = api.get_instrument_quote(74, 'AAPL') 
        if us_data:
             print(f"📊 苹果 (AAPL): 现价 {us_data[0]['price']} / 昨收 {us_data[0]['last_close']}")
        else:
             print("⚠️ 获取美股直接代码失败 (通达信美股代码可能需要特殊映射)")

        api.disconnect()
    else:
        print("❌ 扩展行情服务器连接失败")

if __name__ == '__main__':
    try:
        test_a_stock()
        test_hk_us_stock()
    except Exception as e:
        print(f"❌ 发生异常: {e}")
        print("提示：请确保已运行 'pip3 install pytdx'")
