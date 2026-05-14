# 외부 연동 Dry-run 생성기 및 이미지 템플릿 보고서

## 1. 수행 목적

설치나 외부 호출 없이 다음 단계 작업을 준비했다.

- Telegram 메시지 dry-run 생성기
- n8n webhook payload 샘플 생성기
- Ollama 프롬프트 dry-run 생성기
- 고스틱 이미지 광고 템플릿 생성기

## 2. 추가 CLI

### Telegram 메시지 dry-run

```powershell
python -m ai_company.main telegram-dry-run --message "오늘 AI 회사 MVP 점검 완료 보고 예정"
```

생성:

```txt
08_reports/telegram_dry_run_20260511_011315.md
```

실제 텔레그램 메시지는 발송하지 않았다.

### n8n payload 샘플

```powershell
python -m ai_company.main n8n-payload --task "고스틱 광고 효율 개선 회의 후 승인 파일 생성"
```

생성:

```txt
08_reports/n8n_payload_sample_20260511_011315.json
```

실제 webhook은 호출하지 않았다.

### Ollama dry-run

```powershell
python -m ai_company.main ollama-dry-run --prompt "고스틱 광고 효율 개선을 위한 AI 회의 요약을 작성해줘"
```

생성:

```txt
08_reports/ollama_dry_run_20260511_011315.md
```

실제 모델 호출이나 다운로드는 하지 않았다.

### 이미지 광고 템플릿

```powershell
python -m ai_company.main image-templates --product GOSTICK01
```

생성:

```txt
08_reports/image_templates_GOSTICK01_20260511_011315.md
03_images/templates/image_templates_GOSTICK01_20260511_011315.json
```

## 3. 템플릿 구성

- 1:1 피드
- 4:5 세로 피드
- 9:16 릴스 커버

## 4. 테스트 결과

- `.\.venv\Scripts\python.exe -m pytest`
- 결과: 10 passed
- `node --check 06_apps\ai_office_simulator\app.js`
- 결과: 성공

## 5. 안전 확인

- Telegram 실제 발송 없음
- n8n webhook 실제 호출 없음
- Ollama 모델 호출/다운로드 없음
- 이미지 실제 생성/업로드 없음
- 토큰, webhook URL, chat_id 출력 없음
