import os
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
KONA_TOOL = ROOT / "kona_tool"
if str(KONA_TOOL) not in sys.path:
    sys.path.insert(0, str(KONA_TOOL))
os.environ.setdefault("JWT_SECRET", "ci_test_jwt_secret")

import core.price as price
from unittest.mock import patch


class TestBatchCache(unittest.TestCase):
    def test_batch_skips_cached_codes(self):
        price.price_cache.clear()
        cached_code = 'ci_cached_code_001'
        miss_code = 'ci_missing_code_001'
        price.price_cache.set(cached_code, (10, 9, 0, 0))

        with patch('core.price.get_price', return_value=(5, 4, 1, 0)) as mock_get:
            res = price.batch_get_prices([cached_code, miss_code])
            called_args = [call.args for call in mock_get.call_args_list]

            self.assertEqual(called_args.count((miss_code, False)), 1)
            self.assertNotIn((cached_code, False), called_args)
            self.assertEqual(res[cached_code][0], 10)
            self.assertEqual(res[miss_code][0], 5)


if __name__ == '__main__':
    unittest.main()
