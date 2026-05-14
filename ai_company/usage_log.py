"""LLM 호출 사용량 로그 + 비용 추정.

각 외부 API 호출(claude/openai/gemini) 후 입력/출력 토큰을 받아
`12_logs/llm_usage.jsonl`에 한 줄씩 적재한다. 모델별 단가표(USD/MTok)와
환율로 KRW 추정 비용도 함께 기록한다.

값/키는 절대 저장하지 않는다. 메시지 본문도 저장 안 함 — 토큰 수만.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from .paths import ROOT

LOG_PATH = ROOT / "12_logs" / "llm_usage.jsonl"

# 모델별 단가 (USD per 1M tokens). 정확한 값은 공식 가격표 확인 필요.
# 환경변수 PRICING_OVERRIDE_JSON으로 갱신 가능.
DEFAULT_PRICING: dict[str, dict[str, float]] = {
    # Anthropic Claude
    "claude-haiku-4-5-20251001":  {"input": 1.0,  "output": 5.0},
    "claude-haiku":               {"input": 1.0,  "output": 5.0},
    "claude-sonnet-4-5":          {"input": 3.0,  "output": 15.0},
    "claude-opus-4-6":            {"input": 15.0, "output": 75.0},
    # OpenAI
    "gpt-4o-mini":                {"input": 0.15, "output": 0.60},
    "gpt-4o":                     {"input": 2.50, "output": 10.00},
    # Gemini (참고치)
    "gemini-1.5-flash":           {"input": 0.075, "output": 0.30},
    "gemini-1.5-pro":             {"input": 1.25,  "output": 5.0},
}

# DALL-E 이미지당 USD (1024x1024 standard)
DALLE_PRICE_USD = {
    "dall-e-3":     0.040,
    "dall-e-3-hd":  0.080,
    "dall-e-2":     0.020,
}

# USD → KRW 환산. 시세 변동이라 보수적으로 큰 값.
USD_TO_KRW = float(os.environ.get("USD_TO_KRW", "1400"))


def _pricing_for(model: str) -> dict[str, float]:
    pricing = dict(DEFAULT_PRICING)
    raw = os.environ.get("PRICING_OVERRIDE_JSON")
    if raw:
        try:
            override = json.loads(raw)
            if isinstance(override, dict):
                pricing.update(override)
        except Exception:
            pass
    if model in pricing:
        return pricing[model]
    # 베이스명으로 매칭 (예: claude-haiku-4-5-20251001 → claude-haiku)
    base = model.split("-")[0] + "-" + (model.split("-")[1] if "-" in model[len(model.split("-")[0])+1:] else "")
    base2 = "-".join(model.split("-")[:2])
    return pricing.get(base2) or pricing.get(base) or {"input": 0.0, "output": 0.0}


def estimate_text_cost_krw(model: str, input_tokens: int, output_tokens: int) -> float:
    p = _pricing_for(model)
    usd = (input_tokens / 1_000_000) * p.get("input", 0.0) + (output_tokens / 1_000_000) * p.get("output", 0.0)
    return round(usd * USD_TO_KRW, 2)


def estimate_image_cost_krw(model: str, count: int = 1) -> float:
    usd = DALLE_PRICE_USD.get(model, 0.04) * max(1, int(count))
    return round(usd * USD_TO_KRW, 2)


def _append(record: dict) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def log_text_call(
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    *,
    purpose: str = "",
    success: bool = True,
) -> dict:
    cost_krw = estimate_text_cost_krw(model, input_tokens, output_tokens)
    record = {
        "time": datetime.now().isoformat(),
        "provider": provider,
        "model": model,
        "kind": "text",
        "input_tokens": int(input_tokens or 0),
        "output_tokens": int(output_tokens or 0),
        "cost_krw_est": cost_krw,
        "success": bool(success),
        "purpose": purpose[:80],
    }
    _append(record)
    return record


def log_image_call(
    provider: str,
    model: str,
    count: int,
    *,
    purpose: str = "",
    success: bool = True,
) -> dict:
    cost_krw = estimate_image_cost_krw(model, count)
    record = {
        "time": datetime.now().isoformat(),
        "provider": provider,
        "model": model,
        "kind": "image",
        "image_count": int(count or 1),
        "cost_krw_est": cost_krw,
        "success": bool(success),
        "purpose": purpose[:80],
    }
    _append(record)
    return record


def _iter_records():
    if not LOG_PATH.exists():
        return
    with LOG_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                continue


def daily_summary(when: Optional[datetime] = None) -> dict:
    target = (when or datetime.now()).date().isoformat()
    total_calls = 0
    total_cost = 0.0
    per_provider: dict[str, dict] = {}
    for rec in _iter_records():
        if not rec.get("time", "").startswith(target):
            continue
        total_calls += 1
        c = float(rec.get("cost_krw_est", 0))
        total_cost += c
        p = rec.get("provider", "unknown")
        slot = per_provider.setdefault(p, {"calls": 0, "cost_krw_est": 0.0})
        slot["calls"] += 1
        slot["cost_krw_est"] = round(slot["cost_krw_est"] + c, 2)
    return {
        "date": target,
        "total_calls": total_calls,
        "total_cost_krw_est": round(total_cost, 2),
        "per_provider": per_provider,
    }


def monthly_summary(when: Optional[datetime] = None) -> dict:
    now = when or datetime.now()
    month = f"{now.year:04d}-{now.month:02d}"
    total_calls = 0
    total_cost = 0.0
    for rec in _iter_records():
        if not rec.get("time", "").startswith(month):
            continue
        total_calls += 1
        total_cost += float(rec.get("cost_krw_est", 0))
    return {
        "month": month,
        "total_calls": total_calls,
        "total_cost_krw_est": round(total_cost, 2),
    }


__all__ = [
    "LOG_PATH",
    "USD_TO_KRW",
    "estimate_text_cost_krw",
    "estimate_image_cost_krw",
    "log_text_call",
    "log_image_call",
    "daily_summary",
    "monthly_summary",
]
