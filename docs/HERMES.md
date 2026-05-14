# Hermes AI — 사장님 텔레그램 비서

## 전체 흐름

```
[사장님 텔레그램]
   ↓ 메시지
[Hermes 봇 (사장님 PC, long-poll)]
   ↓ owner_chat_id 검사 (사장님 본인만)
   ↓ inbox.jsonl 기록 + 선호 학습
   ↓ rate limit (분 12회 / 일 60회)
   ↓ nl_command 해석 (위험 키워드 자동 차단)
   ├─ 안전 → CLI 자동 실행 → 결과 텔레그램 회신
   └─ 위험 → 09_approval 자동 생성 → "승인 필요" 회신
   ↓
[가상 사무실 페이지]
   └─ 30초마다 /api/hermes/recent 폴링 → 활동 로그에 실시간 표시
```

## 사장님이 해주실 일

`.env`에 두 줄 채우기:

```
TELEGRAM_BOT_TOKEN=123456:ABC...   # BotFather에서 발급
TELEGRAM_OWNER_CHAT_ID=987654321   # @userinfobot 로 본인 chat_id 확인
```

확인:

```powershell
cd D:\AI_COMPANY
.\.venv\Scripts\Activate.ps1
python -m ai_company.main hermes-status
```

`자격: [OK]` 가 보이면 봇 띄울 준비 완료.

## 봇 실행

### 백그라운드 (권장)

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_hermes.ps1
```

로그: `12_logs/hermes_out.log` , 에러: `12_logs/hermes_err.log` , PID: `12_logs/hermes.pid`

중단:

```powershell
Stop-Process -Id (Get-Content .\12_logs\hermes.pid)
```

### 포그라운드 (디버그)

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_hermes.ps1 -Foreground
```

Ctrl+C로 종료.

### 자동 실행 끄기

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_hermes.ps1 -NoAutoExecute
```

이 모드는 "준비만" — Hermes가 의도는 분석하고 텔레그램으로 답장하지만 실제 CLI는 실행 안 함. 사장님이 텔레그램 회신을 보고 직접 명령.

## 로컬 모의 테스트 (텔레그램 없이)

```powershell
python -m ai_company.main hermes-test --message "고스틱 광고 만들어줘"
```

봇 토큰 없이도 동작. inbox 기록 + 의도 분석 + 자동 실행 결과를 콘솔에 표시. **실제 텔레그램 발송은 안 함.**

## 자동 실행 안전 가드 (다층)

1. **Owner 검사** — `TELEGRAM_OWNER_CHAT_ID`와 일치하는 메시지만 처리. 그 외는 inbox에 "ignored_non_owner" 표시만 남기고 무시
2. **위험 키워드 자동 차단** — `입찰가 / 광고비 / 업로드 / 결제 / 환불 / 로그인 / 발송 / 게시 / 비밀번호` 등 15개 → 자동 실행 X, 09_approval 자동 생성 + 텔레그램 승인 요청
3. **분당/일일 rate limit** — 기본 분당 12회 / 일일 60회. 초과 시 자동 차단 + "사장님 직접 실행" 안내
4. **외부 채널 자동 반영 없음** — Hermes는 AI 회사 CLI만 호출. 스마트스토어/네이버광고/SNS 직접 호출 X
5. **API 키 / 토큰 노출 없음** — `hermes-status`, 로그, 보고서 어디에도 값 안 찍힘

## 메모리 (사장님 선호 학습)

`11_memory/hermes/` 폴더에 다음 파일이 누적됩니다:

| 파일 | 내용 |
|---|---|
| `inbox.jsonl` | 사장님 텔레그램 메시지 (시각/길이/text) |
| `outbox.jsonl` | Hermes 응답 요약 (송신 성공/실패) |
| `preferences.json` | 자주 쓰는 명령 패턴 상위 15개 |
| `recent_decisions.jsonl` | 자동 실행/차단 결정 누적 |
| `rate.json` | 분당/일일 카운터 |

`boss-command` 7단계 흐름의 **1단계 Hermes 인바운드**도 이 메모리를 읽어 "선호 명령 N개 / 최근 결정 N건"을 보고서에 명시합니다.

## 가상 사무실에서의 표시

브라우저로 가상 사무실을 열면:

- 상단 strip: `🟢 Hermes 연결됨` 또는 `⚪ Hermes 미연결` 배지
- 활동 로그: 사장님이 텔레그램에 보낼 때마다 `🔔 사장님 텔레그램: ...` 실시간 표시 (30초 폴링)
- 현재 페어: `수영 ← 사장님 (텔레그램)` 으로 자연스럽게 전환

## 상태 점검 CLI

```powershell
python -m ai_company.main hermes-status      # 자격 + 메모리 + rate 현황
python -m ai_company.main hermes-test --message "..."   # 로컬 모의 처리
```

## 트러블슈팅

| 증상 | 해결 |
|---|---|
| `자격: [--]` | `.env` 확인 — `TELEGRAM_BOT_TOKEN`, `TELEGRAM_OWNER_CHAT_ID` 띄어쓰기/따옴표 없이 채웠는지 |
| 텔레그램에 응답이 안 옴 | 봇 프로세스 살아있는지: `Get-Content .\12_logs\hermes.pid` → `Get-Process -Id ...` |
| 다른 사람이 봇에 말을 거는데 답 안 함 | 정상 — owner_chat_id 외엔 모두 무시 |
| 봇이 명령을 너무 자주 실행함 | `--no-auto-execute` 옵션 + `HERMES_PER_MINUTE` / `HERMES_PER_DAY` 환경변수로 조정 |
