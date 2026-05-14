from __future__ import annotations

import csv
import json
from pathlib import Path

from .paths import ROOT
from .utils import now_stamp, write_report

TARGET_FIELDS = [
    {"name": "originProductNo", "required": False, "write_risk": "high", "note": "스마트스토어 원상품 번호"},
    {"name": "channelProductNo", "required": False, "write_risk": "high", "note": "채널 상품 번호"},
    {"name": "name", "required": True, "write_risk": "high", "note": "상품명"},
    {"name": "salePrice", "required": True, "write_risk": "critical", "note": "판매가"},
    {"name": "stockQuantity", "required": False, "write_risk": "critical", "note": "재고 수량"},
    {"name": "saleStatus", "required": False, "write_risk": "high", "note": "판매 상태"},
    {"name": "detailContent", "required": False, "write_risk": "high", "note": "상세페이지 HTML"},
    {"name": "representativeImage", "required": False, "write_risk": "high", "note": "대표 이미지"},
    {"name": "categoryId", "required": False, "write_risk": "medium", "note": "카테고리"},
    {"name": "customProductCode", "required": True, "write_risk": "low", "note": "내부 상품 코드"},
    {"name": "searchTags", "required": False, "write_risk": "medium", "note": "검색 태그"},
]

LOCAL_TO_TARGET = [
    {"local": "product_code", "target": "customProductCode", "transform": "string 그대로", "mode": "read"},
    {"local": "product_name", "target": "name", "transform": "공백 정리 후 문자열", "mode": "read_then_approval_required_write"},
    {"local": "price", "target": "salePrice", "transform": "정수 원화", "mode": "read_then_approval_required_write"},
    {"local": "tags", "target": "searchTags", "transform": "'|'를 배열로 분리", "mode": "read_then_approval_required_write"},
    {"local": "main_feature", "target": "detailContent", "transform": "상세페이지 초안 입력값", "mode": "draft_only"},
]


def _read_csv_headers(csv_path: Path) -> list[str]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        return next(reader)


def build_smartstore_field_mapping(csv_path: Path | None = None) -> tuple[str, dict[str, object]]:
    csv_path = csv_path or ROOT / "data" / "products.csv"
    headers = _read_csv_headers(csv_path)
    missing_local = sorted({item["local"] for item in LOCAL_TO_TARGET} - set(headers))
    unmapped_local = sorted(set(headers) - {item["local"] for item in LOCAL_TO_TARGET})
    mapped_targets = {item["target"] for item in LOCAL_TO_TARGET}
    unmapped_required_targets = [
        item["name"]
        for item in TARGET_FIELDS
        if item["required"] and item["name"] not in mapped_targets
    ]

    spec = {
        "source_csv": str(csv_path),
        "actual_login": False,
        "actual_api_call": False,
        "mutation_allowed": False,
        "local_headers": headers,
        "target_fields": TARGET_FIELDS,
        "field_mapping": LOCAL_TO_TARGET,
        "missing_local_fields": missing_local,
        "unmapped_local_fields": unmapped_local,
        "unmapped_required_targets": unmapped_required_targets,
        "blocked_write_fields": [
            "name",
            "salePrice",
            "stockQuantity",
            "saleStatus",
            "detailContent",
            "representativeImage",
        ],
    }

    lines = [
        "# 스마트스토어 상품 데이터 필드 매핑 설계",
        "",
        "- 실제 로그인 여부: 로그인 안 함",
        "- 실제 API 호출 여부: 호출 안 함",
        "- 상품 수정/가격/재고/상세페이지 저장 여부: 실행 안 함",
        f"- 로컬 기준 CSV: `{csv_path}`",
        "",
        "## 로컬 필드 → 스마트스토어 후보 필드",
        "",
        "| 로컬 필드 | 스마트스토어 후보 필드 | 변환 | 모드 |",
        "| --- | --- | --- | --- |",
    ]
    for item in LOCAL_TO_TARGET:
        lines.append(f"| {item['local']} | {item['target']} | {item['transform']} | {item['mode']} |")

    lines.extend(
        [
            "",
            "## 필수 점검",
            "",
            f"- 누락된 로컬 필드: {', '.join(missing_local) if missing_local else '없음'}",
            f"- 매핑되지 않은 로컬 필드: {', '.join(unmapped_local) if unmapped_local else '없음'}",
            f"- 매핑되지 않은 필수 타깃 필드: {', '.join(unmapped_required_targets) if unmapped_required_targets else '없음'}",
            "",
            "## 쓰기 차단 필드",
            "",
        ]
    )
    lines.extend(f"- {field}" for field in spec["blocked_write_fields"])
    lines.extend(
        [
            "",
            "## 다음 단계",
            "",
            "- 실제 API 읽기 연동 전 승인 파일 확인",
            "- API 키/토큰/쿠키 값은 출력하지 않음",
            "- 최초 연동은 읽기 전용으로만 설계",
            "- 상품 수정, 가격, 재고, 상세페이지 저장은 별도 최종 승인 필요",
        ]
    )
    return "\n".join(lines), spec


def write_smartstore_field_mapping(csv_path: Path | None = None) -> tuple[Path, Path]:
    report, spec = build_smartstore_field_mapping(csv_path)
    report_path = write_report(ROOT / "08_reports", "smartstore_field_mapping", report)
    folder = ROOT / "04_smartstore" / "dry_run"
    folder.mkdir(parents=True, exist_ok=True)
    json_path = folder / f"smartstore_field_mapping_{now_stamp()}.json"
    json_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    return report_path, json_path
