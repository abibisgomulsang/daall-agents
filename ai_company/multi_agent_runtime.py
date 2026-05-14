"""페르소나별 어댑터 분기 + 자동 폴백 + 라운드 메모리.

흐름:
    persona.model_pref → claude/openai/gemini 시도 (live=True 이고 키가 있을 때만)
    실패/키 없음 → Ollama gemma4 폴백
    Ollama도 죽었으면 None 반환

각 호출은 `11_memory/agents/{memory_dir}/rounds.jsonl` 에 한 줄로 기록.
프롬프트 본문은 저장하지 않고 라운드 번호·길이·제공자만 남긴다.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from .agent_persona import AgentPersona
from .paths import ROOT


def _log_round(
    persona: AgentPersona,
    *,
    round_num: int,
    topic: str,
    response_len: int,
    provider: str,
    success: bool,
) -> None:
    folder = ROOT / "11_memory" / "agents" / persona.memory_dir
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "rounds.jsonl"
    record = {
        "time": datetime.now().isoformat(timespec="seconds"),
        "round": round_num,
        "topic_head": topic[:60],
        "provider": provider,
        "response_len": response_len,
        "success": success,
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _try_claude(prompt: str, system: str, *, live: bool) -> Optional[str]:
    try:
        from . import claude_runtime as cr  # type: ignore
    except Exception:
        return None
    if not cr.has_api_key():
        return None
    return cr.generate(prompt, system=system, live=live, max_tokens=400)


def _try_openai(prompt: str, system: str, *, live: bool) -> Optional[str]:
    try:
        from . import openai_runtime as oa  # type: ignore
    except Exception:
        return None
    if not oa.has_api_key():
        return None
    return oa.generate(prompt, system=system, live=live, max_tokens=400)


def _try_gemini(prompt: str, system: str, *, live: bool) -> Optional[str]:
    try:
        from . import gemini_runtime as gm  # type: ignore
    except Exception:
        return None
    if not gm.has_api_key():
        return None
    return gm.generate(prompt, system=system, live=live, max_tokens=400)


def _try_ollama(prompt: str, system: str, model: str) -> Optional[str]:
    try:
        from . import ollama_runtime as orun  # type: ignore
    except Exception:
        return None
    if not orun.is_alive():
        return None
    return orun.generate(prompt, system=system, model=model, max_tokens=400)


def call_persona(
    persona: AgentPersona,
    prompt: str,
    *,
    round_num: int = 0,
    live: bool = True,
    topic: str = "",
    force_ollama: bool = False,
    inject_brain_pack: bool = True,
) -> tuple[Optional[str], str]:
    """페르소나로 한 번 호출. (text, provider) 반환.

    Args:
        live: True면 외부 API 시도, False면 Ollama만 사용.
        force_ollama: True면 외부 API 무시 (비용 캡 위험 시).
        inject_brain_pack: True면 brain_packs/ 의 KNOWLEDGE.md를 시스템에 자동 주입.
    """
    # 브레인 팩 주입 — 직원 도메인 지식 자동 추가
    if inject_brain_pack:
        try:
            from . import brain_pack as _bp
            system = _bp.augment_system_prompt(persona.system_prompt, persona.key)
        except Exception:
            system = persona.system_prompt
    else:
        system = persona.system_prompt
    text: Optional[str] = None
    provider = "none"

    # 외부 API 시도 (live + force_ollama 아님)
    if live and not force_ollama:
        if persona.model_pref == "claude":
            text = _try_claude(prompt, system, live=live)
            if text and not text.startswith("[Claude blocked]") and not text.startswith("[Claude error]"):
                provider = "claude"
        elif persona.model_pref == "openai":
            text = _try_openai(prompt, system, live=live)
            if text and not text.startswith("[OpenAI blocked]") and not text.startswith("[OpenAI error]"):
                provider = "openai"
        elif persona.model_pref == "gemini":
            text = _try_gemini(prompt, system, live=live)
            if text and not text.startswith("[Gemini blocked]") and not text.startswith("[Gemini error]"):
                provider = "gemini"

    # Ollama 폴백 (외부 API 실패/없음/강제 폴백)
    if not text or provider == "none":
        ollama_text = _try_ollama(prompt, system, persona.ollama_model)
        if ollama_text:
            text = ollama_text
            provider = f"ollama({persona.ollama_model})"

    _log_round(
        persona,
        round_num=round_num,
        topic=topic,
        response_len=len(text or ""),
        provider=provider,
        success=bool(text),
    )
    return text, provider


def load_recent_rounds(persona: AgentPersona, limit: int = 5) -> list[dict]:
    """이전 라운드 기록을 최근 N개만. 메모리 페르소나가 자기 발언을 재참고할 때 사용."""
    path = ROOT / "11_memory" / "agents" / persona.memory_dir / "rounds.jsonl"
    if not path.exists():
        return []
    recs: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                recs.append(json.loads(line))
            except Exception:
                continue
    return recs[-limit:]


__all__ = ["call_persona", "load_recent_rounds"]
