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

from core.ip_region import (
    is_normalized_region,
    normalize_region_parts,
    normalize_region_text,
    resolve_ip_region,
)


class IpRegionTests(unittest.TestCase):
    def setUp(self):
        resolve_ip_region.cache_clear()

    def test_normalize_region_parts_to_sheng_shi(self):
        self.assertEqual(normalize_region_parts("广东省", "深圳市"), "广东-深圳")
        self.assertEqual(normalize_region_parts("湖北", "武汉市"), "湖北-武汉")

    def test_normalize_region_text_filters_non_chinese(self):
        self.assertEqual(normalize_region_text("Guangdong Province-Shenzhen"), "")
        self.assertEqual(normalize_region_text("Hubei-Wu Han Shi"), "")
        self.assertEqual(normalize_region_text("湖北省-武汉市"), "湖北-武汉")

    def test_is_normalized_region(self):
        self.assertTrue(is_normalized_region("广东-深圳"))
        self.assertTrue(is_normalized_region("北京"))
        self.assertFalse(is_normalized_region("Guangdong-Shenzhen"))
        self.assertFalse(is_normalized_region("湖北-"))

    @patch("core.ip_region._resolve_from_ipwho")
    @patch("core.ip_region._resolve_from_ip_api")
    def test_resolve_ip_region_prefers_ip_api(self, mock_api, mock_ipwho):
        mock_api.return_value = "广东-深圳"
        mock_ipwho.return_value = "湖北-武汉"
        self.assertEqual(resolve_ip_region("1.2.3.4"), "广东-深圳")
        mock_api.assert_called_once()
        mock_ipwho.assert_not_called()

    @patch("core.ip_region._resolve_from_ipwho")
    @patch("core.ip_region._resolve_from_ip_api")
    def test_resolve_ip_region_fallback_to_ipwho(self, mock_api, mock_ipwho):
        mock_api.return_value = ""
        mock_ipwho.return_value = "浙江-杭州"
        self.assertEqual(resolve_ip_region("8.8.8.8"), "浙江-杭州")
        mock_api.assert_called_once()
        mock_ipwho.assert_called_once()

    @patch("core.ip_region._resolve_from_ip_api")
    def test_resolve_private_ip_returns_empty(self, mock_api):
        self.assertEqual(resolve_ip_region("192.168.1.8"), "")
        mock_api.assert_not_called()


if __name__ == "__main__":
    unittest.main()
