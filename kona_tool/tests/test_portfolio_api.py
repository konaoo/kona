import os
import sys
import tempfile
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from datetime import datetime, timedelta

# Ensure kona_tool is on sys.path so app.py can import config/core
ROOT = Path(__file__).resolve().parents[2]
KONA_TOOL = ROOT / "kona_tool"
if str(KONA_TOOL) not in sys.path:
    sys.path.insert(0, str(KONA_TOOL))

# Use a temporary database to avoid local schema conflicts
_tmp_dir = tempfile.TemporaryDirectory()
os.environ["KONA_DATABASE_PATH"] = str(Path(_tmp_dir.name) / "test.db")
os.environ.setdefault("JWT_SECRET", "ci_test_jwt_secret")

import app as app_module  # noqa: E402
import portfolio_handlers  # noqa: E402


def _auth_headers(user_id: str, username: str) -> dict:
    token = app_module.generate_token(user_id, username)
    return {"Authorization": f"Bearer {token}"}


def _seed_user(
    user_id: str,
    username: str,
    password_hash: str = "scrypt$16384$8$1$U0FMVA==$SEFTSA==",
) -> None:
    conn = app_module.db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR REPLACE INTO users (id, username, password_hash, legacy_needs_password_setup, is_admin, status)
        VALUES (?, ?, ?, 0, 0, 'active')
        """,
        (user_id, username, password_hash),
    )
    conn.commit()
    conn.close()


class PortfolioApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app_module.app.testing = True
        cls.client = app_module.app.test_client()

    def setUp(self):
        with app_module.market_runtime._market_status_lock:
            app_module.market_runtime._market_status_cache.clear()
        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM portfolio_correction_logs")
        cursor.execute("DELETE FROM portfolio_adjustment_ledger")
        cursor.execute("DELETE FROM cash_assets")
        cursor.execute("DELETE FROM other_assets")
        cursor.execute("DELETE FROM liabilities")
        cursor.execute("DELETE FROM transactions")
        cursor.execute("DELETE FROM portfolio")
        cursor.execute("DELETE FROM portfolio_legacy_adjustment_states")
        cursor.execute("DELETE FROM ledger_daily_snapshots")
        cursor.execute("DELETE FROM investment_ledgers")
        cursor.execute("DELETE FROM daily_snapshots")
        cursor.execute("DELETE FROM runtime_configs")
        conn.commit()
        conn.close()

    def test_buy_idempotent_request_id_prevents_duplicate_qty(self):
        add_resp = self.client.post('/api/portfolio/add', json={
            'code': 'sh600000',
            'name': '浦发银行',
            'price': 10.0,
            'qty': 10.0,
        })
        self.assertEqual(add_resp.status_code, 200)

        request_id = 'req-buy-dedup-1'
        buy_first = self.client.post('/api/portfolio/buy', json={
            'code': 'sh600000',
            'price': 12.0,
            'qty': 5.0,
            'request_id': request_id,
        })
        self.assertEqual(buy_first.status_code, 200)
        self.assertEqual(buy_first.get_json().get('status'), 'ok')
        self.assertGreater(int(buy_first.headers.get('X-Trace-Stage-Count') or 0), 0)

        buy_second = self.client.post('/api/portfolio/buy', json={
            'code': 'sh600000',
            'price': 12.0,
            'qty': 5.0,
            'request_id': request_id,
        })
        self.assertEqual(buy_second.status_code, 200)

        list_resp = self.client.get('/api/portfolio')
        self.assertEqual(list_resp.status_code, 200)
        items = list_resp.get_json() or []
        target = next((item for item in items if item.get('code') == 'sh600000'), None)
        self.assertIsNotNone(target)
        self.assertAlmostEqual(float(target['qty']), 15.0)

    def test_portfolio_ocr_parse_asset_normalizes_candidates(self):
        with patch.object(
            portfolio_handlers.portfolio_ocr,
            'parse_portfolio_asset_candidates',
            return_value=portfolio_handlers.portfolio_ocr.PortfolioOcrParseResult(
                items=[
                    {
                        'name': '腾讯控股',
                        'code': '00700.HK',
                        'qty': 200.0,
                        'price': 318.4,
                        'curr': 'HKD',
                        'asset_type': 'hk',
                        'confidence': 0.94,
                        'note': '截图里价格列靠得比较近',
                    }
                ],
                warnings=['成本价建议再确认一眼'],
                raw_text='{"items":[...]}',
            ),
        ):
            resp = self.client.post(
                '/api/portfolio/ocr_parse_asset',
                data={
                    'file': (io.BytesIO(b'fake-image-bytes'), 'holding.png'),
                },
                content_type='multipart/form-data',
            )

        self.assertEqual(resp.status_code, 200)
        body = resp.get_json() or {}
        self.assertEqual(body.get('warnings'), ['成本价建议再确认一眼'])
        items = body.get('items') or []
        self.assertEqual(len(items), 1)
        first = items[0]
        self.assertEqual(first.get('name'), '腾讯控股')
        self.assertEqual(first.get('code'), 'hk00700')
        self.assertAlmostEqual(float(first.get('qty') or 0), 200.0)
        self.assertAlmostEqual(float(first.get('price') or 0), 318.4)

    def test_portfolio_ocr_parse_asset_returns_provider_error(self):
        with patch.object(
            portfolio_handlers.portfolio_ocr,
            'parse_portfolio_asset_candidates',
            side_effect=portfolio_handlers.portfolio_ocr.PortfolioOcrError(
                'AI 服务未配置，暂时无法识别截图',
                code='OCR_PROVIDER_NOT_CONFIGURED',
                status_code=503,
            ),
        ):
            resp = self.client.post(
                '/api/portfolio/ocr_parse_asset',
                data={
                    'file': (io.BytesIO(b'fake-image-bytes'), 'holding.png'),
                },
                content_type='multipart/form-data',
            )

        self.assertEqual(resp.status_code, 503)
        body = resp.get_json() or {}
        self.assertEqual(body.get('code'), 'OCR_PROVIDER_NOT_CONFIGURED')

    def test_portfolio_ocr_parse_asset_keeps_missing_code_empty(self):
        with patch.object(
            portfolio_handlers.portfolio_ocr,
            'parse_portfolio_asset_candidates',
            return_value=portfolio_handlers.portfolio_ocr.PortfolioOcrParseResult(
                items=[
                    {
                        'name': '江苏银行',
                        'code': '',
                        'qty': 3200.0,
                        'price': 10.092,
                        'curr': 'CNY',
                        'asset_type': 'a',
                        'confidence': 0.78,
                        'note': '',
                    }
                ],
                warnings=[],
                raw_text='{"items":[...]}',
            ),
        ):
            resp = self.client.post(
                '/api/portfolio/ocr_parse_asset',
                data={
                    'file': (io.BytesIO(b'fake-image-bytes'), 'holding.png'),
                },
                content_type='multipart/form-data',
            )

        self.assertEqual(resp.status_code, 200)
        body = resp.get_json() or {}
        items = body.get('items') or []
        self.assertEqual(len(items), 1)
        first = items[0]
        self.assertEqual(first.get('name'), '江苏银行')
        self.assertEqual(first.get('code'), '')
        self.assertAlmostEqual(float(first.get('qty') or 0), 3200.0)
        self.assertAlmostEqual(float(first.get('price') or 0), 10.092)

    def test_portfolio_ocr_prefers_dedicated_ocr_provider_config(self):
        app_module.db.set_runtime_config(
            "ai_providers",
            json.dumps(
                [
                    {
                        "id": "chat01",
                        "type": "zhipu",
                        "name": "聊天模型",
                        "base_url": "https://chat.example.com/v1",
                        "api_key": "chat-key",
                        "model": "glm-chat",
                        "active": True,
                        "protocol": "openai",
                    },
                    {
                        "id": "ocr01",
                        "type": "zhipu",
                        "name": "截图模型",
                        "base_url": "https://vision.example.com/v1",
                        "api_key": "ocr-key",
                        "model": "glm-4.6v-base",
                        "active": False,
                        "protocol": "openai",
                    },
                ],
                ensure_ascii=False,
            ),
            updated_by="test",
        )
        app_module.db.set_runtime_config(
            "ai_ocr_provider_config",
            json.dumps(
                {
                    "provider_id": "ocr01",
                    "model": "glm-4.6v-flash",
                },
                ensure_ascii=False,
            ),
            updated_by="test",
        )

        with patch.object(
            portfolio_handlers.portfolio_ocr,
            "_run_openai_compatible_vision",
            return_value=(
                '{"items":[{"name":"腾讯控股","code":"hk00700","qty":200,'
                '"price":318.4,"curr":"HKD","asset_type":"hk","confidence":0.9,'
                '"note":""}],"warnings":[]}'
            ),
        ) as mocked:
            result = portfolio_handlers.portfolio_ocr.parse_portfolio_asset_candidates(
                db=app_module.db,
                image_bytes=b"fake-image-bytes",
                filename="holding.png",
                content_type="image/png",
            )

        self.assertEqual(len(result.items), 1)
        self.assertEqual(result.warnings, [])
        self.assertEqual(mocked.call_count, 1)
        kwargs = mocked.call_args.kwargs
        self.assertEqual(kwargs.get("api_key"), "ocr-key")
        self.assertEqual(kwargs.get("base_url"), "https://vision.example.com/v1")
        self.assertEqual(kwargs.get("provider_type"), "zhipu")
        self.assertEqual(kwargs.get("model"), "glm-4.6v-flash")

    def test_portfolio_ocr_prompt_forbids_guessing_missing_code(self):
        prompt = portfolio_handlers.portfolio_ocr._build_ocr_prompt()

        self.assertIn("只有截图里明确出现了代码，才能写代码", prompt)
        self.assertIn("绝对不要根据名称、品牌名、常识、热门股票记忆、价格或市场去猜代码", prompt)
        self.assertIn("每条资产尽量输出成一行，优先格式：名称 | 代码 | 数量 | 成本价", prompt)

    def test_portfolio_ocr_single_pass_transcript_parses_pipe_rows(self):
        app_module.db.set_runtime_config(
            "ai_providers",
            json.dumps(
                [
                    {
                        "id": "ocr01",
                        "type": "zhipu",
                        "name": "截图模型",
                        "base_url": "https://vision.example.com/v1",
                        "api_key": "ocr-key",
                        "model": "glm-4.6v-flash",
                        "active": True,
                        "protocol": "openai",
                    },
                ],
                ensure_ascii=False,
            ),
            updated_by="test",
        )

        with patch.object(
            portfolio_handlers.portfolio_ocr,
            "_run_openai_compatible_vision",
            return_value="江苏银行 |  | 3200 | 10.092",
        ) as mocked:
            result = portfolio_handlers.portfolio_ocr.parse_portfolio_asset_candidates(
                db=app_module.db,
                image_bytes=b"fake-image-bytes",
                filename="holding.png",
                content_type="image/png",
            )

        self.assertEqual(len(result.items), 1)
        self.assertEqual(result.items[0].get("name"), "江苏银行")
        self.assertEqual(result.items[0].get("code"), "")
        self.assertEqual(mocked.call_count, 1)
        prompt = mocked.call_args.kwargs.get("prompt") or ""
        self.assertIn("只返回逐行纯文本", prompt)
        self.assertIn("优先格式：名称 | 代码 | 数量 | 成本价", prompt)

    def test_portfolio_ocr_single_pass_still_accepts_json_when_provider_returns_json(self):
        app_module.db.set_runtime_config(
            "ai_providers",
            json.dumps(
                [
                    {
                        "id": "ocr01",
                        "type": "zhipu",
                        "name": "截图模型",
                        "base_url": "https://vision.example.com/v1",
                        "api_key": "ocr-key",
                        "model": "glm-4.6v-flash",
                        "active": True,
                        "protocol": "openai",
                    },
                ],
                ensure_ascii=False,
            ),
            updated_by="test",
        )

        with patch.object(
            portfolio_handlers.portfolio_ocr,
            "_run_openai_compatible_vision",
            return_value=(
                '{"items":[{"name":"腾讯控股","code":"00700","qty":100,'
                '"price":598.0,"curr":"HKD","asset_type":"hk",'
                '"confidence":0.82,"note":"直接返回 JSON"}],"warnings":["来自模型 JSON"]}'
            ),
        ) as mocked_vision:
            result = portfolio_handlers.portfolio_ocr.parse_portfolio_asset_candidates(
                db=app_module.db,
                image_bytes=b"fake-image-bytes",
                filename="holding.png",
                content_type="image/png",
            )

        self.assertEqual(len(result.items), 1)
        self.assertEqual(result.items[0].get("name"), "腾讯控股")
        self.assertEqual(result.items[0].get("code"), "00700")
        self.assertEqual(result.warnings, ["来自模型 JSON"])
        self.assertEqual(mocked_vision.call_count, 1)

    def test_portfolio_ocr_normalize_items_keeps_up_to_twelve_rows(self):
        raw_items = []
        for idx in range(15):
            raw_items.append(
                {
                    "name": f"资产{idx}",
                    "code": "",
                    "qty": idx + 1,
                    "price": idx + 0.5,
                }
            )

        items = portfolio_handlers.portfolio_ocr._normalize_items(raw_items)

        self.assertEqual(len(items), 12)
        self.assertEqual(items[0].get("name"), "资产0")
        self.assertEqual(items[-1].get("name"), "资产11")

    def test_portfolio_ocr_parse_transcript_items_supports_pipe_format(self):
        transcript = "\n".join(
            [
                "腾讯控股 | 00700 | 100 | 598.00",
                "中国海洋 |  | 1000 | HK$21.354",
            ]
        )

        items = portfolio_handlers.portfolio_ocr._parse_transcript_items(transcript)

        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].get("name"), "腾讯控股")
        self.assertEqual(items[0].get("code"), "00700")
        self.assertEqual(items[0].get("qty"), 100.0)
        self.assertEqual(items[0].get("price"), 598.0)
        self.assertEqual(items[1].get("curr"), "HKD")

    def test_portfolio_ocr_parse_transcript_items_supports_two_line_rows(self):
        transcript = "\n".join(
            [
                "腾讯控股 50,800.00 508.000 -9,000.00",
                "00700 100 598.00 -15.05%",
                "恒生高息股 8,512.00 21.280 +284.00",
                "03466 400 20.57 +3.45%",
            ]
        )

        items = portfolio_handlers.portfolio_ocr._parse_transcript_items(transcript)

        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].get("name"), "腾讯控股")
        self.assertEqual(items[0].get("code"), "00700")
        self.assertEqual(items[0].get("qty"), 100.0)
        self.assertEqual(items[0].get("price"), 598.0)

    def test_portfolio_ocr_leading_text_strips_trailing_sign(self):
        name = portfolio_handlers.portfolio_ocr._leading_text_before_number("小米集团 -1,972.85 200 HK$44.395")
        self.assertEqual(name, "小米集团")

    def test_portfolio_modify_allows_negative_cost_price(self):
        add_resp = self.client.post('/api/portfolio/add', json={
            'code': 'sh600002',
            'name': '测试负成本',
            'price': 10.0,
            'qty': 5.0,
        })
        self.assertEqual(add_resp.status_code, 200)

        modify_resp = self.client.post('/api/portfolio/modify', json={
            'code': 'sh600002',
            'qty': 5.0,
            'price': -1.23,
            'adjustment': 3.0,
        })
        self.assertEqual(modify_resp.status_code, 200)
        self.assertEqual((modify_resp.get_json() or {}).get('status'), 'ok')
        self.assertGreater(int(modify_resp.headers.get('X-Trace-Stage-Count') or 0), 0)

        list_resp = self.client.get('/api/portfolio')
        self.assertEqual(list_resp.status_code, 200)
        items = list_resp.get_json() or []
        target = next((item for item in items if item.get('code') == 'sh600002'), None)
        self.assertIsNotNone(target)
        self.assertAlmostEqual(float(target.get('price') or 0.0), -1.23, places=6)

    def test_portfolio_modify_without_adjustment_preserves_realized_pnl_total(self):
        add_resp = self.client.post('/api/portfolio/add', json={
            'code': 'sh600011',
            'name': '测试修改持仓',
            'price': 10.0,
            'qty': 10.0,
        })
        self.assertEqual(add_resp.status_code, 200)

        sell_resp = self.client.post('/api/portfolio/sell', json={
            'code': 'sh600011',
            'price': 12.0,
            'qty': 2.0,
            'request_id': 'req-modify-preserve-ledger',
        })
        self.assertEqual(sell_resp.status_code, 200)

        modify_resp = self.client.post('/api/portfolio/modify', json={
            'code': 'sh600011',
            'qty': 8.0,
            'price': 11.0,
        })
        self.assertEqual(modify_resp.status_code, 200)
        self.assertEqual((modify_resp.get_json() or {}).get('status'), 'ok')

        list_resp = self.client.get('/api/portfolio')
        self.assertEqual(list_resp.status_code, 200)
        items = list_resp.get_json() or []
        target = next((item for item in items if item.get('code') == 'sh600011'), None)
        self.assertIsNotNone(target)
        self.assertAlmostEqual(float(target.get('price') or 0.0), 11.0, places=6)
        self.assertAlmostEqual(float(target.get('adjustment') or 0.0), 4.0, places=6)
        self.assertAlmostEqual(float(target.get('legacy_adjustment') or 0.0), 0.0, places=6)
        self.assertAlmostEqual(float(target.get('ledger_adjustment') or 0.0), 0.0, places=6)
        self.assertAlmostEqual(float(target.get('realized_pnl_adjustment') or 0.0), 4.0, places=6)

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT adjustment FROM portfolio WHERE code = ? AND (user_id IS NULL OR user_id = '')",
            ('sh600011',),
        )
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertAlmostEqual(float(row['adjustment'] or 0.0), 0.0, places=6)
        cursor.execute(
            "SELECT event_type, amount FROM portfolio_adjustment_ledger WHERE code = ?",
            ('sh600011',),
        )
        ledger_rows = cursor.fetchall()
        conn.close()
        self.assertEqual(len(ledger_rows), 0)

    def test_portfolio_add_ignores_legacy_adjustment_payload(self):
        add_resp = self.client.post('/api/portfolio/add', json={
            'code': 'sh600012',
            'name': '测试新增旧调整额',
            'price': 10.0,
            'qty': 10.0,
            'adjustment': 123.45,
        })
        self.assertEqual(add_resp.status_code, 200)
        self.assertEqual((add_resp.get_json() or {}).get('status'), 'ok')

        list_resp = self.client.get('/api/portfolio')
        self.assertEqual(list_resp.status_code, 200)
        items = list_resp.get_json() or []
        target = next((item for item in items if item.get('code') == 'sh600012'), None)
        self.assertIsNotNone(target)
        self.assertAlmostEqual(float(target.get('legacy_adjustment') or 0.0), 0.0, places=6)
        self.assertAlmostEqual(float(target.get('adjustment') or 0.0), 0.0, places=6)

    def test_portfolio_update_rejects_legacy_adjustment_field(self):
        add_resp = self.client.post('/api/portfolio/add', json={
            'code': 'sh600013',
            'name': '测试更新旧调整额',
            'price': 8.0,
            'qty': 2.0,
        })
        self.assertEqual(add_resp.status_code, 200)

        update_resp = self.client.post('/api/portfolio/update', json={
            'code': 'sh600013',
            'field': 'adjustment',
            'val': 9.9,
        })
        self.assertEqual(update_resp.status_code, 400)
        body = update_resp.get_json() or {}
        self.assertEqual(body.get('code'), 'UNSUPPORTED_FIELD')

        list_resp = self.client.get('/api/portfolio')
        self.assertEqual(list_resp.status_code, 200)
        items = list_resp.get_json() or []
        target = next((item for item in items if item.get('code') == 'sh600013'), None)
        self.assertIsNotNone(target)
        self.assertAlmostEqual(float(target.get('legacy_adjustment') or 0.0), 0.0, places=6)

    def test_portfolio_transactions_include_sell_and_dividend_only_once(self):
        add_resp = self.client.post('/api/portfolio/add', json={
            'code': 'sh600021',
            'name': '测试交易记录',
            'price': 10.0,
            'qty': 10.0,
        })
        self.assertEqual(add_resp.status_code, 200)

        sell_resp = self.client.post('/api/portfolio/sell', json={
            'code': 'sh600021',
            'price': 12.0,
            'qty': 2.0,
            'request_id': 'req-portfolio-transactions-sell',
        })
        self.assertEqual(sell_resp.status_code, 200)

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO portfolio_adjustment_ledger
            (user_id, code, event_type, amount, curr, note, source, created_at, updated_at)
            VALUES ('', ?, 'dividend', 8.5, 'CNY', '测试分红', 'test', '2026-03-20 08:00:00', '2026-03-20 08:00:00')
            """,
            ('sh600021',),
        )
        conn.commit()
        conn.close()

        resp = self.client.get('/api/portfolio/transactions?code=sh600021')
        self.assertEqual(resp.status_code, 200)
        records = (resp.get_json() or {}).get('records') or []
        self.assertEqual(len(records), 3)
        self.assertCountEqual(
            [item.get('type') for item in records],
            ['减仓', '初始持仓', '分红'],
        )
        sell_record = next(item for item in records if item.get('type') == '减仓')
        self.assertAlmostEqual(float(sell_record.get('pnl') or 0.0), 4.0, places=6)

    def test_buy_and_sell_transactions_store_curr_market_and_effective_date(self):
        add_resp = self.client.post('/api/portfolio/add', json={
            'code': '00700',
            'name': '腾讯控股',
            'price': 400.0,
            'qty': 2.0,
        })
        self.assertEqual(add_resp.status_code, 200)

        buy_resp = self.client.post('/api/portfolio/buy', json={
            'code': '00700.HK',
            'price': 420.0,
            'qty': 1.0,
        })
        self.assertEqual(buy_resp.status_code, 200)

        sell_resp = self.client.post('/api/portfolio/sell', json={
            'code': '00700.HK',
            'price': 430.0,
            'qty': 1.0,
        })
        self.assertEqual(sell_resp.status_code, 200)

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT type, code, curr, market, effective_date
            FROM transactions
            WHERE code = ?
            ORDER BY id ASC
            """,
            ('00700.HK',),
        )
        rows = cursor.fetchall()
        conn.close()

        self.assertEqual(len(rows), 2)
        self.assertEqual(str(rows[0]['type']), '加仓')
        self.assertEqual(str(rows[0]['curr']), 'HKD')
        self.assertEqual(str(rows[0]['market']), 'hk')
        self.assertRegex(str(rows[0]['effective_date'] or ''), r'^\d{4}-\d{2}-\d{2}$')
        self.assertEqual(str(rows[1]['type']), '减仓')
        self.assertEqual(str(rows[1]['curr']), 'HKD')
        self.assertEqual(str(rows[1]['market']), 'hk')
        self.assertRegex(str(rows[1]['effective_date'] or ''), r'^\d{4}-\d{2}-\d{2}$')

    def test_portfolio_add_writes_opening_balance_log_and_detail_record(self):
        add_resp = self.client.post('/api/portfolio/add', json={
            'code': 'sh600031',
            'name': '三一重工',
            'price': 15.0,
            'qty': 20.0,
        })
        self.assertEqual(add_resp.status_code, 200)

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT correction_type, before_qty, after_qty, before_price, after_price, note
            FROM portfolio_correction_logs
            WHERE code = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            ('sh600031',),
        )
        row = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(str(row['correction_type']), 'opening_balance')
        self.assertAlmostEqual(float(row['before_qty'] or 0.0), 0.0, places=6)
        self.assertAlmostEqual(float(row['after_qty'] or 0.0), 20.0, places=6)
        self.assertIsNone(row['before_price'])
        self.assertAlmostEqual(float(row['after_price'] or 0.0), 15.0, places=6)
        self.assertEqual(str(row['note'] or ''), '初始持仓录入')

        resp = self.client.get('/api/portfolio/transactions?code=sh600031')
        self.assertEqual(resp.status_code, 200)
        records = (resp.get_json() or {}).get('records') or []
        self.assertEqual([item.get('type') for item in records], ['初始持仓'])
        self.assertAlmostEqual(float(records[0].get('after_qty') or 0.0), 20.0, places=6)
        self.assertAlmostEqual(float(records[0].get('after_price') or 0.0), 15.0, places=6)

    def test_position_qty_before_opening_balance_date_is_zero(self):
        ok = app_module.db.add_asset({
            'code': 'f_110018',
            'name': '开放式基金测试',
            'price': 1.5,
            'qty': 100.0,
            'curr': 'CNY',
            'asset_type': 'fund',
        })
        self.assertTrue(ok)

        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        self.assertAlmostEqual(
            float(app_module.db.get_position_qty_as_of_effective_date('f_110018', yesterday) or 0.0),
            0.0,
            places=6,
        )
        self.assertAlmostEqual(
            float(app_module.db.get_position_qty_as_of_effective_date('f_110018', today) or 0.0),
            100.0,
            places=6,
        )

    def test_portfolio_modify_with_note_writes_correction_log(self):
        add_resp = self.client.post('/api/portfolio/add', json={
            'code': 'sh600022',
            'name': '测试修正备注',
            'price': 10.0,
            'qty': 5.0,
        })
        self.assertEqual(add_resp.status_code, 200)

        modify_resp = self.client.post('/api/portfolio/modify', json={
            'code': 'sh600022',
            'qty': 6.0,
            'price': 9.5,
            'note': '更正初始录入数量和成本',
        })
        self.assertEqual(modify_resp.status_code, 200)
        self.assertEqual((modify_resp.get_json() or {}).get('status'), 'ok')

        list_resp = self.client.get('/api/portfolio')
        items = list_resp.get_json() or []
        target = next((item for item in items if item.get('code') == 'sh600022'), None)
        self.assertIsNotNone(target)
        self.assertAlmostEqual(float(target.get('qty') or 0.0), 6.0, places=6)
        self.assertAlmostEqual(float(target.get('price') or 0.0), 9.5, places=6)
        self.assertAlmostEqual(float(target.get('adjustment') or 0.0), 0.0, places=6)

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT correction_type, before_qty, after_qty, before_price, after_price, note
            FROM portfolio_correction_logs
            WHERE code = ?
            ORDER BY id DESC
            """,
            ('sh600022',),
        )
        rows = cursor.fetchall()
        conn.close()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['correction_type'], 'holding')
        self.assertAlmostEqual(float(rows[0]['before_qty'] or 0.0), 5.0, places=6)
        self.assertAlmostEqual(float(rows[0]['after_qty'] or 0.0), 6.0, places=6)
        self.assertAlmostEqual(float(rows[0]['before_price'] or 0.0), 10.0, places=6)
        self.assertAlmostEqual(float(rows[0]['after_price'] or 0.0), 9.5, places=6)
        self.assertEqual(rows[0]['note'], '更正初始录入数量和成本')
        self.assertEqual(rows[1]['correction_type'], 'opening_balance')

    def test_portfolio_list_can_ignore_legacy_adjustment_after_migration_switch(self):
        add_resp = self.client.post('/api/portfolio/add', json={
            'code': 'sh600023',
            'name': '测试新口径列表',
            'price': 10.0,
            'qty': 5.0,
            'adjustment': 6.0,
        })
        self.assertEqual(add_resp.status_code, 200)

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO portfolio_adjustment_ledger (user_id, code, event_type, amount, curr, note, source)
            VALUES ('', 'sh600023', 'dividend', 4.0, 'CNY', '', 'test')
            """
        )
        conn.commit()
        conn.close()

        app_module.db.set_portfolio_legacy_adjustment_ignored(True, note='切到新口径')

        list_resp = self.client.get('/api/portfolio')
        self.assertEqual(list_resp.status_code, 200)
        items = list_resp.get_json() or []
        target = next((item for item in items if item.get('code') == 'sh600023'), None)
        self.assertIsNotNone(target)
        self.assertTrue(bool(target.get('legacy_adjustment_ignored')))
        self.assertAlmostEqual(float(target.get('legacy_adjustment') or 0.0), 0.0, places=6)
        self.assertAlmostEqual(float(target.get('ledger_adjustment') or 0.0), 4.0, places=6)
        self.assertAlmostEqual(float(target.get('adjustment') or 0.0), 4.0, places=6)

    def test_legacy_adjustment_migration_report_marks_ready_when_no_old_value(self):
        add_resp = self.client.post('/api/portfolio/add', json={
            'code': 'sh600024',
            'name': '测试迁移盘点就绪',
            'price': 10.0,
            'qty': 5.0,
        })
        self.assertEqual(add_resp.status_code, 200)

        report = app_module.db.get_portfolio_legacy_adjustment_migration_report()
        self.assertTrue(bool(report.get('ready_to_ignore_now')))
        self.assertEqual(report.get('migration_status'), '可直接切新口径')
        self.assertEqual(int(report.get('nonzero_legacy_position_count') or 0), 0)
        self.assertAlmostEqual(float(report.get('nonzero_legacy_adjustment_total') or 0.0), 0.0, places=6)
        positions = report.get('positions') or []
        self.assertEqual(len(positions), 1)
        self.assertEqual(positions[0].get('migration_hint'), '可直接切新口径')
        self.assertEqual(int(positions[0].get('correction_count') or 0), 1)

    def test_legacy_adjustment_migration_report_lists_positions_that_need_manual_review(self):
        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO portfolio (code, name, qty, price, curr, adjustment, asset_type, user_id, updated_at)
            VALUES ('usAAPL', '苹果', 3.0, 100.0, 'USD', 12.5, 'us', 'legacy-user', datetime('now','localtime'))
            """
        )
        cursor.execute(
            """
            INSERT INTO transactions (code, name, type, price, qty, amount, pnl, time, user_id, curr, market, effective_date)
            VALUES ('usAAPL', '苹果', '减仓', 110.0, 1.0, 110.0, 10.0, '2026-03-18 21:30:00', 'legacy-user', 'USD', 'us', '2026-03-18')
            """
        )
        cursor.execute(
            """
            INSERT INTO portfolio_adjustment_ledger (user_id, code, event_type, amount, curr, note, source)
            VALUES ('legacy-user', 'usAAPL', 'dividend', 3.0, 'USD', '历史现金分红', 'test')
            """
        )
        conn.commit()
        conn.close()

        report = app_module.db.get_portfolio_legacy_adjustment_migration_report('legacy-user')
        self.assertFalse(bool(report.get('ready_to_ignore_now')))
        self.assertEqual(report.get('migration_status'), '仍需人工迁移')
        self.assertEqual(int(report.get('nonzero_legacy_position_count') or 0), 1)
        self.assertAlmostEqual(float(report.get('nonzero_legacy_adjustment_total') or 0.0), 12.5, places=6)
        positions = report.get('positions') or []
        self.assertEqual(len(positions), 1)
        target = positions[0]
        self.assertEqual(target.get('code'), 'usAAPL')
        self.assertTrue(bool(target.get('has_nonzero_legacy_adjustment')))
        self.assertEqual(target.get('migration_hint'), '需要人工迁移')
        self.assertAlmostEqual(float(target.get('legacy_adjustment') or 0.0), 12.5, places=6)
        self.assertAlmostEqual(float(target.get('ledger_adjustment') or 0.0), 3.0, places=6)
        self.assertAlmostEqual(float(target.get('realized_pnl_adjustment') or 0.0), 10.0, places=6)
        self.assertEqual(int(target.get('tx_count') or 0), 1)
        self.assertEqual(int(target.get('correction_count') or 0), 0)

        reports = app_module.db.list_portfolio_legacy_adjustment_migration_reports()
        target_report = next((item for item in reports if item.get('user_id') == 'legacy-user'), None)
        self.assertIsNotNone(target_report)
        self.assertEqual(target_report.get('migration_status'), '仍需人工迁移')

    def test_portfolio_modify_does_not_write_trade_transaction(self):
        add_resp = self.client.post('/api/portfolio/add', json={
            'code': 'sh600025',
            'name': '测试修正不写交易',
            'price': 10.0,
            'qty': 5.0,
        })
        self.assertEqual(add_resp.status_code, 200)

        modify_resp = self.client.post('/api/portfolio/modify', json={
            'code': 'sh600025',
            'qty': 8.0,
            'price': 9.5,
            'note': '补录初始份额',
            'request_id': 'req-modify-with-note-no-buy',
        })
        self.assertEqual(modify_resp.status_code, 200)
        self.assertEqual((modify_resp.get_json() or {}).get('status'), 'ok')

        resp = self.client.get('/api/portfolio/transactions?code=sh600025')
        self.assertEqual(resp.status_code, 200)
        records = (resp.get_json() or {}).get('records') or []
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0].get('type'), '持仓修正')
        self.assertEqual(records[0].get('note'), '补录初始份额')
        self.assertEqual(records[1].get('type'), '初始持仓')

    def test_portfolio_adjustment_event_updates_total_adjustment_and_transactions(self):
        add_resp = self.client.post('/api/portfolio/add', json={
            'code': 'sh600023',
            'name': '测试收益事件',
            'price': 10.0,
            'qty': 5.0,
        })
        self.assertEqual(add_resp.status_code, 200)

        dividend_resp = self.client.post('/api/portfolio/adjustment_event', json={
            'code': 'sh600023',
            'event_type': 'dividend',
            'amount': 8.0,
            'note': '补记现金分红',
            'request_id': 'req-adjustment-event-dividend',
        })
        self.assertEqual(dividend_resp.status_code, 200)
        self.assertEqual((dividend_resp.get_json() or {}).get('status'), 'ok')

        fee_resp = self.client.post('/api/portfolio/adjustment_event', json={
            'code': 'sh600023',
            'event_type': 'fee',
            'amount': 2.0,
            'note': '补记手续费',
            'request_id': 'req-adjustment-event-fee',
        })
        self.assertEqual(fee_resp.status_code, 200)
        self.assertEqual((fee_resp.get_json() or {}).get('status'), 'ok')

        list_resp = self.client.get('/api/portfolio')
        items = list_resp.get_json() or []
        target = next((item for item in items if item.get('code') == 'sh600023'), None)
        self.assertIsNotNone(target)
        self.assertAlmostEqual(float(target.get('adjustment') or 0.0), 6.0, places=6)

        metrics_resp = self.client.get('/api/portfolio?with_metrics=1')
        self.assertEqual(metrics_resp.status_code, 200)
        metric_items = metrics_resp.get_json() or []
        metric_target = next((item for item in metric_items if item.get('code') == 'sh600023'), None)
        self.assertIsNotNone(metric_target)
        self.assertAlmostEqual(float(metric_target.get('display_cost_price') or 0.0), 10.0, places=6)

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT event_type, amount, note
            FROM portfolio_adjustment_ledger
            WHERE code = ?
            ORDER BY id
            """,
            ('sh600023',),
        )
        rows = cursor.fetchall()
        conn.close()
        self.assertEqual([(row['event_type'], float(row['amount'])) for row in rows], [
            ('dividend', 8.0),
            ('fee', -2.0),
        ])
        self.assertEqual(rows[0]['note'], '补记现金分红')
        self.assertEqual(rows[1]['note'], '补记手续费')

        tx_resp = self.client.get('/api/portfolio/transactions?code=sh600023')
        self.assertEqual(tx_resp.status_code, 200)
        records = (tx_resp.get_json() or {}).get('records') or []
        self.assertCountEqual([item.get('type') for item in records], ['手续费', '分红', '初始持仓'])

    def test_portfolio_adjustment_event_allows_empty_note(self):
        add_resp = self.client.post('/api/portfolio/add', json={
            'code': 'sh600026',
            'name': '测试收益事件空备注',
            'price': 10.0,
            'qty': 5.0,
        })
        self.assertEqual(add_resp.status_code, 200)

        dividend_resp = self.client.post('/api/portfolio/adjustment_event', json={
            'code': 'sh600026',
            'event_type': 'dividend',
            'amount': 8.0,
            'request_id': 'req-adjustment-event-empty-note',
        })
        self.assertEqual(dividend_resp.status_code, 200)
        self.assertEqual((dividend_resp.get_json() or {}).get('status'), 'ok')

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT event_type, amount, note
            FROM portfolio_adjustment_ledger
            WHERE code = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            ('sh600026',),
        )
        row = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(row)
        self.assertEqual(row['event_type'], 'dividend')
        self.assertAlmostEqual(float(row['amount']), 8.0, places=6)
        self.assertEqual(row['note'], '')

    def test_add_buy_sell_reject_non_positive_price(self):
        bad_add = self.client.post('/api/portfolio/add', json={
            'code': 'sh600003',
            'name': '非法新增',
            'price': 0.0,
            'qty': 1.0,
        })
        self.assertEqual(bad_add.status_code, 400)
        self.assertEqual((bad_add.get_json() or {}).get('code'), 'INVALID_VALUE')

        add_ok = self.client.post('/api/portfolio/add', json={
            'code': 'sh600003',
            'name': '合法新增',
            'price': 10.0,
            'qty': 2.0,
        })
        self.assertEqual(add_ok.status_code, 200)

        bad_buy = self.client.post('/api/portfolio/buy', json={
            'code': 'sh600003',
            'price': -1.0,
            'qty': 1.0,
        })
        self.assertEqual(bad_buy.status_code, 400)
        self.assertEqual((bad_buy.get_json() or {}).get('code'), 'INVALID_VALUE')

        bad_sell = self.client.post('/api/portfolio/sell', json={
            'code': 'sh600003',
            'price': 0.0,
            'qty': 1.0,
        })
        self.assertEqual(bad_sell.status_code, 400)
        self.assertEqual((bad_sell.get_json() or {}).get('code'), 'INVALID_VALUE')

    def test_delete_corrective_removes_transactions_and_future_snapshots(self):
        add_resp = self.client.post('/api/portfolio/add', json={
            'code': 'sh600001',
            'name': '测试纠错',
            'price': 10.0,
            'qty': 10.0,
        })
        self.assertEqual(add_resp.status_code, 200)

        buy_resp = self.client.post('/api/portfolio/buy', json={
            'code': 'sh600001',
            'price': 11.0,
            'qty': 2.0,
        })
        self.assertEqual(buy_resp.status_code, 200)

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        d1 = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        d2 = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
        cursor.execute(
            """
            INSERT OR REPLACE INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
            VALUES (?, 1, 1, 1, 0, 0, 0, 0, '')
            """,
            (d1,),
        )
        cursor.execute(
            """
            INSERT OR REPLACE INTO daily_snapshots
            (date, total_asset, total_invest, total_cash, total_other, total_liability, total_pnl, day_pnl, user_id)
            VALUES (?, 1, 1, 1, 0, 0, 0, 0, '')
            """,
            (d2,),
        )
        conn.commit()
        conn.close()

        delete_resp = self.client.post('/api/portfolio/delete_corrective', json={
            'code': 'sh600001',
            'request_id': 'req-corrective-1',
        })
        self.assertEqual(delete_resp.status_code, 200)
        payload = delete_resp.get_json()
        self.assertEqual(payload.get('status'), 'ok')
        self.assertEqual(payload.get('code'), 'CORRECTIVE_DELETE_DONE')
        self.assertIn('deleted', payload)

        portfolio_resp = self.client.get('/api/portfolio')
        self.assertEqual(portfolio_resp.status_code, 200)
        portfolio_items = portfolio_resp.get_json() or []
        self.assertFalse(any(item.get('code') == 'sh600001' for item in portfolio_items))

        tx_resp = self.client.get('/api/transactions')
        self.assertEqual(tx_resp.status_code, 200)
        tx_items = tx_resp.get_json() or []
        self.assertFalse(any(item.get('code') == 'sh600001' for item in tx_items))

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(1) AS cnt FROM daily_snapshots WHERE date IN (?, ?) AND (user_id IS NULL OR user_id = '')",
            (d1, d2),
        )
        remaining = int(cursor.fetchone()['cnt'])
        conn.close()
        self.assertEqual(remaining, 0)

    def test_portfolio_ledger_isolation_keeps_adjustments_separate(self):
        default_ledger_id = app_module.db.get_default_ledger_id('')
        second_ledger = app_module.db.create_ledger('', '第二账本')
        second_ledger_id = int(second_ledger['ledger_id'])

        asset_payload = {
            'code': 'sh600031',
            'name': '账本隔离测试',
            'qty': 10.0,
            'price': 10.0,
            'curr': 'CNY',
            'asset_type': 'a',
            'adjustment': 0.0,
        }
        self.assertTrue(app_module.db.add_asset(dict(asset_payload), user_id='', ledger_id=default_ledger_id))
        self.assertTrue(
            app_module.db.add_asset(
                {
                    **asset_payload,
                    'qty': 8.0,
                    'price': 12.0,
                },
                user_id='',
                ledger_id=second_ledger_id,
            )
        )

        dividend_detail = app_module.db.add_portfolio_adjustment_event(
            code='sh600031',
            event_type='dividend',
            amount=5.0,
            user_id='',
            return_detail=True,
            ledger_id=default_ledger_id,
        )
        self.assertTrue(dividend_detail.get('ok'))

        sell_detail = app_module.db.sell_asset(
            code='sh600031',
            price=15.0,
            qty=2.0,
            user_id='',
            return_detail=True,
            ledger_id=second_ledger_id,
        )
        self.assertTrue(sell_detail.get('ok'))

        default_items = app_module.db.get_portfolio(user_id='', ledger_id=default_ledger_id)
        second_items = app_module.db.get_portfolio(user_id='', ledger_id=second_ledger_id)
        self.assertEqual(len(default_items), 1)
        self.assertEqual(len(second_items), 1)

        self.assertAlmostEqual(float(default_items[0].get('ledger_adjustment') or 0.0), 5.0, places=6)
        self.assertAlmostEqual(float(default_items[0].get('realized_pnl_adjustment') or 0.0), 0.0, places=6)
        self.assertAlmostEqual(float(default_items[0].get('adjustment_total') or 0.0), 5.0, places=6)

        self.assertAlmostEqual(float(second_items[0].get('ledger_adjustment') or 0.0), 0.0, places=6)
        self.assertAlmostEqual(float(second_items[0].get('realized_pnl_adjustment') or 0.0), 6.0, places=6)
        self.assertAlmostEqual(float(second_items[0].get('adjustment_total') or 0.0), 6.0, places=6)

    def test_delete_corrective_removes_target_ledger_snapshots_only(self):
        default_ledger_id = app_module.db.get_default_ledger_id('')
        second_ledger = app_module.db.create_ledger('', '保留账本')
        second_ledger_id = int(second_ledger['ledger_id'])

        self.assertTrue(
            app_module.db.add_asset(
                {
                    'code': 'sh600099',
                    'name': '纠错删账本快照',
                    'qty': 10.0,
                    'price': 10.0,
                    'curr': 'CNY',
                    'asset_type': 'a',
                    'adjustment': 0.0,
                },
                user_id='',
                ledger_id=default_ledger_id,
            )
        )

        d1 = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        d2 = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
        self.assertTrue(
            app_module.db.save_ledger_daily_snapshot(user_id='', ledger_id=default_ledger_id, date_str=d1, total_cost=100.0)
        )
        self.assertTrue(
            app_module.db.save_ledger_daily_snapshot(user_id='', ledger_id=default_ledger_id, date_str=d2, total_cost=100.0)
        )
        self.assertTrue(
            app_module.db.save_ledger_daily_snapshot(user_id='', ledger_id=second_ledger_id, date_str=d1, total_cost=200.0)
        )
        self.assertTrue(
            app_module.db.save_ledger_daily_snapshot(user_id='', ledger_id=second_ledger_id, date_str=d2, total_cost=200.0)
        )

        delete_resp = self.client.post('/api/portfolio/delete_corrective', json={
            'code': 'sh600099',
            'ledger_id': default_ledger_id,
            'request_id': 'req-corrective-ledger-1',
        })
        self.assertEqual(delete_resp.status_code, 200)

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(1) AS cnt FROM ledger_daily_snapshots WHERE ledger_id = ? AND date IN (?, ?)",
            (default_ledger_id, d1, d2),
        )
        removed_count = int(cursor.fetchone()['cnt'])
        cursor.execute(
            "SELECT COUNT(1) AS cnt FROM ledger_daily_snapshots WHERE ledger_id = ? AND date IN (?, ?)",
            (second_ledger_id, d1, d2),
        )
        kept_count = int(cursor.fetchone()['cnt'])
        conn.close()

        self.assertEqual(removed_count, 0)
        self.assertEqual(kept_count, 2)

    def test_portfolio_rejects_invalid_ledger_id_query(self):
        resp = self.client.get('/api/portfolio?ledger_id=bad-ledger')
        self.assertEqual(resp.status_code, 400)
        payload = resp.get_json() or {}
        self.assertEqual(payload.get('code'), 'INVALID_LEDGER_ID')

    def test_ledger_reorder_updates_sort_order(self):
        user_id = 'u_ledger_reorder'
        username = 'ledger_reorder_user'
        _seed_user(user_id, username)
        headers = _auth_headers(user_id, username)
        default_ledger_id = app_module.db.get_default_ledger_id(user_id)
        second_ledger = app_module.db.create_ledger(user_id, '第二账本')
        third_ledger = app_module.db.create_ledger(user_id, '第三账本')

        resp = self.client.put('/api/portfolio/ledgers/reorder', json={
            'ledger_ids': [third_ledger['ledger_id'], default_ledger_id, second_ledger['ledger_id']],
        }, headers=headers)

        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json() or {}
        self.assertTrue(payload.get('ok'))

        ledgers = app_module.db.get_ledgers(user_id)
        self.assertEqual(
            [ledger['id'] for ledger in ledgers],
            [third_ledger['ledger_id'], default_ledger_id, second_ledger['ledger_id']],
        )

    def test_ledger_reorder_rejects_unknown_ledger(self):
        user_id = 'u_ledger_reorder'
        username = 'ledger_reorder_user'
        _seed_user(user_id, username)
        headers = _auth_headers(user_id, username)
        default_ledger_id = app_module.db.get_default_ledger_id(user_id)
        app_module.db.create_ledger(user_id, '第二账本')

        resp = self.client.put('/api/portfolio/ledgers/reorder', json={
            'ledger_ids': [default_ledger_id, 999999],
        }, headers=headers)

        self.assertEqual(resp.status_code, 400)
        payload = resp.get_json() or {}
        self.assertEqual(payload.get('code'), 'INVALID_LEDGER_IDS')

    def test_delete_empty_non_default_ledger_succeeds(self):
        user_id = 'u_delete_empty_ledger'
        username = 'delete_empty_ledger_user'
        _seed_user(user_id, username)
        headers = _auth_headers(user_id, username)
        ledger = app_module.db.create_ledger(user_id, '待删除账本')

        resp = self.client.delete(
            f"/api/portfolio/ledgers/{ledger['ledger_id']}",
            headers=headers,
        )

        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json() or {}
        self.assertTrue(payload.get('ok'))

        ledgers = app_module.db.get_ledgers(user_id)
        self.assertNotIn(ledger['ledger_id'], [item['id'] for item in ledgers])

    def test_delete_empty_non_default_ledger_also_removes_ledger_snapshots(self):
        user_id = 'u_delete_empty_ledger_snapshots'
        username = 'delete_empty_ledger_snapshots_user'
        _seed_user(user_id, username)
        headers = _auth_headers(user_id, username)
        ledger = app_module.db.create_ledger(user_id, '待删除账本')
        ledger_id = int(ledger['ledger_id'])

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO ledger_daily_snapshots
            (user_id, ledger_id, date, total_market_value, total_cost, total_pnl, total_pnl_rate, day_pnl, holdings_count)
            VALUES (?, ?, '2026-03-22', 100.0, 100.0, 5.0, 5.0, 5.0, 1)
            """,
            (user_id, ledger_id),
        )
        cursor.execute(
            """
            INSERT INTO ledger_daily_snapshots
            (user_id, ledger_id, date, total_market_value, total_cost, total_pnl, total_pnl_rate, day_pnl, holdings_count)
            VALUES (?, ?, '2026-03-23', 110.0, 100.0, 6.0, 6.0, 1.0, 1)
            """,
            (user_id, ledger_id),
        )
        conn.commit()
        conn.close()

        resp = self.client.delete(
            f"/api/portfolio/ledgers/{ledger_id}",
            headers=headers,
        )

        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json() or {}
        self.assertTrue(payload.get('ok'))

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(1) AS cnt FROM ledger_daily_snapshots WHERE user_id = ? AND ledger_id = ?",
            (user_id, ledger_id),
        )
        row = cursor.fetchone()
        conn.close()
        self.assertEqual(0, int(row['cnt']))

    def test_delete_non_default_ledger_with_holdings_is_rejected(self):
        user_id = 'u_delete_non_empty_ledger'
        username = 'delete_non_empty_ledger_user'
        _seed_user(user_id, username)
        headers = _auth_headers(user_id, username)
        ledger = app_module.db.create_ledger(user_id, '有持仓账本')

        add_resp = self.client.post(
            '/api/portfolio/add',
            json={
                'code': 'sh600519',
                'name': '贵州茅台',
                'price': 1500.0,
                'qty': 1.0,
                'ledger_id': ledger['ledger_id'],
            },
            headers=headers,
        )
        self.assertEqual(add_resp.status_code, 200)

        resp = self.client.delete(
            f"/api/portfolio/ledgers/{ledger['ledger_id']}",
            headers=headers,
        )

        self.assertEqual(resp.status_code, 400)
        payload = resp.get_json() or {}
        self.assertEqual(payload.get('code'), 'HAS_HOLDINGS')

    def test_add_asset_update_only_touches_target_ledger(self):
        user_id = 'u_add_asset_ledger_isolation'
        username = 'add_asset_ledger_isolation_user'
        _seed_user(user_id, username)
        default_ledger_id = app_module.db.get_default_ledger_id(user_id)
        second_ledger = app_module.db.create_ledger(user_id, '第二账本')
        second_ledger_id = int(second_ledger['ledger_id'])

        self.assertTrue(
            app_module.db.add_asset(
                {
                    'code': 'sh600900',
                    'name': '长江电力',
                    'qty': 100.0,
                    'price': 30.0,
                    'curr': 'CNY',
                    'asset_type': 'a',
                },
                user_id=user_id,
                ledger_id=default_ledger_id,
            )
        )
        self.assertTrue(
            app_module.db.add_asset(
                {
                    'code': 'sh600900',
                    'name': '长江电力',
                    'qty': 200.0,
                    'price': 31.0,
                    'curr': 'CNY',
                    'asset_type': 'a',
                },
                user_id=user_id,
                ledger_id=second_ledger_id,
            )
        )
        self.assertTrue(
            app_module.db.add_asset(
                {
                    'code': 'sh600900',
                    'name': '长江电力',
                    'qty': 150.0,
                    'price': 32.0,
                    'curr': 'CNY',
                    'asset_type': 'a',
                },
                user_id=user_id,
                ledger_id=default_ledger_id,
            )
        )

        default_item = app_module.db.get_asset(
            'sh600900',
            user_id=user_id,
            ledger_id=default_ledger_id,
        )
        second_item = app_module.db.get_asset(
            'sh600900',
            user_id=user_id,
            ledger_id=second_ledger_id,
        )

        self.assertIsNotNone(default_item)
        self.assertIsNotNone(second_item)
        self.assertAlmostEqual(float(default_item['qty']), 150.0)
        self.assertAlmostEqual(float(default_item['price']), 32.0)
        self.assertAlmostEqual(float(second_item['qty']), 200.0)
        self.assertAlmostEqual(float(second_item['price']), 31.0)

    def test_db_init_keeps_same_code_positions_in_different_ledgers(self):
        user_id = 'u_init_keeps_cross_ledger_positions'
        username = 'init_keeps_cross_ledger_positions_user'
        _seed_user(user_id, username)
        default_ledger_id = app_module.db.get_default_ledger_id(user_id)
        second_ledger = app_module.db.create_ledger(user_id, '第二账本')
        second_ledger_id = int(second_ledger['ledger_id'])

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO portfolio (
                code, name, qty, price, curr, adjustment, asset_type, user_id, ledger_id
            ) VALUES (?, ?, ?, ?, 'CNY', 0.0, 'a', ?, ?)
            """,
            ('sh600900', '长江电力', 100.0, 26.0, user_id, default_ledger_id),
        )
        cursor.execute(
            """
            INSERT INTO portfolio (
                code, name, qty, price, curr, adjustment, asset_type, user_id, ledger_id
            ) VALUES (?, ?, ?, ?, 'CNY', 0.0, 'a', ?, ?)
            """,
            ('sh600900', '长江电力', 200.0, 27.0, user_id, second_ledger_id),
        )
        conn.commit()
        conn.close()

        app_module.db.init_database()

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT ledger_id, qty, price
            FROM portfolio
            WHERE user_id = ? AND code = ?
            ORDER BY ledger_id
            """,
            (user_id, 'sh600900'),
        )
        rows = cursor.fetchall()
        conn.close()

        self.assertEqual(2, len(rows))
        self.assertEqual([default_ledger_id, second_ledger_id], [int(row['ledger_id']) for row in rows])
        self.assertAlmostEqual(100.0, float(rows[0]['qty']))
        self.assertAlmostEqual(200.0, float(rows[1]['qty']))

    def test_sell_all_keeps_realized_pnl_in_cumulative_total(self):
        add_resp = self.client.post('/api/portfolio/add', json={
            'code': 'sh600010',
            'name': '测试清仓',
            'price': 10.0,
            'qty': 10.0,
        })
        self.assertEqual(add_resp.status_code, 200)

        sell_resp = self.client.post('/api/portfolio/sell', json={
            'code': 'sh600010',
            'price': 12.0,
            'qty': 10.0,
            'request_id': 'req-sellall-1',
        })
        self.assertEqual(sell_resp.status_code, 200)
        self.assertEqual(sell_resp.get_json().get('status'), 'ok')

        list_resp = self.client.get('/api/portfolio')
        self.assertEqual(list_resp.status_code, 200)
        items = list_resp.get_json() or []
        self.assertFalse(any(item.get('code') == 'sh600010' for item in items))

        with patch('core.snapshot.batch_get_prices', return_value={'sh600010': (12.0, 12.0, 0, 0)}):
            with patch('core.snapshot.get_forex_rates', return_value={'CNY': 1.0}):
                stats = app_module.calculate_portfolio_stats(None)
        self.assertAlmostEqual(float(stats.get('total_pnl') or 0.0), 20.0, places=2)

    def test_sell_undo_removes_realized_pnl_ledger(self):
        add_resp = self.client.post('/api/portfolio/add', json={
            'code': 'sh600012',
            'name': '测试撤销卖出',
            'price': 10.0,
            'qty': 10.0,
        })
        self.assertEqual(add_resp.status_code, 200)

        sell_resp = self.client.post('/api/portfolio/sell', json={
            'code': 'sh600012',
            'price': 12.0,
            'qty': 2.0,
            'request_id': 'req-sell-undo-ledger',
        })
        self.assertEqual(sell_resp.status_code, 200)
        undo_token = (sell_resp.get_json() or {}).get('undo_token')
        self.assertTrue(isinstance(undo_token, str) and len(undo_token) > 0)

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(1) AS c FROM portfolio_adjustment_ledger WHERE code = ?", ('sh600012',))
        before_cnt = int(cursor.fetchone()['c'] or 0)
        conn.close()
        self.assertEqual(before_cnt, 0)

        undo_resp = self.client.post('/api/portfolio/undo', json={'undo_token': undo_token})
        self.assertEqual(undo_resp.status_code, 200)
        self.assertEqual((undo_resp.get_json() or {}).get('code'), 'UNDO_DONE')

        portfolio_resp = self.client.get('/api/portfolio')
        items = portfolio_resp.get_json() or []
        target = next((item for item in items if item.get('code') == 'sh600012'), None)
        self.assertIsNotNone(target)
        self.assertAlmostEqual(float(target.get('qty') or 0.0), 10.0, places=6)
        self.assertAlmostEqual(float(target.get('adjustment') or 0.0), 0.0, places=6)

        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(1) AS c FROM portfolio_adjustment_ledger WHERE code = ?", ('sh600012',))
        after_cnt = int(cursor.fetchone()['c'] or 0)
        conn.close()
        self.assertEqual(after_cnt, 0)

    def test_buy_with_cash_and_undo_restores_cash_and_portfolio(self):
        add_cash_resp = self.client.post('/api/cash_assets/add', json={
            'name': '银行卡',
            'amount': 20000.0,
            'curr': 'CNY',
        })
        self.assertEqual(add_cash_resp.status_code, 200)

        cash_list_resp = self.client.get('/api/cash_assets')
        self.assertEqual(cash_list_resp.status_code, 200)
        cash_assets = cash_list_resp.get_json() or []
        self.assertTrue(len(cash_assets) > 0)
        cash_id = cash_assets[-1]['id']

        buy_resp = self.client.post('/api/portfolio/buy_with_cash', json={
            'code': 'sh600000',
            'name': '浦发银行',
            'price': 10.0,
            'qty': 100.0,
            'cash_asset_id': cash_id,
            'request_id': 'req-buy-with-cash-1',
        })
        self.assertEqual(buy_resp.status_code, 200)
        buy_payload = buy_resp.get_json()
        self.assertEqual(buy_payload.get('status'), 'ok')
        self.assertGreater(int(buy_resp.headers.get('X-Trace-Stage-Count') or 0), 0)
        undo_token = buy_payload.get('undo_token')
        self.assertTrue(isinstance(undo_token, str) and len(undo_token) > 0)

        portfolio_resp = self.client.get('/api/portfolio')
        self.assertEqual(portfolio_resp.status_code, 200)
        portfolio_items = portfolio_resp.get_json() or []
        target = next((item for item in portfolio_items if item.get('code') == 'sh600000'), None)
        self.assertIsNotNone(target)
        self.assertAlmostEqual(float(target.get('qty', 0)), 100.0)

        cash_list_resp_after_buy = self.client.get('/api/cash_assets')
        self.assertEqual(cash_list_resp_after_buy.status_code, 200)
        cash_after_buy = cash_list_resp_after_buy.get_json() or []
        buy_cash_item = next((item for item in cash_after_buy if item.get('id') == cash_id), None)
        self.assertIsNotNone(buy_cash_item)
        self.assertAlmostEqual(float(buy_cash_item.get('amount', 0)), 19000.0)

        undo_resp = self.client.post('/api/portfolio/undo', json={
            'undo_token': undo_token,
        })
        self.assertEqual(undo_resp.status_code, 200)
        undo_payload = undo_resp.get_json()
        self.assertEqual(undo_payload.get('status'), 'ok')
        self.assertEqual(undo_payload.get('code'), 'UNDO_DONE')
        self.assertGreater(int(undo_resp.headers.get('X-Trace-Stage-Count') or 0), 0)

        portfolio_resp_after_undo = self.client.get('/api/portfolio')
        self.assertEqual(portfolio_resp_after_undo.status_code, 200)
        portfolio_after_undo = portfolio_resp_after_undo.get_json() or []
        self.assertFalse(any(item.get('code') == 'sh600000' for item in portfolio_after_undo))

        cash_list_resp_after_undo = self.client.get('/api/cash_assets')
        self.assertEqual(cash_list_resp_after_undo.status_code, 200)
        cash_after_undo = cash_list_resp_after_undo.get_json() or []
        undo_cash_item = next((item for item in cash_after_undo if item.get('id') == cash_id), None)
        self.assertIsNotNone(undo_cash_item)
        self.assertAlmostEqual(float(undo_cash_item.get('amount', 0)), 20000.0)

    def test_sell_to_cash_and_undo_restores_cash_and_portfolio(self):
        add_resp = self.client.post('/api/portfolio/add', json={
            'code': 'sh600519',
            'name': '贵州茅台',
            'price': 1000.0,
            'qty': 10.0,
        })
        self.assertEqual(add_resp.status_code, 200)

        add_cash_resp = self.client.post('/api/cash_assets/add', json={
            'name': '银行卡',
            'amount': 2000.0,
            'curr': 'CNY',
        })
        self.assertEqual(add_cash_resp.status_code, 200)

        cash_list_resp = self.client.get('/api/cash_assets')
        self.assertEqual(cash_list_resp.status_code, 200)
        cash_assets = cash_list_resp.get_json() or []
        cash_id = cash_assets[-1]['id']

        sell_resp = self.client.post('/api/portfolio/sell_to_cash', json={
            'code': 'sh600519',
            'price': 1200.0,
            'qty': 2.0,
            'cash_asset_id': cash_id,
            'request_id': 'req-sell-to-cash-1',
        })
        self.assertEqual(sell_resp.status_code, 200)
        sell_payload = sell_resp.get_json() or {}
        self.assertEqual(sell_payload.get('status'), 'ok')
        self.assertGreater(int(sell_resp.headers.get('X-Trace-Stage-Count') or 0), 0)
        self.assertAlmostEqual(float(sell_payload.get('cash_added') or 0.0), 2400.0)
        undo_token = sell_payload.get('undo_token')
        self.assertTrue(isinstance(undo_token, str) and len(undo_token) > 0)

        portfolio_resp = self.client.get('/api/portfolio')
        self.assertEqual(portfolio_resp.status_code, 200)
        portfolio_items = portfolio_resp.get_json() or []
        target = next((item for item in portfolio_items if item.get('code') == 'sh600519'), None)
        self.assertIsNotNone(target)
        self.assertAlmostEqual(float(target.get('qty', 0)), 8.0)

        cash_after_sell_resp = self.client.get('/api/cash_assets')
        self.assertEqual(cash_after_sell_resp.status_code, 200)
        cash_after_sell = cash_after_sell_resp.get_json() or []
        sell_cash_item = next((item for item in cash_after_sell if item.get('id') == cash_id), None)
        self.assertIsNotNone(sell_cash_item)
        self.assertAlmostEqual(float(sell_cash_item.get('amount', 0)), 4400.0)

        undo_resp = self.client.post('/api/portfolio/undo', json={'undo_token': undo_token})
        self.assertEqual(undo_resp.status_code, 200)
        self.assertEqual((undo_resp.get_json() or {}).get('code'), 'UNDO_DONE')

        portfolio_after_undo_resp = self.client.get('/api/portfolio')
        self.assertEqual(portfolio_after_undo_resp.status_code, 200)
        portfolio_after_undo = portfolio_after_undo_resp.get_json() or []
        undo_target = next((item for item in portfolio_after_undo if item.get('code') == 'sh600519'), None)
        self.assertIsNotNone(undo_target)
        self.assertAlmostEqual(float(undo_target.get('qty', 0)), 10.0)

        cash_after_undo_resp = self.client.get('/api/cash_assets')
        self.assertEqual(cash_after_undo_resp.status_code, 200)
        cash_after_undo = cash_after_undo_resp.get_json() or []
        undo_cash_item = next((item for item in cash_after_undo if item.get('id') == cash_id), None)
        self.assertIsNotNone(undo_cash_item)
        self.assertAlmostEqual(float(undo_cash_item.get('amount', 0)), 2000.0)

    def test_buy_with_cash_undo_only_removes_target_ledger_position(self):
        user_id = 'u_buy_with_cash_undo_ledger'
        username = 'buy_with_cash_undo_ledger_user'
        _seed_user(user_id, username)
        headers = _auth_headers(user_id, username)
        default_ledger_id = app_module.db.get_default_ledger_id(user_id)
        second_ledger = app_module.db.create_ledger(user_id, '第二账本')
        second_ledger_id = int(second_ledger['ledger_id'])

        add_cash_resp = self.client.post('/api/cash_assets/add', json={
            'name': '银行卡',
            'amount': 50000.0,
            'curr': 'CNY',
        }, headers=headers)
        self.assertEqual(add_cash_resp.status_code, 200)

        cash_assets = (self.client.get('/api/cash_assets', headers=headers).get_json() or [])
        cash_id = cash_assets[-1]['id']

        add_default_resp = self.client.post('/api/portfolio/add', json={
            'code': 'sh600900',
            'name': '长江电力',
            'price': 29.0,
            'qty': 100.0,
            'ledger_id': default_ledger_id,
        }, headers=headers)
        self.assertEqual(add_default_resp.status_code, 200)

        buy_resp = self.client.post('/api/portfolio/buy_with_cash', json={
            'code': 'sh600900',
            'name': '长江电力',
            'price': 30.0,
            'qty': 200.0,
            'cash_asset_id': cash_id,
            'ledger_id': second_ledger_id,
            'request_id': 'req-buy-with-cash-ledger-undo-1',
        }, headers=headers)
        self.assertEqual(buy_resp.status_code, 200)
        undo_token = (buy_resp.get_json() or {}).get('undo_token')
        self.assertTrue(isinstance(undo_token, str) and len(undo_token) > 0)

        undo_resp = self.client.post('/api/portfolio/undo', json={
            'undo_token': undo_token,
        }, headers=headers)
        self.assertEqual(undo_resp.status_code, 200)

        default_item = app_module.db.get_asset(
            'sh600900',
            user_id=user_id,
            ledger_id=default_ledger_id,
        )
        second_item = app_module.db.get_asset(
            'sh600900',
            user_id=user_id,
            ledger_id=second_ledger_id,
        )

        self.assertIsNotNone(default_item)
        self.assertAlmostEqual(float(default_item['qty']), 100.0)
        self.assertIsNone(second_item)

    def test_buy_with_cash_supports_cross_currency_cash_account(self):
        add_cash_resp = self.client.post('/api/cash_assets/add', json={
            'name': '中国银行',
            'amount': 20000.0,
            'curr': 'CNY',
        })
        self.assertEqual(add_cash_resp.status_code, 200)

        cash_list_resp = self.client.get('/api/cash_assets')
        self.assertEqual(cash_list_resp.status_code, 200)
        cash_assets = cash_list_resp.get_json() or []
        cash_id = cash_assets[-1]['id']

        buy_resp = self.client.post('/api/portfolio/buy_with_cash', json={
            'code': 'AAPL',
            'name': '苹果',
            'price': 252.82,
            'qty': 1.0,
            'curr': 'USD',
            'asset_type': 'us',
            'cash_asset_id': cash_id,
            'request_id': 'req-buy-with-cny-cash-us-stock',
        })
        self.assertEqual(buy_resp.status_code, 200)
        self.assertEqual((buy_resp.get_json() or {}).get('status'), 'ok')
        self.assertGreater(int(buy_resp.headers.get('X-Trace-Stage-Count') or 0), 0)

        portfolio_resp = self.client.get('/api/portfolio')
        self.assertEqual(portfolio_resp.status_code, 200)
        portfolio_items = portfolio_resp.get_json() or []
        self.assertTrue(any(item.get('name') == '苹果' for item in portfolio_items))

        cash_after_buy_resp = self.client.get('/api/cash_assets')
        self.assertEqual(cash_after_buy_resp.status_code, 200)
        cash_after_buy = cash_after_buy_resp.get_json() or []
        buy_cash_item = next((item for item in cash_after_buy if item.get('id') == cash_id), None)
        self.assertIsNotNone(buy_cash_item)
        self.assertLess(float(buy_cash_item.get('amount', 0)), 20000.0)

    def test_buy_with_cash_insufficient_balance_returns_400(self):
        add_cash_resp = self.client.post('/api/cash_assets/add', json={
            'name': '微信',
            'amount': 100.0,
            'curr': 'CNY',
        })
        self.assertEqual(add_cash_resp.status_code, 200)

        cash_list_resp = self.client.get('/api/cash_assets')
        self.assertEqual(cash_list_resp.status_code, 200)
        cash_assets = cash_list_resp.get_json() or []
        cash_id = cash_assets[-1]['id']

        buy_resp = self.client.post('/api/portfolio/buy_with_cash', json={
            'code': 'sh600000',
            'name': '浦发银行',
            'price': 20.0,
            'qty': 10.0,
            'cash_asset_id': cash_id,
        })
        self.assertEqual(buy_resp.status_code, 400)
        payload = buy_resp.get_json()
        self.assertEqual(payload.get('code'), 'INSUFFICIENT_CASH')

        portfolio_resp = self.client.get('/api/portfolio')
        self.assertEqual(portfolio_resp.status_code, 200)
        portfolio_items = portfolio_resp.get_json() or []
        self.assertFalse(any(item.get('code') == 'sh600000' for item in portfolio_items))

    def test_buy_with_cash_supports_fund_decimal_qty(self):
        add_cash_resp = self.client.post('/api/cash_assets/add', json={
            'name': '支付宝',
            'amount': 1000.0,
            'curr': 'CNY',
        })
        self.assertEqual(add_cash_resp.status_code, 200)

        cash_list_resp = self.client.get('/api/cash_assets')
        self.assertEqual(cash_list_resp.status_code, 200)
        cash_assets = cash_list_resp.get_json() or []
        cash_id = cash_assets[-1]['id']

        buy_resp = self.client.post('/api/portfolio/buy_with_cash', json={
            'code': 'f_110017',
            'name': '易方达增强回报债券A',
            'price': 1.2345,
            'qty': 81.0044,
            'cash_asset_id': cash_id,
            'request_id': 'req-buy-fund-decimal-qty',
        })
        self.assertEqual(buy_resp.status_code, 200)
        self.assertEqual((buy_resp.get_json() or {}).get('status'), 'ok')

        portfolio_resp = self.client.get('/api/portfolio')
        self.assertEqual(portfolio_resp.status_code, 200)
        portfolio_items = portfolio_resp.get_json() or []
        target = next((item for item in portfolio_items if item.get('code') == 'f_110017'), None)
        self.assertIsNotNone(target)
        self.assertAlmostEqual(float(target.get('qty') or 0.0), 81.0044, places=4)

    def test_buy_with_cash_merges_legacy_numeric_exchange_fund_position(self):
        conn = app_module.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO portfolio (code, name, qty, price, curr, adjustment, asset_type, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ('159655', '标普ETF', 8400.0, 1.783, 'CNY', 0.0, 'fund', ''),
        )
        conn.commit()
        conn.close()

        add_cash_resp = self.client.post('/api/cash_assets/add', json={
            'name': '浦发银行',
            'amount': 50000.0,
            'curr': 'CNY',
        })
        self.assertEqual(add_cash_resp.status_code, 200)

        cash_list_resp = self.client.get('/api/cash_assets')
        self.assertEqual(cash_list_resp.status_code, 200)
        cash_assets = cash_list_resp.get_json() or []
        cash_id = cash_assets[-1]['id']

        buy_resp = self.client.post('/api/portfolio/buy_with_cash', json={
            'code': '159655',
            'name': '标普ETF',
            'price': 1.72,
            'qty': 1600.0,
            'curr': 'CNY',
            'asset_type': 'fund',
            'cash_asset_id': cash_id,
            'request_id': 'req-buy-legacy-exchange-fund',
        })
        self.assertEqual(buy_resp.status_code, 200)
        self.assertEqual((buy_resp.get_json() or {}).get('status'), 'ok')

        portfolio_resp = self.client.get('/api/portfolio')
        self.assertEqual(portfolio_resp.status_code, 200)
        portfolio_items = portfolio_resp.get_json() or []
        legacy_target = next((item for item in portfolio_items if item.get('code') == '159655'), None)
        self.assertIsNotNone(legacy_target)
        self.assertAlmostEqual(float(legacy_target.get('qty') or 0.0), 10000.0, places=4)
        self.assertFalse(any(item.get('code') == 'sz159655' for item in portfolio_items))

        tx_resp = self.client.get('/api/transactions?limit=20')
        self.assertEqual(tx_resp.status_code, 200)
        tx_items = tx_resp.get_json() or []
        target_tx = next((item for item in tx_items if item.get('name') == '标普ETF'), None)
        self.assertIsNotNone(target_tx)
        self.assertEqual(target_tx.get('code'), '159655')

    def test_snapshot_trigger_returns_ok_when_take_snapshot_succeeds(self):
        with patch.object(app_module, 'take_snapshot', return_value=True) as mocked:
            resp = self.client.post('/api/snapshot/trigger', json={})
        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json() or {}
        self.assertEqual(payload.get('status'), 'ok')
        mocked.assert_called_once_with(None)

    def test_snapshot_fix_requires_dates_list(self):
        missing_resp = self.client.post('/api/snapshot/fix', json={})
        self.assertEqual(missing_resp.status_code, 400)
        self.assertEqual((missing_resp.get_json() or {}).get('error'), 'Missing dates')

        invalid_resp = self.client.post('/api/snapshot/fix', json={'dates': '2026-01-17'})
        self.assertEqual(invalid_resp.status_code, 400)
        self.assertEqual((invalid_resp.get_json() or {}).get('error'), 'dates must be a list')

        with patch.object(app_module.db, 'fix_snapshot_day_pnl', return_value=True) as mocked:
            ok_resp = self.client.post('/api/snapshot/fix', json={'dates': ['2026-01-17', '2026-01-18']})
        self.assertEqual(ok_resp.status_code, 200)
        self.assertEqual((ok_resp.get_json() or {}).get('status'), 'ok')
        mocked.assert_called_once_with(['2026-01-17', '2026-01-18'], None)


if __name__ == '__main__':
    unittest.main()
