import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "kona_tool" / "scripts" / "check_price_health_alert.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("check_price_health_alert", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class PriceHealthAlertScriptTests(unittest.TestCase):
    def test_script_exists(self):
        self.assertTrue(
            SCRIPT_PATH.exists(),
            f"missing script: {SCRIPT_PATH}",
        )

    def test_network_fail_and_stale_hits_delta_alert(self):
        module = _load_module()
        current = {
            "runtime": {
                "network_fail": 130,
                "stale_hits": 80,
            },
            "sources": {},
        }
        previous = {
            "runtime": {
                "network_fail": 100,
                "stale_hits": 40,
            }
        }
        alerts = module.build_alert_messages(current, previous)
        merged = "\n".join(alerts)
        self.assertIn("network_fail", merged)
        self.assertIn("stale_hits", merged)

    def test_source_consecutive_fail_or_circuit_open_alert(self):
        module = _load_module()
        current = {
            "runtime": {
                "network_fail": 0,
                "stale_hits": 0,
            },
            "sources": {
                "sina_stock": {
                    "consecutive_fail": 5,
                    "circuit_open": False,
                },
                "eastmoney_fund": {
                    "consecutive_fail": 2,
                    "circuit_open": True,
                },
            },
        }
        previous = {
            "runtime": {
                "network_fail": 0,
                "stale_hits": 0,
            }
        }
        alerts = module.build_alert_messages(current, previous)
        merged = "\n".join(alerts)
        self.assertIn("sina_stock", merged)
        self.assertIn("eastmoney_fund", merged)
        self.assertIn("consecutive_fail", merged)
        self.assertIn("circuit_open", merged)

    def test_no_alert_when_below_threshold(self):
        module = _load_module()
        current = {
            "runtime": {
                "network_fail": 10,
                "stale_hits": 20,
            },
            "sources": {
                "sina_stock": {
                    "consecutive_fail": 1,
                    "circuit_open": False,
                }
            },
        }
        previous = {
            "runtime": {
                "network_fail": 0,
                "stale_hits": 0,
            }
        }
        alerts = module.build_alert_messages(current, previous)
        self.assertEqual(alerts, [])


if __name__ == "__main__":
    unittest.main()
