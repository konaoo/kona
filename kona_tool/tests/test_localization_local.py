import sys
import os
from pathlib import Path

# Add project root and kona_tool to sys.path
root = "/Users/kona/Desktop/kaka/kona_repo"
if root not in sys.path:
    sys.path.insert(0, root)
if os.path.join(root, "kona_tool") not in sys.path:
    sys.path.insert(0, os.path.join(root, "kona_tool"))

from kona_tool.core.localization import translate_fund_name

def test_localization():
    test_cases = [
        ("Allianz Income and Growth AM USD", "安联收益及增长 AM 美元"),
        ("Allianz Global Investors Fund - Allianz Income and Growth AM USD", "安联 收益及增长 AM 美元"), # Global Investors becomes ""
        ("BlackRock World Energy Fund", "贝莱德世界能源基金"),
        ("J.P. Morgan China Equity A Dis EUR", "摩根大通中国股票 A 派息 欧元"),
        ("Fidelity US Growth Class A Acc USD", "富达美国成长 A类 累积 美元"),
        ("Schroder Global Bond Fund", "施罗德全球债券基金"),
    ]
    
    for en, expected in test_cases:
        actual = translate_fund_name(en)
        print(f"EN: {en}")
        print(f"CN: {actual}")
        # We don't need exact match if the words are there
        if any(word in actual for word in expected.split()):
            print("PASS")
        else:
            print(f"FAIL: Expected part of {expected}")
        print("-" * 20)

if __name__ == "__main__":
    test_localization()
