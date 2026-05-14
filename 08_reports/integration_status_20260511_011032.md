# 외부 연동 준비 상태

| 연동 | 상태 | 안전 확인 | 다음 단계 | 승인 필요 |
| --- | --- | --- | --- | --- |
| Telegram Bot | not_configured | 토큰/채팅 ID 존재 여부만 확인했습니다. 값은 출력하지 않았습니다. | 토큰과 chat_id가 준비되면 dry-run 메시지 파일을 먼저 생성합니다. | 필요 |
| n8n Webhook | not_configured | n8n 명령: 없음, Docker: 없음, webhook URL: 없음 | webhook URL 또는 n8n 설치 방식 확정 후 dry-run workflow를 연결합니다. | 필요 |
| Ollama | not_installed | Ollama 명령: 없음, Node: 있음, npm: 있음 | 설치되어 있으면 모델 목록만 조회하고, 미설치면 설치 승인 파일을 만듭니다. | 필요 |

## 안전 원칙

- 토큰, chat_id, webhook URL 값은 출력하지 않습니다.
- 실제 메시지 발송, 외부 webhook 호출, 모델 설치는 사장님 승인 후 진행합니다.
- 현재 단계는 로컬 dry-run 준비 상태 점검입니다.