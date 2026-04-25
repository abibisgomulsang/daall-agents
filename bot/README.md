# 수영 봇 (openclaw 없는 순수 Node.js 버전)

`@suyeong_bot` 텔레그램 봇을 openclaw 없이 직접 실행합니다.

## 왜 만들었나
openclaw 의존하면서 발생한 문제들:
- Gemini 모델 스키마 호환성 (deprecated 모델, providers 형식 변동)
- `<thinking>` 태그가 응답에 그대로 노출
- gateway/pairing 에러, daemon 재시작 필요 빈번
- 매 모델 변경마다 daemon restart, config validate

이 봇은:
- ✅ 의존성 0 (Node.js 내장 모듈만)
- ✅ Gemini API 직접 호출 (function calling 포함)
- ✅ 도구(`tools/naver-analysis`, `tools/naver-ads`) 그대로 사용
- ✅ openclaw.json의 키를 그대로 가져와서 사용 (재입력 불필요)
- ✅ Windows 스케줄로 자동 시작 등록 가능

## 폴더 구조
```
bot/
├── bot.js                    ← 메인 (Telegram polling + Gemini + 도구 호출)
├── start.js                  ← openclaw.json 읽어서 env 세팅 후 bot.js 실행
├── start.cmd                 ← 수동 실행용 (Windows)
├── install-windows.ps1       ← Windows 자동 시작 등록
├── uninstall-windows.ps1     ← 등록 해제
└── README.md
```

## 요구사항
- Node.js 18+ (이미 설치되어 있음 — `node --version` 확인)
- `~/.openclaw/openclaw.json` 의 `env.vars`, `channels.telegram.accounts.suyeong_bot` 등이 설정되어 있을 것
  - 이미 다 셋업돼 있으므로 추가 입력 불필요

## 사용법

### 1) 수동 테스트 (먼저 정상 동작하는지 확인)
```cmd
cd C:\Users\black\OneDrive\바탕 화면\11.AGENT\bot
start.cmd
```
콘솔에 로그 뜨면서 봇 시작됨. 텔레그램에서 `@suyeong_bot` 한테 메시지 보내서 응답 확인.
종료: `Ctrl+C`

### 2) 자동 시작 등록 (운영)
PowerShell 관리자 권한 (선택) 으로:
```powershell
cd C:\Users\black\OneDrive\바탕 화면\11.AGENT\bot
.\install-windows.ps1
```
Windows 로그인 시마다 봇이 백그라운드(콘솔 안 보임)로 자동 시작.

로그: `~/.suyeong-bot/logs/bot.log`

### 3) 등록 해제
```powershell
.\uninstall-windows.ps1
```

## 명령어 (텔레그램에서)
- `/start`, `/help` — 도움말
- `/reset`, `/clear` — 대화 기록 초기화

## 도구 (Gemini function calling)
수영이 자동으로 호출:
- `naverSearchTrend` — DataLab 검색트렌드
- `naverShoppingTrend` — 쇼핑인사이트
- `naverSearch` — 네이버 검색결과
- `adsCampaigns` / `adsAdGroups` / `adsKeywords` — 캠페인/그룹/키워드 목록
- `adsStats` — 광고 성과 (impCnt, clkCnt, ctr, cpc, salesAmt, avrgRnk 등)
- `adsBalance` — 광고비 잔액
- `adsKeywordTool` — 키워드 검색량/경쟁도
- `adsEstimateBid` — 목표 순위 추정 입찰가

## openclaw 와 동시 실행 금지
같은 텔레그램 봇 토큰을 두 곳에서 polling 하면 충돌.
이 봇 켜기 전에:
```cmd
openclaw daemon stop
```
또는 openclaw 스케줄 작업 비활성화. (자세한 마이그레이션은 아래)

## 마이그레이션 (openclaw → bot)

1. **openclaw 데몬 정지**:
   ```cmd
   openclaw daemon stop
   ```
2. **openclaw 자동 시작 비활성화** (Windows):
   ```powershell
   schtasks /change /tn "OpenClaw Gateway" /disable
   ```
3. **이 봇 설치**:
   ```powershell
   cd bot
   .\install-windows.ps1
   schtasks /run /tn "Suyeong Bot"
   ```
4. **테스트**: 텔레그램에서 메시지 보내서 응답 확인
5. (롤백 필요 시) 위 1~2 역순 + `.\uninstall-windows.ps1`

## 설정 변경

### 모델 바꾸기
`~/.openclaw/openclaw.json` 의 `agents.list[suyeong].model` 또는 환경변수 `MODEL` 로:
- `gemini-flash-latest` (기본, 안정)
- `gemini-2.5-flash` 또는 `gemini-2.5-pro` (성능 ↑, 응답 느림)
- `gemini-2.5-flash-lite` (저렴/빠름)

봇 재시작 필요:
```cmd
schtasks /end /tn "Suyeong Bot"
schtasks /run /tn "Suyeong Bot"
```

### SOUL.md 수정
`~/.openclaw/ws-suyeong/SOUL.md` 직접 편집 또는
`agents/suyeong/SOUL.md` 편집 후 `~/.openclaw/ws-suyeong/SOUL.md` 로 복사.
봇 재시작 필요.

## 트러블슈팅

| 증상 | 확인 |
|---|---|
| 봇이 응답 안 함 | `~/.suyeong-bot/logs/bot.log` 확인 |
| "TELEGRAM_BOT_TOKEN 환경변수 필수" | `~/.openclaw/openclaw.json` 의 `channels.telegram.accounts.suyeong_bot.botToken` 확인 |
| "Gemini: ... 404" | 모델명이 deprecated. `MODEL=gemini-flash-latest` 로 변경 |
| 봇이 같은 메시지에 두 번 답함 | openclaw 데몬도 같이 돌고 있음. `openclaw daemon stop` |
| 도구 호출 실패 | `~/.openclaw/ws-suyeong/tools/` 폴더에 도구 있는지, `NAVER_*` 키 설정됐는지 |
