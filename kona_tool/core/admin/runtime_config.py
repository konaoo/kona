"""
管理后台运行时配置与运营配置。
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse

import config

from core.admin.constants import (
    CONFIG_WHITELIST,
    OPS_APP_UPDATE_DOWNLOAD_URL_KEY,
    OPS_APP_UPDATE_DOWNLOAD_URL_MAX_LENGTH,
    OPS_APP_UPDATE_TEXT_KEY,
    OPS_APP_UPDATE_TEXT_MAX_LENGTH,
    OPS_INVITE_ACQUIRE_IMAGE_URL_KEY,
    OPS_INVITE_ACQUIRE_IMAGE_URL_MAX_LENGTH,
    OPS_INVITE_ACQUIRE_TEXT_KEY,
    OPS_INVITE_ACQUIRE_TEXT_MAX_LENGTH,
    OPS_IOS_QR_IMAGE_URL_KEY,
    OPS_IOS_QR_IMAGE_URL_MAX_LENGTH,
    OPS_IOS_QR_TEXT_KEY,
    OPS_IOS_QR_TEXT_MAX_LENGTH,
    OPS_USER_GROUP_IMAGE_URL_KEY,
    OPS_USER_GROUP_TEXT_KEY,
)
from core.admin.common import coerce_bool


_RUNTIME_CONFIG_OVERRIDES: Dict[str, Any] = {}
_DEFAULT_CONFIG_VALUES: Dict[str, Any] = {
    key: getattr(config, key, None) for key in CONFIG_WHITELIST
}


def coerce_config_value(key: str, value: Any) -> Any:
    rule = CONFIG_WHITELIST[key]
    value_type = rule["type"]
    if value_type == "int":
        normalized = int(value)
        if "min" in rule and normalized < rule["min"]:
            raise ValueError(f"{key} must be >= {rule['min']}")
        if "max" in rule and normalized > rule["max"]:
            raise ValueError(f"{key} must be <= {rule['max']}")
        return normalized
    if value_type == "bool":
        return coerce_bool(value)
    if value_type == "str":
        normalized = str(value).strip()
        choices = rule.get("choices", [])
        if choices and normalized not in choices:
            raise ValueError(f"{key} must be one of {choices}")
        return normalized
    raise ValueError(f"Unsupported config type: {value_type}")


def get_whitelist_configs() -> List[Dict[str, Any]]:
    items = []
    for key, rule in CONFIG_WHITELIST.items():
        value = _RUNTIME_CONFIG_OVERRIDES.get(key, getattr(config, key, None))
        default_value = _DEFAULT_CONFIG_VALUES.get(key)
        if "choices" in rule:
            recommended = " / ".join(str(value) for value in rule["choices"])
        elif "min" in rule and "max" in rule:
            recommended = f"{rule['min']} - {rule['max']}"
        elif "min" in rule:
            recommended = f">= {rule['min']}"
        else:
            recommended = "-"
        items.append(
            {
                "key": key,
                "display_name": rule.get("display_name", key),
                "value": value,
                "default_value": default_value,
                "type": rule["type"],
                "description": rule["description"],
                "min": rule.get("min"),
                "max": rule.get("max"),
                "choices": rule.get("choices", []),
                "recommended": recommended,
            }
        )
    return items


def update_runtime_configs(updates: List[Tuple[str, Any]]) -> List[Dict[str, Any]]:
    updated_items = []
    for key, value in updates:
        if key not in CONFIG_WHITELIST:
            raise ValueError(f"Key not allowed: {key}")
        coerced = coerce_config_value(key, value)
        setattr(config, key, coerced)
        _RUNTIME_CONFIG_OVERRIDES[key] = coerced
        updated_items.append({"key": key, "value": coerced})
    return updated_items


def reset_runtime_configs(key: str = "") -> List[Dict[str, Any]]:
    if key and key not in CONFIG_WHITELIST:
        raise ValueError(f"Key not allowed: {key}")
    keys = [key] if key else list(CONFIG_WHITELIST.keys())
    updated_items = []
    for cfg_key in keys:
        default_value = _DEFAULT_CONFIG_VALUES.get(cfg_key)
        setattr(config, cfg_key, default_value)
        _RUNTIME_CONFIG_OVERRIDES.pop(cfg_key, None)
        updated_items.append({"key": cfg_key, "value": default_value})
    return updated_items


def normalize_invite_acquire_text(raw: Any) -> str:
    text = str(raw or "").strip()
    if not text or len(text) > OPS_INVITE_ACQUIRE_TEXT_MAX_LENGTH:
        raise ValueError(f"text must be 1-{OPS_INVITE_ACQUIRE_TEXT_MAX_LENGTH} characters")
    return text


def normalize_invite_acquire_image_url(raw: Any) -> str:
    url = str(raw or "").strip()
    if not url:
        return ""
    if len(url) > OPS_INVITE_ACQUIRE_IMAGE_URL_MAX_LENGTH:
        raise ValueError(f"image_url must be <= {OPS_INVITE_ACQUIRE_IMAGE_URL_MAX_LENGTH} characters")
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("image_url must start with http:// or https://")
    return url


def normalize_ios_qr_text(raw: Any) -> str:
    text = str(raw or "").strip()
    if not text or len(text) > OPS_IOS_QR_TEXT_MAX_LENGTH:
        raise ValueError(f"text must be 1-{OPS_IOS_QR_TEXT_MAX_LENGTH} characters")
    return text


def normalize_ios_qr_image_url(raw: Any) -> str:
    url = str(raw or "").strip()
    if not url:
        return ""
    if len(url) > OPS_IOS_QR_IMAGE_URL_MAX_LENGTH:
        raise ValueError(f"image_url must be <= {OPS_IOS_QR_IMAGE_URL_MAX_LENGTH} characters")
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("image_url must start with http:// or https://")
    return url


def normalize_app_update_text(raw: Any) -> str:
    text = str(raw or "").strip()
    if not text or len(text) > OPS_APP_UPDATE_TEXT_MAX_LENGTH:
        raise ValueError(f"text must be 1-{OPS_APP_UPDATE_TEXT_MAX_LENGTH} characters")
    return text


def normalize_app_update_download_url(raw: Any) -> str:
    url = str(raw or "").strip()
    if not url:
        return ""
    if len(url) > OPS_APP_UPDATE_DOWNLOAD_URL_MAX_LENGTH:
        raise ValueError(f"download_url must be <= {OPS_APP_UPDATE_DOWNLOAD_URL_MAX_LENGTH} characters")
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("download_url must start with http:// or https://")
    return url


def load_invite_acquire_ops_config(db) -> Dict[str, str]:
    return load_ops_text_image_config(
        db=db,
        text_key=OPS_INVITE_ACQUIRE_TEXT_KEY,
        image_url_key=OPS_INVITE_ACQUIRE_IMAGE_URL_KEY,
        default_text=str(config.INVITE_ACQUIRE_TEXT).strip() or "小红书被限制了，进微信群领邀请码。",
        default_image_url=str(config.INVITE_ACQUIRE_IMAGE_URL).strip(),
    )


def load_user_group_ops_config(db) -> Dict[str, str]:
    return load_ops_text_image_config(
        db=db,
        text_key=OPS_USER_GROUP_TEXT_KEY,
        image_url_key=OPS_USER_GROUP_IMAGE_URL_KEY,
        default_text=str(config.USER_GROUP_TEXT).strip() or "加入咔咔用户群",
        default_image_url=str(config.USER_GROUP_IMAGE_URL).strip(),
    )


def load_ios_qr_ops_config(db) -> Dict[str, str]:
    return load_ops_text_image_config(
        db=db,
        text_key=OPS_IOS_QR_TEXT_KEY,
        image_url_key=OPS_IOS_QR_IMAGE_URL_KEY,
        default_text=str(config.IOS_QR_TEXT).strip() or "扫码下载苹果版",
        default_image_url=str(config.IOS_QR_IMAGE_URL).strip(),
    )


def load_app_update_ops_config(db) -> Dict[str, str]:
    text_raw = db.get_runtime_config(OPS_APP_UPDATE_TEXT_KEY)
    download_url_raw = db.get_runtime_config(OPS_APP_UPDATE_DOWNLOAD_URL_KEY)
    default_text = str(config.CLIENT_APP_RELEASE_NOTES).strip() or "更新内容"
    default_download_url = str(config.CLIENT_APP_DOWNLOAD_URL).strip()
    text = str(text_raw).strip() if text_raw is not None else default_text
    if not text:
        text = default_text
    download_url = str(download_url_raw).strip() if download_url_raw is not None else default_download_url
    return {"text": text, "download_url": download_url}


def load_ops_text_image_config(
    db,
    *,
    text_key: str,
    image_url_key: str,
    default_text: str,
    default_image_url: str,
) -> Dict[str, str]:
    text_raw = db.get_runtime_config(text_key)
    image_url_raw = db.get_runtime_config(image_url_key)
    text = str(text_raw).strip() if text_raw is not None else default_text
    if not text:
        text = default_text
    image_url = str(image_url_raw).strip() if image_url_raw is not None else default_image_url
    return {"text": text, "image_url": image_url}
