# 사장님 명령 → 7단계 파이프라인 (원본 아키텍처)

사장님이 처음 의도하신 흐름을 그대로 코드화했습니다. **한 줄 명령**으로
7단계 전부 자동 진행되고, 마지막에 사장님이 보실 09_approval 파일만 남습니다.

## 전체 흐름

```
[사장님]
   ↓
[1. Hermes AI / AgentAU / n8n]   ← 인바운드 수신 + 오케스트레이션 큐
   ↓
[2. CEO 오케스트레이터]            ← 작업 분해 + 우선순위 + 책임 직원
   ↓
[3. 모델 라우터]                   ← 1순위 모델 결정
       ├─ Codex / ChatGPT : 코딩, 시스템 구축, 전략
       ├─ Claude          : 긴 문서, 고급 코딩, 기획서, 검토
       ├─ Gemini          : 리서치, 트렌드 조사, 아이디어 확장
       ├─ Ollama          : 내 컴퓨터 로컬 반복작업
       └─ 이미지 AI        : 광고 이미지 / 썸네일 제작
   ↓
[4. AI 회의]                       ← 각 AI 직원 의견 + CEO 결론
   ↓
[5. 실행 준비]                     ← 광고 패키지 / 이미지 시안 / 분석
   ↓
[6. 사장님 승인 대기]              ← 09_approval 파일 자동 생성
   ↓
[사장님이 보고 OK → 실제 실행]     ← 이 단계는 사장님이 직접
```

## 명령

```powershell
python -m ai_company.main boss-command --message "고스틱 광고 효율 개선해줘"
python -m ai_company.main boss-command --message "릴스 썸네일 시안 만들어줘" --live
python -m ai_company.main boss-command --message "네이버광고 CSV 분석해줘"
```

`--live`는 4단계 AI 회의가 Ollama로 실제 LLM 의견을 생성하도록 함.
없으면 dry-run 시나리오 의견.

## 각 단계가 만드는 파일

| 단계 | 산출물 위치 |
|---|---|
| 1. Hermes 인바운드 | (로그만, 외부 호출 없음) |
| 2. AgentAU/n8n | (로그만) |
| 3. CEO 오케스트레이터 | `08_reports/ceo_workplan_*.md` |
| 4. 모델 라우터 | 라우팅 카드는 보고서 head에 |
| 5. AI 회의 | `10_meetings/ai_meeting_*.md` |
| 6. 실행 준비 | 작업 종류별로 `02_marketing/`, `03_images/templates/`, `05_naver_ads/` |
| 7. 사장님 승인 | `09_approval/APPROVAL_REQUIRED_boss_pipeline_*.md` |

전체 흐름 요약은 `08_reports/boss_command_*.md`에 한 파일로 묶임.

## 사장님 시점 사용법 (3분 컷)

1. **명령 한 줄**:
   ```powershell
   python -m ai_company.main boss-command --message "고스틱 광고 만들어줘"
   ```

2. **결과 보고서 열기** — 콘솔에 찍힌 `보고서 저장: ...` 경로

3. **마지막 09_approval 파일 검토** — 광고 패키지나 이미지 시안이 어떻게
   준비됐는지 확인

4. **OK면** 사장님이 직접 외부 채널에 반영 (SNS 업로드, 상세페이지 교체 등)
   **NG면** 그냥 무시하시면 됨 (외부에 아무것도 안 나감)

## 위험 단어 자동 차단

명령에 `입찰가 / 광고비 / 업로드 / 결제 / 환불 / 로그인` 같은 단어가 있으면
CEO 단계에서 위험 요소로 표시되고, 7단계 끝나도 외부 채널 자동 반영은
**무조건 사장님이 직접**.

## 비용 가드

라이브 모드(`--live`)에서 외부 API가 호출되면 자동으로:
- 호출 전 일일 ₩1,000 / 월 ₩30,000 캡 검사
- 호출 후 `12_logs/llm_usage.jsonl`에 토큰/비용 추정 적재
- 캡 초과 위험이면 HTTP 호출 자체가 안 됨

## 점검

```powershell
python -m ai_company.main env-check        # 키/사용량 한눈
python -m ai_company.main usage-report     # 누적 비용 보고서
python -m ai_company.main approvals list   # 대기 중 승인 파일
```

## 다른 진입점도 그대로 사용 가능

`boss-command`가 7단계 전부를 묶은 메인 진입점이지만, 단독 명령도 동작합니다:

- `nl --message "..."` — 의도 분류만
- `routed-run --task "..." --live` — 라우터 + 단일 어댑터 호출
- `meeting --topic "..." --with-router --live` — 회의만
- `ad --product GOSTICK01 --with-router` — 광고 패키지만
- `image-templates --product GOSTICK01 --with-router` — 이미지 템플릿만

`boss-command`는 이 모든 단계를 자동으로 묶어줍니다.
