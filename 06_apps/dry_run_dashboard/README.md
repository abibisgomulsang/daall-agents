# Dry-run Dashboard

AI 회사의 로컬 dry-run 산출물, 승인 파일, 앱 상태를 한눈에 보는 정적 대시보드다.
AI 사무실 시뮬레이터와 추천 웹앱으로 이동하는 로컬 링크를 포함한다.
승인 파일 상세 패널에서 최근 승인 요청의 상태, 사유, 경로를 확인할 수 있다.
승인 파일 위험도 점수를 표시해 실제 실행 전 더 조심해야 할 작업을 먼저 볼 수 있다.
실행 계획과 최종 체크리스트 Markdown 파일로 바로 이동하는 로컬 링크를 제공한다.
위험도 기반 실행 검토 큐를 표시하지만 실제 실행은 하지 않는다.

## 실행

```txt
D:\AI_COMPANY\06_apps\dry_run_dashboard\index.html
```

## 데이터 갱신

```powershell
python -m ai_company.main dry-run-dashboard
```

## 안전 범위

- 외부 API 호출 없음
- 로그인 없음
- 실제 업로드/입찰/광고비 변경 없음
