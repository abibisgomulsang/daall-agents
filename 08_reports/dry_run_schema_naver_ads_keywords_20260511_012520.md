# Dry-run 데이터 스키마: naver_ads_keywords

- 설명: 네이버광고 키워드 데이터 dry-run 스키마
- 실제 외부 API 호출 여부: 호출 안 함

## 필드

| 필드 | 타입 | 필수 |
| --- | --- | --- |
| campaign | string | 예 |
| ad_group | string | 아니오 |
| keyword | string | 예 |
| bid | integer | 아니오 |
| cost | integer | 예 |
| clicks | integer | 예 |
| orders | integer | 예 |
| revenue | integer | 예 |

## 금지 액션

- 입찰가 실제 변경
- 광고비 변경
- 키워드 중지