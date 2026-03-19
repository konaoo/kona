# -*- coding: utf-8 -*-
"""AI 聊天请求处理：鉴权 → 构建上下文 → 调 LLM → 生成 SSE 流。"""

from __future__ import annotations

import json
import logging
from typing import Any, Callable, Dict, Optional

from flask import Response, g, jsonify, request

import config
from ai_context_builder import build_user_context

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是"小咔"，咔咔记账的 AI 投资助手。你能看到用户的完整投资组合数据。

规则：
- 用简洁中文回答，给出具体数字和百分比
- 可以分析趋势、风险、仓位集中度、盈亏比
- 可以指出值得关注的信号（如单只仓位过重、连续亏损、盈利回撤等）
- 不给出具体买卖建议（合规），用"值得关注""需注意风险"等表述
- 回答要有条理，适当使用 markdown 格式
- 如果用户问的问题跟投资无关，礼貌提示你是投资分析助手"""


def _get_active_provider(db: Any) -> Optional[Dict[str, Any]]:
    """从 runtime_configs 读取激活的 AI 供应商，fallback 到环境变量。"""
    try:
        raw = db.get_runtime_config("ai_providers")
        if raw:
            providers = json.loads(raw)
            active = next((p for p in providers if p.get("active")), None)
            if active and active.get("api_key"):
                return active
    except Exception as exc:
        logger.warning("Failed to load AI providers from runtime_configs: %s", exc)

    # fallback 到环境变量
    env_key = getattr(config, "AI_API_KEY", "")
    if env_key:
        return {
            "type": getattr(config, "AI_PROVIDER", "deepseek"),
            "api_key": env_key,
            "model": getattr(config, "AI_MODEL", ""),
            "base_url": "",
            "protocol": "anthropic" if getattr(config, "AI_PROVIDER", "") == "anthropic" else "openai",
        }
    return None


def create_ai_chat_handler(
    *,
    db: Any,
    portfolio_read_service: Any,
    rates_getter: Callable[[], Dict[str, float]],
    market_status_getter: Callable[..., Dict[str, Any]],
):
    """创建 AI 聊天 handler，返回可直接调用的函数。"""

    def handle_chat():
        user_id = g.user_id
        if not user_id:
            return jsonify({"error": "请先登录"}), 401

        data = request.json
        if not data or not isinstance(data.get("messages"), list):
            return jsonify({"error": "messages 字段缺失或格式错误"}), 400

        messages = data["messages"]
        if not messages:
            return jsonify({"error": "消息列表不能为空"}), 400

        # 读取激活的供应商配置
        provider_cfg = _get_active_provider(db)
        if not provider_cfg:
            return jsonify({"error": "AI 服务未配置，请联系管理员"}), 503

        # 最多保留最近 20 条（约 10 轮）
        trimmed = messages[-20:]

        # 构建用户数据上下文
        try:
            context = build_user_context(
                user_id=user_id,
                db=db,
                portfolio_read_service=portfolio_read_service,
                rates_getter=rates_getter,
                market_status_getter=market_status_getter,
            )
        except Exception as exc:
            logger.error("ai_context build failed: %s", exc)
            context = "（用户数据加载失败，请基于对话内容回答）"

        system_prompt = SYSTEM_PROMPT + "\n\n# 用户投资数据\n\n" + context

        api_key = provider_cfg["api_key"]
        model = provider_cfg.get("model", "")
        base_url = provider_cfg.get("base_url", "")
        protocol = provider_cfg.get("protocol", "openai")
        provider_type = provider_cfg.get("type", "deepseek")
        max_tokens = getattr(config, "AI_MAX_TOKENS", 2000)

        def generate():
            try:
                if protocol == "anthropic":
                    yield from _stream_anthropic(system_prompt, trimmed, api_key, model, max_tokens)
                else:
                    yield from _stream_openai_compatible(
                        system_prompt, trimmed, api_key, model, max_tokens,
                        base_url=base_url, provider_type=provider_type,
                    )
            except Exception as exc:
                logger.error("AI stream error: %s", exc)
                yield f"data: {json.dumps({'error': str(exc)})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"

        return Response(
            generate(),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
            },
        )

    return handle_chat


def _stream_anthropic(system_prompt, messages, api_key, model, max_tokens):
    """Anthropic Claude 流式输出。"""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    with client.messages.stream(
        model=model or "claude-sonnet-4-20250514",
        max_tokens=max_tokens,
        system=system_prompt,
        messages=messages,
    ) as stream:
        for text in stream.text_stream:
            yield f"data: {json.dumps({'delta': text})}\n\n"


def _stream_openai_compatible(system_prompt, messages, api_key, model, max_tokens, *, base_url="", provider_type=""):
    """OpenAI 兼容接口流式输出（DeepSeek / OpenAI / Gemini / 智谱等）。"""
    from openai import OpenAI

    # 确定 base_url
    if not base_url:
        from admin_routes_ai import PROVIDER_PRESETS
        preset = PROVIDER_PRESETS.get(provider_type, {})
        base_url = preset.get("default_base_url", f"https://api.{provider_type}.com")

    client = OpenAI(api_key=api_key, base_url=base_url)
    stream = client.chat.completions.create(
        model=model or "deepseek-chat",
        max_tokens=max_tokens,
        messages=[{"role": "system", "content": system_prompt}] + messages,
        stream=True,
    )
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            delta = chunk.choices[0].delta.content
            yield f"data: {json.dumps({'delta': delta})}\n\n"
