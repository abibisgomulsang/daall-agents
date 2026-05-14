# 사장님이 AI 직원에게 명령 내리는 법 (전체 로직 포함)

## 한 줄 요약

**사장님은 자연어 한 문장만 입력하시면 됩니다.** 시스템이 알아서:
의도 분류 → 위험 검사 → 모델 선택 → 어댑터 호출 → 보고서 저장.

---

## 명령 진입점 4가지

### 1) CLI 자연어 — 가장 일반적

```powershell
python -m ai_company.main nl --message "고스틱 광고 만들어줘"
python -m ai_company.main nl --message "스마트스토어 상세페이지 검수" --execute --live
```

- `--execute` 없으면: 의도 해석 + 라우팅 + CLI 후보만 보고서로 저장 (실행 X)
- `--execute` 있으면: 안전 명령은 실제 CLI 실행, 위험 명령은 자동 차단
- `--live` 있으면: Ollama가 살아있을 때 의도 분류 사유에 LLM 코멘트 한 줄 추가

### 2) CLI 라우터 직호출 — 자연어를 곧장 LLM에 전달

```powershell
python -m ai_company.main routed-run --task "FastAPI 헬스체크 한 줄 짜줘" --live
python -m ai_company.main routed-run --task "고스틱 광고 썸네일 카피 톤앤매너" --live
```

라우터가 알아서:
- 코딩 키워드 → **Claude**
- 디자인 키워드 → **OpenAI ChatGPT**
- 이미지 생성 → **OpenAI DALL-E**
- 리서치 → **Gemini** (키 없으면 dry-run)
- 반복 정리 → **Ollama** (로컬, 무료)

### 3) CLI 특정 작업 — 직접 지정

```powershell
# AI 회의
python -m ai_company.main meeting --topic "고스틱 광고 효율" --with-router --live

# 광고 패키지 (릴스/문구/이미지 지시서/검수)
python -m ai_company.main ad --product GOSTICK01 --with-router

# 이미지 광고 템플릿
python -m ai_company.main image-templates --product GOSTICK01 --with-router

# 네이버광고 CSV 분석
python -m ai_company.main analyze-ads --csv data/naver_ads_sample.csv
```

### 4) 브라우저 시뮬레이터 채팅 — 자연어 GUI

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_local_viewer.ps1 -OpenBrowser
```

시뮬레이터 페이지의 채팅창에 한국어로 입력:

```
고스틱 광고 회의해줘
네이버광고 csv 분석해줘
스마트스토어 상세페이지 가져와줘
```

응답 위에 라우팅 카드(파란 보더)와 실행 결과가 함께 표시됩니다.

---

## 내부 로직 — 명령 한 줄이 처리되는 전 경로

```
[사장님]
   │  자연어 한 줄 (예: "고스틱 광고 만들어줘")
   ▼
┌──────────────────────────────────────────────────┐
│ 1. nl_command.interpret()                         │
│    · 키워드 기반 의도 17종 중 분류                  │
│    · 위험 단어 검사 (입찰가/광고비/업로드/결제 등)   │
│    · 모델 라우터 통과 (다음 단계)                   │
└──────────────────┬───────────────────────────────┘
                   ▼
┌──────────────────────────────────────────────────┐
│ 2. model_router.route()                           │
│    · 키워드 점수로 1순위 모델 결정                  │
│    · Codex(ChatGPT) / Claude / Gemini /           │
│      Ollama / 이미지 AI 중 하나                    │
│    · 후순위/사유 포함 RoutingDecision 반환          │
└──────────────────┬───────────────────────────────┘
                   ▼
            ┌──────────────┐
            │ 위험 키워드?  │
            └──┬─────────┬─┘
        예    │         │  아니오
              ▼         ▼
┌──────────────────┐  ┌─────────────────────────────┐
│ 09_approval 자동  │  │ 3. execute_routing()         │
│ 승인 파일 생성    │  │    · 매핑된 어댑터 호출       │
│ (실행 차단)       │  └─┬───────────────────────────┘
│                  │    │
│ 사장님이 별도로   │    │
│ approve 명령 후만 │    ▼
│ 실제 실행 가능    │   ┌─────────────────────────┐
└──────────────────┘   │ 4. usage_caps.check_cap │
                       │  · 일일/월간 비용 검사    │
                       │  · 초과면 즉시 차단      │
                       └─────┬───────────────────┘
                             ▼
                       ┌─────────────────────────┐
                       │ 5. 어댑터별 HTTP 호출    │
                       │  · claude_runtime       │
                       │  · openai_runtime       │
                       │  · gemini_runtime       │
                       │  · ollama_runtime       │
                       └─────┬───────────────────┘
                             ▼
                       ┌─────────────────────────┐
                       │ 6. usage_log 자동 기록   │
                       │  · 토큰 수, 비용 추정    │
                       │  · 프롬프트 본문 X        │
                       └─────┬───────────────────┘
                             ▼
                       ┌─────────────────────────┐
                       │ 7. 결과 저장             │
                       │  · 08_reports/*.md       │
                       │  · 10_meetings/*.md      │
                       │  · 02_marketing/*.md     │
                       └─────────────────────────┘
```

## 모델별 담당 작업 (현재 매핑)

| 작업 종류 | 담당 모델 | 위치 |
|---|---|---|
| 코딩 / 백엔드 / CLI / 리팩터 | **Claude** | 외부 API (`.env` 키) |
| 검수 / 긴 문서 / 기획서 | **Claude** | 외부 API |
| 광고 카피 / 디자인 / 비주얼 | **OpenAI ChatGPT** | 외부 API |
| 마케팅 전략 / 톤앤매너 | **OpenAI ChatGPT** | 외부 API |
| 썸네일/포스터 이미지 생성 | **OpenAI DALL-E** | 외부 API |
| 트렌드/리서치/경쟁사 조사 | **Gemini** | 외부 API |
| 분류·태그·반복 정리 | **Ollama gemma4** | 로컬 (무료) |
| 가벼운 분류 / 빠른 응답 | **Ollama gemma4:e2b** | 로컬 (무료) |

## 안전 가드 (자동, 사장님 신경 안 쓰셔도 됨)

1. **위험 키워드 자동 차단** — `입찰가`, `광고비`, `업로드`, `결제`, `로그인`, `발송`, `삭제` 등 15개 단어가 들어오면 자동으로 09_approval 파일을 만들고 실행 차단
2. **일일/월간 비용 캡** — 기본 ₩1,000/일, ₩30,000/월. 초과 위험 시 호출 자체가 안 일어남
3. **--live 명시 필수** — 외부 API 호출은 사장님이 명시할 때만
4. **키 부재 자동 폴백** — 키 없으면 dry-run으로 자동 폴백
5. **외부 채널 반영 끝까지 차단** — 어떤 명령으로도 자동으로 스마트스토어/네이버광고/SNS에 반영 안 됨. 항상 09_approval 승인 → 사장님 직접 실행

## 실전 시나리오 3개

### 시나리오 A — 광고 패키지 빠르게

```powershell
python -m ai_company.main ad --product GOSTICK01 --with-router
```

결과: `08_reports/ad_package_GOSTICK01_*.md` + `09_approval/APPROVAL_REQUIRED_ad_GOSTICK01_*.md`

→ 사장님이 보고서 검토 후 마음에 들면 별도로 SNS 업로드 (이건 수동, 자동 안 함)

### 시나리오 B — "고스틱 광고 효율 회의해줘"

```powershell
python -m ai_company.main nl --message "고스틱 광고 효율 회의해줘" --execute --live
```

내부 흐름:
1. nl_interpret → 의도 `meeting`
2. 라우터 → Claude (회의 결과 검토용)
3. CLI: `meeting --topic "고스틱 광고 효율" --with-router --live`
4. Claude가 각 AI 직원 의견 생성 (Ollama 살아있으면 Gemma4 폴백 가능)
5. 회의록 + 09_approval 자동 생성

### 시나리오 C — 위험 명령 시도 (자동 차단 확인)

```powershell
python -m ai_company.main nl --message "네이버광고 입찰가 200원 올려줘" --execute --live
```

결과: 자동 차단 + `09_approval/APPROVAL_REQUIRED_nl_command_*.md` 자동 생성. 실제 입찰 변경은 발생 안 함.

## 점검 명령 (수시로)

```powershell
# 키와 사용량 한눈에
python -m ai_company.main env-check

# 오늘 LLM 호출 비용 누적 보고서
python -m ai_company.main usage-report

# 승인 대기 파일 목록
python -m ai_company.main approvals list

# Ollama 라이브 상태
python -m ai_company.main ollama-live-status
```

## 결과는 어디에 쌓이나

| 폴더 | 내용 |
|---|---|
| `08_reports/` | 모든 보고서 (회의록 / 광고 / 라우팅 / 사용량) |
| `09_approval/` | 위험 명령 자동 생성 승인 대기 파일 |
| `10_meetings/` | AI 회의 결과 |
| `02_marketing/` | 광고 패키지 |
| `05_naver_ads/` | 네이버광고 분석 |
| `12_logs/` | 활동 로그 + `llm_usage.jsonl` (토큰/비용 추정) |
