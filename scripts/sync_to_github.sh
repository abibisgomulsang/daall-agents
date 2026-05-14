#!/usr/bin/env bash
# 영상 #3 컨셉: 메모리/스킬을 GitHub에 동기화해서
# 컴퓨터가 바뀌어도 영구 백업
# 사용: bash scripts/sync_to_github.sh "사장님 커밋 메시지"

set -e

ROOT="/mnt/d/AI_COMPANY"
MSG="${1:-회사 메모리·스킬 자동 동기화}"

cd "$ROOT"

# .git 없으면 초기화 안내
if [ ! -d ".git" ]; then
    echo "Git 저장소가 아닙니다. 먼저 한 번만:"
    echo "  cd $ROOT"
    echo "  git init"
    echo "  git remote add origin https://github.com/<사장님계정>/abibi-ai-company.git"
    exit 1
fi

# 동기화 대상
TARGETS=(
    "brain_packs/"
    "hermes_skills/"
    "11_memory/agents/"
    "11_memory/hermes/preferences.json"
    "11_memory/goals/"
    "docs/"
    "ai_company/"
    "tests/"
    "TASK_BOARD.md"
    "PROJECT_MASTER_PLAN.md"
    "AGENTS.md"
)

# .gitignore가 보호해야 할 것 — secrets, 큰 파일
GITIGNORE_PROTECT="
.env
.env.local
.venv/
__pycache__/
*.pyc
11_memory/hermes/inbox.jsonl
11_memory/hermes/outbox.jsonl
11_memory/hermes/rate.json
12_logs/
"

if [ ! -f ".gitignore" ]; then
    echo "$GITIGNORE_PROTECT" > .gitignore
    echo "✓ .gitignore 생성"
fi

# 변경 사항 확인
git add "${TARGETS[@]}" 2>/dev/null || true
git add .gitignore

# 커밋할 게 없으면 종료
if git diff --staged --quiet; then
    echo "변경된 파일 없음 — 커밋 안 함"
    exit 0
fi

git commit -m "$MSG ($(date '+%Y-%m-%d %H:%M'))"

# push (remote 설정돼 있을 때만)
if git remote get-url origin >/dev/null 2>&1; then
    echo "GitHub로 push 중..."
    git push origin main 2>&1 || git push origin master 2>&1 || {
        echo "Push 실패 — 'git push' 직접 시도하시거나 remote 확인하세요"
        exit 1
    }
    echo "✅ GitHub 동기화 완료"
else
    echo "✓ 커밋만 완료 (remote 미설정 — 로컬 보관)"
fi
