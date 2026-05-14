from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from .paths import ROOT
from .utils import write_report


def load_activity_events(log_path: Path | None = None) -> tuple[list[dict[str, Any]], int]:
    path = log_path or ROOT / "12_logs" / "ai_office_activity.jsonl"
    if not path.exists():
        return [], 0

    events: list[dict[str, Any]] = []
    ignored = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            ignored += 1
            continue
        if isinstance(event, dict):
            events.append(event)
        else:
            ignored += 1
    return events, ignored


def build_activity_summary(events: list[dict[str, Any]], ignored_lines: int = 0) -> dict[str, Any]:
    by_command: dict[str, list[float]] = defaultdict(list)
    status_counts: dict[str, int] = defaultdict(int)
    agent_counts: dict[str, int] = defaultdict(int)
    last_seen: dict[str, str] = {}
    blocked_events: list[dict[str, Any]] = []

    for event in events:
        command = str(event.get("command") or "unknown")
        status = str(event.get("status") or "unknown")
        agent_id = str(event.get("agent_id") or "unknown")
        status_counts[status] += 1
        agent_counts[agent_id] += 1
        last_seen[command] = str(event.get("time") or "")
        if status == "blocked":
            blocked_events.append(event)

        duration = event.get("duration_seconds")
        if isinstance(duration, int | float):
            by_command[command].append(float(duration))

    command_rows = []
    for command, durations in sorted(by_command.items()):
        command_rows.append(
            {
                "command": command,
                "runs": len(durations),
                "avg_seconds": round(mean(durations), 3),
                "min_seconds": round(min(durations), 3),
                "max_seconds": round(max(durations), 3),
                "last_seen": last_seen.get(command, ""),
            }
        )

    return {
        "total_events": len(events),
        "ignored_lines": ignored_lines,
        "status_counts": dict(sorted(status_counts.items())),
        "agent_counts": dict(sorted(agent_counts.items())),
        "commands": command_rows,
        "blocked_events": blocked_events[-5:],
    }


def render_activity_report(summary: dict[str, Any]) -> str:
    lines = [
        "# AI 사무실 평균 소요 시간 리포트",
        "",
        f"- 총 이벤트 수: {summary['total_events']}",
        f"- 무시한 손상 로그 라인: {summary['ignored_lines']}",
        "",
        "## 상태별 이벤트",
        "",
        "| 상태 | 개수 |",
        "| --- | ---: |",
    ]
    for status, count in summary["status_counts"].items():
        lines.append(f"| {status} | {count} |")

    lines.extend(
        [
            "",
            "## 명령별 평균 소요 시간",
            "",
            "| 명령 | 실행 수 | 평균 초 | 최소 초 | 최대 초 | 마지막 기록 |",
            "| --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in summary["commands"]:
        lines.append(
            f"| {row['command']} | {row['runs']} | {row['avg_seconds']} | "
            f"{row['min_seconds']} | {row['max_seconds']} | {row['last_seen']} |"
        )
    if not summary["commands"]:
        lines.append("| 기록 없음 | 0 | 0 | 0 | 0 | - |")

    lines.extend(
        [
            "",
            "## AI 직원별 이벤트",
            "",
            "| 직원 | 이벤트 수 |",
            "| --- | ---: |",
        ]
    )
    for agent_id, count in summary["agent_counts"].items():
        lines.append(f"| {agent_id} | {count} |")

    lines.extend(["", "## 최근 막힘 이벤트", ""])
    if summary["blocked_events"]:
        for event in summary["blocked_events"]:
            lines.append(f"- {event.get('time', '')} / {event.get('command', '')}: {event.get('detail', '')}")
    else:
        lines.append("- 최근 막힘 이벤트 없음")

    lines.extend(
        [
            "",
            "## 안전 범위",
            "",
            "- 로컬 로그 파일만 읽음",
            "- 외부 서비스 호출 없음",
            "- 실제 업로드/입찰/결제/고객 발송 없음",
        ]
    )
    return "\n".join(lines)


def write_activity_report(log_path: Path | None = None, reports_dir: Path | None = None) -> Path:
    events, ignored = load_activity_events(log_path)
    summary = build_activity_summary(events, ignored)
    return write_report(reports_dir or ROOT / "08_reports", "ai_office_activity_report", render_activity_report(summary))
