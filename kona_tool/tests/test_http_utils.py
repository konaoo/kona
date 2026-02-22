import os
import sys
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
KONA_TOOL = ROOT / "kona_tool"
if str(KONA_TOOL) not in sys.path:
    sys.path.insert(0, str(KONA_TOOL))
os.environ.setdefault("JWT_SECRET", "ci_test_jwt_secret")

from core.utils import http_get


class TestHttpGet(unittest.TestCase):
    @patch('core.utils.requests.get')
    def test_http_get_retries(self, mock_get):
        mock_get.side_effect = Exception('boom')
        with self.assertRaises(Exception):
            http_get('http://example.com', retries=2)
        target_calls = [
            call for call in mock_get.call_args_list
            if call.args and call.args[0] == 'http://example.com'
        ]
        self.assertEqual(len(target_calls), 2)


if __name__ == '__main__':
    unittest.main()
