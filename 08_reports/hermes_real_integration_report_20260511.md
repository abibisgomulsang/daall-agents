# 진짜 Hermes Agent 통합 — 설치 패키지 + 마이그레이션 계획

## 1. 사장님이 결정하신 방향

> "1번으로 하자" — Nous Research의 진짜 Hermes Agent 설치 + 우리 AI 회사를 그 스킬로 등록

## 2. 제가 자동으로 준비해 둔 것

| 파일 | 역할 |
|---|---|
| `docs/HERMES_SETUP.md` | WSL2 + Hermes Agent 설치 + 첫 메시지까지 사장님용 가이드 |
| `hermes_skills/abibi-meeting/SKILL.md` | 멀티 에이전트 3라운드 회의 스킬 |
| `hermes_skills/abibi-ad-package/SKILL.md` | 상품 광고 패키지 스킬 |
| `hermes_skills/abibi-video-edit/SKILL.md` | 비디오 + Premiere 임포트 스킬 |
| `hermes_skills/abibi-analyze-ads/SKILL.md` | 네이버광고 CSV 분석 스킬 |
| `hermes_skills/abibi-boss-command/SKILL.md` | 7단계 풀 파이프라인 스킬 |
| `scripts/install_hermes_skills.sh` | WSL 안에서 한 줄 실행 → 위 5개를 `~/.hermes/skills/`로 자동 설치 |
| `ai_company/hermes_runtime.py` | **[DEPRECATED]** 헤더 추가, 진짜 Hermes 도입 후 단계적 제거 예정 |

각 스킬 SKILL.md는 **Hermes가 자동으로 인식**하는 마크다운 + YAML frontmatter
형식입니다. 사장님이 텔레그램에 "고스틱 광고 만들어줘" 보내시면 Hermes가:

1. 의도 분석 → `abibi-ad-package` 스킬 선택
2. SKILL.md의 동작 섹션을 보고 `/mnt/d/AI_COMPANY/.venv/Scripts/python.exe -m ai_company.main ad ...` 호출
3. 결과 보고서 경로를 텔레그램으로 회신

## 3. 사장님이 하실 일 (20~30분, 한 번만)

`docs/HERMES_SETUP.md` 가이드 그대로:

1. PowerShell 관리자: `wsl --install` → 재부팅
2. Ubuntu 안에서:
   ```bash
   sudo apt update && sudo apt install -y python3 python3-pip curl git
   curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
   source ~/.bashrc
   hermes setup
   ```
3. 우리 회사 스킬 설치:
   ```bash
   bash /mnt/d/AI_COMPANY/scripts/install_hermes_skills.sh
   ```
4. 첫 테스트:
   ```bash
   hermes
   > 고스틱 광고 만들어줘
   ```

설치 끝나시면 `hermes --version` 결과 한 줄만 알려주시면 됩니다.

## 4. 사장님 설치 완료 후 제가 자동으로 진행할 작업

1. **`hermes_runtime.py` 정식 deprecate** — 호출하는 모든 곳에서 제거 또는 어댑터화
2. **가상 사무실 ↔ Hermes 메모리 연동**
   - `/api/hermes/recent` 엔드포인트 → `~/.hermes/sessions/` 의 진짜 세션 데이터 폴링
   - "🔔 사장님 텔레그램" 활동 로그가 진짜 Hermes 활동에서 옴
3. **boss_pipeline 1단계 _hermes_step()** — Hermes 메모리 폴더에서 선호/세션 데이터 읽도록
4. **CLI 정리** — `hermes-run`, `hermes-test`는 deprecated 표시, 사장님이 사용 안 함

## 5. 통합 후 흐름

```
사장님 텔레그램
   ↓
[Hermes Agent (WSL2, 24시간 실행)]
   ├─ 메시지 수신 + 메모리 자동 큐레이션
   ├─ 의도 분석 → abibi-* 스킬 자동 선택
   ├─ 우리 회사 CLI (/mnt/d/AI_COMPANY/.venv/Scripts/python.exe ...) 호출
   ├─ 결과를 텔레그램으로 회신 (+ Discord/Slack 가능)
   └─ 스킬 사용 패턴 학습 → 자기개선
   ↓
[가상 사무실 페이지 (브라우저)]
   └─ Hermes 세션 폴링 → "🔔 사장님 텔레그램" 실시간 표시
```

## 6. 안전 확인

- Hermes는 **WSL2 가상 환경 안**에서만 동작 — Windows 본체 영향 없음
- 우리 D:\AI_COMPANY 코드는 그대로 — Hermes는 `/mnt/d/AI_COMPANY` 마운트로 읽기만
- 스킬은 CLI 호출만 — 우리 09_approval 흐름 그대로 작동
- 외부 채널 자동 반영(스마트스토어/네이버광고/SNS) — 끝까지 없음
- 위험 키워드 자동 차단 — 우리 nl_command + Hermes 자체 안전 가드 이중

## 7. 비용

- WSL2: **무료** (Windows 기본 기능)
- Hermes Agent: **오픈소스, 무료**
- LLM 호출: 사장님 기존 API 키 (Claude/OpenAI) 그대로 사용 — 비용 캡 `usage_caps` 그대로 동작
- 텔레그램 봇: **무료**

## 8. 다음 추천 작업 (설치 후)

- 사장님이 `hermes gateway setup` + `hermes gateway start` 로 텔레그램 게이트웨이 켜기
- Hermes의 **cron 스케줄러**로 매일 09:00 광고 효율 자동 분석 보고
- Hermes의 **자동 스킬 생성** — 사장님이 자주 하는 패턴은 Hermes가 알아서 스킬로 등록
- 가상 사무실 ↔ Hermes 양방향 연결 (제가 자동 진행)
