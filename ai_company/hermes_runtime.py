"""[DEPRECATED] 미니 Hermes 봇 — Nous Research Hermes Agent로 대체 예정.

⚠ 이 모듈은 사장님이 진짜 `Nous Research Hermes Agent`
(https://github.com/NousResearch/hermes-agent)를 설치하시기 전까지의
**임시 미니 봇**입니다. 진짜 Hermes 설치 후에는:

- `docs/HERMES_SETUP.md` 가이드대로 WSL2 + Hermes 설치
- `scripts/install_hermes_skills.sh` 로 우리 회사 스킬 5종 설치
- 이 모듈은 다음 작업에서 정식 deprecate (호출자 마이그레이션 후)
- 가상 사무실은 Hermes 세션 데이터를 직접 폴링하도록 변경

진짜 Hermes는 자기개선 학습 루프, 다중 플랫폼 게이트웨이(텔레그램/Discord/
Slack/WhatsApp/Signal/Email), 스킬 자동 생성, FTS5 세션 검색, 서브에이전트,
cron 스케줄러 등 이 모듈로는 절대 못 만드는 기능을 제공합니다.

원래 docstring:



흐름:
    사장님 텔레그램 메시지 → hermes_runtime
       ↓ owner_chat_id 확인 (사장님 본인 메시지만)
       ↓ inbox.jsonl 기록 + remember_command
       ↓ rate limit 검사 (HERMES_PER_MINUTE, HERMES_PER_DAY)
       ↓ nl_command.interpret() 호출 (위험 키워드 자동 차단 포함)
       ├ 안전 명령 + safe_to_run → 자동 CLI 실행 + 결과 텔레그램 회신
       └ 위험 명령 → 09_approval 자동 생성 + 사장님 텔레그램 회신 ("승인 필요")
    가상 사무실/시뮬레이터는 inbox.jsonl 폴링으로 실시간 동기화

안전 가드:
- 봇 토큰 없거나 python-telegram-bot 미설치 → dry-run 모드 (코드는 동작, 봇은 안 띄움)
- 사장님 chat_id 외의 메시지는 무시
- 분당 12회 / 일일 60회 자동 처리 한도 (환경변수로 조정)
- 위험 키워드는 절대 자동 실행 안 함
- 외부 채널 자동 반영 — 없음
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from dotenv import dotenv_values

from . import hermes_memory as memory
from . import nl_command
from .paths import ROOT


# ──────────────────────────────────────────────
# 토큰/owner 로딩 — 값은 절대 노출하지 않음
# ──────────────────────────────────────────────

def _load_env() -> Dict[str, str]:
    env_path = ROOT / ".env"
    if env_path.exists():
        try:
            return dotenv_values(env_path) or {}
        except Exception:
            return {}
    return {}


def get_bot_token() -> Optional[str]:
    tok = os.environ.get("TELEGRAM_BOT_TOKEN")
    if tok and tok.strip():
        return tok.strip()
    env = _load_env()
    v = env.get("TELEGRAM_BOT_TOKEN")
    return v.strip() if v and v.strip() else None


def get_owner_chat_id() -> Optional[int]:
    raw = os.environ.get("TELEGRAM_OWNER_CHAT_ID")
    if not raw:
        env = _load_env()
        raw = env.get("TELEGRAM_OWNER_CHAT_ID")
    if not raw or not str(raw).strip():
        return None
    try:
        return int(str(raw).strip())
    except ValueError:
        return None


def credentials_ready() -> bool:
    """봇 토큰과 owner chat id가 모두 있는지. 값은 안 보여줌."""
    return bool(get_bot_token()) and (get_owner_chat_id() is not None)


# ──────────────────────────────────────────────
# 텔레그램 전송 (urllib만 사용 — 의존성 0)
# ──────────────────────────────────────────────

import urllib.error
import urllib.parse
import urllib.request


def telegram_send(text: str, *, chat_id: Optional[int] = None) -> Dict[str, Any]:
    """텔레그램 봇으로 메시지 전송. 토큰 없으면 dry-run dict 반환."""
    token = get_bot_token()
    target = chat_id if chat_id is not None else get_owner_chat_id()
    if not token or target is None:
        return {"sent": False, "dry_run": True, "reason": "토큰 또는 owner_chat_id 미설정"}
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": target,
        "text": text[:3900],
        "disable_web_page_preview": "true",
    }).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8", errors="replace")
        memory.record_outbound(text, to_chat_id=target, success=True)
        return {"sent": True, "to": target, "body_head": body[:80]}
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as e:
        memory.record_outbound(text, to_chat_id=target, success=False, reason=str(e)[:80])
        return {"sent": False, "reason": str(e)[:120]}


# ──────────────────────────────────────────────
# 인바운드 처리 — 메시지 한 건 처리
# ──────────────────────────────────────────────

@dataclass
class HermesHandling:
    text: str
    plan_intent: str
    plan_label: str
    safe_to_run: bool
    approval_path: Optional[str]
    reply: str
    auto_executed: bool
    rate_blocked: bool = False
    rate_reason: str = ""


def handle_inbound(
    text: str,
    *,
    from_chat_id: int,
    from_user: str = "",
    message_id: int = 0,
    auto_execute: bool = True,
) -> HermesHandling:
    """텔레그램에서 받은 메시지 한 건을 안전하게 처리."""
    # 1) inbox 기록 + 선호 학습
    memory.record_inbound(text, from_chat_id=from_chat_id, from_user=from_user, message_id=message_id)
    memory.remember_command(text)

    # 2) 의도/위험/라우팅 해석
    plan = nl_command.interpret(text)

    # 3) 위험 키워드 → 자동 실행 안 함
    if not plan.safe_to_run:
        reply = (
            "⚠ 위험 키워드가 포함된 요청입니다. "
            "09_approval 파일을 만들어 두었고, 실제 실행은 사장님 승인 후 직접 진행해 주세요.\n"
            f"\n의도: {plan.intent} — {plan.label}\n승인 파일: {plan.approval_path}"
        )
        memory.record_decision(
            f"위험 명령 차단: {text[:60]}",
            intent=plan.intent,
            artifact_path=plan.approval_path or "",
            safe=False,
            auto_executed=False,
        )
        return HermesHandling(
            text=text,
            plan_intent=plan.intent,
            plan_label=plan.label,
            safe_to_run=False,
            approval_path=plan.approval_path,
            reply=reply,
            auto_executed=False,
        )

    # 4) CLI 매핑 없으면 안내
    if not plan.cli:
        reply = (
            f"의도가 모호합니다 ({plan.intent}). 좀 더 구체적으로 알려주세요. "
            f"예: '고스틱 광고 만들어줘', '네이버광고 분석해줘'."
        )
        return HermesHandling(
            text=text,
            plan_intent=plan.intent,
            plan_label=plan.label,
            safe_to_run=True,
            approval_path=None,
            reply=reply,
            auto_executed=False,
        )

    # 5) rate limit
    if auto_execute:
        ok, reason = memory.check_and_count()
        if not ok:
            reply = (
                f"⏱ {reason}\n자동 실행을 잠시 중단합니다. "
                f"의도는 인식했으니 사장님이 직접 CLI 실행하셔도 됩니다:\n"
                f"  python -m ai_company.main {' '.join(plan.cli)}"
            )
            return HermesHandling(
                text=text, plan_intent=plan.intent, plan_label=plan.label,
                safe_to_run=True, approval_path=None, reply=reply,
                auto_executed=False, rate_blocked=True, rate_reason=reason,
            )

    # 6) CLI 실행
    auto_executed = False
    output = ""
    if auto_execute:
        try:
            full = [sys.executable, "-m", "ai_company.main", *plan.cli]
            result = subprocess.run(
                full, cwd=ROOT, capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=120,
            )
            output = (result.stdout or "").strip()
            if result.returncode != 0:
                output = (output + "\n" + (result.stderr or "").strip()).strip()
                auto_executed = False
            else:
                auto_executed = True
        except Exception as e:
            output = f"실행 오류: {e}"
            auto_executed = False

    reply_head = f"의도: {plan.intent} — {plan.label}\n"
    if auto_executed:
        # 결과 길이 절제 — 저장 경로 위주
        snippet_lines: List[str] = []
        for line in (output.splitlines() or [""])[:12]:
            snippet_lines.append(line)
        reply = (
            "✅ 자동 실행 완료\n"
            + reply_head
            + "결과 요약:\n" + "\n".join(snippet_lines)
        )[:3500]
    else:
        reply = (
            "준비 완료 (자동 실행 X)\n"
            + reply_head
            + "사장님이 직접 실행: python -m ai_company.main " + " ".join(plan.cli)
        )

    memory.record_decision(
        f"자동 실행: {text[:60]}" if auto_executed else f"준비만: {text[:60]}",
        intent=plan.intent,
        artifact_path="",
        safe=True,
        auto_executed=auto_executed,
    )
    return HermesHandling(
        text=text, plan_intent=plan.intent, plan_label=plan.label,
        safe_to_run=True, approval_path=None, reply=reply,
        auto_executed=auto_executed,
    )


def handle_and_reply(
    text: str,
    *,
    from_chat_id: int,
    from_user: str = "",
    message_id: int = 0,
    auto_execute: bool = True,
) -> HermesHandling:
    """인바운드 처리 + 결과를 텔레그램으로 자동 회신."""
    result = handle_inbound(
        text,
        from_chat_id=from_chat_id,
        from_user=from_user,
        message_id=message_id,
        auto_execute=auto_execute,
    )
    if get_bot_token() and get_owner_chat_id() is not None:
        telegram_send(result.reply, chat_id=from_chat_id)
    return result


# ──────────────────────────────────────────────
# 봇 폴링 루프 (long-poll, 의존성 0)
# ──────────────────────────────────────────────

def _telegram_get_updates(token: str, offset: int, timeout: int = 25) -> Optional[List[Dict[str, Any]]]:
    url = f"https://api.telegram.org/bot{token}/getUpdates?timeout={timeout}&offset={offset}"
    try:
        with urllib.request.urlopen(url, timeout=timeout + 5) as resp:
            body = json.loads(resp.read().decode("utf-8", errors="replace"))
        if not body.get("ok"):
            return None
        return body.get("result") or []
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, json.JSONDecodeError):
        return None


def run_bot_loop(
    *,
    auto_execute: bool = True,
    long_poll_seconds: int = 25,
    stop_after_seconds: Optional[int] = None,
) -> None:
    """장기 실행 루프. 사장님 PC에서 백그라운드로 돌리도록 설계.

    stop_after_seconds: 테스트/디버그용 자동 종료. None이면 무한 루프.
    """
    token = get_bot_token()
    owner = get_owner_chat_id()
    if not token or owner is None:
        # 자격 미설정 — dry-run 안내
        memory.record_outbound(
            "Hermes 봇 시작 시도 — TELEGRAM_BOT_TOKEN/TELEGRAM_OWNER_CHAT_ID 미설정으로 종료",
            to_chat_id=0, success=False, reason="missing-credentials",
        )
        return

    started = time.time()
    offset = 0
    while True:
        if stop_after_seconds and (time.time() - started) > stop_after_seconds:
            return
        updates = _telegram_get_updates(token, offset, timeout=long_poll_seconds)
        if updates is None:
            time.sleep(2)
            continue
        for u in updates:
            offset = max(offset, int(u.get("update_id", 0)) + 1)
            msg = u.get("message") or u.get("edited_message") or {}
            chat = msg.get("chat") or {}
            chat_id = chat.get("id")
            text = (msg.get("text") or "").strip()
            user = (msg.get("from") or {}).get("username") or ""
            if not text or chat_id is None:
                continue
            # owner 검사
            if int(chat_id) != owner:
                # 사장님 외의 메시지 — 응답 안 함, inbox에 흔적만 (보안 로그)
                memory.record_inbound(
                    text, from_chat_id=int(chat_id), from_user=str(user)[:32],
                    message_id=int(msg.get("message_id") or 0),
                    status="ignored_non_owner",
                )
                continue
            try:
                handle_and_reply(
                    text,
                    from_chat_id=int(chat_id),
                    from_user=str(user)[:32],
                    message_id=int(msg.get("message_id") or 0),
                    auto_execute=auto_execute,
                )
            except Exception as e:
                telegram_send(f"⚠ Hermes 내부 오류: {e}", chat_id=int(chat_id))


# ──────────────────────────────────────────────
# 종합 상태 — UI/CLI/서버에서 사용
# ──────────────────────────────────────────────

def status_summary() -> Dict[str, Any]:
    return {
        "credentials_ready": credentials_ready(),
        "memory": memory.status_summary(),
        "external_call": False,  # 이 함수 자체는 호출 안 함
    }


__all__ = [
    "credentials_ready",
    "get_bot_token",
    "get_owner_chat_id",
    "telegram_send",
    "handle_inbound",
    "handle_and_reply",
    "run_bot_loop",
    "status_summary",
    "HermesHandling",
]
