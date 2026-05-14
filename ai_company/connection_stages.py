from __future__ import annotations

import json
import shutil
import socket
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values

from .approval import format_approval_request
from .paths import ROOT
from .utils import now_stamp, write_report


@dataclass(frozen=True)
class StageConnection:
    stage: int
    name: str
    connector: str
    status: str
    safe_detail: str
    dry_run_payload: dict[str, object]
    approval_required_for_real: bool
    next_step: str


def _env_presence(keys: list[str]) -> dict[str, bool]:
    env_path = ROOT / ".env"
    values = dotenv_values(env_path) if env_path.exists() else {}
    return {key: bool(values.get(key)) for key in keys}


def _command_exists(command: str) -> bool:
    return shutil.which(command) is not None


def _local_port_open(port: int, host: str = "127.0.0.1", timeout_seconds: float = 0.15) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout_seconds):
            return True
    except OSError:
        return False


def build_stage_connections() -> list[StageConnection]:
    env = _env_presence(
        [
            "ANTHROPIC_API_KEY",
            "CLAUDE_API_KEY",
            "GEMINI_API_KEY",
            "GOOGLE_API_KEY",
            "TELEGRAM_BOT_TOKEN",
            "TELEGRAM_CHAT_ID",
            "HERMES_BASE_URL",
            "HERMES_API_KEY",
            "AGENTAU_BASE_URL",
            "AGENTAU_API_KEY",
            "N8N_WEBHOOK_URL",
        ]
    )
    ollama_command = _command_exists("ollama")
    ollama_port = _local_port_open(11434)
    n8n_command = _command_exists("n8n")
    n8n_port = _local_port_open(5678)

    claude_ready = env["ANTHROPIC_API_KEY"] or env["CLAUDE_API_KEY"]
    gemini_ready = env["GEMINI_API_KEY"] or env["GOOGLE_API_KEY"]
    telegram_ready = env["TELEGRAM_BOT_TOKEN"] and env["TELEGRAM_CHAT_ID"]
    hermes_ready = env["HERMES_BASE_URL"]
    agentau_ready = env["AGENTAU_BASE_URL"]
    n8n_ready = env["N8N_WEBHOOK_URL"] or n8n_port or n8n_command

    return [
        StageConnection(
            stage=4,
            name="Ollama 연결",
            connector="ollama",
            status="ready" if ollama_command or ollama_port else "not_ready",
            safe_detail=f"ollama 명령: {'있음' if ollama_command else '없음'}, 로컬 11434 포트: {'열림' if ollama_port else '닫힘'}",
            dry_run_payload={
                "provider": "ollama",
                "local_only": True,
                "actual_model_call": False,
                "model_download": False,
                "endpoint": "http://127.0.0.1:11434",
                "safe_prompt": "AI 회사 회의 요약 dry-run",
            },
            approval_required_for_real=not (ollama_command or ollama_port),
            next_step="Ollama가 실행 중이면 모델 목록 조회 전 승인 상태를 확인한다.",
        ),
        StageConnection(
            stage=5,
            name="Claude/Gemini API 연결",
            connector="claude_gemini",
            status="ready" if claude_ready and gemini_ready else "partial" if claude_ready or gemini_ready else "not_configured",
            safe_detail=(
                f"Claude 계열 키 존재: {'있음' if claude_ready else '없음'}, "
                f"Gemini 계열 키 존재: {'있음' if gemini_ready else '없음'}"
            ),
            dry_run_payload={
                "providers": ["claude", "gemini"],
                "actual_api_call": False,
                "key_values_exposed": False,
                "routing": {
                    "strategy": "Claude=전략/문서, Gemini=대량 아이디어/비교 검토",
                    "fallback": "로컬 규칙 기반 생성 또는 Ollama",
                },
            },
            approval_required_for_real=True,
            next_step="키 존재 확인 후에도 실제 API 호출은 승인 파일 통과 후만 진행한다.",
        ),
        StageConnection(
            stage=6,
            name="텔레그램 연결",
            connector="telegram",
            status="ready" if telegram_ready else "not_configured",
            safe_detail=(
                f"bot token 존재: {'있음' if env['TELEGRAM_BOT_TOKEN'] else '없음'}, "
                f"chat id 존재: {'있음' if env['TELEGRAM_CHAT_ID'] else '없음'}"
            ),
            dry_run_payload={
                "provider": "telegram",
                "actual_send": False,
                "message_preview": "[dry-run] AI 회사 보고서가 생성되었습니다.",
                "key_values_exposed": False,
            },
            approval_required_for_real=True,
            next_step="실제 발송 전 메시지 초안과 수신 대상을 사장님이 확인한다.",
        ),
        StageConnection(
            stage=7,
            name="Hermes AI 연결",
            connector="hermes",
            status="ready" if hermes_ready else "not_configured",
            safe_detail=(
                f"HERMES_BASE_URL 존재: {'있음' if env['HERMES_BASE_URL'] else '없음'}, "
                f"HERMES_API_KEY 존재: {'있음' if env['HERMES_API_KEY'] else '없음'}"
            ),
            dry_run_payload={
                "provider": "hermes",
                "actual_api_call": False,
                "role": "CEO 오케스트레이터 보조 또는 장기 메모리 에이전트",
                "key_values_exposed": False,
            },
            approval_required_for_real=True,
            next_step="Hermes 엔드포인트 규격이 확정되면 읽기/쓰기 범위를 분리한다.",
        ),
        StageConnection(
            stage=8,
            name="AgentAU/n8n 오케스트레이션 연결",
            connector="agentau_n8n",
            status="ready" if agentau_ready and n8n_ready else "partial" if agentau_ready or n8n_ready else "not_configured",
            safe_detail=(
                f"AgentAU URL 존재: {'있음' if env['AGENTAU_BASE_URL'] else '없음'}, "
                f"n8n webhook/로컬 존재: {'있음' if n8n_ready else '없음'}"
            ),
            dry_run_payload={
                "providers": ["agentau", "n8n"],
                "actual_webhook_call": False,
                "actual_agent_command": False,
                "workflow": ["Codex", "CEO Orchestrator", "AI Meeting", "Approval Gate", "Dry-run Output"],
                "forbidden_actions": ["actual_upload", "bid_change", "payment", "customer_message"],
            },
            approval_required_for_real=True,
            next_step="n8n webhook payload와 AgentAU 업무 큐를 dry-run으로만 왕복 테스트한다.",
        ),
    ]


def _stage_to_dict(stage: StageConnection) -> dict[str, object]:
    return {
        "stage": stage.stage,
        "name": stage.name,
        "connector": stage.connector,
        "status": stage.status,
        "safe_detail": stage.safe_detail,
        "dry_run_payload": stage.dry_run_payload,
        "approval_required_for_real": stage.approval_required_for_real,
        "next_step": stage.next_step,
    }


def build_connection_stage_report(stages: list[StageConnection] | None = None) -> tuple[str, dict[str, object]]:
    stages = stages or build_stage_connections()
    payload = {
        "actual_external_calls": False,
        "key_values_exposed": False,
        "stages": [_stage_to_dict(stage) for stage in stages],
    }
    lines = [
        "# 4~8단계 AI 연결 작업 패키지",
        "",
        "- 실제 외부 API 호출 여부: 호출 안 함",
        "- 실제 텔레그램 발송 여부: 발송 안 함",
        "- API 키/토큰/쿠키 값 출력 여부: 출력 안 함",
        "- 목적: Ollama, Claude/Gemini, Telegram, Hermes, AgentAU/n8n 연결을 승인형 dry-run 구조로 준비",
        "",
        "| 단계 | 연결 | 상태 | 안전 확인 | 실제 연결 승인 | 다음 단계 |",
        "| ---: | --- | --- | --- | --- | --- |",
    ]
    for stage in stages:
        lines.append(
            f"| {stage.stage} | {stage.name} | {stage.status} | {stage.safe_detail} | "
            f"{'필요' if stage.approval_required_for_real else '조건부 불필요'} | {stage.next_step} |"
        )

    lines.extend(
        [
            "",
            "## 실행 게이트",
            "",
            "- Claude/Gemini/Hermes/Telegram/n8n/AgentAU 실제 호출은 사장님 승인 전까지 금지",
            "- Ollama도 모델 다운로드나 장기 실행은 승인 파일 생성 후 진행",
            "- 연결 실패 시 기존 로컬 규칙 기반 AI 회사 기능으로 fallback",
        ]
    )
    return "\n".join(lines), payload


def write_connection_stage_outputs() -> tuple[Path, Path, list[Path], list[Path]]:
    stages = build_stage_connections()
    report, payload = build_connection_stage_report(stages)
    report_path = write_report(ROOT / "08_reports", "connection_stage_4_8", report)

    memory_dir = ROOT / "11_memory" / "integrations"
    memory_dir.mkdir(parents=True, exist_ok=True)
    stamp = now_stamp()
    summary_path = memory_dir / f"connection_stage_4_8_{stamp}.json"
    summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    handshake_paths = []
    for stage in stages:
        path = memory_dir / f"stage_{stage.stage:02d}_{stage.connector}_handshake_{stamp}.json"
        path.write_text(json.dumps(_stage_to_dict(stage), ensure_ascii=False, indent=2), encoding="utf-8")
        handshake_paths.append(path)

    approval_paths = []
    for stage in stages:
        if not stage.approval_required_for_real:
            continue
        approval = format_approval_request(
            task_name=f"{stage.name} 실제 연결",
            target=stage.name,
            before="로컬 dry-run 연결 설계 상태",
            after="승인 후 실제 연결 또는 호출 가능 상태",
            expected_effect="AI 회사의 외부/로컬 에이전트 협업 준비",
            risks=[
                "API 키/토큰 설정 오류",
                "실제 외부 호출 또는 메시지 발송 위험",
                "비용 발생 또는 외부 서비스 정책 위반 가능성",
            ],
            rollback="연동 설정 비활성화, dry-run 모드 유지, 관련 토큰 폐기",
            source_markdown=report,
        )
        approval_paths.append(
            write_report(
                ROOT / "09_approval",
                f"APPROVAL_REQUIRED_stage_{stage.stage:02d}_{stage.connector}_actual_connection",
                approval,
            )
        )
    return report_path, summary_path, handshake_paths, approval_paths
