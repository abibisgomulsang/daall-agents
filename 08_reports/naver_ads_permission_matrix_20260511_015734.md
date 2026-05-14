# 네이버광고 API 읽기/쓰기 권한 매트릭스

- 실제 API 호출 여부: 호출 안 함
- 입찰가 변경 여부: 변경 안 함
- 광고비 변경 여부: 변경 안 함
- 키워드 상태 변경 여부: 변경 안 함

## 엔드포인트 권한표

| 엔드포인트 | 메서드 | 권한 범위 | 쓰기 | MVP 허용 | 승인 필요 | 차단 사유 |
| --- | --- | --- | --- | --- | --- | --- |
| campaign_list | GET | read_campaign | 아니오 | 예 | 예 | - |
| adgroup_list | GET | read_adgroup | 아니오 | 예 | 예 | - |
| keyword_report | GET | read_keyword_report | 아니오 | 예 | 예 | - |
| cost_report | GET | read_cost_report | 아니오 | 예 | 예 | - |
| keyword_bid_update | PUT | write_keyword_bid | 예 | 아니오 | 예 | 입찰가 실제 변경 위험 |
| campaign_budget_update | PUT | write_budget | 예 | 아니오 | 예 | 광고비 실제 변경 위험 |
| keyword_pause | PUT | write_keyword_status | 예 | 아니오 | 예 | 키워드 노출 중지 위험 |

## 안전 게이트

- API 키/secret/customer id 출력 금지
- 읽기 API도 승인 파일 확인 후 진행
- 쓰기 API는 1차 MVP에서 전부 차단
- 입찰가/광고비/키워드 상태 변경은 사장님 최종 승인 필요