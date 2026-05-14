"""OpenAI (ChatGPT + DALL-E) HTTP 어댑터 — 디자인 카피/이미지 전담.

비용이 발생하는 외부 API다. 다음 조건이 모두 충족돼야 실제로 호출된다:

1. `.env` 또는 환경변수에 `OPENAI_API_KEY` 가 있어야 함
2. 호출자가 `live=True`를 명시 (기본은 dry-run)

조건이 안 맞으면 모든 함수는 `None`을 반환해 호출자가 dry-run으로 폴백한다.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Iterable, Optional

from dotenv import dotenv_values

from .paths import ROOT
from . import usage_log, usage_caps


OPENAI_BASE = "https://api.openai.com/v1"
DEFAULT_CHAT_MODEL = os.environ.get("OPENAI_DEFAULT_MODEL", "gpt-4o-mini")
DEFAULT_IMAGE_MODEL = os.environ.get("OPENAI_IMAGE_MODEL", "dall-e-3")
DEFAULT_MAX_TOKENS = int(os.environ.get("OPENAI_DEFAULT_MAX_TOKENS", "800"))
DEFAULT_TIMEOUT = float(os.environ.get("OPENAI_TIMEOUT", "60"))


def _load_api_key() -> Optional[str]:
    """`.env`나 환경변수에서 OPENAI_API_KEY를 가져온다. 값 노출 안 함."""
    key = os.environ.get("OPENAI_API_KEY")
    if key and key.strip():
        return key.strip()
    env_path = ROOT / ".env"
    if env_path.exists():
        try:
            values = dotenv_values(env_path)
            v = values.get("OPENAI_API_KEY")
            if v and v.strip():
                return v.strip()
        except Exception:
            pass
    return None


def has_api_key() -> bool:
    return _load_api_key() is not None


def _http_post(path: str, payload: dict, api_key: str, timeout: float) -> Optional[dict]:
    data = json.dumps(payload).encode("utf-8")
    url = f"{OPENAI_BASE}{path}"
    try:
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return json.loads(body)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, json.JSONDecodeError):
        return None


def generate(
    prompt: str,
    *,
    system: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    live: bool = False,
    timeout: float = DEFAULT_TIMEOUT,
) -> Optional[str]:
    """디자인 카피 / 비주얼 설명 / 썸네일 문구 생성."""
    if not live:
        return None
    if not prompt or not prompt.strip():
        return None
    key = _load_api_key()
    if not key:
        return None
    chosen_model = model or DEFAULT_CHAT_MODEL
    max_t = int(max_tokens or DEFAULT_MAX_TOKENS)
    est = usage_log.estimate_text_cost_krw(chosen_model, len(prompt) // 4, max_t)
    ok, reason = usage_caps.check_cap(est)
    if not ok:
        return f"[OpenAI blocked] {reason}"
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    payload = {
        "model": chosen_model,
        "messages": messages,
        "temperature": float(temperature),
        "max_tokens": max_t,
    }
    res = _http_post("/chat/completions", payload, key, timeout)
    if not res:
        usage_log.log_text_call("openai_chatgpt", chosen_model, 0, 0, success=False, purpose="generate")
        return None
    usage = res.get("usage") or {}
    in_tok = int(usage.get("prompt_tokens", 0) or 0)
    out_tok = int(usage.get("completion_tokens", 0) or 0)
    choices = res.get("choices")
    if isinstance(choices, list) and choices:
        msg = choices[0].get("message") or {}
        text = msg.get("content")
        if isinstance(text, str) and text.strip():
            usage_log.log_text_call("openai_chatgpt", chosen_model, in_tok, out_tok, purpose="generate")
            return text.strip()
    err = res.get("error")
    if isinstance(err, dict):
        usage_log.log_text_call("openai_chatgpt", chosen_model, in_tok, out_tok, success=False, purpose="error")
        return f"[OpenAI error] {err.get('message', 'API error')}"
    return None


def chat(
    messages: Iterable[dict],
    *,
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    live: bool = False,
    timeout: float = DEFAULT_TIMEOUT,
) -> Optional[str]:
    if not live:
        return None
    msgs = list(messages)
    if not msgs:
        return None
    key = _load_api_key()
    if not key:
        return None
    payload = {
        "model": model or DEFAULT_CHAT_MODEL,
        "messages": msgs,
        "temperature": float(temperature),
        "max_tokens": int(max_tokens or DEFAULT_MAX_TOKENS),
    }
    res = _http_post("/chat/completions", payload, key, timeout)
    if not res:
        return None
    choices = res.get("choices")
    if isinstance(choices, list) and choices:
        msg = choices[0].get("message") or {}
        text = msg.get("content")
        if isinstance(text, str) and text.strip():
            return text.strip()
    return None


def generate_image(
    prompt: str,
    *,
    model: Optional[str] = None,
    size: str = "1024x1024",
    n: int = 1,
    live: bool = False,
    timeout: float = DEFAULT_TIMEOUT,
) -> Optional[dict]:
    """디자인 이미지 생성 (DALL-E). 반환: {url, revised_prompt} 리스트 dict.

    1024x1024 이상은 비용이 높다. n 기본값 1 강제.
    """
    if not live:
        return None
    if not prompt or not prompt.strip():
        return None
    key = _load_api_key()
    if not key:
        return None
    n_safe = max(1, min(int(n), 4))
    chosen = model or DEFAULT_IMAGE_MODEL
    est = usage_log.estimate_image_cost_krw(chosen, n_safe)
    ok, reason = usage_caps.check_cap(est)
    if not ok:
        return {"error": reason, "blocked": True}
    payload = {
        "model": chosen,
        "prompt": prompt,
        "n": n_safe,
        "size": size,
    }
    res = _http_post("/images/generations", payload, key, timeout)
    if not res:
        usage_log.log_image_call("openai_dalle", chosen, n_safe, success=False, purpose="image")
        return None
    data = res.get("data")
    if isinstance(data, list) and data:
        usage_log.log_image_call("openai_dalle", chosen, len(data), purpose="image")
        return {
            "model": chosen,
            "size": size,
            "count": len(data),
            "items": [
                {
                    "url": item.get("url"),
                    "revised_prompt": item.get("revised_prompt"),
                }
                for item in data
            ],
        }
    err = res.get("error")
    if isinstance(err, dict):
        usage_log.log_image_call("openai_dalle", chosen, n_safe, success=False, purpose="image_error")
        return {"error": err.get("message", "OpenAI image error")}
    return None


def status_summary() -> dict:
    started = time.time()
    key_present = has_api_key()
    return {
        "provider": "openai_chatgpt",
        "purpose": "디자인 카피 / 이미지 (DALL-E)",
        "api_key_present": key_present,
        "default_chat_model": DEFAULT_CHAT_MODEL,
        "default_image_model": DEFAULT_IMAGE_MODEL,
        "endpoint": OPENAI_BASE,
        "external_call": False,
        "live_mode_requires": ["OPENAI_API_KEY", "--live 옵션"],
        "checked_ms": int((time.time() - started) * 1000),
    }


__all__ = [
    "OPENAI_BASE",
    "DEFAULT_CHAT_MODEL",
    "DEFAULT_IMAGE_MODEL",
    "has_api_key",
    "generate",
    "chat",
    "generate_image",
    "status_summary",
]
