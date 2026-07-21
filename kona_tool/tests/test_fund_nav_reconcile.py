import unittest

from core.fund_nav_reconcile import nav_map_from_points, plan_fund_nav_repair


class FundNavReconcileTest(unittest.TestCase):
    def test_missing_fund_row_is_backfilled_from_confirmed_navs(self):
        navs = nav_map_from_points([
            {"date": "2026-07-16", "value": 1.385},
            {"date": "2026-07-17", "value": 1.384},
        ])
        repair = plan_fund_nav_repair(
            date_str="2026-07-17", code="f_110018", name="易方达增强回报B", curr="CNY",
            qty=422539.27, nav_by_date=navs, fx_rate=1.0, existing=None,
        )
        self.assertIsNotNone(repair)
        self.assertEqual(repair.day_pnl, -422.54)
        self.assertEqual(repair.day_base, 585216.89)


    def test_same_confirmed_result_is_not_rewritten(self):
        navs = {"2026-07-16": 1.385, "2026-07-17": 1.384}
        repair = plan_fund_nav_repair(
            date_str="2026-07-17", code="f_110018", name="易方达增强回报B", curr="CNY",
            qty=422539.27, nav_by_date=navs, fx_rate=1.0,
            existing={"day_pnl": -422.54, "day_base": 585216.89},
        )
        self.assertIsNone(repair)


    def test_confirmed_zero_change_is_saved_when_asset_row_is_missing(self):
        navs = {"2026-07-16": 1.384, "2026-07-17": 1.384}
        repair = plan_fund_nav_repair(
            date_str="2026-07-17", code="f_110018", name="易方达增强回报B", curr="CNY",
            qty=100, nav_by_date=navs, fx_rate=1.0, existing=None,
        )
        self.assertIsNotNone(repair)
        self.assertEqual(repair.day_pnl, 0)
