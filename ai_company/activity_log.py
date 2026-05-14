from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from .approval import ALLOWED_DECISIONS, list_approvals
from .approval_risk import build_approval_priority_queue, build_approval_risk_summary
from .connection_stages import build_stage_connections
from .paths import ROOT

FEED_JS = ROOT / "06_apps" / "ai_office_simulator" / "activity_feed.js"
EVENT_LOG = ROOT / "12_logs" / "ai_office_activity.jsonl"
STATE_FILE = ROOT / "12_logs" / "ai_office_activity_state.json"

COMMAND_AGENT = {
    "init-folders": "ceo",
    "meeting": "ceo",
    "ad": "marketing",
    "analyze-ads": "ads",
    "app-ideas": "app",
    "approvals": "qa",
    "execution-plan": "ceo",
    "final-checklist": "qa",
    "office-simulator": "app",
    "integration-status": "ceo",
    "integration-approvals": "qa",
    "connection-stages": "ceo",
    "telegram-dry-run": "sns",
    "n8n-payload": "ceo",
    "ollama-dry-run": "ceo",
    "ollama-model-list-dry-run": "ceo",
    "image-templates": "image",
    "playwright-dry-run": "app",
    "cat-webapp": "app",
    "experiment-plan": "ceo",
    "share-image-design": "image",
    "share-image-export": "image",
    "dry-run-schema": "data",
    "smartstore-fetch-dry-run": "store",
    "smartstore-mapping": "store",
    "naver-ads-api-dry-run": "ads",
    "naver-ads-permission-matrix": "ads",
    "instagram-upload-dry-run": "sns",
    "instagram-asset-manifest": "sns",
    "dry-run-dashboard": "data",
    "realtime-status-design": "app",
    "activity-report": "data",
    "approval-risk-report": "qa",
    "approval-priority-queue": "ceo",
    "approval-cleanup-report": "qa",
}

COMMAND_TASK = {
    "init-folders": "폴더 구조 점검",
    "meeting": "AI 회의 진행",
    "ad": "광고 패키지 생성",
    "analyze-ads": "네이버광고 CSV 분석",
    "app-ideas": "앱 아이디어 정리",
    "approvals": "승인 파일 점검",
    "execution-plan": "실행 전 dry-run 계획",
    "final-checklist": "최종 실행 체크리스트",
    "office-simulator": "시뮬레이터 안내",
    "integration-status": "외부 연동 상태 점검",
    "integration-approvals": "외부 연동 승인 파일",
    "connection-stages": "4~8단계 AI 연결 패키지",
    "telegram-dry-run": "텔레그램 메시지 dry-run",
    "n8n-payload": "n8n payload 샘플",
    "ollama-dry-run": "Ollama 프롬프트 dry-run",
    "ollama-model-list-dry-run": "Ollama 모델 목록 조회 dry-run",
    "image-templates": "이미지 광고 템플릿",
    "playwright-dry-run": "Playwright dry-run 설계",
    "cat-webapp": "고양이 추천 웹앱 안내",
    "experiment-plan": "AI 실험 설계",
    "share-image-design": "공유 이미지 설계",
    "share-image-export": "공유 이미지 PNG export dry-run",
    "dry-run-schema": "dry-run 데이터 스키마",
    "smartstore-fetch-dry-run": "스마트스토어 데이터 dry-run",
    "smartstore-mapping": "스마트스토어 필드 매핑 설계",
    "naver-ads-api-dry-run": "네이버광고 API dry-run",
    "naver-ads-permission-matrix": "네이버광고 API 권한 매트릭스",
    "instagram-upload-dry-run": "인스타 업로드 dry-run",
    "instagram-asset-manifest": "인스타 자산 매니페스트",
    "dry-run-dashboard": "dry-run 대시보드 갱신",
    "realtime-status-design": "실시간 상태 연동 설계",
    "activity-report": "평균 소요 시간 리포트",
    "approval-risk-report": "승인 파일 위험도 점수화",
    "approval-priority-queue": "승인 실행 우선순위 큐",
    "approval-cleanup-report": "승인 파일 정리 후보 리포트",
}


@dataclass(frozen=True)
class ActivityRecord:
    command: str
    agent_id: str
    status: str
    task: str
    detail: str
    updated_at: str
    duration_seconds: float | None = None


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="milliseconds")


def _load_state(state_file: Path) -> dict[str, dict[str, str]]:
    if not state_file.exists():
        return {"active": {}}
    try:
        return json.loads(state_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"active": {}}


def _save_state(state_file: Path, state: dict[str, dict[str, str]]) -> None:
    state_file.parent.mkdir(parents=True, exist_ok=True)
    temp_path = state_file.with_name(f"{state_file.name}.{uuid4().hex}.tmp")
    temp_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    temp_path.replace(state_file)


def _duration_seconds(started_at: str, ended_at: str) -> float | None:
    try:
        start = datetime.fromisoformat(started_at)
        end = datetime.fromisoformat(ended_at)
    except ValueError:
        return None
    return round(max(0.0, (end - start).total_seconds()), 3)


def _load_recent_events(event_log: Path, limit: int = 6) -> list[dict[str, str]]:
    if not event_log.exists():
        return []
    lines = [line for line in event_log.read_text(encoding="utf-8").splitlines() if line.strip()]
    events: list[dict[str, str]] = []
    for line in lines[-limit:]:
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def _approval_summary(approval_dir: Path | None = None) -> dict[str, object]:
    items = list_approvals(approval_dir)
    counts = {"pending": 0, "approved": 0, "rejected": 0}
    for item in items:
        if item.status in counts:
            counts[item.status] += 1
        else:
            counts["pending"] += 1
    recent = [
        {
            "file_name": item.file_name,
            "status": item.status,
            "status_label": ALLOWED_DECISIONS.get(item.status, "대기"),
            "reason": item.reason or "",
        }
        for item in items[:5]
    ]
    return {"counts": counts, "recent": recent}


def _risk_queue_summary(approval_dir: Path | None = None) -> dict[str, object]:
    try:
        risk_summary = build_approval_risk_summary(approval_dir)
        priority_queue = build_approval_priority_queue(approval_dir, limit=5)
    except OSError:
        return {
            "counts": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            "queue": [],
        }
    return {
        "counts": risk_summary["counts"],
        "queue": priority_queue,
    }


def _connection_stage_summary() -> dict[str, object]:
    counts = {"ready": 0, "partial": 0, "not_configured": 0, "not_ready": 0}
    try:
        stages = build_stage_connections()
    except OSError:
        return {
            "counts": counts,
            "approval_required": 0,
            "items": [],
        }

    items = []
    approval_required = 0
    for stage in stages:
        counts[stage.status] = counts.get(stage.status, 0) + 1
        if stage.approval_required_for_real:
            approval_required += 1
        items.append(
            {
                "stage": stage.stage,
                "name": stage.name,
                "connector": stage.connector,
                "status": stage.status,
                "safe_detail": stage.safe_detail,
                "approval_required_for_real": stage.approval_required_for_real,
                "next_step": stage.next_step,
            }
        )
    return {
        "counts": counts,
        "approval_required": approval_required,
        "items": items,
    }


def _write_feed(record: ActivityRecord, feed_js: Path, event_log: Path, approval_dir: Path | None) -> None:
    feed_js.parent.mkdir(parents=True, exist_ok=True)
    events = _load_recent_events(event_log)
    agents = {
        record.agent_id: {
            "status": record.status,
            "task": record.task,
            "detail": record.detail,
            "duration_seconds": record.duration_seconds,
        }
    }
    payload = {
        "updated_at": record.updated_at,
        "source": "ai_company_cli",
        "agents": agents,
        "events": events,
        "approvals": _approval_summary(approval_dir),
        "risk_queue": _risk_queue_summary(approval_dir),
        "connection_stages": _connection_stage_summary(),
    }
    js = "window.AI_OFFICE_FEED = " + json.dumps(payload, ensure_ascii=False, indent=2) + ";\n"
    feed_js.write_text(js, encoding="utf-8")


def record_activity(
    command: str,
    status: str,
    detail: str = "",
    feed_js: Path = FEED_JS,
    event_log: Path = EVENT_LOG,
    state_file: Path = STATE_FILE,
    approval_dir: Path | None = None,
) -> ActivityRecord:
    event_log.parent.mkdir(parents=True, exist_ok=True)
    updated_at = _now_iso()
    state = _load_state(state_file)
    active_key = f"{COMMAND_AGENT.get(command, 'ceo')}:{command}"
    duration = None

    if status == "active":
        state.setdefault("active", {})[active_key] = updated_at
    elif status in {"idle", "blocked"}:
        started_at = state.setdefault("active", {}).pop(active_key, None)
        if started_at:
            duration = _duration_seconds(started_at, updated_at)
    try:
        _save_state(state_file, state)
    except OSError:
        pass

    record = ActivityRecord(
        command=command,
        agent_id=COMMAND_AGENT.get(command, "ceo"),
        status=status,
        task=COMMAND_TASK.get(command, "AI 회사 작업"),
        detail=detail,
        updated_at=updated_at,
        duration_seconds=duration,
    )
    event = {
        "time": record.updated_at,
        "command": record.command,
        "agent_id": record.agent_id,
        "status": record.status,
        "task": record.task,
        "detail": record.detail,
        "duration_seconds": record.duration_seconds,
    }
    try:
        with event_log.open("a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
        _write_feed(record, feed_js, event_log, approval_dir)
    except OSError:
        pass
    return record
