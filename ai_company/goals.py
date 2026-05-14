"""목표(Goal) 시스템 — 영상에서 본 "월 수익 1천만원" 같은 목표 설정.

`11_memory/goals/active.json` 에 단일 활성 목표를 저장한다.
CEO 오케스트레이터가 매일 이 목표를 참조해서 작업 우선순위를 결정한다.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .paths import ROOT


GOALS_DIR = ROOT / "11_memory" / "goals"
ACTIVE_PATH = GOALS_DIR / "active.json"
HISTORY_PATH = GOALS_DIR / "history.jsonl"


@dataclass
class Goal:
    target: str                       # "월 매출 1000만원"
    deadline: str = ""                # ISO 날짜 또는 빈 문자열
    kpis: List[dict] = field(default_factory=list)
    set_at: str = ""
    progress_notes: List[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        lines = [f"# 활성 목표", "", f"**목표:** {self.target}"]
        if self.deadline:
            lines.append(f"**기한:** {self.deadline}")
        if self.set_at:
            lines.append(f"**설정 시각:** {self.set_at}")
        if self.kpis:
            lines.append("\n## KPI")
            for k in self.kpis:
                lines.append(
                    f"- **{k.get('name')}**: 현재 {k.get('current', 0)} / 목표 {k.get('target', 0)} "
                    f"({_percent(k)}%)"
                )
        if self.progress_notes:
            lines.append("\n## 진행 노트")
            for n in self.progress_notes[-10:]:
                lines.append(f"- {n}")
        return "\n".join(lines)


def _percent(kpi: dict) -> float:
    try:
        cur = float(kpi.get("current", 0))
        tgt = float(kpi.get("target", 0))
        if tgt <= 0:
            return 0.0
        return round((cur / tgt) * 100, 1)
    except (TypeError, ValueError):
        return 0.0


def _ensure() -> None:
    GOALS_DIR.mkdir(parents=True, exist_ok=True)


def set_goal(
    target: str,
    *,
    deadline: str = "",
    kpis: Optional[List[dict]] = None,
) -> Goal:
    _ensure()
    # 기존 목표가 있으면 history에 보관
    prev = _read_active()
    if prev:
        _archive(prev)
    goal = Goal(
        target=target,
        deadline=deadline or "",
        kpis=kpis or _default_kpis_from_target(target),
        set_at=datetime.now().isoformat(timespec="seconds"),
    )
    ACTIVE_PATH.write_text(
        json.dumps(asdict(goal), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return goal


def _archive(goal_dict: dict) -> None:
    _ensure()
    record = dict(goal_dict)
    record["archived_at"] = datetime.now().isoformat(timespec="seconds")
    with HISTORY_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _read_active() -> Optional[dict]:
    if not ACTIVE_PATH.exists():
        return None
    try:
        return json.loads(ACTIVE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None


def get_goal() -> Optional[Goal]:
    raw = _read_active()
    if not raw:
        return None
    return Goal(
        target=raw.get("target", ""),
        deadline=raw.get("deadline", ""),
        kpis=raw.get("kpis") or [],
        set_at=raw.get("set_at", ""),
        progress_notes=raw.get("progress_notes") or [],
    )


def update_kpi(name: str, current: float) -> Optional[Goal]:
    """단일 KPI의 current 값을 갱신."""
    goal = get_goal()
    if not goal:
        return None
    for k in goal.kpis:
        if k.get("name") == name:
            k["current"] = current
            break
    else:
        goal.kpis.append({"name": name, "current": current, "target": 0})
    ACTIVE_PATH.write_text(
        json.dumps(asdict(goal), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return goal


def add_note(note: str) -> Optional[Goal]:
    goal = get_goal()
    if not goal:
        return None
    goal.progress_notes.append(
        f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {note}"
    )
    ACTIVE_PATH.write_text(
        json.dumps(asdict(goal), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return goal


def _default_kpis_from_target(target: str) -> List[dict]:
    """'월 매출 1000만원' 같은 표현에서 KPI 자동 생성."""
    kpis: List[dict] = []
    lower = target.lower()
    if any(k in target for k in ("매출", "수익", "월 매출")):
        # 숫자 추출 시도
        import re
        m = re.search(r"(\d[\d,]*)\s*만", target)
        target_value = 0
        if m:
            target_value = int(m.group(1).replace(",", "")) * 10000
        kpis.append({"name": "월 매출 (KRW)", "current": 0, "target": target_value})
    if any(k in target for k in ("주문", "건수", "판매")):
        kpis.append({"name": "월 주문 건수", "current": 0, "target": 0})
    if "팔로워" in target or "구독" in target:
        kpis.append({"name": "팔로워/구독자", "current": 0, "target": 0})
    if not kpis:
        kpis.append({"name": target, "current": 0, "target": 0})
    return kpis


def status_summary() -> dict:
    goal = get_goal()
    if not goal:
        return {"active": False}
    return {
        "active": True,
        "target": goal.target,
        "deadline": goal.deadline,
        "kpis": [
            {**k, "percent": _percent(k)} for k in goal.kpis
        ],
        "set_at": goal.set_at,
        "note_count": len(goal.progress_notes),
    }


__all__ = [
    "Goal",
    "set_goal",
    "get_goal",
    "update_kpi",
    "add_note",
    "status_summary",
    "ACTIVE_PATH",
]
