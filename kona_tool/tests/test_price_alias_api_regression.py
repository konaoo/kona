"""真实请求和临时数据库验证别名，不改写既有代码及交易关联。"""
import logging
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock

from flask import Flask, g, jsonify

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.db import DatabaseManager
from core.asset_type import infer_asset_type
from core.parser import parse_code
from portfolio_handlers import create_portfolio_payload_handlers
from portfolio_runtime import create_portfolio_runtime


def create_api(tmp_path):
    db = DatabaseManager(str(tmp_path / "aliases.db"))
    runtime = create_portfolio_runtime(
        parse_code=parse_code, infer_asset_type=infer_asset_type,
        batch_get_prices_getter=lambda codes: {},
    )
    app = Flask(__name__)
    app.testing = True

    @app.before_request
    def user():
        g.user_id = None

    handlers = create_portfolio_payload_handlers(
        db=db, logger=logging.getLogger(__name__), portfolio_read_service=Mock(),
        rates_getter=lambda: {}, convert_amount=lambda amount, *args: amount,
        snapshot_saver_async=Mock(), portfolio_identity_normalizer=runtime.normalize_portfolio_identity,
        idempotency_begin=lambda *args: (False, None, None),
        idempotent_response=lambda action, user, request, payload, status=200: (jsonify(payload), status),
        undo_decorator=lambda payload, *args: payload,
        undo_claim=Mock(), undo_release=Mock(), take_snapshot_func=Mock(),
    )
    for name in ("add", "buy", "sell", "buy_with_cash"):
        app.add_url_rule(f"/api/portfolio/{name}", name, handlers[f"portfolio_{name}"], methods=["POST"])
    return app.test_client(), db


def seed(db, code, ledger=0, user=None):
    assert db.add_asset({"code": code, "name": "测试资产", "qty": 10, "price": 2,
                         "curr": "CNY", "asset_type": "fund"}, user, ledger_id=ledger)


class PriceAliasApiRegressionTests(unittest.TestCase):
    def test_anonymous_add_without_ledger_remains_supported(self):
        for suffix in ("600014", "600013", "600004", "600001", "600000"):
            with self.subTest(suffix=suffix), TemporaryDirectory() as tmp_path:
                client, db = create_api(Path(tmp_path))
                response = client.post("/api/portfolio/add", json={"code": f"sh{suffix}", "qty": 10, "price": 2})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(db.get_asset(f"sh{suffix}")["qty"], 10)

    def test_add_reuses_stored_identity_and_old_code_buy_sell_still_work(self):
        for use_canonical in (True, False):
            for legacy, canonical in (
                ("f_600329", "sh600329"), ("f_601818", "sh601818"), ("f_510300", "sh510300"),
            ):
                with self.subTest(legacy=legacy, canonical=canonical, use_canonical=use_canonical), TemporaryDirectory() as tmp_path:
                    client, db = create_api(Path(tmp_path))
                    seed(db, legacy)
                    response = client.post("/api/portfolio/add", json={
                        "code": canonical if use_canonical else legacy, "qty": 12, "price": 2,
                    })
                    self.assertEqual(response.status_code, 200)
                    self.assertIsNone(db.get_asset(canonical))
                    self.assertEqual(db.get_asset(legacy)["qty"], 12)  # 新增原本就是覆盖，不擅自变成数量相加。
                    for action, qty in (("buy", 2), ("sell", 1)):
                        result = client.post(f"/api/portfolio/{action}", json={"code": legacy, "qty": qty, "price": 2})
                        self.assertEqual(result.status_code, 200)
                    self.assertEqual(db.get_asset(legacy)["qty"], 13)
                    self.assertEqual({tx["code"] for tx in db.get_transactions()}, {legacy})

    def test_alias_match_does_not_cross_ledger_or_user(self):
        with TemporaryDirectory() as tmp_path:
            client, db = create_api(Path(tmp_path))
            seed(db, "f_600329", ledger=1)
            seed(db, "f_600329", ledger=2, user="other")
            response = client.post("/api/portfolio/add", json={
                "code": "sh600329", "qty": 3, "price": 2, "ledger_id": 2,
            })
            self.assertEqual(response.status_code, 200)
            self.assertEqual(db.get_asset("f_600329", ledger_id=1)["qty"], 10)
            self.assertEqual(db.get_asset("sh600329", ledger_id=2)["qty"], 3)
            self.assertEqual(db.get_asset("f_600329", "other", ledger_id=2)["qty"], 10)

    def test_two_existing_aliases_are_rejected_without_modification(self):
        with TemporaryDirectory() as tmp_path:
            client, db = create_api(Path(tmp_path))
            seed(db, "f_600329")
            seed(db, "sh600329")
            response = client.post("/api/portfolio/add", json={"code": "sh600329", "qty": 3, "price": 2})
            self.assertEqual(response.status_code, 409)
            self.assertEqual(response.get_json()["code"], "AMBIGUOUS_ASSET_ALIAS")
            self.assertEqual(db.get_asset("f_600329")["qty"], 10)
            self.assertEqual(db.get_asset("sh600329")["qty"], 10)

    def test_cash_buy_reuses_old_identity(self):
        for incoming in ("f_600329", "sh600329"):
            with self.subTest(incoming=incoming), TemporaryDirectory() as tmp_path:
                client, db = create_api(Path(tmp_path))
                seed(db, "f_600329")
                self.assertTrue(db.add_cash_asset("测试现金", 100, "CNY"))
                cash_id = db.get_cash_assets()[0]["id"]
                response = client.post("/api/portfolio/buy_with_cash", json={
                    "code": incoming, "name": "达仁堂", "qty": 2, "price": 2, "cash_asset_id": cash_id,
                })
                self.assertEqual(response.status_code, 200)
                self.assertIsNone(db.get_asset("sh600329"))
                self.assertEqual(db.get_asset("f_600329")["qty"], 12)
                self.assertEqual(db.get_cash_asset_by_id(cash_id)["amount"], 96)
                self.assertEqual({tx["code"] for tx in db.get_transactions()}, {"f_600329"})


if __name__ == "__main__":
    unittest.main()
