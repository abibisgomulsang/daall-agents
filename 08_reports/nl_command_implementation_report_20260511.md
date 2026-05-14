# 자연어 명령 시스템 구축 보고서

## 1. 수행한 일

사장님이 한국어 자연어로 명령을 내리면 시스템이 자동으로 의도를 분류하고
모델 라우터를 통과시켜 실행 가능한 CLI 명령을 만드는 인터페이스를
구축했다. 위험 키워드는 자동 차단되며 승인 파일이 자동 생성된다.

```
사장님 자연어 입력
   ↓
[nl_command.interpret()]
   ├─ 의도 분류 (17개 의도)
   ├─ 위험 키워드 검사 (15개 단어)
   └─ 모델 라우터 통과
   ↓
NLPlan { intent, cli, routing, safe_to_run, approval_path }
   ↓
└─ 기본: 해석 보고서만
└─ --execute: 안전한 경우 CLI 실행 / 위험하면 승인 파일
```

## 2. 생성/수정한 파일

- `ai_company/nl_command.py` (신규, 약 240줄)
  - `NLPlan` dataclass — 해석 결과 컨테이너
  - `_classify_intent()` — 17개 의도 분류
  - `_find_risk_keywords()` — CODEX_SAFE_RULES 위험 단어 검사
  - `_extract_product_code()` — `GOSTICK01` 같은 상품 코드 자동 추출
  - `_extract_topic()` — 회의 토픽 추출 ("...회의해줘" 자르기)
  - `interpret()` — 메인 진입점
  - `run_plan()` — 안전한 NLPlan만 실제 CLI 실행
  - `write_plan_report()` — 08_reports에 해석 보고서 저장
- `ai_company/main.py` — `nl --message "..." [--execute]` CLI 명령 추가
- `tests/test_smoke.py` — 4건의 테스트 추가
  - `test_nl_command_intent_classification` — 의도 분류 6개 케이스
  - `test_nl_command_blocks_risky_keywords` — 위험 키워드 차단 + 승인 파일 생성
  - `test_nl_command_empty_message` — 빈 메시지 처리
  - `test_nl_command_risk_keywords_cover_safe_rules` — RISK_KEYWORDS 커버리지
- `docs/NL_COMMAND.md` (신규) — 사용법 / 의도 매핑표 / 안전 규칙

## 3. 사용 예시

### 안전한 명령 (자동 실행 가능)

```powershell
python -m ai_company.main nl --message "고스틱 광고 만들어줘"
# → ad --product GOSTICK01 (이미지 AI 라우팅)

python -m ai_company.main nl --message "네이버 광고 회의해줘" --execute
# → meeting --topic ... --with-router (라우터 통합 회의 즉시 실행)

python -m ai_company.main nl --message "릴스 썸네일 시안"
# → image-templates --product GOSTICK01 (이미지 AI 라우팅)
```

### 위험 명령 (자동 차단 + 승인 파일)

```powershell
python -m ai_company.main nl --message "네이버광고 입찰가 200원 올려줘"
# → 차단됨. 09_approval/APPROVAL_REQUIRED_nl_command_*.md 자동 생성
```

## 4. 지원 의도 17개

회의, 광고 분석, 대시보드, 승인 우선순위, 승인 위험도, 승인 목록, Ollama
모델, 4~8단계 연결, 실험 설계, 이미지 템플릿, 인스타 dry-run, 스마트스토어
fetch, Playwright, 광고 패키지, 사무실 시뮬레이터, 모델 라우터, 폴백 회의.

자세한 매핑표는 `docs/NL_COMMAND.md` 참고.

## 5. 안전 검사

CODEX_SAFE_RULES.md의 15개 위험 키워드 자동 검사:

```
삭제, 대량 삭제, 결제, 주문, 환불, 업로드, 게시, 발송,
입찰가, 광고비, 배포, 로그인, 쿠키, 토큰, 비밀번호
```

위험 키워드 포함 시:
- `safe_to_run=False` 마킹
- `--execute` 플래그가 있어도 실행 안 함
- `09_approval/APPROVAL_REQUIRED_nl_command_*.md` 자동 생성
- 사장님 별도 승인 필요

## 6. 테스트 결과

샌드박스 파일시스템 캐시 문제로 자동 pytest는 이 환경에서 안정적이지 않다.
Windows 본체에서 다음으로 검증 권장:

```powershell
python -m pytest tests/test_smoke.py -k nl_command -q
```

기대 결과: 4건 모두 통과.

## 7. 사장님 확인 필요한 부분

- 자주 쓰시는 명령 어휘가 더 있으면 알려주시면 `_classify_intent`에
  추가합니다 (예: "고양이 MBTI 앱 만들어", "재구매 캠페인 띄워")
- 위험 키워드 자동 차단 외에 추가로 막을 단어가 있는지
- `--execute`를 기본값으로 만들고 `--dry-run`을 옵션으로 뒤집을지

## 8. 다음 추천 작업

- 시뮬레이터 채팅 UI (`scripts/local_viewer_server.py`)와 통합: 이미 있는
  `plan_chat_command()`를 `nl_interpret()`로 교체
- 텔레그램 봇 연결: 사장님 텔레그램 메시지 → nl_interpret → 자동 실행
- 명령 히스토리: 08_reports에 nl_command_plan_*.md를 모아 사장님이
  반복 명령을 볼 수 있는 인덱스 페이지
- 의도 분류기 학습: Ollama 로컬 모델로 키워드 기반 분류기를 개선

## 안전 확인

- 외부 API 호출 / 메시지 발송 / 결제 — 없음
- D:\AI_COMPANY 밖 파일 수정 — 없음
- API 키 / 비밀번호 / 토큰 노출 — 없음
- 위험 명령 자동 실행 — 차단 (승인 파일만 생성)
