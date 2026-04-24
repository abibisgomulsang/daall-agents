# 다올에프엔에스 / 아비비의고물상 — AI 에이전트 팀

> 사장님의 AI 팀 전체 인덱스. 각 에이전트의 정체성·역할·운영 규칙은 하위 폴더의 CLAUDE.md를 참고.

## 회사
- **법인**: 주식회사 다올에프엔에스 (Daol FNS Co., Ltd.)
- **사업라인 1**: 산업용 컨베이어 시스템
- **사업라인 2**: 핸드메이드 고양이 장난감 — 브랜드 **아비비의고물상**
- **브랜드 고양이**: 아치, 일비, 단비 (이름 조합 → 아비비)
- **판매 채널**: 네이버 스마트스토어(주력), 쇼피, 토스 쇼핑, 오프라인
- **메이커**: 수경, 인용, 장원, 수민

## 에이전트 팀 (총 7명)

### 회사 업무 5인방 (기존)
| 이름 | 역할 | 모델 | 워크스페이스 |
|---|---|---|---|
| **민지** | 마케팅 매니저 | GPT-4o | `~/.openclaw/ws-minji` |
| **하린** | 경영 전략가 | Claude Opus | `~/.openclaw/ws-harin` |
| **현우** | 상품 기획자 | Claude Sonnet | `~/.openclaw/ws-hyunwoo` |
| **도윤** | 데이터 분석가 | Gemini Pro | `~/.openclaw/ws-doyun` |
| **지호** | 해외사업 (Shopee) | Gemini Pro | `~/.openclaw/ws-jiho` |

### 광고 운영 (신규)
| 이름 | 역할 | 모델 | 텔레그램 | 워크스페이스 |
|---|---|---|---|---|
| **수영 (Suyeong)** | 네이버 광고 옵티마이저 | Claude Opus 4.7 | `@suyoeng_bot` | `~/.openclaw/ws-suyeong` |

### 사장님 개인 비서 (신규)
| 이름 | 역할 | 모델 | 텔레그램 | 워크스페이스 |
|---|---|---|---|---|
| **세아 (Sea-ah)** | 개인 비서 (일정/할일/아이디어 평가) | Claude Sonnet | (미생성) | `~/.openclaw/ws-seah` |

## 폴더 구조
```
11.AGENT/
├── CLAUDE.md                  ← 이 파일 (전체 인덱스)
├── README.md
├── abibi-setup.sh             ← 5인방 셋업 (참고용)
├── suyeong-seah-setup.sh      ← 수영·세아 셋업 (참고용)
└── agents/
    ├── suyeong/
    │   ├── CLAUDE.md
    │   ├── SOUL.md
    │   └── README.md
    └── seah/
        ├── CLAUDE.md
        ├── SOUL.md
        └── README.md
```

## 운영 시스템
- **openclaw**: 멀티 LLM 라우팅 + 텔레그램 봇 채널
- 각 에이전트마다 별도 텔레그램 봇 (BotFather로 토큰 발급)
- 설정 파일: `~/.openclaw/openclaw.json`

## ⚠️ 셋업 스크립트 사용 시 주의
`abibi-setup.sh` 와 `suyeong-seah-setup.sh` 는 `cat > openclaw.json` 으로 **통째로 덮어쓰는** 구조입니다. 이미 운영 중인 openclaw.json이 있으면 그대로 돌리지 마세요 — 게이트웨이 토큰, API 키 등이 날아갑니다. 대신 필요한 섹션(`agents.list`, `bindings`, `channels.telegram.accounts`)만 수동 머지하세요.

## 신규 에이전트 추가 절차
1. `agents/{이름}/` 폴더에 CLAUDE.md, SOUL.md, README.md 작성
2. `~/.openclaw/ws-{이름}/SOUL.md` 생성
3. `openclaw.json`의 `agents.list`, `bindings`, `channels.telegram.accounts`에 항목 머지
4. 텔레그램 BotFather에서 봇 생성 → 토큰을 `accounts.{accountId}.botToken` 에 넣기
5. 이 CLAUDE.md 표 업데이트

## 변경 이력
- 2026-04-24: 수영(나린→개명) + 세아 추가, 폴더 구조화, 루트 CLAUDE.md 신설
