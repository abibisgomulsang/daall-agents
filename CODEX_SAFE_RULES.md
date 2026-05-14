# Codex 안전 운영 규칙

## Codex에게 허용할 일

- `D:\AI_COMPANY` 안의 파일 생성/수정
- `D:\AI_COMPANY` 안의 폴더 생성
- Python/Node 코드 작성
- Python 가상환경 생성: `python -m venv .venv`
- Python 패키지 설치: `pip install -r requirements.txt`
- Python CLI 실행: `python -m ai_company.main ...`
- 테스트 실행: `pytest`, `python -m pytest`
- 광고 문구 생성
- CSV/엑셀 분석
- 보고서 생성
- dry-run 자동화 코드 작성
- Git 작업: `git init`, `git status`, `git add`, `git commit`
- `requirements.txt` 수정
- `ai_company` 내부 코드 수정
- `docs` 문서 작성
- `08_reports` 보고서 생성
- 승인 대기 파일 생성
- `10_meetings` 회의 결과 생성
- 시뮬레이터, 테스트용 웹앱, 로컬 dry-run 도구 생성

## 자동 진행 원칙

위 허용 작업은 사장님에게 매번 묻지 않고 바로 진행한다.

단, 작업 범위는 `D:\AI_COMPANY` 안으로 제한한다. 외부 서비스 실제 반영, 결제, 고객 발송, API 키 노출, 시스템 변경은 자동 진행 대상이 아니다.

## Codex에게 승인 전 금지할 일

- 스마트스토어 실제 로그인
- 스마트스토어 실제 상품 수정
- 네이버광고 실제 입찰가 변경
- 네이버광고 실제 광고비 변경
- SNS 실제 업로드
- SNS 실제 게시
- 고객에게 실제 메시지 발송
- 결제/주문/환불 처리
- API 키/비밀번호 출력
- 쿠키/세션 토큰 출력
- `.env` 내용 출력 또는 요약
- `D:\AI_COMPANY` 밖의 파일 수정
- 시스템 폴더 수정
- 대량 삭제
- 전체 PC 스캔
- 브라우저에서 로그인 세션 임의 사용

## 승인 단계

실행이 필요한 작업은 반드시 승인 파일을 만든다.

파일 위치:

```txt
09_approval
```

파일 예시:

```txt
APPROVAL_REQUIRED_2026-05-08_NAVER_ADS.md
```

내용:

```txt
작업명:
변경 대상:
변경 전:
변경 후:
예상 효과:
위험 요소:
되돌리는 방법:
승인 필요 여부:
```

## 권장 권한 모드

Codex CLI 실행 시:

```powershell
codex --cd D:\AI_COMPANY --ask-for-approval on-request
```

## 위험 작업 기준

아래 단어가 들어간 작업은 무조건 승인 필요:

- 삭제
- 대량 삭제
- 결제
- 주문
- 환불
- 업로드
- 게시
- 발송
- 입찰가
- 광고비
- 배포
- 로그인
- 쿠키
- 토큰
- 비밀번호
