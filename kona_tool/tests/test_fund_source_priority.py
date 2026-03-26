import os
import sys
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
KONA_TOOL = ROOT / "kona_tool"
if str(KONA_TOOL) not in sys.path:
    sys.path.insert(0, str(KONA_TOOL))

os.environ.setdefault("JWT_SECRET", "ci_test_jwt_secret")

from core.fund import get_fund_overseas_history_points, get_fund_price


class _JsonResp:
    def __init__(self, data, status_code=200):
        self._data = data
        self.status_code = status_code
        self.text = data if isinstance(data, str) else ""

    def json(self):
        return self._data


class _TextResp:
    def __init__(self, text: str, status_code=200):
        self.text = text
        self.status_code = status_code


class TestFundSourcePriority(unittest.TestCase):
    def test_fidelity_history_parser_reads_historical_nav_rows(self):
        from core.fund import get_fidelity_history_points

        payload = {
            "items": [
                {"date": "2026-03-25", "nav": "9.22", "changePercent": "0.66"},
                {"date": "2026-03-24", "nav": "9.16", "changePercent": "-0.76"},
                {"date": "2026-03-23", "nav": "9.23", "changePercent": "0.65"},
            ]
        }
        with patch("core.fund.monitored_http_get", return_value=_JsonResp(payload)):
            points = get_fidelity_history_points("LU1116320737", limit=2)

        self.assertEqual(
            points,
            [
                {"date": "2026-03-24", "value": 9.16},
                {"date": "2026-03-25", "value": 9.22},
            ],
        )

    def test_otc_fund_prefers_f10_confirmed_nav(self):
        with patch("core.fund.get_fund_eastmoney_f10", return_value=(1.5904, 1.5225, 0.0679, 4.46)) as f10_mock, patch(
            "core.fund.get_fund_tencent_jj",
            return_value=(1.5225, 1.6000, -0.0775, -4.84),
        ) as tencent_mock, patch(
            "core.fund.get_fund_tiantian_price",
            return_value=(1.2345, 1.2300, 0.0045, 0.36),
        ) as tiantian_mock:
            price, yclose, amt, chg = get_fund_price("f_025209")

        self.assertAlmostEqual(price, 1.5904, places=4)
        self.assertAlmostEqual(yclose, 1.5225, places=4)
        self.assertAlmostEqual(amt, 0.0679, places=4)
        self.assertAlmostEqual(chg, 4.46, places=2)
        f10_mock.assert_called_once()
        tencent_mock.assert_not_called()
        tiantian_mock.assert_not_called()

    def test_otc_fund_fallbacks_to_tiantian_when_f10_missing(self):
        with patch("core.fund.get_fund_eastmoney_f10", return_value=(0.0, 0.0, 0.0, 0.0)) as f10_mock, patch(
            "core.fund.get_fund_tencent_jj",
            return_value=(0.0, 0.0, 0.0, 0.0),
        ) as tencent_mock, patch(
            "core.fund.get_fund_tiantian_price",
            return_value=(1.2345, 1.2300, 0.0045, 0.36),
        ) as tiantian_mock:
            price, yclose, amt, chg = get_fund_price("f_110017")

        self.assertAlmostEqual(price, 1.2345, places=4)
        self.assertAlmostEqual(yclose, 1.2300, places=4)
        self.assertAlmostEqual(amt, 0.0045, places=4)
        self.assertAlmostEqual(chg, 0.36, places=2)
        tiantian_mock.assert_called_once()
        tencent_mock.assert_not_called()
        f10_mock.assert_called_once()

    def test_otc_fund_fallbacks_to_tencent_when_f10_and_tiantian_zero(self):
        with patch("core.fund.get_fund_eastmoney_f10", return_value=(0.0, 0.0, 0.0, 0.0)) as f10_mock, patch(
            "core.fund.get_fund_tiantian_price",
            return_value=(0.0, 0.0, 0.0, 0.0),
        ) as tiantian_mock, patch(
            "core.fund.get_fund_tencent_jj",
            return_value=(1.2345, 1.2300, 0.0045, 0.36),
        ) as tencent_mock:
            price, yclose, amt, chg = get_fund_price("f_110017")

        self.assertAlmostEqual(price, 1.2345, places=4)
        self.assertAlmostEqual(yclose, 1.2300, places=4)
        self.assertAlmostEqual(amt, 0.0045, places=4)
        self.assertAlmostEqual(chg, 0.36, places=2)
        tiantian_mock.assert_called_once()
        f10_mock.assert_called_once()
        tencent_mock.assert_called_once()

    def test_968_overseas_fund_prefers_overseas_html_before_tencent(self):
        with patch("core.fund.get_fund_eastmoney_f10", return_value=(0.0, 0.0, 0.0, 0.0)) as f10_mock, patch(
            "core.fund.get_fund_tiantian_price",
            return_value=(0.0, 0.0, 0.0, 0.0),
        ) as tiantian_mock, patch(
            "core.fund.get_fund_eastmoney_mobile",
            return_value=(0.0, 0.0, 0.0, 0.0),
        ) as mobile_mock, patch(
            "core.fund.get_fund_overseas_html",
            return_value=(10.46, 10.44, 0.02, 0.19),
        ) as overseas_mock, patch(
            "core.fund.get_fund_tencent_jj",
            return_value=(10.44, 10.49, -0.05, -0.48),
        ) as tencent_mock:
            price, yclose, amt, chg = get_fund_price("f_968163")

        self.assertAlmostEqual(price, 10.46, places=2)
        self.assertAlmostEqual(yclose, 10.44, places=2)
        self.assertAlmostEqual(amt, 0.02, places=2)
        self.assertAlmostEqual(chg, 0.19, places=2)
        f10_mock.assert_called_once()
        tiantian_mock.assert_not_called()
        mobile_mock.assert_not_called()
        overseas_mock.assert_called_once()
        tencent_mock.assert_not_called()

    def test_968_overseas_fund_prefers_overseas_html_before_tiantian(self):
        with patch("core.fund.get_fund_eastmoney_f10", return_value=(0.0, 0.0, 0.0, 0.0)) as f10_mock, patch(
            "core.fund.get_fund_overseas_html",
            return_value=(17.96, 17.85, 0.11, 0.62),
        ) as overseas_mock, patch(
            "core.fund.get_fund_tiantian_price",
            return_value=(17.85, 17.85, 0.0, 0.0),
        ) as tiantian_mock:
            price, yclose, amt, chg = get_fund_price("f_968048")

        self.assertAlmostEqual(price, 17.96, places=2)
        self.assertAlmostEqual(yclose, 17.85, places=2)
        self.assertAlmostEqual(amt, 0.11, places=2)
        self.assertAlmostEqual(chg, 0.62, places=2)
        f10_mock.assert_called_once()
        overseas_mock.assert_called_once()
        tiantian_mock.assert_not_called()

    def test_f10_parser_reads_latest_confirmed_nav(self):
        from core.fund import get_fund_eastmoney_f10

        payload = {
            "Data": {
                "LSJZList": [
                    {"FSRQ": "2026-03-04", "DWJZ": "1.5904", "JZZZL": "4.46"},
                    {"FSRQ": "2026-03-03", "DWJZ": "1.5225", "JZZZL": "-5.43"},
                ]
            }
        }
        with patch("core.fund.monitored_http_get", return_value=_JsonResp(payload)):
            price, yclose, amt, chg = get_fund_eastmoney_f10("025209")

        self.assertAlmostEqual(price, 1.5904, places=4)
        self.assertAlmostEqual(yclose, 1.5225, places=4)
        self.assertAlmostEqual(amt, 0.0679, places=4)
        self.assertAlmostEqual(chg, 4.46, places=2)

    def test_overseas_history_parser_reads_recent_nav_rows(self):
        html = """
        <table id="tb_Data">
            <tbody>
                <tr>
                    <th>净值日期</th><th>单位净值</th><th>日增长值</th><th>日增长率</th>
                </tr>
                <tr>
                    <td class="">2026-03-05</td>
                    <td class="numberClass">17.9600</td>
                    <td class="numberClass ui-color-red">0.1100</td>
                    <td class="numberClass ui-color-red">0.62%</td>
                </tr>
                <tr>
                    <td class="">2026-03-04</td>
                    <td class="numberClass">17.8500</td>
                    <td class="numberClass ui-color-green">-0.4300</td>
                    <td class="numberClass ui-color-green">-2.35%</td>
                </tr>
                <tr>
                    <td class="">2026-03-03</td>
                    <td class="numberClass">18.2800</td>
                    <td class="numberClass ui-color-green">-0.5300</td>
                    <td class="numberClass ui-color-green">-2.82%</td>
                </tr>
            </tbody>
        </table>
        """
        with patch("core.fund.monitored_http_get", return_value=_TextResp(html)):
            points = get_fund_overseas_history_points("968048", limit=2)

        self.assertEqual(
            points,
            [
                {"date": "2026-03-04", "value": 17.85},
                {"date": "2026-03-05", "value": 17.96},
            ],
        )

    def test_overseas_history_falls_back_to_fidelity_for_isin(self):
        fidelity_payload = {
            "items": [
                {"date": "2026-03-25", "nav": "9.22"},
                {"date": "2026-03-24", "nav": "9.16"},
                {"date": "2026-03-23", "nav": "9.23"},
            ]
        }
        with patch(
            "core.fund.monitored_http_get",
            side_effect=[_TextResp("<html><body>empty</body></html>"), _JsonResp(fidelity_payload)],
        ):
            points = get_fund_overseas_history_points("LU1116320737", limit=3)

        self.assertEqual(
            points,
            [
                {"date": "2026-03-23", "value": 9.23},
                {"date": "2026-03-24", "value": 9.16},
                {"date": "2026-03-25", "value": 9.22},
            ],
        )

    def test_tencent_jj_parser_reads_latest_confirmed_nav(self):
        from core.fund import get_fund_tencent_jj

        text = 'v_jj025209="025209~永赢先锋半导体智选混合发起C~0.0000~0.0000~~1.5904~1.5904~4.4598~2026-03-04~";'
        with patch("core.fund.monitored_http_get", return_value=_TextResp(text)):
            price, yclose, amt, chg = get_fund_tencent_jj("025209")

        self.assertAlmostEqual(price, 1.5904, places=4)
        self.assertAlmostEqual(yclose, 1.5225, places=4)
        self.assertAlmostEqual(amt, 0.0679, places=4)
        self.assertAlmostEqual(chg, 4.4598, places=3)

    def test_tencent_jj_parser_does_not_treat_accumulated_nav_as_yclose(self):
        from core.fund import get_fund_tencent_jj

        text = 'v_jj110017="110017~易方达增强回报债券A~0.0000~0.0000~~1.3970~2.6780~0.0000~2026-03-05~";'
        with patch("core.fund.monitored_http_get", return_value=_TextResp(text)):
            price, yclose, amt, chg = get_fund_tencent_jj("110017")

        self.assertAlmostEqual(price, 1.3970, places=4)
        self.assertAlmostEqual(yclose, 1.3970, places=4)
        self.assertAlmostEqual(amt, 0.0, places=6)
        self.assertAlmostEqual(chg, 0.0, places=6)


if __name__ == "__main__":
    unittest.main()
