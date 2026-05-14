"""Hermes 장기 메모리 + inbox/outbox.

`11_memory/hermes/` 아래에 다음 파일을 운영한다:

- `inbox.jsonl`   — 사장님이 텔레그램으로 보낸 메시지 (수신순)
- `outbox.jsonl`  — Hermes가 사장님에게 보낸 응답 (송신순)
- `preferences.json` — 사장님 선호 (자주 쓰는 명령, 선호 톤 등)
- `recent_decisions.jsonl` — 최근 처리한 결정/결과 요약
- `rate.json`     — 분당/일일 자동 처리 카운터 (rate limit)

값/키 자체는 절대 저장하지 않는다 (텔레그램 봇 토큰, API 키 등). 메시지
본문은 사장님 입력만 저장하고, AI 응답은 길이/요약만 저장.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from .paths import ROOT


HERMES_DIR = ROOT / "11_memory" / "hermes"


def _ensure() -> None:
    HERMES_DIR.mkdir(parents=True, exist_ok=True)


# ──────────────────────────────────────────────
# inbox / outbox
# ──────────────────────────────────────────────

INBOX_PATH = lambda: HERMES_DIR / "inbox.jsonl"   # noqa: E731
OUTBOX_PATH = lambda: HERMES_DIR / "outbox.jsonl"   # noqa: E731


def _append_jsonl(path: Path, record: Dict[str, Any]) -> None:
    _ensure()
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def record_inbound(
    text: str,
    *,
    from_chat_id: int,
    from_user: str = "",
    message_id: int = 0,
    status: str = "received",
) -> Dict[str, Any]:
    rec = {
        "time": datetime.now().isoformat(timespec="seconds"),
        "kind": "inbound",
        "from_chat_id": int(from_chat_id),
        "from_user": from_user[:40],
        "message_id": int(message_id),
        "text": text[:600],
        "status": status,
    }
    _append_jsonl(INBOX_PATH(), rec)
    return rec


def record_outbound(
    text_summary: str,
    *,
    to_chat_id: int,
    success: bool = True,
    reason: str = "",
) -> Dict[str, Any]:
    rec = {
        "time": datetime.now().isoformat(timespec="seconds"),
        "kind": "outbound",
        "to_chat_id": int(to_chat_id),
        "text_summary": text_summary[:400],
        "success": bool(success),
        "reason": reason[:120],
    }
    _append_jsonl(OUTBOX_PATH(), rec)
    return rec


def read_jsonl(path: Path, limit: int = 50) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    recs: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                recs.append(json.loads(line))
            except Exception:
                continue
    return recs[-limit:]


def recent_inbound(limit: int = 20) -> List[Dict[str, Any]]:
    return read_jsonl(INBOX_PATH(), limit=limit)


def recent_outbound(limit: int = 20) -> List[Dict[str, Any]]:
    return read_jsonl(OUTBOX_PATH(), limit=limit)


# ──────────────────────────────────────────────
# 사장님 선호 (preferences.json)
# ──────────────────────────────────────────────

PREFS_PATH = lambda: HERMES_DIR / "preferences.json"   # noqa: E731


def _load_prefs() -> Dict[str, Any]:
    p = PREFS_PATH()
    if not p.exists():
        return {
            "favorite_commands": [],
            "favorite_topics": [],
            "preferred_tone": "차분하고 짧게",
            "updated_at": "",
        }
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"favorite_commands": [], "favorite_topics": [], "preferred_tone": "차분하고 짧게"}


def _save_prefs(prefs: Dict[str, Any]) -> None:
    _ensure()
    prefs["updated_at"] = datetime.now().isoformat(timespec="seconds")
    PREFS_PATH().write_text(json.dumps(prefs, ensure_ascii=False, indent=2), encoding="utf-8")


def get_preferences() -> Dict[str, Any]:
    return _load_prefs()


def remember_command(text: str) -> None:
    """사장님이 자주 쓰는 명령 패턴 기억 (상위 단어만)."""
    prefs = _load_prefs()
    favs = prefs.get("favorite_commands") or []
    # 간단한 빈도 학습 — 메시지 머리 24자
    head = text.strip().splitlines()[0][:24] if text.strip() else ""
    if not head:
        return
    # 중복은 위로 이동
    favs = [f for f in favs if f.get("head") != head]
    favs.insert(0, {"head": head, "last_seen": datetime.now().isoformat(timespec="seconds")})
    prefs["favorite_commands"] = favs[:15]
    _save_prefs(prefs)


# ──────────────────────────────────────────────
# 최근 결정 요약
# ──────────────────────────────────────────────

DECISIONS_PATH = lambda: HERMES_DIR / "recent_decisions.jsonl"   # noqa: E731


def record_decision(
    title: str,
    *,
    intent: str = "",
    artifact_path: str = "",
    safe: bool = True,
    auto_executed: bool = False,
) -> Dict[str, Any]:
    rec = {
        "time": datetime.now().isoformat(timespec="seconds"),
        "title": title[:120],
        "intent": intent[:40],
        "artifact_path": artifact_path[:240],
        "safe": bool(safe),
        "auto_executed": bool(auto_executed),
    }
    _append_jsonl(DECISIONS_PATH(), rec)
    return rec


def recent_decisions(limit: int = 10) -> List[Dict[str, Any]]:
    return read_jsonl(DECISIONS_PATH(), limit=limit)


# ──────────────────────────────────────────────
# Rate limit (분당/일일)
# ──────────────────────────────────────────────

RATE_PATH = lambda: HERMES_DIR / "rate.json"   # noqa: E731

DEFAULT_PER_MINUTE = int(os.environ.get("HERMES_PER_MINUTE", "12"))
DEFAULT_PER_DAY    = int(os.environ.get("HERMES_PER_DAY",    "60"))


def _load_rate() -> Dict[str, Any]:
    p = RATE_PATH()
    if not p.exists():
        return {"minute_window": [], "day_count": 0, "day_date": ""}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"minute_window": [], "day_count": 0, "day_date": ""}


def _save_rate(rate: Dict[str, Any]) -> None:
    _ensure()
    RATE_PATH().write_text(json.dumps(rate, ensure_ascii=False, indent=2), encoding="utf-8")


def check_and_count() -> tuple[bool, str]:
    """rate limit 검사 + 통과 시 카운트 증가.

    Returns (ok, reason).
    """
    now = datetime.now()
    today = now.date().isoformat()
    rate = _load_rate()
    # 분 단위 윈도우 정리
    cutoff = (now - timedelta(seconds=60)).isoformat()
    window: List[str] = [t for t in rate.get("minute_window", []) if t >= cutoff]
    if len(window) >= DEFAULT_PER_MINUTE:
        return False, f"분당 자동 처리 한도 {DEFAULT_PER_MINUTE}회 초과 — 잠시 후 다시 시도"
    # 일 단위
    if rate.get("day_date") != today:
        rate["day_date"] = today
        rate["day_count"] = 0
    if rate.get("day_count", 0) >= DEFAULT_PER_DAY:
        return False, f"일일 자동 처리 한도 {DEFAULT_PER_DAY}회 초과 — 내일 다시 시도"
    # 통과 시 카운트
    window.append(now.isoformat())
    rate["minute_window"] = window[-DEFAULT_PER_MINUTE:]
    rate["day_count"] = int(rate.get("day_count", 0)) + 1
    _save_rate(rate)
    return True, "ok"


def rate_status() -> Dict[str, Any]:
    rate = _load_rate()
    return {
        "per_minute_cap": DEFAULT_PER_MINUTE,
        "per_day_cap": DEFAULT_PER_DAY,
        "minute_used": len(rate.get("minute_window") or []),
        "day_used": int(rate.get("day_count", 0)),
        "day_date": rate.get("day_date", ""),
    }


# ──────────────────────────────────────────────
# 종합 상태 — UI/CLI에서 사용
# ──────────────────────────────────────────────

def status_summary() -> Dict[str, Any]:
    return {
        "memory_dir": str(HERMES_DIR),
        "inbox_count": len(recent_inbound(limit=1000)),
        "outbox_count": len(recent_outbound(limit=1000)),
        "decisions_count": len(recent_decisions(limit=1000)),
        "preferences": _load_prefs(),
        "rate": rate_status(),
    }


__all__ = [
    "HERMES_DIR",
    "record_inbound",
    "record_outbound",
    "recent_inbound",
    "recent_outbound",
    "get_preferences",
    "remember_command",
    "record_decision",
    "recent_decisions",
    "check_and_count",
    "rate_status",
    "status_summary",
]
