from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
from .agents import AGENTS, AgentRole
from .model_router import RoutingDecision, route as route_model

@dataclass
class AgentOpinion:
    agent: str
    opinion: str
    action: str

@dataclass
class MeetingResult:
    topic: str
    opinions: List[AgentOpinion]
    ceo_decision: str
    approval_required: bool
    routing: Optional[RoutingDecision] = field(default=None)

def _offline_opinion(role: AgentRole, topic: str) -> AgentOpinion:
    if "데이터" in role.name:
        return AgentOpinion(
            role.name,
            f"{topic} 문제는 먼저 노출수, 클릭률, 전환율, ROAS를 분리해서 봐야 합니다. 클릭은 있는데 구매가 낮으면 상세페이지/가격/리뷰 문제가 큽니다.",
            "최근 광고 CSV를 분석하고 ROAS 150% 이하 키워드를 개선 후보로 분류"
        )
    if "고객심리" in role.name:
        return AgentOpinion(
            role.name,
            "고양이 장난감 광고는 제품 설명보다 집사의 고민을 먼저 건드려야 합니다. 예: '사줘도 안 노는 고양이, 문제는 장난감이 아니라 사냥 자극일 수 있습니다.'",
            "후킹 문구를 공감형 3개, 문제제기형 3개로 작성"
        )
    if "SNS" in role.name:
        return AgentOpinion(
            role.name,
            "릴스는 첫 2초에 고양이 반응 장면이나 강한 자막이 필요합니다. 정적인 상품 사진보다 사용 장면 중심으로 테스트해야 합니다.",
            "9:16 릴스 대본과 썸네일 문구 3안 생성"
        )
    if "상품" in role.name:
        return AgentOpinion(
            role.name,
            "고스틱은 리필/세트/고양이 성향별 추천을 함께 강조하면 재구매와 객단가를 올릴 수 있습니다.",
            "고스틱 본품+리필 세트 제안과 상세페이지 첫 문단 개선"
        )
    if "네이버광고" in role.name:
        return AgentOpinion(
            role.name,
            "낭비 키워드는 클릭 대비 주문이 낮은 키워드입니다. 입찰가 조정보다 먼저 광고문구와 랜딩 메시지 일치 여부를 확인해야 합니다.",
            "키워드별 CPC/전환율/ROAS 표 생성 후 중지/개선/증액 후보 분류"
        )
    return AgentOpinion(
        role.name,
        "실제 업로드, 광고비 변경, 상품 수정은 승인 대기 파일을 만들어야 합니다. 과장 표현과 치료/효능 표현은 피해야 합니다.",
        "승인 필요 항목과 위험 표현 체크리스트 생성"
    )


def _build_ceo_decision(topic: str, routing: Optional[RoutingDecision]) -> str:
    base = (
        f"'{topic}'에 대한 CEO AI 결론: "
        "1) 데이터로 원인을 분리한다. "
        "2) 공감형 후킹 문구를 만든다. "
        "3) 릴스/썸네일/상세페이지를 동시에 테스트한다. "
        "4) ROAS 낮은 키워드는 바로 중지하지 말고 광고문구와 랜딩을 먼저 맞춘다. "
        "5) 실제 수정은 승인 대기 파일을 만든 뒤 진행한다."
    )
    if routing is None:
        return base
    return (
        base
        + f" 6) 실행 단계는 모델 라우터 결정에 따라 {routing.primary.model.display_name}"
        f"({routing.primary.model.role})에게 1차 위임한다."
    )


def _live_opinion(role: AgentRole, topic: str) -> Optional[AgentOpinion]:
    """Ollama가 살아있으면 실제 LLM으로 의견 생성. 실패 시 None."""
    try:
        from . import ollama_runtime as _r  # type: ignore
    except Exception:
        return None
    if not _r.is_alive():
        return None
    system = (
        "너는 한국 1인 고양이 용품 회사의 AI 직원이다. "
        "사장님이 결과만 보신다. 답변은 한국어 두 문단으로 짧게."
        " 절대 외부에 실제 업로드/입찰 변경/결제를 하지 않는다고 가정한다."
        " 과장광고/치료/100% 보장 표현 금지."
    )
    prompt = (
        f"네 역할: {role.name}\n"
        f"네 미션: {role.mission}\n"
        f"네 관점: {role.perspective}\n"
        f"회의 주제: {topic}\n\n"
        "다음 JSON 형식으로만 답하라. 다른 문장 금지.\n"
        '{"opinion": "<3~4문장 의견>", "action": "<바로 실행 가능한 dry-run 제안 1문장>"}'
    )
    raw = _r.generate(prompt, system=system, temperature=0.5, max_tokens=380)
    if not raw:
        return None
    # JSON 파싱 시도; 실패하면 plain text 사용
    import json, re
    text = raw.strip()
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        try:
            parsed = json.loads(m.group(0))
            op = str(parsed.get("opinion") or "").strip()
            ac = str(parsed.get("action") or "").strip()
            if op and ac:
                return AgentOpinion(role.name, op, ac)
        except Exception:
            pass
    # JSON 실패 시: 첫 두 문장을 의견, 마지막 줄을 action으로
    lines = [ln for ln in text.split("\n") if ln.strip()]
    if not lines:
        return None
    op = " ".join(lines[:-1]) or lines[0]
    ac = lines[-1]
    return AgentOpinion(role.name, op, ac)


def _live_ceo_decision(topic: str, opinions: List[AgentOpinion], routing: Optional[RoutingDecision]) -> Optional[str]:
    """Ollama로 CEO 종합 결론 생성. 실패 시 None."""
    try:
        from . import ollama_runtime as _r  # type: ignore
    except Exception:
        return None
    if not _r.is_alive():
        return None
    bullet = "\n".join(f"- [{o.agent}] {o.opinion}" for o in opinions)
    system = (
        "너는 한국 1인 고양이 용품 회사의 CEO AI다. 다른 AI 직원의 의견을 종합한다. "
        "사장님 승인 없이는 실제 업로드/결제/입찰 변경을 하지 않는다고 가정. 한국어로 4~6문장."
    )
    routing_note = ""
    if routing is not None:
        routing_note = (
            f"\n실행 단계는 모델 라우터 결정에 따라 {routing.primary.model.display_name}"
            f"({routing.primary.model.role})에게 1차 위임된다.\n"
        )
    prompt = (
        f"회의 주제: {topic}\n\n"
        f"직원 의견:\n{bullet}\n"
        f"{routing_note}\n"
        "위 의견을 종합한 CEO 결론을 4~6문장으로 작성. 실행 전 09_approval 승인 흐름을 반드시 명시."
    )
    return _r.generate(prompt, system=system, temperature=0.4, max_tokens=400)


def run_meeting(
    topic: str,
    routing: Optional[RoutingDecision] = None,
    *,
    live: bool = False,
) -> MeetingResult:
    """AI 회의 실행.

    Args:
        topic: 회의 주제.
        routing: 모델 라우터 결정. None이면 라우터 미통과 회의.
        live: True면 Ollama 실제 호출로 의견 생성. 실패 시 자동으로 _offline_opinion 폴백.
    """
    opinions: List[AgentOpinion] = []
    for role in AGENTS:
        op = _live_opinion(role, topic) if live else None
        if op is None:
            op = _offline_opinion(role, topic)
        opinions.append(op)

    ceo_decision = None
    if live:
        ceo_decision = _live_ceo_decision(topic, opinions, routing)
    if not ceo_decision:
        ceo_decision = _build_ceo_decision(topic, routing)

    return MeetingResult(
        topic=topic,
        opinions=opinions,
        ceo_decision=ceo_decision,
        approval_required=True,
        routing=routing,
    )


def run_routed_meeting(topic: str, *, live: bool = False) -> MeetingResult:
    decision = route_model(topic)
    return run_meeting(topic, routing=decision, live=live)


def meeting_to_markdown(result: MeetingResult) -> str:
    lines = [f"# AI 회의 결과: {result.topic}", ""]
    if result.routing is not None:
        r = result.routing
        runners = (
            ", ".join(rs.model.display_name for rs in r.runners_up)
            if r.runners_up else "없음"
        )
        lines.extend([
            "## 모델 라우터 결정",
            f"- 1순위 모델: **{r.primary.model.display_name}** ({r.primary.model.role})",
            f"- 1순위 점수: {r.primary.score}",
            f"- 후순위: {runners}",
            f"- dry-run: {r.handoff['dry_run']} / executed: {r.handoff['executed']}",
            "",
        ])
    for opinion in result.opinions:
        lines.extend([
            f"## {opinion.agent}",
            f"- 의견: {opinion.opinion}",
            f"- 제안 행동: {opinion.action}",
            "",
        ])
    lines.extend([
        "## CEO AI 최종 결론",
        result.ceo_decision,
        "",
        "## 승인 필요 여부",
        "필요" if result.approval_required else "불필요",
    ])
    return "\n".join(lines)