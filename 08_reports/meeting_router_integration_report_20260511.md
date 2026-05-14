# 라우터-회의 통합 보고서

## 1. 수행한 일

모델 라우터 단계를 AI 회의 시스템에 연결했다. 이제 회의 실행 시 모델
라우터를 통과시키면 회의록 머리에 라우팅 결정 카드가 첨부되고, CEO AI
결론에 "실행 단계는 [1순위 모델]에게 1차 위임한다" 문장이 자동 추가된다.

```
사장님 → CEO 오케스트레이터 → 모델 라우터 → AI 회의 ← (이번에 연결됨)
   → 실행 준비 → 사장님 승인
```

## 2. 생성/수정한 파일

- `ai_company/meeting.py` (수정)
  - `MeetingResult.routing: Optional[RoutingDecision]` 필드 추가
  - `run_meeting(topic, routing=None)` — 라우터 결정을 받아 회의 실행
  - `run_routed_meeting(topic)` — 라우터 자동 통과 편의 함수
  - `_build_ceo_decision(topic, routing)` — CEO 결론에 위임 문장 추가
  - `meeting_to_markdown()` — 회의록에 "## 모델 라우터 결정" 섹션 추가
- `ai_company/main.py` (수정)
  - `meeting --with-router` 플래그 추가
  - `run_routed_meeting` import
- `tests/test_smoke.py` (수정)
  - `test_routed_meeting_includes_routing_card` 추가
  - `test_meeting_without_router_keeps_old_behavior` 추가

## 3. 사용 방법

```powershell
# 기존 회의 (라우터 미통과)
python -m ai_company.main meeting --topic "고스틱 광고 효율 개선"

# 라우터 통합 회의
python -m ai_company.main meeting --topic "스마트스토어 상세페이지 문구 검수" --with-router
```

`--with-router` 사용 시 회의록 머리에 다음과 같은 카드가 자동 첨부된다.

```markdown
## 모델 라우터 결정
- 1순위 모델: **Claude** (긴 문서, 고급 코딩, 기획서, 검토)
- 1순위 점수: 7
- 후순위: 이미지 AI (Stable Diffusion / Canva / PIL)
- dry-run: True / executed: False
```

그리고 CEO 결론에 다음 문장이 추가된다.

> "6) 실행 단계는 모델 라우터 결정에 따라 Claude(긴 문서, 고급 코딩,
> 기획서, 검토)에게 1차 위임한다."

## 4. 호환성

- `--with-router` 없이 호출하면 기존 동작 그대로 (라우팅 섹션 없음)
- `MeetingResult.routing`은 `Optional`이라 기존 코드는 영향받지 않음
- 시뮬레이터, 승인 파일, 회의 보고서 흐름은 변경 없음

## 5. 테스트

추가된 pytest 케이스 (Windows 본체에서 `python -m pytest tests/test_smoke.py -k "routed_meeting or meeting_without_router"` 로 실행 가능):

- `test_routed_meeting_includes_routing_card` — 라우팅 결정이 회의록과
  CEO 결론에 포함되는지 검증
- `test_meeting_without_router_keeps_old_behavior` — 라우터 없이는
  라우팅 섹션이 안 들어가는지 검증

샌드박스 파일시스템 캐시 문제로 이 환경에서는 자동 실행이 불안정해
Windows 본체 검증 권장.

## 6. 사장님 확인 필요한 부분

- `--with-router`를 회의 기본값으로 만들지(즉 항상 라우터 통과) 옵션 유지할지
- 라우팅 카드에 후순위 후보 점수까지 표시할지, 1순위만 표시할지
- AI 회의 → 실행 준비 단계로 넘길 때 라우팅 정보 그대로 전달하는 방식

## 7. 다음 추천 작업

- 실행 준비(`marketing.py`, `image_templates.py` 등)도 라우팅 정보 받기
- AI 사무실 시뮬레이터 상태판에 라우팅 결정 카드 표시
- 텔레그램 명령 흐름: 사장님 입력 → 라우터 → 회의 → 승인 end-to-end dry-run

## 안전 확인

- 실제 API 호출 / 외부 발송 / 결제 / 입찰 변경 — 없음
- 모든 처리는 D:\AI_COMPANY 내부의 dry-run 보고서로만 저장
- 라우팅 결정은 dry_run=True / executed=False 로만 마킹
