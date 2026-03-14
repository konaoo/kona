import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
KONA_TOOL = ROOT / "kona_tool"
if str(KONA_TOOL) not in sys.path:
    sys.path.insert(0, str(KONA_TOOL))

from startup_runtime import create_startup_runtime  # noqa: E402


class _FakeLogger:
    def __init__(self):
        self.info_messages = []

    def info(self, message, *args):
        self.info_messages.append(message % args if args else message)


class _FakeThread:
    def __init__(self, target=None, daemon=None):
        self.target = target
        self.daemon = daemon
        self.started = False

    def start(self):
        self.started = True


class _FakePreloader:
    def __init__(self):
        self.started = False

    def start(self):
        self.started = True


class StartupRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.logger = _FakeLogger()
        self.created_threads = []

        def _thread_factory(target=None, daemon=None):
            thread = _FakeThread(target=target, daemon=daemon)
            self.created_threads.append(thread)
            return thread

        self.opened_urls = []
        self.slept = []
        self.runtime = create_startup_runtime(
            logger=self.logger,
            thread_factory=_thread_factory,
            sleep_func=lambda seconds: self.slept.append(seconds),
            browser_open_func=lambda url: self.opened_urls.append(url),
        )

    def test_metrics_token_ok_supports_direct_header_and_bearer(self):
        self.assertTrue(
            self.runtime.metrics_token_ok(
                "secret",
                {"X-Kona-Metrics-Token": "secret"},
            )
        )
        self.assertTrue(
            self.runtime.metrics_token_ok(
                "secret",
                {"Authorization": "Bearer secret"},
            )
        )
        self.assertFalse(self.runtime.metrics_token_ok("secret", {}))

    def test_open_browser_waits_then_opens_url(self):
        self.runtime.open_browser("http://127.0.0.1:52345")
        self.assertEqual(self.slept, [1.5])
        self.assertEqual(self.opened_urls, ["http://127.0.0.1:52345"])

    def test_launch_runtime_services_starts_expected_threads_and_preloader(self):
        created_preloaders = []

        def _preloader_factory(db_path, interval):
            self.assertEqual(db_path, "/tmp/test.db")
            self.assertEqual(interval, 30)
            preloader = _FakePreloader()
            created_preloaders.append(preloader)
            return preloader

        scheduler_calls = []
        snapshot_calls = []
        browser_calls = []
        preloader = self.runtime.launch_runtime_services(
            enable_background_scheduler=True,
            background_scheduler_target=lambda: scheduler_calls.append("scheduler"),
            enable_startup_snapshot=True,
            startup_snapshot_target=lambda: snapshot_calls.append("snapshot"),
            preloader_factory=_preloader_factory,
            db_path="/tmp/test.db",
            preload_interval=30,
            open_browser_target=lambda: browser_calls.append("browser"),
        )

        self.assertEqual(len(self.created_threads), 3)
        self.assertTrue(all(thread.started for thread in self.created_threads))
        self.assertTrue(created_preloaders[0].started)
        self.assertIs(preloader, created_preloaders[0])

    def test_launch_runtime_services_logs_when_scheduler_disabled(self):
        self.runtime.launch_runtime_services(
            enable_background_scheduler=False,
            background_scheduler_target=lambda: None,
            enable_startup_snapshot=False,
            startup_snapshot_target=lambda: None,
            preloader_factory=lambda db_path, interval: _FakePreloader(),
            db_path="/tmp/test.db",
            preload_interval=10,
            open_browser_target=lambda: None,
        )
        self.assertTrue(any("Background scheduler disabled." in message for message in self.logger.info_messages))


if __name__ == "__main__":
    unittest.main()
