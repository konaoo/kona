import os
import sys
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
KONA_TOOL = ROOT / "kona_tool"
if str(KONA_TOOL) not in sys.path:
    sys.path.insert(0, str(KONA_TOOL))

os.environ.setdefault("JWT_SECRET", "ci_test_jwt_secret")

import core.market_calendar as market_calendar  # noqa: E402


class MarketCalendarTests(unittest.TestCase):
    def test_market_from_asset_prefers_asset_type(self):
        asset = {"code": "sh600000", "asset_type": "us"}
        self.assertEqual(market_calendar.market_from_asset(asset), "us")

    def test_market_from_asset_code_fallback(self):
        self.assertEqual(
            market_calendar.market_from_asset({"code": "hk00700", "asset_type": ""}),
            "hk",
        )
        self.assertEqual(
            market_calendar.market_from_asset({"code": "gb_aapl", "asset_type": ""}),
            "us",
        )
        self.assertEqual(
            market_calendar.market_from_asset({"code": "f_000001", "asset_type": ""}),
            "fund",
        )

    def test_force_closed_override_has_priority(self):
        with tempfile.TemporaryDirectory() as tmp:
            override_path = Path(tmp) / "market_holidays.json"
            override_path.write_text(
                json.dumps(
                    {
                        "force_closed": {
                            "a": ["2026-01-05"],
                        }
                    }
                ),
                encoding="utf-8",
            )

            with patch.object(
                market_calendar.config,
                "MARKET_HOLIDAY_OVERRIDES_PATH",
                override_path,
            ):
                with patch.object(
                    market_calendar,
                    "_is_trading_day_from_calendar",
                    return_value=True,
                ):
                    self.assertFalse(
                        market_calendar.is_trading_day("a", "2026-01-05")
                    )

    def test_force_open_override_has_priority(self):
        with tempfile.TemporaryDirectory() as tmp:
            override_path = Path(tmp) / "market_holidays.json"
            override_path.write_text(
                json.dumps(
                    {
                        "force_open": {
                            "us": ["2026-01-04"],
                        }
                    }
                ),
                encoding="utf-8",
            )

            with patch.object(
                market_calendar.config,
                "MARKET_HOLIDAY_OVERRIDES_PATH",
                override_path,
            ):
                with patch.object(
                    market_calendar,
                    "_is_trading_day_from_calendar",
                    return_value=False,
                ):
                    self.assertTrue(
                        market_calendar.is_trading_day("us", "2026-01-04")
                    )

    def test_all_markets_closed_uses_each_market(self):
        with patch.object(
            market_calendar,
            "is_trading_day",
            side_effect=lambda market, _d: market == "us",
        ):
            self.assertFalse(
                market_calendar.is_markets_closed_on_date(
                    ["a", "hk", "us"], "2026-01-06"
                )
            )
        with patch.object(market_calendar, "is_trading_day", return_value=False):
            self.assertTrue(
                market_calendar.is_markets_closed_on_date(
                    ["a", "hk", "us"], "2026-01-06"
                )
            )

    def test_is_market_open_now_delegates_status(self):
        with patch.object(
            market_calendar,
            "get_market_status",
            return_value={"open": True, "reason": "open_session"},
        ):
            self.assertTrue(market_calendar.is_market_open_now("a"))
        with patch.object(
            market_calendar,
            "get_market_status",
            return_value={"open": False, "reason": "off_hours"},
        ):
            self.assertFalse(market_calendar.is_market_open_now("a"))

    def test_all_markets_closed_supports_date_like_argument(self):
        with patch.object(
            market_calendar,
            "is_markets_closed_on_date",
            return_value=True,
        ) as mocked:
            self.assertTrue(
                market_calendar.all_markets_closed(
                    ["a", "hk", "us", "fund"], "2026-01-01"
                )
            )
            mocked.assert_called_once()

    def test_hk_half_day_afternoon_closed_by_calendar(self):
        # 2026-02-16 港股半日市，14:00 HKT(06:00 UTC) 应为休市。
        probe_utc = datetime(2026, 2, 16, 6, 0, 0, tzinfo=timezone.utc)
        status = market_calendar.get_market_status("hk", now=probe_utc)
        self.assertFalse(status["open"])

    def test_trading_day_matrix_for_2026_02_16(self):
        # 该日期在交易日历中：A/Fund 休市，HK 交易日，US 休市（总统日）。
        self.assertFalse(market_calendar.is_trading_day("a", "2026-02-16"))
        self.assertTrue(market_calendar.is_trading_day("hk", "2026-02-16"))
        self.assertFalse(market_calendar.is_trading_day("us", "2026-02-16"))
        self.assertFalse(market_calendar.is_trading_day("fund", "2026-02-16"))


if __name__ == "__main__":
    unittest.main()
