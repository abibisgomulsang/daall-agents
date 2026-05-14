"""Ollama 실제 HTTP 어댑터.

기존 dry-run 모듈들이 이 어댑터를 import 해서 **선택적으로** 실제 호출로
승격할 수 있다. 호출 실패/타임아웃/Ollama 미설치 모든 경우에 `None`을
반환하므로, 호출자는 None일 때 기존 dry-run 출력으로 폴백한다.

의존성 0 (urllib + json 만 사용). 외부 네트워크 호출 없음 — `127.0.0.1:11434`만.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Iterable, List, Optional


OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_LOCAL_MODEL = os.environ.get("DEFAULT_LOCAL_MODEL", "gemma4:e2b")
DEFAULT_TIMEOUT = float(os.environ.get("OLLAMA_TIMEOUT", "20"))
SHORT_TIMEOUT = float(os.environ.get("OLLAMA_HEALTH_TIMEOUT", "2"))


@dataclass
class OllamaModel:
    name: str
    size_bytes: int
    parameter_size: str
    family: str
    quantization: str

    @property
    def size_gb(self) -> float:
        return self.size_bytes / (1024 ** 3)


def _http_get(path: str, timeout: float) -> Optional[dict]:
    url = f"{OLLAMA_BASE_URL.rstrip('/')}{path}"
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return json.loads(body)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, json.JSONDecodeError):
        return None


def _http_post(path: str, payload: dict, timeout: float) -> Optional[dict]:
    url = f"{OLLAMA_BASE_URL.rstrip('/')}{path}"
    data = json.dumps(payload).encode("utf-8")
    try:
        req = urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return json.loads(body)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, json.JSONDecodeError):
        return None


def is_alive() -> bool:
    """Ollama 데몬이 응답하는지 짧은 타임아웃으로 확인."""
    res = _http_get("/api/tags", SHORT_TIMEOUT)
    return res is not None and "models" in res


def list_models() -> Optional[List[OllamaModel]]:
    """현재 설치된 모델 목록. 실패 시 None."""
    res = _http_get("/api/tags", SHORT_TIMEOUT * 2)
    if not res or "models" not in res:
        return None
    out: List[OllamaModel] = []
    for m in res["models"]:
        details = m.get("details", {}) or {}
        out.append(
            OllamaModel(
                name=m.get("name", "unknown"),
                size_bytes=int(m.get("size", 0)),
                parameter_size=details.get("parameter_size", "?"),
                family=details.get("family", "?"),
                quantization=details.get("quantization_level", "?"),
            )
        )
    return out


def has_model(name: str) -> bool:
    """특정 모델이 설치되어 있는지 (콜론 태그 일치 또는 베이스 일치)."""
    models = list_models()
    if models is None:
        return False
    target = name.lower()
    target_base = target.split(":")[0]
    for m in models:
        ml = m.name.lower()
        if ml == target:
            return True
        if ml.split(":")[0] == target_base:
            return True
    return False


def generate(
    prompt: str,
    *,
    model: Optional[str] = None,
    system: Optional[str] = None,
    temperature: float = 0.6,
    max_tokens: int = 400,
    timeout: float = DEFAULT_TIMEOUT,
) -> Optional[str]:
    """단발 텍스트 생성. 실패 시 None."""
    if not prompt or not prompt.strip():
        return None
    chosen = model or DEFAULT_LOCAL_MODEL
    payload = {
        "model": chosen,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": float(temperature),
            "num_predict": int(max_tokens),
        },
    }
    if system:
        payload["system"] = system
    res = _http_post("/api/generate", payload, timeout)
    if not res:
        return None
    text = res.get("response")
    if isinstance(text, str) and text.strip():
        return text.strip()
    return None


def chat(
    messages: Iterable[dict],
    *,
    model: Optional[str] = None,
    temperature: float = 0.6,
    timeout: float = DEFAULT_TIMEOUT,
) -> Optional[str]:
    """다중 턴 채팅. messages = [{"role":"system|user|assistant","content":"..."}]"""
    msgs = list(messages)
    if not msgs:
        return None
    chosen = model or DEFAULT_LOCAL_MODEL
    payload = {
        "model": chosen,
        "messages": msgs,
        "stream": False,
        "options": {"temperature": float(temperature)},
    }
    res = _http_post("/api/chat", payload, timeout)
    if not res:
        return None
    msg = res.get("message") or {}
    text = msg.get("content")
    if isinstance(text, str) and text.strip():
        return text.strip()
    return None


def status_summary() -> dict:
    """UI/보고서용 간결 요약. 실패해도 예외 없이 dict 반환."""
    started = time.time()
    models = list_models()
    elapsed_ms = int((time.time() - started) * 1000)
    alive = models is not None
    default = DEFAULT_LOCAL_MODEL
    default_present = bool(models) and has_model(default)
    return {
        "alive": alive,
        "base_url": OLLAMA_BASE_URL,
        "default_model": default,
        "default_model_present": default_present,
        "model_count": len(models) if models else 0,
        "models": [
            {
                "name": m.name,
                "size_gb": round(m.size_gb, 2),
                "parameters": m.parameter_size,
                "family": m.family,
                "quantization": m.quantization,
            }
            for m in (models or [])
        ],
        "latency_ms": elapsed_ms,
        "actual_call": True,
        "external_call": False,
    }


__all__ = [
    "OllamaModel",
    "OLLAMA_BASE_URL",
    "DEFAULT_LOCAL_MODEL",
    "is_alive",
    "list_models",
    "has_model",
    "generate",
    "chat",
    "status_summary",
]
