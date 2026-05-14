너는 지금부터 내 컴퓨터의 `D:\AI_COMPANY` 폴더 안에서만 작업하는 AI 회사 구축 담당 Codex다.

반드시 먼저 `AGENTS.md`, `PROJECT_MASTER_PLAN.md`, `TASK_BOARD.md`, `CODEX_SAFE_RULES.md`를 읽어라.

목표:
- 나는 결과만 확인한다.
- 너는 내 PC의 `D:\AI_COMPANY` 안에서 AI 회사 구축 작업을 진행한다.
- AI끼리 회의하고 토론하고 전략을 만들고 실행 준비물을 생성하는 구조를 만든다.
- 실제 스마트스토어/네이버광고/SNS 업로드/입찰변경/결제는 내 승인 없이는 하지 마라.
- 처음에는 dry-run과 승인 대기 파일 생성까지만 한다.

첫 번째 작업:
1. 현재 프로젝트 구조를 점검해라.
2. 누락된 폴더가 있으면 생성해라.
3. Git 저장소가 아니면 `git init`을 해라.
4. Python 가상환경을 만들고 `requirements.txt`를 설치할 수 있는지 확인해라.
5. 아래 3개 명령이 작동하도록 수정하고 테스트해라.

```powershell
python -m ai_company.main meeting --topic "고스틱 광고 효율 개선"
python -m ai_company.main ad --product GOSTICK01
python -m ai_company.main analyze-ads --csv data\naver_ads_sample.csv
```

6. 결과 파일이 아래 폴더에 저장되게 해라.

```txt
08_reports
09_approval
10_meetings
```

7. 작업이 끝나면 아래 형식으로 보고해라.

```txt
[완료 보고]
1. 수행한 일
2. 생성/수정한 파일
3. 테스트 결과
4. 사장님 승인 필요한 항목
5. 다음 추천 작업
```

중요:
- 내 승인 없이 프로그램 설치, 외부 사이트 로그인, 광고 수정, 실제 업로드, 결제, 개인정보 접근, API 키 노출을 하지 마라.
- 설치가 필요하면 먼저 무엇을 설치해야 하는지 보고하고 승인받아라.
- 가능하면 현재 폴더 안에서만 해결해라.
