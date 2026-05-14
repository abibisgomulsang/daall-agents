from __future__ import annotations

import json
import shutil
import socket
from pathlib import Path

from .approval import format_approval_request
from .paths import ROOT
from .utils import now_stamp, write_report

# 선택적 라이브 모드 — ollama_runtime가 import 가능하면 사용
try:
    from . import ollama_runtime as _runtime  # type: ignore
except Exception:  # pragma: no cover
    _runtime = None


def _command_exists(command: str) -> bool:
    return shutil.which(command) is not None


def _local_port_open(port: int, host: str = "127.0.0.1", timeout_seconds: float = 0.15) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout_seconds):
            return True
    except OSError:
        return False


def build_ollama_live_status() -> tuple[str, dict[str, object]]:
    """실제 Ollama 호출로 로컬 모델 목록을 조회한 라이브 보고서.

    `_runtime`이 import 안 됐거나 데몬이 죽어 있으면 dry-run으로 자동 폴백.
    실패해도 예외 없이 dict 반환.
    """
    if _runtime is None:
        return build_ollama_model_list_dry_run()
    summary = _runtime.status_summary()
    if not summary.get("alive"):
        # 데몬 안 살아있음 → dry-run 보고서로 폴백
        md, payload = build_ollama_model_list_dry_run()
        payload["live_attempted"] = True
        payload["live_alive"] = False
        return md, payload

    models = summary.get("models", [])
    lines = [
        "# Ollama 로컬 모델 라이브 상태 (실제 호출)",
        "",
        f"- 데몬 응답 여부: 응답 받음 (latency {summary['latency_ms']} ms)",
        f"- 베이스 URL: {summary['base_url']}",
        f"- 기본 모델: `{summary['default_model']}` "
        f"({'설치됨' if summary['default_model_present'] else '미설치'})",
        f"- 설치된 모델 수: {summary['model_count']}",
        f"- 외부 네트워크 호출 여부: 없음 (127.0.0.1 로컬만)",
        "",
        "## 설치된 모델",
        "",
        "| 이름 | 크기 | 파라미터 | 패밀리 | 양자화 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for m in models:
        lines.append(
            f"| `{m['name']}` | {m['size_gb']:.2f} GB | {m['parameters']} | "
            f"{m['family']} | {m['quantization']} |"
        )
    if not models:
        lines.append("| (모델이 설치되어 있지 않음) |  |  |  |  |")
    lines.extend([
        "",
        "## 안전 확인",
        "",
        "- 외부 네트워크 호출 여부: 없음 (모든 호출은 127.0.0.1)",
        "- 실제 모델 실행/다운로드 여부: 이 보고서에서는 없음 (목록 조회만)",
        "- 사장님 승인 없이 모델 다운로드/장시간 생성 호출 안 함",
    ])
    payload = dict(summary)
    payload["dry_run_only"] = False
    payload["live_attempted"] = True
    payload["live_alive"] = True
    return "\n".join(lines), payload


def write_ollama_live_status(reports_dir: Path | None = None) -> tuple[Path, Path]:
    md, payload = build_ollama_live_status()
    reports_folder = reports_dir or ROOT / "08_reports"
    report_path = write_report(reports_folder, "ollama_live_status", md)
    memory_folder = ROOT / "11_memory" / "integrations"
    memory_folder.mkdir(parents=True, exist_ok=True)
    json_path = memory_folder / f"ollama_live_status_{now_stamp()}.json"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return report_path, json_path


def build_ollama_model_list_dry_run() -> tuple[str, dict[str, object]]:
    command_available = _command_exists("ollama")
    port_open = _local_port_open(11434)
    payload = {
        "dry_run_only": True,
        "actual_model_list_query": False,
        "actual_model_call": False,
        "model_download": False,
        "external_network_call": False,
        "command_available": command_available,
        "local_port_11434_open": port_open,
        "endpoint": "http://127.0.0.1:11434",
        "planned_read_only_methods": [
            "ollama list",
            "GET http://127.0.0.1:11434/api/tags",
        ],
        "approval_required_before_query": True,
        "forbidden_without_approval": [
            "model_list_query",
            "model_pull",
            "model_run",
            "long_running_generation",
        ],
    }
    lines = [
        "# Ollama 로컬 모델 목록 조회 승인형 Dry-run",
        "",
        "- 실제 모델 목록 조회 여부: 조회 안 함",
        "- 실제 모델 호출 여부: 호출 안 함",
        "- 모델 다운로드 여부: 다운로드 안 함",
        "- 외부 네트워크 호출 여부: 호출 안 함",
        f"- Ollama 명령 존재 여부: {'있음' if command_available else '없음'}",
        f"- 로컬 11434 포트 상태: {'열림' if port_open else '닫힘'}",
        "",
        "## 승인 후 읽기 전용 조회 후보",
        "",
        "| 방법 | 목적 | 실제 변경 가능성 |",
        "| --- | --- | --- |",
        "| `ollama list` | 로컬 설치 모델명 확인 | 없음, 읽기 전용 |",
        "| `GET http://127.0.0.1:11434/api/tags` | Ollama 로컬 API 모델 목록 확인 | 없음, 읽기 전용 |",
        "",
        "## 승인 게이트",
        "",
        "1. 이 dry-run 보고서와 승인 파일을 먼저 확인한다.",
        "2. 사장님 승인 후 모델 목록만 읽기 전용으로 조회한다.",
        "3. 조회 결과에는 모델명/크기/수정일 같은 로컬 모델 메타데이터만 저장한다.",
        "4. 모델 실행, 모델 다운로드, 장기 생성 작업은 별도 승인 파일을 만든다.",
        "",
        "## 실패 시 fallback",
        "",
        "- Ollama가 없거나 꺼져 있으면 기존 로컬 규칙 기반 회의/광고/검수 기능을 유지한다.",
        "- 설치 또는 실행 요청은 별도 승인 후 진행한다.",
    ]
    return "\n".join(lines), payload


def write_ollama_model_list_dry_run(
    reports_dir: Path | None = None,
    memory_dir: Path | None = None,
    approval_dir: Path | None = None,
) -> tuple[Path, Path, Path]:
    report, payload = build_ollama_model_list_dry_run()
    reports_folder = reports_dir or ROOT / "08_reports"
    memory_folder = memory_dir or ROOT / "11_memory" / "integrations"
    approval_folder = approval_dir or ROOT / "09_approval"

    report_path = write_report(reports_folder, "ollama_model_list_dry_run", report)

    memory_folder.mkdir(parents=True, exist_ok=True)
    json_path = memory_folder / f"ollama_model_list_dry_run_{now_stamp()}.json"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    approval = format_approval_request(
        task_name="Ollama 로컬 모델 목록 읽기 전용 조회",
        target="로컬 Ollama 모델 목록",
        before="모델 목록 미조회 상태",
        after="승인 후 로컬 모델 목록 메타데이터만 조회",
        expected_effect="AI 회사가 사용할 로컬 모델 후보를 안전하게 파악",
        risks=[
            "로컬 Ollama 프로세스가 꺼져 있어 조회 실패 가능",
            "모델명/크기/수정일 같은 로컬 환경 메타데이터가 보고서에 저장됨",
            "모델 실행이나 다운로드로 오해하지 않도록 범위 확인 필요",
        ],
        rollback="조회 결과 파일을 폐기하고 dry-run 상태 유지",
        source_markdown=report,
    )
    approval_path = write_report(
        approval_folder,
        "APPROVAL_REQUIRED_ollama_model_list_readonly",
        approval,
    )
    return report_path, json_path, approval_path
