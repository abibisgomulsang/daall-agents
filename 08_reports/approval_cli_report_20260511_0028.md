# 승인 관리 CLI 구축 보고서

## 1. 목적

실제 스마트스토어, SNS, 네이버광고 변경 전에 `09_approval` 폴더의 승인 대기 파일을 조회하고, 승인/반려 결정을 별도 기록으로 남기는 안전 장치를 추가했다.

## 2. 추가 명령

### 승인 목록 조회

```powershell
python -m ai_company.main approvals list
```

출력 항목:
- 상태
- 승인 대기 파일명
- 최근 결정 시각
- 사유

### 승인/반려 기록

```powershell
python -m ai_company.main approvals decide --file APPROVAL_REQUIRED_...md --decision approved --reason "승인 사유"
python -m ai_company.main approvals decide --file APPROVAL_REQUIRED_...md --decision rejected --reason "반려 사유"
```

주의:
- 이 명령은 승인 상태만 기록한다.
- 실제 업로드, 광고 수정, 입찰 변경, 결제는 실행하지 않는다.

## 3. 생성되는 기록

- `09_approval/approval_decisions.jsonl`
- `09_approval/APPROVAL_DECISION_...md`

## 4. 테스트 결과

- `.\.venv\Scripts\python.exe -m pytest`
- 결과: 4 passed

## 5. 현재 승인 상태

`python -m ai_company.main approvals list` 기준 기존 승인 요청 8개가 모두 대기 상태다.

## 6. 다음 단계 제안

승인 기록을 기반으로 실제 실행 전 최종 dry-run 플랜을 만드는 명령을 추가한다.

예:

```powershell
python -m ai_company.main execution-plan --approval APPROVAL_REQUIRED_...md
```
