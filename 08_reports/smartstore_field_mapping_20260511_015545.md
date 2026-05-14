# 스마트스토어 상품 데이터 필드 매핑 설계

- 실제 로그인 여부: 로그인 안 함
- 실제 API 호출 여부: 호출 안 함
- 상품 수정/가격/재고/상세페이지 저장 여부: 실행 안 함
- 로컬 기준 CSV: `D:\AI_COMPANY\data\products.csv`

## 로컬 필드 → 스마트스토어 후보 필드

| 로컬 필드 | 스마트스토어 후보 필드 | 변환 | 모드 |
| --- | --- | --- | --- |
| product_code | customProductCode | string 그대로 | read |
| product_name | name | 공백 정리 후 문자열 | read_then_approval_required_write |
| price | salePrice | 정수 원화 | read_then_approval_required_write |
| tags | searchTags | '|'를 배열로 분리 | read_then_approval_required_write |
| main_feature | detailContent | 상세페이지 초안 입력값 | draft_only |

## 필수 점검

- 누락된 로컬 필드: 없음
- 매핑되지 않은 로컬 필드: cost, target_cat
- 매핑되지 않은 필수 타깃 필드: 없음

## 쓰기 차단 필드

- name
- salePrice
- stockQuantity
- saleStatus
- detailContent
- representativeImage

## 다음 단계

- 실제 API 읽기 연동 전 승인 파일 확인
- API 키/토큰/쿠키 값은 출력하지 않음
- 최초 연동은 읽기 전용으로만 설계
- 상품 수정, 가격, 재고, 상세페이지 저장은 별도 최종 승인 필요