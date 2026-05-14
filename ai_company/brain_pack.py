"""브레인 팩 — 도메인 지식 주입 시스템.

`brain_packs/<pack_name>/KNOWLEDGE.md` 파일을 읽어 페르소나 시스템 프롬프트에
런타임으로 주입한다. 영상에서 본 "매트릭스 지식 주입"의 단순 버전.

각 직원은 자기에게 매핑된 brain pack을 자동으로 컨텍스트에 받는다.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from .paths import ROOT


BRAIN_PACKS_DIR = ROOT / "brain_packs"


# 직원 페르소나 키 → 자동 주입할 브레인 팩 목록
DEFAULT_AGENT_PACKS: Dict[str, List[str]] = {
    "marketing":  ["marketing", "cat_business"],
    "sns":        ["marketing", "video_editing", "cat_business"],
    "data":       ["naver_ads", "cat_business"],
    "naverads":   ["naver_ads", "cat_business"],
    "review":     ["marketing", "cat_business"],
    "psy":        ["cat_business"],
    "product":    ["cat_business"],
    "video":      ["video_editing", "marketing"],
    "ceo":        ["cat_business", "marketing"],
    "suyeong":    ["cat_business"],
}


def list_packs() -> List[str]:
    if not BRAIN_PACKS_DIR.exists():
        return []
    return sorted(p.name for p in BRAIN_PACKS_DIR.iterdir() if p.is_dir())


def load_pack(name: str) -> Optional[str]:
    """단일 브레인 팩의 KNOWLEDGE.md 내용 반환. 없으면 None."""
    md_path = BRAIN_PACKS_DIR / name / "KNOWLEDGE.md"
    if not md_path.exists():
        return None
    try:
        return md_path.read_text(encoding="utf-8")
    except Exception:
        return None


def packs_for_agent(agent_key: str) -> List[str]:
    """직원 키에 매핑된 브레인 팩 이름 목록."""
    return list(DEFAULT_AGENT_PACKS.get(agent_key, []))


def assemble_knowledge(agent_key: str, *, max_chars: int = 4000) -> str:
    """직원에게 주입할 종합 지식 텍스트. 너무 길면 잘림."""
    parts: List[str] = []
    for pack_name in packs_for_agent(agent_key):
        content = load_pack(pack_name)
        if not content:
            continue
        parts.append(f"=== [{pack_name.upper()} 브레인 팩] ===\n{content}")
    text = "\n\n".join(parts)
    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n... (지식 잘림 — max_chars 초과)"
    return text


def augment_system_prompt(base: str, agent_key: str, *, enabled: bool = True) -> str:
    """페르소나 시스템 프롬프트 + 브레인 팩 결합."""
    if not enabled:
        return base
    knowledge = assemble_knowledge(agent_key)
    if not knowledge:
        return base
    return (
        base.rstrip()
        + "\n\n--- 주입된 브레인 팩 (도메인 지식) ---\n"
        + knowledge
        + "\n--- 끝 ---\n위 지식을 답변에 반영해라. 다만 외워서 답하는 게 아니라 자연스럽게 사용."
    )


def status_summary() -> Dict[str, object]:
    """CLI/UI용 종합 상태."""
    packs = list_packs()
    return {
        "brain_packs_dir": str(BRAIN_PACKS_DIR),
        "pack_count": len(packs),
        "packs": [
            {
                "name": p,
                "size_chars": len(load_pack(p) or ""),
                "agents": [k for k, v in DEFAULT_AGENT_PACKS.items() if p in v],
            }
            for p in packs
        ],
        "agent_mapping": DEFAULT_AGENT_PACKS,
    }


__all__ = [
    "BRAIN_PACKS_DIR",
    "DEFAULT_AGENT_PACKS",
    "list_packs",
    "load_pack",
    "packs_for_agent",
    "assemble_knowledge",
    "augment_system_prompt",
    "status_summary",
]
