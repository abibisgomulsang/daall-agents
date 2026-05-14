"""의견 충돌 감지 + 표결 + CEO 판단.

2라운드 답변에서 동의/반대/보완 키워드를 자동 추출해 단순 표결을 진행한다.
표결 동률이면 CEO 페르소나가 결정한다 (LLM 호출 1회).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List


# 한국어 입장 신호어
AGREE_WORDS = ("동의", "찬성", "맞", "그대로", "수용", "괜찮", "찬", "공감")
DISAGREE_WORDS = ("반대", "다르게 생각", "동의하지 않", "반박", "수정 필요", "재고", "보완 필요", "위험")


@dataclass
class VoteResult:
    agree: List[str]
    disagree: List[str]
    abstain: List[str]
    conflict: bool
    winner: str         # "agree" | "disagree" | "tie"
    note: str = ""


def _stance(text: str) -> str:
    """텍스트 한 줄의 입장 분류. agree/disagree/abstain."""
    if not text:
        return "abstain"
    t = text.lower()
    # 빨리 일치하는 패턴 우선
    if any(w in text for w in DISAGREE_WORDS):
        return "disagree"
    if any(w in text for w in AGREE_WORDS):
        return "agree"
    return "abstain"


def tally(round2: Dict[str, str]) -> VoteResult:
    """라운드2(반박/동조) 답변 dict {persona_key: text} → 표결 결과."""
    agree: List[str] = []
    disagree: List[str] = []
    abstain: List[str] = []
    for key, text in round2.items():
        st = _stance(text or "")
        if st == "agree":
            agree.append(key)
        elif st == "disagree":
            disagree.append(key)
        else:
            abstain.append(key)
    conflict = bool(agree) and bool(disagree)
    if len(agree) > len(disagree):
        winner = "agree"
    elif len(disagree) > len(agree):
        winner = "disagree"
    else:
        winner = "tie"
    return VoteResult(
        agree=agree,
        disagree=disagree,
        abstain=abstain,
        conflict=conflict,
        winner=winner,
        note=f"동의 {len(agree)}, 반대 {len(disagree)}, 기권 {len(abstain)}",
    )


def render_vote(vote: VoteResult) -> str:
    return (
        "## 표결 결과\n"
        f"- 동의: {', '.join(vote.agree) or '없음'}\n"
        f"- 반대: {', '.join(vote.disagree) or '없음'}\n"
        f"- 기권: {', '.join(vote.abstain) or '없음'}\n"
        f"- 충돌 여부: {'있음' if vote.conflict else '없음'}\n"
        f"- 1차 결론: {vote.winner}\n"
        f"- 비고: {vote.note}"
    )


__all__ = ["VoteResult", "tally", "render_vote"]
