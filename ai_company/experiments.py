from __future__ import annotations

import json
from pathlib import Path

from .meeting import meeting_to_markdown, run_meeting
from .paths import ROOT
from .utils import now_stamp, write_report


def build_experiment_plan(topic: str) -> tuple[str, dict[str, object]]:
    meeting = run_meeting(topic)
    experiments = [
        {
            "id": "EXP-001",
            "name": "공감형 후킹 문구 테스트",
            "hypothesis": "집사의 고민을 먼저 짚는 문구가 제품 설명형 문구보다 클릭률을 높인다.",
            "variants": [
                "사줘도 안 놀던 고양이, 장난감 문제가 아닐 수 있어요.",
                "고스틱, 고양이의 사냥 스위치를 다시 켜는 놀이템.",
            ],
            "metric": "CTR",
            "guardrail": "과장 표현, 치료/효능 표현 금지",
        },
        {
            "id": "EXP-002",
            "name": "릴스 첫 2초 썸네일 테스트",
            "hypothesis": "고양이 반응 장면을 첫 화면에 둔 릴스가 정적 상품 컷보다 유지율을 높인다.",
            "variants": [
                "고양이가 장난감을 보는 순간",
                "상품 컷과 카피 중심 썸네일",
            ],
            "metric": "2초 유지율, 저장, 공유",
            "guardrail": "저작권 확인된 영상/이미지만 사용",
        },
        {
            "id": "EXP-003",
            "name": "리필/세트 메시지 테스트",
            "hypothesis": "본품 단독보다 리필/세트 구매 포인트를 함께 제시하면 객단가가 개선된다.",
            "variants": [
                "고스틱 본품 중심",
                "고스틱 본품 + 리필 세트 중심",
            ],
            "metric": "전환율, 객단가, ROAS",
            "guardrail": "가격/재고/배송 문구는 실제 반영 전 재확인",
        },
    ]
    payload = {
        "topic": topic,
        "approval_required": True,
        "dry_run_only": True,
        "experiments": experiments,
    }
    lines = [
        f"# AI 회의 기반 자동 실험 설계: {topic}",
        "",
        "## 회의 요약",
        "",
        meeting_to_markdown(meeting),
        "",
        "## 실험 후보",
        "",
    ]
    for item in experiments:
        lines.extend(
            [
                f"### {item['id']} {item['name']}",
                "",
                f"- 가설: {item['hypothesis']}",
                f"- 핵심 지표: {item['metric']}",
                f"- 안전 기준: {item['guardrail']}",
                "- 변형안:",
            ]
        )
        lines.extend(f"  - {variant}" for variant in item["variants"])
        lines.append("")
    lines.extend(
        [
            "## 실행 조건",
            "",
            "- 현재 문서는 dry-run 실험 설계입니다.",
            "- 실제 광고/SNS/스마트스토어 반영 전 승인 파일을 확인해야 합니다.",
            "- 실험 시작 전 변경 전 상태와 지표 기준선을 저장해야 합니다.",
        ]
    )
    return "\n".join(lines), payload


def write_experiment_plan(topic: str) -> tuple[Path, Path]:
    md, payload = build_experiment_plan(topic)
    report_path = write_report(ROOT / "08_reports", "experiment_plan", md)
    folder = ROOT / "08_reports"
    folder.mkdir(parents=True, exist_ok=True)
    json_path = folder / f"experiment_plan_{now_stamp()}.json"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return report_path, json_path
