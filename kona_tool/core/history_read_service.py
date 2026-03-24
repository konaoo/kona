"""历史读侧服务。"""

from __future__ import annotations

from typing import Any, Dict, List

from .request_trace import trace_request_stage


class HistoryReadService:
    def __init__(self, *, db: Any) -> None:
        self.db = db

    def get_history(self, *, days: int, user_id: str | None) -> List[Dict]:
        with trace_request_stage("history.db", days=days):
            return self.db.get_history(days, user_id)
