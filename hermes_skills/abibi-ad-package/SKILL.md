---
name: abibi-ad-package
description: 아비비 AI 회사 — 상품 광고 패키지 생성. 후킹 문구 3안 + 인스타 피드 + 릴스 대본 + 이미지 편집 지시서 + 해시태그 + 검수 결과를 한 번에. 모델 라우터 결정도 머리에 첨부.
triggers:
  - "광고 만들어"
  - "광고 패키지"
  - "광고 카피"
  - "후킹 문구"
  - "릴스 만들어"
---

# 상품 광고 패키지 생성

사장님 요청에서 **상품 코드**를 추출하라:

| 한국어 | 코드 |
|---|---|
| 고스틱 | GOSTICK01 |
| 플라고 | PLAGO01 |
| 리필 | REFILL01 |

명시되지 않으면 기본 `GOSTICK01` 사용.

## 동작

```bash
cd /mnt/d/AI_COMPANY
"/mnt/d/AI_COMPANY/.venv/Scripts/python.exe" -m ai_company.main ad --product GOSTICK01 --with-router
```

## 결과

- 광고 패키지 마크다운: `D:\AI_COMPANY\08_reports\ad_package_*.md`
- 승인 대기 파일: `D:\AI_COMPANY\09_approval\APPROVAL_REQUIRED_ad_*.md`

## 사장님께 보고할 것

1. 1순위 모델 라우터 결정 (이미지 AI / Codex 등)
2. 후킹 문구 3안 짧게 요약
3. 검수 AI 위험 경고가 있다면 명시
4. **"실제 SNS 업로드는 09_approval 검토 후 사장님이 직접 진행"** 한 줄 강조

## 안전 규칙

- 실제 SNS 게시/광고 집행 절대 안 함
- 모든 산출물은 D:\AI_COMPANY 내부 파일로만
- 과장광고/효능/100% 표현은 검수 AI가 자동 차단
