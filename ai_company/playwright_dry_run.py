from __future__ import annotations

from pathlib import Path

from .paths import ROOT
from .utils import write_report

TARGETS = {
    "naver_ads": {
        "name": "네이버광고",
        "blocked_actions": ["로그인 세션 사용", "입찰가 변경", "광고비 변경", "키워드 중지"],
        "safe_steps": [
            "승인 파일과 실행계획 파일을 읽는다.",
            "실제 브라우저 자동화 전 대상 URL과 조치 후보를 보고서로만 정리한다.",
            "로그인 화면 접근이 필요하면 사장님 승인 전에는 중단한다.",
            "폼 입력이나 저장 버튼 클릭은 실행하지 않는다.",
            "실제 반영 전 스크린샷과 변경 전 설정을 확보한다.",
        ],
    },
    "smartstore": {
        "name": "스마트스토어",
        "blocked_actions": ["상품명 수정", "가격 변경", "재고 변경", "이미지 업로드", "상세페이지 저장"],
        "safe_steps": [
            "상품 코드와 변경 후보를 승인 파일로 정리한다.",
            "로그인 또는 상품 수정 화면 접근 전 사장님 승인을 확인한다.",
            "상세페이지 문구/이미지는 로컬 보고서에서만 검수한다.",
            "저장 버튼 클릭은 실제 실행 승인 후 별도 단계에서만 한다.",
        ],
    },
    "sns": {
        "name": "SNS",
        "blocked_actions": ["게시물 업로드", "릴스 게시", "댓글/DM 발송", "광고 집행"],
        "safe_steps": [
            "게시 문구와 해시태그를 로컬 파일로만 생성한다.",
            "이미지 저작권과 가격/재고/링크를 검수한다.",
            "업로드 화면 접근이나 게시 버튼 클릭은 승인 전 금지한다.",
        ],
    },
}


def build_playwright_dry_run(target: str) -> str:
    if target not in TARGETS:
        allowed = ", ".join(sorted(TARGETS))
        raise ValueError(f"target은 다음 중 하나여야 합니다: {allowed}")

    config = TARGETS[target]
    lines = [
        f"# Playwright Dry-run 설계: {config['name']}",
        "",
        "- 실제 브라우저 실행 여부: 실행 안 함",
        "- 외부 사이트 로그인 여부: 로그인 안 함",
        "- 실제 저장/게시/입찰 변경 여부: 실행 안 함",
        "",
        "## 안전 단계",
        "",
    ]
    lines.extend(f"{index}. {step}" for index, step in enumerate(config["safe_steps"], start=1))
    lines.extend(
        [
            "",
            "## 금지 액션",
            "",
        ]
    )
    lines.extend(f"- {action}" for action in config["blocked_actions"])
    lines.extend(
        [
            "",
            "## 자동화 골격",
            "",
            "```python",
            "def run_dry_run(page):",
            "    # 1. 승인 파일과 실행계획을 먼저 확인",
            "    # 2. 로그인/저장/게시/결제/입찰 변경은 수행하지 않음",
            "    # 3. 실제 실행 전 스크린샷과 변경 전 값을 확보",
            "    return {'status': 'dry_run_only'}",
            "```",
            "",
            "## 결론",
            "",
            "이 문서는 실제 Playwright 실행 전 설계 파일입니다. 외부 사이트 조작은 사장님 승인 후 별도 단계에서만 진행합니다.",
        ]
    )
    return "\n".join(lines)


def write_playwright_dry_run(target: str) -> Path:
    md = build_playwright_dry_run(target)
    return write_report(ROOT / "08_reports", f"playwright_dry_run_{target}", md)
