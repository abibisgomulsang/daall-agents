# GitHub 메모리 동기화 가이드

영상 #3 컨셉: 컴퓨터가 바뀌어도 우리 회사 메모리/스킬/지식 영구 보존.

## 한 번만 — 초기 설정 (10분)

### 1) GitHub 비공개(private) 저장소 만들기

1. https://github.com 로그인
2. 우상단 **+** → **New repository**
3. Repository name: `abibi-ai-company`
4. ⚠ **반드시 Private** 선택 (사장님 메모리 + 사업 정보)
5. **Create repository** 클릭

### 2) WSL에서 Git 설정 (한 번만)

Ubuntu 터미널에서:

```bash
git config --global user.name "사장님 이름"
git config --global user.email "daallfns@gmail.com"
```

### 3) D:\AI_COMPANY를 Git 저장소로 초기화

```bash
cd /mnt/d/AI_COMPANY
git init
git branch -M main
git remote add origin https://github.com/<사장님깃허브계정>/abibi-ai-company.git
```

### 4) GitHub 인증 (Personal Access Token)

비밀번호 대신 토큰 사용:

1. https://github.com/settings/tokens 접속
2. **Generate new token (classic)** 클릭
3. Note: `abibi-ai-company-sync`, Expiration: `No expiration`
4. Scopes: **repo** 체크
5. **Generate token** → 키 복사

키를 git credential helper에 저장:

```bash
git config --global credential.helper store
```

첫 push 시 username + token 입력하면 이후 자동 사용.

## 매일 — 백업하기 (10초)

```bash
bash /mnt/d/AI_COMPANY/scripts/sync_to_github.sh "오늘 광고 회의 결과 추가"
```

이 한 줄이 다음을 GitHub에 자동 push:

- `brain_packs/` — 도메인 지식
- `hermes_skills/` — Hermes 스킬 5종
- `11_memory/agents/` — 직원별 메모리
- `11_memory/goals/` — 목표 + KPI
- `docs/` — 모든 가이드
- `ai_company/` — 우리 회사 소스 코드
- `tests/` — 테스트

자동으로 **제외**되는 것 (보안):

- `.env` (API 키 + 토큰)
- `.venv/` (가상환경)
- `12_logs/` (로그)
- `11_memory/hermes/inbox.jsonl` 등 일시 데이터

## 컴퓨터 바뀌었을 때 — 복원 (5분)

새 컴퓨터에서:

```bash
cd D:\
git clone https://github.com/<사장님계정>/abibi-ai-company.git AI_COMPANY
cd D:\AI_COMPANY
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

그 다음 `.env` 파일만 새로 만들어서 API 키 채우면 끝.

WSL에서 Hermes도:

```bash
cp /mnt/d/AI_COMPANY/hermes_skills/* ~/.hermes/skills/ -r
```

## 자동 백업 설정 (선택)

매일 밤 23:00 자동 백업하려면:

```bash
crontab -e
```

마지막 줄에 추가:

```
0 23 * * * bash /mnt/d/AI_COMPANY/scripts/sync_to_github.sh "일일 자동 백업"
```

저장 후 종료.

## 안전 확인

- ✅ **Private 저장소**여야 합니다 — public이면 사장님 사업 정보 노출
- ✅ `.gitignore`가 자동으로 `.env` 차단 — API 키 절대 GitHub에 안 올라감
- ✅ inbox/outbox 같은 일시 파일은 제외 — 토큰 잔재 차단
- ❌ Public 저장소 절대 안 됨
- ❌ `.env` 파일을 GitHub에 절대 올리지 마세요

## 트러블슈팅

| 증상 | 해결 |
|---|---|
| `push rejected` | `git pull --rebase origin main` 먼저 |
| 인증 실패 | Personal Access Token 재발급 |
| 큰 파일 거부 (>100MB) | `12_logs/` 같은 큰 파일 `.gitignore`에 추가 |
| 한글 파일명 깨짐 | `git config --global core.quotepath false` |
