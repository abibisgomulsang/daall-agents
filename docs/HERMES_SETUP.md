# Hermes Agent 설치 가이드 (사장님용)

## 큰 그림

```
Windows (D:\AI_COMPANY ← 우리 회사 그대로 있음)
   │
   ├─ WSL2 (Ubuntu, 리눅스 가상환경)
   │     └─ Hermes Agent 설치
   │         ├─ 텔레그램/Discord/Slack 게이트웨이
   │         ├─ 우리 회사 스킬 5종 (제가 미리 패키징 완료)
   │         └─ 메모리/세션/스킬 자기개선
   │
   └─ 가상 사무실 페이지 (Hermes 세션 폴링으로 연결 예정)
```

총 소요 시간: **약 20~30분** (WSL 설치가 가장 오래 걸림)

## 1단계 — WSL2 설치 (10분)

**PowerShell을 관리자 권한으로** 열고:

```powershell
wsl --install
```

자동으로 Ubuntu 22.04 또는 24.04가 설치됩니다. **재부팅 한 번 필요**.

재부팅 후 자동으로 Ubuntu 터미널이 뜨면서 사용자 이름/비밀번호를 묻습니다. **사장님 평소 쓰는 ID·비밀번호** 입력하세요.

확인:

```powershell
wsl --status
# Default Version: 2 가 보여야 함
```

## 2단계 — WSL 안에서 기본 도구 설치 (5분)

Ubuntu 터미널 열고 (시작 메뉴에서 "Ubuntu" 검색):

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv curl git build-essential
```

비밀번호 한 번 더 묻습니다.

## 3단계 — Hermes Agent 설치 (5분)

같은 Ubuntu 터미널에서:

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

설치 완료 후 셸 리로드:

```bash
source ~/.bashrc
hermes --version
# v2026.x.x 같은 버전이 보이면 성공
```

## 4단계 — Hermes 초기 설정 (5분)

```bash
hermes setup
```

대화식 설정이 시작됩니다. 다음 항목을 답하시면 됩니다.

| 질문 | 답 |
|---|---|
| LLM provider | `anthropic` (또는 `openai`, `openrouter` 등 사장님 선호) |
| API 키 | 이미 D:\AI_COMPANY\\.env 에 있는 키 그대로 |
| Telegram bot? | yes |
| Telegram bot token | `.env`의 `TELEGRAM_BOT_TOKEN` |
| Owner chat id | `.env`의 `TELEGRAM_OWNER_CHAT_ID` |
| Personality | 기본 또는 사장님 톤 적용 |

`OpenClaw에서 마이그레이션?` 같은 게 뜨면 **no** (우리는 처음 설치).

## 5단계 — 우리 AI 회사 스킬 설치 (1분)

설치 끝나면 **Ubuntu 터미널**에서:

```bash
# D:\AI_COMPANY 가 WSL에서는 /mnt/d/AI_COMPANY 로 보입니다
bash /mnt/d/AI_COMPANY/scripts/install_hermes_skills.sh
```

성공하면 다음과 같이 출력됩니다:

```
✅ 5개 스킬 설치 완료:
  - abibi-meeting           (AI 회의)
  - abibi-ad-package        (광고 패키지)
  - abibi-video-edit        (비디오 + Premiere)
  - abibi-analyze-ads       (네이버광고 분석)
  - abibi-boss-command      (7단계 풀 파이프라인)
```

## 6단계 — 첫 메시지 테스트

### 터미널에서

```bash
hermes
# Hermes 채팅창이 열리면:
> 우리 회사 스킬 뭐 있어?
> 고스틱 광고 만들어줘
```

Hermes가 `abibi-ad-package` 스킬을 자동으로 골라서 우리 AI 회사 CLI를 호출하고, 결과 보고서 경로를 알려줍니다.

### 텔레그램에서

`hermes gateway start` 명령으로 게이트웨이를 띄우고, 텔레그램 봇한테 한국어로 말 거시면 됩니다. **이때부터 사장님은 텔레그램만 쓰셔도 회사 전체가 돌아갑니다.**

## 트러블슈팅

| 증상 | 해결 |
|---|---|
| `wsl --install` 권한 오류 | PowerShell을 "관리자 권한으로 실행" 했는지 확인 |
| Ubuntu 안 뜸 | 재부팅 후 시작 메뉴에서 "Ubuntu" 직접 실행 |
| `hermes: command not found` | `source ~/.bashrc` 한 번 실행 |
| `curl install.sh` 실패 | 다시 시도 또는 가이드의 "Quick Install" 수동 단계 따라하기 |
| 텔레그램 응답 없음 | `hermes doctor` 로 진단, `.env` 의 봇 토큰/chat id 재확인 |
| 우리 회사 스킬 호출 시 Python 못 찾음 | WSL 안에서 `ls /mnt/d/AI_COMPANY/.venv/Scripts/python.exe` 가 보이는지 확인 (Windows의 가상환경 그대로 사용) |

## 안전 확인

- Hermes는 사장님 PC의 **WSL2 가상 리눅스 안에서만 동작**합니다 — Windows 본체에 영향 없음
- 우리 D:\AI_COMPANY 폴더는 그대로 — Hermes가 `/mnt/d/AI_COMPANY`로 마운트해서 읽기만
- 스킬 호출 → 우리 회사 CLI 호출 → 09_approval 흐름 → 사장님 승인 후 실행은 **변함 없음**
- 외부 SNS/네이버광고/스마트스토어 자동 반영은 끝까지 없음

## 설치 끝나면 알려주세요

`hermes --version` 결과 한 줄만 알려주시면 제가 다음 단계 (가상 사무실 ↔ Hermes 메모리 연동, 기존 미니 봇 제거)를 자동으로 진행하겠습니다.
