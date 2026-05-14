# Dry-run 데이터 스키마: sns_posts

- 설명: SNS 게시물 dry-run 스키마
- 실제 외부 API 호출 여부: 호출 안 함

## 필드

| 필드 | 타입 | 필수 |
| --- | --- | --- |
| channel | string | 예 |
| caption | string | 예 |
| hashtags | array[string] | 아니오 |
| asset_path | string | 아니오 |
| scheduled_at | string | 아니오 |

## 금지 액션

- 실제 업로드
- 게시
- DM/댓글 발송