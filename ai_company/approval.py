from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .paths import ROOT

DECISIONS_FILE = "approval_decisions.jsonl"
ALLOWED_DECISIONS = {"approved": "승인", "rejected": "반려"}


@dataclass(frozen=True)
class ApprovalItem:
    file_name: str
    path: Path
    status: str
    last_decision_at: str | None = None
    reason: str | None = None


def format_approval_request(
    task_name: str,
    target: str,
    before: str,
    after: str,
    expected_effect: str,
    risks: list[str],
    rollback: str,
    source_markdown: str,
) -> str:
    risk_lines = "\n".join(f"- {risk}" for risk in risks)
    return "\n".join(
        [
            f"# 승인 필요: {task_name}",
            "",
            f"- 작업명: {task_name}",
            f"- 변경 대상: {target}",
            f"- 변경 전: {before}",
            f"- 변경 후: {after}",
            f"- 예상 효과: {expected_effect}",
            "- 위험 요소:",
            risk_lines,
            f"- 되돌리는 방법: {rollback}",
            "- 승인 필요 여부: 필요",
            "- 현재 실행 상태: dry-run 생성만 완료",
            "",
            "## 원본 초안",
            "",
            source_markdown,
        ]
    )


def _approval_dir(path: Path | None = None) -> Path:
    return path or ROOT / "09_approval"


def _now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _load_decisions(approval_dir: Path) -> list[dict[str, str]]:
    decisions_path = approval_dir / DECISIONS_FILE
    if not decisions_path.exists():
        return []

    decisions: list[dict[str, str]] = []
    for line in decisions_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            decisions.append(json.loads(line))
    return decisions


def _latest_decision_by_file(approval_dir: Path) -> dict[str, dict[str, str]]:
    latest: dict[str, dict[str, str]] = {}
    for decision in _load_decisions(approval_dir):
        file_name = decision.get("file_name")
        if file_name:
            latest[file_name] = decision
    return latest


def list_approvals(approval_dir: Path | None = None) -> list[ApprovalItem]:
    folder = _approval_dir(approval_dir)
    folder.mkdir(parents=True, exist_ok=True)
    latest = _latest_decision_by_file(folder)
    items: list[ApprovalItem] = []

    for path in sorted(folder.glob("APPROVAL_REQUIRED_*.md"), key=lambda p: p.stat().st_mtime, reverse=True):
        decision = latest.get(path.name)
        if decision:
            status = decision.get("decision", "unknown")
            decided_at = decision.get("decided_at")
            reason = decision.get("reason")
        else:
            status = "pending"
            decided_at = None
            reason = None
        items.append(ApprovalItem(path.name, path, status, decided_at, reason))
    return items


def render_approvals(items: list[ApprovalItem]) -> str:
    if not items:
        return "승인 대기 파일이 없습니다."

    lines = [
        "# 승인 파일 목록",
        "",
        "| 상태 | 파일 | 최근 결정 시각 | 사유 |",
        "| --- | --- | --- | --- |",
    ]
    for item in items:
        status = ALLOWED_DECISIONS.get(item.status, "대기")
        lines.append(
            f"| {status} | {item.file_name} | {item.last_decision_at or '-'} | {item.reason or '-'} |"
        )
    return "\n".join(lines)


def record_decision(
    file_name: str,
    decision: str,
    reason: str,
    approval_dir: Path | None = None,
) -> Path:
    if decision not in ALLOWED_DECISIONS:
        allowed = ", ".join(sorted(ALLOWED_DECISIONS))
        raise ValueError(f"decision은 다음 중 하나여야 합니다: {allowed}")

    folder = _approval_dir(approval_dir)
    target = folder / file_name
    if not target.exists() or not target.name.startswith("APPROVAL_REQUIRED_"):
        raise FileNotFoundError(f"승인 대기 파일을 찾을 수 없습니다: {file_name}")

    decided_at = _now_stamp()
    record = {
        "file_name": target.name,
        "decision": decision,
        "decision_label": ALLOWED_DECISIONS[decision],
        "reason": reason,
        "decided_at": decided_at,
        "dry_run_only": "true",
    }

    decisions_path = folder / DECISIONS_FILE
    with decisions_path.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    md_path = folder / f"APPROVAL_DECISION_{decision}_{target.stem}_{decided_at}.md"
    original = target.read_text(encoding="utf-8")
    md = [
        f"# 승인 결정 기록: {ALLOWED_DECISIONS[decision]}",
        "",
        f"- 대상 파일: `{target.name}`",
        f"- 결정: {ALLOWED_DECISIONS[decision]}",
        f"- 결정 시각: {decided_at}",
        f"- 사유: {reason}",
        "- 실제 실행 여부: 실행 안 함",
        "",
        "## 안전 메모",
        "",
        "이 파일은 승인 상태 기록입니다. 스마트스토어/SNS/네이버광고 실제 변경은 별도 실행 명령과 사장님 재확인 후 진행해야 합니다.",
        "",
        "## 원본 승인 요청",
        "",
        original,
    ]
    md_path.write_text("\n".join(md), encoding="utf-8")
    return md_path
