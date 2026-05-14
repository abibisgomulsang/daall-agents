# 실행계획 CLI 및 AI 사무실 시뮬레이터 구축 보고서

## 1. 수행 목적

승인 대기 파일을 실제 실행 전 dry-run 계획으로 바꾸는 CLI를 추가하고, AI 직원들이 업무중인지 대기중인지 육안으로 볼 수 있는 사무실 시뮬레이터를 만들었다.

## 2. 추가된 CLI

### 실행 전 dry-run 계획 생성

```powershell
python -m ai_company.main execution-plan --approval APPROVAL_REQUIRED_naver_ads_actions_20260511_002118.md
```

생성 파일:

```txt
08_reports/execution_plan_naver_ads_actions_20260511_002118_20260511_004702.md
08_reports/execution_plan_naver_ads_actions_20260511_002118_20260511_005031.md
```

특징:
- 승인 파일을 읽는다.
- 승인 상태를 확인한다.
- 실제 실행은 하지 않는다.
- 네이버광고 승인 파일이면 키워드별 dry-run 조치 후보를 표로 만든다.

### 시뮬레이터 위치 출력

```powershell
python -m ai_company.main office-simulator
```

출력 위치:

```txt
D:\AI_COMPANY\06_apps\ai_office_simulator\index.html
```

## 3. AI 사무실 시뮬레이터

생성 위치:

```txt
06_apps/ai_office_simulator
```

구성:
- `index.html`
- `styles.css`
- `app.js`
- `README.md`

현재 기능:
- CEO, 데이터, 마케팅, SNS, 이미지, 스마트스토어, 네이버광고, 앱개발, 검수 AI 캐릭터 표시
- 캐릭터가 사무실 안에서 이동
- 업무중, 검수, 대기, 막힘 상태 색상 표시
- 업무 큐와 활동 로그 표시
- 시나리오 선택, 속도 조절, 전체 집중 버튼 제공

## 4. 승인 파일 포맷 개선

새로 생성되는 승인 파일은 아래 항목을 포함한다.

- 작업명
- 변경 대상
- 변경 전
- 변경 후
- 예상 효과
- 위험 요소
- 되돌리는 방법
- 승인 필요 여부
- 현재 실행 상태

## 5. 테스트 결과

- `.\.venv\Scripts\python.exe -m pytest`
- 결과: 6 passed
- `node --check 06_apps\ai_office_simulator\app.js`
- 결과: 성공

## 6. 브라우저 검증 메모

Codex 인앱 브라우저가 로컬 `file://` 및 `localhost` 접근을 차단해 화면 캡처 검증은 수행하지 못했다. 대신 정적 파일 존재, JS 문법, HTML 핵심 요소, Python CLI 테스트를 확인했다.

## 7. 다음 작업

- 시뮬레이터를 실제 CLI 작업 로그와 연결
- 승인 기록 기반 최종 체크리스트 추가
- 네이버광고 dry-run 결과를 CSV로도 저장
