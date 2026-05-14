---
name: abibi-boss-command
description: 아비비 AI 회사 — 7단계 풀 파이프라인. 사장님 한 줄 명령으로 Hermes 인바운드 → AgentAU/n8n → CEO 오케스트레이터 → 모델 라우터 → AI 회의 → 실행 준비 → 사장님 승인 대기까지 자동. 사장님이 "전부 해줘"류 큰 요청 보냈을 때 사용.
triggers:
  - "전부 해줘"
  - "다 처리해"
  - "풀 코스"
  - "처음부터 끝까지"
  - "회의부터 준비까지"
---

# 7단계 풀 파이프라인

사장님이 큰 단위 요청을 했을 때만 사용. 작은 명령은 더 구체적인 스킬
(`abibi-meeting`, `abibi-ad-package` 등)을 우선 호출.

## 동작 (멀티 에이전트 회의 포함)

```bash
cd /mnt/d/AI_COMPANY
"/mnt/d/AI_COMPANY/.venv/Scripts/python.exe" -m ai_company.main boss-command \
  --message "<사장님 메시지 그대로>" --live --multi
```

## 결과

종합 보고서 한 파일 + 단계별 산출물:

- `D:\AI_COMPANY\08_reports\boss_command_*.md` — 7단계 전체 흐름
- `D:\AI_COMPANY\08_reports\ceo_workplan_*.md` — CEO 작업 분해
- `D:\AI_COMPANY\10_meetings\multi_meeting_*.md` — 멀티 회의록
- 작업 유형에 따라 `02_marketing/` / `05_naver_ads/` / `06_apps/video_briefs/` 등
- `D:\AI_COMPANY\09_approval\APPROVAL_REQUIRED_boss_pipeline_*.md` — 최종 승인 대기

## 사장님께 보고할 것

1. 1차 책임 직원 (CEO 분배 결과)
2. 회의 표결 결과 한 줄
3. 산출물 종류 (광고 패키지 / 비디오 / 분석)
4. 09_approval 파일 경로 — **"검토 후 OK면 사장님이 직접 외부 채널 반영"**

## 안전 규칙

- 7단계 끝나도 외부 채널 자동 반영 절대 없음
- 사장님이 09_approval 파일을 보고 직접 결정 → 직접 실행
- 위험 키워드 자동 차단 + 비용 캡 검사는 단계마다 동작
