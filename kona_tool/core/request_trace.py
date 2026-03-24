"""请求级链路追踪辅助。

这一层只做两件事：
- 让服务层可以按阶段记录耗时
- 避免服务层直接依赖具体 logger 或 response 细节
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Any, Dict, Iterator, List

from flask import g, has_request_context


def _coerce_meta_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (int, float, bool)):
        return value
    text = str(value).strip()
    if not text:
        return None
    return text[:120]


def record_request_stage(stage: str, elapsed_ms: float, **meta: Any) -> Dict[str, Any] | None:
    """在当前请求上下文里记录一个阶段耗时。"""
    if not has_request_context():
        return None

    normalized_stage = str(stage or "").strip()
    if not normalized_stage:
        return None

    payload: Dict[str, Any] = {
        "stage": normalized_stage[:80],
        "elapsed_ms": round(max(float(elapsed_ms or 0.0), 0.0), 3),
    }
    for key, value in meta.items():
        normalized = _coerce_meta_value(value)
        if normalized is not None:
            payload[str(key)] = normalized

    stages = getattr(g, "request_trace_stages", None)
    if stages is None:
        stages = []
        g.request_trace_stages = stages
    stages.append(payload)
    return payload


def get_request_stages() -> List[Dict[str, Any]]:
    if not has_request_context():
        return []
    stages = getattr(g, "request_trace_stages", None) or []
    return [dict(item) for item in stages]


@contextmanager
def trace_request_stage(stage: str, **meta: Any) -> Iterator[None]:
    """用 `with` 包住一个阶段，自动记录耗时。"""
    started_at = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = (time.perf_counter() - started_at) * 1000.0
        record_request_stage(stage, elapsed_ms, **meta)
