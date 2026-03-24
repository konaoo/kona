import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from flask import Flask, g

ROOT = Path(__file__).resolve().parents[2]
KONA_TOOL = ROOT / "kona_tool"
if str(KONA_TOOL) not in sys.path:
    sys.path.insert(0, str(KONA_TOOL))

from ai_handlers import create_ai_chat_handler  # noqa: E402
from request_runtime import create_request_runtime  # noqa: E402


class _FakeDb:
    def __init__(self, *, initial_balance: int = 1, allow_consume: bool = True):
        self.balance = initial_balance
        self.allow_consume = allow_consume
        self.ledger = []

    def get_runtime_config(self, key):
        if key == "ai_providers":
            return (
                '[{"type":"zhipu","api_key":"test-key","model":"glm-test",'
                '"base_url":"https://example.com/v1","protocol":"openai","active":true}]'
            )
        if key == "user_group_ops":
            return (
                '{"text":"加入咔咔用户群获取积分","image_url":"https://example.com/group.png"}'
            )
        return None

    def get_cash_assets(self, user_id):
        return [{"name": "中国银行", "amount": 10000, "curr": "CNY"}]

    def get_other_assets(self, user_id):
        return []

    def get_liabilities(self, user_id):
        return []

    def get_history(self, days, user_id):
        return [{"date": "2026-03-19", "total_asset": 123456, "day_pnl": 456}]

    def get_rank_data(self, rank_type, market, user_id):
        return [{"name": "苹果", "code": "AAPL", "adjustment": 12.3}]

    def get_user_ai_credits_balance(self, user_id):
        return self.balance

    def adjust_user_ai_credits(
        self,
        *,
        user_id,
        delta,
        reason,
        source,
        request_id="",
        operator_user_id="",
    ):
        if not self.allow_consume or self.balance + delta < 0:
            return {
                "ok": False,
                "code": "AI_CREDITS_REQUIRED",
                "user_id": user_id,
                "username": "kona",
                "balance_before": self.balance,
                "balance_after": self.balance,
            }
        self.balance += delta
        entry = {
            "user_id": user_id,
            "delta": delta,
            "reason": reason,
            "source": source,
            "request_id": request_id,
            "operator_user_id": operator_user_id,
            "balance_after": self.balance,
        }
        self.ledger.append(entry)
        return {
            "ok": True,
            "user_id": user_id,
            "username": "kona",
            "balance_before": self.balance - delta,
            "balance_after": self.balance,
            "delta": delta,
            "ledger_id": len(self.ledger),
        }


class _FakePortfolioReadService:
    def build_metrics_payload(self, user_id):
        return [
            {
                "code": "AAPL",
                "name": "苹果",
                "qty": 10,
                "price": 100,
                "current_price": 105,
                "pnl": 50,
                "pnl_rate": 5,
                "day_pnl": 8,
                "curr": "USD",
                "asset_type": "us",
            }
        ]


class _FakeLogger:
    def __init__(self):
        self.info_messages = []
        self.warning_messages = []
        self.error_messages = []
        self.debug_messages = []

    def info(self, message, *args):
        self.info_messages.append(message % args if args else message)

    def warning(self, message, *args):
        self.warning_messages.append(message % args if args else message)

    def error(self, message, *args):
        self.error_messages.append(message % args if args else message)

    def debug(self, message, *args):
        self.debug_messages.append(message % args if args else message)


class AiChatHandlerTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.logger = _FakeLogger()

    def _build_app(self, db: _FakeDb):
        runtime = create_request_runtime(
            db=db,
            logger=self.logger,
            client_ip_getter=lambda: "127.0.0.1",
            resolve_ip_region=lambda ip: "本地",
            verify_token=lambda token: (True, {"user_id": "u-ai"}),
            is_policy_enabled=lambda scope_key, default=True: True,
            get_policy_limit_per_min=lambda scope_key: 0,
            time_getter=lambda: 1_700_000_000.0,
            activity_touch_interval_seconds=30.0,
        )
        runtime.register_hooks(self.app)

        handler = create_ai_chat_handler(
            db=db,
            portfolio_read_service=_FakePortfolioReadService(),
            rates_getter=lambda: {"CNY": 1.0, "USD": 7.2},
            market_status_getter=lambda now_utc, force_refresh=False: {
                "markets": {"us": {"label": "美股", "is_open": True}},
            },
        )

        @self.app.route("/api/ai/chat", methods=["POST"])
        def _chat():
            g.user_id = "u-ai"
            return handler()

    def test_ai_chat_returns_402_when_user_has_no_credits(self):
        db = _FakeDb(initial_balance=0)
        self._build_app(db)

        client = self.app.test_client()
        resp = client.post(
            "/api/ai/chat",
            json={"messages": [{"role": "user", "content": "帮我看下"}]},
            headers={"X-Request-Id": "ai-credit-empty-001"},
        )

        self.assertEqual(resp.status_code, 402)
        payload = resp.get_json()
        self.assertEqual(payload.get("code"), "AI_CREDITS_REQUIRED")
        self.assertEqual(payload.get("ai_credits_balance"), 0)
        self.assertIn("加入咔咔用户群", payload.get("user_group_text") or "")
        self.assertEqual(db.ledger, [])

    def test_ai_chat_consumes_one_credit_after_first_token(self):
        db = _FakeDb(initial_balance=2)
        self._build_app(db)

        with (
            patch(
                "ai_handlers._stream_openai_compatible",
                return_value=iter(
                    [
                        'data: {"delta": "你好"}\n\n',
                        'data: {"delta": "，这里是分析结果"}\n\n',
                    ]
                ),
            ),
            patch("ai_handlers.logger", self.logger),
        ):
            client = self.app.test_client()
            resp = client.post(
                "/api/ai/chat",
                json={"messages": [{"role": "user", "content": "帮我看下"}]},
                headers={"X-Request-Id": "ai-credit-success-001"},
            )
            body = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get("X-Trace-Stage-Count"), "7")
        self.assertIn('data: {"delta": "你好"}', body)
        self.assertEqual(db.balance, 1)
        self.assertEqual(len(db.ledger), 1)
        self.assertEqual(db.ledger[0]["delta"], -1)
        self.assertEqual(db.ledger[0]["reason"], "AI 对话消费")
        self.assertTrue(
            any(
                "AI_CHAT_TRACE request_id=ai-credit-success-001 stage=provider.total" in message
                and "credit_consumed=yes" in message
                for message in self.logger.info_messages
            )
        )

    def test_ai_chat_returns_stream_error_when_credit_consume_fails_after_first_token(self):
        db = _FakeDb(initial_balance=1, allow_consume=False)
        self._build_app(db)

        with patch(
            "ai_handlers._stream_openai_compatible",
            return_value=iter(['data: {"delta": "你好"}\n\n']),
        ):
            client = self.app.test_client()
            resp = client.post(
                "/api/ai/chat",
                json={"messages": [{"role": "user", "content": "帮我看下"}]},
                headers={"X-Request-Id": "ai-credit-race-001"},
            )
            body = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertNotIn('data: {"delta": "你好"}', body)
        self.assertIn('"code": "AI_CREDITS_REQUIRED"', body)
        self.assertEqual(db.balance, 1)
        self.assertEqual(db.ledger, [])


if __name__ == "__main__":
    unittest.main()
