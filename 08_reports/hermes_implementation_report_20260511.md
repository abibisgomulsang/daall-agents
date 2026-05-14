# Hermes AI 실연결 보고서

## 1. 한 줄 요약

사장님이 **텔레그램에 "고스틱 광고 만들어줘"** 라고 한 마디 보내면:
1) 사장님 PC의 Hermes 봇이 받아서
2) 위험 키워드 검사 + rate limit 통과 후
3) `nl_command` 자동 분류 + CLI 자동 실행
4) 결과를 텔레그램으로 다시 보내드리고
5) 가상 사무실 페이지에는 "🔔 사장님 텔레그램: …" 활동 로그가 30초 안에 자동 표시됩니다.

`boss-command`의 1단계 Hermes는 더 이상 mock이 아닙니다.

## 2. 신규 모듈

| 파일 | 역할 |
|---|---|
| `ai_company/hermes_memory.py` | inbox/outbox JSONL + 선호 학습 + rate limit 카운터 |
| `ai_company/hermes_runtime.py` | 텔레그램 long-poll 봇 + 명령 안전 처리 + 회신 |
| `scripts/start_hermes.ps1` | 백그라운드/포그라운드 실행 (12_logs에 pid·로그) |
| `docs/HERMES.md` | 사장님 시점 가이드 |

## 3. 수정 모듈

- `ai_company/boss_pipeline.py` — 1단계 `_hermes_step()`이 진짜 메모리에 기록·선호 학습
- `ai_company/main.py` — `hermes-status`, `hermes-run`, `hermes-test` CLI
- `scripts/local_viewer_server.py` — `/api/hermes/status`, `/api/hermes/recent` 추가
- `06_apps/virtual_office/index.html` — Hermes 배지 추가
- `06_apps/virtual_office/app.js` — inbox 30초 폴링, 새 메시지 활동 로그 자동 표시
- `tests/test_smoke.py` — 4건 추가 (메모리/rate/위험 차단/안전 실행)

## 4. 안전 가드 다층 구조

| 가드 | 동작 |
|---|---|
| Owner 검사 | `TELEGRAM_OWNER_CHAT_ID` 일치 메시지만 처리. 그 외는 inbox에 `ignored_non_owner` 마킹만 |
| 위험 키워드 자동 차단 | 입찰가/광고비/업로드/결제/로그인/발송 등 → 자동 실행 X, 09_approval 자동 생성 + "승인 필요" 회신 |
| 분당 rate limit | 기본 12회 (환경변수 `HERMES_PER_MINUTE`로 조정) |
| 일일 rate limit | 기본 60회 (환경변수 `HERMES_PER_DAY`로 조정) |
| 외부 채널 자동 반영 | 끝까지 없음 — Hermes는 AI 회사 CLI만 호출 |
| 키/토큰 노출 | 어디에도 출력 안 됨 (`hermes-status`, 로그, 보고서 전부 "있음/없음"만) |

## 5. 사장님이 할 일 (5분)

1. `.env`에 두 줄 채우기:
   ```
   TELEGRAM_BOT_TOKEN=123456:ABC...
   TELEGRAM_OWNER_CHAT_ID=987654321
   ```
2. 자격 확인:
   ```powershell
   cd D:\AI_COMPANY
   .\.venv\Scripts\Activate.ps1
   python -m ai_company.main hermes-status
   ```
3. 봇 실행:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\start_hermes.ps1
   ```
4. 텔레그램에서 봇한테 메시지 보내기. 가상 사무실 페이지를 켜두면 활동 로그에 실시간 표시.

## 6. 로컬 모의 테스트 (토큰 없이도 동작)

```powershell
# 안전 명령 — 자동 실행 시도
python -m ai_company.main hermes-test --message "고스틱 광고 만들어줘"

# 위험 명령 — 차단 + 09_approval 생성 확인
python -m ai_company.main hermes-test --message "네이버광고 입찰가 200원 올려줘"
```

콘솔에서 Hermes 응답 미리 확인 가능. 텔레그램 실제 발송은 안 합니다.

## 7. 가상 사무실 변화

- 상단 strip 배지: `⚪ Hermes 미연결` → 자격 채우면 `🟢 Hermes 연결됨`
- 활동 로그: 사장님 텔레그램 보낼 때마다 `🔔 사장님 텔레그램: …` 자동 추가 (30초 안에)
- 페이지 다시 열어도 이전 inbox는 다시 표시되지 않음 (이미 본 메시지는 localStorage `seen` 목록으로 중복 방지)

## 8. boss-command 1단계 강화

기존엔 mock 텍스트만 출력했던 Hermes 단계가:

```
1. Hermes AI 인바운드
   - 메모리: 선호 명령 5개 / 최근 결정 3건
   - 텔레그램 자격: 설정됨
   - 메시지 길이: 18자
   - 산출물: D:\AI_COMPANY\11_memory\hermes\inbox.jsonl
```

이렇게 실제 데이터로 채워집니다. boss-command를 한 번씩 돌릴 때마다 사장님 메시지가 inbox에 누적되고 선호도 학습이 진행됩니다.

## 9. 비용

- **봇 자체 비용 0** (텔레그램 API 무료)
- **LLM 호출 비용**은 기존 캡 그대로 적용 (`usage_caps`)
- 분당/일일 rate limit으로 폭주 방지

## 10. 안전 체크리스트

- [x] 봇 토큰·chat_id 값 노출 0
- [x] Owner 외 메시지 자동 무시
- [x] 위험 키워드 자동 차단 + 09_approval
- [x] 분당/일일 자동 처리 한도
- [x] 외부 채널 자동 반영 — 없음
- [x] CLI 자동 실행은 안전 명령에만, 사장님이 직접 실행하시는 흐름과 동일한 안전 가드 통과

## 11. 다음 추천 작업

- `outbox`가 인라인 다이얼로그 형식으로 가상 사무실 "대화록" 탭에 합쳐지면 더 자연스러움
- 정기 알림 — 매일 오전 9시 "어제 결정 N건 / 비용 ₩X" 자동 텔레그램
- Hermes가 직접 `multi-meeting` 결과의 핵심 5문장을 텔레그램에 회신
