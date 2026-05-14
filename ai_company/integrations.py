from __future__ import annotations

import shutil
from dataclasses import dataclass
import json
from pathlib import Path

from dotenv import dotenv_values

from .approval import format_approval_request
from .paths import ROOT
from .utils import now_stamp, write_report


@dataclass(frozen=True)
class IntegrationStatus:
    name: str
    status: str
    safe_detail: str
    next_step: str
    approval_required: bool


def _env_presence(keys: list[str]) -> dict[str, bool]:
    env_path = ROOT / ".env"
    values = dotenv_values(env_path) if env_path.exists() else {}
    return {key: bool(values.get(key)) for key in keys}


def _command_exists(command: str) -> bool:
    return shutil.which(command) is not None


def _reports_dir(path: Path | None = None) -> Path:
    return path or ROOT / "08_reports"


def check_integrations() -> list[IntegrationStatus]:
    env = _env_presence(["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "N8N_WEBHOOK_URL"])
    docker_ok = _command_exists("docker")
    ollama_ok = _command_exists("ollama")
    node_ok = _command_exists("node")
    npm_ok = _command_exists("npm")
    n8n_ok = _command_exists("n8n")

    telegram_ready = env["TELEGRAM_BOT_TOKEN"] and env["TELEGRAM_CHAT_ID"]
    n8n_ready = env["N8N_WEBHOOK_URL"] or n8n_ok

    return [
        IntegrationStatus(
            name="Telegram Bot",
            status="ready" if telegram_ready else "not_configured",
            safe_detail="토큰/채팅 ID 존재 여부만 확인했습니다. 값은 출력하지 않았습니다.",
            next_step="토큰과 chat_id가 준비되면 dry-run 메시지 파일을 먼저 생성합니다.",
            approval_required=True,
        ),
        IntegrationStatus(
            name="n8n Webhook",
            status="ready" if n8n_ready else "not_configured",
            safe_detail=f"n8n 명령: {'있음' if n8n_ok else '없음'}, Docker: {'있음' if docker_ok else '없음'}, webhook URL: {'있음' if env['N8N_WEBHOOK_URL'] else '없음'}",
            next_step="webhook URL 또는 n8n 설치 방식 확정 후 dry-run workflow를 연결합니다.",
            approval_required=True,
        ),
        IntegrationStatus(
            name="Ollama",
            status="ready" if ollama_ok else "not_installed",
            safe_detail=f"Ollama 명령: {'있음' if ollama_ok else '없음'}, Node: {'있음' if node_ok else '없음'}, npm: {'있음' if npm_ok else '없음'}",
            next_step="설치되어 있으면 모델 목록만 조회하고, 미설치면 설치 승인 파일을 만듭니다.",
            approval_required=not ollama_ok,
        ),
    ]


def render_integration_status(statuses: list[IntegrationStatus]) -> str:
    lines = [
        "# 외부 연동 준비 상태",
        "",
        "| 연동 | 상태 | 안전 확인 | 다음 단계 | 승인 필요 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in statuses:
        lines.append(
            f"| {item.name} | {item.status} | {item.safe_detail} | {item.next_step} | {'필요' if item.approval_required else '불필요'} |"
        )
    lines.extend(
        [
            "",
            "## 안전 원칙",
            "",
            "- 토큰, chat_id, webhook URL 값은 출력하지 않습니다.",
            "- 실제 메시지 발송, 외부 webhook 호출, 모델 설치는 사장님 승인 후 진행합니다.",
            "- 현재 단계는 로컬 dry-run 준비 상태 점검입니다.",
        ]
    )
    return "\n".join(lines)


def write_integration_status_report() -> Path:
    return write_report(ROOT / "08_reports", "integration_status", render_integration_status(check_integrations()))


def write_integration_approval_requests() -> list[Path]:
    statuses = check_integrations()
    paths: list[Path] = []
    for item in statuses:
        if not item.approval_required:
            continue
        md = format_approval_request(
            task_name=f"{item.name} 외부 연동 준비",
            target=item.name,
            before="로컬 dry-run 준비 상태",
            after="외부 연동 또는 설치/호출 가능 상태",
            expected_effect="AI 회사가 외부 명령 수신, 자동화, 로컬 모델 실행을 준비",
            risks=[
                "토큰 또는 webhook 설정 오류",
                "실제 메시지 발송 가능성",
                "외부 서비스 호출 또는 설치 작업 필요",
            ],
            rollback="연동 설정 비활성화, 토큰 제거, webhook 비활성화",
            source_markdown=render_integration_status([item]),
        )
        safe_name = item.name.lower().replace(" ", "_")
        paths.append(write_report(ROOT / "09_approval", f"APPROVAL_REQUIRED_integration_{safe_name}", md))
    return paths


def write_telegram_dry_run(message: str, reports_dir: Path | None = None) -> Path:
    md = "\n".join(
        [
            "# Telegram 메시지 Dry-run",
            "",
            "- 실제 발송 여부: 발송 안 함",
            "- 토큰 출력 여부: 출력 안 함",
            "- chat_id 출력 여부: 출력 안 함",
            "",
            "## 메시지 초안",
            "",
            message,
            "",
            "## 실행 전 확인",
            "",
            "- `TELEGRAM_BOT_TOKEN` 존재 여부 확인",
            "- `TELEGRAM_CHAT_ID` 존재 여부 확인",
            "- 사장님 승인 파일 확인",
            "- 실제 발송 직전 메시지 문구 재검수",
        ]
    )
    return write_report(_reports_dir(reports_dir), "telegram_dry_run", md)


def write_n8n_payload_sample(task: str, reports_dir: Path | None = None) -> Path:
    payload = {
        "source": "ai_company_dry_run",
        "dry_run": True,
        "task": task,
        "requested_outputs": ["08_reports", "09_approval"],
        "approval_required": True,
        "forbidden_actions": [
            "actual_upload",
            "ad_bid_change",
            "payment",
            "customer_message",
        ],
    }
    folder = _reports_dir(reports_dir)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"n8n_payload_sample_{now_stamp()}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def write_ollama_dry_run(prompt: str, reports_dir: Path | None = None) -> Path:
    ollama_ok = _command_exists("ollama")
    md = "\n".join(
        [
            "# Ollama 로컬 모델 Dry-run",
            "",
            f"- Ollama 명령 존재 여부: {'있음' if ollama_ok else '없음'}",
            "- 실제 모델 호출 여부: 호출 안 함",
            "- 모델 다운로드 여부: 다운로드 안 함",
            "",
            "## 프롬프트 초안",
            "",
            prompt,
            "",
            "## 연결 설계",
            "",
            "1. 사장님 승인 후 Ollama 설치 또는 실행 상태를 확인한다.",
            "2. 모델 목록 조회 전 승인 상태를 확인한다.",
            "3. 회의/광고/검수 업무에 사용할 모델명을 설정한다.",
            "4. 실패 시 기존 오프라인 규칙 기반 응답으로 fallback한다.",
        ]
    )
    return write_report(_reports_dir(reports_dir), "ollama_dry_run", md)
