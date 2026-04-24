# 다올에프엔에스 / 아비비의고물상 — AI 에이전트 팀

> 사장님의 AI 팀 인덱스. 각 에이전트의 정체성·역할·운영 규칙은 하위 폴더의 CLAUDE.md를 참고.

## 회사
- **법인**: 주식회사 다올에프엔에스 (Daol FNS Co., Ltd.)
- **사업라인 1**: 산업용 컨베이어 시스템
- **사업라인 2**: 핸드메이드 고양이 장난감 — 브랜드 **아비비의고물상**
- **브랜드 고양이**: 아치, 일비, 단비 (이름 조합 → 아비비)
- **판매 채널**: 네이버 스마트스토어(주력), 쇼피, 토스 쇼핑, 오프라인
- **메이커**: 수경, 인용, 장원, 수민

## 현재 운영 중

| 이름 | 역할 (4역할 통합) | 모델 | 텔레그램 | 상태 |
|---|---|---|---|---|
| **수영 (Suyeong)** | 네이버 광고 분석가 + 마케팅 매니저 + 데이터 분석가 + 사장님 비서 | Gemini 2.5 Pro | `@suyeong_bot` | 🟢 가동 중 |

## 에이전트 placeholder (역할 미정)

원래 5인방으로 나눠 셋업했으나, 일단 **수영 한 명에 4역할 통합**. 아래 에이전트들은 이름만 남겨두고 역할은 추후 결정.

| 이름 | 원 역할 | 현재 상태 |
|---|---|---|
| 민지 | (구) 마케팅 매니저 — 수영에 통합 | 봇 미생성, 역할 미정 |
| 도윤 | (구) 데이터 분석가 — 수영에 통합 | 봇 미생성, 역할 미정 |
| 지호 | (구) 해외사업 (Shopee) | 봇 미생성, 역할 미정 |
| 하린 | (구) 경영전략가 | 봇 삭제됨, 역할 미정 |
| 현우 | (구) 상품기획자 | 봇 삭제됨, 역할 미정 |
| 세아 | (구) 개인 비서 — 수영에 통합 | 봇 미생성, 역할 미정 |

**나중에 사장님이 어떤 에이전트에 어떤 역할을 줄지 결정하실 예정.**

## 폴더 구조
```
11.AGENT/
├── CLAUDE.md                  ← 이 파일
├── README.md
├── abibi-setup.sh             ← (참고용) 옛 5인방 셋업 스크립트
├── suyeong-seah-setup.sh      ← (참고용) 옛 셋업 스크립트
├── tools/
│   ├── naver-analysis/        ← DataLab/검색 API 클라이언트
│   └── naver-ads/             ← 검색광고 API 클라이언트 (조회 전용)
└── agents/
    ├── suyeong/               ← 🟢 가동 중 (4역할 통합)
    │   ├── CLAUDE.md
    │   ├── SOUL.md
    │   └── README.md
    └── seah/                  ← placeholder (역할 미정)
        ├── CLAUDE.md
        ├── SOUL.md
        └── README.md
```

## 운영 시스템
- **openclaw**: 멀티 LLM 라우팅 + 텔레그램 봇 채널
- 워크스페이스: `~/.openclaw/ws-suyeong/`
- 설정: `~/.openclaw/openclaw.json`

## ⚠️ 셋업 스크립트 사용 시 주의
`abibi-setup.sh`, `suyeong-seah-setup.sh` 는 `cat > openclaw.json` 으로 **통째로 덮어쓰는** 구조. 이미 운영 중인 openclaw.json이 있으면 그대로 돌리지 마세요 — 게이트웨이 토큰, API 키 등이 날아갑니다. 대신 필요한 섹션만 수동 머지.

## 신규 에이전트 추가 / 역할 할당 절차
1. `agents/{이름}/` 폴더에 CLAUDE.md, SOUL.md, README.md 작성/수정
2. `~/.openclaw/ws-{이름}/SOUL.md` 동기화
3. `openclaw.json`의 `agents.list`, `bindings`, `channels.telegram.accounts`에 추가
4. 텔레그램 BotFather에서 봇 생성 → 토큰을 `accounts.{accountId}.botToken` 에 입력
5. `openclaw daemon restart`
6. 이 CLAUDE.md 표 업데이트

## 변경 이력
- 2026-04-24: 초기 셋업 (수영·세아 추가)
- 2026-04-24: 수영 역할을 분석/추천(옵션 C)으로 조정, 광고 API 도구 추가
- 2026-04-24: **수영을 4역할 통합 에이전트로 전환** (민지/도윤/지호/세아 역할 합침). 하린/현우 봇 삭제. 나머지 에이전트는 역할 미정 placeholder로 보관.
