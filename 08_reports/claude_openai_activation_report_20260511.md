# Claude(코딩) + OpenAI(디자인) 어댑터 활성화 보고서

## 1. 사장님 결정

> "코딩은 클로드, 디자인은 ChatGPT API 사용할 수 있게 해줘"

이 결정대로 라우팅 매핑과 어댑터를 모두 재구성했다. **외부 API라 토큰
비용이 발생**하므로 4중 안전 가드를 박았다.

## 2. 활성화한 모듈

| 모듈 | 역할 | 비용 안전 가드 |
|---|---|---|
| `ai_company/claude_runtime.py` (신규) | Anthropic Claude — 코딩/검수/긴 문서 | live=False이거나 키 없으면 None |
| `ai_company/openai_runtime.py` (신규) | OpenAI ChatGPT + DALL-E — 디자인/이미지 | live=False이거나 키 없으면 None |
| `ai_company/model_router.py` | 매핑 갱신 + `execute_routing()` | 키 부재 시 친절한 사유와 함께 거부 |
| `ai_company/main.py` | `env-check`, `routed-run --live` CLI | live 플래그 명시 필수 |
| `scripts/local_viewer_server.py` | `/api/providers/status` | 키 존재 여부만 노출, 값 절대 안 보냄 |
| `06_apps/agent_matrix/agents_data.js` | 자동 오케스트레이션 매핑 갱신 | (전략 변경만) |
| `06_apps/agent_matrix/app.js` | 라이브 상태 3개 공급자 표시 | 각 행 옆 🟢 KEY / 🟢 LIVE / 🟢 DALL-E |
| `tests/test_smoke.py` | 7건 추가 | 키 없을 때 폴백, 모킹된 응답 파싱, 라우팅 분기 |

## 3. 자동 오케스트레이션 매핑 (사장님 결정 반영)

```
suyeong   → Claude        (사장님 비서, 긴 문맥)
ceo       → Claude
marketing → OpenAI        (디자인 카피)
sns       → OpenAI        (릴스/인스타 톤)
image     → 이미지 AI     (DALL-E 실제 이미지)
smartstore→ Ollama        (상품/리뷰 반복 정리)
naverads  → Claude        (광고 분석/문서)
developer → Claude        (코딩 전반)
data      → Ollama        (분류·요약)
review    → Claude        (검수)
researcher→ Gemini
```

라우터 키워드도 그에 맞게 재배치:
- "코딩 / 코드 / 리팩터 / 자동화 / 백엔드 / CLI" → **Claude**
- "디자인 / 비주얼 / 광고 / 마케팅 / 톤앤매너" → **OpenAI (ChatGPT)**
- "이미지 / 썸네일 이미지 / 그려 / 렌더 / DALL-E" → **이미지 AI (DALL-E)**

## 4. 비용 안전 가드 (4중)

1. **명시 옵션 필수** — `--live` 플래그 없으면 절대 호출 안 함
2. **키 부재 → 자동 차단** — `_load_api_key()`가 None 반환 시 함수가 즉시 None
3. **max_tokens 기본 제한** — Claude 1000, OpenAI 800 (한 호출 한국어 약 4~6 문단)
4. **이미지 생성 n 제한** — DALL-E n 매개변수 자동 max 4로 클램프

추가로:
- API 키 값은 어디에서도 절대 출력 안 됨 (status_summary, env-check, 보고서 모두 "있음/없음"만)
- 외부 채널 반영(스마트스토어/네이버광고/SNS 업로드)은 변경 없이 그대로 차단

## 5. 새 CLI 명령

```powershell
cd D:\AI_COMPANY
.\.venv\Scripts\Activate.ps1

# (1) 키 존재 점검 — 값은 절대 출력 안 함
python -m ai_company.main env-check

# (2) 라우터 + 실제 어댑터 호출 (코딩 → Claude)
python -m ai_company.main routed-run --task "FastAPI 백엔드 리팩터링 가이드" --live

# (3) 라우터 + 실제 어댑터 호출 (디자인 → OpenAI)
python -m ai_company.main routed-run --task "고스틱 광고 디자인 카피 톤앤매너" --live

# (4) 회의 라이브 모드는 그대로 Ollama 사용 (로컬, 무료)
python -m ai_company.main meeting --topic "고스틱 광고 효율" --with-router --live
```

`--live` 없이 실행하면 라우터 결정만 보이고 호출은 안 됩니다 (비용 0).

## 6. 사장님이 해주셔야 할 것

`D:\AI_COMPANY\.env` 파일을 메모장으로 열어서 다음 두 줄에 키를 채워주세요:

```
ANTHROPIC_API_KEY=sk-ant-...        # Claude 콘솔에서 발급
OPENAI_API_KEY=sk-...               # OpenAI 콘솔에서 발급
```

그 다음:

```powershell
python -m ai_company.main env-check
```

위에서 `[OK]  Claude API (코딩)`, `[OK]  OpenAI API (디자인)` 둘 다 표시되면 끝.
이후 `routed-run --live` 또는 시뮬레이터의 자연어 명령이 실제 호출로 동작합니다.

## 7. 사장님이 페이지에서 보실 변화

직원 매트릭스 → 모델 오케스트레이션 모달의 라이브 상태 줄:

```
🟢 Ollama 🟢 LIVE · Claude(코딩) 🟢 KEY · OpenAI(디자인) 🟢 KEY
```

각 에이전트 행 옆에는 매핑된 공급자에 따라 🟢 LIVE / 🟢 KEY / 🟢 DALL-E 태그.

## 8. 안전 체크리스트

- [x] `.env` 값 절대 출력 안 함 (env-check, status_summary, 보고서, UI 전부)
- [x] live=False면 외부 호출 0
- [x] 키 부재 시 자동 차단 + 친절한 사유 메시지
- [x] max_tokens 기본 제한
- [x] DALL-E n 제한 (1~4)
- [x] 위험 키워드 자동 차단 / 09_approval 흐름 그대로 유지
- [x] 외부 채널 반영(스마트스토어/네이버광고/SNS) 변경 없음

## 9. 다음 추천 작업

- Gemini 어댑터 (`gemini_runtime.py`) — `GOOGLE_API_KEY` 채우면 같은 패턴
- 호출당 토큰/비용 추정치 로그 (`12_logs/llm_usage.jsonl`)
- 일일/월간 비용 캡 — 한도 초과 시 자동 차단
- 회의 결과를 Claude에게 검수 시키는 `meeting --review-with-claude` 옵션
