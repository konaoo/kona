# -*- coding: utf-8 -*-
"""AI 聊天请求处理：鉴权 → 构建上下文 → 调 LLM → 生成 SSE 流。"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Callable, Dict, Optional

from flask import Response, g, jsonify, request, stream_with_context

import config
from ai_context_builder import build_user_context
from core.admin.runtime_config import load_user_group_ops_config
from core.request_trace import record_request_stage, trace_request_stage

logger = logging.getLogger(__name__)

AI_PROVIDERS_KEY = "ai_providers"
AI_OCR_PROVIDER_CONFIG_KEY = "ai_ocr_provider_config"

SYSTEM_PROMPT = """你是"小咔"，咔咔记账的 AI 投资助手。你能看到用户的完整投资组合数据。

规则：
- 用简洁中文回答，给出具体数字和百分比
- 可以分析趋势、风险、仓位集中度、盈亏比
- 可以指出值得关注的信号（如单只仓位过重、连续亏损、盈利回撤等）
- 不给出具体买卖建议（合规），用"值得关注""需注意风险"等表述
- 回答要有条理，适当使用 markdown 格式
- 如果用户问的问题跟投资无关，礼貌提示你是投资分析助手"""


def _build_ai_credits_required_payload(db: Any, user_id: str, *, balance: int | None = None) -> Dict[str, Any]:
    ops_config = load_user_group_ops_config(db)
    resolved_balance = balance if balance is not None else db.get_user_ai_credits_balance(user_id)
    return {
        "error": "当前没有可用积分，加入咔咔用户群获取积分",
        "code": "AI_CREDITS_REQUIRED",
        "ai_credits_balance": max(int(resolved_balance or 0), 0),
        "user_group_text": str(ops_config.get("text") or "").strip() or "加入咔咔用户群",
        "user_group_image_url": str(ops_config.get("image_url") or "").strip(),
    }


def _load_runtime_ai_providers(db: Any) -> list[dict[str, Any]]:
    raw = db.get_runtime_config(AI_PROVIDERS_KEY)
    if not raw:
        return []
    try:
        providers = json.loads(raw)
    except Exception as exc:
        logger.warning("Failed to load AI providers from runtime_configs: %s", exc)
        return []
    if not isinstance(providers, list):
        return []
    return [item for item in providers if isinstance(item, dict)]


def _build_env_provider() -> Optional[Dict[str, Any]]:
    env_key = str(getattr(config, "AI_API_KEY", "") or "").strip()
    if not env_key:
        env_key = str(os.getenv("OPENAI_API_KEY", "") or "").strip()
    env_base_url = str(getattr(config, "AI_BASE_URL", "") or "").strip()
    if not env_base_url:
        env_base_url = str(os.getenv("OPENAI_API_BASE", "") or "").strip()
    env_provider = str(getattr(config, "AI_PROVIDER", "") or "").strip()
    if not env_provider and env_key:
        env_provider = "openai"
    env_model = str(getattr(config, "AI_MODEL", "") or "").strip()
    if not env_model:
        env_model = str(os.getenv("OPENAI_MODEL", "") or "").strip()
    if not env_key:
        return None
    return {
        "id": "env_default",
        "type": env_provider or "openai",
        "api_key": env_key,
        "model": env_model,
        "base_url": env_base_url,
        "protocol": "anthropic" if (env_provider or "").lower() == "anthropic" else "openai",
        "active": True,
    }


def _find_provider_by_id(providers: list[dict[str, Any]], provider_id: str) -> Optional[dict[str, Any]]:
    target = str(provider_id or "").strip()
    if not target:
        return None
    for provider in providers:
        if str(provider.get("id") or "").strip() == target:
            return provider
    return None


def _load_ocr_provider_config(db: Any) -> Dict[str, str]:
    raw = db.get_runtime_config(AI_OCR_PROVIDER_CONFIG_KEY)
    if not raw:
        return {}
    try:
        payload = json.loads(raw)
    except Exception as exc:
        logger.warning("Failed to load OCR provider config from runtime_configs: %s", exc)
        return {}
    if not isinstance(payload, dict):
        return {}
    return {
        "provider_id": str(payload.get("provider_id") or "").strip(),
        "model": str(payload.get("model") or "").strip(),
    }


def _get_active_provider(db: Any) -> Optional[Dict[str, Any]]:
    """从 runtime_configs 读取激活的 AI 供应商，fallback 到环境变量。"""
    providers = _load_runtime_ai_providers(db)
    active = next((p for p in providers if p.get("active") and p.get("api_key")), None)
    if active:
        return dict(active)
    return _build_env_provider()


def _get_ocr_provider(db: Any) -> Optional[Dict[str, Any]]:
    providers = _load_runtime_ai_providers(db)
    ocr_cfg = _load_ocr_provider_config(db)
    provider_id = str(ocr_cfg.get("provider_id") or "").strip()
    model_override = str(ocr_cfg.get("model") or "").strip()

    selected = _find_provider_by_id(providers, provider_id) if provider_id else None
    if not selected:
        selected = next((p for p in providers if p.get("active") and p.get("api_key")), None)
    if selected and selected.get("api_key"):
        resolved = dict(selected)
        if model_override:
            resolved["model"] = model_override
        return resolved

    env_provider = _build_env_provider()
    if env_provider and model_override:
        env_provider["model"] = model_override
    return env_provider


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

        with trace_request_stage("ai.credits.precheck"):
            ai_credits_balance = db.get_user_ai_credits_balance(user_id)
        if ai_credits_balance <= 0:
            return jsonify(_build_ai_credits_required_payload(db, user_id, balance=ai_credits_balance)), 402

        # 读取激活的供应商配置
        provider_cfg = _get_active_provider(db)
        if not provider_cfg:
            return jsonify({"error": "AI 服务未配置，请联系管理员"}), 503

        # 最多保留最近 20 条（约 10 轮）
        trimmed = messages[-20:]

        # 构建用户数据上下文
        try:
            with trace_request_stage("ai.context.build"):
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
            provider_started_at = time.perf_counter()
            first_token_recorded = False
            credit_consumed = False
            request_id = str(getattr(g, "request_id", "") or "-").strip() or "-"
            try:
                if protocol == "anthropic":
                    stream_iter = _stream_anthropic(
                        system_prompt,
                        trimmed,
                        api_key,
                        model,
                        max_tokens,
                    )
                else:
                    stream_iter = _stream_openai_compatible(
                        system_prompt,
                        trimmed,
                        api_key,
                        model,
                        max_tokens,
                        base_url=base_url,
                        provider_type=provider_type,
                    )
                for chunk in stream_iter:
                    if not first_token_recorded:
                        first_token_ms = (time.perf_counter() - provider_started_at) * 1000.0
                        record_request_stage(
                            "ai.provider.first_token",
                            first_token_ms,
                            provider=provider_type,
                            model=model or "",
                            protocol=protocol,
                        )
                        logger.info(
                            "AI_CHAT_TRACE request_id=%s stage=provider.first_token elapsed_ms=%.3f provider=%s model=%s protocol=%s",
                            request_id,
                            first_token_ms,
                            provider_type,
                            model or "-",
                            protocol,
                        )
                        with trace_request_stage("ai.credits.consume"):
                            consume_result = db.adjust_user_ai_credits(
                                user_id=user_id,
                                delta=-1,
                                reason="AI 对话消费",
                                source="ai_chat",
                                request_id=request_id,
                            )
                        if not consume_result or not consume_result.get("ok"):
                            yield (
                                "data: "
                                f"{json.dumps(_build_ai_credits_required_payload(db, user_id, balance=0), ensure_ascii=False)}"
                                "\n\n"
                            )
                            return
                        credit_consumed = True
                        first_token_recorded = True
                    yield chunk
            except Exception as exc:
                logger.error("AI stream error: %s", exc)
                yield f"data: {json.dumps({'error': str(exc)})}\n\n"
            finally:
                total_ms = (time.perf_counter() - provider_started_at) * 1000.0
                record_request_stage(
                    "ai.provider.total",
                    total_ms,
                    provider=provider_type,
                    model=model or "",
                    protocol=protocol,
                    first_token=first_token_recorded,
                    credit_consumed=credit_consumed,
                )
                logger.info(
                    "AI_CHAT_TRACE request_id=%s stage=provider.total elapsed_ms=%.3f provider=%s model=%s protocol=%s first_token=%s credit_consumed=%s",
                    request_id,
                    total_ms,
                    provider_type,
                    model or "-",
                    protocol,
                    "yes" if first_token_recorded else "no",
                    "yes" if credit_consumed else "no",
                )
            yield f"data: {json.dumps({'done': True})}\n\n"

        return Response(
            stream_with_context(generate()),
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
