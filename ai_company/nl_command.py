"""자연어 명령 인터페이스.

사장님이 텔레그램/시뮬레이터/CLI에서 한국어 자연어로 명령을 내리면
이 모듈이 의도를 분류하고:

1) 모델 라우터 결정 (Codex/Claude/Gemini/Ollama/이미지 AI)
2) 실행할 CLI 명령 후보
3) 안전 검사 (위험 키워드면 자동 실행 차단 + 승인 파일 생성)

세 가지를 하나의 `NLPlan`으로 묶어 반환한다. 실제 실행은 호출자가
`execute=True`를 명시했을 때만 한다. 외부 채널 반영, 결제, 입찰 변경
등 위험 작업은 항상 승인 파일 생성으로만 마무리한다.
"""
from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass, field
from typing import List, Optional

from .model_router import RoutingDecision, route as route_model
from .paths import ROOT
from .approval import format_approval_request
from .utils import write_report


# 사장님 instruction의 CODEX_SAFE_RULES 위험 키워드 그대로 옮김.
RISK_KEYWORDS: tuple[str, ...] = (
    "삭제", "대량 삭제", "결제", "주문", "환불",
    "업로드", "게시", "발송", "입찰가", "광고비",
    "배포", "로그인", "쿠키", "토큰", "비밀번호",
)

# 제품 코드 패턴 (영문 대문자 + 숫자, 예: GOSTICK01)
PRODUCT_CODE_PATTERN = re.compile(r"\b([A-Z]{2,}\d{1,3})\b")


@dataclass
class NLPlan:
    """자연어 명령 해석 결과."""

    message: str
    intent: str
    label: str
    cli: List[str] = field(default_factory=list)
    routing: Optional[RoutingDecision] = None
    safe_to_run: bool = True
    risk_keywords: List[str] = field(default_factory=list)
    approval_required: bool = False
    approval_path: Optional[str] = None
    reasoning: List[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        lines: List[str] = []
        lines.append("# 자연어 명령 해석 결과")
        lines.append("")
        lines.append(f"- 입력 메시지: {self.message}")
        lines.append(f"- 분류 의도: **{self.intent}** — {self.label}")
        lines.append(
            f"- 실행 가능 여부: {'바로 실행 가능' if self.safe_to_run else '승인 필요'}"
        )
        if self.cli:
            lines.append(f"- CLI 후보: `python -m ai_company.main {' '.join(self.cli)}`")
        else:
            lines.append("- CLI 후보: 없음 (직접 명령으로 변환 불가)")
        if self.routing is not None:
            r = self.routing
            lines.append(
                f"- 모델 라우터 1순위: **{r.primary.model.display_name}** "
                f"({r.primary.model.role}) / 점수 {r.primary.score}"
            )
        if self.risk_keywords:
            lines.append(f"- 위험 키워드: {', '.join(self.risk_keywords)}")
        if self.approval_required:
            lines.append("- 승인 필요: 09_approval 파일 생성됨")
            if self.approval_path:
                lines.append(f"- 승인 파일: {self.approval_path}")
        lines.append("")
        lines.append("## 분류 사유")
        for reason in self.reasoning or ["기본 의도 라우팅"]:
            lines.append(f"- {reason}")
        lines.append("")
        lines.append("## 다음 단계")
        if self.safe_to_run and self.cli:
            lines.append("- CLI 명령을 그대로 실행 (필요 시 사장님 결과 확인)")
        elif self.approval_required:
            lines.append("- 사장님이 09_approval 파일 검토 후 승인하면 실제 실행")
        else:
            lines.append("- 자연어를 좀 더 구체적으로 입력하면 CLI 매핑이 정확해짐")
        return "\n".join(lines)


def _extract_product_code(text: str, default: str = "GOSTICK01") -> str:
    match = PRODUCT_CODE_PATTERN.search(text)
    return match.group(1) if match else default


def _extract_topic(text: str, default: str = "고스틱 광고 효율 개선") -> str:
    cleaned = text.strip()
    for marker in ("회의해줘", "회의해", "회의 해줘", "분석해줘", "분석해", "만들어줘"):
        if marker in cleaned:
            cleaned = cleaned.split(marker, 1)[0].strip()
            break
    return cleaned[:80] if cleaned else default


def _find_risk_keywords(text: str) -> List[str]:
    return [kw for kw in RISK_KEYWORDS if kw in text]


def _classify_intent(text: str, lowered: str) -> tuple[str, str, List[str], List[str]]:
    """의도 분류. (intent_key, label, cli_args, reasons) 반환."""
    reasons: List[str] = []

    # 회의 의도가 가장 명확한 표현을 먼저 잡는다.
    if "회의" in text or "meeting" in lowered or "토론" in text:
        topic = _extract_topic(text)
        reasons.append(f"'회의/토론' 키워드 → AI 회의 (--with-router)로 토픽='{topic}'")
        return "meeting", "AI 회의 (라우터 통과)", ["meeting", "--topic", topic, "--with-router"], reasons

    if "네이버" in text or "csv" in lowered or "광고 분석" in text or "ROAS" in text or "roas" in lowered:
        reasons.append("'네이버/CSV/광고 분석' 키워드 → 네이버광고 CSV 분석")
        return (
            "analyze_ads",
            "네이버광고 CSV 분석",
            ["analyze-ads", "--csv", "data/naver_ads_sample.csv"],
            reasons,
        )

    if "대시보드" in text or "dashboard" in lowered:
        reasons.append("'대시보드' 키워드 → dry-run 대시보드 갱신")
        return "dashboard", "dry-run 대시보드 갱신", ["dry-run-dashboard"], reasons

    if "우선" in text and "승인" in text:
        reasons.append("'우선순위/승인' 키워드 → 승인 우선순위 큐")
        return "approval_queue", "승인 파일 우선순위 큐", ["approval-priority-queue"], reasons

    if ("승인" in text and "위험" in text) or ("위험" in text and "리포트" in text):
        reasons.append("'승인/위험' 키워드 → 승인 위험도 리포트")
        return "approval_risk", "승인 위험도 리포트", ["approval-risk-report"], reasons

    if "승인" in text or "approval" in lowered:
        reasons.append("'승인' 키워드 → 승인 파일 목록 조회")
        return "approvals_list", "승인 파일 목록 조회", ["approvals", "list"], reasons

    if "ollama" in lowered or "올라마" in text or ("모델" in text and "목록" in text):
        reasons.append("'Ollama/모델 목록' 키워드 → Ollama 모델 목록 dry-run")
        return "ollama_models", "Ollama 모델 목록 dry-run", ["ollama-model-list-dry-run"], reasons

    if any(k in text for k in ("텔레그램", "telegram")) or "n8n" in lowered or "hermes" in lowered or "연결" in text:
        reasons.append("'텔레그램/n8n/Hermes/연결' 키워드 → 4~8단계 연결 dry-run")
        return "connection_stages", "4~8단계 AI 연결 dry-run", ["connection-stages"], reasons

    if "실험" in text or "테스트 설계" in text or "AB" in text:
        topic = _extract_topic(text)
        reasons.append(f"'실험/테스트 설계' 키워드 → 실험 설계 토픽='{topic}'")
        return "experiment", "AI 회의 기반 실험 설계", ["experiment-plan", "--topic", topic], reasons

    if "썸네일" in text or "이미지" in text or "포스터" in text or "비주얼" in text:
        product = _extract_product_code(text)
        reasons.append(f"'썸네일/이미지' 키워드 → 이미지 광고 템플릿 product='{product}'")
        return "image_templates", "이미지 광고 템플릿", ["image-templates", "--product", product], reasons

    if "인스타" in text or "instagram" in lowered:
        product = _extract_product_code(text)
        reasons.append(f"'인스타' 키워드 → 인스타 업로드 승인형 dry-run product='{product}'")
        return (
            "instagram_dry_run",
            "인스타 업로드 승인형 dry-run",
            ["instagram-upload-dry-run", "--product", product],
            reasons,
        )

    if "스마트스토어" in text or "smartstore" in lowered or "상세페이지" in text:
        reasons.append("'스마트스토어/상세페이지' 키워드 → 상품 데이터 dry-run")
        return (
            "smartstore_fetch",
            "스마트스토어 상품 데이터 dry-run",
            ["smartstore-fetch-dry-run"],
            reasons,
        )

    if "플레이라이트" in text or "playwright" in lowered or "브라우저" in text:
        reasons.append("'Playwright/브라우저' 키워드 → 브라우저 자동화 dry-run")
        return (
            "playwright_dry_run",
            "Playwright dry-run 설계",
            ["playwright-dry-run", "--target", "naver_ads"],
            reasons,
        )

    if "광고" in text or "릴스" in text or "문구" in text:
        product = _extract_product_code(text)
        reasons.append(f"'광고/릴스/문구' 키워드 → 광고 패키지 product='{product}'")
        return "ad_package", "광고 패키지 생성", ["ad", "--product", product], reasons

    if "시뮬레이터" in text or "사무실" in text or "office" in lowered:
        reasons.append("'시뮬레이터/사무실' 키워드 → AI 사무실 시뮬레이터 위치 확인")
        return "office_simulator", "AI 사무실 시뮬레이터 위치", ["office-simulator"], reasons

    if "라우터" in text or "어느 모델" in text or "어떤 모델" in text:
        reasons.append("'라우터/모델' 키워드 → 모델 라우터 결정 보고서")
        return (
            "model_router",
            "모델 라우터 결정",
            ["model-router", "--task", text[:200]],
            reasons,
        )

    # 폴백: AI 회의 (라우터 통과)
    topic = _extract_topic(text)
    reasons.append(f"명확한 의도 키워드 없음 → 폴백으로 AI 회의 (라우터 통과) topic='{topic}'")
    return "meeting_fallback", "AI 회의 (폴백)", ["meeting", "--topic", topic, "--with-router"], reasons


def _create_approval_for_risky_command(plan: NLPlan) -> str:
    """위험 키워드가 있는 자연어 명령을 09_approval에 기록."""
    approval_dir = ROOT / "09_approval"
    approval_dir.mkdir(parents=True, exist_ok=True)
    body = format_approval_request(
        task_name=f"자연어 명령 안전 확인: {plan.intent}",
        target=f"입력 메시지: {plan.message}",
        before="외부 채널/계정 상태 그대로 유지",
        after="사장님 승인 후에만 실제 명령 실행",
        expected_effect="자연어 명령 의도대로 dry-run 또는 실제 실행 진행",
        risks=[
            f"위험 키워드 포함: {', '.join(plan.risk_keywords)}",
            "외부 채널 반영/결제/입찰 변경 가능성",
            "사장님 미승인 시 실행 금지",
        ],
        rollback="실제 실행 전이라면 09_approval 파일을 반려로 기록",
        source_markdown=f"# 자연어 명령 원문\n\n{plan.message}\n\n# 의도\n\n{plan.intent} — {plan.label}",
    )
    path = write_report(approval_dir, "APPROVAL_REQUIRED_nl_command", body)
    return str(path)


def _live_enrich_reasoning(plan: "NLPlan") -> None:
    """Ollama가 살아있으면 분류 결과에 자연어 사유 한 줄을 더 붙임. 실패 시 무시."""
    try:
        from . import ollama_runtime as _r  # type: ignore
    except Exception:
        return
    if not _r.is_alive():
        return
    prompt = (
        f"사장님 메시지: {plan.message}\n"
        f"우리 시스템이 분류한 의도: {plan.intent} ({plan.label})\n\n"
        "한국어 한 줄(40자 이내)로 이 분류가 맞아 보이는지 자연스럽게 코멘트하라."
        " '맞습니다', '약간 모호합니다' 같은 짧은 평가만."
    )
    line = _r.generate(prompt, temperature=0.3, max_tokens=80, timeout=8)
    if line:
        plan.reasoning.append(f"Ollama 의견: {line.strip().splitlines()[0]}")


def interpret(message: str, attach_routing: bool = True, *, live: bool = False) -> NLPlan:
    """자연어 메시지 → NLPlan."""
    text = message.strip()
    if not text:
        return NLPlan(
            message=message,
            intent="empty",
            label="빈 메시지",
            cli=[],
            safe_to_run=False,
            reasoning=["메시지가 비어 있어 의도를 분류할 수 없음"],
        )

    lowered = text.lower()
    intent, label, cli, reasons = _classify_intent(text, lowered)
    routing = route_model(text) if attach_routing else None
    risks = _find_risk_keywords(text)
    safe = not risks

    plan = NLPlan(
        message=message,
        intent=intent,
        label=label,
        cli=cli,
        routing=routing,
        safe_to_run=safe,
        risk_keywords=risks,
        approval_required=bool(risks),
        reasoning=reasons,
    )

    if plan.approval_required:
        plan.approval_path = _create_approval_for_risky_command(plan)
        plan.reasoning.append(
            f"위험 키워드 {', '.join(risks)} → 자동 실행 차단, 승인 파일 생성"
        )

    if live:
        _live_enrich_reasoning(plan)

    return plan


def run_plan(plan: NLPlan, timeout: int = 180) -> dict:
    """NLPlan을 실제 CLI 실행. 안전한 경우에만 실행됨."""
    if not plan.safe_to_run:
        return {
            "returncode": -1,
            "output": "위험 키워드 포함으로 실행 차단됨. 09_approval 파일 확인 필요.",
            "command_line": "(차단됨)",
            "approval_path": plan.approval_path,
        }
    if not plan.cli:
        return {
            "returncode": -1,
            "output": "CLI 매핑이 없어 실행할 수 없습니다.",
            "command_line": "(없음)",
        }
    full_command = [sys.executable, "-m", "ai_company.main", *plan.cli]
    completed = subprocess.run(
        full_command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        shell=False,
        check=False,
    )
    output = (completed.stdout or "").strip()
    error = (completed.stderr or "").strip()
    combined = output if completed.returncode == 0 else "\n".join(p for p in (output, error) if p)
    return {
        "returncode": completed.returncode,
        "output": combined,
        "command_line": "python -m ai_company.main " + " ".join(plan.cli),
    }


def write_plan_report(plan: NLPlan) -> str:
    """plan을 08_reports에 저장."""
    folder = ROOT / "08_reports"
    folder.mkdir(parents=True, exist_ok=True)
    path = write_report(folder, "nl_command_plan", plan.to_markdown())
    return str(path)


__all__ = [
    "NLPlan",
    "RISK_KEYWORDS",
    "interpret",
    "run_plan",
    "write_plan_report",
]
