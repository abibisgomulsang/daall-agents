#!/bin/bash
# 네이버 검색광고 API 도구 설치 스크립트
set -e

echo "🔧 네이버 검색광고 API 도구 설치"

# Node.js 확인
if ! command -v node >/dev/null 2>&1; then
  echo "❌ Node.js 필요"
  exit 1
fi
echo "  ✅ $(node --version)"

# 환경변수 확인
WARN=0
[ -z "$NAVER_AD_CUSTOMER_ID" ] && { echo "  ⚠️  NAVER_AD_CUSTOMER_ID 미설정"; WARN=1; }
[ -z "$NAVER_AD_API_KEY" ]     && { echo "  ⚠️  NAVER_AD_API_KEY 미설정"; WARN=1; }
[ -z "$NAVER_AD_SECRET_KEY" ]  && { echo "  ⚠️  NAVER_AD_SECRET_KEY 미설정"; WARN=1; }
if [ $WARN -eq 1 ]; then
  echo "  ~/.openclaw/openclaw.json env.vars에 3개 키 등록 후 게이트웨이 재시작 필요"
fi

# ws-suyeong 으로 동기화
TARGET=~/.openclaw/ws-suyeong/tools/naver-ads
SOURCE_DIR=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$TARGET"
cp -f "$SOURCE_DIR/client.js" "$TARGET/"
cp -f "$SOURCE_DIR/cli.js" "$TARGET/"
cp -f "$SOURCE_DIR/README.md" "$TARGET/"
echo "  ✅ 도구 동기화: $TARGET"

# 자격증명 있으면 시범 호출
if [ -n "$NAVER_AD_CUSTOMER_ID" ] && [ -n "$NAVER_AD_API_KEY" ] && [ -n "$NAVER_AD_SECRET_KEY" ]; then
  echo ""
  echo "📡 시범 호출: 광고비 잔액..."
  node "$TARGET/cli.js" balance 2>&1 | head -10
fi

echo ""
echo "🎉 완료. 사용법: node $TARGET/cli.js --help"
