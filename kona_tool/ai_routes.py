# -*- coding: utf-8 -*-
"""AI 聊天路由 Blueprint。"""

from __future__ import annotations

from flask import Blueprint
from core.auth import login_required


def create_ai_blueprint(
    *,
    limiter,
    ai_chat_handler,
):
    bp = Blueprint("ai_routes", __name__)

    @bp.route("/api/ai/chat", methods=["POST"])
    @limiter.limit("20/hour;5/minute")
    @login_required
    def ai_chat():
        """AI 聊天 SSE 流式端点。"""
        return ai_chat_handler()

    return bp
