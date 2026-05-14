from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .paths import ROOT, ensure_folders
from .meeting import run_meeting, run_routed_meeting, meeting_to_markdown
from .marketing import generate_ad_package, generate_routed_ad_package
from .ads_analysis import analyze_naver_ads_csv
from .app_ideas import cat_app_ideas
from .approval import format_approval_request, list_approvals, record_decision, render_approvals
from .utils import write_report
from .activity_log import record_activity
from .activity_report import write_activity_report
from .approval_cleanup import write_approval_cleanup_report
from .approval_risk import write_approval_priority_queue, write_approval_risk_report
from .connection_stages import write_connection_stage_outputs
from .dashboard import write_dashboard_data, write_realtime_status_design
from .dry_run_schemas import write_schema_report
from .experiments import write_experiment_plan
from .external_dry_runs import (
    export_payload_csv,
    write_instagram_upload_dry_run,
    write_naver_ads_api_dry_run,
    write_smartstore_fetch_dry_run,
)
from .execution_plan import write_execution_plan_outputs, write_final_checklist
from .image_templates import write_image_templates
from .instagram_assets import write_instagram_asset_manifest
from .model_router import write_routing_decision
from .nl_command import interpret as nl_interpret, run_plan as nl_run_plan, write_plan_report as nl_write_report
from .e2e_dry_run import write_e2e_report
from .integrations import (
    write_integration_approval_requests,
    write_integration_status_report,
    write_n8n_payload_sample,
    write_ollama_dry_run,
    write_telegram_dry_run,
)
from .naver_ads_permissions import write_naver_ads_permission_matrix
from .ollama_models import write_ollama_model_list_dry_run, write_ollama_live_status
from . import claude_runtime as _claude_rt
from . import openai_runtime as _openai_rt
from . import ollama_runtime as _ollama_rt
from . import gemini_runtime as _gemini_rt
from . import usage_caps as _usage_caps
from . import usage_log as _usage_log
from .model_router import execute_routing as _execute_routing, route as _route
from .boss_pipeline import write_boss_command_report as _boss_pipeline
from .multi_agent_meeting import write_multi_meeting as _write_multi_meeting
from . import hermes_runtime as _hermes
from . import hermes_memory as _hermes_mem
from . import brain_pack as _brain
from . import goals as _goals
from . import enterprise_mode as _enterprise
from .video_editing import (
    write_video_package as _write_video_package,
    build_timeline as _build_timeline,
)
from .premiere_controller import (
    write_premiere_package as _write_premiere_package,
    launch_premiere as _launch_premiere,
)
from .playwright_dry_run import write_playwright_dry_run
from .share_images import write_share_image_design, build_share_image_png
from .smartstore_mapping import write_smartstore_field_mapping


def init_folders() -> None:
    ensure_folders()
    print("기본 폴더 생성 완료")


def meeting(topic: str, with_router: bool = False, live: bool = False) -> None:
    ensure_folders()
    if with_router:
        result = run_routed_meeting(topic, live=live)
    else:
        result = run_meeting(topic, live=live)
    md = meeting_to_markdown(result)
    meeting_path = write_report(ROOT / "10_meetings", "ai_meeting", md)
    report_path = write_report(ROOT / "08_reports", "ai_meeting_report", md)
    approval_path = write_report(
        ROOT / "09_approval",
        "APPROVAL_REQUIRED_meeting_actions",
        format_approval_request(
            task_name="AI 회의 후속 실행",
            target="회의 결론 기반 광고, SNS, 상세페이지 개선안",
            before="현재 운영 상태 유지",
            after="회의 결과를 바탕으로 실행 후보를 실제 채널에 반영",
            expected_effect="광고 메시지와 랜딩 메시지의 일치도 개선",
            risks=["성과 하락 가능성", "과장 표현 사용 위험", "실제 채널 반영 시 되돌림 필요"],
            rollback="기존 문구, 이미지, 광고 설정으로 복구",
            source_markdown=md,
        )
    )
    print(md)
    print(f"\n회의 결과 저장: {meeting_path}")
    print(f"회의 보고서 저장: {report_path}")
    print(f"승인 대기 저장: {approval_path}")


def ad(product: str, with_router: bool = False) -> None:
    ensure_folders()
    md = generate_routed_ad_package(product) if with_router else generate_ad_package(product)
    path = write_report(ROOT / "08_reports", f"ad_package_{product}", md)
    approval_path = write_report(
        ROOT / "09_approval",
        f"APPROVAL_REQUIRED_ad_{product}",
        format_approval_request(
            task_name=f"{product} 광고 패키지 실행",
            target="SNS 게시물, 릴스, 광고 이미지, 광고 문구",
            before="기존 광고 소재와 상품 상세페이지 유지",
            after="생성된 광고 패키지를 승인된 채널에 반영",
            expected_effect="고양이 집사 공감형 메시지로 클릭과 전환 개선",
            risks=["가격/재고/링크 오류", "이미지 저작권 확인 누락", "SNS 업로드 후 수정 비용 발생"],
            rollback="게시물 비공개, 광고 소재 비활성화, 기존 소재 재적용",
            source_markdown=md,
        )
    )
    print(md)
    print(f"\n광고 패키지 저장: {path}")
    print(f"승인 대기 저장: {approval_path}")


def analyze_ads(csv_path: Path) -> None:
    ensure_folders()
    md = analyze_naver_ads_csv(csv_path)
    path = write_report(ROOT / "05_naver_ads", "naver_ads_report", md)
    report_path = write_report(ROOT / "08_reports", "naver_ads_report", md)
    approval_path = write_report(
        ROOT / "09_approval",
        "APPROVAL_REQUIRED_naver_ads_actions",
        format_approval_request(
            task_name="네이버광고 효율 개선 조치",
            target="네이버광고 키워드, 광고 문구, 입찰/예산 후보",
            before="현재 키워드와 입찰/예산 설정 유지",
            after="분석 결과에 따라 중지 후보, 문구 개선 후보, 유지 후보를 검토",
            expected_effect="낭비 클릭 감소와 ROAS 개선 후보 도출",
            risks=["입찰가 또는 키워드 변경 시 노출 감소", "성과 데이터 부족으로 오판 가능", "광고비 변경 위험"],
            rollback="변경 전 입찰가, 키워드 상태, 광고 문구로 복구",
            source_markdown=md,
        )
    )
    print(md)
    print(f"\n광고 분석 저장: {path}")
    print(f"광고 분석 보고서 저장: {report_path}")
    print(f"승인 대기 저장: {approval_path}")


def app_ideas() -> None:
    ensure_folders()
    md = cat_app_ideas()
    path = write_report(ROOT / "08_reports", "cat_app_ideas", md)
    print(md)
    print(f"\n앱 아이디어 저장: {path}")


def approvals_list() -> None:
    ensure_folders()
    print(render_approvals(list_approvals()))


def approvals_decide(file_name: str, decision: str, reason: str) -> None:
    ensure_folders()
    path = record_decision(file_name, decision, reason)
    print("승인 상태를 기록했습니다. 실제 실행은 하지 않았습니다.")
    print(f"결정 기록 저장: {path}")


def execution_plan(file_name: str) -> None:
    ensure_folders()
    output = write_execution_plan_outputs(file_name)
    print("실행 전 dry-run 계획을 생성했습니다. 실제 실행은 하지 않았습니다.")
    print(f"실행계획 저장: {output.plan_path}")
    if output.csv_path:
        print(f"키워드 CSV 저장: {output.csv_path}")


def final_checklist(file_name: str) -> None:
    ensure_folders()
    path = write_final_checklist(file_name)
    print("실행 전 최종 체크리스트를 생성했습니다. 실제 실행은 하지 않았습니다.")
    print(f"체크리스트 저장: {path}")


def office_simulator() -> None:
    ensure_folders()
    path = ROOT / "06_apps" / "ai_office_simulator" / "index.html"
    print("AI 사무실 시뮬레이터 위치")
    print(path)


def integration_status() -> None:
    ensure_folders()
    path = write_integration_status_report()
    print("외부 연동 준비 상태 보고서를 생성했습니다. 토큰/비밀번호 값은 출력하지 않았습니다.")
    print(f"보고서 저장: {path}")


def integration_approvals() -> None:
    ensure_folders()
    paths = write_integration_approval_requests()
    if not paths:
        print("승인 대기 파일이 필요한 외부 연동 항목이 없습니다.")
        return
    print("외부 연동 승인 대기 파일을 생성했습니다. 실제 호출/설치/발송은 하지 않았습니다.")
    for path in paths:
        print(f"승인 대기 저장: {path}")


def connection_stages() -> None:
    ensure_folders()
    report_path, summary_path, handshake_paths, approval_paths = write_connection_stage_outputs()
    print("4~8단계 AI 연결 dry-run 패키지를 생성했습니다. 실제 API 호출/메시지 발송/webhook 호출은 하지 않았습니다.")
    print(f"보고서 저장: {report_path}")
    print(f"요약 JSON 저장: {summary_path}")
    for path in handshake_paths:
        print(f"핸드셰이크 저장: {path}")
    for path in approval_paths:
        print(f"승인 대기 저장: {path}")


def telegram_dry_run(message: str) -> None:
    ensure_folders()
    path = write_telegram_dry_run(message)
    print("Telegram 메시지 dry-run 파일을 생성했습니다. 실제 발송은 하지 않았습니다.")
    print(f"보고서 저장: {path}")


def n8n_payload(task: str) -> None:
    ensure_folders()
    path = write_n8n_payload_sample(task)
    print("n8n webhook payload 샘플을 생성했습니다. 실제 webhook 호출은 하지 않았습니다.")
    print(f"payload 저장: {path}")


def ollama_dry_run(prompt: str) -> None:
    ensure_folders()
    path = write_ollama_dry_run(prompt)
    print("Ollama dry-run 파일을 생성했습니다. 실제 모델 호출/다운로드는 하지 않았습니다.")
    print(f"보고서 저장: {path}")


def ollama_model_list_dry_run() -> None:
    ensure_folders()
    report_path, json_path, approval_path = write_ollama_model_list_dry_run()
    print("Ollama 모델 목록 조회 승인형 dry-run을 생성했습니다. 실제 모델 목록 조회/호출/다운로드는 하지 않았습니다.")
    print(f"보고서 저장: {report_path}")
    print(f"JSON 저장: {json_path}")
    print(f"승인 대기 저장: {approval_path}")


def ollama_live_status() -> None:
    ensure_folders()
    report_path, json_path = write_ollama_live_status()
    print("Ollama 라이브 상태 보고서를 생성했습니다 (127.0.0.1 로컬 호출만, 외부 호출 없음).")
    print(f"보고서 저장: {report_path}")
    print(f"JSON 저장: {json_path}")


def usage_report() -> None:
    """오늘/이번 달 LLM 호출 비용 추정 보고서를 08_reports에 저장."""
    ensure_folders()
    caps = _usage_caps.caps_status()
    day = _usage_log.daily_summary()
    month = _usage_log.monthly_summary()
    lines = [
        "# LLM 호출 사용량 / 비용 추정 보고서",
        "",
        f"- 일일 호출: {day['total_calls']}회 · ₩{day['total_cost_krw_est']:,.0f} (캡 ₩{int(caps['daily_cap_krw']):,})",
        f"- 월간 호출: {month['total_calls']}회 · ₩{month['total_cost_krw_est']:,.0f} (캡 ₩{int(caps['monthly_cap_krw']):,})",
        "",
        "## 오늘 공급자별",
        "",
        "| 공급자 | 호출 | 추정 비용 (KRW) |",
        "| --- | --- | --- |",
    ]
    for p, slot in (day.get("per_provider") or {}).items():
        lines.append(f"| {p} | {slot['calls']} | ₩{slot['cost_krw_est']:,.0f} |")
    if not day.get("per_provider"):
        lines.append("| (오늘 호출 기록 없음) |  |  |")
    lines.extend([
        "",
        "## 안전 확인",
        "",
        "- API 키 값: 어디에도 출력되지 않음",
        "- 비용은 모델별 단가표 + USD/KRW 환산으로 추정한 값. 정확한 청구액은 공급자 콘솔 기준.",
        "- 캡 초과 시 호출 자동 차단 (호출 함수가 차단 사유와 함께 반환).",
    ])
    md = "\n".join(lines)
    path = write_report(ROOT / "08_reports", "llm_usage_report", md)
    print("LLM 사용량 보고서를 저장했습니다.")
    print(f"보고서 저장: {path}")
    print(f"오늘 ₩{day['total_cost_krw_est']:,.0f} / 캡 ₩{int(caps['daily_cap_krw']):,}")


def video_timeline(script: str, title: str = "고스틱 릴스", seconds: float = 15.0) -> None:
    """SNS 대본 → 비디오 AI 타임라인/스크립트/SRT/Premiere 산출물 생성."""
    ensure_folders()
    md_path, py_path, srt_path, summary_path = _write_video_package(
        script, title=title, target_seconds=seconds, include_premiere=True
    )
    print("비디오 AI 산출물을 만들었습니다. 실제 렌더링/업로드는 하지 않았습니다.")
    print(f"타임라인: {md_path}")
    print(f"MoviePy 스크립트: {py_path}")
    print(f"SRT 자막: {srt_path}")
    print(f"종합 보고서: {summary_path}")


def premiere_control(
    script: str,
    title: str = "고스틱 릴스",
    seconds: float = 15.0,
    launch: bool = False,
    approve: bool = False,
) -> None:
    """SNS 대본 → Premiere Pro 자동 임포트 산출물(FCPXML + .jsx + EDL).

    --launch: Windows에서 Premiere Pro를 실제로 실행 (사장님 명시 승인 후만).
    --approve: --launch와 함께 줘야 실제 실행됨. 안전 가드.
    """
    ensure_folders()
    tl = _build_timeline(script, title=title, target_seconds=seconds)
    pkg = _write_premiere_package(tl, sequence_name=(title or "AI_Reels_01"))
    print("Premiere Pro 자동 컨트롤 산출물을 생성했습니다 (자동 실행 안 함).")
    print(f"폴더:        {pkg.folder}")
    print(f"FCPXML:      {pkg.fcpxml_path}")
    print(f"ExtendScript:{pkg.jsx_path}")
    print(f"EDL 백업:    {pkg.edl_path}")
    print(f"가이드:      {pkg.readme_path}")
    print(f"종합 보고서: {pkg.report_path}")
    if launch:
        result = _launch_premiere(pkg, approved=approve)
        if result.get("launched"):
            print(f"\nPremiere Pro 실행 완료 — exe: {result['exe']}")
            print("Premiere 안에서 README 가이드대로 임포트하세요.")
        else:
            print(f"\nPremiere 자동 실행 안 함: {result.get('reason')}")
            if not approve:
                print("실제 실행하시려면 --launch --approve 두 플래그를 함께 주세요.")


def multi_meeting(topic: str, live: bool = True) -> None:
    """3라운드 토론 멀티 에이전트 회의를 실행하고 10_meetings에 저장."""
    ensure_folders()
    md_path, json_path = _write_multi_meeting(topic, live=live)
    print("3라운드 멀티 에이전트 회의를 마쳤습니다. 외부 채널 실제 반영은 일어나지 않았습니다.")
    print(f"회의록 저장: {md_path}")
    print(f"JSON 저장: {json_path}")


def boss_command(message: str, live: bool = False, multi: bool = False) -> None:
    """사장님 한 줄 → Hermes→AgentAU→CEO→라우터→회의→실행준비→승인 7단계 자동."""
    ensure_folders()
    md_path, json_path = _boss_pipeline(message, live=live, multi=multi)
    print("사장님 명령 처리 7단계가 끝났습니다. 외부 채널 실제 반영은 일어나지 않았습니다.")
    print(f"보고서 저장: {md_path}")
    print(f"JSON 저장: {json_path}")
    print("\n다음 단계: 09_approval 폴더의 새 파일을 검토하시고, OK면 별도 명령으로 실제 반영하시면 됩니다.")


def brain_status() -> None:
    """브레인 팩 현황."""
    ensure_folders()
    s = _brain.status_summary()
    print(f"브레인 팩 폴더: {s['brain_packs_dir']}")
    print(f"등록된 팩 수: {s['pack_count']}")
    print("\n팩 목록:")
    for p in s["packs"]:
        agents = ", ".join(p["agents"]) or "(없음)"
        print(f"  - {p['name']:20s}  ({p['size_chars']}자, 주입 대상: {agents})")


def goal_set(target: str, deadline: str = "") -> None:
    """활성 목표 설정."""
    ensure_folders()
    goal = _goals.set_goal(target, deadline=deadline)
    print(f"활성 목표 설정 완료: {goal.target}")
    if goal.kpis:
        print("KPI 후보:")
        for k in goal.kpis:
            print(f"  - {k['name']:20s}  현재 {k.get('current', 0)} / 목표 {k.get('target', 0)}")


def goal_status_cli() -> None:
    s = _goals.status_summary()
    if not s.get("active"):
        print("활성 목표 없음. 'goal-set --target ...' 로 설정하세요.")
        return
    print(f"목표: {s['target']}")
    print(f"기한: {s.get('deadline') or '미설정'}")
    print("KPI:")
    for k in s["kpis"]:
        print(f"  - {k['name']:20s}  {k.get('current')} / {k.get('target')} ({k.get('percent')}%)")
    print(f"설정 시각: {s.get('set_at')}, 노트 {s.get('note_count', 0)}건")


def enterprise_daily(live: bool = False) -> None:
    """엔터프라이즈 자율 모드 1일 사이클 실행."""
    ensure_folders()
    result = _enterprise.run_daily_cycle(live=live)
    path = _enterprise.write_daily_report(result)
    print(f"엔터프라이즈 일일 사이클 완료 — 보고서: {path}")
    if result.meeting_path:
        print(f"회의록: {result.meeting_path}")
    if result.approval_path:
        print(f"승인 대기: {result.approval_path}")
    if result.actions_decided:
        print("\n결정된 액션:")
        for a in result.actions_decided:
            print(f"  - {a}")


def hermes_status() -> None:
    """Hermes 자격(키 존재 여부)·메모리·rate 현황 표시. 값/토큰은 절대 출력 안 함."""
    ensure_folders()
    s = _hermes.status_summary()
    mem = s.get("memory", {})
    rate = mem.get("rate", {})
    print("=" * 60)
    print(" Hermes AI 상태 점검 — 토큰/값은 절대 출력하지 않습니다")
    print("=" * 60)
    print(f"  자격 (Token + Owner Chat ID): {'[OK]' if s['credentials_ready'] else '[--]'}")
    print(f"  메모리 폴더: {mem.get('memory_dir')}")
    print(f"  Inbox 누적: {mem.get('inbox_count', 0)}건")
    print(f"  Outbox 누적: {mem.get('outbox_count', 0)}건")
    print(f"  최근 결정 기록: {mem.get('decisions_count', 0)}건")
    print(f"  자동 처리 한도: 분당 {rate.get('per_minute_cap')} / 일일 {rate.get('per_day_cap')}")
    print(f"  오늘 사용: 분당 {rate.get('minute_used')} / 일일 {rate.get('day_used')} ({rate.get('day_date')})")
    print("=" * 60)
    if not s["credentials_ready"]:
        print(" .env에 TELEGRAM_BOT_TOKEN, TELEGRAM_OWNER_CHAT_ID 두 줄을 채워주세요.")
        print(" 채우신 뒤에는 scripts/start_hermes.ps1 로 봇을 백그라운드 실행하시면 됩니다.")


def hermes_run(no_auto_execute: bool = False) -> None:
    """텔레그램 long-poll 루프 진입. Ctrl+C로 중단."""
    ensure_folders()
    if not _hermes.credentials_ready():
        print("Hermes 자격이 설정되지 않았습니다. env-check 또는 hermes-status를 먼저 확인하세요.")
        return
    print("Hermes 봇 시작 — 사장님 메시지를 기다립니다 (Ctrl+C로 중단).")
    _hermes.run_bot_loop(auto_execute=not no_auto_execute)


def hermes_test(message: str) -> None:
    """로컬에서 봇 인바운드 한 건을 시뮬레이션 (텔레그램 실제 발송은 안 함)."""
    ensure_folders()
    owner = _hermes.get_owner_chat_id() or 0
    res = _hermes.handle_inbound(message, from_chat_id=owner, from_user="boss_local_test")
    print("Hermes 처리 결과 — 텔레그램으로 실제 발송은 하지 않았습니다.")
    print(f"의도: {res.plan_intent} / {res.plan_label}")
    print(f"안전 실행 가능: {res.safe_to_run} / 자동 실행됨: {res.auto_executed}")
    if res.approval_path:
        print(f"승인 대기: {res.approval_path}")
    print("\n--- Hermes가 사장님에게 보낼 응답 ---")
    print(res.reply)


def env_check() -> None:
    """환경변수/.env 키 존재 여부 + 오늘 사용량 표시 (값 노출 안 함)."""
    ensure_folders()
    rows = [
        ("Ollama (로컬, 무료)",    _ollama_rt.is_alive(),       "127.0.0.1:11434 응답 여부"),
        ("Claude API (코딩)",     _claude_rt.has_api_key(),    "ANTHROPIC_API_KEY in .env"),
        ("OpenAI API (디자인)",   _openai_rt.has_api_key(),    "OPENAI_API_KEY in .env"),
        ("Gemini API (리서치)",   _gemini_rt.has_api_key(),    "GOOGLE_API_KEY in .env"),
    ]
    print("=" * 60)
    print(" AI 회사 환경 점검 — 키 값은 절대 출력하지 않습니다")
    print("=" * 60)
    for label, ok, hint in rows:
        mark = "[OK]" if ok else "[--]"
        print(f"  {mark}  {label:24s}  ({hint})")
    print("-" * 60)
    caps = _usage_caps.caps_status()
    print(
        f"  오늘 LLM 호출: {caps['daily_calls']}회 · "
        f"₩{caps['daily_used_krw']:,.0f} / 일일 캡 ₩{int(caps['daily_cap_krw']):,}"
    )
    print(
        f"  이번 달 호출: {caps['monthly_calls']}회 · "
        f"₩{caps['monthly_used_krw']:,.0f} / 월 캡 ₩{int(caps['monthly_cap_krw']):,}"
    )
    print("=" * 60)
    print(" 캡은 환경변수 DAILY_LLM_CAP_KRW / MONTHLY_LLM_CAP_KRW 로 조정 가능합니다.")
    print(" 비용은 추정치이며, 정확한 청구액은 각 공급자 콘솔을 확인하세요.")


def run_routed(task: str, live: bool = False) -> None:
    """라우터 결정 후 실제 어댑터 호출 (--live)."""
    ensure_folders()
    decision = _route(task)
    primary = decision.primary.model
    print(f"라우터 1순위: {primary.display_name} ({primary.role})")
    print(f"점수: {decision.primary.score}")
    if not live:
        print("\n--live 옵션 없어 실제 호출은 하지 않았습니다. dry-run 결정만 표시.")
        return
    print("\n[실행] 라이브 호출 시도 중...")
    system = (
        "너는 1인 고양이 용품 회사의 AI 직원이다. 사장님은 결과만 본다. "
        "절대 실제 업로드/입찰 변경/결제/SNS 게시를 한다고 가정하지 않는다. 한국어로 답."
    )
    res = _execute_routing(decision, task, system=system, live=True)
    print(f"공급자: {res.get('provider') or '미연결'}")
    print(f"사유: {res.get('reason')}")
    if res.get("text"):
        print("\n--- 결과 ---")
        print(res["text"])
    if res.get("image"):
        print("\n--- 이미지 결과 ---")
        img = res["image"]
        for item in img.get("items", []):
            print(f"  URL: {item.get('url')}")
            if item.get("revised_prompt"):
                print(f"  Revised: {item['revised_prompt'][:120]}")


def image_templates(product: str, with_router: bool = False) -> None:
    ensure_folders()
    report_path, json_path = write_image_templates(product, with_router=with_router)
    print("이미지 광고 템플릿을 생성했습니다. 실제 업로드/이미지 생성은 하지 않았습니다.")
    print(f"보고서 저장: {report_path}")
    print(f"JSON 저장: {json_path}")


def playwright_dry_run(target: str) -> None:
    ensure_folders()
    path = write_playwright_dry_run(target)
    print("Playwright dry-run 설계 파일을 생성했습니다. 실제 브라우저 자동화는 실행하지 않았습니다.")
    print(f"보고서 저장: {path}")


def cat_webapp() -> None:
    ensure_folders()
    path = ROOT / "06_apps" / "cat_toy_recommender" / "index.html"
    print("고양이 장난감 추천 웹앱 위치")
    print(path)


def experiment_plan(topic: str) -> None:
    ensure_folders()
    report_path, json_path = write_experiment_plan(topic)
    print("AI 회의 기반 자동 실험 설계를 생성했습니다. 실제 광고/SNS/스토어 반영은 하지 않았습니다.")
    print(f"보고서 저장: {report_path}")
    print(f"JSON 저장: {json_path}")


def share_image_design(result: str) -> None:
    ensure_folders()
    report_path, json_path = write_share_image_design(result)
    print("추천 결과 공유 이미지 설계를 생성했습니다. 실제 이미지 생성/업로드는 하지 않았습니다.")
    print(f"보고서 저장: {report_path}")
    print(f"JSON 저장: {json_path}")


def share_image_export(result: str) -> None:
    ensure_folders()
    png_path, report_path = build_share_image_png(result)
    print("추천 결과 공유 이미지 PNG dry-run 파일을 생성했습니다. 실제 업로드/게시를 하지 않았습니다.")
    print(f"PNG 저장: {png_path}")
    print(f"보고서 저장: {report_path}")


def dry_run_schema(schema: str) -> None:
    ensure_folders()
    report_path, json_path = write_schema_report(schema)
    print("외부 API 연동 전 dry-run 데이터 스키마를 생성했습니다. 실제 API 호출은 하지 않았습니다.")
    print(f"보고서 저장: {report_path}")
    print(f"JSON 저장: {json_path}")


def smartstore_fetch_dry_run() -> None:
    ensure_folders()
    report_path, json_path, approval_path = write_smartstore_fetch_dry_run()
    csv_path = export_payload_csv(json_path, ROOT / "04_smartstore" / "dry_run" / f"{json_path.stem}.csv")
    print("스마트스토어 상품 데이터 가져오기 dry-run을 생성했습니다. 실제 로그인/API 호출은 하지 않았습니다.")
    print(f"보고서 저장: {report_path}")
    print(f"JSON 저장: {json_path}")
    print(f"CSV 저장: {csv_path}")
    print(f"승인 대기 저장: {approval_path}")


def smartstore_mapping() -> None:
    ensure_folders()
    report_path, json_path = write_smartstore_field_mapping()
    print("스마트스토어 상품 데이터 필드 매핑 설계를 생성했습니다. 실제 로그인/API 호출/상품 수정은 하지 않았습니다.")
    print(f"보고서 저장: {report_path}")
    print(f"JSON 저장: {json_path}")


def naver_ads_api_dry_run() -> None:
    ensure_folders()
    report_path, json_path, approval_path = write_naver_ads_api_dry_run()
    print("네이버광고 API dry-run 어댑터를 생성했습니다. 실제 API 호출/입찰 변경은 하지 않았습니다.")
    print(f"보고서 저장: {report_path}")
    print(f"JSON 저장: {json_path}")
    print(f"승인 대기 저장: {approval_path}")


def naver_ads_permission_matrix() -> None:
    ensure_folders()
    report_path, json_path = write_naver_ads_permission_matrix()
    print("네이버광고 API 읽기/쓰기 권한 매트릭스를 생성했습니다. 실제 API 호출/입찰/광고비 변경은 하지 않았습니다.")
    print(f"보고서 저장: {report_path}")
    print(f"JSON 저장: {json_path}")


def instagram_upload_dry_run(product: str) -> None:
    ensure_folders()
    report_path, json_path, approval_path = write_instagram_upload_dry_run(product)
    print("인스타 업로드 승인형 dry-run 패키지를 생성했습니다. 실제 업로드/게시를 하지 않았습니다.")
    print(f"보고서 저장: {report_path}")
    print(f"JSON 저장: {json_path}")
    print(f"승인 대기 저장: {approval_path}")


def instagram_asset_manifest(product: str) -> None:
    ensure_folders()
    report_path, json_path = write_instagram_asset_manifest(product)
    print("인스타 업로드 전 자산 매니페스트를 생성했습니다. 실제 업로드/게시를 하지 않았습니다.")
    print(f"보고서 저장: {report_path}")
    print(f"JSON 저장: {json_path}")


def dry_run_dashboard() -> None:
    ensure_folders()
    data_path, report_path = write_dashboard_data()
    print("dry-run 통합 대시보드 데이터를 갱신했습니다. 외부 API 호출은 하지 않았습니다.")
    print(f"데이터 저장: {data_path}")
    print(f"보고서 저장: {report_path}")


def realtime_status_design() -> None:
    ensure_folders()
    path = write_realtime_status_design()
    print("AI 직원 실시간 작업 상태 연동 설계를 생성했습니다.")
    print(f"보고서 저장: {path}")


def activity_report() -> None:
    ensure_folders()
    path = write_activity_report()
    print("AI 사무실 평균 소요 시간 리포트를 생성했습니다.")
    print(f"보고서 저장: {path}")


def approval_risk_report() -> None:
    ensure_folders()
    path = write_approval_risk_report()
    print("승인 파일 위험도 리포트를 생성했습니다. 실제 실행은 하지 않았습니다.")
    print(f"보고서 저장: {path}")


def approval_priority_queue() -> None:
    ensure_folders()
    path = write_approval_priority_queue()
    print("승인 파일 실행 우선순위 큐를 생성했습니다. 실제 실행은 하지 않았습니다.")
    print(f"보고서 저장: {path}")


def approval_cleanup_report() -> None:
    ensure_folders()
    path = write_approval_cleanup_report()
    print("승인 파일 중복/오래된 요청 정리 리포트를 생성했습니다. 실제 삭제는 하지 않았습니다.")
    print(f"보고서 저장: {path}")


def model_router(task: str) -> None:
    ensure_folders()
    md_path, json_path = write_routing_decision(task)
    print("모델 라우터 결정 보고서를 생성했습니다. 실제 API 호출/모델 실행은 하지 않았습니다.")
    print(f"보고서 저장: {md_path}")
    print(f"핸드오프 JSON 저장: {json_path}")


def e2e_dry_run(message: str) -> None:
    ensure_folders()
    md_path, json_path = write_e2e_report(message)
    print("텔레그램 e2e dry-run 보고서를 생성했습니다. 실제 텔레그램 호출은 하지 않았습니다.")
    print(f"보고서 저장: {md_path}")
    print(f"JSON 저장: {json_path}")


def nl(message: str, execute: bool = False, live: bool = False) -> None:
    ensure_folders()
    plan = nl_interpret(message, live=live)
    report_path = nl_write_report(plan)
    print(plan.to_markdown())
    print(f"\n해석 결과 저장: {report_path}")
    if plan.approval_path:
        print(f"승인 대기 저장: {plan.approval_path}")
    if execute:
        if not plan.safe_to_run:
            print("\n위험 키워드 포함으로 실행하지 않았습니다. 사장님 승인 후 다시 시도하세요.")
            return
        if not plan.cli:
            print("\nCLI 매핑이 없어 실행할 수 없습니다.")
            return
        print(f"\n[실행] {' '.join(plan.cli)}")
        result = nl_run_plan(plan)
        print(result.get("output", ""))
        print(f"\n실행 명령: {result.get('command_line', '')}")
        print(f"리턴 코드: {result.get('returncode', -1)}")
    else:
        print("\n실제 실행을 원하면 --execute 플래그를 추가하세요.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="아비비 AI 회사 MVP CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init-folders", help="프로젝트 기본 폴더를 생성합니다.")

    meeting_parser = subparsers.add_parser("meeting", help="AI 직원 회의를 실행하고 결과를 저장합니다.")
    meeting_parser.add_argument("--topic", "-t", required=True, help="AI 회의 주제")
    meeting_parser.add_argument(
        "--with-router",
        action="store_true",
        help="회의 시작 전 모델 라우터를 통과시켜 1순위 모델 위임을 회의록에 포함합니다.",
    )
    meeting_parser.add_argument(
        "--live",
        action="store_true",
        help="로컬 Ollama로 각 AI 직원의 의견과 CEO 결론을 실제 생성. 실패 시 자동 폴백.",
    )

    ad_parser = subparsers.add_parser("ad", help="상품 코드 기반 광고 패키지를 생성합니다.")
    ad_parser.add_argument("--product", "-p", required=True, help="상품 코드")
    ad_parser.add_argument(
        "--with-router",
        action="store_true",
        help="모델 라우터 결정을 광고 패키지 머리에 첨부합니다.",
    )

    analyze_parser = subparsers.add_parser("analyze-ads", help="네이버광고 CSV를 분석합니다.")
    analyze_parser.add_argument("--csv", "-c", required=True, type=Path, help="네이버광고 CSV 경로")

    subparsers.add_parser("app-ideas", help="고양이 앱 아이디어를 출력하고 저장합니다.")

    approvals_parser = subparsers.add_parser("approvals", help="승인 대기 파일을 조회하거나 승인/반려 기록을 남깁니다.")
    approvals_subparsers = approvals_parser.add_subparsers(dest="approvals_command", required=True)
    approvals_subparsers.add_parser("list", help="09_approval 폴더의 승인 파일 상태를 출력합니다.")

    decide_parser = approvals_subparsers.add_parser("decide", help="승인 파일에 대한 승인/반려 기록을 남깁니다.")
    decide_parser.add_argument("--file", "-f", required=True, help="APPROVAL_REQUIRED_...md 파일명")
    decide_parser.add_argument("--decision", "-d", required=True, choices=["approved", "rejected"], help="approved 또는 rejected")
    decide_parser.add_argument("--reason", "-r", required=True, help="승인/반려 사유")

    execution_parser = subparsers.add_parser("execution-plan", help="승인 파일 기반 실행 전 dry-run 계획을 생성합니다.")
    execution_parser.add_argument("--approval", "-a", required=True, help="APPROVAL_REQUIRED_...md 파일명")

    checklist_parser = subparsers.add_parser("final-checklist", help="승인 파일 기반 실행 전 최종 체크리스트를 생성합니다.")
    checklist_parser.add_argument("--approval", "-a", required=True, help="APPROVAL_REQUIRED_...md 파일명")

    subparsers.add_parser("office-simulator", help="AI 직원 사무실 시뮬레이터 HTML 위치를 출력합니다.")
    subparsers.add_parser("integration-status", help="Telegram/n8n/Ollama 연동 준비 상태를 보고서로 저장합니다.")
    subparsers.add_parser("integration-approvals", help="외부 연동 전 필요한 승인 대기 파일을 생성합니다.")
    subparsers.add_parser("connection-stages", help="4~8단계 AI 연결 dry-run 패키지를 생성합니다.")

    telegram_parser = subparsers.add_parser("telegram-dry-run", help="Telegram 메시지 dry-run 보고서를 생성합니다.")
    telegram_parser.add_argument("--message", "-m", required=True, help="발송하지 않고 저장할 메시지 초안")

    n8n_parser = subparsers.add_parser("n8n-payload", help="n8n webhook payload 샘플 JSON을 생성합니다.")
    n8n_parser.add_argument("--task", "-t", required=True, help="n8n에 전달할 업무 설명")

    ollama_parser = subparsers.add_parser("ollama-dry-run", help="Ollama 호출 전 dry-run 보고서를 생성합니다.")
    ollama_parser.add_argument("--prompt", "-p", required=True, help="모델에 전달할 프롬프트 초안")
    subparsers.add_parser("ollama-model-list-dry-run", help="Ollama 모델 목록 조회 전 승인형 dry-run 산출물을 생성합니다.")
    subparsers.add_parser("ollama-live-status", help="로컬 Ollama 데몬을 실제로 호출해 설치 모델 목록과 상태를 보고합니다.")
    subparsers.add_parser("env-check", help=".env의 API 키 존재 여부와 오늘 사용량/캡을 표시합니다. 값은 절대 출력하지 않습니다.")
    subparsers.add_parser("usage-report", help="08_reports에 LLM 호출 사용량/비용 추정 보고서를 저장합니다.")
    subparsers.add_parser("hermes-status", help="Hermes 자격/메모리/rate 현황을 표시합니다 (값/토큰 비노출).")
    subparsers.add_parser("brain-status", help="브레인 팩(도메인 지식) 현황과 직원별 매핑을 표시합니다.")
    subparsers.add_parser("goal-status", help="활성 목표와 KPI 진행률을 표시합니다.")

    goal_parser = subparsers.add_parser("goal-set", help="활성 목표를 설정합니다. KPI는 target 문자열에서 자동 추출.")
    goal_parser.add_argument("--target", "-t", required=True, help="예: '월 매출 1000만원'")
    goal_parser.add_argument("--deadline", "-d", default="", help="기한 (ISO 또는 자유 형식)")

    ent_parser = subparsers.add_parser(
        "enterprise-daily",
        help="엔터프라이즈 자율 모드 1일 사이클 (KPI 점검 → 회의 → 09_approval).",
    )
    ent_parser.add_argument(
        "--live",
        action="store_true",
        help="회의 단계에서 실제 LLM 호출 (없으면 dry-run 시나리오).",
    )

    hermes_run_parser = subparsers.add_parser(
        "hermes-run",
        help="텔레그램 봇 long-poll 루프 시작. start_hermes.ps1로 백그라운드 실행 권장.",
    )
    hermes_run_parser.add_argument(
        "--no-auto-execute",
        action="store_true",
        help="안전 명령도 자동 실행하지 않고 '준비만' 모드. 위험 명령은 그대로 차단.",
    )

    hermes_test_parser = subparsers.add_parser(
        "hermes-test",
        help="로컬에서 Hermes 인바운드 한 건을 모의 처리 (텔레그램 실제 발송 X).",
    )
    hermes_test_parser.add_argument("--message", "-m", required=True, help="모의 텔레그램 메시지")

    routed_parser = subparsers.add_parser(
        "routed-run",
        help="자연어 작업을 라우터에 보내고 1순위 모델 어댑터를 호출합니다. --live 없으면 dry-run.",
    )
    routed_parser.add_argument("--task", "-t", required=True, help="작업 설명 (자연어)")
    routed_parser.add_argument(
        "--live",
        action="store_true",
        help="외부 API 키가 있으면 실제 호출 (비용 발생). 없으면 dry-run.",
    )

    boss_parser = subparsers.add_parser(
        "boss-command",
        help="사장님 한 줄 명령으로 Hermes→AgentAU→CEO→라우터→회의→실행준비→승인 7단계 전부 실행.",
    )
    boss_parser.add_argument("--message", "-m", required=True, help="사장님 자연어 명령")
    boss_parser.add_argument(
        "--live",
        action="store_true",
        help="AI 회의 단계에서 Ollama 실제 호출. 외부 API 호출은 모델 라우터 결정과 별개.",
    )
    boss_parser.add_argument(
        "--multi",
        action="store_true",
        help="5단계 회의를 3라운드 멀티 에이전트 토론(직원별 모델·페르소나·표결)으로 진행.",
    )

    multi_meeting_parser = subparsers.add_parser(
        "multi-meeting",
        help="3라운드 멀티 에이전트 토론 회의(각 직원 별 모델/페르소나/메모리, CEO LLM 분배, 의견 충돌 시 표결).",
    )
    multi_meeting_parser.add_argument("--topic", "-t", required=True, help="회의 주제")
    multi_meeting_parser.add_argument(
        "--no-live",
        action="store_true",
        help="외부 API 사용 안 함. 전부 Ollama로만 진행.",
    )

    video_parser = subparsers.add_parser(
        "video-timeline",
        help="SNS 대본 → 9:16 타임라인 + MoviePy 자동 편집 스크립트 + SRT 자막 + Premiere FCPXML/.jsx (dry-run).",
    )
    video_parser.add_argument("--script", "-s", required=True, help="SNS/릴스 대본 텍스트")
    video_parser.add_argument("--title", default="고스틱 릴스", help="영상 제목 (선택)")
    video_parser.add_argument("--seconds", type=float, default=15.0, help="목표 길이(초)")

    premiere_parser = subparsers.add_parser(
        "premiere-control",
        help="SNS 대본 → Premiere Pro 자동 임포트 산출물(FCPXML/.jsx/EDL). --launch로 Premiere 자동 실행 가능.",
    )
    premiere_parser.add_argument("--script", "-s", required=True, help="SNS/릴스 대본 텍스트")
    premiere_parser.add_argument("--title", default="고스틱 릴스", help="시퀀스 이름")
    premiere_parser.add_argument("--seconds", type=float, default=15.0, help="목표 길이(초)")
    premiere_parser.add_argument(
        "--launch",
        action="store_true",
        help="산출물 생성 후 Premiere Pro를 자동 실행. --approve 도 함께 줘야 동작.",
    )
    premiere_parser.add_argument(
        "--approve",
        action="store_true",
        help="--launch와 함께 명시할 때만 Premiere 실행. 사장님 안전 가드.",
    )

    image_parser = subparsers.add_parser("image-templates", help="상품별 이미지 광고 템플릿을 생성합니다.")
    image_parser.add_argument("--product", "-p", required=True, help="상품 코드")
    image_parser.add_argument(
        "--with-router",
        action="store_true",
        help="모델 라우터 결정을 템플릿 보고서 머리에 첨부합니다.",
    )

    playwright_parser = subparsers.add_parser("playwright-dry-run", help="외부 사이트 자동화 전 Playwright dry-run 설계를 생성합니다.")
    playwright_parser.add_argument("--target", "-t", required=True, choices=["naver_ads", "smartstore", "sns"], help="dry-run 대상")

    subparsers.add_parser("cat-webapp", help="고양이 장난감 추천 웹앱 위치를 출력합니다.")

    experiment_parser = subparsers.add_parser("experiment-plan", help="AI 회의 기반 자동 실험 설계를 생성합니다.")
    experiment_parser.add_argument("--topic", "-t", required=True, help="실험 설계 주제")

    share_parser = subparsers.add_parser("share-image-design", help="추천 결과 공유 이미지 설계를 생성합니다.")
    share_parser.add_argument("--result", "-r", required=True, choices=["GOSTICK01", "PLAGO01", "REFILL01"], help="추천 결과 코드")

    share_export_parser = subparsers.add_parser("share-image-export", help="추천 결과 공유 이미지 PNG dry-run 파일을 생성합니다.")
    share_export_parser.add_argument("--result", "-r", required=True, choices=["GOSTICK01", "PLAGO01", "REFILL01"], help="추천 결과 코드")

    schema_parser = subparsers.add_parser("dry-run-schema", help="외부 API 연동 전 dry-run 데이터 스키마를 생성합니다.")
    schema_parser.add_argument("--schema", "-s", required=True, choices=["smartstore_products", "naver_ads_keywords", "sns_posts"], help="스키마 이름")

    subparsers.add_parser("smartstore-fetch-dry-run", help="스마트스토어 상품 데이터 가져오기 dry-run 산출물을 생성합니다.")
    subparsers.add_parser("smartstore-mapping", help="스마트스토어 상품 데이터 실제 연동 전 필드 매핑 설계를 생성합니다.")
    subparsers.add_parser("naver-ads-api-dry-run", help="네이버광고 API dry-run 어댑터 산출물을 생성합니다.")
    subparsers.add_parser("naver-ads-permission-matrix", help="네이버광고 API 읽기/쓰기 권한 매트릭스를 생성합니다.")

    instagram_parser = subparsers.add_parser("instagram-upload-dry-run", help="인스타 업로드 승인형 dry-run 패키지를 생성합니다.")
    instagram_parser.add_argument("--product", "-p", required=True, help="상품 코드")

    instagram_asset_parser = subparsers.add_parser("instagram-asset-manifest", help="인스타 업로드 전 로컬 자산 매니페스트를 생성합니다.")
    instagram_asset_parser.add_argument("--product", "-p", required=True, help="상품 코드")

    subparsers.add_parser("dry-run-dashboard", help="dry-run 통합 대시보드 데이터를 갱신합니다.")
    subparsers.add_parser("realtime-status-design", help="AI 직원 실시간 작업 상태 연동 설계를 생성합니다.")
    subparsers.add_parser("activity-report", help="AI 직원 활동 로그 평균 소요 시간 리포트를 생성합니다.")
    subparsers.add_parser("approval-risk-report", help="승인 파일 위험도를 점수화한 리포트를 생성합니다.")
    subparsers.add_parser("approval-priority-queue", help="승인 파일 위험도 기반 실행 검토 우선순위 큐를 생성합니다.")
    subparsers.add_parser("approval-cleanup-report", help="승인 파일 중복/오래된 요청 정리 후보 리포트를 생성합니다.")

    router_parser = subparsers.add_parser(
        "model-router",
        help="작업 설명을 받아 Codex/Claude/Gemini/Ollama/이미지 AI 중 어느 모델로 보낼지 결정한 보고서를 생성합니다.",
    )
    router_parser.add_argument("--task", "-t", required=True, help="라우팅할 작업 설명")

    e2e_parser = subparsers.add_parser(
        "e2e-dry-run",
        help="텔레그램 인바운드 → 라우터 → 회의 → 승인 전 흐름의 dry-run 보고서를 생성합니다.",
    )
    e2e_parser.add_argument("--message", "-m", required=True, help="모의 텔레그램 메시지")

    nl_parser = subparsers.add_parser(
        "nl",
        help="한국어 자연어 명령을 해석해 의도/CLI/모델 라우팅을 한 번에 처리합니다.",
    )
    nl_parser.add_argument("--message", "-m", required=True, help="자연어 명령 메시지")
    nl_parser.add_argument(
        "--execute",
        action="store_true",
        help="해석된 CLI를 실제 실행합니다. 위험 키워드가 있으면 자동 차단됩니다.",
    )
    nl_parser.add_argument(
        "--live",
        action="store_true",
        help="Ollama가 살아있으면 분류 사유에 자연어 코멘트를 추가합니다.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    record_activity(args.command, "active", "명령 실행 시작")

    try:
        if args.command == "init-folders":
            init_folders()
        elif args.command == "meeting":
            meeting(
                args.topic,
                with_router=getattr(args, "with_router", False),
                live=getattr(args, "live", False),
            )
        elif args.command == "ad":
            ad(args.product, with_router=getattr(args, "with_router", False))
        elif args.command == "analyze-ads":
            analyze_ads(args.csv)
        elif args.command == "app-ideas":
            app_ideas()
        elif args.command == "approvals":
            if args.approvals_command == "list":
                approvals_list()
            elif args.approvals_command == "decide":
                approvals_decide(args.file, args.decision, args.reason)
            else:
                parser.error(f"지원하지 않는 approvals 명령입니다: {args.approvals_command}")
        elif args.command == "execution-plan":
            execution_plan(args.approval)
        elif args.command == "final-checklist":
            final_checklist(args.approval)
        elif args.command == "office-simulator":
            office_simulator()
        elif args.command == "integration-status":
            integration_status()
        elif args.command == "integration-approvals":
            integration_approvals()
        elif args.command == "connection-stages":
            connection_stages()
        elif args.command == "telegram-dry-run":
            telegram_dry_run(args.message)
        elif args.command == "n8n-payload":
            n8n_payload(args.task)
        elif args.command == "ollama-dry-run":
            ollama_dry_run(args.prompt)
        elif args.command == "ollama-model-list-dry-run":
            ollama_model_list_dry_run()
        elif args.command == "ollama-live-status":
            ollama_live_status()
        elif args.command == "env-check":
            env_check()
        elif args.command == "usage-report":
            usage_report()
        elif args.command == "hermes-status":
            hermes_status()
        elif args.command == "brain-status":
            brain_status()
        elif args.command == "goal-status":
            goal_status_cli()
        elif args.command == "goal-set":
            goal_set(args.target, deadline=args.deadline)
        elif args.command == "enterprise-daily":
            enterprise_daily(live=getattr(args, "live", False))
        elif args.command == "hermes-run":
            hermes_run(no_auto_execute=getattr(args, "no_auto_execute", False))
        elif args.command == "hermes-test":
            hermes_test(args.message)
        elif args.command == "routed-run":
            run_routed(args.task, live=getattr(args, "live", False))
        elif args.command == "boss-command":
            boss_command(
                args.message,
                live=getattr(args, "live", False),
                multi=getattr(args, "multi", False),
            )
        elif args.command == "multi-meeting":
            multi_meeting(args.topic, live=not getattr(args, "no_live", False))
        elif args.command == "video-timeline":
            video_timeline(args.script, title=args.title, seconds=args.seconds)
        elif args.command == "premiere-control":
            premiere_control(
                args.script,
                title=args.title,
                seconds=args.seconds,
                launch=getattr(args, "launch", False),
                approve=getattr(args, "approve", False),
            )
        elif args.command == "image-templates":
            image_templates(args.product, with_router=getattr(args, "with_router", False))
        elif args.command == "playwright-dry-run":
            playwright_dry_run(args.target)
        elif args.command == "cat-webapp":
            cat_webapp()
        elif args.command == "experiment-plan":
            experiment_plan(args.topic)
        elif args.command == "share-image-design":
            share_image_design(args.result)
        elif args.command == "share-image-export":
            share_image_export(args.result)
        elif args.command == "dry-run-schema":
            dry_run_schema(args.schema)
        elif args.command == "smartstore-fetch-dry-run":
            smartstore_fetch_dry_run()
        elif args.command == "smartstore-mapping":
            smartstore_mapping()
        elif args.command == "naver-ads-api-dry-run":
            naver_ads_api_dry_run()
        elif args.command == "naver-ads-permission-matrix":
            naver_ads_permission_matrix()
        elif args.command == "instagram-upload-dry-run":
            instagram_upload_dry_run(args.product)
        elif args.command == "instagram-asset-manifest":
            instagram_asset_manifest(args.product)
        elif args.command == "dry-run-dashboard":
            dry_run_dashboard()
        elif args.command == "realtime-status-design":
            realtime_status_design()
        elif args.command == "activity-report":
            activity_report()
        elif args.command == "approval-risk-report":
            approval_risk_report()
        elif args.command == "approval-priority-queue":
            approval_priority_queue()
        elif args.command == "approval-cleanup-report":
            approval_cleanup_report()
        elif args.command == "model-router":
            model_router(args.task)
        elif args.command == "nl":
            nl(
                args.message,
                execute=getattr(args, "execute", False),
                live=getattr(args, "live", False),
            )
        elif args.command == "e2e-dry-run":
            e2e_dry_run(args.message)
        else:
            parser.error(f"지원하지 않는 명령입니다: {args.command}")
    except Exception as exc:
        record_activity(args.command, "blocked", f"실패: {exc}")
        raise
    record_activity(args.command, "idle", "명령 실행 완료")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())