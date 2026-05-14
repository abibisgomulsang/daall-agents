"""엔터프라이즈 자율 모드 — 사장님이 큰 목표만 주면 직원들이 알아서.

영상에서 본 "엔터프라이즈 모드" 컨셉:
  사장님: "월 수익 1천만원 목표"
     ↓
  CEO가 일일 KPI 점검
  → 직원 회의 자동 소집 (멀티 에이전트 토론)
  → 산출물 생성
  → 09_approval 자동 생성
  → 사장님 검토 후 실행

본 모듈은 **하루 1회 점검 사이클**을 정의한다. 사장님이 자율 모드 ON 하면
cron 또는 수동 호출로 매일 실행되어 회사가 알아서 굴러간다.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from . import goals, hermes_memory
from .multi_agent_meeting import run_multi_meeting
from .paths import ROOT
from .utils import now_stamp, write_report


@dataclass
class DailyCheckResult:
    date: str
    goal_active: bool
    goal_target: str
    kpi_gap_summary: str
    actions_decided: List[str]
    meeting_path: Optional[str]
    approval_path: Optional[str]


def _build_kpi_summary(goal_status: dict) -> tuple[str, List[str]]:
    """KPI 격차를 분석 → 사람이 읽는 문장 + 부족한 항목 리스트."""
    if not goal_status.get("active"):
        return "활성 목표 없음", []
    kpis = goal_status.get("kpis") or []
    if not kpis:
        return "KPI 미설정", []
    lines: List[str] = []
    gaps: List[str] = []
    for k in kpis:
        name = k.get("name", "?")
        current = k.get("current", 0)
        target = k.get("target", 0)
        pct = k.get("percent", 0)
        lines.append(f"- {name}: {current} / {target} ({pct}%)")
        try:
            if float(target) > 0 and float(pct) < 70:
                gaps.append(f"{name} ({pct}%)")
        except (TypeError, ValueError):
            pass
    summary = " · ".join(lines)
    return summary, gaps


def _select_topic_for_today(goal_status: dict, gaps: List[str]) -> Optional[str]:
    if not goal_status.get("active"):
        return None
    if not gaps:
        return f"{goal_status['target']} — 현재 페이스 유지 위한 일일 점검"
    return (
        f"{goal_status['target']} — KPI 격차 회복 회의 "
        f"(부족 항목: {', '.join(gaps[:3])})"
    )


def run_daily_cycle(*, live: bool = False) -> DailyCheckResult:
    """엔터프라이즈 자율 모드 1일 사이클."""
    today = datetime.now().strftime("%Y-%m-%d")
    goal_status = goals.status_summary()
    kpi_text, gaps = _build_kpi_summary(goal_status)
    topic = _select_topic_for_today(goal_status, gaps)

    meeting_path: Optional[str] = None
    actions: List[str] = []
    approval_path: Optional[str] = None

    if topic:
        # 멀티 에이전트 회의 자동 소집
        try:
            meeting = run_multi_meeting(topic, live=live, max_members=5)
            md = meeting.to_markdown()
            path = write_report(
                ROOT / "10_meetings", "enterprise_daily", md
            )
            meeting_path = str(path)

            # CEO 결론에서 다음 행동 추출 (단순 룰: 줄 첫 머리 동사형)
            for line in meeting.ceo_summary.split("\n"):
                line = line.strip(" -*0123456789.")
                if line and len(line) > 6 and len(line) < 100:
                    actions.append(line)
            actions = actions[:5]
        except Exception as e:
            actions.append(f"회의 호출 실패: {e}")

        # 09_approval 자동 생성 (사장님 검토 요청)
        from .approval import format_approval_request
        approval_body = format_approval_request(
            task_name=f"엔터프라이즈 일일 사이클 — {today}",
            target=f"활성 목표: {goal_status.get('target', '미설정')}",
            before="현재 상태 유지",
            after=f"오늘 결정된 액션 {len(actions)}건 실행 (사장님 확인 후)",
            expected_effect="KPI 격차 회복",
            risks=[
                "자동 실행 X — 사장님 검토 후 직접 진행",
                f"KPI 부족 항목: {', '.join(gaps) or '없음'}",
            ],
            rollback="승인 안 하면 자동으로 다음날 사이클",
            source_markdown=f"# 일일 KPI\n\n{kpi_text}\n\n# 회의 결과\n\n{meeting_path}",
        )
        approval_path = str(
            write_report(
                ROOT / "09_approval",
                f"APPROVAL_REQUIRED_enterprise_daily_{today}",
                approval_body,
            )
        )

    # Hermes 메모리에 일일 결정 기록
    try:
        hermes_memory.record_decision(
            f"엔터프라이즈 일일 — {topic or '목표 없음'}",
            intent="enterprise_daily",
            artifact_path=meeting_path or "",
            safe=True,
            auto_executed=False,
        )
    except Exception:
        pass

    return DailyCheckResult(
        date=today,
        goal_active=bool(goal_status.get("active")),
        goal_target=goal_status.get("target", ""),
        kpi_gap_summary=kpi_text,
        actions_decided=actions,
        meeting_path=meeting_path,
        approval_path=approval_path,
    )


def write_daily_report(result: DailyCheckResult) -> Path:
    lines = [
        f"# 엔터프라이즈 일일 사이클 — {result.date}",
        "",
        f"- 목표 활성 여부: {'예' if result.goal_active else '아니오 (목표 미설정)'}",
        f"- 목표: {result.goal_target or '미설정'}",
        "",
        "## KPI 격차",
        "",
        result.kpi_gap_summary,
        "",
        "## 오늘 결정된 액션",
        "",
    ]
    if result.actions_decided:
        for a in result.actions_decided:
            lines.append(f"- {a}")
    else:
        lines.append("- (없음)")
    if result.meeting_path:
        lines.extend(["", "## 회의록", f"- {result.meeting_path}"])
    if result.approval_path:
        lines.extend(["", "## 사장님 승인 대기", f"- {result.approval_path}"])
    lines.extend([
        "",
        "## 안전 확인",
        "- 외부 채널 자동 반영: 없음",
        "- 모든 실행은 사장님 09_approval 검토 후 직접 진행",
    ])
    return write_report(
        ROOT / "08_reports", f"enterprise_daily_{result.date}", "\n".join(lines)
    )


__all__ = ["DailyCheckResult", "run_daily_cycle", "write_daily_report"]
