import sys
from pathlib import Path
import unittest

from flask import Flask, g, jsonify

ROOT = Path(__file__).resolve().parents[2]
KONA_TOOL = ROOT / "kona_tool"
if str(KONA_TOOL) not in sys.path:
    sys.path.insert(0, str(KONA_TOOL))

from request_runtime import create_request_runtime  # noqa: E402


class _FakeDb:
    def __init__(self):
        self.users = {}
        self.last_active_calls = []
        self.admin_audit_calls = []

    def get_user_by_id(self, user_id):
        return self.users.get(user_id)

    def update_last_active(self, user_id, active_ip="", active_region=""):
        self.last_active_calls.append(
            {
                "user_id": user_id,
                "active_ip": active_ip,
                "active_region": active_region,
            }
        )

    def add_admin_audit_log(self, **kwargs):
        self.admin_audit_calls.append(kwargs)


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


class RequestRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.db = _FakeDb()
        self.logger = _FakeLogger()
        self.now = 1_700_000_000.0
        self.runtime = create_request_runtime(
            db=self.db,
            logger=self.logger,
            client_ip_getter=lambda: "10.8.0.1",
            resolve_ip_region=lambda ip: "广东-深圳" if ip else "",
            verify_token=lambda token: (True, {"user_id": "u_force"}),
            is_policy_enabled=lambda scope_key, default=True: True,
            get_policy_limit_per_min=lambda scope_key: 0,
            time_getter=lambda: self.now,
            activity_touch_interval_seconds=30.0,
        )

    def test_auth_audit_will_mask_username(self):
        with self.app.test_request_context("/api/auth/login", headers={"User-Agent": "UnitTest/1.0"}):
            self.runtime.auth_audit(
                event="auth_login",
                outcome="failed",
                username="konae",
                reason="bad_password",
            )

        self.assertEqual(len(self.logger.info_messages), 1)
        message = self.logger.info_messages[0]
        self.assertIn("username=ko***", message)
        self.assertIn("event=auth_login", message)
        self.assertIn("path=/api/auth/login", message)

    def test_enforce_api_group_policy_blocks_force_change_user(self):
        self.db.users["u_force"] = {
            "id": "u_force",
            "status": "active",
            "must_change_password": 1,
        }

        with self.app.test_request_context(
            "/api/portfolio",
            headers={"Authorization": "Bearer token_force"},
        ):
            response = self.runtime.enforce_api_group_policy()

        self.assertIsNotNone(response)
        flask_response, status_code = response
        self.assertEqual(status_code, 403)
        self.assertEqual(flask_response.get_json().get("code"), "PASSWORD_CHANGE_REQUIRED")

    def test_mark_user_recent_activity_is_throttled(self):
        with self.app.test_request_context("/api/portfolio"):
            g.user_id = "u_1"
            response = self.runtime.mark_user_recent_activity(self.app.response_class("ok"))
            self.assertEqual(response.status_code, 200)

        self.assertEqual(len(self.db.last_active_calls), 1)
        self.assertEqual(self.db.last_active_calls[0]["active_region"], "广东-深圳")

        with self.app.test_request_context("/api/portfolio"):
            g.user_id = "u_1"
            self.runtime.mark_user_recent_activity(self.app.response_class("ok"))

        self.assertEqual(len(self.db.last_active_calls), 1)

        self.now += 31.0
        with self.app.test_request_context("/api/portfolio"):
            g.user_id = "u_1"
            self.runtime.mark_user_recent_activity(self.app.response_class("ok"))

        self.assertEqual(len(self.db.last_active_calls), 2)

    def test_admin_write_audit_records_failed_response(self):
        @self.runtime.admin_write_audit(action="admin.users.update", target_type="user")
        def _handler():
            return jsonify({"error": "boom"}), 400

        with self.app.test_request_context(
            "/api/admin/users/update",
            method="POST",
            json={"user_id": "u_target"},
        ):
            g.user_id = "u_admin"
            response = _handler()

        self.assertEqual(response[1], 400)
        self.assertEqual(len(self.db.admin_audit_calls), 1)
        audit = self.db.admin_audit_calls[0]
        self.assertEqual(audit["admin_user_id"], "u_admin")
        self.assertEqual(audit["action"], "admin.users.update")
        self.assertEqual(audit["target_type"], "user")
        self.assertEqual(audit["target_id"], "u_target")
        self.assertEqual(audit["status_code"], 400)
        self.assertEqual(audit["result"], "failed")
        self.assertEqual(audit["error"], "boom")

    def test_request_trace_sets_response_header_and_logs_api_summary(self):
        self.runtime.register_hooks(self.app)

        @self.app.route("/api/ping")
        def _ping():
            g.user_id = "u_trace"
            return jsonify({"status": "ok"})

        client = self.app.test_client()
        resp = client.get("/api/ping", headers={"X-Request-Id": "trace-req-001"})

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get("X-Request-Id"), "trace-req-001")
        self.assertTrue(
            any(
                "REQUEST request_id=trace-req-001 method=GET path=/api/ping status=200" in message
                for message in self.logger.info_messages
            )
        )


if __name__ == "__main__":
    unittest.main()
