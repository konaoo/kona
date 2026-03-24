"""市场快讯抓取与缓存模块。"""

from __future__ import annotations

import logging
import os
import re
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional

import requests

from .policy_runtime import is_policy_enabled

SINA_API_URL = "https://zhibo.sina.com.cn/api/zhibo/feed"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://finance.sina.com.cn/7x24/",
}

_HTML_RE = re.compile(r"<.*?>")
logger = logging.getLogger(__name__)


def _safe_int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        logger.warning("Invalid integer env %s=%s, fallback=%s", name, raw, default)
        return default


def _safe_float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        logger.warning("Invalid float env %s=%s, fallback=%s", name, raw, default)
        return default


class NewsFetcher:
    """带短周期热缓存的快讯抓取器。"""

    def __init__(self) -> None:
        self._cache: List[Dict] = []
        self._lock = threading.RLock()
        self._refreshing = False
        self._last_refresh_monotonic = 0.0

        self._refresh_interval_sec = max(
            0.8,
            _safe_float_env("NEWS_REFRESH_INTERVAL_SEC", 2.0),
        )
        self._cache_max_items = max(50, _safe_int_env("NEWS_CACHE_MAX_ITEMS", 200))
        self._upstream_page_size = max(50, _safe_int_env("NEWS_UPSTREAM_PAGE_SIZE", 80))

    def fetch_latest(self, page: int = 1, page_size: int = 30) -> List[Dict]:
        """返回缓存中的分页快讯（必要时刷新）。"""
        if not is_policy_enabled("upstream.news", default=True):
            logger.warning("News upstream disabled by admin policy")
            return []

        safe_page = max(1, int(page or 1))
        safe_page_size = max(1, min(200, int(page_size or 30)))
        self._refresh_if_needed()

        with self._lock:
            snapshot = list(self._cache)

        start = (safe_page - 1) * safe_page_size
        end = start + safe_page_size
        if start >= len(snapshot):
            return []
        return snapshot[start:end]

    def fetch_since(self, since_id: str, limit: int = 50) -> List[Dict]:
        """返回 since_id 之后的新快讯（不包含 since_id 本身）。"""
        if not is_policy_enabled("upstream.news", default=True):
            logger.warning("News upstream disabled by admin policy")
            return []

        safe_limit = max(1, min(200, int(limit or 50)))
        self._refresh_if_needed()

        with self._lock:
            snapshot = list(self._cache)

        marker = str(since_id or "").strip()
        if not marker:
            return snapshot[:safe_limit]

        result: List[Dict] = []
        for item in snapshot:
            item_id = str(item.get("id", "")).strip()
            if item_id and item_id == marker:
                break
            result.append(item)
            if len(result) >= safe_limit:
                break
        return result

    def latest_id(self) -> Optional[str]:
        """返回当前缓存中最新一条快讯 id。"""
        self._refresh_if_needed()
        with self._lock:
            if not self._cache:
                return None
            value = self._cache[0].get("id")
            if value is None:
                return None
            text = str(value).strip()
            return text or None

    def _refresh_if_needed(self, force: bool = False) -> None:
        now = time.monotonic()
        with self._lock:
            cache_ready = bool(self._cache)
            if (
                not force
                and cache_ready
                and (now - self._last_refresh_monotonic) < self._refresh_interval_sec
            ):
                return
            if self._refreshing:
                return
            self._refreshing = True

        try:
            latest = self._fetch_upstream_page(page=1, page_size=self._upstream_page_size)
            if latest:
                self._merge_cache(latest)
            with self._lock:
                self._last_refresh_monotonic = time.monotonic()
        except Exception:  # pragma: no cover - 日志兜底
            logger.exception("News cache refresh failed")
        finally:
            with self._lock:
                self._refreshing = False

    def _fetch_upstream_page(self, page: int, page_size: int) -> List[Dict]:
        params = {
            "page": page,
            "page_size": page_size,
            "zhibo_id": 152,
            "tag_id": 0,
            "dire": "f",
            "dpc": 1,
            "pagesize": page_size,
            "_": int(time.time() * 1000),
        }

        resp = requests.get(SINA_API_URL, headers=HEADERS, params=params, timeout=5)
        if resp.status_code != 200:
            logger.warning("Sina fetch failed status=%s", resp.status_code)
            return []

        payload = resp.json()
        feed = (
            payload.get("result", {})
            .get("data", {})
            .get("feed", {})
            .get("list", [])
        )
        if not isinstance(feed, list):
            logger.warning("Sina response structure changed: feed.list is not list")
            return []

        result: List[Dict] = []
        for item in feed:
            if not isinstance(item, dict):
                continue

            content = item.get("rich_text", "")
            if not content:
                continue
            content = self._clean_html(str(content))
            if not content:
                continue

            create_time = str(item.get("create_time", "") or "")
            date_text = create_time.split(" ")[0] if " " in create_time else ""
            time_text = (
                create_time.split(" ")[-1][:5]
                if " " in create_time
                else datetime.now().strftime("%H:%M")
            )

            important = False
            tags = item.get("tag")
            if isinstance(tags, list):
                for tag in tags:
                    if isinstance(tag, dict) and tag.get("name") in {"重磅", "突发", "焦点"}:
                        important = True
                        break
            if any(key in content for key in ("加息", "降息", "CPI", "GDP")):
                important = True

            result.append(
                {
                    "id": item.get("id"),
                    "time": time_text,
                    "date": date_text,
                    "content": content,
                    "important": important,
                }
            )

        return result

    def _merge_cache(self, latest: List[Dict]) -> None:
        with self._lock:
            merged: List[Dict] = []
            seen = set()

            for item in latest + self._cache:
                raw_id = item.get("id") if isinstance(item, dict) else None
                item_id = str(raw_id).strip() if raw_id is not None else ""
                if not item_id or item_id in seen:
                    continue
                seen.add(item_id)
                merged.append(item)
                if len(merged) >= self._cache_max_items:
                    break

            self._cache = merged

    @staticmethod
    def _clean_html(raw_html: str) -> str:
        return _HTML_RE.sub("", raw_html).strip()


news_fetcher = NewsFetcher()
