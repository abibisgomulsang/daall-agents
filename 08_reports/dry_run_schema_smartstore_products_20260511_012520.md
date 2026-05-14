# Dry-run 데이터 스키마: smartstore_products

- 설명: 스마트스토어 상품 데이터 dry-run 스키마
- 실제 외부 API 호출 여부: 호출 안 함

## 필드

| 필드 | 타입 | 필수 |
| --- | --- | --- |
| product_code | string | 예 |
| product_name | string | 예 |
| price | integer | 예 |
| stock | integer | 아니오 |
| status | string | 아니오 |
| detail_page_url | string | 아니오 |

## 금지 액션

- 상품명 실제 수정
- 가격 변경
- 재고 변경
- 상세페이지 저장