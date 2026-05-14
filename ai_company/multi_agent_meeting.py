"""멀티 에이전트 3라운드 토론.

흐름:
    [라운드 1] 각 직원이 자기 모델로 의견 (개별 호출)
    [라운드 2] 다른 직원 의견 다 보고 반박/동조 (개별 호출, 같은 모델)
    표결      voting.tally(라운드2) — 충돌 시 CEO가 판단
    [라운드 3] CEO 종합 결론 (Claude 우선, Ollama 폴백)

비용 보호:
- 회의 시작 전 추정 비용 + 일일/월 캡 검사
- 캡 초과 위험 시 force_ollama=True 로 강등 (모두 무료)
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from . import ceo_assigner, voting, usage_caps, usage_log
from .agent_persona import CEO_PERSONA, get_persona, AgentPersona
from .multi_agent_runtime import call_persona
from .paths import ROOT
from .utils import now_stamp


@dataclass
class MeetingTurn:
    persona_key: str
    persona_name: str
    text: str
    provider: str


@dataclass
class MultiAgentMeetingResult:
    topic: str
    assignment: ceo_assigner.CEOAssignment
    round1: List[MeetingTurn]
    round2: List[MeetingTurn]
    vote: voting.VoteResult
    ceo_summary: str
    ceo_summary_provider: str
    force_ollama: bool
    created_at: str
    estimated_cost_krw: float = 0.0

    def to_markdown(self) -> str:
        a = self.assignment
        lines = ["# 멀티 에이전트 회의 결과", ""]
        lines.append(f"- 시각: {self.created_at}")
        lines.append(f"- 주제: {self.topic}")
        lines.append(f"- 본질(CEO): {a.essence}")
        lines.append(f"- 1차 책임: **{get_persona(a.primary_owner_key).name}**")
        lines.append(f"- 회의 멤버: " + ", ".join(get_persona(k).name for k in a.member_keys))
        lines.append(f"- CEO LLM 분배 사용: {'예' if a.used_llm else '아니오 (키워드 폴백)'}")
        lines.append(f"- 비용 보호 강등: {'적용 (전부 Ollama)' if self.force_ollama else '없음'}")
        lines.append(f"- 추정 비용: ₩{self.estimated_cost_krw:.0f}")
        lines.append("")
        lines.append("## 라운드 1 — 각자 의견")
        for t in self.round1:
            lines.append(f"### {t.persona_name}  _({t.provider})_")
            lines.append(t.text or "_응답 없음_")
            lines.append("")
        lines.append("## 라운드 2 — 다른 의견 보고 반박/동조")
        for t in self.round2:
            lines.append(f"### {t.persona_name}  _({t.provider})_")
            lines.append(t.text or "_응답 없음_")
            lines.append("")
        lines.append(voting.render_vote(self.vote))
        lines.append("")
        lines.append("## 라운드 3 — CEO 종합 결론")
        lines.append(f"_(공급자: {self.ceo_summary_provider})_")
        lines.append("")
        lines.append(self.ceo_summary or "_응답 없음_")
        lines.append("")
        lines.append("## 승인 흐름")
        lines.append("- 실제 외부 채널 반영(스마트스토어/네이버광고/SNS)은 09_approval 승인 후 사장님이 직접 실행")
        return "\n".join(lines)


def _estimate_cost(members: List[AgentPersona], live: bool) -> float:
    """모든 외부 API 호출이 max_tokens(400) 다 쓴다 가정한 보수적 추정."""
    if not live:
        return 0.0
    total = 0.0
    for p in members:
        for round_n in (1, 2):  # 라운드 1·2
            if p.model_pref == "claude":
                total += usage_log.estimate_text_cost_krw("claude-haiku-4-5-20251001", 150, 400)
            elif p.model_pref == "openai":
                total += usage_log.estimate_text_cost_krw("gpt-4o-mini", 150, 400)
            elif p.model_pref == "gemini":
                total += usage_log.estimate_text_cost_krw("gemini-1.5-flash", 150, 400)
    # CEO 종합도 1회
    total += usage_log.estimate_text_cost_krw("claude-haiku-4-5-20251001", 400, 400)
    return round(total, 2)


def _bullet(turns: List[MeetingTurn], exclude_key: Optional[str] = None) -> str:
    return "\n".join(
        f"- [{t.persona_name}] {t.text}"
        for t in turns
        if t.text and (exclude_key is None or t.persona_key != exclude_key)
    )


def run_multi_meeting(
    topic: str,
    *,
    live: bool = True,
    max_members: int = 6,
) -> MultiAgentMeetingResult:
    if not topic or not topic.strip():
        raise ValueError("회의 주제가 비어 있습니다.")

    # 1. CEO 분배
    assignment = ceo_assigner.assign(topic, live=live)
    member_keys = assignment.member_keys[:max_members]
    members = [get_persona(k) for k in member_keys]

    # 2. 비용 추정 + 캡 검사 → 초과 위험이면 강등
    est = _estimate_cost(members, live)
    ok, reason = usage_caps.check_cap(est)
    force_ollama = False
    if live and not ok:
        force_ollama = True

    # 3. 라운드 1
    round1: List[MeetingTurn] = []
    for p in members:
        prompt = (
            f"회의 주제: {topic}\n\n"
            f"네 역할: {p.name} — {p.role}\n"
            f"네 말투: {p.voice}\n\n"
            "위 주제에 대한 의견과 바로 실행 가능한 제안 1개를 3~5문장으로 한국어로 답해라. "
            "외부 채널 실제 반영은 09_approval 승인 후라고 가정."
        )
        text, provider = call_persona(
            p, prompt, round_num=1, live=live, topic=topic, force_ollama=force_ollama
        )
        round1.append(MeetingTurn(p.key, p.name, text or "", provider))

    # 4. 라운드 2 — 다른 의견 보고 반박/동조
    bullet_all = _bullet(round1)
    round2: List[MeetingTurn] = []
    for p in members:
        others = _bullet(round1, exclude_key=p.key) or "(다른 의견 없음)"
        prompt = (
            f"회의 주제: {topic}\n\n"
            f"다른 직원들의 의견:\n{others}\n\n"
            f"네 입장({p.name} — {p.role})에서 위 의견에 대해 동의/반대/보완을 짧게 답해라. "
            "반박이면 '반대', 동의면 '동의', 보완이면 '보완 필요'라고 첫 단어에 명시. "
            "한국어 3~5문장."
        )
        text, provider = call_persona(
            p, prompt, round_num=2, live=live, topic=topic, force_ollama=force_ollama
        )
        round2.append(MeetingTurn(p.key, p.name, text or "", provider))

    # 5. 표결
    round2_dict = {t.persona_key: t.text for t in round2}
    vote = voting.tally(round2_dict)

    # 6. 라운드 3 — CEO 종합
    bullet_r2 = _bullet(round2)
    vote_md = voting.render_vote(vote)
    ceo_prompt = (
        f"회의 주제: {topic}\n\n"
        f"라운드 1 의견:\n{bullet_all}\n\n"
        f"라운드 2 반박/동조:\n{bullet_r2}\n\n"
        f"{vote_md}\n\n"
        f"CEO로서 위 토론을 4~6문장으로 종합하라. "
        f"충돌이 있으면 누구 의견을 채택할지 명시. "
        f"실행 전 09_approval 승인 흐름을 반드시 명시."
    )
    ceo_text, ceo_provider = call_persona(
        CEO_PERSONA,
        ceo_prompt,
        round_num=3,
        live=live,
        topic=topic,
        force_ollama=force_ollama,
    )

    return MultiAgentMeetingResult(
        topic=topic,
        assignment=assignment,
        round1=round1,
        round2=round2,
        vote=vote,
        ceo_summary=ceo_text or "(CEO 응답 실패 — Ollama 폴백 권장)",
        ceo_summary_provider=ceo_provider,
        force_ollama=force_ollama,
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        estimated_cost_krw=est,
    )


def write_multi_meeting(topic: str, *, live: bool = True) -> tuple[Path, Path]:
    result = run_multi_meeting(topic, live=live)
    folder = ROOT / "10_meetings"
    folder.mkdir(parents=True, exist_ok=True)
    base = now_stamp()
    stamp = base
    suffix = 0
    while (folder / f"multi_meeting_{stamp}.md").exists():
        suffix += 1
        stamp = f"{base}_{suffix:02d}"
    md_path = folder / f"multi_meeting_{stamp}.md"
    json_path = folder / f"multi_meeting_{stamp}.json"
    md_path.write_text(result.to_markdown(), encoding="utf-8")
    json_path.write_text(
        json.dumps(
            {
                "topic": result.topic,
                "created_at": result.created_at,
                "assignment": {
                    "essence": result.assignment.essence,
                    "primary": result.assignment.primary_owner_key,
                    "members": result.assignment.member_keys,
                    "used_llm": result.assignment.used_llm,
                },
                "round1": [t.__dict__ for t in result.round1],
                "round2": [t.__dict__ for t in result.round2],
                "vote": {
                    "agree": result.vote.agree,
                    "disagree": result.vote.disagree,
                    "abstain": result.vote.abstain,
                    "conflict": result.vote.conflict,
                    "winner": result.vote.winner,
                    "note": result.vote.note,
                },
                "ceo_summary_provider": result.ceo_summary_provider,
                "estimated_cost_krw": result.estimated_cost_krw,
                "force_ollama": result.force_ollama,
                "external_call": True,
            },
            ensure_ascii=False, indent=2
        ),
        encoding="utf-8",
    )
    return md_path, json_path


__all__ = [
    "MeetingTurn",
    "MultiAgentMeetingResult",
    "run_multi_meeting",
    "write_multi_meeting",
]
