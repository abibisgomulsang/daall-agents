# 모델 라우터 결정 보고서

- 생성 시각: 2026-05-10 18:18:22
- 입력 작업: 스마트스토어 상세페이지 문구 검수
- 1순위 모델: **Claude** (긴 문서, 고급 코딩, 기획서, 검토)
- 1순위 점수: 7

## 라우팅 사유 (1순위)
- 키워드 일치: '검수' (+3)
- 키워드 일치: '상세페이지' (+3)
- 강점 토큰 일치: '스마트스토어 상세페이지 문구 검수' (+1)

## 후순위 후보
- 이미지 AI (Stable Diffusion / Canva / PIL) — 점수 1 / 역할: 광고 이미지, 썸네일, 시각 자산
    - 강점 토큰 일치: '상세페이지 비주얼 초안' (+1)

## 안전 규칙 (해당 모델)
- API 키, 비밀번호, .env 노출 금지

## Dry-run 핸드오프 페이로드 (실제 호출 안 함)
```json
{
  "router_version": "1.0.0",
  "task": "스마트스토어 상세페이지 문구 검수",
  "primary_model": "claude",
  "primary_display_name": "Claude",
  "role": "긴 문서, 고급 코딩, 기획서, 검토",
  "runners_up": [
    "image_ai"
  ],
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
