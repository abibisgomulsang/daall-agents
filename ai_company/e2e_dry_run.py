"""텔레그램 → 라우터 → 회의 → 승인 end-to-end dry-run.

사장님이 텔레그램에 자연어로 명령을 보내는 시나리오의 전 흐름을
단일 보고서로 묶는 모듈이다. **실제 텔레그램 API/외부 호출은 하지 않는다.**

흐름:

    텔레그램 인바운드 (mock)
       ↓
    Hermes 기억 조회 (mock)
       ↓
    nl_command.interpret()
       ↓
    모델 라우터 (NLPlan 내부)
       ↓
    AI 회의 (라우터 통과)
       ↓
    승인 파일 (위험 명령이면)
       ↓
    사장님 알림 메시지 (mock)
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from .meeting import run_routed_meeting, meeting_to_markdown
from .nl_command import interpret as nl_interpret, NLPlan
from .paths import ROOT
from .utils import now_stamp


@dataclass
class E2EStep:
    """단일 단계 로그."""

    name: str
    description: str
    artifact_path: Optional[str] = None
    details: List[str] = field(default_factory=list)


@dataclass
class E2EReport:
    """end-to-end dry-run 전체 보고."""

    inbound_message: str
    steps: List[E2EStep]
    plan: NLPlan
    meeting_md: Optional[str] = None
    boss_notification: str = ""
    created_at: str = ""

    def to_markdown(self) -> str:
        lines: List[str] = []
        lines.append("# 텔레그램 e2e dry-run 보고서")
        lines.append("")
        lines.append(f"- 생성 시각: {self.created_at}")
        lines.append(f"- 인바운드 메시지: {self.inbound_message}")
        lines.append(f"- 분류 의도: **{self.plan.intent}** — {self.plan.label}")
        lines.append(f"- 실행 가능: {'예' if self.plan.safe_to_run else '아니오 (승인 필요)'}")
        if self.plan.routing is not None:
            r = self.plan.routing
            lines.append(
                f"- 모델 라우터 1순위: **{r.primary.model.display_name}** "
                f"({r.primary.model.role}) / 점수 {r.primary.score}"
            )
        lines.append("")
        lines.append("## 단계 로그")
        for idx, step in enumerate(self.steps, 1):
            lines.append(f"### {idx}. {step.name}")
            lines.append(step.description)
            if step.artifact_path:
                lines.append(f"- 산출물: `{step.artifact_path}`")
            for detail in step.details:
                lines.append(f"- {detail}")
            lines.append("")
        lines.append("## 사장님 알림 (mock — 실제 발송 안 함)")
        lines.append("```")
        lines.append(self.boss_notification)
        lines.append("```")
        lines.append("")
        lines.append("## 안전 확인")
        lines.append("- 실제 텔레그램 API 호출 여부: 호출 안 함")
        lines.append("- 실제 외부 발송/업로드/결제 여부: 없음")
        lines.append("- 모든 산출물은 D:\\AI_COMPANY 내부 dry-run 파일")
        return "\n".join(lines)


def _mock_telegram_inbound(message: str) -> dict:
    return {
        "update_id": 0,
        "message": {
            "from": {"id": 0, "username": "boss_dry_run"},
            "chat": {"id": 0, "type": "private"},
            "text": message,
            "date": int(datetime.now().timestamp()),
        },
        "dry_run": True,
        "actual_telegram_call": False,
    }


def _mock_hermes_lookup(message: str) -> dict:
    return {
        "memory_keys_checked": ["사장님 자주 쓰는 명령", "최근 회의 결론", "광고 상태"],
        "matched_memories": [],
        "dry_run": True,
        "note": "Hermes 실제 메모리 조회는 사장님 승인 후 진행. 현재는 빈 결과 mock.",
    }


def _build_boss_notification(plan: NLPlan, meeting_md: Optional[str]) -> str:
    lines: List[str] = []
    lines.append("📬 AI 회사 알림 (사장님)")
    lines.append("")
    lines.append(f"입력: {plan.message}")
    lines.append(f"분류: {plan.intent} — {plan.label}")
    if plan.routing is not None:
        lines.append(
            f"라우터: {plan.routing.primary.model.display_name} "
            f"(점수 {plan.routing.primary.score})"
        )
    if plan.safe_to_run and plan.cli:
        lines.append("상태: dry-run 결과 준비 완료. 사장님 확인 후 실행 권장")
    elif plan.approval_required:
        lines.append("상태: 위험 키워드 포함. 09_approval 파일 생성, 승인 대기")
        if plan.approval_path:
            lines.append(f"승인 파일: {plan.approval_path}")
    else:
        lines.append("상태: CLI 매핑 없음. 자연어를 좀 더 구체적으로 입력")
    if meeting_md:
        lines.append("회의 결과 요약: 10_meetings 폴더 참고")
    return "\n".join(lines)


def build_e2e_report(message: str) -> E2EReport:
    steps: List[E2EStep] = []

    # 1단계: 텔레그램 인바운드 (mock)
    inbound = _mock_telegram_inbound(message)
    steps.append(
        E2EStep(
            name="텔레그램 인바운드 수신",
            description="실제 텔레그램 webhook 대신 mock payload 생성. 실제 호출 없음.",
            details=[
                f"username: {inbound['message']['from']['username']}",
                f"chat_type: {inbound['message']['chat']['type']}",
                f"dry_run: {inbound['dry_run']}",
            ],
        )
    )

    # 2단계: Hermes 기억 조회 (mock)
    hermes = _mock_hermes_lookup(message)
    steps.append(
        E2EStep(
            name="Hermes 기억 조회",
            description="장기 기억/사장님 선호 명령 패턴 조회. 현재는 mock 빈 결과.",
            details=[f"keys checked: {len(hermes['memory_keys_checked'])}", hermes["note"]],
        )
    )

    # 3단계: nl_command 해석 (의도 + 라우터 + 위험 검사 통합)
    plan = nl_interpret(message)
    nl_details = [
        f"의도: {plan.intent} — {plan.label}",
        f"CLI 후보: {' '.join(plan.cli) if plan.cli else '없음'}",
        f"safe_to_run: {plan.safe_to_run}",
    ]
    if plan.risk_keywords:
        nl_details.append(f"위험 키워드: {', '.join(plan.risk_keywords)}")
    steps.append(
        E2EStep(
            name="nl_command.interpret() 호출",
            description="자연어 → 의도 + 모델 라우팅 + 위험 검사 통합 해석.",
            details=nl_details,
        )
    )

    # 4단계: 모델 라우터 (이미 NLPlan 안에 들어 있음)
    if plan.routing is not None:
        r = plan.routing
        router_details = [
            f"1순위: {r.primary.model.display_name} ({r.primary.model.role})",
            f"점수: {r.primary.score}",
        ]
        if r.runners_up:
            router_details.append(
                "후순위: " + ", ".join(rs.model.display_name for rs in r.runners_up)
            )
        steps.append(
            E2EStep(
                name="모델 라우터 결정",
                description="작업 설명을 5개 모델 패널로 점수 라우팅. 실제 API 호출 없음.",
                details=router_details,
            )
        )

    # 5단계: 의도가 회의 계열이면 회의 시뮬레이션
    meeting_md: Optional[str] = None
    if plan.intent in ("meeting", "meeting_fallback", "experiment"):
        result = run_routed_meeting(message[:80])
        meeting_md = meeting_to_markdown(result)
        steps.append(
            E2EStep(
                name="AI 회의 (라우터 통과)",
                description="라우팅 카드 포함 회의 진행. 실제 외부 호출 없음.",
                details=[f"의견 개수: {len(result.opinions)}", "CEO 결론 생성됨"],
            )
        )

    # 6단계: 승인 단계
    if plan.approval_required and plan.approval_path:
        steps.append(
            E2EStep(
                name="승인 파일 자동 생성",
                description="위험 키워드 발견. 09_approval 파일 작성, 자동 실행 차단.",
                artifact_path=plan.approval_path,
            )
        )
    elif plan.safe_to_run:
        steps.append(
            E2EStep(
                name="자동 실행 가능 단계",
                description="안전한 명령이라 --execute 옵션 시 바로 CLI 실행 가능. 이 dry-run에서는 실행 안 함.",
                details=[
                    "실행 명령: python -m ai_company.main " + " ".join(plan.cli)
                ],
            )
        )

    # 7단계: 사장님 알림 (mock)
    notification = _build_boss_notification(plan, meeting_md)
    steps.append(
        E2EStep(
            name="사장님 알림 mock",
            description="실제 텔레그램 발송 대신 알림 문구를 보고서에 첨부. 실제 발송 없음.",
        )
    )

    return E2EReport(
        inbound_message=message,
        steps=steps,
        plan=plan,
        meeting_md=meeting_md,
        boss_notification=notification,
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )


def write_e2e_report(message: str) -> Tuple[Path, Path]:
    """e2e 보고서를 08_reports에 저장."""
    report = build_e2e_report(message)
    folder = ROOT / "08_reports"
    folder.mkdir(parents=True, exist_ok=True)
    base_stamp = now_stamp()
    stamp = base_stamp
    suffix = 0
    while (folder / f"e2e_dry_run_{stamp}.md").exists() or (
        folder / f"e2e_dry_run_{stamp}.json"
    ).exists():
        suffix += 1
        stamp = f"{base_stamp}_{suffix:02d}"
    md_path = folder / f"e2e_dry_run_{stamp}.md"
    json_path = folder / f"e2e_dry_run_{stamp}.json"
    md_path.write_text(report.to_markdown(), encoding="utf-8")
    payload = {
        "inbound_message": report.inbound_message,
        "created_at": report.created_at,
        "intent": report.plan.intent,
        "label": report.plan.label,
        "safe_to_run": report.plan.safe_to_run,
        "approval_path": report.plan.approval_path,
        "cli": list(report.plan.cli),
        "routing_primary": report.plan.routing.primary.model.key if report.plan.routing else None,
        "steps": [
            {
                "name": s.name,
                "description": s.description,
                "artifact_path": s.artifact_path,
                "details": list(s.details),
            }
            for s in report.steps
        ],
        "boss_notification": report.boss_notification,
        "dry_run": True,
        "actual_telegram_call": False,
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return md_path, json_path


__all__ = [
    "E2EStep",
    "E2EReport",
    "build_e2e_report",
    "write_e2e_report",
]
