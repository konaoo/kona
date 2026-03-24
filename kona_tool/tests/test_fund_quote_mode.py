import os
import sys
import json
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
KONA_TOOL = ROOT / "kona_tool"
if str(KONA_TOOL) not in sys.path:
    sys.path.insert(0, str(KONA_TOOL))

os.environ.setdefault("JWT_SECRET", "ci_test_jwt_secret")

from core.fund import get_fund_tiantian_price


class _Resp:
    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.status_code = status_code


class TestFundQuoteMode(unittest.TestCase):
    def test_tiantian_prefers_confirmed_dwjz_over_estimated_gsz(self):
        payload = {
            "fundcode": "017811",
            "dwjz": "1.8915",
            "gsz": "1.8787",
            "gszzl": "-0.67",
        }
        text = f"jsonpgz({json.dumps(payload)});"
        with patch("core.fund.monitored_http_get", return_value=_Resp(text)):
            price, yclose, amt, chg = get_fund_tiantian_price("f_017811")

        self.assertAlmostEqual(price, 1.8915, places=4)
        self.assertGreater(yclose, 0.0)
        self.assertAlmostEqual(amt, price - yclose, places=6)
        self.assertAlmostEqual(chg, (amt / yclose * 100), places=6)

    def test_tiantian_falls_back_to_gsz_when_dwjz_missing(self):
        payload = {
            "fundcode": "110017",
            "dwjz": "",
            "gsz": "1.2345",
            "gszzl": "0.80",
        }
        text = f"jsonpgz({json.dumps(payload)});"
        with patch("core.fund.monitored_http_get", return_value=_Resp(text)):
            price, *_ = get_fund_tiantian_price("f_110017")

        self.assertAlmostEqual(price, 1.2345, places=4)


if __name__ == "__main__":
    unittest.main()
