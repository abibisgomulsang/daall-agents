# 모델 라우터 구축 보고서

## 1. 수행한 일

사장님이 공유한 아키텍처 다이어그램 중 비어 있던 **모델 라우터** 단계를
구현했다.

```
사장님 → Hermes/AgentAU/n8n → CEO 오케스트레이터 → [모델 라우터 ← 신규]
   → (Codex/ChatGPT · Claude · Gemini · Ollama · 이미지 AI)
   → AI 회의 → 실행 준비 → 사장님 승인
```

모델 라우터는 작업 설명을 받아 5개 모델 패널 중 가장 적합한 곳으로
점수 기반 라우팅 결정을 생성한다. **실제 API 호출/모델 다운로드/외부 발송은
하지 않는다.** 모든 결과는 dry-run 핸드오프 페이로드로만 만들어진다.

## 2. 생성/수정한 파일

- `ai_company/model_router.py` (신규)
  - `ModelProfile`, `RouteScore`, `RoutingDecision` 데이터 클래스
  - `MODEL_PROFILES` — 사장님 정의 그대로 코드화한 5개 모델 카드
  - `route(task)` — 작업 설명 → 1순위/후순위 결정
  - `write_routing_decision(task)` — 08_reports에 보고서 + JSON 핸드오프 저장
  - 같은 초 내 다중 호출 시 파일 덮어쓰기 방지 (suffix _01, _02 …)
  - 키워드가 안 잡히는 모호한 요청은 Claude 기본 라우팅(폴백)
- `ai_company/main.py`
  - `model-router --task "..."` CLI 명령 추가
- `docs/MODEL_ROUTER.md` (신규)
  - 아키텍처 다이어그램, 모델 매핑표, 사용법, 안전 규칙, 확장 포인트
- `tests/test_smoke.py`
  - `test_model_router_routes_to_correct_panel` — 5개 모델 라우트 검증
  - `test_model_router_fallback_for_unknown_task` — Claude 폴백 검증
  - `test_model_router_writes_collision_safe_files` — 동일 초 다중 호출 검증

## 3. 테스트 결과

CLI를 통해 6건의 실제 라우팅 결정을 생성, `08_reports/`에 저장됨.

| 입력 작업 | 1순위 모델 | 점수 | 보고서 |
|---|---|---|---|
| 고스틱 광고 릴스 썸네일 시안 만들어줘 | 이미지 AI | 8 | model_router_decision_20260510_181639.md |
| 고양이 MBTI 앱 경쟁 서비스 트렌드 조사 | Gemini | 8 | model_router_decision_20260510_181644.md |
| FastAPI 백엔드 코드 자동화 스크립트 작성 | Codex / ChatGPT | 10 | model_router_decision_20260510_181645.md |
| 스마트스토어 상세페이지 문구 검수 | Claude | 7 | model_router_decision_20260510_181822.md |
| 트렌드 리서치 | Gemini | 7 | model_router_decision_20260510_181757.md |
| FastAPI 코드 자동화 | Codex / ChatGPT | 7 | model_router_decision_20260510_181756.md |

Ollama 라우팅("최근 리뷰 200건을 긍정/부정으로 분류하고 태그")은
점수 트레이스로 검증.

- 키워드 일치: "분류" (+3), "태그" (+3) = 6점
- 강점 토큰: "리뷰" (+1) = 1점
- 합계 7점, 타 모델은 0점 → Ollama 1순위 확정

5개 모델 패널 모두 정상 라우팅됨.

## 4. 사장님 확인 필요한 부분

- 모델별 키워드 사전이 사장님 실제 업무 어휘와 맞는지 확인 필요.
  - 부족한 키워드 알려주시면 `MODEL_PROFILES`에 추가합니다.
- 폴백 모델을 Claude로 잡았는데, ChatGPT가 더 익숙하시면 바꿀 수 있습니다.
- Hermes/AgentAU/n8n 연동은 다음 단계. 라우터 출력 JSON이 n8n
  webhook payload와 호환됩니다 (`integrations.py` 참고).

## 5. 다음 추천 작업

- AI 회의 시스템과 라우터 연결: 라우터 결과 JSON을 `meeting.py`로 입력
- 사장님 어휘 사전 확장: 자주 쓰는 명령 예시 모아서 키워드 보강
- 시뮬레이터 표시: AI 사무실 시뮬레이터 상태판에 라우팅 결정 카드 추가
- 다중 라우팅: 1순위와 후순위 점수가 근접하면 양쪽 모두에 핸드오프
- 텔레그램 명령 흐름: 사장님 텔레그램 입력 → Hermes → 모델 라우터 →
  결과 보고 흐름의 end-to-end dry-run

## 안전 확인

- 실제 API 호출 / 외부 발송 / 결제 / 입찰 변경 / SNS 업로드 — 없음
- API 키 / 비밀번호 / 쿠키 / .env 노출 — 없음
- D:\AI_COMPANY 밖의 파일 수정 — 없음
- 모든 결과는 dry-run 보고서 + JSON 핸드오프 형식으로만 저장
