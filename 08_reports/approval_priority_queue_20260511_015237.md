# 승인 파일 실행 우선순위 큐

- 실제 실행 여부: 실행 안 함
- 목적: 승인 파일 중 먼저 검토해야 할 항목을 위험도 기준으로 정렬

| 순위 | 위험도 | 점수 | 승인 상태 | 파일 | 다음 단계 | 게이트 |
| ---: | --- | ---: | --- | --- | --- | --- |
| 1 | 매우 높음 | 100 | pending | APPROVAL_REQUIRED_ad_GOSTICK01_20260510_235522.md | 최종 체크리스트 생성 후 원본 화면/설정 백업 | 사장님 재확인 전 실제 실행 금지 |
| 2 | 매우 높음 | 100 | pending | APPROVAL_REQUIRED_ad_GOSTICK01_20260511_001353.md | 최종 체크리스트 생성 후 원본 화면/설정 백업 | 사장님 재확인 전 실제 실행 금지 |
| 3 | 매우 높음 | 100 | pending | APPROVAL_REQUIRED_ad_GOSTICK01_20260511_002115.md | 최종 체크리스트 생성 후 원본 화면/설정 백업 | 사장님 재확인 전 실제 실행 금지 |
| 4 | 매우 높음 | 100 | pending | APPROVAL_REQUIRED_ad_GOSTICK01_20260511_005859.md | 최종 체크리스트 생성 후 원본 화면/설정 백업 | 사장님 재확인 전 실제 실행 금지 |
| 5 | 매우 높음 | 100 | pending | APPROVAL_REQUIRED_ad_GOSTICK01_20260511_013510.md | 최종 체크리스트 생성 후 원본 화면/설정 백업 | 사장님 재확인 전 실제 실행 금지 |
| 6 | 매우 높음 | 100 | pending | APPROVAL_REQUIRED_instagram_upload_GOSTICK01_20260511_012738.md | 최종 체크리스트 생성 후 원본 화면/설정 백업 | 사장님 재확인 전 실제 실행 금지 |
| 7 | 매우 높음 | 100 | pending | APPROVAL_REQUIRED_meeting_actions_20260510_235521.md | 최종 체크리스트 생성 후 원본 화면/설정 백업 | 사장님 재확인 전 실제 실행 금지 |
| 8 | 매우 높음 | 100 | pending | APPROVAL_REQUIRED_meeting_actions_20260511_001353.md | 최종 체크리스트 생성 후 원본 화면/설정 백업 | 사장님 재확인 전 실제 실행 금지 |
| 9 | 매우 높음 | 100 | pending | APPROVAL_REQUIRED_meeting_actions_20260511_002111.md | 최종 체크리스트 생성 후 원본 화면/설정 백업 | 사장님 재확인 전 실제 실행 금지 |
| 10 | 매우 높음 | 100 | pending | APPROVAL_REQUIRED_meeting_actions_20260511_005855.md | 최종 체크리스트 생성 후 원본 화면/설정 백업 | 사장님 재확인 전 실제 실행 금지 |
| 11 | 매우 높음 | 100 | pending | APPROVAL_REQUIRED_meeting_actions_20260511_013511.md | 최종 체크리스트 생성 후 원본 화면/설정 백업 | 사장님 재확인 전 실제 실행 금지 |
| 12 | 매우 높음 | 100 | pending | APPROVAL_REQUIRED_naver_ads_actions_20260511_001353.md | 최종 체크리스트 생성 후 원본 화면/설정 백업 | 사장님 재확인 전 실제 실행 금지 |

## 안전 메모

- 큐에 올라간 항목은 실행 후보가 아니라 검토 우선순위다.
- 스마트스토어/네이버광고/SNS 실제 실행은 사장님 승인 전까지 금지다.
- 결제, 고객 발송, 주문/환불, API 키 노출은 자동 진행하지 않는다.