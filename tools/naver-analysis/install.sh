#!/bin/bash
# 수영의 네이버 분석 도구 설치 스크립트
# 사장님이 텔레그램에서 "도구 설치해줘" 하면 수영이 이 스크립트를 실행

set -e

echo "🔧 네이버 분석 도구 설치 시작"

# 1) Node.js 확인
if ! command -v node >/dev/null 2>&1; then
  echo "❌ Node.js가 설치되어 있지 않습니다."
  echo "   https://nodejs.org 에서 LTS 버전을 설치한 후 다시 시도해주세요."
  exit 1
fi
NODE_VER=$(node --version)
echo "  ✅ Node.js $NODE_VER"

# 2) 환경변수 확인
WARN=0
[ -z "$NAVER_CLIENT_ID" ]     && { echo "  ⚠️  NAVER_CLIENT_ID 미설정"; WARN=1; }
[ -z "$NAVER_CLIENT_SECRET" ] && { echo "  ⚠️  NAVER_CLIENT_SECRET 미설정"; WARN=1; }
if [ $WARN -eq 1 ]; then
  echo ""
  echo "  ~/.openclaw/openclaw.json 의 env.vars 에 두 키 등록 후 gateway 재시작 필요:"
  echo "    \"NAVER_CLIENT_ID\":     \"...\","
  echo "    \"NAVER_CLIENT_SECRET\": \"...\""
  echo ""
fi

# 3) ws-suyeong 으로 도구 동기화
TARGET=~/.openclaw/ws-suyeong/tools/naver-analysis
SOURCE_DIR=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$TARGET"
cp -f "$SOURCE_DIR/client.js" "$TARGET/"
cp -f "$SOURCE_DIR/cli.js" "$TARGET/"
cp -f "$SOURCE_DIR/README.md" "$TARGET/"
echo "  ✅ 도구 복사 완료: $TARGET"

# 4) 설치 확인 (자격증명이 있을 때만 실제 호출)
if [ -n "$NAVER_CLIENT_ID" ] && [ -n "$NAVER_CLIENT_SECRET" ]; then
  echo ""
  echo "📡 시범 호출: 최근 7일간 '고양이 장난감' 검색 트렌드..."
  node "$TARGET/cli.js" trend "고양이 장난감" --start "$(date -d '-7 days' +%Y-%m-%d 2>/dev/null || date -v-7d +%Y-%m-%d)" --end "$(date +%Y-%m-%d)" 2>&1 | head -20
fi

echo ""
echo "🎉 설치 완료. 사용법: node $TARGET/cli.js --help"
