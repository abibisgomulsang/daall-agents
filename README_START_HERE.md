# 아비비 AI 회사 - Codex 로컬 실행 시작 문서

이 패키지는 Codex가 사장님 컴퓨터의 전용 작업공간에서 AI 회사를 구축하도록 만든 시작 세트입니다.

## 핵심 목표

사장님은 결과만 확인하고, Codex/AI 에이전트들이 다음 업무를 진행합니다.

- AI 회의 및 토론
- 마케팅 전략 생성
- SNS 광고 문구 생성
- 이미지 광고 제작 지시서 생성
- 앱 개발
- 스마트스토어 운영 분석
- 네이버광고 효율 분석
- 업무 결과 보고서 생성

## 안전 원칙

Codex에게 처음부터 전체 컴퓨터 권한을 주지 마세요.

권장 작업공간:

```powershell
D:\AI_COMPANY
```

Codex는 이 폴더 안에서만 작업하게 시작합니다.

## 1. 압축 풀 위치

이 ZIP 파일 내용을 아래 폴더에 풀어주세요.

```powershell
D:\AI_COMPANY
```

## 2. PowerShell에서 폴더로 이동

```powershell
cd D:\AI_COMPANY
```

## 3. 기본 폴더/환경 점검

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1
```

Codex CLI까지 설치하려면 Node.js가 설치된 상태에서:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1 -InstallCodex
```

## 4. Codex 시작

```powershell
codex --cd D:\AI_COMPANY --ask-for-approval on-request
```

## 5. Codex에 붙여넣을 첫 명령

아래 파일 내용을 Codex에 그대로 붙여넣으세요.

```txt
CODEX_FIRST_PROMPT.md
```

## 6. API 키/토큰

`.env.example`을 복사해서 `.env`를 만들되, 실제 키는 절대 Git에 올리지 마세요.

```powershell
copy .env.example .env
```

## 7. 첫 테스트

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m ai_company.main meeting --topic "고스틱 광고 효율 개선"
python -m ai_company.main ad --product GOSTICK01
python -m ai_company.main analyze-ads --csv data\naver_ads_sample.csv
```

## 다음 목표

첫 번째 MVP는 아래 3개입니다.

1. AI 회의 시스템
2. 고스틱 광고 생성 시스템
3. 스마트스토어/네이버광고 분석 시스템

## 시각화 화면 열기

앱 브라우저에서 `file://` 주소가 안 열리면 로컬 서버로 확인합니다.

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
