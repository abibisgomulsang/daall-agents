from __future__ import annotations

import json
from pathlib import Path

from .paths import ROOT
from .utils import now_stamp, write_report

ENDPOINT_MATRIX = [
    {
        "name": "campaign_list",
        "method": "GET",
        "scope": "read_campaign",
        "writes": False,
        "mvp_allowed": True,
        "approval_required": True,
        "blocked_reason": "",
    },
    {
        "name": "adgroup_list",
        "method": "GET",
        "scope": "read_adgroup",
        "writes": False,
        "mvp_allowed": True,
        "approval_required": True,
        "blocked_reason": "",
    },
    {
        "name": "keyword_report",
        "method": "GET",
        "scope": "read_keyword_report",
        "writes": False,
        "mvp_allowed": True,
        "approval_required": True,
        "blocked_reason": "",
    },
    {
        "name": "cost_report",
        "method": "GET",
        "scope": "read_cost_report",
        "writes": False,
        "mvp_allowed": True,
        "approval_required": True,
        "blocked_reason": "",
    },
    {
        "name": "keyword_bid_update",
        "method": "PUT",
        "scope": "write_keyword_bid",
        "writes": True,
        "mvp_allowed": False,
        "approval_required": True,
        "blocked_reason": "입찰가 실제 변경 위험",
    },
    {
        "name": "campaign_budget_update",
        "method": "PUT",
        "scope": "write_budget",
        "writes": True,
        "mvp_allowed": False,
        "approval_required": True,
        "blocked_reason": "광고비 실제 변경 위험",
    },
    {
        "name": "keyword_pause",
        "method": "PUT",
        "scope": "write_keyword_status",
        "writes": True,
        "mvp_allowed": False,
        "approval_required": True,
        "blocked_reason": "키워드 노출 중지 위험",
    },
]


def build_naver_ads_permission_matrix() -> tuple[str, dict[str, object]]:
    allowed_reads = [item for item in ENDPOINT_MATRIX if item["mvp_allowed"] and not item["writes"]]
    blocked_writes = [item for item in ENDPOINT_MATRIX if item["writes"]]
    spec = {
        "actual_api_call": False,
        "mutation_allowed": False,
        "read_endpoints_allowed_after_approval": [item["name"] for item in allowed_reads],
        "write_endpoints_blocked": [item["name"] for item in blocked_writes],
        "endpoints": ENDPOINT_MATRIX,
        "safety_gates": [
            "API 키/secret/customer id 출력 금지",
            "읽기 API도 승인 파일 확인 후 진행",
            "쓰기 API는 1차 MVP에서 전부 차단",
            "입찰가/광고비/키워드 상태 변경은 사장님 최종 승인 필요",
        ],
    }

    lines = [
        "# 네이버광고 API 읽기/쓰기 권한 매트릭스",
        "",
        "- 실제 API 호출 여부: 호출 안 함",
        "- 입찰가 변경 여부: 변경 안 함",
        "- 광고비 변경 여부: 변경 안 함",
        "- 키워드 상태 변경 여부: 변경 안 함",
        "",
        "## 엔드포인트 권한표",
        "",
        "| 엔드포인트 | 메서드 | 권한 범위 | 쓰기 | MVP 허용 | 승인 필요 | 차단 사유 |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in ENDPOINT_MATRIX:
        lines.append(
            f"| {item['name']} | {item['method']} | {item['scope']} | "
            f"{'예' if item['writes'] else '아니오'} | {'예' if item['mvp_allowed'] else '아니오'} | "
            f"{'예' if item['approval_required'] else '아니오'} | {item['blocked_reason'] or '-'} |"
        )

    lines.extend(["", "## 안전 게이트", ""])
    lines.extend(f"- {gate}" for gate in spec["safety_gates"])
    return "\n".join(lines), spec


def write_naver_ads_permission_matrix() -> tuple[Path, Path]:
    report, spec = build_naver_ads_permission_matrix()
    report_path = write_report(ROOT / "08_reports", "naver_ads_permission_matrix", report)
    folder = ROOT / "05_naver_ads" / "dry_run"
    folder.mkdir(parents=True, exist_ok=True)
    json_path = folder / f"naver_ads_permission_matrix_{now_stamp()}.json"
    json_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    return report_path, json_path
