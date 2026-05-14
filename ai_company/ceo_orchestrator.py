"""CEO 오케스트레이터 — 사장님 명령을 받아 작업을 분해·우선순위화하고
AI 회의 소집과 실행 준비를 조율한다.

흐름 안에서의 위치:

    Hermes → AgentAU/n8n → [CEO 오케스트레이터] → 모델 라우터 → AI 회의 → 실행 준비

CEO는 **결정 권한자**가 아니라 **흐름의 매니저**다. 실제 외부 채널 반영은
끝까지 사장님 승인 후에만 일어난다.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .model_router import RoutingDecision, route as _route


@dataclass
class CEOWorkPlan:
    """CEO가 작업을 분해한 결과."""

    task: str
    subtasks: List[str] = field(default_factory=list)
    primary_owner: str = "데이터 AI"  # AI 직원 이름
    needs_meeting: bool = True
    needs_execution_prep: bool = True
    risks: List[str] = field(default_factory=list)
    routing: Optional[RoutingDecision] = None

    def to_markdown(self) -> str:
        lines = ["# CEO 오케스트레이터 작업 분해", ""]
        lines.append(f"- 입력 작업: {self.task}")
        lines.append(f"- 1차 책임 직원: {self.primary_owner}")
        if self.routing is not None:
            lines.append(
                f"- 라우터 1순위 모델: **{self.routing.primary.model.display_name}** "
                f"({self.routing.primary.model.role})"
            )
        lines.append(f"- AI 회의 필요: {'예' if self.needs_meeting else '아니오'}")
        lines.append(f"- 실행 준비 필요: {'예' if self.needs_execution_prep else '아니오'}")
        lines.append("")
        lines.append("## 작업 분해 (서브태스크)")
        for i, st in enumerate(self.subtasks, 1):
            lines.append(f"{i}. {st}")
        if self.risks:
            lines.append("")
            lines.append("## 사장님 확인 필요 위험 요소")
            for r in self.risks:
                lines.append(f"- {r}")
        return "\n".join(lines)


# 의도 키워드 → 1차 책임 직원
_OWNER_MAP = [
    (("비디오", "영상", "편집", "타임라인", "쇼츠 편집", "자막 편집", "ffmpeg", "MoviePy"), "비디오 AI"),
    (("회의", "토론", "결정"), "CEO"),
    (("광고", "릴스", "썸네일", "후킹", "카피"), "마케팅 AI"),
    (("SNS", "인스타", "릴스"), "SNS AI"),
    (("이미지", "디자인", "비주얼", "그래픽"), "이미지 AI"),
    (("스마트스토어", "상세페이지", "상품"), "상품 AI"),
    (("네이버광고", "ROAS", "CTR", "CPC", "키워드"), "네이버광고 AI"),
    (("코딩", "코드", "API", "앱", "백엔드", "스크립트"), "개발 AI"),
    (("CSV", "엑셀", "데이터", "매출", "분석", "리포트"), "데이터 AI"),
    (("검수", "검토", "리뷰", "확인", "체크"), "검수 AI"),
    (("리서치", "트렌드", "조사", "경쟁사", "아이디어"), "리서처 AI"),
]


def _detect_owner(task: str) -> str:
    for keywords, owner in _OWNER_MAP:
        if any(k in task for k in keywords):
            return owner
    return "CEO"  # 모호하면 CEO가 직접


def _detect_risks(task: str) -> List[str]:
    risks: List[str] = []
    risk_words = {
        "입찰가": "광고비/입찰가 변경 위험 — 사장님 명시 승인 필요",
        "광고비": "광고 예산 변경 위험 — 사장님 명시 승인 필요",
        "업로드": "외부 SNS/스토어 업로드 위험 — 승인 파일 생성",
        "게시": "SNS 게시 위험 — 승인 파일 생성",
        "발송": "메시지 발송 위험 — 승인 파일 생성",
        "결제": "결제 위험 — 절대 자동 진행 안 함",
        "환불": "환불 위험 — 절대 자동 진행 안 함",
        "로그인": "외부 로그인 위험 — 사장님이 직접 로그인",
    }
    for w, msg in risk_words.items():
        if w in task:
            risks.append(msg)
    return risks


def _decompose(task: str, owner: str) -> List[str]:
    """오너 별 기본 서브태스크."""
    if owner == "비디오 AI":
        return [
            "SNS 대본을 컷 단위로 분할",
            "9:16 타임라인 설계(시작/끝/자막/BGM)",
            "MoviePy 기반 Python 자동 편집 스크립트 초안",
            "SRT 자막 초안 + ffmpeg 합성 명령",
            "BGM 라이선스 확인 후 09_approval 승인 흐름",
        ]
    if owner == "마케팅 AI":
        return [
            "후킹 문구 3안 (공감형/문제제기형/혜택형)",
            "릴스 15초 대본 1안",
            "썸네일 카피 + 비주얼 가이드",
            "검수 AI 협업 — 과장광고/저작권 점검",
        ]
    if owner == "이미지 AI":
        return [
            "1:1 / 4:5 / 9:16 비율별 메인 카피",
            "비주얼 컨셉 설명 (배경/구도/조명)",
            "제작 도구 안내 (DALL-E / SD / Canva)",
            "저작권/초상권 체크리스트",
        ]
    if owner == "네이버광고 AI":
        return [
            "키워드별 CTR/CPC/ROAS 표 생성",
            "낭비 키워드 후보 분류",
            "광고 문구/랜딩 일치도 점검",
            "변경 후보 — 09_approval 승인 파일 작성",
        ]
    if owner == "상품 AI":
        return [
            "상품 데이터 가져오기 dry-run",
            "리뷰 키워드 클러스터링",
            "상세페이지 첫 단락 개선안",
            "옵션/세트/리필 전략 제안",
        ]
    if owner == "개발 AI":
        return [
            "현재 폴더 구조 + 의존성 점검",
            "코드 변경/추가 계획서",
            "테스트 케이스 추가 또는 dry-run",
            "사장님 검토 후 적용",
        ]
    if owner == "데이터 AI":
        return [
            "원천 데이터 위치/형식 확인",
            "지표 분리: 노출/클릭/전환/ROAS/매출",
            "이상치/저효율 항목 추출",
            "주간 리포트 dry-run 작성",
        ]
    if owner == "리서처 AI":
        return [
            "타깃 키워드/시장 식별",
            "최근 3개월 트렌드 요약",
            "경쟁사 3~5곳 비교",
            "사장님이 결정할 후보 아이디어 묶음",
        ]
    if owner == "검수 AI":
        return [
            "과장광고/효능 표현 점검",
            "저작권/개인정보 위험 점검",
            "브랜드 톤 일치 여부 점검",
            "통과/재작성 후보 분리",
        ]
    if owner == "SNS AI":
        return [
            "릴스 후킹 2초 시안 3개",
            "본문 카피 / 해시태그 / 캘린더",
            "검수 AI 협업 점검",
            "업로드 승인 파일 작성",
        ]
    # CEO
    return [
        "주제 명확화 — 무엇을 결정할 회의인지",
        "관련 직원 의견 수집",
        "결론 + 실행 후보 도출",
        "09_approval 승인 흐름 명시",
    ]


def build_plan(task: str, routing: Optional[RoutingDecision] = None) -> CEOWorkPlan:
    """사장님 명령을 받아 CEO가 분해한 계획서를 만든다."""
    if not task or not task.strip():
        raise ValueError("작업 설명이 비어 있습니다.")
    owner = _detect_owner(task)
    subtasks = _decompose(task, owner)
    risks = _detect_risks(task)
    return CEOWorkPlan(
        task=task,
        subtasks=subtasks,
        primary_owner=owner,
        needs_meeting=True,
        needs_execution_prep=True,
        risks=risks,
        routing=routing or _route(task),
    )


__all__ = ["CEOWorkPlan", "build_plan"]
