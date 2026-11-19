"""海外源退避、恢复探测及请求统计回归。"""
import unittest
from unittest.mock import Mock, patch

from requests.exceptions import Timeout

from core.source_health import SourceHealth
from core.utils import monitored_http_get


class SourceHealthBackoffTests(unittest.TestCase):
    def test_overseas_failures_back_off_and_allow_one_probe_per_worker(self):
        health = SourceHealth(fail_threshold=2, cooldown_seconds=10)
        with patch("core.source_health.time.time", return_value=1000):
            health.record("stooq_us_history", False, timeout=True)
            self.assertTrue(health.can_attempt("stooq_us_history"))
            health.record("stooq_us_history", False, timeout=True)
            self.assertFalse(health.can_attempt("stooq_us_history"))
            self.assertEqual(health.snapshot()["stooq_us_history"]["circuit_open_until"], 1300)
        with patch("core.source_health.time.time", return_value=1300):
            self.assertTrue(health.can_attempt("stooq_us_history"))
            self.assertFalse(health.can_attempt("stooq_us_history"))
            health.record("stooq_us_history", False)
            self.assertEqual(health.snapshot()["stooq_us_history"]["circuit_open_until"], 1900)
        with patch("core.source_health.time.time", return_value=1900):
            self.assertTrue(health.can_attempt("stooq_us_history"))
            health.record("stooq_us_history", True)
            self.assertTrue(health.can_attempt("stooq_us_history"))
            self.assertEqual(health.snapshot()["stooq_us_history"]["circuit_trips"], 0)


    def test_blocked_overseas_source_cools_immediately(self):
        for status in (403, 429):
            with self.subTest(status=status):
                health = SourceHealth()
                with patch("core.source_health.time.time", return_value=1000):
                    health.record("fidelity_fund_history", False, status_code=status, retry_after_seconds=1800)
                    self.assertFalse(health.can_attempt("fidelity_fund_history"))
                    self.assertEqual(health.snapshot()["fidelity_fund_history"]["circuit_open_until"], 2800)
                    # 其他可用备源不受影响。
                    self.assertTrue(health.can_attempt("overseas_fund_history"))


    def test_domestic_source_retains_existing_policy(self):
        health = SourceHealth(fail_threshold=2, cooldown_seconds=10)
        with patch("core.source_health.time.time", return_value=1000):
            health.record("tencent_stock", False, status_code=403)
            self.assertTrue(health.can_attempt("tencent_stock"))
            health.record("tencent_stock", False)
            self.assertEqual(health.snapshot()["tencent_stock"]["circuit_open_until"], 1010)


    def test_abandoned_probe_lease_expires_and_backoff_is_bounded(self):
        health = SourceHealth(fail_threshold=1)
        with patch("core.source_health.time.time", return_value=1000):
            for _ in range(30):
                health.record("morningstar_fund_history", False)
            self.assertEqual(health.snapshot()["morningstar_fund_history"]["circuit_open_until"], 4600)
        with patch("core.source_health.time.time", return_value=4600):
            self.assertTrue(health.can_attempt("morningstar_fund_history"))
            self.assertFalse(health.can_attempt("morningstar_fund_history"))
        with patch("core.source_health.time.time", return_value=4700):
            self.assertTrue(health.can_attempt("morningstar_fund_history"))


    def test_monitored_http_skips_network_and_recovers(self):
        health = SourceHealth(fail_threshold=1)
        response = Mock(status_code=429, headers={"Retry-After": "1800"})
        with patch("core.utils.source_health", health), patch("core.utils.requests.get", return_value=response) as get:
            monitored_http_get("yahoo_us_history", "https://example.test")
            with self.assertRaisesRegex(RuntimeError, "circuit open"):
                monitored_http_get("yahoo_us_history", "https://example.test")
            self.assertEqual(get.call_count, 1)
            snap = health.snapshot()["yahoo_us_history"]
            self.assertEqual(snap["last_status_code"], 429)
            self.assertEqual(snap["fail"], 1)
            self.assertEqual(snap["skipped"], 1)


    def test_timeout_still_records_and_raises(self):
        health = SourceHealth(fail_threshold=1)
        with patch("core.utils.source_health", health), patch("core.utils.requests.get", side_effect=Timeout("timeout")):
            with self.assertRaises(Timeout):
                monitored_http_get("stooq_us_history", "https://example.test")
        self.assertEqual(health.snapshot()["stooq_us_history"]["timeout"], 1)
