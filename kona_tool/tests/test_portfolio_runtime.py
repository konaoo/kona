import sys
from pathlib import Path
import unittest

from flask import Flask

ROOT = Path(__file__).resolve().parents[2]
KONA_TOOL = ROOT / "kona_tool"
if str(KONA_TOOL) not in sys.path:
    sys.path.insert(0, str(KONA_TOOL))

from portfolio_runtime import create_portfolio_runtime  # noqa: E402


def _fake_parse_code(code: str, curr: str) -> dict:
    raw = str(code or "").strip()
    lower = raw.lower()
    if lower.startswith(("sh", "sz", "bj", "gb_", "ft_", "f_")):
        normalized = lower
    elif raw and not raw.isdigit():
        normalized = f"gb_{lower}"
    elif raw.isdigit():
        normalized = f"f_{raw}"
    else:
        normalized = lower
    return {"code": normalized, "curr": curr}


def _fake_infer_asset_type(code: str, name: str) -> str:
    lower = str(code or "").lower()
    if lower.startswith("f_"):
        return "fund"
    if lower.startswith(("gb_", "ft_", "sh", "sz", "bj")):
        return "a"
    return "fund"


class PortfolioRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.now = 1_700_000_000.0
        self.runtime = create_portfolio_runtime(
            parse_code=_fake_parse_code,
            infer_asset_type=_fake_infer_asset_type,
            batch_get_prices_getter=lambda codes: {"sz159687": (1.7, 1.6, 0.1, 6.2)},
            time_getter=lambda: self.now,
            token_factory=lambda length: "undo-fixed-token",
        )

    def test_normalize_portfolio_identity_converts_us_symbol_to_gb(self):
        normalized = self.runtime.normalize_portfolio_identity("BRK.B", "CNY", "伯克希尔")
        self.assertEqual(normalized["code"], "gb_brk.b")
        self.assertEqual(normalized["curr"], "USD")

    def test_normalize_portfolio_identity_converts_exchange_fund_code(self):
        normalized = self.runtime.normalize_portfolio_identity("f_159687", "CNY", "测试 ETF")
        self.assertEqual(normalized["code"], "sz159687")
        self.assertEqual(normalized["curr"], "CNY")

    def test_idempotency_begin_returns_inflight_then_done_payload(self):
        hit, payload, status = self.runtime.idempotency_begin("portfolio_buy", "u_1", "req-1")
        self.assertFalse(hit)
        self.assertIsNone(payload)
        self.assertIsNone(status)

        hit, payload, status = self.runtime.idempotency_begin("portfolio_buy", "u_1", "req-1")
        self.assertTrue(hit)
        self.assertEqual(status, 200)
        self.assertEqual(payload.get("code"), "REQUEST_DEDUP_IN_FLIGHT")

        with self.app.app_context():
            response, status_code = self.runtime.idempotent_response(
                "portfolio_buy",
                "u_1",
                "req-1",
                {"status": "ok", "code": "BUY_DONE"},
                200,
            )
        self.assertEqual(status_code, 200)
        self.assertEqual(response.get_json().get("code"), "BUY_DONE")

        hit, payload, status = self.runtime.idempotency_begin("portfolio_buy", "u_1", "req-1")
        self.assertTrue(hit)
        self.assertEqual(status, 200)
        self.assertEqual(payload.get("code"), "BUY_DONE")

    def test_undo_record_claim_and_release(self):
        payload = self.runtime.decorate_with_undo({"status": "ok"}, "u_2", {"op_type": "buy"})
        self.assertEqual(payload.get("undo_token"), "undo-fixed-token")

        operation, error = self.runtime.claim_undo_record("u_2", "undo-fixed-token")
        self.assertIsNone(error)
        self.assertEqual(operation.get("op_type"), "buy")

        operation, error = self.runtime.claim_undo_record("u_2", "undo-fixed-token")
        self.assertIsNone(operation)
        self.assertEqual(error[0], "UNDO_ALREADY_USED")

        self.runtime.release_undo_claim("u_2", "undo-fixed-token")
        operation, error = self.runtime.claim_undo_record("u_2", "undo-fixed-token")
        self.assertIsNone(error)
        self.assertEqual(operation.get("op_type"), "buy")

    def test_convert_amount_uses_currency_rates(self):
        converted = self.runtime.convert_amount(
            100.0,
            "USD",
            "HKD",
            {"USD": 7.2, "HKD": 0.92},
        )
        self.assertAlmostEqual(converted, 782.6087, places=3)


if __name__ == "__main__":
    unittest.main()
