# 모델 라우터 결정 보고서

- 생성 시각: 2026-05-10 18:16:39
- 입력 작업: 고스틱 광고 릴스 썸네일 시안 만들어줘
- 1순위 모델: **이미지 AI (Stable Diffusion / Canva / PIL)** (광고 이미지, 썸네일, 시각 자산)
- 1순위 점수: 8

## 라우팅 사유 (1순위)
- 키워드 일치: '썸네일' (+3)
- 키워드 일치: '썸' (+3)
- 강점 토큰 일치: '광고 이미지 기획' (+1)
- 강점 토큰 일치: '썸네일 구성안' (+1)

## 후순위 후보
- Gemini — 점수 1 / 역할: 리서치, 트렌드 조사, 아이디어 확장
    - 강점 토큰 일치: '광고 소재 아이디어' (+1)
- Ollama (로컬) — 점수 1 / 역할: 내 PC 로컬 반복작업
    - 강점 토큰 일치: '광고 문구 초안' (+1)

## 안전 규칙 (해당 모델)
- 저작권/초상권 확인 후 사용
- 실제 게시는 승인 후

## Dry-run 핸드오프 페이로드 (실제 호출 안 함)
```json
{
  "router_version": "1.0.0",
  "task": "고스틱 광고 릴스 썸네일 시안 만들어줘",
  "primary_model": "image_ai",
  "primary_display_name": "이미지 AI (Stable Diffusion / Canva / PIL)",
  "role": "광고 이미지, 썸네일, 시각 자산",
  "runners_up": [
    "gemini",
    "ollama"
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
