# 외부 채널 dry-run 어댑터 보고서

## 1. 수행 목적

스마트스토어, 네이버광고, 인스타그램 실제 실행 전 로컬 dry-run 산출물과 승인 대기 파일을 만들 수 있게 했다.

## 2. 스마트스토어 상품 데이터 가져오기 dry-run

명령:

```powershell
python -m ai_company.main smartstore-fetch-dry-run
```

생성:

```txt
08_reports/smartstore_fetch_dry_run_20260511_012738.md
04_smartstore/dry_run/smartstore_products_20260511_012738.json
04_smartstore/dry_run/smartstore_products_20260511_012738.csv
09_approval/APPROVAL_REQUIRED_smartstore_fetch_20260511_012738.md
```

실제 로그인/API 호출/상품 수정은 하지 않았다.

## 3. 네이버광고 API dry-run 어댑터

명령:

```powershell
python -m ai_company.main naver-ads-api-dry-run
```

생성:

```txt
08_reports/naver_ads_api_dry_run_20260511_012738.md
05_naver_ads/dry_run/naver_ads_api_plan_20260511_012738.json
09_approval/APPROVAL_REQUIRED_naver_ads_api_read_20260511_012738.md
```

실제 API 호출, 입찰가 변경, 광고비 변경은 하지 않았다.

## 4. 인스타 업로드 승인형 dry-run

명령:

```powershell
python -m ai_company.main instagram-upload-dry-run --product GOSTICK01
```

생성:

```txt
08_reports/instagram_upload_dry_run_GOSTICK01_20260511_012738.md
02_marketing/instagram_dry_run/instagram_upload_GOSTICK01_20260511_012738.json
09_approval/APPROVAL_REQUIRED_instagram_upload_GOSTICK01_20260511_012738.md
```

실제 업로드/게시/예약/고객 메시지는 하지 않았다.

## 5. 테스트 결과

- `.\.venv\Scripts\python.exe -m pytest`
- 결과: 16 passed

## 6. 안전 확인

- API 키/토큰 출력 없음
- 외부 서비스 로그인 없음
- 결제/주문/환불 없음
- 실제 업로드/입찰/광고비 변경 없음
