"""모델 라우터.

사장님이 공유한 아키텍처를 코드화한 모듈이다.

사장님 → Hermes/AgentAU/n8n → CEO 오케스트레이터 → 모델 라우터 →
  (Codex/ChatGPT, Claude, Gemini, Ollama, 이미지 AI) → AI 회의 →
  실행 준비 → 사장님 승인

이 모듈은 실제 모델 호출을 하지 않는다. 작업 설명을 받아 어떤 모델 패널이
가장 적합한지 점수화하고, dry-run 핸드오프 페이로드만 생성한다. 실제 API
호출, 비밀번호/토큰 노출, 외부 발송은 하지 않는다.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json

from .paths import ROOT
from .utils import now_stamp


@dataclass(frozen=True)
class ModelProfile:
    """라우팅 후보 모델 프로필."""

    key: str
    display_name: str
    role: str
    strengths: Tuple[str, ...]
    keywords: Tuple[str, ...]
    keyword_weight: int = 3
    strength_weight: int = 1
    safety_notes: Tuple[str, ...] = ()


# 사장님 원본 아키텍처:
#   Codex/ChatGPT: 코딩, 시스템 구축, 전략
#   Claude:        긴 문서, 고급 코딩, 기획서, 검토
#   Gemini:        리서치, 트렌드 조사, 아이디어 확장
#   Ollama:        내 컴퓨터 로컬 반복작업
#   이미지 AI:      광고 이미지/썸네일 제작
MODEL_PROFILES: Tuple[ModelProfile, ...] = (
    ModelProfile(
        key="codex_chatgpt",
        display_name="Codex / ChatGPT",
        role="코딩, 시스템 구축, 전략",
        strengths=(
            "코딩",
            "시스템 구축",
            "자동화 코드",
            "전략 수립",
            "마케팅 기획",
            "스크립트",
            "리팩터링",
        ),
        keywords=(
            "코딩", "코드", "스크립트", "자동화", "리팩터",
            "버그", "테스트 작성", "CLI",
            "시스템", "구축", "API", "백엔드", "프론트엔드", "DB",
            "전략", "마케팅", "기획",
        ),
        safety_notes=(
            "API 토큰 비용 발생 — --live 명시 시에만 실제 호출",
            "외부 배포/결제/광고 집행 전 사장님 승인 필수",
        ),
    ),
    ModelProfile(
        key="claude",
        display_name="Claude",
        role="긴 문서, 고급 코딩, 기획서, 검토",
        strengths=(
            "긴 문서 정리",
            "고급 코딩",
            "앱 설계",
            "복잡한 기획",
            "AI 회의 결과 검토",
            "스마트스토어 상세페이지 문구 검수",
            "리뷰 / 검수",
        ),
        keywords=(
            "긴 문서", "기획서", "검토", "검수", "리뷰",
            "정리", "요약 보고서", "상세페이지", "설계", "리팩터링",
            "코드 리뷰", "문서화", "스펙",
            "고급 코딩", "아키텍처",
        ),
        safety_notes=(
            "API 토큰 비용 발생 — --live 명시 시에만 실제 호출",
            "API 키, 비밀번호, .env 노출 금지",
        ),
    ),
    ModelProfile(
        key="gemini",
        display_name="Gemini",
        role="리서치, 트렌드 조사, 아이디어 확장",
        strengths=(
            "시장 조사",
            "트렌드 조사",
            "경쟁사 아이디어",
            "고양이 앱 아이디어 확장",
            "광고 소재 아이디어",
            "자료 기반 리서치",
        ),
        keywords=(
            "리서치", "조사", "트렌드", "경쟁사", "아이디어",
            "벤치마킹", "탐색", "시장", "키워드 조사", "분석",
            "인사이트",
        ),
        safety_notes=(
            "리서치 결과는 출처와 함께 보고. 단정 표현/과장 금지",
        ),
    ),
    ModelProfile(
        key="ollama",
        display_name="Ollama (로컬)",
        role="내 PC 로컬 반복작업",
        strengths=(
            "리뷰 분류",
            "고객 문의 분류",
            "상품 태그 생성",
            "광고 문구 초안",
            "반복 요약",
            "간단한 데이터 분석",
        ),
        keywords=(
            "분류", "태그", "라벨링", "초안", "반복",
            "대량", "벌크", "필터", "로컬", "오프라인",
            "요약 초안", "전처리",
        ),
        safety_notes=(
            "고급 전략/복잡한 코딩은 Claude/ChatGPT로 라우팅",
            "모델 다운로드/실행은 승인 후",
        ),
    ),
    ModelProfile(
        key="image_ai",
        display_name="이미지 AI (DALL-E / SD / Canva)",
        role="광고 이미지/썸네일 제작",
        strengths=(
            "광고 이미지 기획",
            "썸네일 구성안",
            "이미지 편집 지시서",
            "광고 이미지 생성",
            "썸네일 이미지",
            "포스터 이미지",
            "릴스 컷 이미지",
            "상세페이지 비주얼 초안",
        ),
        keywords=(
            "이미지", "썸네일", "포스터", "광고 이미지", "디자인",
            "비주얼", "릴스 컷", "그래픽", "캔버스", "썸",
            "이미지 생성", "그려", "렌더", "DALL-E", "Stable Diffusion",
            "사진", "일러스트",
        ),
        safety_notes=(
            "DALL-E 호출은 비용 발생 — --live 명시 시에만",
            "저작권/초상권 확인 후 사용",
            "실제 게시는 승인 후",
        ),
    ),
)

MODEL_BY_KEY: Dict[str, ModelProfile] = {p.key: p for p in MODEL_PROFILES}


@dataclass
class RouteScore:
    """단일 모델에 대한 점수와 사유."""

    model: ModelProfile
    score: int
    reasons: List[str] = field(default_factory=list)


@dataclass
class RoutingDecision:
    """최종 라우팅 결정."""

    task: str
    primary: RouteScore
    runners_up: List[RouteScore]
    handoff: Dict[str, object]
    created_at: str

    def to_markdown(self) -> str:
        lines: List[str] = []
        lines.append("# 모델 라우터 결정 보고서")
        lines.append("")
        lines.append(f"- 생성 시각: {self.created_at}")
        lines.append(f"- 입력 작업: {self.task}")
        lines.append(
            f"- 1순위 모델: **{self.primary.model.display_name}** ({self.primary.model.role})"
        )
        lines.append(f"- 1순위 점수: {self.primary.score}")
        lines.append("")
        lines.append("## 라우팅 사유 (1순위)")
        for reason in self.primary.reasons or ["기본 라우팅 규칙에 따라 선택"]:
            lines.append(f"- {reason}")
        lines.append("")
        if self.runners_up:
            lines.append("## 후순위 후보")
            for rs in self.runners_up:
                lines.append(
                    f"- {rs.model.display_name} — 점수 {rs.score} / 역할: {rs.model.role}"
                )
                for reason in rs.reasons[:3]:
                    lines.append(f"    - {reason}")
            lines.append("")
        lines.append("## 안전 규칙 (해당 모델)")
        for note in self.primary.model.safety_notes or ("특이 사항 없음",):
            lines.append(f"- {note}")
        lines.append("")
        lines.append("## Dry-run 핸드오프 페이로드 (실제 호출 안 함)")
        lines.append("```json")
        lines.append(json.dumps(self.handoff, ensure_ascii=False, indent=2))
        lines.append("```")
        lines.append("")
        lines.append("## 다음 단계")
        lines.append("- AI 회의 시스템에 결과 전달")
        lines.append("- 실행 준비물(광고/문서/이미지) 생성")
        lines.append("- 외부 호출/업로드/입찰 변경은 09_approval 파일 작성 후 사장님 승인")
        lines.append("")
        return "\n".join(lines)


def _score_model(task: str, profile: ModelProfile) -> RouteScore:
    task_lower = task.lower()
    score = 0
    reasons: List[str] = []
    for kw in profile.keywords:
        if kw.lower() in task_lower:
            score += profile.keyword_weight
            reasons.append(f"키워드 일치: '{kw}' (+{profile.keyword_weight})")
    for strength in profile.strengths:
        # 강점 문구가 작업 설명에 부분적으로 포함되면 약한 가중치 부여
        token = strength.split()[0].lower()
        if token and token in task_lower:
            score += profile.strength_weight
            reasons.append(f"강점 토큰 일치: '{strength}' (+{profile.strength_weight})")
    return RouteScore(model=profile, score=score, reasons=reasons)


def _fallback_primary(task: str) -> RouteScore:
    """키워드가 하나도 안 잡힐 때 기본값.

    프로젝트 규약상 긴 기획서/검수는 Claude를 권장하므로 fallback = Claude.
    """
    claude = MODEL_BY_KEY["claude"]
    return RouteScore(
        model=claude,
        score=0,
        reasons=[
            "키워드가 명확하지 않아 기본 라우팅(Claude: 긴 문서/검토)으로 처리",
            "사장님이 의도한 모델을 알려주시면 라우팅이 더 정확해집니다.",
        ],
    )


def route(task: str) -> RoutingDecision:
    if not task or not task.strip():
        raise ValueError("작업 설명이 비어 있습니다.")

    scored = [_score_model(task, profile) for profile in MODEL_PROFILES]
    scored.sort(key=lambda rs: rs.score, reverse=True)

    primary = scored[0] if scored and scored[0].score > 0 else _fallback_primary(task)
    runners = [
        rs for rs in scored if rs.model.key != primary.model.key and rs.score > 0
    ]

    handoff = {
        "router_version": "1.0.0",
        "task": task,
        "primary_model": primary.model.key,
        "primary_display_name": primary.model.display_name,
        "role": primary.model.role,
        "runners_up": [rs.model.key for rs in runners],
        "dry_run": True,
        "executed": False,
        "next_stage": "ai_meeting",
        "approval_required_for_external": True,
    }

    return RoutingDecision(
        task=task,
        primary=primary,
        runners_up=runners,
        handoff=handoff,
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )


def execute_routing(
    decision: "RoutingDecision",
    prompt: str,
    *,
    system: Optional[str] = None,
    live: bool = False,
) -> Dict[str, object]:
    """라우팅 결정대로 적절한 어댑터를 호출. live=False면 dry-run만."""
    primary_key = decision.primary.model.key
    result: Dict[str, object] = {
        "primary_model": primary_key,
        "live_requested": live,
        "executed": False,
        "provider": None,
        "text": None,
        "image": None,
        "reason": "dry-run only",
        "external_call": False,
    }
    if not live:
        return result

    if primary_key == "claude":
        try:
            from . import claude_runtime as cr  # type: ignore
        except Exception as e:
            result["reason"] = f"claude_runtime import 실패: {e}"
            return result
        if not cr.has_api_key():
            result["reason"] = "ANTHROPIC_API_KEY 미설정 — .env에 키를 채워주세요"
            return result
        text = cr.generate(prompt, system=system, live=True)
        result.update({
            "executed": True,
            "provider": "anthropic_claude",
            "text": text,
            "external_call": True,
            "reason": "claude 호출 완료" if text else "claude 응답 없음",
        })
        return result

    if primary_key == "codex_chatgpt":
        try:
            from . import openai_runtime as oa  # type: ignore
        except Exception as e:
            result["reason"] = f"openai_runtime import 실패: {e}"
            return result
        if not oa.has_api_key():
            result["reason"] = "OPENAI_API_KEY 미설정 — .env에 키를 채워주세요"
            return result
        text = oa.generate(prompt, system=system, live=True)
        result.update({
            "executed": True,
            "provider": "openai_chatgpt",
            "text": text,
            "external_call": True,
            "reason": "openai chat 호출 완료" if text else "openai 응답 없음",
        })
        return result

    if primary_key == "image_ai":
        try:
            from . import openai_runtime as oa  # type: ignore
        except Exception as e:
            result["reason"] = f"openai_runtime import 실패: {e}"
            return result
        if not oa.has_api_key():
            result["reason"] = "OPENAI_API_KEY 미설정 (DALL-E)"
            return result
        img = oa.generate_image(prompt, live=True)
        result.update({
            "executed": True,
            "provider": "openai_dalle",
            "image": img,
            "external_call": True,
            "reason": "DALL-E 호출 완료" if img else "DALL-E 응답 없음",
        })
        return result

    if primary_key == "gemini":
        try:
            from . import gemini_runtime as gm  # type: ignore
        except Exception as e:
            result["reason"] = f"gemini_runtime import 실패: {e}"
            return result
        if not gm.has_api_key():
            result["reason"] = "GOOGLE_API_KEY 미설정 — .env에 키를 채워주세요"
            return result
        text = gm.generate(prompt, system=system, live=True)
        result.update({
            "executed": True,
            "provider": "google_gemini",
            "text": text,
            "external_call": True,
            "reason": "gemini 호출 완료" if text else "gemini 응답 없음",
        })
        return result

    if primary_key == "ollama":
        try:
            from . import ollama_runtime as oll  # type: ignore
        except Exception as e:
            result["reason"] = f"ollama_runtime import 실패: {e}"
            return result
        if not oll.is_alive():
            result["reason"] = "Ollama 데몬 응답 없음"
            return result
        text = oll.generate(prompt, system=system)
        result.update({
            "executed": True,
            "provider": "ollama_local",
            "text": text,
            "external_call": False,  # 로컬
            "reason": "ollama 호출 완료" if text else "ollama 응답 없음",
        })
        return result

    # gemini 등 미구현 어댑터
    result["reason"] = f"{primary_key} 어댑터 미구현 — dry-run 유지"
    return result


def write_routing_decision(task: str) -> Tuple[Path, Path]:
    """라우팅 결과를 08_reports에 보고서(md)와 핸드오프(json)로 저장."""
    decision = route(task)
    folder = ROOT / "08_reports"
    folder.mkdir(parents=True, exist_ok=True)
    base_stamp = now_stamp()
    stamp = base_stamp
    suffix = 0
    # 같은 초 내 연속 호출 시 파일 덮어쓰기 방지
    while (
        (folder / f"model_router_decision_{stamp}.md").exists()
        or (folder / f"model_router_handoff_{stamp}.json").exists()
    ):
        suffix += 1
        stamp = f"{base_stamp}_{suffix:02d}"
    md_path = folder / f"model_router_decision_{stamp}.md"
    json_path = folder / f"model_router_handoff_{stamp}.json"
    md_path.write_text(decision.to_markdown(), encoding="utf-8")
    payload = {
        "task": decision.task,
        "primary": {
            "key": decision.primary.model.key,
            "display_name": decision.primary.model.display_name,
            "role": decision.primary.model.role,
            "score": decision.primary.score,
            "reasons": decision.primary.reasons,
        },
        "runners_up": [
            {
                "key": rs.model.key,
                "display_name": rs.model.display_name,
                "score": rs.score,
            }
            for rs in decision.runners_up
        ],
        "handoff": decision.handoff,
        "created_at": decision.created_at,
    }
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return md_path, json_path


__all__ = [
    "MODEL_PROFILES",
    "MODEL_BY_KEY",
    "ModelProfile",
    "RouteScore",
    "RoutingDecision",
    "route",
    "write_routing_decision",
    "execute_routing",
]
