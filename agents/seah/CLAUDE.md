# 세아 (Sea-ah) — 역할 미정 placeholder

> 현재 활성화되지 않음. 사장님의 비서 역할은 수영(@suyeong_bot)에 통합됨.

## 상태
- 텔레그램 봇: 미생성
- 워크스페이스: 미생성
- 역할: **미정** (추후 사장님이 결정)

## 변경 이력
- 2026-04-24: 처음에는 사장님 개인 비서(일정·할일·아이디어 평가)로 설계됨
- 2026-04-24: 비서 역할이 수영에 통합되면서 placeholder 상태로 전환

## 활성화 절차
사장님이 새 역할 할당하실 때:
1. SOUL.md / CLAUDE.md / README.md를 새 역할로 재작성
2. `~/.openclaw/ws-seah/` 워크스페이스 생성 + SOUL 동기화
3. BotFather에서 봇 생성 → 토큰 발급
4. `~/.openclaw/openclaw.json`의 `agents.list` / `bindings` / `channels.telegram.accounts`에 항목 추가
5. `openclaw daemon restart`
6. 루트 CLAUDE.md 표 업데이트
