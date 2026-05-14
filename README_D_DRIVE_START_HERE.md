# D드라이브 설치 전용 시작 문서

이 버전은 `D:\AI_COMPANY` 기준으로 맞춘 AI 회사 구축 패키지입니다.

## 1. 압축 풀 위치

아래 위치에 압축을 풀어주세요.

```powershell
D:\AI_COMPANY
```

압축을 풀었을 때 바로 아래 파일이 보여야 합니다.

```txt
D:\AI_COMPANY\AGENTS.md
D:\AI_COMPANY\CODEX_FIRST_PROMPT.md
D:\AI_COMPANY\PROJECT_MASTER_PLAN.md
D:\AI_COMPANY\TASK_BOARD.md
D:\AI_COMPANY\ai_company
D:\AI_COMPANY\scripts
D:\AI_COMPANY\data
```

## 2. PowerShell 실행

```powershell
cd D:\AI_COMPANY
```

## 3. 기본 세팅

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1
```

## 4. Python 테스트

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m ai_company.main meeting --topic "고스틱 광고 효율 개선"
python -m ai_company.main ad --product GOSTICK01
python -m ai_company.main analyze-ads --csv data\naver_ads_sample.csv
```

## 5. Codex 실행

```powershell
codex --cd D:\AI_COMPANY --ask-for-approval on-request
```

`codex` 명령이 안 잡히면:

```powershell
& "$env:APPDATA\npm\codex.cmd" --cd D:\AI_COMPANY --ask-for-approval on-request
```

## 6. Codex 첫 명령

Codex가 열리면 `CODEX_FIRST_PROMPT.md` 내용을 전부 복사해서 붙여넣으세요.

## 7. 시각화 화면 열기

앱 브라우저에서 `file://` 주소가 안 열리면 로컬 서버를 사용하세요.

```powershell
cd D:\AI_COMPANY
powershell -ExecutionPolicy Bypass -File .\scripts\start_local_viewer.ps1
```

시뮬레이터:

```txt
http://127.0.0.1:8765/06_apps/ai_office_simulator/index.html
```

시뮬레이터 안의 `AI 회사 채팅`에 아래처럼 입력하면 PowerShell 명령 대신 안전한 dry-run 작업을 실행합니다.

```txt
고스틱 광고 회의해줘
고스틱 광고 만들어줘
네이버 광고 분석해줘
대시보드 갱신해줘
```

Dry-run 대시보드:

```txt
http://127.0.0.1:8765/06_apps/dry_run_dashboard/index.html
```
