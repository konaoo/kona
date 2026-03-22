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
import time
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
_MAX_RETURN_ITEMS = 12
_VISION_RETRY_DELAYS = (2.0, 4.0, 8.0)


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
    text_model = str(provider.get("text_model") or "").strip() or model
    base_url = str(provider.get("base_url") or "").strip()
    provider_type = str(provider.get("type") or "").strip().lower()
    if not api_key:
        raise PortfolioOcrError(
            "AI 服务未配置有效密钥，暂时无法识别截图",
            code="OCR_PROVIDER_NOT_CONFIGURED",
            status_code=503,
        )

    image_b64 = base64.b64encode(image_bytes).decode("ascii")
    prompts = [_build_ocr_prompt()]

    def _run_vision(prompt: str) -> str:
        if protocol == "anthropic":
            return _run_anthropic_vision(
                prompt=prompt,
                image_b64=image_b64,
                media_type=media_type,
                api_key=api_key,
                model=model,
            )
        return _run_openai_compatible_vision(
            prompt=prompt,
            image_b64=image_b64,
            media_type=media_type,
            api_key=api_key,
            model=model,
            base_url=base_url,
            provider_type=provider_type,
        )

    raw_text = ""
    try:
        last_parse_error: PortfolioOcrError | None = None
        last_warnings: List[str] = []
        for idx, prompt in enumerate(prompts):
            raw_text = _run_vision(prompt)
            try:
                payload = _parse_response_json(raw_text)
            except PortfolioOcrError as exc:
                last_parse_error = exc
                if exc.code in {"OCR_INVALID_JSON", "OCR_EMPTY_RESPONSE"}:
                    break
                raise
            items = _normalize_items(payload.get("items"))
            warnings = _normalize_warnings(payload.get("warnings"))
            last_warnings = warnings
            if items:
                return PortfolioOcrParseResult(
                    items=items,
                    warnings=warnings,
                    raw_text=raw_text,
                )
        merged_transcript_items: List[Dict[str, Any]] = []
        merged_transcript_warnings: List[str] = []
        transcript_raw_parts: List[str] = []
        last_transcript_error: PortfolioOcrError | None = None
        for transcript_prompt in _build_table_transcript_prompts():
            transcript = _run_vision(transcript_prompt)
            transcript_raw_parts.append(transcript)
            try:
                transcript_payload = _parse_transcript_to_payload(
                    transcript=transcript,
                    protocol=protocol,
                    api_key=api_key,
                    model=text_model,
                    base_url=base_url,
                    provider_type=provider_type,
                )
            except PortfolioOcrError as exc:
                last_transcript_error = exc
                if exc.code in {"OCR_EMPTY_RESPONSE", "OCR_INVALID_JSON"}:
                    continue
                raise
            transcript_items = _normalize_items(transcript_payload.get("items"))
            transcript_warnings = _normalize_warnings(transcript_payload.get("warnings"))
            merged_transcript_warnings.extend(transcript_warnings)
            merged_transcript_items = _merge_transcript_items(
                merged_transcript_items,
                transcript_items,
            )
            if merged_transcript_items:
                break
        if merged_transcript_items:
            merged_warnings = last_warnings + merged_transcript_warnings
            return PortfolioOcrParseResult(
                items=merged_transcript_items,
                warnings=_dedupe_texts(merged_warnings),
                raw_text="\n\n".join([part for part in transcript_raw_parts if str(part or "").strip()]),
            )
        if last_transcript_error is not None:
            raise last_transcript_error
        if last_parse_error is not None:
            raise last_parse_error
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

    raise PortfolioOcrError(
        "截图识别失败，请稍后重试",
        code="OCR_PARSE_FAILED",
        status_code=502,
    )


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
        "截图可能是单只持仓详情，也可能是深色背景、整页、多行、多列表格的持仓列表。"
        "不要臆造完整交易记录，不要输出解释性文字。"
        "\n\n"
        "严格返回一个 JSON 对象，不要加 markdown 代码块。格式如下：\n"
        "{\n"
        '  "items": [\n'
        "    {\n"
        '      "name": "资产名称",\n'
        '      "code": "截图里明确出现的代码；如果截图里没出现，就给空字符串",\n'
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
        "1. 最多返回 12 条候选资产。\n"
        "2. 如果同一张图里有多条资产，按从上到下、从左到右的顺序返回。\n"
        "3. 只有在截图里明确看到了代码，才能填写 code；如果没有明确看到，code 必须是空字符串。\n"
        "4. 如果数量或成本价看不清，就填 null，不要瞎猜。\n"
        "5. 绝对不要根据资产名称、品牌名、常识、热门股票记忆、价格或市场去猜代码。\n"
        "6. 如果截图是表格或列表，优先逐行提取名称、代码、数量、成本价，缺哪个就留空，不要因为缺一列就整行放弃。\n"
        "7. 如果表头写的是“成本/现价”，优先把前一个值当作成本价；如果表头写的是“现价/成本”，优先把后一个值当作成本价。\n"
        "8. 市值、盈亏、涨跌幅、今日盈亏、参考盈亏都不是 price，不要误填到成本价。\n"
        "9. 如果代码能明确识别，尽量给出标准代码，如：sh600519、hk00700、gb_aapl、f_110017。\n"
        "10. confidence 取 0 到 1 之间的小数。\n"
        "11. 只返回 JSON。"
    )


def _build_table_ocr_prompt() -> str:
    return (
        "你现在面对的是投资软件里的复杂持仓表截图。"
        "这类截图通常是深色背景、多行、多列、整页列表。"
        "你的任务不是解释页面，而是把每一行能识别出的资产提取成新增资产草稿。"
        "\n\n"
        "严格返回一个 JSON 对象，不要加 markdown 代码块。格式如下：\n"
        "{\n"
        '  "items": [\n'
        "    {\n"
        '      "name": "资产名称",\n'
        '      "code": "截图里明确出现的代码；如果截图里没出现，就给空字符串",\n'
        '      "qty": 123.45,\n'
        '      "price": 12.34,\n'
        '      "curr": "CNY/HKD/USD 之一，判断不出就给空字符串",\n'
        '      "asset_type": "a/hk/us/fund 之一，判断不出就给空字符串",\n'
        '      "confidence": 0.0,\n'
        '      "note": "最多一句提醒"\n'
        "    }\n"
        "  ],\n"
        '  "warnings": ["如果有整列看不清或字段缺失，在这里给简短提醒"]\n'
        "}\n\n"
        "表格识别规则：\n"
        "1. 最多返回 12 条资产，按从上到下顺序提取。\n"
        "2. 一行资产通常包含名称，可能还带一行代码；数量、成本价、现价、盈亏可能分散在右侧多列。\n"
        "3. 只提名称、代码、数量、成本价；市值、盈亏、涨跌幅都不要塞进 price。\n"
        "4. 如果表头是“成本/现价”，前一个值优先当成本价；如果表头是“现价/成本”，后一个值优先当成本价。\n"
        "5. 如果代码没出现在截图里，code 必须为空字符串，绝对不要猜。\n"
        "6. 如果一行里名称和数量能看清，但成本价看不清，也要保留这条资产，缺字段留空。\n"
        "7. 如果左侧有市场提示，例如“沪港”“港股”“美股”，可以用来辅助判断 curr 和 asset_type，但不能拿来猜代码。\n"
        "8. 只返回 JSON。"
    )


def _build_table_transcript_prompt(region_hint: str = "") -> str:
    region_text = f"另外，只关注资产列表的{region_hint}。" if region_hint else ""
    return (
        "你现在面对的是投资软件里的复杂持仓列表截图。"
        "请忽略顶部导航、底部标签栏、账户汇总区、分组汇总数字、列标题，只关注真正的资产列表区域。"
        + region_text +
        "请先不要输出 JSON，也不要总结。"
        "只做一件事：把截图里从上到下能看清的每一条资产，尽量合并成一行文本抄出来。"
        "\n\n"
        "规则：\n"
        "1. 每条资产优先输出成：名称 | 代码 | 数量 | 成本价。\n"
        "2. 如果代码没显示，就把代码位置留空，例如：腾讯控股 |  | 100 | 598.00。\n"
        "3. 如果一只资产在原图里分两行展示，请你尽量自己合并成一行再输出。\n"
        "4. 如果表头是“成本/现价”，优先把前一个数当成本；如果表头是“现价/成本”，优先把后一个数当成本。\n"
        "5. 市值、盈亏、涨跌幅不要放进成本价。\n"
        "6. 只返回逐行纯文本，不要 markdown，不要 JSON，不要解释。"
    )


def _build_table_transcript_prompts() -> List[str]:
    return [
        _build_table_transcript_prompt(),
        (
            "这是证券持仓总览截图。只看资产列表的上半段，忽略顶部导航、底部标签栏、列标题和下半段资产。"
            "把你能看清的每条资产逐行抄出来，只保留名称、代码、数量、成本价。"
            "如果没有代码不要猜。不要输出 JSON，不要解释。"
        ),
        (
            "这是证券持仓总览截图。只看资产列表的中间区域，忽略顶部导航、底部标签栏、列标题和上下两端资产。"
            "把你能看清的每条资产逐行抄出来，只保留名称、代码、数量、成本价。"
            "如果没有代码不要猜。不要输出 JSON，不要解释。"
        ),
        (
            "这是证券持仓总览截图。只看资产列表的下半段，忽略顶部导航、底部标签栏、列标题和上半段资产。"
            "把你能看清的每条资产逐行抄出来，只保留名称、代码、数量、成本价。"
            "如果没有代码不要猜。不要输出 JSON，不要解释。"
        ),
    ]


def _build_transcript_to_json_prompt(transcript: str) -> str:
    return (
        "你现在拿到的是从复杂持仓截图里逐行抄出的文本。"
        "请把它整理成新增资产草稿 JSON。"
        "\n\n"
        "严格返回一个 JSON 对象，不要加 markdown 代码块。格式如下：\n"
        "{\n"
        '  "items": [\n'
        "    {\n"
        '      "name": "资产名称",\n'
        '      "code": "文本里明确出现的代码；如果文本里没有，就给空字符串",\n'
        '      "qty": 123.45,\n'
        '      "price": 12.34,\n'
        '      "curr": "CNY/HKD/USD 之一，判断不出就给空字符串",\n'
        '      "asset_type": "a/hk/us/fund 之一，判断不出就给空字符串",\n'
        '      "confidence": 0.0,\n'
        '      "note": "最多一句提醒"\n'
        "    }\n"
        "  ],\n"
        '  "warnings": ["如果有字段仍然不确定，在这里给简短提醒"]\n'
        "}\n\n"
        "规则：\n"
        "1. 最多返回 12 条资产。\n"
        "2. 只提取名称、代码、数量、成本价。\n"
        "3. 代码只有在文本里明确出现时才能填写，绝对不要根据名称去猜。\n"
        "4. 成本价优先从“成本/现价”列里取成本，不要把市值、盈亏、涨跌幅塞进 price。\n"
        "5. 只返回 JSON。\n\n"
        f"原始逐行文本：\n{transcript}"
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

    def _call_once() -> str:
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

    return _run_with_rate_limit_retry(_call_once)


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
    return _call_openai_compatible_chat(
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
        api_key=api_key,
        model=model,
        base_url=base_url,
        provider_type=provider_type,
    )


def _run_openai_compatible_text(
    *,
    prompt: str,
    api_key: str,
    model: str,
    base_url: str,
    provider_type: str,
) -> str:
    return _call_openai_compatible_chat(
        messages=[{"role": "user", "content": prompt}],
        api_key=api_key,
        model=model,
        base_url=base_url,
        provider_type=provider_type,
    )


def _call_openai_compatible_chat(
    *,
    messages: List[Dict[str, Any]],
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

    def _call_once() -> str:
        client = OpenAI(api_key=api_key, base_url=resolved_base_url or None)
        resp = client.chat.completions.create(
            model=model or "gpt-4.1-mini",
            max_tokens=1200,
            temperature=0.1,
            messages=messages,
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

    return _run_with_rate_limit_retry(_call_once)


def _parse_transcript_to_payload(
    *,
    transcript: str,
    protocol: str,
    api_key: str,
    model: str,
    base_url: str,
    provider_type: str,
) -> Dict[str, Any]:
    text = str(transcript or "").strip()
    if not text:
        raise PortfolioOcrError(
            "截图识别结果为空",
            code="OCR_EMPTY_RESPONSE",
            status_code=502,
        )
    parsed_items = _parse_transcript_items(text)
    if parsed_items:
        return {"items": parsed_items, "warnings": []}
    prompt = _build_transcript_to_json_prompt(text)
    if protocol == "anthropic":
        structured = _run_anthropic_text(
            prompt=prompt,
            api_key=api_key,
            model=model,
        )
    else:
        structured = _run_openai_compatible_text(
            prompt=prompt,
            api_key=api_key,
            model=model,
            base_url=base_url,
            provider_type=provider_type,
        )
    return _parse_response_json(structured)


def _parse_transcript_items(transcript: str) -> List[Dict[str, Any]]:
    lines = [str(line or "").strip() for line in str(transcript or "").splitlines()]
    lines = [line for line in lines if line]
    items = _parse_pipe_lines(lines)
    if items:
        return items[:_MAX_RETURN_ITEMS]
    items = _parse_loose_lines(lines)
    return items[:_MAX_RETURN_ITEMS]


def _parse_pipe_lines(lines: List[str]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for line in lines:
        if "|" not in line:
            continue
        parts = [part.strip() for part in line.split("|")]
        if len(parts) < 4:
            continue
        name = parts[0]
        code = _extract_explicit_code(parts[1])
        qty = _coerce_number(parts[2])
        price, curr = _coerce_price_with_currency(parts[3])
        if not name:
            continue
        asset_type = _infer_asset_type(code=code, curr=curr)
        items.append(
            {
                "name": name,
                "code": code,
                "qty": qty,
                "price": price,
                "curr": curr,
                "asset_type": asset_type,
                "confidence": 0.65,
                "note": "",
            }
        )
    return items


def _parse_loose_lines(lines: List[str]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    idx = 0
    while idx < len(lines):
        current = lines[idx]
        next_line = lines[idx + 1] if idx + 1 < len(lines) else ""
        two_line_item = _parse_two_line_item(current, next_line)
        if two_line_item:
            items.append(two_line_item)
            idx += 2
            continue
        one_line_item = _parse_one_line_item(current)
        if one_line_item:
            items.append(one_line_item)
        idx += 1
    return items


def _parse_two_line_item(first_line: str, second_line: str) -> Dict[str, Any] | None:
    if not first_line or not second_line:
        return None
    code = _extract_explicit_code(second_line.split()[0] if second_line.split() else "")
    second_numbers = re.findall(r"(?:HK\$|US\$|\$|¥)?\d[\d,]*(?:\.\d+)?", second_line)
    if not code or len(second_numbers) < 3:
        return None
    name = _leading_text_before_number(first_line)
    if not name:
        return None
    qty = _coerce_number(second_numbers[1])
    price, curr = _coerce_price_with_currency(second_numbers[2])
    if qty is None or price is None:
        return None
    asset_type = _infer_asset_type(code=code, curr=curr)
    return {
        "name": name,
        "code": code,
        "qty": qty,
        "price": price,
        "curr": curr,
        "asset_type": asset_type,
        "confidence": 0.62,
        "note": "",
    }


def _parse_one_line_item(line: str) -> Dict[str, Any] | None:
    name = _leading_text_before_number(line)
    if not name:
        return None
    tail = str(line or "").strip()[len(name) :].strip()
    tokens = tail.split()
    explicit_code = _extract_explicit_code(tokens[0]) if tokens else ""
    numbers = re.findall(r"(?:HK\$|US\$|\$|¥)?\d[\d,]*(?:\.\d+)?", tail)
    if len(numbers) < 2:
        return None
    if explicit_code and len(numbers) >= 3:
        qty = _coerce_number(numbers[1])
        price, curr = _coerce_price_with_currency(numbers[2])
        code = explicit_code
    else:
        qty = _coerce_number(numbers[-2])
        price, curr = _coerce_price_with_currency(numbers[-1])
        code = ""
    if qty is None or price is None:
        return None
    return {
        "name": name,
        "code": code,
        "qty": qty,
        "price": price,
        "curr": curr,
        "asset_type": _infer_asset_type(code=code, curr=curr),
        "confidence": 0.58,
        "note": "",
    }


def _leading_text_before_number(line: str) -> str:
    text = str(line or "").strip()
    if not text:
        return ""
    match = re.search(r"(?:HK\$|US\$|\$|¥)?\d", text)
    if not match:
        return re.sub(r"[\s+\-]+$", "", text).strip()
    return re.sub(r"[\s+\-]+$", "", text[: match.start()]).strip()


def _extract_explicit_code(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    match = re.fullmatch(r"[A-Za-z]{1,5}\d{1,6}|\d{4,6}|[A-Za-z]{1,10}", text)
    if not match:
        return ""
    return text


def _coerce_price_with_currency(raw: Any) -> tuple[float | None, str]:
    text = str(raw or "").strip().replace(",", "")
    if not text:
        return None, ""
    curr = ""
    upper = text.upper()
    if upper.startswith("HK$"):
        curr = "HKD"
        text = text[3:]
    elif upper.startswith("US$"):
        curr = "USD"
        text = text[3:]
    elif text.startswith("$"):
        curr = "USD"
        text = text[1:]
    elif text.startswith("¥"):
        curr = "CNY"
        text = text[1:]
    return _coerce_number(text), curr


def _infer_asset_type(*, code: str, curr: str) -> str:
    lower_code = str(code or "").strip().lower()
    upper_curr = str(curr or "").strip().upper()
    if lower_code.startswith("hk") or upper_curr == "HKD":
        return "hk"
    if lower_code.startswith("gb_") or upper_curr == "USD":
        return "us"
    if lower_code.startswith("f_"):
        return "fund"
    if lower_code.startswith(("sh", "sz", "bj")) or upper_curr == "CNY":
        return "a"
    return ""


def _run_anthropic_text(
    *,
    prompt: str,
    api_key: str,
    model: str,
) -> str:
    import anthropic

    def _call_once() -> str:
        client = anthropic.Anthropic(api_key=api_key)
        resp = client.messages.create(
            model=model or "claude-sonnet-4-20250514",
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}],
        )
        chunks: List[str] = []
        for item in getattr(resp, "content", []) or []:
            text = getattr(item, "text", None)
            if text:
                chunks.append(text)
        return "\n".join(chunks).strip()

    return _run_with_rate_limit_retry(_call_once)


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
    for raw in raw_items[:_MAX_RETURN_ITEMS]:
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


def _dedupe_texts(values: List[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _merge_transcript_items(
    existing: List[Dict[str, Any]],
    incoming: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    merged = list(existing)
    seen = {
        (
            str(item.get("name") or "").strip(),
            str(item.get("code") or "").strip(),
            str(item.get("qty")),
            str(item.get("price")),
        )
        for item in merged
    }
    for item in incoming:
        key = (
            str(item.get("name") or "").strip(),
            str(item.get("code") or "").strip(),
            str(item.get("qty")),
            str(item.get("price")),
        )
        if key in seen:
            continue
        seen.add(key)
        merged.append(item)
        if len(merged) >= _MAX_RETURN_ITEMS:
            break
    return merged


def _run_with_rate_limit_retry(callable_):
    last_exc = None
    for attempt in range(len(_VISION_RETRY_DELAYS) + 1):
        try:
            return callable_()
        except Exception as exc:
            last_exc = exc
            if attempt >= len(_VISION_RETRY_DELAYS) or not _is_rate_limit_error(exc):
                raise
            time.sleep(_VISION_RETRY_DELAYS[attempt])
    raise last_exc


def _is_rate_limit_error(exc: Exception) -> bool:
    text = str(exc or "").lower()
    return (
        "rate limit" in text
        or "访问量过大" in text
        or "速率限制" in text
        or "error code: 429" in text
        or "code': '1302'" in text
        or 'code": "1302"' in text
        or "code': '1305'" in text
        or 'code": "1305"' in text
    )


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
