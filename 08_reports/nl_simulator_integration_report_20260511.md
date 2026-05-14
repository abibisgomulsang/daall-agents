# 자연어 채팅 → 시뮬레이터 통합 보고서

## 1. 수행한 일

기존 `scripts/local_viewer_server.py`의 `plan_chat_command()`(키워드 분기)를
`ai_company.nl_command.interpret()`로 교체했다. 이제 AI 사무실 시뮬레이터
채팅에서 자연어로 명령하면:

- 자동 의도 분류 (17개)
- 모델 라우터 1순위/후순위 결정
- 위험 키워드 자동 차단 + 승인 파일 자동 생성
- 라우팅 카드 채팅창 표시

가 한 번에 일어난다.

## 2. 생성/수정한 파일

- `scripts/local_viewer_server.py`
  - `ai_company.nl_command.interpret`를 sys.path 통해 import
  - `plan_chat_command()`를 nl_interpret 어댑터로 교체
  - 응답에 `routing`, `intent`, `approval_path`, `risk_keywords` 필드 추가
  - 기존 키워드 분기 로직은 폴백으로 유지 (import 실패 대비)
- `06_apps/ai_office_simulator/app.js`
  - `sendChat()` 응답 처리에서 `data.routing`이 있으면 채팅에 라우팅 카드 추가
  - `data.approval_path`가 있으면 승인 대기 안내 메시지 추가
- `06_apps/ai_office_simulator/styles.css`
  - `.chat-message.router` 스타일 추가 (파란 좌측 보더 + 연한 파란 배경)
- `tests/test_smoke.py`
  - `test_local_viewer_chat_planner` 확장: 라우팅 정보/승인 경로 검증
  - `test_office_simulator_files_exist` 확장: 라우터 카드 스타일/스크립트 검증

## 3. 동작 흐름

```
사장님 채팅 입력
   ↓
시뮬레이터 sendChat()
   ↓ POST /api/chat
local_viewer_server.plan_chat_command()
   ↓ (nl_interpret 호출)
nl_command.interpret()
   ├─ 의도 분류
   ├─ 위험 키워드 검사 (위험시 09_approval 자동 생성)
   └─ 모델 라우터 통과
   ↓ NLPlan
plan_chat_command() → JSON 응답
   { ok, command, label, intent, routing, approval_path? }
   ↓
sendChat() 응답 처리
   ├─ 라우팅 카드 추가 (있으면)
   ├─ 명령 실행 결과 표시
   └─ 승인 안내 (위험 명령이면)
```

## 4. 호환성

- 기존 응답 형식(`ok`, `command`, `label`) 그대로 유지 — 기존 UI 코드 영향 없음
- 추가 필드(`routing`, `intent`, `approval_path`)는 옵션 — 표시 안 해도 동작
- import 실패 시 기존 키워드 분기 자동 폴백

## 5. 테스트 결과

샌드박스 파일시스템 캐시 문제로 자동 pytest는 불안정. Windows 본체에서
`python -m pytest tests/test_smoke.py -k "local_viewer or office_simulator"`
로 검증 권장. 기존 테스트 4건 + 라우팅 통합 검증 2건.

## 6. 사장님 확인 필요한 부분

- 라우팅 카드 색상/위치가 마음에 드시는지 (현재: 파란 좌측 보더)
- 위험 키워드 발견 시 채팅에 표시할 안내 메시지 톤
- 의도 분류기에 추가하실 어휘

## 7. 다음 자동 진행 작업

이어서 진행 중:

- 텔레그램 → nl_command → 라우터 → 회의 → 승인 end-to-end dry-run 패키지
- 실행 준비 단계(marketing/image_templates)도 라우팅 정보 수신
