from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .approval import ALLOWED_DECISIONS, list_approvals
from .approval_risk import analyze_all_approval_risks, build_approval_priority_queue, build_approval_risk_summary
from .paths import ROOT
from .utils import now_stamp, write_report


def _count_files(folder: Path, pattern: str) -> int:
    return len(list(folder.glob(pattern))) if folder.exists() else 0


def _relative_app_href(path: Path) -> str:
    return "../../" + path.relative_to(ROOT).as_posix()


def _approval_title(path: Path) -> str:
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            clean = line.strip().lstrip("#").strip()
            if clean:
                return clean[:90]
    except OSError:
        return path.name
    return path.name


def _recent_execution_artifacts(limit: int = 12) -> list[dict[str, str]]:
    reports_dir = ROOT / "08_reports"
    if not reports_dir.exists():
        return []

    candidates = []
    for pattern, label in (
        ("final_checklist_*.md", "최종 체크리스트"),
        ("execution_plan_*.md", "실행 계획"),
    ):
        for path in reports_dir.glob(pattern):
            candidates.append((path.stat().st_mtime, label, path))

    artifacts = []
    for _, label, path in sorted(candidates, reverse=True)[:limit]:
        artifacts.append(
            {
                "name": path.name,
                "title": _approval_title(path),
                "kind": label,
                "modified_at": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "path": str(path),
                "href": _relative_app_href(path),
            }
        )
    return artifacts


def _approval_detail_items(limit: int = 12) -> list[dict[str, str]]:
    items = []
    risk_by_file = {risk.file_name: risk for risk in analyze_all_approval_risks()}
    for item in list_approvals()[:limit]:
        modified_at = datetime.fromtimestamp(item.path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        risk = risk_by_file.get(item.file_name)
        items.append(
            {
                "file_name": item.file_name,
                "title": _approval_title(item.path),
                "status": item.status,
                "status_label": ALLOWED_DECISIONS.get(item.status, "대기"),
                "decided_at": item.last_decision_at or "-",
                "reason": item.reason or "-",
                "modified_at": modified_at,
                "path": str(item.path),
                "risk_score": str(risk.score if risk else 0),
                "risk_level": str(risk.level if risk else "low"),
                "risk_label": str(risk.level_label if risk else "낮음"),
            }
        )
    return items


def build_dashboard_data() -> dict[str, object]:
    approvals = list_approvals()
    counts = {"pending": 0, "approved": 0, "rejected": 0}
    for item in approvals:
        if item.status in counts:
            counts[item.status] += 1
        else:
            counts["pending"] += 1

    return {
        "updated_at": now_stamp(),
        "approvals": counts,
        "approval_risk": build_approval_risk_summary(),
        "approval_items": _approval_detail_items(),
        "approval_priority_queue": build_approval_priority_queue(limit=8),
        "execution_artifacts": _recent_execution_artifacts(),
        "reports": {
            "total_reports": _count_files(ROOT / "08_reports", "*.md"),
            "approval_files": _count_files(ROOT / "09_approval", "APPROVAL_REQUIRED_*.md"),
            "meetings": _count_files(ROOT / "10_meetings", "*.md"),
        },
        "dry_runs": {
            "smartstore": _count_files(ROOT / "04_smartstore" / "dry_run", "*.*"),
            "naver_ads": _count_files(ROOT / "05_naver_ads" / "dry_run", "*.*"),
            "instagram": _count_files(ROOT / "02_marketing" / "instagram_dry_run", "*.*"),
            "schemas": _count_files(ROOT / "11_memory" / "schemas", "*.json"),
        },
        "apps": [
            {
                "name": "AI Office Simulator",
                "path": "06_apps/ai_office_simulator/index.html",
                "href": "../ai_office_simulator/index.html",
                "status": "ready",
            },
            {
                "name": "Cat Toy Recommender",
                "path": "06_apps/cat_toy_recommender/index.html",
                "href": "../cat_toy_recommender/index.html",
                "status": "ready",
            },
            {
                "name": "Dry-run Dashboard",
                "path": "06_apps/dry_run_dashboard/index.html",
                "href": "../dry_run_dashboard/index.html",
                "status": "ready",
            },
        ],
    }


def write_dashboard_data() -> tuple[Path, Path]:
    data = build_dashboard_data()
    app_dir = ROOT / "06_apps" / "dry_run_dashboard"
    app_dir.mkdir(parents=True, exist_ok=True)
    js_path = app_dir / "dashboard_data.js"
    js_path.write_text(
        "window.DRY_RUN_DASHBOARD_DATA = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )
    report = [
        "# Dry-run 통합 대시보드 데이터",
        "",
        f"- 업데이트: {data['updated_at']}",
        f"- 보고서 수: {data['reports']['total_reports']}",
        f"- 승인 대기 파일 수: {data['reports']['approval_files']}",
        f"- 스마트스토어 dry-run 파일 수: {data['dry_runs']['smartstore']}",
        f"- 네이버광고 dry-run 파일 수: {data['dry_runs']['naver_ads']}",
        f"- 인스타 dry-run 파일 수: {data['dry_runs']['instagram']}",
        "",
        "실제 외부 API 호출 없이 로컬 파일 수와 승인 상태만 집계했습니다.",
    ]
    report_path = write_report(ROOT / "08_reports", "dry_run_dashboard_data", "\n".join(report))
    return js_path, report_path


def build_realtime_status_design() -> str:
    return "\n".join(
        [
            "# AI 직원 실시간 작업 상태 연동 설계",
            "",
            "## 현재 방식",
            "",
            "- CLI 명령 시작/완료/실패를 `12_logs/ai_office_activity.jsonl`에 기록",
            "- 시뮬레이터용 최신 상태를 `06_apps/ai_office_simulator/activity_feed.js`에 반영",
            "- 브라우저는 5초마다 `activity_feed.js`를 다시 읽어 상태를 갱신",
            "",
            "## 다음 단계 설계",
            "",
            "1. 장기 실행 작업에는 heartbeat 이벤트를 10초 단위로 기록한다.",
            "2. 각 AI 직원별 진행률 필드를 추가한다.",
            "3. 실패 이벤트에는 복구 제안과 관련 로그 경로를 연결한다.",
            "4. n8n/Ollama/Telegram 연동 후에도 실제 외부 실행 전에는 dry-run 상태만 표시한다.",
            "",
            "## 안전 기준",
            "",
            "- 토큰/쿠키/API 키는 상태 피드에 포함하지 않는다.",
            "- 외부 서비스 실제 실행 여부는 승인 상태와 분리해 표시한다.",
            "- 실패해도 실제 광고/SNS/스토어 변경 명령은 자동 실행하지 않는다.",
        ]
    )


def write_realtime_status_design() -> Path:
    return write_report(ROOT / "08_reports", "realtime_status_design", build_realtime_status_design())
