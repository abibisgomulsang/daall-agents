from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
MAX_OUTPUT_CHARS = 1400

# nl_command 패키지 사용을 위해 프로젝트 루트를 sys.path에 추가
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
try:
    from ai_company.nl_command import interpret as _nl_interpret  # type: ignore
except Exception:  # pragma: no cover - import 실패 시 폴백
    _nl_interpret = None

try:
    from ai_company.ollama_runtime import status_summary as _ollama_status  # type: ignore
except Exception:  # pragma: no cover
    _ollama_status = None

try:
    from ai_company.claude_runtime import status_summary as _claude_status  # type: ignore
except Exception:  # pragma: no cover
    _claude_status = None

try:
    from ai_company.openai_runtime import status_summary as _openai_status  # type: ignore
except Exception:  # pragma: no cover
    _openai_status = None

try:
    from ai_company.gemini_runtime import status_summary as _gemini_status  # type: ignore
except Exception:  # pragma: no cover
    _gemini_status = None

try:
    from ai_company.usage_caps import caps_status as _caps_status  # type: ignore
except Exception:  # pragma: no cover
    _caps_status = None

try:
    from ai_company import hermes_memory as _hermes_mem  # type: ignore
    from ai_company import hermes_runtime as _hermes_rt  # type: ignore
except Exception:  # pragma: no cover
    _hermes_mem = None
    _hermes_rt = None


def _product_code(message: str) -> str:
    upper = message.upper()
    for code in ("GOSTICK01", "PLAGO01", "REFILL01"):
        if code in upper:
            return code
    return "GOSTICK01"


def _extract_quoted_text(message: str) -> str | None:
    match = re.search(r'"([^"]+)"|\'([^\']+)\'|“([^”]+)”|‘([^’]+)’', message)
    if not match:
        return None
    return next(group for group in match.groups() if group)


def _topic(message: str, default: str = "고스틱 광고 효율 개선") -> str:
    quoted = _extract_quoted_text(message)
    if quoted:
        return quoted

    for marker in ("주제:", "주제=", "topic:", "topic="):
        if marker in message:
            value = message.split(marker, 1)[1].strip()
            if value:
                return value[:80]
    return default


def plan_chat_command(message: str) -> dict[str, object]:
    """자연어 메시지를 시뮬레이터 채팅용 명령 계획으로 변환.

    1차 시도: `ai_company.nl_command.interpret()` (모델 라우터 통합)
    실패/폴백 시: 기존 키워드 분기 로직

    반환 형식 (기존 호환):
        {"ok": bool, "command": [...], "label": str, "reply": str?,
         "routing": {...}?, "intent": str?, "approval_path": str?}
    """
    text = message.strip()
    lowered = text.lower()

    if not text:
        return {
            "ok": False,
            "reply": "메시지를 입력하면 안전한 AI 회사 명령으로 실행합니다.",
            "command": [],
        }

    # 1차: nl_interpret 사용 (라우터 통합)
    if _nl_interpret is not None:
        try:
            plan = _nl_interpret(text, attach_routing=True)
        except Exception:
            plan = None
        if plan is not None and plan.intent != "empty":
            payload: dict[str, object] = {
                "ok": plan.safe_to_run and bool(plan.cli),
                "command": list(plan.cli),
                "label": plan.label,
                "intent": plan.intent,
            }
            if plan.routing is not None:
                payload["routing"] = {
                    "primary_key": plan.routing.primary.model.key,
                    "primary_name": plan.routing.primary.model.display_name,
                    "primary_role": plan.routing.primary.model.role,
                    "score": plan.routing.primary.score,
                    "runners_up": [
                        rs.model.display_name for rs in plan.routing.runners_up
                    ],
                }
            if not plan.safe_to_run:
                payload["reply"] = (
                    "위험 키워드가 포함된 요청입니다. 09_approval 파일을 만들어 두었고 "
                    "실제 실행은 사장님 승인 후에만 진행됩니다."
                )
                payload["risk_keywords"] = list(plan.risk_keywords)
                if plan.approval_path:
                    payload["approval_path"] = plan.approval_path
            return payload

    # 2차 폴백: 기존 키워드 분기
    if any(word in text for word in ("입찰", "광고비", "업로드", "게시", "발송", "결제", "주문", "환불", "로그인")):
        return {
            "ok": False,
            "reply": "실제 외부 실행이 될 수 있는 요청입니다. 승인 파일 생성/dry-run까지만 채팅에서 처리할 수 있습니다.",
            "command": [],
        }

    if "네이버" in text or "csv" in lowered or "분석" in text:
        return {
            "ok": True,
            "label": "네이버광고 샘플 CSV 분석",
            "command": ["analyze-ads", "--csv", "data/naver_ads_sample.csv"],
        }

    if "대시보드" in text or "dashboard" in lowered:
        return {
            "ok": True,
            "label": "dry-run 대시보드 갱신",
            "command": ["dry-run-dashboard"],
        }

    if "승인" in text and ("우선" in text or "큐" in text or "위험" in text):
        return {
            "ok": True,
            "label": "승인 파일 우선순위 큐 생성",
            "command": ["approval-priority-queue"],
        }

    if "승인" in text or "approval" in lowered:
        return {
            "ok": True,
            "label": "승인 파일 목록 조회",
            "command": ["approvals", "list"],
        }

    if "ollama" in lowered or "올라마" in text or ("모델" in text and "목록" in text):
        return {
            "ok": True,
            "label": "Ollama 모델 목록 조회 승인형 dry-run",
            "command": ["ollama-model-list-dry-run"],
        }

    if "연결" in text or "텔레그램" in text or "telegram" in lowered or "n8n" in lowered or "hermes" in lowered:
        return {
            "ok": True,
            "label": "4~8단계 연결 dry-run 패키지",
            "command": ["connection-stages"],
        }

    if "실험" in text or "테스트 설계" in text:
        return {
            "ok": True,
            "label": "AI 회의 기반 실험 설계",
            "command": ["experiment-plan", "--topic", _topic(text)],
        }

    if "인스타" in text or "instagram" in lowered or "sns" in lowered:
        return {
            "ok": True,
            "label": "인스타 업로드 승인형 dry-run",
            "command": ["instagram-upload-dry-run", "--product", _product_code(text)],
        }

    if "회의" in text or "meeting" in lowered:
        return {
            "ok": True,
            "label": "AI 회의 진행",
            "command": ["meeting", "--topic", _topic(text)],
        }

    if "광고" in text or "문구" in text or "릴스" in text or "ad" in lowered:
        return {
            "ok": True,
            "label": f"{_product_code(text)} 광고 패키지 생성",
            "command": ["ad", "--product", _product_code(text)],
        }

    if "시뮬레이터" in text or "office" in lowered:
        return {
            "ok": True,
            "label": "AI 사무실 시뮬레이터 위치 확인",
            "command": ["office-simulator"],
        }

    return {
        "ok": True,
        "label": "AI 회의 진행",
        "command": ["meeting", "--topic", text[:80]],
    }


def run_ai_company_command(command: list[str]) -> dict[str, object]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    full_command = [sys.executable, "-m", "ai_company.main", *command]
    completed = subprocess.run(
        full_command,
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
        shell=False,
        check=False,
    )
    output = (completed.stdout or "").strip()
    error = (completed.stderr or "").strip()
    combined = output if completed.returncode == 0 else "\n".join(part for part in (output, error) if part)
    if len(combined) > MAX_OUTPUT_CHARS:
        combined = combined[:MAX_OUTPUT_CHARS] + "\n...출력이 길어 일부만 표시했습니다."
    return {
        "returncode": completed.returncode,
        "output": combined,
        "command_line": "python -m ai_company.main " + " ".join(command),
    }


class LocalViewerHandler(SimpleHTTPRequestHandler):
    server_version = "AICompanyLocalViewer/1.0"

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def _send_json(self, status: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = unquote(urlparse(self.path).path)
        if path == "/api/health":
            self._send_json(200, {"ok": True, "service": "ai_company_local_viewer"})
            return
        if path == "/api/ollama/status":
            if _ollama_status is None:
                self._send_json(200, {"alive": False, "reason": "ollama_runtime not importable"})
                return
            try:
                payload = _ollama_status()
            except Exception as exc:  # pragma: no cover
                self._send_json(200, {"alive": False, "reason": str(exc)})
                return
            self._send_json(200, payload)
            return
        if path == "/api/providers/status":
            # 모든 모델 공급자의 상태를 한 번에 — 값/키는 노출 안 함
            providers: dict[str, object] = {}
            if _ollama_status is not None:
                try:
                    providers["ollama"] = _ollama_status()
                except Exception as exc:  # pragma: no cover
                    providers["ollama"] = {"alive": False, "reason": str(exc)}
            else:
                providers["ollama"] = {"alive": False, "reason": "not importable"}
            if _claude_status is not None:
                try:
                    providers["claude"] = _claude_status()
                except Exception as exc:  # pragma: no cover
                    providers["claude"] = {"api_key_present": False, "reason": str(exc)}
            else:
                providers["claude"] = {"api_key_present": False, "reason": "not importable"}
            if _openai_status is not None:
                try:
                    providers["openai"] = _openai_status()
                except Exception as exc:  # pragma: no cover
                    providers["openai"] = {"api_key_present": False, "reason": str(exc)}
            else:
                providers["openai"] = {"api_key_present": False, "reason": "not importable"}
            if _gemini_status is not None:
                try:
                    providers["gemini"] = _gemini_status()
                except Exception as exc:  # pragma: no cover
                    providers["gemini"] = {"api_key_present": False, "reason": str(exc)}
            else:
                providers["gemini"] = {"api_key_present": False, "reason": "not importable"}
            caps = None
            if _caps_status is not None:
                try:
                    caps = _caps_status()
                except Exception:  # pragma: no cover
                    caps = None
            self._send_json(200, {"providers": providers, "usage": caps})
            return
        if path == "/api/hermes/status":
            if _hermes_rt is None:
                self._send_json(200, {"credentials_ready": False, "reason": "hermes_runtime not importable"})
                return
            try:
                self._send_json(200, _hermes_rt.status_summary())
            except Exception as exc:  # pragma: no cover
                self._send_json(200, {"credentials_ready": False, "reason": str(exc)})
            return
        if path == "/api/hermes/recent":
            if _hermes_mem is None:
                self._send_json(200, {"inbound": [], "decisions": []})
                return
            try:
                payload = {
                    "inbound": _hermes_mem.recent_inbound(limit=30),
                    "outbound": _hermes_mem.recent_outbound(limit=10),
                    "decisions": _hermes_mem.recent_decisions(limit=10),
                }
            except Exception as exc:  # pragma: no cover
                payload = {"inbound": [], "decisions": [], "error": str(exc)}
            self._send_json(200, payload)
            return
        super().do_GET()

    def do_POST(self) -> None:
        path = unquote(urlparse(self.path).path)
        if path != "/api/chat":
            self._send_json(404, {"ok": False, "reply": "지원하지 않는 API입니다."})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(min(length, 10000))
            payload = json.loads(raw_body.decode("utf-8"))
            message = str(payload.get("message", ""))
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
            self._send_json(400, {"ok": False, "reply": "메시지를 읽을 수 없습니다."})
            return

        plan = plan_chat_command(message)
        if not plan.get("ok"):
            self._send_json(200, plan)
            return

        try:
            result = run_ai_company_command([str(part) for part in plan["command"]])
        except subprocess.TimeoutExpired:
            self._send_json(
                200,
                {
                    "ok": False,
                    "reply": "명령 시간이 오래 걸려 중단했습니다.",
                    "command": plan["command"],
                },
            )
            return

        self._send_json(
            200,
            {
                "ok": result["returncode"] == 0,
                "label": plan.get("label", "AI 회사 명령"),
                "command": plan["command"],
                "command_line": result["command_line"],
                "reply": "완료했습니다." if result["returncode"] == 0 else "명령 실행 중 문제가 생겼습니다.",
                "output": result["output"],
            },
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="AI Company local viewer server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), LocalViewerHandler)
    print(f"Serving D:\\AI_COMPANY at http://{args.host}:{args.port}", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
