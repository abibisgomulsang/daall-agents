from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

from .approval import list_approvals
from .paths import ROOT
from .utils import write_report

TIMESTAMP_RE = re.compile(r"_[0-9]{8}_[0-9]{6}")


def _normalized_key(file_name: str) -> str:
    stem = Path(file_name).stem
    stem = stem.removeprefix("APPROVAL_REQUIRED_")
    return TIMESTAMP_RE.sub("", stem)


def build_approval_cleanup_summary(
    approval_dir: Path | None = None,
    stale_hours: int = 12,
) -> dict[str, object]:
    items = list_approvals(approval_dir)
    now = datetime.now()
    stale_before = now - timedelta(hours=stale_hours)
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    stale = []

    for item in items:
        modified = datetime.fromtimestamp(item.path.stat().st_mtime)
        record = {
            "file_name": item.file_name,
            "status": item.status,
            "modified_at": modified.strftime("%Y-%m-%d %H:%M:%S"),
            "path": str(item.path),
        }
        groups[_normalized_key(item.file_name)].append(record)
        if modified < stale_before and item.status == "pending":
            stale.append(record)

    duplicate_groups = [
        {"key": key, "count": len(records), "files": sorted(records, key=lambda record: record["modified_at"], reverse=True)}
        for key, records in sorted(groups.items())
        if len(records) > 1
    ]

    return {
        "total": len(items),
        "duplicate_groups": duplicate_groups,
        "stale_hours": stale_hours,
        "stale": sorted(stale, key=lambda record: record["modified_at"]),
    }


def render_approval_cleanup_report(summary: dict[str, object]) -> str:
    lines = [
        "# 승인 파일 중복/오래된 요청 정리 리포트",
        "",
        "- 실제 삭제 여부: 삭제 안 함",
        "- 목적: 승인 파일 정리 후보를 사람이 확인하기 쉽게 표시",
        f"- 전체 승인 파일: {summary['total']}개",
        f"- 중복 그룹: {len(summary['duplicate_groups'])}개",
        f"- 오래된 대기 요청 기준: {summary['stale_hours']}시간",
        f"- 오래된 대기 요청: {len(summary['stale'])}개",
        "",
        "## 중복 그룹",
        "",
    ]
    duplicate_groups = summary["duplicate_groups"]
    if not duplicate_groups:
        lines.append("- 중복 승인 요청 후보 없음")
    else:
        for group in duplicate_groups:
            lines.append(f"### {group['key']} ({group['count']}개)")
            for index, item in enumerate(group["files"], start=1):
                keep_note = "최신 유지 후보" if index == 1 else "이전 요청 후보"
                lines.append(f"- {keep_note}: {item['file_name']} / {item['modified_at']} / {item['status']}")
            lines.append("")

    lines.extend(
        [
            "## 오래된 대기 요청",
            "",
        ]
    )
    stale = summary["stale"]
    if not stale:
        lines.append("- 오래된 대기 요청 후보 없음")
    else:
        for item in stale:
            lines.append(f"- {item['file_name']} / {item['modified_at']} / {item['status']}")

    lines.extend(
        [
            "",
            "## 안전 메모",
            "",
            "- 이 리포트는 정리 후보만 보여준다.",
            "- 승인 파일 삭제, 대량 삭제, 외부 실행은 하지 않는다.",
            "- 삭제가 필요하면 별도 승인 후 개별 파일 단위로 처리해야 한다.",
        ]
    )
    return "\n".join(lines)


def write_approval_cleanup_report(
    approval_dir: Path | None = None,
    reports_dir: Path | None = None,
    stale_hours: int = 12,
) -> Path:
    summary = build_approval_cleanup_summary(approval_dir, stale_hours)
    return write_report(
        reports_dir or ROOT / "08_reports",
        "approval_cleanup_report",
        render_approval_cleanup_report(summary),
    )
