# 텔레그램 e2e Dry-run 구축 보고서

## 1. 수행한 일

사장님이 텔레그램에 자연어 명령을 입력했을 때 일어나는 전체 흐름을
단일 dry-run 보고서로 묶는 `e2e_dry_run` 모듈을 추가했다.

```
텔레그램 인바운드 (mock)
   ↓ Hermes 기억 조회 (mock)
   ↓ nl_command.interpret (의도 + 위험 + 라우터)
   ↓ 모델 라우터 결정 (1순위/후순위)
   ↓ AI 회의 (의도가 회의 계열일 때)
   ↓ 승인 파일 자동 생성 (위험 명령일 때) / 자동 실행 가능 단계
   ↓ 사장님 알림 mock
```

모든 단계는 **실제 텔레그램 API 호출/외부 발송 없이** 보고서로만 남는다.

## 2. 생성/수정한 파일

- `ai_company/e2e_dry_run.py` (신규, 약 240줄)
  - `E2EStep`, `E2EReport` 데이터 클래스
  - `_mock_telegram_inbound()` — 텔레그램 webhook payload mock
  - `_mock_hermes_lookup()` — Hermes 기억 조회 mock
  - `_build_boss_notification()` — 사장님 알림 문구 (실제 발송 안 함)
  - `build_e2e_report()` — 전 흐름을 E2EReport로 반환
  - `write_e2e_report()` — 08_reports에 md+json 저장 (충돌 방지)
- `ai_company/main.py` — `e2e-dry-run --message "..."` CLI 추가
- `tests/test_smoke.py` — 3건 추가
  - `test_e2e_dry_run_flow_safe_message` — 안전 명령 전 흐름
  - `test_e2e_dry_run_flow_risky_message` — 위험 명령 차단 + 승인 단계
  - `test_e2e_dry_run_writes_files` — md/json 파일 생성 검증

## 3. 사용 예시

```powershell
# 안전 명령 — 전 흐름 가시화
python -m ai_company.main e2e-dry-run --message "고스틱 광고 효율 회의해줘"

# 위험 명령 — 승인 단계까지 자동 포함
python -m ai_company.main e2e-dry-run --message "네이버광고 입찰가 200원 올려줘"
```

출력 보고서 구조:

```markdown
# 텔레그램 e2e dry-run 보고서
- 인바운드 메시지
- 분류 의도 + 실행 가능 여부
- 라우터 1순위/점수

## 단계 로그
1. 텔레그램 인바운드 수신 (mock)
2. Hermes 기억 조회 (mock)
3. nl_command.interpret() 호출
4. 모델 라우터 결정
5. AI 회의 (회의 의도일 때만)
6. 승인 파일 자동 생성 또는 자동 실행 가능 단계
7. 사장님 알림 mock

## 사장님 알림 (mock)
실제 발송 없는 알림 문구

## 안전 확인
- 실제 텔레그램 API 호출 여부: 호출 안 함
- 실제 외부 발송/업로드/결제 여부: 없음
```

## 4. 다음 단계 (이어서 진행)

- 실행 준비 단계(marketing/image_templates)도 라우팅 정보 수신하도록 확장

## 안전 확인

- 실제 텔레그램 봇 토큰 사용: 없음
- 실제 webhook 호출: 없음
- 실제 외부 발송/업로드: 없음
- D:\AI_COMPANY 밖 파일 수정: 없음
- API 키/비밀번호 노출: 없음
