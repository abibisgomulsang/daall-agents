# 안전 규칙 개정 및 1차 MVP 재검증 보고서

## 1. 목적

`D:\AI_COMPANY` 안의 일반 개발 작업은 자동 진행하고, 외부 서비스 실제 실행만 사장님 승인 대상으로 유지하도록 운영 문서를 개정했다.

## 2. 문서 개정 요약

### 자동 진행 허용

- `D:\AI_COMPANY` 안의 파일 읽기, 생성, 수정
- 폴더 생성
- `git init`, `git status`, `git add`, `git commit`
- `python -m venv .venv`
- `pip install -r requirements.txt`
- `pytest`, `python -m pytest`
- `python -m ai_company.main ...`
- `requirements.txt` 수정
- `ai_company` 내부 코드 수정
- `docs` 문서 작성
- `08_reports`, `09_approval`, `10_meetings` 산출물 생성

### 승인 필요 유지

- 스마트스토어 실제 로그인/수정/업로드
- 네이버광고 실제 입찰가/광고비 변경
- SNS 실제 업로드/게시
- 고객 메시지 발송
- 결제/주문/환불
- `D:\AI_COMPANY` 밖의 파일 수정
- `.env` 내용 출력 또는 요약
- API 키, 비밀번호, 쿠키, 토큰 표시
- 대량 삭제
- 시스템 설정 변경

## 3. 환경 확인

- `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`
- 결과: 모든 패키지 이미 설치됨

## 4. 1차 MVP 재실행 결과

### AI 회의

- 명령: `python -m ai_company.main meeting --topic "고스틱 광고 효율 개선"`
- 결과: 성공
- 저장:
  - `10_meetings/ai_meeting_20260511_005855.md`
  - `08_reports/ai_meeting_report_20260511_005855.md`
  - `09_approval/APPROVAL_REQUIRED_meeting_actions_20260511_005855.md`

### 광고 패키지

- 명령: `python -m ai_company.main ad --product GOSTICK01`
- 결과: 성공
- 저장:
  - `08_reports/ad_package_GOSTICK01_20260511_005859.md`
  - `09_approval/APPROVAL_REQUIRED_ad_GOSTICK01_20260511_005859.md`

### 네이버광고 분석

- 명령: `python -m ai_company.main analyze-ads --csv data\naver_ads_sample.csv`
- 결과: 성공
- 저장:
  - `05_naver_ads/naver_ads_report_20260511_005903.md`
  - `08_reports/naver_ads_report_20260511_005903.md`
  - `09_approval/APPROVAL_REQUIRED_naver_ads_actions_20260511_005903.md`

### 실행 전 dry-run 계획

- 명령: `python -m ai_company.main execution-plan --approval APPROVAL_REQUIRED_naver_ads_actions_20260511_005903.md`
- 결과: 성공
- 저장:
  - `08_reports/execution_plan_naver_ads_actions_20260511_005903_20260511_005915.md`

## 5. 테스트 결과

- 명령: `.\.venv\Scripts\python.exe -m pytest`
- 결과: 6 passed

## 6. 안전 확인

- 외부 서비스 로그인 없음
- 스마트스토어/SNS/네이버광고 실제 변경 없음
- 결제/주문/환불 없음
- `.env` 내용 출력 없음
- API 키/비밀번호/쿠키/토큰 출력 없음
