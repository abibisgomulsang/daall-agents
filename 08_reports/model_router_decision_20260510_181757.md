# 모델 라우터 결정 보고서

- 생성 시각: 2026-05-10 18:17:57
- 입력 작업: 트렌드 리서치
- 1순위 모델: **Gemini** (리서치, 트렌드 조사, 아이디어 확장)
- 1순위 점수: 7

## 라우팅 사유 (1순위)
- 키워드 일치: '리서치' (+3)
- 키워드 일치: '트렌드' (+3)
- 강점 토큰 일치: '트렌드 조사' (+1)

## 안전 규칙 (해당 모델)
- 리서치 결과는 출처와 함께 보고. 단정 표현/과장 금지

## Dry-run 핸드오프 페이로드 (실제 호출 안 함)
```json
{
  "router_version": "1.0.0",
  "task": "트렌드 리서치",
  "primary_model": "gemini",
  "primary_display_name": "Gemini",
  "role": "리서치, 트렌드 조사, 아이디어 확장",
  "runners_up": [],
  "dry_run": true,
  "executed": false,
  "next_stage": "ai_meeting",
  "approval_required_for_external": true
}
```

## 다음 단계
- AI 회의 시스템에 결과 전달
- 실행 준비물(광고/문서/이미지) 생성
- 외부 호출/업로드/입찰 변경은 09_approval 파일 작성 후 사장님 승인
