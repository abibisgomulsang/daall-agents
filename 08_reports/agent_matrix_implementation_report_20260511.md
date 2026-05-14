# 직원 에이전트 보기 페이지 구축 보고서

## 1. 수행한 일

사장님이 보여주신 Antigravity Connect AI 스크린샷과 동일한 형태로
**직원 에이전트 보기** 페이지를 만들었다.

- 다크 테마 카드 매트릭스
- 필터 칩: 전체 / 활성 / 옵션(오프라인) / 채용 대기
- 상단 메뉴: 시스템 진단 · 리포트 자동화 · 모델 오케스트레이션
- 모달 3종 (로컬 LLM 카탈로그 + 자동 오케스트레이션 포함)

## 2. 생성 파일

`06_apps/agent_matrix/`

- `index.html` — 메인 페이지 (브라우저로 직접 열기 가능)
- `styles.css` — 스크린샷 톤에 맞춘 다크 테마
- `agents_data.js` — 10명의 에이전트 + 5개 모델 + 자동 매핑 데이터
- `app.js` — 필터/모달/모델 저장 로직

추가 수정:

- `06_apps/ai_office_simulator/index.html` — "직원 에이전트 보기" 링크 추가
- `tests/test_smoke.py` — 매트릭스 파일/필수 키 검증 테스트 추가
- `TASK_BOARD.md` — 항목 갱신

## 3. 등록된 에이전트 10명

| 키 | 이름 | 역할 | 상태 |
|---|---|---|---|
| ceo | CEO | Chief Executive Agent | 활성 |
| marketing | 마케팅 | Marketing Lead | 활성 |
| sns | SNS | Head of SNS · 릴스 · 인스타 | 활성 |
| image | 이미지 | Lead Designer | 활성 |
| smartstore | 스마트스토어 | Marketplace Manager | 활성 |
| naverads | 네이버광고 | Ads Performance Lead | 오프라인 |
| developer | Developer | Lead Engineer | 오프라인 |
| data | 데이터 | Data Analyst | 오프라인 |
| review | 검수 | Compliance & QA | 활성 |
| researcher | 리서처 | Trend & Data Researcher | 채용 대기 |

상태 분포는 사장님 화면처럼 "5 / 10 ONLINE" 박스에 자동 표시.

## 4. 모델 오케스트레이션 (사장님 두 번째 스크린샷)

- 머신 자동 감지 (Platform · CPU 코어 · RAM 추정 · 화면 · UA)
- 에이전트별 모델 드롭다운: Codex / Claude / Gemini / Ollama / 이미지 AI
- **자동 오케스트레이션** 버튼 — `ai_company/model_router.py` 매핑과 정합:
  - CEO → Claude / 마케팅 → Codex / SNS → Ollama / 이미지 → 이미지 AI /
    스마트스토어 → Ollama / 네이버광고 → Codex / Developer → Codex /
    데이터 → Codex / 검수 → Claude / 리서처 → Gemini
- **로컬 LLM 카탈로그** 토글 (llama3.1:8b, gemma2:9b, qwen2.5:7b, phi3:mini, mistral:7b)
- 저장은 브라우저 `localStorage`에 보관 (서버 호출 없음). 다음 단계에서 백엔드와
  연결 가능.

## 5. 시스템 진단 모달

`navigator` / `screen` API로 자동 수집:

- OS Platform / CPU 코어 / RAM 추정 / 화면 해상도 / 언어 / UA / 현재 시각
- 안전 규칙 요약(`AGENTS.md` 핵심 4줄)

## 6. 리포트 자동화 모달

매일/매주/매월 자동 dry-run 보고서 후보를 표로 표시:

- 매일 09:00 활동 로그 평균 소요 시간 (`activity-report`)
- 매일 09:05 승인 위험도 우선순위 (`approval-priority-queue`)
- 매주 월 10:00 네이버광고 CSV 분석 (`analyze-ads`)
- 매월 1일 09:30 승인 파일 정리 (`approval-cleanup-report`)

`schtasks` 예시 명령도 같이 표기.

## 7. 사용 방법

브라우저로 직접 열거나, 로컬 뷰어 서버 켜고 접속:

```powershell
# 직접 열기
start D:\AI_COMPANY\06_apps\agent_matrix\index.html

# 또는 서버로
powershell -ExecutionPolicy Bypass -File .\scripts\start_local_viewer.ps1
# 후 http://127.0.0.1:8765/06_apps/agent_matrix/index.html
```

## 8. 사장님 확인 필요한 부분

- 에이전트 10명 구성 (사장님 회사에 맞는 추가/제거 가능)
- 자동 매핑 기본값 (Claude/Codex/Gemini/Ollama/이미지 AI 분배 비율)
- 모델 매핑 저장 방식: 현재 brower localStorage → 백엔드 파일(JSON)로 옮길지

## 9. 안전 확인

- 외부 API 호출 / 모델 다운로드 / 발송 — 없음
- localStorage 외에 사용자 데이터 외부 전송 — 없음
- 보여주는 시스템 진단 정보는 브라우저 자체 API만 사용 (서버 측 시스템 명령 호출 없음)
- 자동 오케스트레이션은 매핑 표 갱신만, 실제 모델 호출은 사장님이 별도 명령으로 진행
