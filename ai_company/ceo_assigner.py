"""CEO LLM이 작업을 분석해 회의 멤버를 결정한다.

키워드 매칭 대신 CEO 페르소나(Claude 우선, Ollama 폴백)에게 직접 묻는다.
실패 시 키워드 기반 폴백을 사용한다.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import List, Optional

from .agent_persona import CEO_PERSONA, DEFAULT_MEETING_KEYS, PERSONAS_BY_KEY, PERSONAS
from .multi_agent_runtime import call_persona


# 폴백용 키워드 매칭
FALLBACK_OWNER_MAP = [
    (("비디오", "영상", "편집", "타임라인", "컷 편집", "자막 편집", "ffmpeg", "MoviePy", "쇼츠 편집"), "video"),
    (("회의", "토론", "결정"), "data"),
    (("광고", "후킹", "카피"), "marketing"),
    (("릴스", "썸네일", "SNS", "인스타"), "sns"),
    (("이미지", "디자인", "비주얼"), "marketing"),
    (("스마트스토어", "상세페이지", "상품", "리필", "세트"), "product"),
    (("네이버광고", "ROAS", "CTR", "CPC", "키워드"), "naverads"),
    (("CSV", "엑셀", "데이터", "매출", "분석", "리포트"), "data"),
    (("검수", "검토", "리뷰", "확인", "체크"), "review"),
    (("심리", "고민", "공감"), "psy"),
]


@dataclass
class CEOAssignment:
    task: str
    essence: str
    primary_owner_key: str
    member_keys: List[str]
    reason: str
    used_llm: bool


def _fallback_owner(task: str) -> str:
    for kws, key in FALLBACK_OWNER_MAP:
        if any(k in task for k in kws):
            return key
    return "data"


def _build_members(primary_key: str) -> List[str]:
    # 1순위 + 보조 직원 자동 선택
    base = [primary_key]
    # 광고/마케팅 작업이면 검수·심리·SNS 보조
    if primary_key in ("marketing", "naverads"):
        for k in ("data", "psy", "sns", "review"):
            if k not in base:
                base.append(k)
    elif primary_key == "sns":
        for k in ("marketing", "review", "data"):
            if k not in base:
                base.append(k)
    elif primary_key == "product":
        for k in ("data", "psy", "review"):
            if k not in base:
                base.append(k)
    elif primary_key == "data":
        for k in ("psy", "naverads", "review"):
            if k not in base:
                base.append(k)
    elif primary_key == "review":
        for k in ("data", "psy", "marketing"):
            if k not in base:
                base.append(k)
    elif primary_key == "video":
        # 비디오 작업은 SNS·마케팅·검수와 한 팀
        for k in ("sns", "marketing", "review"):
            if k not in base:
                base.append(k)
    elif primary_key == "sns":
        # SNS 작업이면 비디오 AI도 자동 동참
        for k in ("video", "marketing", "review"):
            if k not in base:
                base.append(k)
    else:
        for k in DEFAULT_MEETING_KEYS:
            if k not in base and len(base) < 5:
                base.append(k)
    return base[:5]


def _parse_assignment_json(raw: str) -> Optional[dict]:
    if not raw:
        return None
    # 첫 JSON 객체만 추출
    m = re.search(r"\{[\s\S]*?\}", raw)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def assign(task: str, *, live: bool = False) -> CEOAssignment:
    """CEO LLM에게 회의 멤버/책임자를 받는다. 실패 시 키워드 폴백."""
    if not task or not task.strip():
        raise ValueError("작업 설명이 비어 있습니다.")

    # 가능한 멤버 후보 명단을 알려주고 LLM이 골라야 한다
    candidates = ", ".join(f'{p.key}({p.name})' for p in PERSONAS)
    prompt = (
        f"회사 직원 후보: {candidates}.\n"
        f"사장님 요청: {task}\n\n"
        "이 작업의 본질이 무엇이고 회의에 누구를 부를지 정해라. "
        "오직 JSON 한 객체로만 답하라(다른 문장 금지):\n"
        '{"essence":"<한 줄 요약>","primary_owner":"<key>","members":["<key>", ...],"reason":"<짧은 이유>"}'
    )

    used_llm = False
    parsed: Optional[dict] = None
    if live:
        text, _provider = call_persona(
            CEO_PERSONA, prompt, round_num=0, live=True, topic=task
        )
        if text:
            parsed = _parse_assignment_json(text)
            if parsed:
                used_llm = True

    if not parsed:
        # 폴백: 키워드 기반
        primary = _fallback_owner(task)
        members = _build_members(primary)
        return CEOAssignment(
            task=task,
            essence="키워드 매칭 기반 (CEO LLM 미사용 또는 응답 실패)",
            primary_owner_key=primary,
            member_keys=members,
            reason="LLM 실패/오프라인 모드 — 키워드 매칭으로 책임자 선정",
            used_llm=False,
        )

    primary = parsed.get("primary_owner")
    if primary not in PERSONAS_BY_KEY:
        primary = _fallback_owner(task)
    members_raw = parsed.get("members") or []
    members = [m for m in members_raw if m in PERSONAS_BY_KEY and m != "ceo"]
    if not members:
        members = _build_members(primary)
    if primary not in members:
        members.insert(0, primary)
    members = members[:6]

    return CEOAssignment(
        task=task,
        essence=str(parsed.get("essence") or "")[:200],
        primary_owner_key=primary,
        member_keys=members,
        reason=str(parsed.get("reason") or "")[:200],
        used_llm=used_llm,
    )


__all__ = ["CEOAssignment", "assign"]
