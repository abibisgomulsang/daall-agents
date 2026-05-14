---
name: abibi-meeting
description: 아비비 AI 회사 — 3라운드 멀티 에이전트 토론 회의. 7명의 직원(데이터/심리/SNS/상품/네이버광고/검수/마케팅)이 자기 모델·페르소나로 각자 의견 → 반박/동조 → 표결 → CEO 종합. SNS 작업이면 비디오 AI도 자동 합석.
triggers:
  - "회의"
  - "토론"
  - "직원 의견"
  - "AI 회의"
  - "다 같이"
  - "팀 회의"
---

# AI 회사 멀티 에이전트 회의

사장님이 회의나 토론을 요청하면 이 스킬을 호출하라.

## 동작

WSL의 `/mnt/d/AI_COMPANY` 에 있는 우리 회사 CLI를 호출한다.

```bash
cd /mnt/d/AI_COMPANY
"/mnt/d/AI_COMPANY/.venv/Scripts/python.exe" -m ai_company.main multi-meeting --topic "<사장님 주제>"
```

`<사장님 주제>` 자리에 사장님 메시지에서 추출한 주제를 넣어라. 예:
- "고스틱 광고 효율 회의해줘" → `--topic "고스틱 광고 효율 개선"`
- "네이버광고 ROAS 회복 어떻게 할까" → `--topic "네이버광고 ROAS 회복"`

비용 절약 모드(모든 직원 Ollama):

```bash
... multi-meeting --topic "..." --no-live
```

## 결과

- 회의록: `D:\AI_COMPANY\10_meetings\multi_meeting_*.md`
- JSON: 같은 폴더의 `.json`
- 직원 발언 메모리: `11_memory/agents/<직원>/rounds.jsonl`

## 사장님께 보고할 것

1. 1차 책임자가 누구인지
2. 표결 결과 (동의/반대/기권)
3. CEO 종합 결론 핵심 한 줄
4. 회의록 파일 경로

## 안전 규칙

- 외부 채널 자동 반영 절대 없음
- 비용 캡 자동 검사 (₩1,000/일) — 초과 시 자동으로 모두 Ollama 강등
- 사장님 승인 흐름은 회의 결론에 항상 명시되어 있음
