"""Anthropic Claude HTTP 어댑터 — 코딩/긴 문서/검수 전담.

비용이 발생하는 외부 API다. 다음 조건이 모두 충족돼야 실제로 호출된다:

1. `.env` 또는 환경변수에 `ANTHROPIC_API_KEY` 가 있어야 함
2. 호출자가 `live=True`를 명시 (기본은 dry-run)

조건이 안 맞으면 모든 함수는 `None`을 반환해 호출자가 dry-run으로 폴백한다.
urllib만 사용해 의존성 0 (`dotenv`만 `.env` 로드에 사용).
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Iterable, List, Optional

from dotenv import dotenv_values

from .paths import ROOT
from . import usage_log, usage_caps


CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_API_VERSION = "2023-06-01"
DEFAULT_MODEL = os.environ.get("CLAUDE_DEFAULT_MODEL", "claude-haiku-4-5-20251001")
DEFAULT_MAX_TOKENS = int(os.environ.get("CLAUDE_DEFAULT_MAX_TOKENS", "1000"))
DEFAULT_TIMEOUT = float(os.environ.get("CLAUDE_TIMEOUT", "45"))


def _load_api_key() -> Optional[str]:
    """`.env`나 환경변수에서 ANTHROPIC_API_KEY를 가져온다. 절대 출력하지 않는다."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key and key.strip():
        return key.strip()
    env_path = ROOT / ".env"
    if env_path.exists():
        try:
            values = dotenv_values(env_path)
            v = values.get("ANTHROPIC_API_KEY")
            if v and v.strip():
                return v.strip()
        except Exception:
            pass
    return None


def has_api_key() -> bool:
    """키 존재 여부만 반환. 값은 노출하지 않는다."""
    return _load_api_key() is not None


def _http_post(payload: dict, api_key: str, timeout: float) -> Optional[dict]:
    data = json.dumps(payload).encode("utf-8")
    try:
        req = urllib.request.Request(
            CLAUDE_API_URL,
            data=data,
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": CLAUDE_API_VERSION,
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
    temperature: float = 0.4,
    max_tokens: Optional[int] = None,
    live: bool = False,
    timeout: float = DEFAULT_TIMEOUT,
) -> Optional[str]:
    """단발 코딩/검수 요청. 안전 가드 통과 못하면 None 반환."""
    if not live:
        return None
    if not prompt or not prompt.strip():
        return None
    key = _load_api_key()
    if not key:
        return None
    # 비용 캡 사전 점검 — 보수적으로 max_tokens 전부 사용한다고 가정
    chosen_model = model or DEFAULT_MODEL
    max_t = int(max_tokens or DEFAULT_MAX_TOKENS)
    est = usage_log.estimate_text_cost_krw(chosen_model, len(prompt) // 3, max_t)
    ok, reason = usage_caps.check_cap(est)
    if not ok:
        return f"[Claude blocked] {reason}"
    payload = {
        "model": chosen_model,
        "max_tokens": max_t,
        "temperature": float(temperature),
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        payload["system"] = system
    res = _http_post(payload, key, timeout)
    if not res:
        usage_log.log_text_call("anthropic_claude", chosen_model, 0, 0, success=False, purpose="generate")
        return None
    usage = res.get("usage") or {}
    in_tok = int(usage.get("input_tokens", 0) or 0)
    out_tok = int(usage.get("output_tokens", 0) or 0)
    # Anthropic response: { content: [{type:"text", text:"..."}], ... }
    content = res.get("content")
    if isinstance(content, list):
        parts = [
            blk.get("text", "")
            for blk in content
            if isinstance(blk, dict) and blk.get("type") == "text"
        ]
        text = "\n".join(p for p in parts if p).strip()
        if text:
            usage_log.log_text_call("anthropic_claude", chosen_model, in_tok, out_tok, purpose="generate")
            return text
    err = res.get("error")
    if isinstance(err, dict):
        msg = err.get("message", "Claude API error")
        usage_log.log_text_call("anthropic_claude", chosen_model, in_tok, out_tok, success=False, purpose="error")
        return f"[Claude error] {msg}"
    return None


def chat(
    messages: Iterable[dict],
    *,
    system: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.4,
    max_tokens: Optional[int] = None,
    live: bool = False,
    timeout: float = DEFAULT_TIMEOUT,
) -> Optional[str]:
    """다중 턴 채팅 — messages = [{role: user|assistant, content: ...}]"""
    if not live:
        return None
    msgs = list(messages)
    if not msgs:
        return None
    key = _load_api_key()
    if not key:
        return None
    # Anthropic는 system을 별도 필드로 받음
    payload = {
        "model": model or DEFAULT_MODEL,
        "max_tokens": int(max_tokens or DEFAULT_MAX_TOKENS),
        "temperature": float(temperature),
        "messages": [m for m in msgs if m.get("role") in ("user", "assistant")],
    }
    if system:
        payload["system"] = system
    res = _http_post(payload, key, timeout)
    if not res:
        return None
    content = res.get("content")
    if isinstance(content, list):
        parts = [
            blk.get("text", "")
            for blk in content
            if isinstance(blk, dict) and blk.get("type") == "text"
        ]
        text = "\n".join(p for p in parts if p).strip()
        if text:
            return text
    return None


def status_summary() -> dict:
    """키 존재 여부만 반환. 실제 호출 안 함 (비용 0)."""
    started = time.time()
    key_present = has_api_key()
    return {
        "provider": "anthropic_claude",
        "purpose": "코딩 / 긴 문서 / 검수",
        "api_key_present": key_present,
        "default_model": DEFAULT_MODEL,
        "endpoint": CLAUDE_API_URL,
        "external_call": False,  # status_summary는 호출 안 함
        "live_mode_requires": ["ANTHROPIC_API_KEY", "--live 옵션"],
        "checked_ms": int((time.time() - started) * 1000),
    }


__all__ = [
    "CLAUDE_API_URL",
    "DEFAULT_MODEL",
    "has_api_key",
    "generate",
    "chat",
    "status_summary",
]
