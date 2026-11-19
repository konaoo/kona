import unittest

from core.fund_nav_reconcile import nav_map_from_points, needs_nav_verification, plan_fund_nav_repair


class FundNavReconcileTest(unittest.TestCase):
    def test_zero_without_base_is_rechecked_regardless_of_source_label(self):
        self.assertTrue(needs_nav_verification(None))
        for source in ("backfill", "exact", "recalculated", "fund_nav_reconcile"):
            self.assertTrue(needs_nav_verification({"day_pnl": 0, "day_base": 0, "source": source}))
        for source in ("backfill", "exact", "recalculated"):
            self.assertTrue(needs_nav_verification({"day_pnl": 0, "day_base": 46192.21, "source": source}))
        self.assertFalse(needs_nav_verification({"day_pnl": 0, "day_base": 46192.21, "source": "fund_nav_reconcile"}))
        self.assertFalse(needs_nav_verification({"day_pnl": -93.32, "day_base": 46285.53}))

    def test_missing_target_nav_does_not_replace_zero_with_estimate(self):
        repair = plan_fund_nav_repair(
            date_str="2026-11-18", code="f_968163", name="摩根亚洲总收益", curr="CNY",
            qty=4665.88, nav_by_date={"2026-11-16": 9.9, "2026-11-17": 9.9}, fx_rate=1,
            existing={"day_pnl": 0, "day_base": 0},
        )
        self.assertIsNone(repair)

    def test_verified_flat_nav_keeps_zero_but_supplies_verification_base(self):
        repair = plan_fund_nav_repair(
            date_str="2026-11-17", code="f_968163", name="摩根亚洲总收益", curr="CNY",
            qty=4665.88, nav_by_date={"2026-11-16": 9.9, "2026-11-17": 9.9}, fx_rate=1,
            existing={"day_pnl": 0, "day_base": 0},
        )
        self.assertEqual(repair.day_pnl, 0)
        self.assertEqual(repair.day_base, 46192.21)

    def test_flat_nav_with_base_is_marked_verified_once(self):
        args = dict(
            date_str="2026-11-17", code="f_968163", name="摩根亚洲总收益", curr="CNY",
            qty=4665.88, nav_by_date={"2026-11-16": 9.9, "2026-11-17": 9.9}, fx_rate=1,
        )
        row = {"day_pnl": 0, "day_base": 46192.21, "source": "backfill"}
        self.assertIsNotNone(plan_fund_nav_repair(**args, existing=row))
        row["source"] = "fund_nav_reconcile"
        self.assertIsNone(plan_fund_nav_repair(**args, existing=row))

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
