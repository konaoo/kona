# -*- coding: utf-8 -*-
"""
管理后台：AI 供应商配置路由。
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Dict, List

from flask import g, jsonify

from core.admin import common as admin_common
from core.auth import admin_required

logger = logging.getLogger(__name__)

AI_PROVIDERS_KEY = "ai_providers"
AI_OCR_PROVIDER_CONFIG_KEY = "ai_ocr_provider_config"

# 预置供应商类型定义
PROVIDER_PRESETS: Dict[str, Dict[str, str]] = {
    "deepseek": {
        "label": "DeepSeek",
        "default_base_url": "https://api.deepseek.com",
        "default_model": "deepseek-chat",
        "protocol": "openai",
    },
    "openai": {
        "label": "OpenAI",
        "default_base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o",
        "protocol": "openai",
    },
    "anthropic": {
        "label": "Anthropic Claude",
        "default_base_url": "https://api.anthropic.com",
        "default_model": "claude-sonnet-4-20250514",
        "protocol": "anthropic",
    },
    "gemini": {
        "label": "Google Gemini",
        "default_base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "default_model": "gemini-2.0-flash",
        "protocol": "openai",
    },
    "zhipu": {
        "label": "智谱 GLM",
        "default_base_url": "https://open.bigmodel.cn/api/paas/v4",
        "default_model": "glm-4-flash",
        "protocol": "openai",
    },
    "custom": {
        "label": "自定义供应商",
        "default_base_url": "",
        "default_model": "",
        "protocol": "openai",
    },
}


def _load_providers(db: Any) -> List[Dict[str, Any]]:
    raw = db.get_runtime_config(AI_PROVIDERS_KEY)
    if not raw:
        return []
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return []


def _save_providers(db: Any, providers: List[Dict[str, Any]], updater: str = "") -> None:
    db.set_runtime_config(AI_PROVIDERS_KEY, json.dumps(providers, ensure_ascii=False), updated_by=updater)


def _load_ocr_provider_config(db: Any) -> Dict[str, str]:
    raw = db.get_runtime_config(AI_OCR_PROVIDER_CONFIG_KEY)
    if not raw:
        return {}
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    return {
        "provider_id": str(payload.get("provider_id") or "").strip(),
        "model": str(payload.get("model") or "").strip(),
    }


def _save_ocr_provider_config(db: Any, config_payload: Dict[str, str], updater: str = "") -> None:
    db.set_runtime_config(
        AI_OCR_PROVIDER_CONFIG_KEY,
        json.dumps(config_payload, ensure_ascii=False),
        updated_by=updater,
    )


def _mask_key(api_key: str) -> str:
    """脱敏 API Key：保留末 4 位。"""
    key = str(api_key or "").strip()
    if len(key) <= 4:
        return "****"
    return "****" + key[-4:]


def _sanitize_provider(p: Dict[str, Any]) -> Dict[str, Any]:
    """返回给前端的脱敏供应商数据。"""
    return {
        "id": p.get("id", ""),
        "type": p.get("type", "custom"),
        "name": p.get("name", ""),
        "base_url": p.get("base_url", ""),
        "api_key_masked": _mask_key(p.get("api_key", "")),
        "model": p.get("model", ""),
        "active": p.get("active", False),
        "protocol": p.get("protocol", "openai"),
    }


def _sanitize_ocr_config(
    providers: List[Dict[str, Any]],
    ocr_config: Dict[str, str],
) -> Dict[str, Any]:
    provider_id = str(ocr_config.get("provider_id") or "").strip()
    model = str(ocr_config.get("model") or "").strip()
    provider = next((p for p in providers if str(p.get("id") or "").strip() == provider_id), None)
    provider_name = str(provider.get("name") or "").strip() if provider else ""
    inherited_model = str(provider.get("model") or "").strip() if provider else ""
    resolved_model = model or inherited_model
    return {
        "provider_id": provider_id,
        "provider_name": provider_name,
        "model": model,
        "resolved_model": resolved_model,
        "enabled": bool(provider_id and provider),
    }


def register_admin_ai_routes(bp, db, admin_write_audit) -> None:

    @bp.route("/ai/presets", methods=["GET"])
    @admin_required
    def admin_ai_presets():
        """返回预置供应商类型列表。"""
        return jsonify({"presets": PROVIDER_PRESETS})

    @bp.route("/ai/providers", methods=["GET"])
    @admin_required
    def admin_ai_providers():
        """返回已配置的供应商列表（api_key 脱敏）。"""
        providers = _load_providers(db)
        ocr_config = _load_ocr_provider_config(db)
        return jsonify({
            "providers": [_sanitize_provider(p) for p in providers],
            "ocr_config": _sanitize_ocr_config(providers, ocr_config),
        })

    @bp.route("/ai/providers/save", methods=["POST"])
    @admin_write_audit(action="admin.ai.provider.save", target_type="ai_provider")
    @admin_required
    def admin_ai_provider_save():
        """新增或更新供应商配置。"""
        data = admin_common.json_body()
        provider_id = str(data.get("id", "")).strip()
        provider_type = str(data.get("type", "custom")).strip()
        name = str(data.get("name", "")).strip()
        base_url = str(data.get("base_url", "")).strip()
        api_key = str(data.get("api_key", "")).strip()
        model = str(data.get("model", "")).strip()

        if not name:
            preset = PROVIDER_PRESETS.get(provider_type, {})
            name = preset.get("label", provider_type)

        if not api_key and not provider_id:
            return jsonify({"error": "API Key 不能为空"}), 400

        # 确定协议
        preset = PROVIDER_PRESETS.get(provider_type, {})
        protocol = preset.get("protocol", "openai")
        if not base_url:
            base_url = preset.get("default_base_url", "")
        if not model:
            model = preset.get("default_model", "")

        providers = _load_providers(db)
        updater = str(getattr(g, "user_id", "") or "")

        if provider_id:
            # 更新已有供应商
            found = False
            for p in providers:
                if p["id"] == provider_id:
                    p["type"] = provider_type
                    p["name"] = name
                    p["base_url"] = base_url
                    p["model"] = model
                    p["protocol"] = protocol
                    # 如果前端没改 key（传了空或脱敏值），保留原值
                    if api_key and not api_key.startswith("****"):
                        p["api_key"] = api_key
                    found = True
                    break
            if not found:
                return jsonify({"error": "供应商不存在"}), 404
        else:
            # 新增
            if not api_key:
                return jsonify({"error": "API Key 不能为空"}), 400
            new_provider = {
                "id": str(uuid.uuid4())[:8],
                "type": provider_type,
                "name": name,
                "base_url": base_url,
                "api_key": api_key,
                "model": model,
                "active": len(providers) == 0,  # 第一个自动激活
                "protocol": protocol,
            }
            providers.append(new_provider)

        _save_providers(db, providers, updater)
        return jsonify({
            "status": "ok",
            "providers": [_sanitize_provider(p) for p in providers],
        })

    @bp.route("/ai/providers/delete", methods=["POST"])
    @admin_write_audit(action="admin.ai.provider.delete", target_type="ai_provider")
    @admin_required
    def admin_ai_provider_delete():
        """删除供应商。"""
        data = admin_common.json_body()
        provider_id = str(data.get("id", "")).strip()
        if not provider_id:
            return jsonify({"error": "缺少供应商 ID"}), 400

        providers = _load_providers(db)
        updater = str(getattr(g, "user_id", "") or "")

        new_providers = [p for p in providers if p.get("id") != provider_id]
        if len(new_providers) == len(providers):
            return jsonify({"error": "供应商不存在"}), 404

        ocr_config = _load_ocr_provider_config(db)
        if str(ocr_config.get("provider_id") or "").strip() == provider_id:
            _save_ocr_provider_config(db, {"provider_id": "", "model": ""}, updater)

        _save_providers(db, new_providers, updater)
        return jsonify({
            "status": "ok",
            "providers": [_sanitize_provider(p) for p in new_providers],
        })

    @bp.route("/ai/providers/activate", methods=["POST"])
    @admin_write_audit(action="admin.ai.provider.activate", target_type="ai_provider")
    @admin_required
    def admin_ai_provider_activate():
        """设置激活的供应商。"""
        data = admin_common.json_body()
        provider_id = str(data.get("id", "")).strip()
        if not provider_id:
            return jsonify({"error": "缺少供应商 ID"}), 400

        providers = _load_providers(db)
        updater = str(getattr(g, "user_id", "") or "")

        found = False
        for p in providers:
            if p["id"] == provider_id:
                p["active"] = True
                found = True
            else:
                p["active"] = False

        if not found:
            return jsonify({"error": "供应商不存在"}), 404

        _save_providers(db, providers, updater)
        return jsonify({
            "status": "ok",
            "providers": [_sanitize_provider(p) for p in providers],
        })

    @bp.route("/ai/ocr/save", methods=["POST"])
    @admin_write_audit(action="admin.ai.ocr.save", target_type="ai_provider")
    @admin_required
    def admin_ai_ocr_save():
        """保存截图识别专用配置。"""
        data = admin_common.json_body()
        provider_id = str(data.get("provider_id", "")).strip()
        model = str(data.get("model", "")).strip()
        updater = str(getattr(g, "user_id", "") or "")

        providers = _load_providers(db)
        provider = next((p for p in providers if str(p.get("id") or "").strip() == provider_id), None)
        if provider_id and not provider:
            return jsonify({"error": "截图识别供应商不存在"}), 404

        payload = {
            "provider_id": provider_id,
            "model": model,
        }
        _save_ocr_provider_config(db, payload, updater)
        return jsonify({
            "status": "ok",
            "ocr_config": _sanitize_ocr_config(providers, payload),
        })

    @bp.route("/ai/providers/test", methods=["POST"])
    @admin_required
    def admin_ai_provider_test():
        """测试供应商连通性。"""
        data = admin_common.json_body()
        provider_type = str(data.get("type", "custom")).strip()
        base_url = str(data.get("base_url", "")).strip()
        api_key = str(data.get("api_key", "")).strip()
        model = str(data.get("model", "")).strip()
        provider_id = str(data.get("id", "")).strip()

        # 如果 api_key 是脱敏值，尝试从已保存的配置中读取真实 key
        if (not api_key or api_key.startswith("****")) and provider_id:
            providers = _load_providers(db)
            for p in providers:
                if p["id"] == provider_id:
                    api_key = p.get("api_key", "")
                    if not base_url:
                        base_url = p.get("base_url", "")
                    if not model:
                        model = p.get("model", "")
                    if not provider_type or provider_type == "custom":
                        provider_type = p.get("type", "custom")
                    break

        if not api_key:
            return jsonify({"error": "API Key 不能为空"}), 400

        preset = PROVIDER_PRESETS.get(provider_type, {})
        protocol = preset.get("protocol", "openai")
        if not base_url:
            base_url = preset.get("default_base_url", "")
        if not model:
            model = preset.get("default_model", "")

        try:
            if protocol == "anthropic":
                result = _test_anthropic(api_key, model)
            else:
                result = _test_openai_compatible(api_key, base_url, model)
            # 测试成功后顺便拉取模型列表
            try:
                models = _fetch_models(protocol, api_key, base_url)
                result["models"] = models
            except Exception as exc:
                logger.info("Model list fetch failed (non-fatal): %s", exc)
                result["models"] = []
            return jsonify({"status": "ok", **result})
        except Exception as exc:
            logger.warning("AI provider test failed: %s", exc)
            error_msg = str(exc)
            if "401" in error_msg or "Unauthorized" in error_msg or "authentication" in error_msg.lower():
                error_msg = "认证失败：API Key 无效"
            elif "404" in error_msg:
                error_msg = "接口地址错误或模型不存在"
            elif "Connection" in error_msg or "connect" in error_msg.lower():
                error_msg = "网络连接失败：无法访问 API 地址"
            return jsonify({"error": error_msg}), 400

    @bp.route("/ai/providers/models", methods=["POST"])
    @admin_required
    def admin_ai_provider_models():
        """获取供应商支持的模型列表。"""
        data = admin_common.json_body()
        provider_type = str(data.get("type", "custom")).strip()
        base_url = str(data.get("base_url", "")).strip()
        api_key = str(data.get("api_key", "")).strip()
        provider_id = str(data.get("id", "")).strip()

        # 如果 api_key 是脱敏值，从已保存的配置中读取
        if (not api_key or api_key.startswith("****")) and provider_id:
            providers = _load_providers(db)
            for p in providers:
                if p["id"] == provider_id:
                    api_key = p.get("api_key", "")
                    if not base_url:
                        base_url = p.get("base_url", "")
                    if not provider_type or provider_type == "custom":
                        provider_type = p.get("type", "custom")
                    break

        if not api_key:
            return jsonify({"error": "API Key 不能为空"}), 400

        preset = PROVIDER_PRESETS.get(provider_type, {})
        protocol = preset.get("protocol", "openai")
        if not base_url:
            base_url = preset.get("default_base_url", "")

        try:
            models = _fetch_models(protocol, api_key, base_url)
            return jsonify({"status": "ok", "models": models})
        except Exception as exc:
            logger.warning("Model list fetch failed: %s", exc)
            return jsonify({"error": f"获取模型列表失败：{exc}"}), 400


def _fetch_models(protocol: str, api_key: str, base_url: str) -> List[Dict[str, str]]:
    """获取供应商支持的模型列表。"""
    if protocol == "anthropic":
        return _fetch_anthropic_models(api_key)
    else:
        return _fetch_openai_models(api_key, base_url)


def _fetch_anthropic_models(api_key: str) -> List[Dict[str, str]]:
    """拉取 Anthropic 模型列表。"""
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    try:
        resp = client.models.list(limit=100)
        models = []
        for m in resp.data:
            models.append({"id": m.id, "name": getattr(m, "display_name", m.id)})
        # 按 id 排序
        models.sort(key=lambda x: x["id"])
        return models
    except Exception:
        # fallback: 返回已知模型
        return [
            {"id": "claude-opus-4-20250514", "name": "Claude Opus 4"},
            {"id": "claude-sonnet-4-20250514", "name": "Claude Sonnet 4"},
            {"id": "claude-haiku-4-20250414", "name": "Claude Haiku 4"},
            {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet"},
        ]


def _fetch_openai_models(api_key: str, base_url: str) -> List[Dict[str, str]]:
    """拉取 OpenAI 兼容接口的模型列表。"""
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url=base_url)
    resp = client.models.list()
    models = []
    for m in resp.data:
        models.append({"id": m.id, "name": m.id})
    models.sort(key=lambda x: x["id"])
    return models


def _test_anthropic(api_key: str, model: str) -> Dict[str, Any]:
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    resp = client.messages.create(
        model=model or "claude-sonnet-4-20250514",
        max_tokens=5,
        messages=[{"role": "user", "content": "hi"}],
    )
    return {"model": resp.model, "message": "连接成功"}


def _test_openai_compatible(api_key: str, base_url: str, model: str) -> Dict[str, Any]:
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url=base_url)
    resp = client.chat.completions.create(
        model=model or "gpt-4o",
        max_tokens=5,
        messages=[{"role": "user", "content": "hi"}],
    )
    return {"model": resp.model, "message": "连接成功"}
