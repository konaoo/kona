"""对账入口必须复核零占位，不把净值未发布当作平盘。"""
import unittest
from unittest.mock import Mock, patch

from scripts import reconcile_recent_fund_navs as reconcile


def run_plan(rows, points, *, verify_existing=False):
    db = Mock()
    db.get_position_qty_as_of_effective_date.return_value = 4665.88
    with patch.object(reconcile, "iter_dates", return_value=iter(["2026-11-17", "2026-11-18"])), patch.object(
        reconcile, "load_ledgers_with_snapshots", return_value=[("test-user", 62)]
    ), patch.object(reconcile, "load_fund_assets", return_value={"f_968163": {"name": "摩根亚洲总收益", "curr": "CNY"}}), patch.object(
        reconcile, "load_existing_rows", side_effect=lambda *args, date_str, **kwargs: rows.get(date_str, {})
    ), patch.object(reconcile, "get_asset_trend", return_value={"points": points}) as history, patch.object(
        reconcile, "derive_historical_fx", return_value=1
    ):
        repairs, warnings = reconcile.build_repairs(db, days=2, verify_existing=verify_existing)
    return repairs, warnings, history, db


class FundNavReconcileScriptTests(unittest.TestCase):
    def test_reconcile_excludes_legacy_stock_and_exchange_aliases(self):
        for code in ("f_600329", "f_601818", "f_159201", "f_513300"):
            with self.subTest(code=code):
                self.assertFalse(reconcile._is_otc_fund(code))
        for code in ("f_110018", "f_968048", "ft_LU1116320737"):
            with self.subTest(code=code):
                self.assertTrue(reconcile._is_otc_fund(code))

    def test_daily_plan_rechecks_exact_and_backfill_zero_only_with_confirmed_nav(self):
        rows = {
            "2026-11-17": {"f_968163": {"day_pnl": 0, "day_base": 0, "source": "exact"}},
            "2026-11-18": {"f_968163": {"day_pnl": 0, "day_base": 0, "source": "backfill"}},
        }
        repairs, warnings, history, db = run_plan(rows, [
            {"date": "2026-11-16", "value": 9.9}, {"date": "2026-11-17", "value": 9.9},
        ])
        self.assertEqual(len(repairs), 1)
        repair = repairs[0][2]
        self.assertEqual(repair.date_str, "2026-11-17")
        self.assertEqual(repair.day_pnl, 0)
        self.assertEqual(repair.day_base, 46192.21)
        self.assertEqual(len(warnings), 1)
        self.assertIn("2026-11-18", warnings[0])
        history.assert_called_once()
        db.save_daily_snapshot_asset_breakdowns.assert_not_called()

    def test_verified_zero_with_positive_base_does_not_request_history_again(self):
        row = {"f_968163": {"day_pnl": 0, "day_base": 46192.21, "source": "fund_nav_reconcile"}}
        repairs, warnings, history, _ = run_plan({"2026-11-17": row, "2026-11-18": row}, [])
        self.assertEqual(repairs, [])
        self.assertEqual(warnings, [])
        history.assert_not_called()

    def test_later_nav_replaces_pending_zero_but_not_confirmed_row(self):
        rows = {
            "2026-11-17": {"f_968163": {"day_pnl": 0, "day_base": 46192.21, "source": "fund_nav_reconcile"}},
            "2026-11-18": {"f_968163": {"day_pnl": 0, "day_base": 46192.21, "source": "exact"}},
        }
        # 模拟数据，不是线上 11/18 官方净值。
        repairs, warnings, _, _ = run_plan(rows, [
            {"date": "2026-11-17", "value": 9.9}, {"date": "2026-11-18", "value": 9.91},
        ])
        self.assertEqual(len(repairs), 1)
        self.assertEqual(repairs[0][2].date_str, "2026-11-18")
        self.assertEqual(repairs[0][2].day_pnl, 46.66)
        self.assertEqual(warnings, [])

    def test_manual_verify_existing_still_checks_nonzero_rows(self):
        row = {"f_968163": {"day_pnl": 10, "day_base": 46192.21}}
        repairs, _, history, _ = run_plan({"2026-11-17": row}, [
            {"date": "2026-11-16", "value": 9.9}, {"date": "2026-11-17", "value": 9.9},
        ], verify_existing=True)
        self.assertEqual(repairs[0][2].old_day_pnl, 10)
        history.assert_called_once()
