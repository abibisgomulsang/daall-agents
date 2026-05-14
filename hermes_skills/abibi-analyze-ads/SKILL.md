---
name: abibi-analyze-ads
description: 아비비 AI 회사 — 네이버광고 CSV 분석. CTR/CPC/전환율/ROAS 분리 분석, 낭비 키워드 추출, 입찰가 조정 후보, 광고 문구 개선안. 분석만, 실제 입찰 변경 절대 안 함.
triggers:
  - "네이버광고 분석"
  - "광고 분석"
  - "ROAS"
  - "CTR"
  - "키워드 분석"
  - "낭비 키워드"
---

# 네이버광고 효율 분석

사장님이 광고 분석을 요청하면 이 스킬을 호출.

## 동작

```bash
cd /mnt/d/AI_COMPANY
"/mnt/d/AI_COMPANY/.venv/Scripts/python.exe" -m ai_company.main analyze-ads \
  --csv data/naver_ads_sample.csv
```

`data/naver_ads_sample.csv` 외에 사장님이 다른 CSV를 두셨으면 그 경로를 사용.

## 결과

- 분석 보고서: `D:\AI_COMPANY\05_naver_ads\naver_ads_report_*.md`
- 08_reports 사본: `D:\AI_COMPANY\08_reports\naver_ads_report_*.md`
- 승인 대기: `D:\AI_COMPANY\09_approval\APPROVAL_REQUIRED_naver_ads_actions_*.md`

## 사장님께 보고할 것

1. 전체 ROAS 한 줄
2. 낭비 키워드 1~3순위
3. 입찰 변경 후보 — **"실제 변경은 09_approval 검토 후 사장님 직접"** 강조

## 안전 규칙

- 실제 입찰가 / 광고비 변경 절대 안 함
- 분석 결과는 보고서로만 — 사장님이 보시고 직접 네이버광고 콘솔에서 적용
- 위험 키워드(입찰가, 광고비, 변경, 적용) 포함 명령은 자동 차단
