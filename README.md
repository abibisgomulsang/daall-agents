# 11.AGENT — 다올에프엔에스 AI 에이전트 팀

주식회사 다올에프엔에스 / 아비비의고물상 브랜드의 AI 에이전트 운영 저장소.

## 현재 가동 중
- **수영** (`@suyeong_bot`) — 4역할 통합 에이전트
  - 네이버 광고 분석가 + 마케팅 매니저 + 데이터 분석가 + 사장님 비서

## 도구
- `tools/naver-analysis/` — DataLab(검색트렌드, 쇼핑인사이트) + 검색 API
- `tools/naver-ads/` — 네이버 검색광고 API (조회 전용)

## 역할 미정 placeholder
민지·도윤·지호·세아·하린·현우 — 추후 역할 할당 예정.
자세한 내용은 [CLAUDE.md](./CLAUDE.md) 참고.

## 운영 시스템
- openclaw (멀티 LLM 라우팅 + 텔레그램 봇)
- 워크스페이스: `~/.openclaw/ws-{이름}/`
- 설정: `~/.openclaw/openclaw.json`
