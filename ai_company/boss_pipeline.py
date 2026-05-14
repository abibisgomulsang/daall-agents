"""사장님 명령 → 사장님 승인까지 7단계 통합 파이프라인.

사장님이 처음 의도하신 아키텍처를 정확히 코드화한 흐름:

    [사장님]
       ↓ 자연어 한 줄
    [1. Hermes AI]               — 인바운드 수신 + 메모리 조회 (mock)
       ↓
    [2. AgentAU / n8n]            — 오케스트레이션 큐 진입 (mock)
       ↓
    [3. CEO 오케스트레이터]        — 작업 분해 + 우선순위 + 책임 직원
       ↓
    [4. 모델 라우터]              — Codex/Claude/Gemini/Ollama/이미지 AI 중 1순위
       ↓
    [5. AI 회의]                  — 각 AI 직원 의견 + CEO 결론
       ↓
    [6. 실행 준비]                — 광고 패키지 / 이미지 시안 / 분석 등 산출물
       ↓
    [7. 사장님 승인 대기]          — 09_approval 자동 생성, 사장님이 보고 OK

실제 외부 채널 반영(스마트스토어/네이버광고/SNS)은 7단계 끝나도 **자동으로
일어나지 않는다**. 사장님이 09_approval 파일을 직접 확인한 뒤 별도로
실행하셔야 한다.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from . import ceo_orchestrator as _ceo
from .approval import format_approval_request
from .meeting import meeting_to_markdown, run_meeting
from .model_router import RoutingDecision, route as _route
from .paths import ROOT
from .utils import now_stamp, write_report


@dataclass
class PipelineStage:
    """단일 단계 산출물."""

    number: int
    name: str
    description: str
    artifact_path: Optional[str] = None
    details: List[str] = field(default_factory=list)


@dataclass
class BossCommandResult:
    """사장님 한 줄 명령의 전 결과."""

    message: str
    stages: List[PipelineStage]
    routing: Optional[RoutingDecision]
    ceo_plan_md: str
    meeting_md: str
    execution_prep_md: str
    approval_path: Optional[str] = None
    created_at: str = ""

    def to_markdown(self) -> str:
        lines = ["# 사장님 명령 처리 결과", ""]
        lines.append(f"- 생성: {self.created_at}")
        lines.append(f"- 입력 메시지: {self.message}")
        if self.routing is not None:
            lines.append(
                f"- 라우터 1순위: **{self.routing.primary.model.display_name}** "
                f"({self.routing.primary.model.role})"
            )
        lines.append("")
        lines.append("## 7단계 진행 로그")
        for s in self.stages:
            lines.append(f"### {s.number}. {s.name}")
            lines.append(s.description)
            if s.artifact_path:
                lines.append(f"- 산출물: `{s.artifact_path}`")
            for d in s.details:
                lines.append(f"- {d}")
            lines.append("")
        if self.approval_path:
            lines.append("## 사장님 승인 대기")
            lines.append(f"- 파일: `{self.approval_path}`")
            lines.append("- 검토 후 `python -m ai_company.main approvals decide --file ... --decision approved --reason ...`")
            lines.append("- 외부 채널 실제 반영은 사장님이 별도 명령으로 진행해야 합니다.")
        return "\n".join(lines)


def _hermes_step(message: str) -> PipelineStage:
    """1단계 — Hermes 인바운드. 실제 메모리에 기록 + 선호 학습."""
    details: List[str] = []
    artifact: Optional[str] = None
    try:
        from . import hermes_memory, hermes_runtime
        # 메시지 inbox에 기록 (사장님 PC에서 직접 입력한 메시지도 추적)
        hermes_memory.record_inbound(
            message, from_chat_id=0, from_user="boss_cli", message_id=0,
            status="received_via_boss_command",
        )
        hermes_memory.remember_command(message)
        prefs = hermes_memory.get_preferences()
        recent = hermes_memory.recent_decisions(limit=3)
        creds = hermes_runtime.credentials_ready()
        details.append(f"메모리: 선호 명령 {len(prefs.get('favorite_commands') or [])}개 / 최근 결정 {len(recent)}건")
        details.append(f"텔레그램 자격: {'설정됨' if creds else '미설정 — 봇 미실행'}")
        details.append(f"메시지 길이: {len(message)}자")
        artifact = str(hermes_memory.INBOX_PATH())
    except Exception as e:
        details.append(f"Hermes 메모리 호출 실패: {e}")
    return PipelineStage(
        number=1,
        name="Hermes AI 인바운드",
        description="사장님 메시지를 Hermes 메모리에 기록하고 선호 학습. 실제 텔레그램 발신 X.",
        artifact_path=artifact,
        details=details,
    )


def _agentau_step(message: str) -> PipelineStage:
    """2단계 — AgentAU/n8n 오케스트레이션 큐 진입 mock."""
    return PipelineStage(
        number=2,
        name="AgentAU / n8n 오케스트레이션",
        description="작업을 AgentAU(또는 n8n) 큐에 등록 (mock). 실제 webhook 호출은 사장님 승인 후.",
        details=[
            "큐 이름: ai_company.boss_inbound",
            "외부 webhook 호출 여부: 없음 (dry-run)",
        ],
    )


def _ceo_step(message: str, routing: RoutingDecision) -> tuple[PipelineStage, str, Path]:
    plan = _ceo.build_plan(message, routing=routing)
    md = plan.to_markdown()
    path = write_report(ROOT / "08_reports", "ceo_workplan", md)
    return (
        PipelineStage(
            number=3,
            name="CEO 오케스트레이터 작업 분해",
            description=f"1차 책임 직원: {plan.primary_owner} · 서브태스크 {len(plan.subtasks)}개",
            artifact_path=str(path),
            details=[f"- {st}" for st in plan.subtasks]
            + ([f"위험 요소: {len(plan.risks)}건" if plan.risks else "위험 요소: 없음"]),
        ),
        md,
        path,
    )


def _router_step(routing: RoutingDecision) -> PipelineStage:
    return PipelineStage(
        number=4,
        name="모델 라우터",
        description=(
            f"1순위 **{routing.primary.model.display_name}** "
            f"({routing.primary.model.role}) / 점수 {routing.primary.score}"
        ),
        details=[
            "후순위: " + (", ".join(rs.model.display_name for rs in routing.runners_up) or "없음"),
            f"dry-run: {routing.handoff['dry_run']} / executed: {routing.handoff['executed']}",
        ],
    )


def _meeting_step(message: str, routing: RoutingDecision, *, live: bool, multi: bool = False) -> tuple[PipelineStage, str, Path]:
    if multi:
        from .multi_agent_meeting import run_multi_meeting
        result = run_multi_meeting(message, live=live)
        md = result.to_markdown()
        path = write_report(ROOT / "10_meetings", "multi_meeting_boss_pipeline", md)
        members = ", ".join([t.persona_name for t in result.round1])
        return (
            PipelineStage(
                number=5,
                name="AI 회의 (멀티 에이전트 3라운드)",
                description=(
                    f"{len(result.round1)}명 토론. 멤버: {members}. "
                    + (f"(force_ollama, 캡 보호 동작)" if result.force_ollama else "(라이브)")
                ),
                artifact_path=str(path),
                details=[
                    f"표결: 동의 {len(result.vote.agree)} · 반대 {len(result.vote.disagree)} · 기권 {len(result.vote.abstain)}",
                    f"추정 비용: ₩{result.estimated_cost_krw:.0f}",
                ],
            ),
            md,
            path,
        )
    result = run_meeting(message, routing=routing, live=live)
    md = meeting_to_markdown(result)
    path = write_report(ROOT / "10_meetings", "ai_meeting", md)
    return (
        PipelineStage(
            number=5,
            name="AI 회의",
            description=(
                f"{len(result.opinions)}명 직원 의견 수집 후 CEO 결론. "
                + ("(live: Ollama/Claude 시도)" if live else "(dry-run)")
            ),
            artifact_path=str(path),
        ),
        md,
        path,
    )


def _detect_execution_kind(message: str, owner: str) -> str:
    msg = message.lower()
    # 비디오 작업 — SNS 대본 → 편집 패키지
    video_kw = ("비디오", "영상", "편집", "타임라인", "릴스 편집", "쇼츠 편집", "자막 편집", "ffmpeg", "moviepy")
    if any(w in message for w in video_kw) or owner == "비디오 AI":
        return "video_package"
    if "광고" in message or owner == "마케팅 AI":
        return "ad_package"
    if "이미지" in message or "썸네일" in message or owner == "이미지 AI":
        return "image_templates"
    if "csv" in msg or "ROAS" in message or owner == "네이버광고 AI":
        return "analyze_ads"
    return "generic_dryrun"


def _execution_prep_step(message: str, owner: str) -> tuple[PipelineStage, str, Path]:
    """6단계 — 실행 준비물 생성 (광고 패키지 / 이미지 / 분석 등)."""
    kind = _detect_execution_kind(message, owner)
    out_md = []
    artifact_str = ""

    if kind == "video_package":
        from .video_editing import write_video_package
        try:
            md_path, _py_path, _srt_path, summary_path = write_video_package(
                message,
                title=f"릴스/쇼츠 — {message[:24]}",
                target_seconds=15.0,
            )
            md = Path(summary_path).read_text(encoding="utf-8")
            artifact_str = str(summary_path)
        except Exception as e:
            md = f"# 실행 준비 (비디오)\n\n대본이 비어 있거나 분석할 수 없습니다: {e}"
            path = write_report(ROOT / "08_reports", "video_brief_skip", md)
            artifact_str = str(path)
        out_md.append(md)
    elif kind == "ad_package":
        from .marketing import generate_routed_ad_package
        try:
            md = generate_routed_ad_package("GOSTICK01")
        except Exception:
            md = f"# 실행 준비 (광고 패키지)\n\n상품 데이터 미준비. 사장님이 상품 코드를 지정해 주세요."
        out_md.append(md)
        path = write_report(ROOT / "02_marketing", "ad_package_GOSTICK01_boss_pipeline", md)
        artifact_str = str(path)
    elif kind == "image_templates":
        from .image_templates import build_image_templates
        try:
            md, _ = build_image_templates("GOSTICK01")
        except Exception:
            md = "# 실행 준비 (이미지 템플릿)\n\n상품 데이터 미준비. 사장님이 상품 코드를 지정해 주세요."
        out_md.append(md)
        path = write_report(ROOT / "03_images" / "templates", "image_brief_boss_pipeline", md)
        artifact_str = str(path)
    elif kind == "analyze_ads":
        from .ads_analysis import analyze_naver_ads_csv
        csv_path = ROOT / "data" / "naver_ads_sample.csv"
        if csv_path.exists():
            md = analyze_naver_ads_csv(csv_path)
        else:
            md = "# 실행 준비 (네이버광고 분석)\n\n샘플 CSV가 없습니다. data/naver_ads_sample.csv 를 준비해주세요."
        out_md.append(md)
        path = write_report(ROOT / "05_naver_ads", "naver_ads_boss_pipeline", md)
        artifact_str = str(path)
    else:
        # generic — CEO 작업 분해를 그대로 실행 준비물로
        md = (
            "# 실행 준비 (일반)\n\n"
            f"입력: {message}\n\n"
            "이 작업은 표준 실행 준비물 매핑이 없어 CEO 작업 분해를 그대로 사용합니다.\n"
            "사장님이 구체적인 출력 형태를 지정해주시면 다음 호출부터 자동 매핑됩니다."
        )
        out_md.append(md)
        path = write_report(ROOT / "08_reports", "execution_prep_generic", md)
        artifact_str = str(path)

    return (
        PipelineStage(
            number=6,
            name="실행 준비",
            description=f"준비물 종류: {kind}",
            artifact_path=artifact_str,
        ),
        "\n\n".join(out_md),
        Path(artifact_str),
    )


def _approval_step(message: str, owner: str, kind_hint: str) -> tuple[PipelineStage, Path]:
    """7단계 — 사장님 승인 대기 파일 자동 생성."""
    body = format_approval_request(
        task_name=f"사장님 명령 후속 실행: {message[:40]}",
        target=f"1차 책임 직원 {owner} 가 준비한 산출물",
        before="외부 채널 상태 유지 (스마트스토어/네이버광고/SNS 변경 없음)",
        after="사장님 승인 후 별도 명령으로만 실제 반영",
        expected_effect="사장님이 결과만 확인하고 OK/NG 결정",
        risks=[
            "외부 채널 실제 반영은 자동으로 일어나지 않음",
            "API 키/토큰/.env 노출 금지 (시스템 차원에서 차단)",
        ],
        rollback="승인 파일을 반려로 기록하면 흐름 종료",
        source_markdown=f"# 사장님 명령 원문\n\n{message}\n\n# 준비물 종류\n\n{kind_hint}",
    )
    path = write_report(
        ROOT / "09_approval",
        "APPROVAL_REQUIRED_boss_pipeline",
        body,
    )
    return (
        PipelineStage(
            number=7,
            name="사장님 승인 대기",
            description="외부 채널 반영 전 사장님 승인 대기 파일을 자동으로 생성했습니다.",
            artifact_path=str(path),
            details=[
                "approve 명령: python -m ai_company.main approvals decide --file <파일명> --decision approved --reason ...",
                "외부 채널 자동 반영: 없음 (사장님 별도 실행 필요)",
            ],
        ),
        path,
    )


def run_boss_command(message: str, *, live: bool = False, multi: bool = False) -> BossCommandResult:
    """사장님 한 줄 → 7단계 파이프라인 실행."""
    if not message or not message.strip():
        raise ValueError("메시지가 비어 있습니다.")
    stages: List[PipelineStage] = []

    # 1. Hermes
    stages.append(_hermes_step(message))
    # 2. AgentAU/n8n
    stages.append(_agentau_step(message))
    # 라우터 결정은 3단계 CEO 안에서 한 번 만들고 4단계는 표시만
    routing = _route(message)
    # 3. CEO
    ceo_stage, ceo_md, ceo_path = _ceo_step(message, routing)
    stages.append(ceo_stage)
    # 4. 라우터 표시
    stages.append(_router_step(routing))
    # 5. AI 회의
    meeting_stage, meeting_md, _ = _meeting_step(message, routing, live=live, multi=multi)
    stages.append(meeting_stage)
    # 6. 실행 준비
    owner = _ceo.build_plan(message, routing=routing).primary_owner
    exec_stage, exec_md, _ = _execution_prep_step(message, owner)
    stages.append(exec_stage)
    # 7. 사장님 승인 대기
    approval_stage, approval_path = _approval_step(message, owner, _detect_execution_kind(message, owner))
    stages.append(approval_stage)

    return BossCommandResult(
        message=message,
        stages=stages,
        routing=routing,
        ceo_plan_md=ceo_md,
        meeting_md=meeting_md,
        execution_prep_md=exec_md,
        approval_path=str(approval_path),
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )


def write_boss_command_report(message: str, *, live: bool = False, multi: bool = False) -> tuple[Path, Path]:
    result = run_boss_command(message, live=live, multi=multi)
    folder = ROOT / "08_reports"
    folder.mkdir(parents=True, exist_ok=True)
    md_path = folder / f"boss_command_{now_stamp()}.md"
    json_path = folder / f"boss_command_{now_stamp()}.json"
    # 동시 호출 충돌 회피
    suffix = 0
    while md_path.exists():
        suffix += 1
        md_path = folder / f"boss_command_{now_stamp()}_{suffix:02d}.md"
        json_path = folder / f"boss_command_{now_stamp()}_{suffix:02d}.json"
    md_path.write_text(result.to_markdown(), encoding="utf-8")
    json_path.write_text(
        json.dumps(
            {
                "message": result.message,
                "created_at": result.created_at,
                "routing_primary": result.routing.primary.model.key if result.routing else None,
                "stages": [
                    {"number": s.number, "name": s.name, "artifact_path": s.artifact_path}
                    for s in result.stages
                ],
                "approval_path": result.approval_path,
                "external_call": False,
            },
            ensure_ascii=False, indent=2
        ),
        encoding="utf-8",
    )
    return md_path, json_path


__all__ = [
    "PipelineStage",
    "BossCommandResult",
    "run_boss_command",
    "write_boss_command_report",
]
