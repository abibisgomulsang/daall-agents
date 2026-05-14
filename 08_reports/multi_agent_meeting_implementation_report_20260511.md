# 멀티 에이전트 3라운드 토론 구축 보고서

## 1. 사장님 요청 4가지 — 전부 충족

| 요청 | 충족 방법 |
|---|---|
| Ollama 무료 기본, 직원별 모델/페르소나/메모리 분리 | `agent_persona.py` — 7개 페르소나, 데이터/검수=Claude, 마케팅=OpenAI, 나머지 Ollama |
| 토론 라운드 1→2→3 | `multi_agent_meeting.py` — 의견 → 반박/동조 → CEO 종합 |
| CEO가 LLM으로 작업 분배 | `ceo_assigner.py` — CEO 페르소나에게 JSON 응답 요청, 실패 시 키워드 폴백 |
| 의견 충돌 시 표결/CEO 판단 | `voting.py` — 동의/반대/보완 키워드 자동 분류 + CEO 라운드3에서 명시적 판단 |

## 2. 신규 모듈

| 파일 | 역할 |
|---|---|
| `ai_company/agent_persona.py` | 7명 직원 + CEO 페르소나 정의. 직원별 model_pref·system_prompt·voice·memory_dir |
| `ai_company/multi_agent_runtime.py` | 페르소나별 어댑터 분기 호출. 실패/캡 초과 시 자동 Ollama 폴백. `11_memory/agents/{dir}/rounds.jsonl` 적재 |
| `ai_company/ceo_assigner.py` | CEO LLM이 회의 멤버·1차 책임자 결정. JSON 파싱 실패 시 키워드 폴백 |
| `ai_company/voting.py` | 라운드2 답변에서 동의/반대/보완 자동 분류, winner·conflict 산출 |
| `ai_company/multi_agent_meeting.py` | 3라운드 토론 엔진 + 비용 추정 + 캡 검사 + 자동 강등 + 결과 저장 |
| `docs/MULTI_AGENT_MEETING.md` | 구조/명령/안전 가이드 |

## 3. 수정 파일

- `ai_company/main.py` — `multi-meeting --topic "..." [--no-live]` CLI 추가. `boss-command --multi` 플래그 추가.
- `ai_company/boss_pipeline.py` — 5단계 회의를 `multi=True`일 때 `run_multi_meeting`으로 교체.
- `tests/test_smoke.py` — 6건 추가 (페르소나/런타임 폴백/투표/CEO 분배/회의 전체 흐름)

## 4. 비용 보호 — 자동 동작

회의 시작 직전에 추정 비용을 계산하고 `usage_caps.check_cap()`로 검사합니다.

- 데이터/검수 Claude × 2라운드 + 마케팅 OpenAI × 2라운드 + CEO 종합 1회 = **약 ₩100~200/회**
- 일일 캡 ₩1,000이면 회의 5~10회 가능
- 캡 초과 위험이면 **자동으로 `force_ollama=True` 강등** → 모두 무료

회의록에 `force_ollama: 적용 (전부 Ollama)` / `추정 비용: ₩142` 같이 명시되어 사장님이 즉시 확인 가능.

## 5. 메모리

각 직원은 자기 폴더(`11_memory/agents/<persona.memory_dir>/rounds.jsonl`)에 라운드 기록을 누적합니다.

**저장되는 것**: 시각, 라운드 번호, topic 앞 60자, 응답 길이, 사용한 공급자(provider), 성공 여부.
**저장 안 되는 것**: 프롬프트 본문, 응답 본문(요약/길이만), API 키.

추후 직원이 자기 과거 발언을 참조하려면 `multi_agent_runtime.load_recent_rounds()` 사용 가능.

## 6. 사용 방법

```powershell
cd D:\AI_COMPANY
.\.venv\Scripts\Activate.ps1

# 단독 멀티 회의 — 외부 API 사용 (캡 자동)
python -m ai_company.main multi-meeting --topic "네이버광고 ROAS 1.4 회복"

# 외부 API 안 쓰고 전부 Ollama로
python -m ai_company.main multi-meeting --topic "고스틱 광고 후킹 전략" --no-live

# 사장님 명령 7단계 + 멀티 회의 (5단계만 토론 모드)
python -m ai_company.main boss-command --message "고스틱 광고 효율 개선" --live --multi
```

결과는 `10_meetings/multi_meeting_*.md` 와 `_.json` 으로 저장. 각 직원 메모리는
`11_memory/agents/<dir>/rounds.jsonl` 에 누적.

## 7. 출력 예시 (force_ollama 강등이 동작한 회의)

```markdown
# 멀티 에이전트 회의 결과
- 주제: 네이버광고 ROAS 1.4 회복
- 본질(CEO): 광고 효율 회복 + 카피 검토
- 1차 책임: 네이버광고 AI
- 회의 멤버: 네이버광고 AI, 데이터 AI, 고객심리 AI, 마케팅 AI, 검수 AI
- CEO LLM 분배 사용: 예
- 비용 보호 강등: 없음
- 추정 비용: ₩142

## 라운드 1 — 각자 의견
### 데이터 AI  _(claude)_
...

## 라운드 2 — 다른 의견 보고 반박/동조
### 검수 AI  _(claude)_
반대. 위험 표현 가능성...

## 표결 결과
- 동의: data, sns
- 반대: review
- 충돌 여부: 있음
- 1차 결론: agree
- 비고: 동의 2, 반대 1, 기권 2

## 라운드 3 — CEO 종합 결론
_(공급자: claude)_
표결에서는 동의 우위지만 검수 AI의 위험 지적은 무게가 있다.
실행 전 09_approval 승인을 받고 ...
```

## 8. 안전 체크리스트

- [x] 외부 API 호출 — `--live` 명시 + 캡 통과 시만
- [x] 캡 초과 위험 → 자동 Ollama 강등
- [x] 키 부재 → 자동 Ollama 폴백
- [x] 프롬프트 본문 저장 안 함 (토큰 수·길이만)
- [x] API 키 값 어디에도 노출 안 됨
- [x] 사장님 승인 흐름이 CEO 결론에 자동 명시
- [x] 외부 채널 자동 반영 — 없음

## 9. 사장님이 첫 회의 돌려보시는 명령

```powershell
python -m ai_company.main multi-meeting --topic "고스틱 광고 효율 개선" 
```

이 한 줄로 7개 직원이 자기 모델/페르소나로 3라운드 토론합니다.
**예상 비용 ₩100~200**, 캡 안에서 자동 진행. 결과는 `10_meetings/` 폴더의
최신 `multi_meeting_*.md`에서 확인하시면 됩니다.

## 10. 다음 추천 작업

- 가상 사무실 UI의 "대화록" 탭에 멀티 회의 실제 발언 표시
- 직원 메모리(rounds.jsonl)를 라운드 입력에 반영 — "지난번 회의에서 데이터 AI가 말한 그 키워드..."
- 회의 결론을 자동으로 09_approval 파일에 첨부
- Gemini API 키 채우시면 리서처 AI도 외부 API로 승격
