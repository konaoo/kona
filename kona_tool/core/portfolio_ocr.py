"""截图识别添加资产：图片 -> 候选资产结构。

第一版约束：
- 只服务“添加资产”入口
- 只返回候选结果，不直接写库
- 优先复用现有 AI 提供方，不在这里额外引入 OCR 依赖
"""

from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List

from ai_handlers import _get_ocr_provider


_SUPPORTED_IMAGE_TYPES = {
    "image/jpeg": "image/jpeg",
    "image/jpg": "image/jpeg",
    "image/png": "image/png",
    "image/webp": "image/webp",
}
_MAX_UPLOAD_BYTES = 4 * 1024 * 1024


class PortfolioOcrError(RuntimeError):
    def __init__(self, message: str, *, code: str, status_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


@dataclass(frozen=True)
class PortfolioOcrParseResult:
    items: List[Dict[str, Any]]
    warnings: List[str]
    raw_text: str


def parse_portfolio_asset_candidates(
    *,
    db: Any,
    image_bytes: bytes,
    filename: str = "",
    content_type: str = "",
) -> PortfolioOcrParseResult:
    media_type = _normalize_media_type(filename=filename, content_type=content_type)
    if len(image_bytes) <= 0:
        raise PortfolioOcrError("图片内容为空", code="OCR_EMPTY_FILE", status_code=400)
    if len(image_bytes) > _MAX_UPLOAD_BYTES:
        raise PortfolioOcrError(
            "图片过大，请控制在 4MB 以内",
            code="OCR_FILE_TOO_LARGE",
            status_code=400,
        )

    provider = _get_ocr_provider(db)
    if not provider:
        raise PortfolioOcrError(
            "AI 服务未配置，暂时无法识别截图",
            code="OCR_PROVIDER_NOT_CONFIGURED",
            status_code=503,
        )

    protocol = str(provider.get("protocol") or "openai").strip().lower()
    api_key = str(provider.get("api_key") or "").strip()
    model = str(provider.get("model") or "").strip()
    base_url = str(provider.get("base_url") or "").strip()
    provider_type = str(provider.get("type") or "").strip().lower()
    if not api_key:
        raise PortfolioOcrError(
            "AI 服务未配置有效密钥，暂时无法识别截图",
            code="OCR_PROVIDER_NOT_CONFIGURED",
            status_code=503,
        )

    image_b64 = base64.b64encode(image_bytes).decode("ascii")
    prompt = _build_ocr_prompt()
    try:
        if protocol == "anthropic":
            raw_text = _run_anthropic_vision(
                prompt=prompt,
                image_b64=image_b64,
                media_type=media_type,
                api_key=api_key,
                model=model,
            )
        else:
            raw_text = _run_openai_compatible_vision(
                prompt=prompt,
                image_b64=image_b64,
                media_type=media_type,
                api_key=api_key,
                model=model,
                base_url=base_url,
                provider_type=provider_type,
            )
    except PortfolioOcrError:
        raise
    except Exception as exc:
        lower = str(exc).lower()
        if "vision" in lower or "image" in lower or "multimodal" in lower:
            raise PortfolioOcrError(
                "当前 AI 模型不支持截图识别，请切到支持图片的模型后再试",
                code="OCR_MODEL_NOT_SUPPORTED",
                status_code=502,
            ) from exc
        raise PortfolioOcrError(
            f"截图识别失败：{exc}",
            code="OCR_PARSE_FAILED",
            status_code=502,
        ) from exc

    payload = _parse_response_json(raw_text)
    items = _normalize_items(payload.get("items"))
    warnings = _normalize_warnings(payload.get("warnings"))
    return PortfolioOcrParseResult(items=items, warnings=warnings, raw_text=raw_text)


def build_local_demo_result() -> PortfolioOcrParseResult:
    return PortfolioOcrParseResult(
        items=[
            {
                "name": "腾讯控股",
                "code": "hk00700",
                "qty": 200.0,
                "price": 318.4,
                "curr": "HKD",
                "asset_type": "hk",
                "confidence": 0.66,
                "note": "本地演示候选，用来验收交互链路",
            },
            {
                "name": "苹果",
                "code": "gb_aapl",
                "qty": 15.0,
                "price": 182.0,
                "curr": "USD",
                "asset_type": "us",
                "confidence": 0.58,
                "note": "本地演示候选，用来验收交互链路",
            },
            {
                "name": "易方达增强回报债券A",
                "code": "f_110017",
                "qty": 10000.0,
                "price": 1.053,
                "curr": "CNY",
                "asset_type": "fund",
                "confidence": 0.61,
                "note": "本地演示候选，用来验收交互链路",
            },
        ],
        warnings=[
            "当前是本地演示结果，不代表截图真实识别内容",
            "等本地 AI 配置恢复后，会自动切回真实识别",
        ],
        raw_text='{"mode":"local_demo"}',
    )


def _normalize_media_type(*, filename: str, content_type: str) -> str:
    normalized = str(content_type or "").strip().lower()
    if normalized in _SUPPORTED_IMAGE_TYPES:
        return _SUPPORTED_IMAGE_TYPES[normalized]
    lower_name = str(filename or "").strip().lower()
    if lower_name.endswith(".png"):
        return "image/png"
    if lower_name.endswith(".webp"):
        return "image/webp"
    if lower_name.endswith(".jpg") or lower_name.endswith(".jpeg"):
        return "image/jpeg"
    raise PortfolioOcrError(
        "仅支持 png、jpg、jpeg、webp 图片",
        code="OCR_UNSUPPORTED_FILE_TYPE",
        status_code=400,
    )


def _build_ocr_prompt() -> str:
    return (
        "你是投资记账产品里的截图识别助手。"
        "当前任务只服务“添加资产”入口，不是导入交易历史。"
        "请从用户上传的持仓截图里提取可直接用于“新增资产表单”的候选资产。"
        "不要臆造完整交易记录，不要输出解释性文字。"
        "\n\n"
        "严格返回一个 JSON 对象，不要加 markdown 代码块。格式如下：\n"
        "{\n"
        '  "items": [\n'
        "    {\n"
        '      "name": "资产名称",\n'
        '      "code": "标准化或接近标准化的代码",\n'
        '      "qty": 123.45,\n'
        '      "price": 12.34,\n'
        '      "curr": "CNY/HKD/USD 之一，判断不出就给空字符串",\n'
        '      "asset_type": "a/hk/us/fund 之一，判断不出就给空字符串",\n'
        '      "confidence": 0.0,\n'
        '      "note": "最多一句提醒"\n'
        "    }\n"
        "  ],\n"
        '  "warnings": ["如果截图模糊或字段不确定，在这里给简短提醒"]\n'
        "}\n\n"
        "要求：\n"
        "1. 最多返回 5 条候选资产。\n"
        "2. 如果同一张图里有多条资产，按你最有把握的顺序返回。\n"
        "3. 如果代码能明显识别，尽量给出标准代码，如：sh600519、hk00700、gb_aapl、f_110017。\n"
        "4. 如果数量或成本价看不清，就填 null，不要瞎猜。\n"
        "5. confidence 取 0 到 1 之间的小数。\n"
        "6. 只返回 JSON。"
    )


def _run_anthropic_vision(
    *,
    prompt: str,
    image_b64: str,
    media_type: str,
    api_key: str,
    model: str,
) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    resp = client.messages.create(
        model=model or "claude-sonnet-4-20250514",
        max_tokens=1200,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_b64,
                        },
                    },
                ],
            }
        ],
    )
    chunks: List[str] = []
    for item in getattr(resp, "content", []) or []:
        text = getattr(item, "text", None)
        if text:
            chunks.append(text)
    return "\n".join(chunks).strip()


def _run_openai_compatible_vision(
    *,
    prompt: str,
    image_b64: str,
    media_type: str,
    api_key: str,
    model: str,
    base_url: str,
    provider_type: str,
) -> str:
    from openai import OpenAI
    from admin_routes_ai import PROVIDER_PRESETS

    resolved_base_url = base_url
    if not resolved_base_url:
        preset = PROVIDER_PRESETS.get(provider_type, {})
        resolved_base_url = str(preset.get("default_base_url") or "").strip()

    client = OpenAI(api_key=api_key, base_url=resolved_base_url or None)
    resp = client.chat.completions.create(
        model=model or "gpt-4.1-mini",
        max_tokens=1200,
        temperature=0.1,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media_type};base64,{image_b64}",
                        },
                    },
                ],
            }
        ],
    )
    text = (((resp.choices or [None])[0]).message.content if (resp.choices or [None])[0] else "") or ""
    if isinstance(text, list):
        parts = []
        for item in text:
            if isinstance(item, dict):
                value = item.get("text")
                if value:
                    parts.append(str(value))
        return "\n".join(parts).strip()
    return str(text).strip()


def _parse_response_json(raw_text: str) -> Dict[str, Any]:
    text = str(raw_text or "").strip()
    if not text:
        raise PortfolioOcrError(
            "截图识别结果为空",
            code="OCR_EMPTY_RESPONSE",
            status_code=502,
        )
    candidate = text
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, flags=re.S)
    if fenced:
        candidate = fenced.group(1)
    else:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            candidate = text[start : end + 1]
    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise PortfolioOcrError(
            "截图识别结果格式不对，暂时无法解析",
            code="OCR_INVALID_JSON",
            status_code=502,
        ) from exc
    if not isinstance(payload, dict):
        raise PortfolioOcrError(
            "截图识别结果格式不对，暂时无法解析",
            code="OCR_INVALID_JSON",
            status_code=502,
        )
    return payload


def _normalize_items(raw_items: Any) -> List[Dict[str, Any]]:
    if not isinstance(raw_items, list):
        return []
    items: List[Dict[str, Any]] = []
    for raw in raw_items[:5]:
        if not isinstance(raw, dict):
            continue
        name = str(raw.get("name") or "").strip()
        code = str(raw.get("code") or "").strip()
        if not name and not code:
            continue
        qty = _coerce_number(raw.get("qty"))
        price = _coerce_number(raw.get("price"))
        confidence = _coerce_confidence(raw.get("confidence"))
        items.append(
            {
                "name": name,
                "code": code,
                "qty": qty,
                "price": price,
                "curr": str(raw.get("curr") or "").strip().upper(),
                "asset_type": str(raw.get("asset_type") or "").strip().lower(),
                "confidence": confidence,
                "note": str(raw.get("note") or "").strip(),
            }
        )
    return items


def _normalize_warnings(raw_warnings: Any) -> List[str]:
    if not isinstance(raw_warnings, list):
        return []
    values: List[str] = []
    for item in raw_warnings[:8]:
        text = str(item or "").strip()
        if text:
            values.append(text)
    return values


def _coerce_number(raw: Any) -> float | None:
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    text = str(raw).strip().replace(",", "")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _coerce_confidence(raw: Any) -> float:
    value = _coerce_number(raw)
    if value is None:
        return 0.0
    if value < 0:
        return 0.0
    if value > 1:
        return 1.0
    return float(value)
