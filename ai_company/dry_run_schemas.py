from __future__ import annotations

import json
from pathlib import Path

from .paths import ROOT
from .utils import now_stamp, write_report

SCHEMAS = {
    "smartstore_products": {
        "description": "스마트스토어 상품 데이터 dry-run 스키마",
        "fields": [
            {"name": "product_code", "type": "string", "required": True},
            {"name": "product_name", "type": "string", "required": True},
            {"name": "price", "type": "integer", "required": True},
            {"name": "stock", "type": "integer", "required": False},
            {"name": "status", "type": "string", "required": False},
            {"name": "detail_page_url", "type": "string", "required": False},
        ],
        "blocked_actions": ["상품명 실제 수정", "가격 변경", "재고 변경", "상세페이지 저장"],
    },
    "naver_ads_keywords": {
        "description": "네이버광고 키워드 데이터 dry-run 스키마",
        "fields": [
            {"name": "campaign", "type": "string", "required": True},
            {"name": "ad_group", "type": "string", "required": False},
            {"name": "keyword", "type": "string", "required": True},
            {"name": "bid", "type": "integer", "required": False},
            {"name": "cost", "type": "integer", "required": True},
            {"name": "clicks", "type": "integer", "required": True},
            {"name": "orders", "type": "integer", "required": True},
            {"name": "revenue", "type": "integer", "required": True},
        ],
        "blocked_actions": ["입찰가 실제 변경", "광고비 변경", "키워드 중지"],
    },
    "sns_posts": {
        "description": "SNS 게시물 dry-run 스키마",
        "fields": [
            {"name": "channel", "type": "string", "required": True},
            {"name": "caption", "type": "string", "required": True},
            {"name": "hashtags", "type": "array[string]", "required": False},
            {"name": "asset_path", "type": "string", "required": False},
            {"name": "scheduled_at", "type": "string", "required": False},
        ],
        "blocked_actions": ["실제 업로드", "게시", "DM/댓글 발송"],
    },
}


def build_schema_report(schema_name: str) -> tuple[str, dict[str, object]]:
    if schema_name not in SCHEMAS:
        allowed = ", ".join(sorted(SCHEMAS))
        raise ValueError(f"schema_name은 다음 중 하나여야 합니다: {allowed}")
    schema = SCHEMAS[schema_name]
    lines = [
        f"# Dry-run 데이터 스키마: {schema_name}",
        "",
        f"- 설명: {schema['description']}",
        "- 실제 외부 API 호출 여부: 호출 안 함",
        "",
        "## 필드",
        "",
        "| 필드 | 타입 | 필수 |",
        "| --- | --- | --- |",
    ]
    for field in schema["fields"]:
        lines.append(f"| {field['name']} | {field['type']} | {'예' if field['required'] else '아니오'} |")
    lines.extend(
        [
            "",
            "## 금지 액션",
            "",
        ]
    )
    lines.extend(f"- {action}" for action in schema["blocked_actions"])
    return "\n".join(lines), schema


def write_schema_report(schema_name: str) -> tuple[Path, Path]:
    md, schema = build_schema_report(schema_name)
    report_path = write_report(ROOT / "08_reports", f"dry_run_schema_{schema_name}", md)
    folder = ROOT / "11_memory" / "schemas"
    folder.mkdir(parents=True, exist_ok=True)
    json_path = folder / f"{schema_name}_{now_stamp()}.json"
    json_path.write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")
    return report_path, json_path
