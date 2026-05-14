# CONNECT AI LAB 영상 영감 — 5가지 업그레이드 적용 보고서

## 사장님이 보여주신 영상 3편 핵심 → 우리 시스템 적용 결과

| 영상 컨셉 | 우리 시스템 적용 | 산출물 |
|---|---|---|
| **무료 로컬 AI + 엔터프라이즈 자동화** (영상 1) | 엔터프라이즈 자율 모드 | `ai_company/enterprise_mode.py` + CLI `enterprise-daily` |
| **에이전트 캐릭터화 + 스킬 고정** (영상 2 "코다리 부장") | 직원 별명·성격 보강 | `agents_data.js` 갱신 — 코퍼/릴리/픽셀/코다리/넘버스/쉴드/탐정/컷마스터 |
| **매트릭스 지식 주입** (영상 3) | 브레인 팩 시스템 | `brain_packs/` (4팩) + `ai_company/brain_pack.py` |
| **GitHub 메모리 동기화** (영상 3) | 백업 스크립트 + 가이드 | `scripts/sync_to_github.sh` + `docs/GITHUB_SYNC.md` |
| **목표 기반 자율 동작** (영상 1 "월 1천만원") | 목표(Goal) 시스템 + KPI | `ai_company/goals.py` + CLI `goal-set/goal-status` |

## 1) 브레인 팩 — 도메인 지식 자동 주입

영상의 "매트릭스 지식 주입"을 우리 식으로:

**신규 폴더 `brain_packs/`:**
```
marketing/KNOWLEDGE.md         — 후킹 2초 법칙, PAS 공식, 30자 헤드라인
cat_business/KNOWLEDGE.md       — 사장님 회사·고양이 성향 5분류·시즌 캠페인
naver_ads/KNOWLEDGE.md          — ROAS 회복 4단계, 낭비 키워드 5신호, 시간대 전략
video_editing/KNOWLEDGE.md      — 9:16 황금 구조, ffmpeg 명령, BGM 라이선스
```

**자동 주입:** `multi_agent_runtime.call_persona()`가 직원 호출 시 `brain_pack.augment_system_prompt()`를 거치게 만들었어요. 마케팅 AI는 자동으로 PAS 공식을 알고, 데이터 AI는 ROAS 회복 룰을 외운 채 답합니다.

**확인:**
```bash
python -m ai_company.main brain-status
```

## 2) 직원 캐릭터화

영상에서 본 "코다리 부장" 같은 친근한 캐릭터로 11명 직원 다 보강:

| key | 이름 | 별명 | 성격 |
|---|---|---|---|
| ceo | CEO | 민지 | 결단력, 짧고 명확 |
| marketing | 마케팅 | 코퍼 | 활기차고 임팩트 있는 카피 |
| sns | SNS | 릴리 | 트렌드 민감, 후킹 2초 |
| image | 이미지 | 픽셀 | 컬러 대비 본능 |
| smartstore | 스마트스토어 | 스토리 | 리뷰 광인 |
| naverads | 네이버광고 | 냅키 | 낭비 키워드 사냥꾼 |
| developer | Developer | **코다리** | 친절한 코딩 부장 ← 영상 그대로 |
| data | 데이터 | 넘버스 | 표·숫자만 신뢰 |
| review | 검수 | 쉴드 | 위험·저작권 1순위 |
| researcher | 리서처 | 탐정 | 경쟁사 5곳 30분 분석 |
| video | 비디오 | 컷마스터 | 1.5초 컷 룰 강박 |

직원 매트릭스 페이지 새로고침하면 각 카드에 별명·성격 보입니다.

## 3) 목표(Goal) 시스템

영상의 "월 1천만 원 목표" 컨셉:

**한 줄로 목표 설정:**
```bash
python -m ai_company.main goal-set --target "월 매출 1000만원" --deadline "2026-12-31"
```

→ KPI 자동 추출 (월 매출 KRW 10,000,000)

**현황 보기:**
```bash
python -m ai_company.main goal-status
```

`11_memory/goals/active.json`에 저장. 향후 가상 사무실 UI 상단에 진행률 바 자동 표시 가능.

## 4) 엔터프라이즈 자율 모드

영상의 "에이전트들이 알아서 일함" 컨셉을 dry-run 안전 가드 안에서:

```bash
python -m ai_company.main enterprise-daily --live
```

매일 1회 호출 시:
1. 활성 목표 + KPI 격차 분석
2. 부족한 KPI 회복 토픽으로 멀티 에이전트 회의 자동 소집
3. 결정된 액션 5개 추출
4. **09_approval 자동 생성** — 사장님 검토 대기
5. 보고서 `08_reports/enterprise_daily_*.md`

**자동 실행 안 함** — 사장님 승인 흐름 그대로 유지.

크론으로 매일 09:00 자동 실행도 가능:
```bash
crontab -e
# 0 9 * * * cd /mnt/d/AI_COMPANY && /mnt/d/AI_COMPANY/.venv/Scripts/python.exe -m ai_company.main enterprise-daily --live
```

## 5) GitHub 메모리 동기화

영상 #3의 "컴퓨터 바뀌어도 영구 백업" 컨셉:

**한 번만:**
- GitHub Private 저장소 생성
- `git init`, `git remote add origin ...`, Personal Access Token 발급

**매일 한 줄:**
```bash
bash /mnt/d/AI_COMPANY/scripts/sync_to_github.sh "오늘 광고 회의 결과 추가"
```

자동 백업: `brain_packs/`, `hermes_skills/`, `11_memory/agents/`, `11_memory/goals/`, `docs/`, `ai_company/`, `tests/`.

자동 제외 (보안): `.env`, `.venv/`, `12_logs/`, `inbox.jsonl/outbox.jsonl`.

가이드: `docs/GITHUB_SYNC.md`

## 사장님이 지금 바로 해보실 수 있는 것

### Hermes 채팅에서 (텔레그램 또는 hermes CLI)

```
나에 대해 뭐 알아? 회사·고양이·상품 다 말해줘.
```
→ 브레인 팩 + 마이그레이션된 메모리 둘 다 활용해서 풍성하게 답함.

```
고스틱 광고 후킹 문구 3개 만들어줘
```
→ 마케팅 AI(코퍼)가 자동으로 PAS 공식 적용해서 답함 (브레인 팩 영향).

### CLI에서

```powershell
cd D:\AI_COMPANY
.\.venv\Scripts\Activate.ps1

# 목표 설정
python -m ai_company.main goal-set --target "월 매출 500만원"

# 엔터프라이즈 일일 사이클 (KPI 회복 회의 자동 소집)
python -m ai_company.main enterprise-daily

# 브레인 팩 현황
python -m ai_company.main brain-status

# 활성 목표 확인
python -m ai_company.main goal-status
```

## 안전 가드

- 브레인 팩 주입 = 시스템 프롬프트에만 추가, 외부 호출 없음
- 목표 시스템 = 로컬 JSON 파일만, 외부 전송 없음
- 엔터프라이즈 모드 = 09_approval 자동 생성으로 사장님 검토 강제
- GitHub 동기화 = `.env`/`secret`/`logs` 자동 제외 (`.gitignore`)
- 외부 채널(스마트스토어/네이버광고/SNS) 자동 반영 — 끝까지 없음

## 다음 추천 작업

- 가상 사무실 페이지 상단에 **목표 진행률 바** 추가 (활성 목표 KPI 시각화)
- 매일 09:00 `enterprise-daily` 자동 cron 등록
- 영상 #3의 "에이전트 학습 평가" 시뮬 — 직원별 응답 품질 점수
- 브레인 팩 추가 — 인스타 알고리즘, 스마트스토어 SEO 등
