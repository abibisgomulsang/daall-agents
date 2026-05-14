# AI 회사 사용법 — 사장님용 요약

사장님은 결과만 확인하시면 됩니다. 가장 편한 진입점부터 안내합니다.

## A. 가장 쉬운 방법: 자연어 한 줄

```powershell
python -m ai_company.main nl --message "고스틱 광고 만들어줘"
```

자연어 한 문장만 넣으면:

1. 의도 분류 (회의/광고/분석/이미지/리서치 등 17개)
2. 모델 라우터 통과 (Codex / Claude / Gemini / Ollama / 이미지 AI)
3. CLI 명령 변환
4. 위험 키워드 자동 차단 + 승인 파일 자동 생성

까지 한 번에 처리하고 `08_reports/nl_command_plan_*.md`에 저장합니다.

실제 실행까지 가시면 `--execute`를 붙이세요. 위험 키워드(`입찰가`,
`광고비`, `업로드`, `결제` 등)는 `--execute` 있어도 차단됩니다.

```powershell
python -m ai_company.main nl --message "고스틱 광고 만들어줘" --execute
```

### 자연어 예시 모음

| 사장님 입력 | 자동 변환되는 명령 | 라우팅 결과 |
|---|---|---|
| 고스틱 광고 만들어줘 | `ad --product GOSTICK01` | Codex/이미지 AI |
| 고스틱 광고 효율 회의해줘 | `meeting --topic ... --with-router` | 회의 라우팅 |
| 네이버 광고 CSV 분석해줘 | `analyze-ads --csv data/naver_ads_sample.csv` | Codex |
| 릴스 썸네일 시안 | `image-templates --product GOSTICK01` | 이미지 AI |
| 고양이 MBTI 앱 경쟁사 조사 | `meeting --topic ... --with-router` | Gemini |
| 스마트스토어 상세페이지 검수 | `smartstore-fetch-dry-run` | Claude |
| 리뷰 200건 분류 | `meeting --topic ... --with-router` | Ollama |
| 네이버광고 입찰가 200원 올려줘 | **차단됨** | 09_approval 파일 자동 생성 |

## B. 텔레그램 e2e dry-run 전체 흐름 보기

```powershell
python -m ai_company.main e2e-dry-run --message "고스틱 광고 효율 회의해줘"
```

텔레그램 인바운드 → Hermes 기억 → nl_command → 라우터 → 회의 →
승인 → 사장님 알림까지 단계별 보고서가 `08_reports/e2e_dry_run_*.md`로
저장됩니다. **실제 텔레그램 호출 없음.**

## C. 직접 CLI도 가능

자연어 대신 정확한 명령을 쓰시고 싶으면.

| 명령 | 설명 |
|---|---|
| `meeting --topic "..." [--with-router]` | AI 회의. `--with-router`로 라우팅 카드 포함 |
| `ad --product GOSTICK01 [--with-router]` | 광고 패키지 (릴스/문구/이미지 지시서/검수) |
| `image-templates --product GOSTICK01 [--with-router]` | 이미지 광고 템플릿 3종 |
| `analyze-ads --csv data/naver_ads_sample.csv` | 네이버광고 CSV 분석 |
| `model-router --task "..."` | 모델 라우터 결정만 |
| `experiment-plan --topic "..."` | AI 회의 기반 실험 설계 |
| `dry-run-dashboard` | dry-run 통합 대시보드 갱신 |
| `approvals list` | 승인 대기 파일 목록 |
| `approvals decide --file ... --decision approved --reason "..."` | 승인/반려 기록 |
| `approval-priority-queue` | 위험도 기반 검토 우선순위 |

## D. 시뮬레이터 채팅 UI

브라우저에서 자연어로 명령하기.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_local_viewer.ps1
```

서버가 켜지면 브라우저로 `http://127.0.0.1:8765/06_apps/ai_office_simulator/index.html`
에 접속해 채팅창에 입력. 응답에 라우팅 카드(파란 보더)와 결과가 함께
표시됩니다.

## E. 결과는 어디에 저장되나

| 폴더 | 내용 |
|---|---|
| `08_reports/` | 각 명령 결과 보고서 (라우터/회의/광고/e2e 등) |
| `09_approval/` | 승인 대기 파일 (위험 명령이면 자동 생성) |
| `10_meetings/` | AI 회의 결과 마크다운 |
| `02_marketing/` | 광고 패키지 |
| `03_images/templates/` | 이미지 템플릿 JSON |
| `05_naver_ads/` | 네이버광고 분석 |
| `12_logs/` | 작업 활동 로그 |

## F. 안전 규칙 (자동 적용)

다음은 사장님 승인 없이는 **자동으로 차단**됩니다.

- 스마트스토어 / 네이버광고 / SNS **실제** 로그인 · 입찰변경 · 업로드 · 결제
- 위험 키워드 자동 검사: `삭제 / 결제 / 주문 / 환불 / 업로드 / 게시 / 발송 /
  입찰가 / 광고비 / 배포 / 로그인 / 쿠키 / 토큰 / 비밀번호`
- 차단 시 `09_approval/APPROVAL_REQUIRED_*.md` 파일이 자동 생성됨

승인 흐름:

```
위험 명령 입력
  ↓
09_approval 파일 자동 생성
  ↓
사장님이 approvals list로 확인
  ↓
approvals decide --file ... --decision approved --reason "..."
  ↓
이후 별도로 CLI 직접 실행 (자동 실행은 끝까지 없음)
```

## G. 한 번에 보는 핵심 흐름

```
사장님
   ↓ (자연어 메시지 / CLI)
[nl_command — 의도 분류 + 위험 검사]
   ↓
[모델 라우터 — Codex/Claude/Gemini/Ollama/이미지 AI 결정]
   ↓
[AI 회의 or 실행 준비물 생성]
   ↓
[보고서 + 승인 파일]
   ↓
사장님 확인 후 별도 승인 → 실제 실행
```

## H. 자주 쓰실 만한 한 줄

```powershell
# 빠른 회의
python -m ai_company.main nl --message "고스틱 광고 효율 회의해줘" --execute

# 광고 + 이미지 + 검수 한방
python -m ai_company.main ad --product GOSTICK01 --with-router

# 네이버광고 효율 분석
python -m ai_company.main nl --message "네이버 광고 분석해줘" --execute

# 승인 대기 파일 한 번에 보기
python -m ai_company.main approvals list

# 위험도 우선 검토
python -m ai_company.main approval-priority-queue
```

---

자세한 모듈별 문서:

- `docs/MODEL_ROUTER.md` — 모델 라우터 매핑/안전 규칙
- `docs/NL_COMMAND.md` — 자연어 의도 17개 매핑표
- `AGENTS.md` — AI 직원 구조와 자동 진행 허용 범위
- `CODEX_SAFE_RULES.md` — 안전 운영 규칙
- `TASK_BOARD.md` — 진행/완료 작업 보드
