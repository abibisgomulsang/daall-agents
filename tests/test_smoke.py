import importlib.util

from ai_company.meeting import run_meeting, run_routed_meeting
from ai_company.marketing import generate_ad_package, generate_routed_ad_package
from ai_company.ads_analysis import analyze_naver_ads_csv
from ai_company.activity_log import record_activity
from ai_company.activity_report import build_activity_summary, load_activity_events, render_activity_report, write_activity_report
from ai_company.approval_cleanup import build_approval_cleanup_summary, write_approval_cleanup_report
from ai_company.approval_risk import (
    analyze_all_approval_risks,
    build_approval_priority_queue,
    build_approval_risk_summary,
    write_approval_priority_queue,
    write_approval_risk_report,
)
from ai_company.approval import format_approval_request, list_approvals, record_decision, render_approvals
from ai_company.connection_stages import build_connection_stage_report, build_stage_connections, write_connection_stage_outputs
from ai_company.dashboard import build_dashboard_data, build_realtime_status_design
from ai_company.dry_run_schemas import build_schema_report
from ai_company.experiments import build_experiment_plan
from ai_company.external_dry_runs import (
    build_instagram_upload_dry_run,
    build_naver_ads_api_dry_run,
    build_smartstore_fetch_dry_run,
)
from ai_company.execution_plan import build_execution_plan, build_final_checklist, write_execution_plan_outputs
from ai_company.image_templates import build_image_templates
from ai_company.instagram_assets import build_instagram_asset_manifest
from ai_company.model_router import route, write_routing_decision
from ai_company.nl_command import interpret as nl_interpret, RISK_KEYWORDS
from ai_company.e2e_dry_run import build_e2e_report, write_e2e_report
from ai_company.integrations import (
    check_integrations,
    render_integration_status,
    write_n8n_payload_sample,
    write_ollama_dry_run,
    write_telegram_dry_run,
)
from ai_company.naver_ads_permissions import build_naver_ads_permission_matrix
from ai_company.ollama_models import build_ollama_model_list_dry_run, write_ollama_model_list_dry_run
from ai_company.paths import ROOT
from ai_company.playwright_dry_run import build_playwright_dry_run
from ai_company.share_images import build_share_image_design, build_share_image_png
from ai_company.smartstore_mapping import build_smartstore_field_mapping


def _load_local_viewer_server():
    module_path = ROOT / "scripts" / "local_viewer_server.py"
    spec = importlib.util.spec_from_file_location("local_viewer_server", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

def test_meeting():
    result = run_meeting("고스틱 광고 효율 개선")
    assert result.opinions
    assert "CEO" in result.ceo_decision


def test_meeting_live_falls_back_when_ollama_unreachable(monkeypatch):
    # Ollama가 죽어 있다고 모킹 → live=True여도 _offline_opinion으로 폴백해야 한다
    import ai_company.ollama_runtime as rt
    monkeypatch.setattr(rt, "is_alive", lambda: False)
    monkeypatch.setattr(rt, "generate", lambda *a, **k: None)
    result = run_meeting("고스틱 광고 효율 개선", live=True)
    assert result.opinions
    assert "CEO" in result.ceo_decision


def test_ollama_runtime_handles_dead_endpoint(monkeypatch):
    import ai_company.ollama_runtime as rt
    monkeypatch.setattr(rt, "_http_get", lambda *a, **k: None)
    monkeypatch.setattr(rt, "_http_post", lambda *a, **k: None)
    assert rt.is_alive() is False
    assert rt.list_models() is None
    assert rt.has_model("gemma4:e2b") is False
    assert rt.generate("hi") is None
    assert rt.chat([{"role": "user", "content": "hi"}]) is None
    s = rt.status_summary()
    assert s["alive"] is False
    assert s["external_call"] is False


def test_ollama_runtime_uses_mocked_models(monkeypatch):
    import ai_company.ollama_runtime as rt
    fake = {
        "models": [
            {"name": "gemma4:e2b", "size": 7162405886,
             "details": {"parameter_size": "5.1B", "family": "gemma4",
                          "quantization_level": "Q4_K_M"}},
            {"name": "gemma4:latest", "size": 9608350718,
             "details": {"parameter_size": "8.0B", "family": "gemma4",
                          "quantization_level": "Q4_K_M"}},
        ]
    }
    monkeypatch.setattr(rt, "_http_get", lambda path, t: fake if path == "/api/tags" else None)
    assert rt.is_alive() is True
    models = rt.list_models()
    assert models and len(models) == 2
    assert rt.has_model("gemma4:e2b") is True
    assert rt.has_model("gemma4") is True  # 베이스 일치
    assert rt.has_model("llama3") is False
    s = rt.status_summary()
    assert s["alive"] is True
    assert s["model_count"] == 2
    assert s["external_call"] is False

def test_ad_package():
    md = generate_ad_package("GOSTICK01")
    assert "고스틱" in md
    assert "릴스 대본" in md
    # 라우터 미통과시 라우팅 카드 없음
    assert "## 모델 라우터 결정" not in md


def test_ad_package_with_router():
    md = generate_routed_ad_package("GOSTICK01")
    assert "고스틱" in md
    assert "## 모델 라우터 결정" in md
    assert "1순위 모델" in md

def test_ads_analysis():
    md = analyze_naver_ads_csv(ROOT / "data" / "naver_ads_sample.csv")
    assert "ROAS" in md
    assert "네이버광고" in md

def test_approval_decision_flow(tmp_path):
    approval_file = tmp_path / "APPROVAL_REQUIRED_test_action_20260511.md"
    approval_file.write_text("# 승인 필요\n\n실제 실행 전 확인", encoding="utf-8")

    pending = list_approvals(tmp_path)
    assert len(pending) == 1
    assert pending[0].status == "pending"
    assert "대기" in render_approvals(pending)

    decision_path = record_decision(
        approval_file.name,
        "approved",
        "테스트 승인",
        approval_dir=tmp_path,
    )

    decided = list_approvals(tmp_path)
    assert decision_path.exists()
    assert decided[0].status == "approved"
    assert decided[0].reason == "테스트 승인"
    assert "실행 안 함" in decision_path.read_text(encoding="utf-8")

def test_structured_approval_and_execution_plan(tmp_path):
    source = analyze_naver_ads_csv(ROOT / "data" / "naver_ads_sample.csv")
    approval = format_approval_request(
        task_name="네이버광고 테스트 조치",
        target="키워드",
        before="현재 상태 유지",
        after="dry-run 후보 검토",
        expected_effect="ROAS 개선 후보 도출",
        risks=["입찰 변경 위험"],
        rollback="기존 설정으로 복구",
        source_markdown=source,
    )
    approval_file = tmp_path / "APPROVAL_REQUIRED_naver_ads_test.md"
    approval_file.write_text(approval, encoding="utf-8")

    plan = build_execution_plan(approval_file.name, approval_dir=tmp_path)

    assert "실행 전 Dry-run 계획" in plan
    assert "네이버광고 dry-run 분류" in plan
    assert "실제 실행 여부: 실행 안 함" in plan
    assert "키워드" in plan

    output = write_execution_plan_outputs(
        approval_file.name,
        approval_dir=tmp_path,
        reports_dir=tmp_path,
    )
    assert output.plan_path.exists()
    assert output.csv_path is not None
    assert output.csv_path.exists()
    assert "dry_run_action" in output.csv_path.read_text(encoding="utf-8-sig")

    checklist = build_final_checklist(approval_file.name, approval_dir=tmp_path)
    assert "실행 전 최종 체크리스트" in checklist
    assert "승인 대기" in checklist

def test_approval_risk_report(tmp_path):
    risky = tmp_path / "APPROVAL_REQUIRED_risky.md"
    risky.write_text(
        "# 승인 필요\n\n- 네이버광고 입찰가 변경\n- SNS 업로드\n- 실제 실행 여부: 실행 안 함",
        encoding="utf-8",
    )
    quiet = tmp_path / "APPROVAL_REQUIRED_quiet.md"
    quiet.write_text("# 승인 필요\n\n- 로컬 보고서 검토\n- dry-run", encoding="utf-8")

    risks = analyze_all_approval_risks(tmp_path)
    queue = build_approval_priority_queue(tmp_path)
    summary = build_approval_risk_summary(tmp_path)
    report_path = write_approval_risk_report(tmp_path, reports_dir=tmp_path)
    queue_path = write_approval_priority_queue(tmp_path, reports_dir=tmp_path)

    assert risks[0].file_name == risky.name
    assert queue[0]["file_name"] == risky.name
    assert risks[0].score > risks[-1].score
    assert summary["total"] == 2
    assert report_path.exists()
    assert queue_path.exists()
    assert "승인 파일 위험도 리포트" in report_path.read_text(encoding="utf-8")
    assert "실행 우선순위 큐" in queue_path.read_text(encoding="utf-8")

def test_approval_cleanup_report(tmp_path):
    first = tmp_path / "APPROVAL_REQUIRED_ad_GOSTICK01_20260511_010000.md"
    second = tmp_path / "APPROVAL_REQUIRED_ad_GOSTICK01_20260511_020000.md"
    first.write_text("# 승인 필요\n\n오래된 광고 요청", encoding="utf-8")
    second.write_text("# 승인 필요\n\n새 광고 요청", encoding="utf-8")

    summary = build_approval_cleanup_summary(tmp_path, stale_hours=0)
    report_path = write_approval_cleanup_report(tmp_path, reports_dir=tmp_path, stale_hours=0)
    report = report_path.read_text(encoding="utf-8")

    assert summary["total"] == 2
    assert len(summary["duplicate_groups"]) == 1
    assert "실제 삭제 여부: 삭제 안 함" in report
    assert "최신 유지 후보" in report

def test_office_simulator_files_exist():
    simulator_dir = ROOT / "06_apps" / "ai_office_simulator"
    assert (simulator_dir / "index.html").exists()
    assert (simulator_dir / "styles.css").exists()
    assert (simulator_dir / "app.js").exists()
    assert (simulator_dir / "activity_feed.js").exists()
    html = (simulator_dir / "index.html").read_text(encoding="utf-8")
    script = (simulator_dir / "app.js").read_text(encoding="utf-8")
    assert "../dry_run_dashboard/index.html" in html
    assert "riskQueue" in html
    assert "connectionStageList" in html
    assert "chatForm" in html
    assert "chatMessages" in html
    # 라우팅 카드 표시용 클래스가 스타일/스크립트에 들어있어야 한다
    styles = (simulator_dir / "styles.css").read_text(encoding="utf-8")
    assert "chat-message.router" in styles
    assert 'appendChatMessage(\n        "router"' in script or '"router"' in script
    assert "renderRiskQueue" in script
    assert "renderConnectionStages" in script
    assert "sendChat" in script
    assert "../agent_matrix/index.html" in html


def test_agent_matrix_files_exist():
    app_dir = ROOT / "06_apps" / "agent_matrix"
    assert (app_dir / "index.html").exists()
    assert (app_dir / "styles.css").exists()
    assert (app_dir / "app.js").exists()
    assert (app_dir / "agents_data.js").exists()
    html = (app_dir / "index.html").read_text(encoding="utf-8")
    data = (app_dir / "agents_data.js").read_text(encoding="utf-8")
    script = (app_dir / "app.js").read_text(encoding="utf-8")
    assert "에이전트 매트릭스" in html
    assert "modal-systemDiag" in html
    assert "modal-reportAuto" in html
    assert "modal-orchestrator" in html
    for k in ("codex_chatgpt", "claude", "gemini", "ollama", "image_ai"):
        assert k in data
    for key in ("ceo", "marketing", "sns", "image", "review"):
        assert f'key: "{key}"' in data
    assert "btnSaveMap" in script
    assert "btnAutoMap" in script
    assert "localStorage" in script
    # 가상 사무실 페이지로의 링크
    assert "../virtual_office/index.html" in html


def test_hermes_memory_records_inbox_and_preferences(tmp_path, monkeypatch):
    import ai_company.hermes_memory as hm
    monkeypatch.setattr(hm, "HERMES_DIR", tmp_path / "hermes")
    hm.record_inbound("고스틱 광고 만들어줘", from_chat_id=12345, from_user="boss", message_id=1)
    hm.remember_command("고스틱 광고 만들어줘")
    hm.record_decision("자동 실행 테스트", intent="ad_package", safe=True, auto_executed=True)
    inb = hm.recent_inbound(limit=5)
    dec = hm.recent_decisions(limit=5)
    prefs = hm.get_preferences()
    assert inb and inb[-1]["text"] == "고스틱 광고 만들어줘"
    assert dec and dec[-1]["auto_executed"] is True
    favs = prefs.get("favorite_commands") or []
    assert favs and favs[0]["head"].startswith("고스틱")


def test_hermes_rate_limit_blocks_after_burst(tmp_path, monkeypatch):
    import ai_company.hermes_memory as hm
    monkeypatch.setattr(hm, "HERMES_DIR", tmp_path / "hermes")
    monkeypatch.setattr(hm, "DEFAULT_PER_MINUTE", 3)
    monkeypatch.setattr(hm, "DEFAULT_PER_DAY", 100)
    for _ in range(3):
        ok, _ = hm.check_and_count()
        assert ok is True
    ok, reason = hm.check_and_count()
    assert ok is False
    assert "분당" in reason


def test_hermes_handle_inbound_blocks_risky_keywords(tmp_path, monkeypatch):
    import ai_company.hermes_memory as hm
    import ai_company.hermes_runtime as hr
    monkeypatch.setattr(hm, "HERMES_DIR", tmp_path / "hermes")
    # 토큰 없음 = telegram 발송 없음
    monkeypatch.setattr(hr, "get_bot_token", lambda: None)
    monkeypatch.setattr(hr, "get_owner_chat_id", lambda: None)
    monkeypatch.setattr("ai_company.nl_command.ROOT", tmp_path)
    (tmp_path / "09_approval").mkdir()

    res = hr.handle_inbound("네이버광고 입찰가 200원 올려줘", from_chat_id=1)
    assert res.safe_to_run is False
    assert res.auto_executed is False
    assert res.approval_path is not None
    assert "위험 키워드" in res.reply


def test_hermes_handle_inbound_safe_command_runs(tmp_path, monkeypatch):
    import ai_company.hermes_memory as hm
    import ai_company.hermes_runtime as hr
    monkeypatch.setattr(hm, "HERMES_DIR", tmp_path / "hermes")
    monkeypatch.setattr(hr, "get_bot_token", lambda: None)
    monkeypatch.setattr(hr, "get_owner_chat_id", lambda: None)
    # subprocess.run을 모킹해서 실제 CLI는 호출 안 함
    class FakeResult:
        returncode = 0
        stdout = "AI 회의 완료: 결과 저장: 10_meetings/xxx.md"
        stderr = ""
    monkeypatch.setattr("subprocess.run", lambda *a, **k: FakeResult())
    res = hr.handle_inbound("고스틱 광고 만들어줘", from_chat_id=1, auto_execute=True)
    assert res.safe_to_run is True
    assert res.auto_executed is True
    assert "자동 실행 완료" in res.reply


def test_virtual_office_has_persistent_storage():
    """가상 사무실이 localStorage로 상태 영속화하는지 코드 수준 검증."""
    app_js = (ROOT / "06_apps" / "virtual_office" / "app.js").read_text(encoding="utf-8")
    assert "ai_company.virtual_office.state.v1" in app_js
    assert "saveStateLocal" in app_js
    assert "loadStateLocal" in app_js
    assert "clearStateLocal" in app_js
    assert "beforeunload" in app_js
    # 초기화 시 복원 시도
    assert "loadStateLocal()" in app_js


def test_simulator_chat_has_persistent_storage():
    app_js = (ROOT / "06_apps" / "ai_office_simulator" / "app.js").read_text(encoding="utf-8")
    assert "ai_company.simulator.chat.v1" in app_js
    assert "loadChatHistory" in app_js
    assert "saveChatHistory" in app_js
    assert "clearChatHistory" in app_js
    assert "restoreChatHistory" in app_js


def test_agent_matrix_has_persistent_storage_and_filter():
    app_js = (ROOT / "06_apps" / "agent_matrix" / "app.js").read_text(encoding="utf-8")
    assert "ai_company.agent_matrix.model_map.v1" in app_js
    assert "ai_company.agent_matrix.filter.v1" in app_js
    assert "saveFilter" in app_js
    assert "loadFilter" in app_js
    assert "clearAllMatrixStorage" in app_js


def test_virtual_office_files_exist():
    app_dir = ROOT / "06_apps" / "virtual_office"
    assert (app_dir / "index.html").exists()
    assert (app_dir / "styles.css").exists()
    assert (app_dir / "app.js").exists()
    html = (app_dir / "index.html").read_text(encoding="utf-8")
    styles = (app_dir / "styles.css").read_text(encoding="utf-8")
    script = (app_dir / "app.js").read_text(encoding="utf-8")
    # 상단 상태바
    assert "dayValue" in html
    assert "timeValue" in html
    assert "autoLabel" in html
    # 3개 탭
    assert 'data-tab="activity"' in html
    assert 'data-tab="artifacts"' in html
    assert 'data-tab="dialog"' in html
    # 시뮬레이션 키 함수/엘리먼트
    assert "officeMap" in html
    assert "pairLine" in script
    assert "drawOffice" in script
    assert "logActivity" in script
    # 가상 사무실에서 직원 에이전트 보기로 가는 링크
    assert "../agent_matrix/index.html" in html
    # 픽셀톤 다크 테마용 클래스
    assert ".office-map-card" in styles
    assert ".activity-list" in styles
    # 실데이터 연동 (수영 에이전트 + real_data.json 로더)
    assert "realDataBadge" in html
    assert "real_data.json" in script
    assert "loadRealData" in script
    assert "refreshRealData" in script
    assert "dataAgentLineFromReal" in script
    assert "real-badge" in styles


def test_real_data_sample_schema_valid():
    import json
    sample = ROOT / "08_reports" / "real_data.sample.json"
    assert sample.exists()
    data = json.loads(sample.read_text(encoding="utf-8"))
    # 필수 최상위 키
    for k in ("updated_at", "source", "naver_ads", "smartstore", "alerts"):
        assert k in data, f"real_data.sample.json missing key: {k}"
    # 네이버광고 핵심 수치
    nads = data["naver_ads"]
    for k in ("roas", "target_roas", "worst_keywords", "best_keywords"):
        assert k in nads
    assert isinstance(nads["worst_keywords"], list)
    # 스마트스토어 재고/리뷰
    smt = data["smartstore"]
    for k in ("today_orders", "avg_review_score", "low_stock"):
        assert k in smt
    # 알림 구조 (level/title/owner)
    for alert in data["alerts"]:
        assert "level" in alert
        assert "title" in alert
        assert alert["level"] in {"info", "warning", "danger"}
    # 샘플 표시
    assert data.get("is_sample") is True


def test_local_viewer_chat_planner():
    server = _load_local_viewer_server()

    meeting = server.plan_chat_command("고스틱 광고 회의해줘")
    ad = server.plan_chat_command("고스틱 광고 만들어줘")
    ads = server.plan_chat_command("네이버 광고 분석해줘")
    blocked = server.plan_chat_command("네이버 광고 입찰가 바꿔줘")

    assert meeting["command"][0] == "meeting"
    assert ad["command"] == ["ad", "--product", "GOSTICK01"]
    assert ads["command"] == ["analyze-ads", "--csv", "data/naver_ads_sample.csv"]
    assert blocked["ok"] is False
    # nl_interpret 통합 후 라우팅/의도 정보가 함께 들어와야 한다
    assert "routing" in meeting
    assert "routing" in ad
    assert "routing" in ads
    assert blocked.get("approval_path")  # 위험 키워드는 승인 파일 생성

def test_activity_feed_updates_simulator():
    feed_path = ROOT / "12_logs" / "pytest_activity_feed.js"
    log_path = ROOT / "12_logs" / "pytest_activity_log.jsonl"
    state_path = ROOT / "12_logs" / "pytest_activity_state.json"
    record = record_activity(
        "execution-plan",
        "active",
        "테스트 작업",
        feed_js=feed_path,
        event_log=log_path,
        state_file=state_path,
    )
    done = record_activity(
        "execution-plan",
        "idle",
        "테스트 완료",
        feed_js=feed_path,
        event_log=log_path,
        state_file=state_path,
    )
    feed = feed_path.read_text(encoding="utf-8")
    assert record.agent_id == "ceo"
    assert done.duration_seconds is not None
    assert "AI_OFFICE_FEED" in feed
    assert "duration_seconds" in feed
    assert "approvals" in feed
    assert "risk_queue" in feed
    assert "connection_stages" in feed

def test_activity_report_handles_durations_and_bad_lines(tmp_path):
    log_path = tmp_path / "activity.jsonl"
    log_path.write_text(
        "\n".join(
            [
                '{"time":"2026-05-11T01:00:00","command":"meeting","agent_id":"ceo","status":"active","duration_seconds":null}',
                '{"time":"2026-05-11T01:00:01","command":"meeting","agent_id":"ceo","status":"idle","duration_seconds":1.0}',
                "bad-json",
                '{"time":"2026-05-11T01:00:02","command":"ad","agent_id":"marketing","status":"blocked","detail":"테스트 실패","duration_seconds":2.0}',
            ]
        ),
        encoding="utf-8",
    )

    events, ignored = load_activity_events(log_path)
    summary = build_activity_summary(events, ignored)
    report = render_activity_report(summary)
    report_path = write_activity_report(log_path, reports_dir=tmp_path)

    assert ignored == 1
    assert summary["commands"][0]["avg_seconds"] == 2.0
    assert "AI 사무실 평균 소요 시간 리포트" in report
    assert "테스트 실패" in report
    assert report_path.exists()

def test_integration_status_is_safe():
    statuses = check_integrations()
    report = render_integration_status(statuses)
    assert "외부 연동 준비 상태" in report
    assert "값은 출력하지 않았습니다" in report
    assert "Telegram Bot" in report
    assert "Ollama" in report

def test_connection_stages_are_dry_run(tmp_path, monkeypatch):
    monkeypatch.setattr("ai_company.connection_stages.ROOT", tmp_path)
    (tmp_path / "08_reports").mkdir()
    (tmp_path / "09_approval").mkdir()

    stages = build_stage_connections()
    report, payload = build_connection_stage_report(stages)
    report_path, summary_path, handshake_paths, approval_paths = write_connection_stage_outputs()

    assert [stage.stage for stage in stages] == [4, 5, 6, 7, 8]
    assert payload["actual_external_calls"] is False
    assert payload["key_values_exposed"] is False
    assert "4~8단계 AI 연결 작업 패키지" in report
    assert report_path.exists()
    assert summary_path.exists()
    assert len(handshake_paths) == 5
    assert approval_paths

def test_integration_dry_run_outputs(tmp_path):
    telegram_path = write_telegram_dry_run("테스트 메시지", reports_dir=tmp_path)
    n8n_path = write_n8n_payload_sample("테스트 업무", reports_dir=tmp_path)
    ollama_path = write_ollama_dry_run("테스트 프롬프트", reports_dir=tmp_path)

    assert telegram_path.exists()
    assert n8n_path.exists()
    assert ollama_path.exists()
    assert "실제 발송 여부: 발송 안 함" in telegram_path.read_text(encoding="utf-8")
    assert '"dry_run": true' in n8n_path.read_text(encoding="utf-8")
    assert "실제 모델 호출 여부: 호출 안 함" in ollama_path.read_text(encoding="utf-8")

def test_ollama_live_status_falls_back_when_dead(monkeypatch, tmp_path):
    import ai_company.ollama_runtime as rt
    from ai_company.ollama_models import build_ollama_live_status
    monkeypatch.setattr(rt, "_http_get", lambda *a, **k: None)
    md, payload = build_ollama_live_status()
    # 데몬이 죽었으면 dry-run 보고서로 폴백 (live_attempted=True 표시)
    assert payload.get("live_attempted") is True
    assert payload.get("live_alive") is False
    assert "Ollama" in md


def test_claude_runtime_safe_without_key(monkeypatch):
    import ai_company.claude_runtime as cr
    monkeypatch.setattr(cr, "_load_api_key", lambda: None)
    assert cr.has_api_key() is False
    # live=True여도 키 없으면 None
    assert cr.generate("hello", live=True) is None
    # live=False면 키 있어도 None
    monkeypatch.setattr(cr, "_load_api_key", lambda: "sk-test")
    assert cr.generate("hello", live=False) is None
    s = cr.status_summary()
    assert s["external_call"] is False
    assert s["provider"] == "anthropic_claude"


def test_claude_runtime_parses_mocked_response(monkeypatch):
    import ai_company.claude_runtime as cr
    monkeypatch.setattr(cr, "_load_api_key", lambda: "sk-test")
    monkeypatch.setattr(
        cr, "_http_post",
        lambda payload, key, t: {"content": [{"type": "text", "text": "def foo(): pass"}]},
    )
    out = cr.generate("간단한 파이썬 함수 짜줘", live=True)
    assert out == "def foo(): pass"


def test_openai_runtime_safe_without_key(monkeypatch):
    import ai_company.openai_runtime as oa
    monkeypatch.setattr(oa, "_load_api_key", lambda: None)
    assert oa.has_api_key() is False
    assert oa.generate("hi", live=True) is None
    assert oa.generate_image("a cat", live=True) is None
    s = oa.status_summary()
    assert s["external_call"] is False
    assert s["provider"] == "openai_chatgpt"


def test_openai_runtime_parses_mocked_chat_and_image(monkeypatch):
    import ai_company.openai_runtime as oa
    monkeypatch.setattr(oa, "_load_api_key", lambda: "sk-test")

    def fake_post(path, payload, key, t):
        if path == "/chat/completions":
            return {"choices": [{"message": {"content": "썸네일 카피 시안"}}]}
        if path == "/images/generations":
            return {"data": [{"url": "https://img/x.png", "revised_prompt": "a cat"}]}
        return None

    monkeypatch.setattr(oa, "_http_post", fake_post)
    assert oa.generate("디자인 카피", live=True) == "썸네일 카피 시안"
    img = oa.generate_image("cute cat poster", live=True)
    assert img and img["count"] == 1
    assert img["items"][0]["url"].endswith(".png")


def test_usage_log_estimates_and_summarizes(tmp_path, monkeypatch):
    from ai_company import usage_log
    monkeypatch.setattr(usage_log, "LOG_PATH", tmp_path / "llm.jsonl")
    # 가짜 모델 단가 적용은 환경변수로 가능, 여기선 실제 단가표 사용
    rec = usage_log.log_text_call("anthropic_claude", "claude-haiku-4-5-20251001", 1000, 2000, purpose="test")
    assert rec["cost_krw_est"] > 0
    d = usage_log.daily_summary()
    assert d["total_calls"] == 1
    assert d["per_provider"]["anthropic_claude"]["calls"] == 1


def test_usage_caps_blocks_when_exceeded(tmp_path, monkeypatch):
    from ai_company import usage_log, usage_caps
    monkeypatch.setattr(usage_log, "LOG_PATH", tmp_path / "llm.jsonl")
    monkeypatch.setenv("DAILY_LLM_CAP_KRW", "100")
    # 이미 ₩500 사용한 상태로 만들고 추가 ₩10 호출 시도 → 차단
    usage_log.log_text_call("anthropic_claude", "claude-haiku-4-5-20251001", 100000, 100000)
    ok, reason = usage_caps.check_cap(estimated_krw=10)
    assert ok is False
    assert "일일 캡" in reason


def test_claude_respects_cap(monkeypatch, tmp_path):
    import ai_company.claude_runtime as cr
    from ai_company import usage_log
    monkeypatch.setattr(cr, "_load_api_key", lambda: "sk-test")
    monkeypatch.setattr(usage_log, "LOG_PATH", tmp_path / "llm.jsonl")
    monkeypatch.setenv("DAILY_LLM_CAP_KRW", "0")
    out = cr.generate("hello", live=True)
    assert out and out.startswith("[Claude blocked]")


def test_gemini_runtime_safe_without_key(monkeypatch):
    import ai_company.gemini_runtime as gm
    monkeypatch.setattr(gm, "_load_api_key", lambda: None)
    assert gm.has_api_key() is False
    assert gm.generate("hi", live=True) is None
    s = gm.status_summary()
    assert s["external_call"] is False
    assert s["provider"] == "google_gemini"


def test_gemini_runtime_parses_mocked_response(monkeypatch):
    import ai_company.gemini_runtime as gm
    monkeypatch.setattr(gm, "_load_api_key", lambda: "key")
    fake = {
        "candidates": [{
            "content": {"parts": [{"text": "트렌드 1: ..."}]},
        }],
        "usageMetadata": {"promptTokenCount": 30, "candidatesTokenCount": 80}
    }
    monkeypatch.setattr(gm, "_http_post", lambda *a, **k: fake)
    out = gm.generate("고양이 장난감 트렌드", live=True)
    assert out and "트렌드" in out


def test_model_router_original_architecture_mapping():
    """사장님 원본 아키텍처: 코딩→Codex/ChatGPT, 긴 문서/검수→Claude, 리서치→Gemini, 이미지→이미지 AI."""
    from ai_company.model_router import route
    coding = route("Next.js 백엔드 코드 자동화 스크립트 리팩터링")
    review = route("스마트스토어 상세페이지 검수")
    research = route("고양이 MBTI 앱 경쟁사 트렌드 조사")
    image = route("릴스 썸네일 이미지 시안")
    repeat = route("리뷰 200건 긍정/부정 분류 태그")
    assert coding.primary.model.key == "codex_chatgpt"
    assert review.primary.model.key == "claude"
    assert research.primary.model.key == "gemini"
    assert image.primary.model.key == "image_ai"
    assert repeat.primary.model.key == "ollama"


def test_boss_pipeline_runs_full_7_stages(tmp_path, monkeypatch):
    """boss-command 7단계 산출물이 전부 생성되는지."""
    monkeypatch.setattr("ai_company.boss_pipeline.ROOT", tmp_path)
    monkeypatch.setattr("ai_company.ceo_orchestrator._route", lambda t: __import__("ai_company.model_router", fromlist=["route"]).route(t))
    for sub in ["08_reports", "09_approval", "10_meetings", "02_marketing", "03_images/templates", "05_naver_ads"]:
        (tmp_path / sub).mkdir(parents=True, exist_ok=True)

    from ai_company.boss_pipeline import run_boss_command
    result = run_boss_command("고스틱 광고 효율 회의해줘")
    assert len(result.stages) == 7
    names = [s.name for s in result.stages]
    assert "Hermes AI 인바운드" in names[0]
    assert "AgentAU" in names[1]
    assert "CEO" in names[2]
    assert "모델 라우터" in names[3]
    assert "AI 회의" in names[4]
    assert "실행 준비" in names[5]
    assert "사장님 승인" in names[6]
    assert result.approval_path
    assert result.routing is not None


def test_video_agent_present_in_personas_and_matrix():
    from ai_company.agent_persona import PERSONAS_BY_KEY, DEFAULT_MEETING_KEYS
    assert "video" in PERSONAS_BY_KEY
    v = PERSONAS_BY_KEY["video"]
    assert v.name == "비디오 AI"
    assert v.memory_dir == "video_ai"
    assert "video" in DEFAULT_MEETING_KEYS

    matrix_data = (ROOT / "06_apps" / "agent_matrix" / "agents_data.js").read_text(encoding="utf-8")
    assert 'key: "video"' in matrix_data
    assert '🎬' in matrix_data
    assert 'video: "codex_chatgpt"' in matrix_data


def test_ceo_assigner_falls_back_to_video_for_editing_task():
    from ai_company.ceo_assigner import assign
    a = assign("SNS 대본 받아서 영상 편집 타임라인 짜줘", live=False)
    assert a.primary_owner_key == "video"
    assert "video" in a.member_keys


def test_premiere_controller_emits_valid_fcpxml_and_jsx(tmp_path, monkeypatch):
    from ai_company import premiere_controller as pc
    from ai_company.video_editing import build_timeline
    monkeypatch.setattr(pc, "ROOT", tmp_path)
    tl = build_timeline(
        "후킹 자막.\n사용 장면 1.\n사용 장면 2.\n결과 컷.",
        title="테스트 릴스",
        target_seconds=12.0,
    )
    pkg = pc.write_premiere_package(tl, sequence_name="Test_Seq")
    # 파일 모두 존재
    assert pkg.fcpxml_path.exists() and pkg.jsx_path.exists() and pkg.edl_path.exists()
    assert pkg.readme_path.exists() and pkg.report_path.exists()
    # FCPXML 핵심 태그
    xml = pkg.fcpxml_path.read_text(encoding="utf-8")
    assert "<fcpxml version=" in xml
    assert "<sequence" in xml
    assert "<asset-clip" in xml
    assert "1080" in xml and "1920" in xml  # 9:16
    # 시퀀스 이름이 들어가 있어야 한다
    assert "Test_Seq" in xml
    # ExtendScript 핵심
    jsx = pkg.jsx_path.read_text(encoding="utf-8")
    assert "app.project" in jsx
    assert "importFiles" in jsx
    assert "createBin" in jsx
    # EDL 형식
    edl = pkg.edl_path.read_text(encoding="utf-8")
    assert "TITLE:" in edl
    assert "FCM:" in edl


def test_premiere_launch_blocked_without_approve(tmp_path, monkeypatch):
    from ai_company import premiere_controller as pc
    from ai_company.video_editing import build_timeline
    monkeypatch.setattr(pc, "ROOT", tmp_path)
    tl = build_timeline("후킹.\n사용 장면.\n마무리.", target_seconds=8.0)
    pkg = pc.write_premiere_package(tl, sequence_name="Block_Test")
    # approved=False 면 절대 실행 안 됨
    res = pc.launch_premiere(pkg, approved=False)
    assert res["launched"] is False
    assert "approved=False" in res["reason"]


def test_video_timeline_generation():
    from ai_company.video_editing import build_timeline, to_moviepy_script, to_srt
    script = (
        "사줘도 안 놀던 고양이, 사냥본능을 깨워보세요.\n"
        "고스틱을 천천히 흔들고, 멈췄다가 다시 움직여요.\n"
        "활동량 많은 고양이가 점프하기 시작합니다.\n"
        "오늘 놀이는 고스틱으로 시작해보세요."
    )
    tl = build_timeline(script, title="테스트 릴스", target_seconds=15.0)
    assert len(tl.clips) >= 3
    assert tl.clips[0].start == 0.0
    # 후킹 컷은 짧다
    assert tl.clips[0].end <= 3.0
    assert tl.ratio == "9:16"

    py = to_moviepy_script(tl)
    assert "moviepy" in py
    assert "concatenate_videoclips" in py
    assert "VideoFileClip" in py

    srt = to_srt(tl)
    assert "1\n" in srt
    assert "-->" in srt


def test_video_package_writes_files(tmp_path, monkeypatch):
    from ai_company import video_editing as ve
    monkeypatch.setattr(ve, "ROOT", tmp_path)
    md_path, py_path, srt_path, summary_path = ve.write_video_package(
        "후킹 자막.\n사용 장면.\n결과 장면.", title="테스트", target_seconds=10.0
    )
    assert md_path.exists()
    assert py_path.exists()
    assert srt_path.exists()
    assert summary_path.exists()
    assert "moviepy" in py_path.read_text(encoding="utf-8")


def test_agent_personas_have_required_fields():
    from ai_company.agent_persona import PERSONAS, CEO_PERSONA, PERSONAS_BY_KEY
    keys = {p.key for p in PERSONAS}
    # 사장님 결정 — 데이터·검수는 Claude, 마케팅은 OpenAI
    assert PERSONAS_BY_KEY["data"].model_pref == "claude"
    assert PERSONAS_BY_KEY["review"].model_pref == "claude"
    assert PERSONAS_BY_KEY["marketing"].model_pref == "openai"
    # 그 외는 Ollama 기본
    for k in ("psy", "sns", "product", "naverads"):
        assert PERSONAS_BY_KEY[k].model_pref == "ollama"
    assert CEO_PERSONA.can_be_ceo is True


def test_multi_agent_runtime_falls_back_when_external_dead(monkeypatch, tmp_path):
    # 모든 외부 API와 Ollama 죽음을 모킹 → None 반환
    monkeypatch.setattr("ai_company.multi_agent_runtime.ROOT", tmp_path)
    monkeypatch.setattr("ai_company.multi_agent_runtime._try_claude", lambda *a, **k: None)
    monkeypatch.setattr("ai_company.multi_agent_runtime._try_openai", lambda *a, **k: None)
    monkeypatch.setattr("ai_company.multi_agent_runtime._try_gemini", lambda *a, **k: None)
    monkeypatch.setattr("ai_company.multi_agent_runtime._try_ollama", lambda *a, **k: None)
    from ai_company.multi_agent_runtime import call_persona
    from ai_company.agent_persona import PERSONAS_BY_KEY
    text, provider = call_persona(PERSONAS_BY_KEY["data"], "test", round_num=1)
    assert text is None
    assert provider == "none"
    # 라운드 로그는 적재됐어야 한다
    log = tmp_path / "11_memory" / "agents" / "data_ai" / "rounds.jsonl"
    assert log.exists()


def test_multi_agent_runtime_uses_claude_if_alive(monkeypatch, tmp_path):
    monkeypatch.setattr("ai_company.multi_agent_runtime.ROOT", tmp_path)
    monkeypatch.setattr("ai_company.multi_agent_runtime._try_claude", lambda *a, **k: "데이터 분석 결과 입니다.")
    monkeypatch.setattr("ai_company.multi_agent_runtime._try_openai", lambda *a, **k: None)
    monkeypatch.setattr("ai_company.multi_agent_runtime._try_ollama", lambda *a, **k: None)
    from ai_company.multi_agent_runtime import call_persona
    from ai_company.agent_persona import PERSONAS_BY_KEY
    text, provider = call_persona(PERSONAS_BY_KEY["data"], "test", round_num=1, live=True)
    assert text and "데이터" in text
    assert provider == "claude"


def test_voting_detects_conflict_and_winner():
    from ai_company.voting import tally
    res = tally({
        "data": "동의합니다. 그대로 진행해도 되겠습니다.",
        "psy": "반대합니다. 사용자 심리 측면에서 위험합니다.",
        "sns": "동의합니다.",
        "review": "보완 필요. 위험 표현이 있을 수 있습니다.",
        "marketing": "",  # 기권
    })
    assert "data" in res.agree
    assert "psy" in res.disagree
    assert "review" in res.disagree  # 보완 필요 → 반대 계열
    assert "marketing" in res.abstain
    assert res.conflict is True
    assert res.winner in {"agree", "disagree", "tie"}


def test_ceo_assigner_falls_back_to_keywords_offline():
    from ai_company.ceo_assigner import assign
    a = assign("네이버광고 ROAS 1.4 회복 회의", live=False)
    assert a.primary_owner_key == "naverads"
    assert "naverads" in a.member_keys
    assert a.used_llm is False


def test_multi_agent_meeting_runs_with_all_offline(monkeypatch, tmp_path):
    """모든 어댑터가 죽어도 3라운드 구조 자체는 안전하게 끝나야 한다."""
    monkeypatch.setattr("ai_company.multi_agent_runtime.ROOT", tmp_path)
    monkeypatch.setattr("ai_company.multi_agent_runtime._try_claude", lambda *a, **k: None)
    monkeypatch.setattr("ai_company.multi_agent_runtime._try_openai", lambda *a, **k: None)
    monkeypatch.setattr("ai_company.multi_agent_runtime._try_ollama", lambda *a, **k: "임시 응답: 데이터 위주로 본다.")
    from ai_company.multi_agent_meeting import run_multi_meeting
    result = run_multi_meeting("네이버광고 ROAS 회복", live=False)
    assert len(result.round1) >= 3
    assert len(result.round2) == len(result.round1)
    assert result.ceo_summary
    assert result.vote.winner in {"agree", "disagree", "tie"}


def test_ceo_orchestrator_detects_owner_and_risks():
    from ai_company.ceo_orchestrator import build_plan
    p1 = build_plan("네이버광고 입찰가 변경 검토")
    assert p1.primary_owner == "네이버광고 AI"
    assert any("입찰가" in r for r in p1.risks)
    p2 = build_plan("릴스 썸네일 시안 만들어줘")
    assert p2.primary_owner == "이미지 AI"


def test_execute_routing_respects_live_and_key_presence(monkeypatch):
    from ai_company.model_router import route, execute_routing
    decision = route("Next.js 백엔드 리팩터링")
    # live=False면 무조건 dry-run
    res = execute_routing(decision, "do it", live=False)
    assert res["executed"] is False
    assert res["external_call"] is False
    # claude_runtime 키 없을 때 — 실행 거부 + 친절한 사유
    import ai_company.claude_runtime as cr
    monkeypatch.setattr(cr, "has_api_key", lambda: False)
    res = execute_routing(decision, "do it", live=True)
    assert res["executed"] is False
    assert "ANTHROPIC_API_KEY" in res["reason"]


def test_ollama_live_status_with_live_models(monkeypatch):
    import ai_company.ollama_runtime as rt
    from ai_company.ollama_models import build_ollama_live_status
    fake = {
        "models": [
            {"name": "gemma4:e2b", "size": 7162405886,
             "details": {"parameter_size": "5.1B", "family": "gemma4",
                          "quantization_level": "Q4_K_M"}},
        ]
    }
    monkeypatch.setattr(rt, "_http_get", lambda path, t: fake if path == "/api/tags" else None)
    md, payload = build_ollama_live_status()
    assert payload.get("alive") is True
    assert payload.get("model_count") == 1
    assert payload.get("external_call") is False
    assert "라이브 상태" in md
    assert "gemma4:e2b" in md


def test_ollama_model_list_dry_run(tmp_path):
    md, payload = build_ollama_model_list_dry_run()
    report_path, json_path, approval_path = write_ollama_model_list_dry_run(
        reports_dir=tmp_path,
        memory_dir=tmp_path,
        approval_dir=tmp_path,
    )

    assert "모델 목록 조회 승인형 Dry-run" in md
    assert payload["actual_model_list_query"] is False
    assert payload["actual_model_call"] is False
    assert payload["model_download"] is False
    assert report_path.exists()
    assert json_path.exists()
    assert approval_path.exists()
    assert "읽기 전용 조회" in approval_path.read_text(encoding="utf-8")

def test_image_templates():
    md, data = build_image_templates("GOSTICK01")
    assert "고스틱" in md
    assert "square_feed" in md
    assert data["product_code"] == "GOSTICK01"
    # routing 정보가 없으면 카드 미표시
    assert "## 모델 라우터 결정" not in md
    assert "routing" not in data


def test_image_templates_with_router():
    from ai_company.model_router import route as _route
    decision = _route("고스틱 광고 이미지 썸네일")
    md, data = build_image_templates("GOSTICK01", routing=decision)
    assert "## 모델 라우터 결정" in md
    assert "1순위 모델" in md
    assert "routing" in data
    assert data["routing"]["primary_key"] in {
        "image_ai", "codex_chatgpt", "claude", "gemini", "ollama"
    }

def test_playwright_dry_run_plan():
    md = build_playwright_dry_run("naver_ads")
    assert "Playwright Dry-run" in md
    assert "실제 브라우저 실행 여부: 실행 안 함" in md
    assert "입찰가 변경" in md

def test_cat_recommender_files_exist():
    app_dir = ROOT / "06_apps" / "cat_toy_recommender"
    assert (app_dir / "index.html").exists()
    assert (app_dir / "styles.css").exists()
    assert (app_dir / "app.js").exists()
    html = (app_dir / "index.html").read_text(encoding="utf-8")
    script = (app_dir / "app.js").read_text(encoding="utf-8")
    assert html.count("<fieldset>") == 8
    assert "shareCanvas" in html
    assert "drawSharePreview" in script

def test_experiment_plan():
    md, data = build_experiment_plan("고스틱 광고 효율 개선")
    assert "자동 실험 설계" in md
    assert data["dry_run_only"] is True
    assert len(data["experiments"]) == 3

def test_share_image_design():
    md, spec = build_share_image_design("GOSTICK01")
    assert "공유 이미지 설계" in md
    assert spec["canvas"]["ratio"] == "9:16"
    assert spec["result_code"] == "GOSTICK01"

def test_share_image_png_export(tmp_path):
    png_path, report_path = build_share_image_png("GOSTICK01", output_dir=tmp_path, reports_dir=tmp_path)
    assert png_path.exists()
    assert report_path.exists()
    assert png_path.read_bytes().startswith(b"\x89PNG")
    assert "업로드 안 함" in report_path.read_text(encoding="utf-8")

def test_dry_run_schema():
    md, schema = build_schema_report("naver_ads_keywords")
    assert "Dry-run 데이터 스키마" in md
    assert "입찰가 실제 변경" in md
    assert schema["fields"][0]["name"] == "campaign"

def test_external_dry_run_builders():
    smartstore_md, smartstore_payload = build_smartstore_fetch_dry_run()
    naver_md, naver_payload = build_naver_ads_api_dry_run()
    instagram_md, instagram_payload = build_instagram_upload_dry_run("GOSTICK01")

    assert "실제 로그인 여부: 로그인 안 함" in smartstore_md
    assert smartstore_payload["actual_api_call"] is False
    assert "실제 API 호출 여부: 호출 안 함" in naver_md
    assert naver_payload["mutation_allowed"] is False
    assert "실제 업로드 여부: 업로드 안 함" in instagram_md
    assert instagram_payload["product_code"] == "GOSTICK01"

def test_smartstore_field_mapping():
    md, spec = build_smartstore_field_mapping()
    assert "필드 매핑 설계" in md
    assert spec["actual_api_call"] is False
    assert spec["mutation_allowed"] is False
    assert "salePrice" in spec["blocked_write_fields"]

def test_naver_ads_permission_matrix():
    md, spec = build_naver_ads_permission_matrix()
    assert "권한 매트릭스" in md
    assert spec["actual_api_call"] is False
    assert spec["mutation_allowed"] is False
    assert "keyword_bid_update" in spec["write_endpoints_blocked"]

def test_instagram_asset_manifest():
    md, manifest = build_instagram_asset_manifest("GOSTICK01")
    assert "자산 매니페스트" in md
    assert manifest["actual_upload"] is False
    assert manifest["actual_post"] is False
    assert manifest["customer_message"] is False

def test_model_router_routes_to_correct_panel():
    cases = {
        "고스틱 광고 릴스 썸네일 시안 만들어줘": "image_ai",
        "스마트스토어 상세페이지 문구 검수": "claude",
        "고양이 MBTI 앱 경쟁 서비스 트렌드 조사": "gemini",
        "최근 리뷰 200건을 긍정/부정으로 분류하고 태그": "ollama",
        "FastAPI 백엔드 코드 자동화 스크립트 작성": "codex_chatgpt",
    }
    for task, expected_key in cases.items():
        decision = route(task)
        assert decision.primary.model.key == expected_key, (
            f"task={task!r} → primary={decision.primary.model.key!r}, expected={expected_key!r}"
        )
        assert decision.handoff["dry_run"] is True
        assert decision.handoff["executed"] is False
        assert decision.handoff["approval_required_for_external"] is True


def test_e2e_dry_run_flow_safe_message():
    report = build_e2e_report("고스틱 광고 효율 회의해줘")
    assert report.plan.intent == "meeting"
    assert report.plan.safe_to_run is True
    assert report.meeting_md is not None
    assert "## 모델 라우터 결정" in report.meeting_md
    # 단계 이름들이 모두 들어있는지
    names = [s.name for s in report.steps]
    assert any("텔레그램 인바운드" in n for n in names)
    assert any("Hermes" in n for n in names)
    assert any("모델 라우터" in n for n in names)
    assert any("사장님 알림" in n for n in names)
    md = report.to_markdown()
    assert "실제 텔레그램 API 호출 여부: 호출 안 함" in md


def test_e2e_dry_run_flow_risky_message(tmp_path, monkeypatch):
    monkeypatch.setattr("ai_company.nl_command.ROOT", tmp_path)
    (tmp_path / "09_approval").mkdir()
    report = build_e2e_report("네이버광고 입찰가 200원 올려줘")
    assert report.plan.safe_to_run is False
    assert "입찰가" in report.plan.risk_keywords
    assert report.plan.approval_path is not None
    # 승인 단계가 단계 로그에 들어있어야 한다
    names = [s.name for s in report.steps]
    assert any("승인 파일 자동 생성" in n for n in names)


def test_e2e_dry_run_writes_files(tmp_path, monkeypatch):
    monkeypatch.setattr("ai_company.e2e_dry_run.ROOT", tmp_path)
    monkeypatch.setattr("ai_company.nl_command.ROOT", tmp_path)
    (tmp_path / "08_reports").mkdir()
    (tmp_path / "09_approval").mkdir()
    md_path, json_path = write_e2e_report("고스틱 광고 만들어줘")
    assert md_path.exists()
    assert json_path.exists()
    text = md_path.read_text(encoding="utf-8")
    assert "텔레그램 e2e dry-run" in text


def test_nl_command_intent_classification():
    cases = {
        "고스틱 광고 만들어줘": "ad_package",
        "고스틱 광고 효율 회의해줘": "meeting",
        "네이버 광고 CSV 분석해줘": "analyze_ads",
        "스마트스토어 상품 가져와줘": "smartstore_fetch",
        "릴스 썸네일 시안 만들어줘": "image_templates",
        "Ollama 모델 목록 보여줘": "ollama_models",
    }
    for message, expected_intent in cases.items():
        plan = nl_interpret(message)
        assert plan.intent == expected_intent, (
            f"message={message!r} → intent={plan.intent!r}, expected={expected_intent!r}"
        )
        assert plan.routing is not None
        assert plan.cli  # CLI 후보가 비어 있지 않음


def test_nl_command_blocks_risky_keywords(tmp_path, monkeypatch):
    monkeypatch.setattr("ai_company.nl_command.ROOT", tmp_path)
    (tmp_path / "09_approval").mkdir()
    plan = nl_interpret("네이버광고 입찰가를 200원 올려줘")
    assert plan.safe_to_run is False
    assert "입찰가" in plan.risk_keywords
    assert plan.approval_required is True
    assert plan.approval_path is not None
    from pathlib import Path
    assert Path(plan.approval_path).exists()


def test_nl_command_empty_message():
    plan = nl_interpret("")
    assert plan.intent == "empty"
    assert plan.safe_to_run is False
    assert plan.cli == []


def test_nl_command_risk_keywords_cover_safe_rules():
    # CODEX_SAFE_RULES의 위험 단어가 RISK_KEYWORDS에 모두 포함되는지
    for kw in ("입찰가", "광고비", "업로드", "결제", "환불", "로그인", "비밀번호"):
        assert kw in RISK_KEYWORDS


def test_routed_meeting_includes_routing_card():
    result = run_routed_meeting("스마트스토어 상세페이지 문구 검수")
    assert result.routing is not None
    assert result.routing.primary.model.key == "claude"
    assert "Claude" in result.ceo_decision

    from ai_company.meeting import meeting_to_markdown
    md = meeting_to_markdown(result)
    assert "## 모델 라우터 결정" in md
    assert "Claude" in md
    assert "dry-run" in md


def test_meeting_without_router_keeps_old_behavior():
    result = run_meeting("고스틱 광고 효율 개선")
    assert result.routing is None
    from ai_company.meeting import meeting_to_markdown
    md = meeting_to_markdown(result)
    assert "## 모델 라우터 결정" not in md


def test_model_router_fallback_for_unknown_task():
    decision = route("어떤 모델을 써야할지 알 수 없는 모호한 요청")
    # 키워드가 안 잡히면 Claude로 폴백
    assert decision.primary.model.key == "claude"


def test_model_router_writes_collision_safe_files(tmp_path, monkeypatch):
    monkeypatch.setattr("ai_company.model_router.ROOT", tmp_path)
    (tmp_path / "08_reports").mkdir()
    md1, json1 = writ