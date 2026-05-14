#!/usr/bin/env bash
# 아비비 AI 회사 → Hermes Agent 스킬 설치
# WSL2 안에서 실행: bash /mnt/d/AI_COMPANY/scripts/install_hermes_skills.sh

set -e

SRC_DIR="/mnt/d/AI_COMPANY/hermes_skills"
DST_DIR="$HOME/.hermes/skills"

# 색상
RED=$'\033[31m'; GRN=$'\033[32m'; YLW=$'\033[33m'; RST=$'\033[0m'

echo "${YLW}[1/4]${RST} Hermes Agent 설치 확인 중..."
if ! command -v hermes >/dev/null 2>&1; then
    echo "${RED}[X]${RST} 'hermes' 명령을 찾을 수 없습니다."
    echo "    먼저 Hermes Agent를 설치해 주세요:"
    echo "    curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash"
    echo "    source ~/.bashrc"
    exit 1
fi
echo "${GRN}[OK]${RST} hermes 명령: $(command -v hermes)"

echo "${YLW}[2/4]${RST} 우리 AI 회사 폴더 마운트 확인..."
if [ ! -d "$SRC_DIR" ]; then
    echo "${RED}[X]${RST} $SRC_DIR 가 보이지 않습니다."
    echo "    WSL에서 Windows 드라이브가 마운트됐는지 확인하세요."
    echo "    예상 경로: D:\\AI_COMPANY\\hermes_skills → /mnt/d/AI_COMPANY/hermes_skills"
    exit 1
fi
echo "${GRN}[OK]${RST} 원본: $SRC_DIR"

echo "${YLW}[3/4]${RST} 우리 회사 Python venv 확인..."
WIN_PY="/mnt/d/AI_COMPANY/.venv/Scripts/python.exe"
if [ ! -f "$WIN_PY" ]; then
    echo "${YLW}[!]${RST} Windows 가상환경 Python이 안 보입니다: $WIN_PY"
    echo "    Windows에서 .venv를 만들어 두셨다면 그대로 사용됩니다."
    echo "    아직 안 만드셨다면, Windows PowerShell에서:"
    echo "      cd D:\\AI_COMPANY"
    echo "      python -m venv .venv"
    echo "      .\\.venv\\Scripts\\Activate.ps1"
    echo "      pip install -r requirements.txt"
fi

mkdir -p "$DST_DIR"

echo "${YLW}[4/4]${RST} 스킬 5종을 $DST_DIR 로 설치..."
INSTALLED=()
for d in "$SRC_DIR"/*/; do
    name=$(basename "$d")
    target="$DST_DIR/$name"
    rm -rf "$target"
    cp -r "$d" "$target"
    INSTALLED+=("$name")
done

echo ""
echo "${GRN}✅ ${#INSTALLED[@]}개 스킬 설치 완료:${RST}"
for n in "${INSTALLED[@]}"; do
    echo "  - $n"
done

echo ""
echo "${YLW}다음 단계:${RST}"
echo "  1) hermes                       # 채팅 시작"
echo "  2) /skills                       # 스킬 목록 확인 (위 5개 보여야 함)"
echo "  3) '고스틱 광고 만들어줘'           # 첫 명령 시도"
echo ""
echo "${YLW}게이트웨이(텔레그램):${RST}"
echo "  hermes gateway setup            # 1회만"
echo "  hermes gateway start            # 백그라운드 실행"
