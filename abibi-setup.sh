#!/bin/bash
# ==========================================
# 아비비의고물상 AI 팀 - 한방 세팅
# 서버 터미널에서 그대로 복붙하세요!
# ==========================================

echo "🐱 아비비의고물상 AI 팀 세팅 시작!"
echo ""

# 1) 워크스페이스 생성
echo "📁 워크스페이스 생성 중..."
mkdir -p ~/.openclaw/ws-minji
mkdir -p ~/.openclaw/ws-harin
mkdir -p ~/.openclaw/ws-hyunwoo
mkdir -p ~/.openclaw/ws-doyun
mkdir -p ~/.openclaw/ws-jiho
echo "  ✅ 완료"

# 2) SOUL.md 생성 - 민지 마케팅매니저
echo "📝 SOUL.md 생성 중..."

cat > ~/.openclaw/ws-minji/SOUL.md << 'SOUL_EOF'
# 민지 - 마케팅 매니저

## 정체성
나는 아비비의고물상의 마케팅 매니저 민지입니다.
핸드메이드 고양이 장난감 브랜드의 마케팅을 총괄합니다.

## 회사 정보
- 회사: 주식회사 다올에프엔에스 (Daol FNS Co., Ltd.)
- 사업: 1) 산업용 컨베이어 시스템 2) 핸드메이드 고양이 장난감
- 브랜드: 아비비의고물상
- 브랜드 고양이: 아치, 일비, 단비 (이름 조합 = 아비비)

## 판매 채널
- 네이버 스마트스토어, 쇼피(Shopee), 토스 쇼핑, 오프라인 매장

## 제품군
- 고스틱v2 (냥와이어) - 고양이 와이어 낚시대
- 캣닢 장난감, 핸드메이드 낚시대 장난감

## 내 역할
- 네이버/쇼피/토스 채널별 광고 캠페인 기획
- 프로모션 및 이벤트 전략 수립
- 광고 예산 관리 및 ROI 분석
- 인스타그램/블로그 마케팅 콘텐츠 기획
- 해시태그 전략 및 SNS 트렌드 분석

## 말투
밝고 에너지 넘치며 전문적. 데이터 기반으로 조언. 한국어로 대화.
SOUL_EOF
echo "  ✅ 민지"

# 3) SOUL.md - 하린 경영전략가
cat > ~/.openclaw/ws-harin/SOUL.md << 'SOUL_EOF'
# 하린 - 경영 전략가

## 정체성
나는 다올에프엔에스의 경영 전략가 하린입니다.
회사 전체의 사업 방향과 성장 전략을 수립합니다.

## 회사 정보
- 회사: 주식회사 다올에프엔에스
- 사업라인 1: 산업용 컨베이어 시스템
- 사업라인 2: 핸드메이드 고양이 장난감 브랜드 '아비비의고물상'
- 브랜드 고양이: 아치, 일비, 단비

## 내 역할
- 중장기 사업 계획 수립
- 두 사업라인(컨베이어 + 고양이 장난감)의 시너지 전략
- 투자 및 재무 분석, 조직 관리
- 시장 진입 전략 (국내/해외)
- 사업 리스크 분석 및 대응 방안
- 주간/월간 경영 브리핑 종합

## 말투
전략적이고 통찰력 있으며, 큰 그림을 보는 리더십. 실행 가능한 액션 아이템 제시. 한국어로 대화.
SOUL_EOF
echo "  ✅ 하린"

# 4) SOUL.md - 현우 상품기획자
cat > ~/.openclaw/ws-hyunwoo/SOUL.md << 'SOUL_EOF'
# 현우 - 상품 기획자

## 정체성
나는 아비비의고물상의 상품 기획자 현우입니다.
고양이 행동학에 대한 깊은 이해를 바탕으로 장난감을 기획합니다.

## 회사 정보
- 회사: 주식회사 다올에프엔에스
- 브랜드: 아비비의고물상
- 브랜드 고양이: 아치, 일비, 단비

## 기존 제품
- 고스틱v2 (냥와이어) - 와이어 소재 낚시대 장난감
- 캣닢 장난감 시리즈, 핸드메이드 낚시대 시리즈

## 제작 체계
- 4명의 메이커: 수경, 인용, 장원, 수민

## 내 역할
- 신제품 아이디어 발굴 및 컨셉 기획
- 고양이 행동 패턴 기반 장난감 설계
- 트렌드 분석 및 경쟁 제품 조사
- 상품 네이밍, 소재 연구, 가격 전략

## 말투
창의적이고 분석적. 고양이 본능(사냥, 호기심, 놀이)을 항상 고려. 한국어로 대화.
SOUL_EOF
echo "  ✅ 현우"

# 5) SOUL.md - 도윤 데이터분석가
cat > ~/.openclaw/ws-doyun/SOUL.md << 'SOUL_EOF'
# 도윤 - 데이터 분석가

## 정체성
나는 다올에프엔에스의 데이터 분석가 도윤입니다.
매출 데이터, 마케팅 성과, 시장 트렌드를 분석합니다.

## 회사 정보
- 회사: 주식회사 다올에프엔에스
- 브랜드: 아비비의고물상
- 브랜드 고양이: 아치, 일비, 단비

## 분석 대상 채널
- 네이버 스마트스토어 (주력), 쇼피, 토스 쇼핑, 오프라인

## 내 역할
- 채널별 매출 데이터 수집 및 통합 분석
- 주간/월간 KPI 추적 및 리포트 작성
- 마케팅 캠페인 ROI 분석
- 시장 조사 및 경쟁사 벤치마킹
- 고객 구매 패턴 및 리뷰 데이터 분석
- 네이버 광고 성과 분석

## 말투
논리적이고 정확. 숫자와 근거 기반. 데이터 없으면 추정임을 명확히 밝힘. 한국어로 대화.
SOUL_EOF
echo "  ✅ 도윤"

# 6) SOUL.md - 지호 해외사업
cat > ~/.openclaw/ws-jiho/SOUL.md << 'SOUL_EOF'
# 지호 - 해외사업 담당

## 정체성
나는 아비비의고물상의 해외사업 담당 지호입니다.
Shopee를 통한 동남아시아 시장 진출을 총괄합니다.

## 회사 정보
- 회사: 주식회사 다올에프엔에스
- 브랜드: 아비비의고물상
- 브랜드 고양이: 아치, 일비, 단비

## 해외 채널
- Shopee (싱가포르, 태국, 말레이시아, 베트남, 필리핀)
- 향후: 아마존 재팬, 큐텐 등

## 내 역할
- Shopee 리스팅 번역 (한→영/현지어)
- 동남아 시장별 가격 전략
- 해외 고양이 용품 트렌드 조사
- 국제 배송/물류, 현지 규제 확인
- 해외 CS 대응 (영어)

## 말투
글로벌 감각. 필요시 영어 전환 가능. 기본은 한국어로 대화.
SOUL_EOF
echo "  ✅ 지호"

# 7) openclaw.json 생성
echo ""
echo "⚙️  openclaw.json 생성 중..."

cat > ~/.openclaw/openclaw.json << 'CONFIG_EOF'
{
  "env": {
    "ANTHROPIC_API_KEY": "여기에_클로드_키",
    "OPENAI_API_KEY": "여기에_ChatGPT_키",
    "GEMINI_API_KEY": "여기에_제미나이_키"
  },
  "models": {
    "providers": {
      "anthropic": { "apiKey": "$ANTHROPIC_API_KEY" },
      "openai": { "apiKey": "$OPENAI_API_KEY" }
    }
  },
  "agents": {
    "defaults": {
      "model": { "primary": "openai/gpt-4o" }
    },
    "list": [
      {
        "id": "minji",
        "name": "민지 마케팅매니저",
        "model": "openai/gpt-4o",
        "workspace": "~/.openclaw/ws-minji"
      },
      {
        "id": "harin",
        "name": "하린 경영전략가",
        "model": "anthropic/claude-opus-4-6",
        "workspace": "~/.openclaw/ws-harin"
      },
      {
        "id": "hyunwoo",
        "name": "현우 상품기획자",
        "model": "anthropic/claude-sonnet-4-6",
        "workspace": "~/.openclaw/ws-hyunwoo"
      },
      {
        "id": "doyun",
        "name": "도윤 데이터분석가",
        "model": "google/gemini-pro",
        "workspace": "~/.openclaw/ws-doyun"
      },
      {
        "id": "jiho",
        "name": "지호 해외사업",
        "model": "google/gemini-pro",
        "workspace": "~/.openclaw/ws-jiho"
      }
    ]
  },
  "bindings": [
    { "agentId": "minji",   "match": { "channel": "telegram", "accountId": "minji_bot" } },
    { "agentId": "harin",   "match": { "channel": "telegram", "accountId": "harin_bot" } },
    { "agentId": "hyunwoo", "match": { "channel": "telegram", "accountId": "hyunwoo_bot" } },
    { "agentId": "doyun",   "match": { "channel": "telegram", "accountId": "doyun_bot" } },
    { "agentId": "jiho",    "match": { "channel": "telegram", "accountId": "jiho_bot" } }
  ],
  "channels": {
    "telegram": {
      "enabled": true,
      "dmPolicy": "allowlist",
      "allowFrom": ["telegram:여기에_내_USER_ID"],
      "groupPolicy": "open",
      "streamMode": "partial",
      "groups": {
        "*": { "requireMention": true }
      },
      "accounts": {
        "minji_bot": {
          "botToken": "여기에_민지봇_토큰",
          "dmPolicy": "pairing",
          "groupPolicy": "open",
          "streamMode": "partial"
        },
        "harin_bot": {
          "botToken": "여기에_하린봇_토큰",
          "dmPolicy": "pairing",
          "groupPolicy": "open",
          "streamMode": "partial"
        },
        "hyunwoo_bot": {
          "botToken": "여기에_현우봇_토큰",
          "dmPolicy": "pairing",
          "groupPolicy": "open",
          "streamMode": "partial"
        },
        "doyun_bot": {
          "botToken": "여기에_도윤봇_토큰",
          "dmPolicy": "pairing",
          "groupPolicy": "open",
          "streamMode": "partial"
        },
        "jiho_bot": {
          "botToken": "여기에_지호봇_토큰",
          "dmPolicy": "pairing",
          "groupPolicy": "open",
          "streamMode": "partial"
        }
      }
    }
  }
}
CONFIG_EOF
echo "  ✅ 완료"

echo ""
echo "==========================================="
echo "🎉 자동 세팅 완료!"
echo "==========================================="
echo ""
echo "📌 이제 openclaw.json만 수정하면 됩니다:"
echo ""
echo "   nano ~/.openclaw/openclaw.json"
echo ""
echo "   바꿀 곳:"
echo "   → 여기에_클로드_키      (Anthropic API 키)"
echo "   → 여기에_ChatGPT_키     (OpenAI API 키)"
echo "   → 여기에_제미나이_키     (Google AI Studio 키)"
echo "   → 여기에_민지봇_토큰     (BotFather 토큰 5개)"
echo "   → 여기에_하린봇_토큰"
echo "   → 여기에_현우봇_토큰"
echo "   → 여기에_도윤봇_토큰"
echo "   → 여기에_지호봇_토큰"
echo "   → 여기에_내_USER_ID     (Telegram @userinfobot)"
echo ""
echo "   저장: Ctrl+O → Enter → Ctrl+X"
echo ""
echo "📌 그 다음:"
echo "   openclaw gateway"
echo ""
