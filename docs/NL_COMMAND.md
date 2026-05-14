# 자연어 명령 인터페이스 (NL Command)

사장님이 한국어 자연어로 명령을 내리면 시스템이 자동으로:

1. **의도 분류** — 회의 / 광고 / 분석 / 이미지 / 인스타 / 라우터 등
2. **모델 라우터 통과** — Codex/Claude/Gemini/Ollama/이미지 AI 중 1순위 결정
3. **CLI 명령으로 변환** — `python -m ai_company.main ...` 인자 생성
4. **안전 검사** — 위험 키워드 자동 차단 + 09_approval 파일 자동 생성

## 흐름

```
사장님 자연어 입력
   ↓
[ai_company/nl_command.py]
   ├─ _classify_intent (키워드 기반 의도 분류)
   ├─ _find_risk_keywords (CODEX_SAFE_RULES 위험 단어)
   └─ route_model (모델 라우터 통과)
   ↓
NLPlan {intent, cli, routing, safe_to_run, approval_path}
   ↓
실행 모드 두 가지
   ├─ 기본: 해석 보고서만 출력 (08_reports/nl_command_plan_*.md)
   └─ --execute: 안전한 경우만 CLI 실제 실행
```

## 사용 방법

### 해석만 (실행 안 함)

```powershell
python -m ai_company.main nl --message "고스틱 광고 만들어줘"
python -m ai_company.main nl --message "네이버 광고 효율 회의해줘"
python -m ai_company.main nl --message "릴스 썸네일 시안"
python -m ai_company.main nl --message "스마트스토어 상세페이지 가져와"
```

출력 예시:

```
# 자연어 명령 해석 결과
- 입력 메시지: 고스틱 광고 만들어줘
- 분류 의도: **ad_package** — 광고 패키지 생성
- 실행 가능 여부: 바로 실행 가능
- CLI 후보: `python -m ai_company.main ad --product GOSTICK01`
- 모델 라우터 1순위: **Codex / ChatGPT** (코딩, 시스템 구축, 전략) / 점수 3
```

### 해석 + 실제 실행

```powershell
python -m ai_company.main nl --message "고스틱 광고 만들어줘" --execute
```

`--execute` 플래그가 있어도, 위험 키워드가 포함되면 자동 차단되고 09_approval
파일이 생성된다.

### 위험 키워드 차단 예시

```powershell
python -m ai_company.main nl --message "네이버광고 입찰가 200원 올려줘"
```

결과:

```
- 실행 가능 여부: 승인 필요
- 위험 키워드: 입찰가
- 승인 필요: 09_approval 파일 생성됨
```

## 지원 의도 (현재)

| 의도 key | 트리거 키워드 | CLI |
|---|---|---|
| meeting | 회의, meeting, 토론 | `meeting --topic ... --with-router` |
| analyze_ads | 네이버, csv, 광고 분석, ROAS | `analyze-ads --csv ...` |
| dashboard | 대시보드, dashboard | `dry-run-dashboard` |
| approval_queue | 우선 + 승인 | `approval-priority-queue` |
| approval_risk | 승인 + 위험 / 위험 + 리포트 | `approval-risk-report` |
| approvals_list | 승인, approval | `approvals list` |
| ollama_models | ollama, 올라마, 모델 + 목록 | `ollama-model-list-dry-run` |
| connection_stages | 텔레그램/n8n/Hermes/연결 | `connection-stages` |
| experiment | 실험, AB | `experiment-plan --topic ...` |
| image_templates | 썸네일, 이미지, 포스터, 비주얼 | `image-templates --product ...` |
| instagram_dry_run | 인스타, instagram | `instagram-upload-dry-run --product ...` |
| smartstore_fetch | 스마트스토어, 상세페이지 | `smartstore-fetch-dry-run` |
| playwright_dry_run | 플레이라이트, playwright, 브라우저 | `playwright-dry-run --target naver_ads` |
| ad_package | 광고, 릴스, 문구 | `ad --product ...` |
| office_simulator | 시뮬레이터, 사무실 | `office-simulator` |
| model_router | 라우터, 어느/어떤 모델 | `model-router --task ...` |
| meeting_fallback | (그 외) | `meeting --topic ... --with-router` |

새 의도 추가는 `_classify_intent`에 키워드 분기 한 줄 추가하면 된다.

## 위험 키워드 (자동 차단)

`CODEX_SAFE_RULES.md`의 위험 단어를 그대로 옮겼다.

```
삭제, 대량 삭제, 결제, 주문, 환불,
업로드, 게시, 발송, 입찰가, 광고비,
배포, 로그인, 쿠키, 토큰, 비밀번호
```

이 단어가 포함되면 `safe_to_run=False`로 표시되고, `09_approval/`에
`APPROVAL_REQUIRED_nl_command_*.md` 파일이 자동 생성된다. `--execute`로도
실행되지 않는다. 사장님이 승인 파일을 검토하고 별도로 실제 CLI를 실행해야
한다.

## 통합 포인트

- **시뮬레이터 채팅 UI** — `scripts/local_viewer_server.py`의 `plan_chat_command()`와 공존.
  추후 `nl_interpret()`로 통합 가능.
- **텔레그램 봇** — Hermes/n8n 단계에서 텔레그램 메시지를 `nl_interpret`로 넘기면
  자동 명령 실행이 된다 (위험 메시지는 차단).
- **AgentAU 오케스트레이션** — NLPlan의 `handoff` 정보를 그대로 AgentAU에 넘기면
  AI 회의로 진입한다.

## 안전 규칙

- 자체 CLI 호출은 `subprocess.run(check=False)` 기반. 외부 네트워크/SNS 호출
  없음.
- 위험 키워드 자동 차단 + 승인 파일 생성.
- 빈 메시지는 의도 분류 거부.
- `--execute`가 없으면 절대 실제 CLI를 실행하지 않는다.
