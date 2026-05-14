from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .approval import list_approvals
from .paths import ROOT
from .utils import write_report


@dataclass(frozen=True)
class RiskRule:
    keyword: str
    weight: int
    reason: str


@dataclass(frozen=True)
class ApprovalRisk:
    file_name: str
    score: int
    level: str
    level_label: str
    matched_keywords: list[str]
    safety_signals: list[str]
    path: Path


RISK_RULES = [
    RiskRule("결제", 30, "금전 처리"),
    RiskRule("주문", 30, "주문 처리"),
    RiskRule("환불", 30, "환불 처리"),
    RiskRule("고객 메시지", 30, "고객 직접 발송"),
    RiskRule("비밀번호", 30, "인증 정보"),
    RiskRule("쿠키", 30, "세션 정보"),
    RiskRule("토큰", 30, "인증 토큰"),
    RiskRule("API 키", 30, "API 인증 정보"),
    RiskRule("로그인", 24, "외부 서비스 로그인"),
    RiskRule("입찰가", 24, "광고 입찰 변경"),
    RiskRule("광고비", 24, "광고 예산 변경"),
    RiskRule("업로드", 22, "외부 채널 업로드"),
    RiskRule("게시", 22, "외부 채널 게시"),
    RiskRule("발송", 22, "외부 발송"),
    RiskRule("상품 수정", 20, "상품 정보 변경"),
    RiskRule("상세페이지", 20, "상세페이지 변경"),
    RiskRule("가격", 18, "가격 변경 가능성"),
    RiskRule("재고", 18, "재고 변경 가능성"),
    RiskRule("스마트스토어", 14, "스마트스토어 연동"),
    RiskRule("네이버광고", 14, "네이버광고 연동"),
    RiskRule("SNS", 12, "SNS 채널 연동"),
    RiskRule("인스타", 12, "인스타그램 채널 연동"),
    RiskRule("광고 집행", 12, "광고 집행 가능성"),
    RiskRule("외부 API", 12, "외부 API 연동"),
]

SAFETY_SIGNALS = [
    "dry-run",
    "실행 안 함",
    "업로드 안 함",
    "게시 안 함",
    "호출 안 함",
    "로그인 안 함",
    "승인 필요",
    "사장님 승인",
]


def _risk_level(score: int) -> tuple[str, str]:
    if score >= 70:
        return "critical", "매우 높음"
    if score >= 45:
        return "high", "높음"
    if score >= 20:
        return "medium", "보통"
    return "low", "낮음"


def analyze_approval_risk(path: Path) -> ApprovalRisk:
    text = path.read_text(encoding="utf-8", errors="ignore")
    matched_rules = [rule for rule in RISK_RULES if rule.keyword in text]
    safety_signals = [signal for signal in SAFETY_SIGNALS if signal in text]
    raw_score = sum(rule.weight for rule in matched_rules)
    safety_discount = min(18, len(safety_signals) * 3)
    score = max(0, min(100, raw_score - safety_discount))
    level, level_label = _risk_level(score)
    matched_keywords = [f"{rule.keyword}({rule.reason})" for rule in matched_rules]
    return ApprovalRisk(path.name, score, level, level_label, matched_keywords, safety_signals, path)


def analyze_all_approval_risks(approval_dir: Path | None = None) -> list[ApprovalRisk]:
    items = list_approvals(approval_dir)
    risks = [analyze_approval_risk(item.path) for item in items]
    return sorted(risks, key=lambda item: (-item.score, item.file_name))


def build_approval_risk_summary(approval_dir: Path | None = None) -> dict[str, object]:
    risks = analyze_all_approval_risks(approval_dir)
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for risk in risks:
        counts[risk.level] += 1
    return {
        "total": len(risks),
        "counts": counts,
        "top": [
            {
                "file_name": risk.file_name,
                "score": risk.score,
                "level": risk.level,
                "level_label": risk.level_label,
                "matched_keywords": risk.matched_keywords[:8],
                "safety_signals": risk.safety_signals[:8],
                "path": str(risk.path),
            }
            for risk in risks[:10]
        ],
    }


def build_approval_priority_queue(approval_dir: Path | None = None, limit: int = 12) -> list[dict[str, object]]:
    approval_items = {item.file_name: item for item in list_approvals(approval_dir)}
    queue = []
    for index, risk in enumerate(analyze_all_approval_risks(approval_dir)[:limit], start=1):
        approval = approval_items.get(risk.file_name)
        status = approval.status if approval else "pending"
        if risk.level in {"critical", "high"}:
            gate = "사장님 재확인 전 실제 실행 금지"
            next_step = "최종 체크리스트 생성 후 원본 화면/설정 백업"
        elif status == "approved":
            gate = "승인 기록 있음, 실행 직전 재확인 필요"
            next_step = "실행 계획과 현재 외부 화면 값을 대조"
        else:
            gate = "승인 대기"
            next_step = "승인 파일 내용 검토 후 보류 또는 반려 판단"
        queue.append(
            {
                "rank": index,
                "file_name": risk.file_name,
                "score": risk.score,
                "level": risk.level,
                "level_label": risk.level_label,
                "status": status,
                "gate": gate,
                "next_step": next_step,
                "matched_keywords": risk.matched_keywords[:6],
                "path": str(risk.path),
            }
        )
    return queue


def render_approval_priority_queue(queue: list[dict[str, object]]) -> str:
    lines = [
        "# 승인 파일 실행 우선순위 큐",
        "",
        "- 실제 실행 여부: 실행 안 함",
        "- 목적: 승인 파일 중 먼저 검토해야 할 항목을 위험도 기준으로 정렬",
        "",
        "| 순위 | 위험도 | 점수 | 승인 상태 | 파일 | 다음 단계 | 게이트 |",
        "| ---: | --- | ---: | --- | --- | --- | --- |",
    ]
    for item in queue:
        lines.append(
            f"| {item['rank']} | {item['level_label']} | {item['score']} | {item['status']} | "
            f"{item['file_name']} | {item['next_step']} | {item['gate']} |"
        )
    if not queue:
        lines.append("| 0 | 낮음 | 0 | - | 승인 파일 없음 | - | - |")

    lines.extend(
        [
            "",
            "## 안전 메모",
            "",
            "- 큐에 올라간 항목은 실행 후보가 아니라 검토 우선순위다.",
            "- 스마트스토어/네이버광고/SNS 실제 실행은 사장님 승인 전까지 금지다.",
            "- 결제, 고객 발송, 주문/환불, API 키 노출은 자동 진행하지 않는다.",
        ]
    )
    return "\n".join(lines)


def write_approval_priority_queue(approval_dir: Path | None = None, reports_dir: Path | None = None) -> Path:
    queue = build_approval_priority_queue(approval_dir)
    return write_report(reports_dir or ROOT / "08_reports", "approval_priority_queue", render_approval_priority_queue(queue))


def render_approval_risk_report(summary: dict[str, object]) -> str:
    counts = summary["counts"]
    lines = [
        "# 승인 파일 위험도 리포트",
        "",
        f"- 분석 대상 승인 파일: {summary['total']}개",
        f"- 매우 높음: {counts['critical']}개",
        f"- 높음: {counts['high']}개",
        f"- 보통: {counts['medium']}개",
        f"- 낮음: {counts['low']}개",
        "",
        "## 위험도 상위 승인 파일",
        "",
        "| 위험도 | 점수 | 파일 | 주요 키워드 | 안전 신호 |",
        "| --- | ---: | --- | --- | --- |",
    ]
    for item in summary["top"]:
        keywords = ", ".join(item["matched_keywords"]) or "-"
        signals = ", ".join(item["safety_signals"]) or "-"
        lines.append(f"| {item['level_label']} | {item['score']} | {item['file_name']} | {keywords} | {signals} |")

    if not summary["top"]:
        lines.append("| 낮음 | 0 | 승인 파일 없음 | - | - |")

    lines.extend(
        [
            "",
            "## 해석 기준",
            "",
            "- 이 점수는 실제 실행 위험도를 빠르게 보기 위한 로컬 휴리스틱이다.",
            "- 점수가 높아도 자동 실행하지 않는다.",
            "- 스마트스토어/네이버광고/SNS 실제 실행은 별도 승인 전까지 금지다.",
            "- API 키, 쿠키, 토큰, 비밀번호 내용은 읽거나 표시하지 않는다.",
        ]
    )
    return "\n".join(lines)


def write_approval_risk_report(approval_dir: Path | None = None, reports_dir: Path | None = None) -> Path:
    summary = build_approval_risk_summary(approval_dir)
    return write_report(reports_dir or ROOT / "08_reports", "approval_risk_report", render_approval_risk_report(summary))
