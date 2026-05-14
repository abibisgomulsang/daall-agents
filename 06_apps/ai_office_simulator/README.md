# AI Company Office Simulator

AI 직원들이 업무중, 검수, 대기, 막힘 상태인지 한눈에 볼 수 있는 정적 웹 시뮬레이터다.

## 실행

앱 브라우저에서 `file://` 주소가 막히면 로컬 서버로 연다.

```powershell
cd D:\AI_COMPANY
powershell -ExecutionPolicy Bypass -File .\scripts\start_local_viewer.ps1
```

출력된 아래 주소를 브라우저에 붙여넣는다.

```txt
http://127.0.0.1:8765/06_apps/ai_office_simulator/index.html
```

일반 브라우저에서 파일 직접 열기도 가능하다.

```txt
D:\AI_COMPANY\06_apps\ai_office_simulator\index.html
```

## 현재 범위

- 외부 서버 없음
- 로그인 없음
- 실제 스마트스토어/SNS/네이버광고 실행 없음
- CLI 작업 로그를 `activity_feed.js`로 읽어 상태판에 반영
- 채팅창에서 자연어를 안전한 dry-run CLI 명령으로 실행
- 승인 대기/승인/반려 개수를 상태판에 표시
- 승인 파일 위험도와 실행 검토 큐를 업무 큐에 표시
- 4~8단계 Ollama/Claude-Gemini/Telegram/Hermes/AgentAU-n8n 연결 상태를 표시
- 명령별 소요 시간을 활동 로그에 표시
- dry-run 대시보드와 추천 웹앱으로 이동하는 로컬 링크 제공
- 작업 로그가 없으면 화면 상태 시뮬레이션 제공

## 채팅 예시

```txt
고스틱 광고 회의해줘
고스틱 광고 만들어줘
네이버 광고 분석해줘
대시보드 갱신해줘
Ollama 모델 목록 dry-run 만들어줘
```

채팅 실행은 로컬 서버에서 허용된 `ai_company.main` 명령만 사용한다. 실제 업로드, 게시, 입찰 변경, 발송, 결제는 실행하지 않는다.

## 다음 확장

- 승인 완료 후 Ollama 모델 목록 읽기 전용 조회 결과 표시
- 작업별 평균 소요 시간 리포트
