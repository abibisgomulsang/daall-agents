"""Google Gemini HTTP 어댑터 — 리서치/트렌드 조사 전담.

키(`GOOGLE_API_KEY`)가 채워지기 전까지는 모든 호출이 None을 반환해
호출자가 dry-run으로 폴백한다. 사장님이 키 채우는 순간 바로 작동.

Generative Language API:
  POST https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key=...
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Optional

from dotenv import dotenv_values

from .paths import ROOT
from . import usage_log, usage_caps


GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_MODEL = os.environ.get("GEMINI_DEFAULT_MODEL", "gemini-1.5-flash")
DEFAULT_MAX_TOKENS = int(os.environ.get("GEMINI_DEFAULT_MAX_TOKENS", "800"))
DEFAULT_TIMEOUT = float(os.environ.get("GEMINI_TIMEOUT", "45"))


def _load_api_key() -> Optional[str]:
    key = os.environ.get("GOOGLE_API_KEY")
    if key and key.strip():
        return key.strip()
    env_path = ROOT / ".env"
    if env_path.exists():
        try:
            values = dotenv_values(env_path)
            v = values.get("GOOGLE_API_KEY")
            if v and v.strip():
                return v.strip()
        except Exception:
            pass
    return None


def has_api_key() -> bool:
    return _load_api_key() is not None


def _http_post(model: str, payload: dict, api_key: str, timeout: float) -> Optional[dict]:
    data = json.dumps(payload).encode("utf-8")
    url = f"{GEMINI_BASE}/models/{model}:generateContent?key={api_key}"
    try:
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
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
    temperature: float = 0.5,
    max_tokens: Optional[int] = None,
    live: bool = False,
    timeout: float = DEFAULT_TIMEOUT,
) -> Optional[str]:
    if not live:
        return None
    if not prompt or not prompt.strip():
        return None
    key = _load_api_key()
    if not key:
        return None
    chosen = model or DEFAULT_MODEL
    max_t = int(max_tokens or DEFAULT_MAX_TOKENS)
    est = usage_log.estimate_text_cost_krw(chosen, len(prompt) // 4, max_t)
    ok, reason = usage_caps.check_cap(est)
    if not ok:
        return f"[Gemini blocked] {reason}"

    parts = []
    if system:
        parts.append({"text": f"[SYSTEM]\n{system}\n\n[USER]\n{prompt}"})
    else:
        parts.append({"text": prompt})
    payload = {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {
            "temperature": float(temperature),
            "maxOutputTokens": max_t,
        },
    }
    res = _http_post(chosen, payload, key, timeout)
    if not res:
        usage_log.log_text_call("google_gemini", chosen, 0, 0, success=False, purpose="generate")
        return None

    # Gemini response: candidates[0].content.parts[].text
    cands = res.get("candidates") or []
    if cands:
        cand = cands[0]
        content = cand.get("content") or {}
        parts_out = content.get("parts") or []
        text = "\n".join(p.get("text", "") for p in parts_out if p.get("text"))
        usage_meta = res.get("usageMetadata") or {}
        in_tok = int(usage_meta.get("promptTokenCount", 0) or 0)
        out_tok = int(usage_meta.get("candidatesTokenCount", 0) or 0)
        if text.strip():
            usage_log.log_text_call("google_gemini", chosen, in_tok, out_tok, purpose="generate")
            return text.strip()
    err = res.get("error")
    if isinstance(err, dict):
        usage_log.log_text_call("google_gemini", chosen, 0, 0, success=False, purpose="error")
        return f"[Gemini error] {err.get('message', 'API error')}"
    return None


def status_summary() -> dict:
    started = time.time()
    return {
        "provider": "google_gemini",
        "purpose": "리서치 / 트렌드 / 아이디어 확장",
        "api_key_present": has_api_key(),
        "default_model": DEFAULT_MODEL,
        "endpoint": GEMINI_BASE,
        "external_call": False,
        "live_mode_requires": ["GOOGLE_API_KEY", "--live 옵션"],
        "checked_ms": int((time.time() - started) * 1000),
    }


__all__ = ["has_api_key", "generate", "status_summary"]
