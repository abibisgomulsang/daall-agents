# 자동 실험 설계, 공유 이미지 설계, dry-run 스키마 보고서

## 1. 수행 목적

AI 회의 결과를 실제 광고/SNS/스토어 실행 전 실험 설계로 변환하고, 추천 웹앱 결과 공유 이미지 설계와 외부 API 연동 전 dry-run 데이터 스키마를 만들었다.

## 2. 자동 실험 설계

명령:

```powershell
python -m ai_company.main experiment-plan --topic "고스틱 광고 효율 개선"
```

생성:

```txt
08_reports/experiment_plan_20260511_012520.md
08_reports/experiment_plan_20260511_012520.json
```

실험 후보:
- 공감형 후킹 문구 테스트
- 릴스 첫 2초 썸네일 테스트
- 리필/세트 메시지 테스트

## 3. 추천 결과 공유 이미지 설계

명령:

```powershell
python -m ai_company.main share-image-design --result GOSTICK01
```

생성:

```txt
08_reports/share_image_design_GOSTICK01_20260511_012520.md
03_images/share_cards/share_image_design_GOSTICK01_20260511_012520.json
```

실제 이미지 생성 또는 SNS 업로드는 하지 않았다.

## 4. dry-run 데이터 스키마

명령:

```powershell
python -m ai_company.main dry-run-schema --schema smartstore_products
python -m ai_company.main dry-run-schema --schema naver_ads_keywords
python -m ai_company.main dry-run-schema --schema sns_posts
```

생성:

```txt
08_reports/dry_run_schema_smartstore_products_20260511_012520.md
08_reports/dry_run_schema_naver_ads_keywords_20260511_012520.md
08_reports/dry_run_schema_sns_posts_20260511_012520.md
11_memory/schemas/*.json
```

## 5. 테스트 결과

- `.\.venv\Scripts\python.exe -m pytest`
- 결과: 15 passed

## 6. 안전 확인

- 실제 스마트스토어 API 호출 없음
- 실제 네이버광고 API 호출 없음
- 실제 SNS 업로드 없음
- 결제/고객 메시지 없음
- API 키/토큰 출력 없음
