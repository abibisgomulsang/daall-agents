# 비용 가드 + Gemini 어댑터 활성화 보고서

## 1. 한 문장 요약

사장님이 Claude/OpenAI 키를 채워주신 상태에서 **호출당 토큰/비용 자동 기록**,
**일일·월간 비용 캡 자동 차단**, **Gemini 어댑터(키 없으면 dry-run)**를 추가했다.
키 값은 어디에서도 출력되지 않으며, 모든 호출은 캡 통과 후에만 실행된다.

## 2. 새 모듈

| 모듈 | 역할 |
|---|---|
| `ai_company/usage_log.py` | 호출당 토큰을 `12_logs/llm_usage.jsonl`에 적재. 모델별 단가표(USD/MTok)와 환율로 KRW 비용 추정 |
| `ai_company/usage_caps.py` | 일일/월간 캡 검사. 호출 전에 `check_cap()`로 차단 가능 |
| `ai_company/gemini_runtime.py` | Google Gemini 어댑터. 키 없으면 None 폴백 |

## 3. 기본 캡

| 항목 | 기본값 | 환경변수로 조정 |
|---|---|---|
| 일일 캡 | ₩1,000 | `DAILY_LLM_CAP_KRW` |
| 월간 캡 | ₩30,000 | `MONTHLY_LLM_CAP_KRW` |
| USD→KRW | 1,400 | `USD_TO_KRW` |

캡 초과 시 호출 함수가 즉시 `[Claude blocked] ...` / `[OpenAI blocked] ...`
같은 문자열을 반환하고 실제 API 호출은 발생하지 않는다.

## 4. 단가표 (USD per 1M tokens)

| 모델 | 입력 | 출력 |
|---|---|---|
| claude-haiku-4-5 | $1.0 | $5.0 |
| claude-sonnet-4-5 | $3.0 | $15.0 |
| claude-opus-4-6 | $15.0 | $75.0 |
| gpt-4o-mini | $0.15 | $0.60 |
| gpt-4o | $2.50 | $10.0 |
| gemini-1.5-flash | $0.075 | $0.30 |
| gemini-1.5-pro | $1.25 | $5.0 |

DALL-E 3 표준 1024×1024는 이미지당 $0.04. 단가표는
`PRICING_OVERRIDE_JSON` 환경변수로 갱신 가능.

## 5. 어댑터 수정사항

- **`claude_runtime.py`**, **`openai_runtime.py`**, **`gemini_runtime.py`**
  세 어댑터 모두 호출 직전에 `usage_caps.check_cap()` 통과해야 실제 HTTP 요청.
  호출 후 응답의 `usage` 메타데이터로 토큰 카운트를 받아 `usage_log`에 자동 기록.
- **`model_router.execute_routing()`**에 Gemini 분기 추가. 라우터가 리서치
  의도를 만나면 Gemini로 보내고, 키 없으면 친절한 사유 반환.

## 6. 새 CLI

```powershell
# 환경 점검 + 오늘 사용량/캡
python -m ai_company.main env-check

# 사용량 보고서를 08_reports에 저장
python -m ai_company.main usage-report
```

`env-check` 출력 예시:

```
============================================================
 AI 회사 환경 점검 — 키 값은 절대 출력하지 않습니다
============================================================
  [OK]  Ollama (로컬, 무료)      (127.0.0.1:11434 응답 여부)
  [OK]  Claude API (코딩)        (ANTHROPIC_API_KEY in .env)
  [OK]  OpenAI API (디자인)      (OPENAI_API_KEY in .env)
  [--]  Gemini API (리서치)      (GOOGLE_API_KEY in .env)
------------------------------------------------------------
  오늘 LLM 호출: 0회 · ₩0 / 일일 캡 ₩1,000
  이번 달 호출: 0회 · ₩0 / 월 캡 ₩30,000
============================================================
```

## 7. UI 변경

직원 매트릭스 → 모델 오케스트레이션 모달의 라이브 상태 줄:

```
Ollama 🟢 LIVE · Claude(코딩) 🟢 KEY · OpenAI(디자인) 🟢 KEY ·
Gemini(리서치) ⚪ no key · 오늘 0회 · ₩0 / 캡 ₩1,000
```

매핑된 에이전트 행에는 매핑 공급자에 따라 🟢 LIVE / 🟢 KEY / 🟢 DALL-E 태그.

## 8. 동작 흐름 (안전 경로)

```
호출 요청 (claude_runtime.generate(..., live=True))
   ↓ 키 존재 검사 → 없으면 None
   ↓ usage_log.estimate_text_cost_krw(...) 로 ₩ 추정
   ↓ usage_caps.check_cap(추정) 통과
   ↓ HTTP POST → 응답
   ↓ usage.input_tokens / output_tokens 회수
   ↓ usage_log.log_text_call(...) 으로 jsonl 적재
   ↓ 호출자에게 텍스트 반환
```

## 9. 사장님 확인 필요한 부분

- 기본 캡(₩1,000/일, ₩30,000/월)이 적절한지
- 첫 실호출 결과 확인: `python -m ai_company.main routed-run --task "..." --live`
- Gemini 채우실 의사가 있으시면 `.env`의 `GOOGLE_API_KEY` 추가 → 자동 활성화

## 10. 안전 확인

- [x] API 키 값: 모든 보고서/UI/CLI/로그에서 절대 노출 안 됨
- [x] 호출 직전 캡 검사 → 초과 시 자동 차단
- [x] 비용 추정치는 모델별 단가표 기준, 정확 청구액은 공급자 콘솔 기준
- [x] `--live` 옵션 없으면 외부 호출 0
- [x] `usage_log.jsonl`에는 토큰 수와 비용 추정치만 — 프롬프트 본문 저장 안 함
- [x] 위험 키워드 자동 차단 / 09_approval 흐름 그대로 유지
