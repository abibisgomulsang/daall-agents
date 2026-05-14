# Telegram / n8n / Ollama Dry-run 연결 계획

## 원칙

- 실제 메시지 발송, webhook 호출, 설치, 모델 다운로드는 사장님 승인 후 진행한다.
- 토큰, webhook URL, chat_id 값은 화면에 출력하지 않는다.
- 먼저 로컬 보고서와 승인 대기 파일을 생성한다.

## 1. Telegram Bot

목표:
- 사장님이 텔레그램으로 명령을 보내면 AI 회사가 업무를 접수한다.
- 결과는 `08_reports`와 `09_approval`에 저장한다.

필요 설정:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Dry-run 단계:
1. `.env`에 값 존재 여부만 확인한다.
2. 실제 발송 대신 `08_reports/telegram_dry_run_*.md`를 만든다.
3. 실제 발송 전 `09_approval/APPROVAL_REQUIRED_integration_telegram_bot_*.md` 승인을 확인한다.

## 2. n8n Webhook

목표:
- 반복 업무를 n8n webhook으로 받아 Python CLI를 호출할 준비를 한다.

필요 설정:
- `N8N_WEBHOOK_URL` 또는 로컬 n8n 실행 환경
- Docker 또는 n8n CLI

Dry-run 단계:
1. webhook URL 존재 여부만 확인한다.
2. 실제 POST 호출 없이 workflow 설계 문서를 만든다.
3. 실제 webhook 호출 전 승인 파일을 만든다.

## 3. Ollama

목표:
- 로컬 모델을 이용해 회의/마케팅/검수 초안을 보조한다.

필요 설정:
- Ollama 설치
- 사용할 모델명 확정

Dry-run 단계:
1. `ollama` 명령 존재 여부만 확인한다.
2. 설치되어 있으면 모델 목록 조회 전 승인 파일을 만든다.
3. 미설치면 설치 승인 파일을 만든다.
4. 모델 목록 조회는 `ollama-model-list-dry-run` 산출물 승인 후 읽기 전용으로만 진행한다.

## 현재 CLI

```powershell
python -m ai_company.main integration-status
python -m ai_company.main integration-approvals
python -m ai_company.main ollama-model-list-dry-run
```

## 금지

- 승인 전 텔레그램 실제 메시지 발송
- 승인 전 n8n webhook 실제 호출
- 승인 전 Ollama 설치 또는 모델 다운로드
- 승인 전 Ollama 모델 목록 실제 조회
- 토큰, webhook URL, chat_id 값 출력
