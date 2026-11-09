#!/usr/bin/env bash
# ==============================================================================
# B3-2 AI Git Helper - 단계별 인터랙티브 시연 스크립트 (Interactive Demo Runner)
# 엔터(Enter)를 누를 때마다 전체 기능이 하나의 자연스러운 개발 흐름으로 시연됩니다.
# ==============================================================================

# 색상 정의
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# 파이썬 실행 바이너리 결정
if command -v python3 >/dev/null 2>&1; then
    PYTHON="python3"
else
    PYTHON="python"
fi

# API 키 유효성 확인 함수
has_valid_api_key() {
    "${PYTHON}" -c "
import os
from git_agent.cli import load_dotenv
load_dotenv()
k = os.getenv('OPENAI_API_KEY') or os.getenv('AI_API_KEY')
print('1' if k and 'your-key' not in k and len(k) > 10 else '0')
" 2>/dev/null || echo "0"
}

# 임시 파일 정리 트랩
cleanup() {
    git reset HEAD demo_calculator.py demo_untracked_sample.py >/dev/null 2>&1 || true
    rm -f demo_calculator.py demo_untracked_sample.py
}
trap cleanup EXIT INT TERM

pause_step() {
    echo ""
    if [ -t 0 ]; then
        echo -e "${YELLOW}▶ [엔터(Enter)]를 누르면 위 명령어를 실행합니다...${NC}"
        read -r
    else
        echo -e "${CYAN}▶ (자동 실행 모드로 진행합니다...)${NC}"
    fi
}

echo -e "${BOLD}${CYAN}======================================================================${NC}"
echo -e "${BOLD}${CYAN} 🚀 B3-2 AI Git Helper - 전체 기능 단계별 시연 (Interactive Demo)${NC}"
echo -e "${BOLD}${CYAN}======================================================================${NC}"
echo -e "개발자의 일상적인 기능 개발 라이프사이클을 따라 전체 기능이 순차 진행됩니다."
echo -e "각 단계의 설명과 복붙 명령어를 확인하신 후 [엔터]를 눌러주세요.\n"

# ------------------------------------------------------------------------------
# [Step 1] 변경 사항 없음 (Empty Diff) 정상 방어
# ------------------------------------------------------------------------------
echo -e "${BOLD}${GREEN}----------------------------------------------------------------------${NC}"
echo -e "${BOLD}${GREEN}[Step 1/6] 변경 사항 없음 (Empty Diff) 정상 방어 시연${NC}"
echo -e "${BOLD}${GREEN}----------------------------------------------------------------------${NC}"
echo -e "📌 ${BOLD}설명${NC}: 작업 트리에 아무 변경 사항이 없을 때, 에러 없이 친절한 안내를 출력하고 정상 종료(0)합니다."
echo -e "💻 ${BOLD}실행 명령어${NC}: ${CYAN}${PYTHON} main.py commit${NC}"
pause_step

${PYTHON} main.py commit
echo -e "\n✔ [Step 1 완료] 빈 변경사항에 대한 예외 처리 및 정상 종료 확인."

# ------------------------------------------------------------------------------
# [Step 2] 신규 파일 생성 및 미추적 파일(Untracked File) 지능형 감지
# ------------------------------------------------------------------------------
echo ""
echo -e "${BOLD}${GREEN}----------------------------------------------------------------------${NC}"
echo -e "${BOLD}${GREEN}[Step 2/6] 신규 파일 생성 및 미추적 파일(Untracked) 감지 시연${NC}"
echo -e "${BOLD}${GREEN}----------------------------------------------------------------------${NC}"
echo -e "📌 ${BOLD}설명${NC}: 새 파일을 만들고 git add를 깜빡했을 때, diff는 비어있지만 미추적 파일을 감지해 git add를 유도합니다."
echo -e "📝 ${BOLD}사전 준비${NC}: touch demo_untracked_sample.py 실행"
touch demo_untracked_sample.py
echo -e "💻 ${BOLD}실행 명령어${NC}: ${CYAN}${PYTHON} main.py commit${NC}"
pause_step

${PYTHON} main.py commit || true
rm -f demo_untracked_sample.py
echo -e "\n✔ [Step 2 완료] 미추적 파일 지능형 감지 및 git add 안내 출력 확인."

# ------------------------------------------------------------------------------
# [Step 3] 현실적 코드 작성 및 Safe-Mode 민감정보 자동 마스킹 (Dry-Run)
# ------------------------------------------------------------------------------
echo ""
echo -e "${BOLD}${GREEN}----------------------------------------------------------------------${NC}"
echo -e "${BOLD}${GREEN}[Step 3/6] Safe-Mode 민감정보 자동 마스킹 시연 (과금 0원 Dry-Run)${NC}"
echo -e "${BOLD}${GREEN}----------------------------------------------------------------------${NC}"
echo -e "📌 ${BOLD}설명${NC}: 현실적 수학 유틸리티 코드(demo_calculator.py)를 작성하고 실수로 하드코딩된 API 키를 삽입합니다."
echo -e "         외부 AI 프롬프트로 전송되기 전 [MASKED]로 안전하게 치환되는지 검증합니다."
echo -e "📝 ${BOLD}사전 준비${NC}: demo_calculator.py 생성 (가짜 API Key / Token 포함)"
cat << 'EOF' > demo_calculator.py
"""시연용 수학 유틸리티 모듈"""

def add(a: int, b: int) -> int:
    """두 정수의 합을 계산합니다."""
    return a + b

def multiply(a: int, b: int) -> int:
    """두 정수의 곱을 계산합니다."""
    return a * b

# 실수로 하드코딩된 민감정보 (Safe-Mode 마스킹 시연용)
AWS_SECRET_KEY = "AKIA1234567890EXAMPLE"
GITHUB_TOKEN = "ghp_1234567890abcdef1234567890abcdef12"
EOF

git add demo_calculator.py
echo -e "💻 ${BOLD}실행 명령어${NC}: ${CYAN}${PYTHON} main.py commit --staged --dry-run${NC}"
pause_step

${PYTHON} main.py commit --staged --dry-run
echo -e "\n✔ [Step 3 완료] Diff 상에서 민감 키가 [MASKED]로 완벽히 치환되어 유출이 차단됨을 확인."

# ------------------------------------------------------------------------------
# [Step 4] 미스테이징(Unstaged) 작업 중 커밋 메시지 자동 생성
# ------------------------------------------------------------------------------
echo ""
echo -e "${BOLD}${GREEN}----------------------------------------------------------------------${NC}"
echo -e "${BOLD}${GREEN}[Step 4/6] 작업 중(Unstaged) 커밋 메시지 자동 생성 시연${NC}"
echo -e "${BOLD}${GREEN}----------------------------------------------------------------------${NC}"
echo -e "📌 ${BOLD}설명${NC}: 민감정보를 제거하고 정상 코드로 정리한 뒤, git add 없이 작업 중(Unstaged) 상태에서 커밋 메시지를 생성합니다."
echo -e "📝 ${BOLD}사전 준비${NC}: demo_calculator.py 정상화 (민감정보 제거)"
cat << 'EOF' > demo_calculator.py
"""시연용 수학 유틸리티 모듈"""

def add(a: int, b: int) -> int:
    """두 정수의 합을 계산합니다."""
    return a + b

def multiply(a: int, b: int) -> int:
    """두 정수의 곱을 계산합니다."""
    return a * b
EOF

if [ "$(has_valid_api_key)" = "1" ]; then
    CMD="${PYTHON} main.py commit --model gemini-3-flash"
    echo -e "💻 ${BOLD}실행 명령어${NC}: ${CYAN}${CMD}${NC}"
    pause_step
    ${PYTHON} main.py commit --model gemini-3-flash || ${PYTHON} main.py commit
else
    CMD="${PYTHON} main.py commit --dry-run"
    echo -e "ℹ️ (유효한 API 키 미설정 환경이므로 안전하게 --dry-run 프리뷰 모드로 시연합니다.)"
    echo -e "💻 ${BOLD}실행 명령어${NC}: ${CYAN}${CMD}${NC}"
    pause_step
    ${PYTHON} main.py commit --dry-run
fi
echo -e "\n✔ [Step 4 완료] Conventional Commits 규격(feat: ...)의 시맨틱 커밋 메시지 생성 확인."

# ------------------------------------------------------------------------------
# [Step 5] 스테이징(Staged) 및 파라미터 제어 PR 설명서 자동 생성
# ------------------------------------------------------------------------------
echo ""
echo -e "${BOLD}${GREEN}----------------------------------------------------------------------${NC}"
echo -e "${BOLD}${GREEN}[Step 5/6] 스테이징(Staged) 및 파라미터 제어 PR 설명서 생성 시연${NC}"
echo -e "${BOLD}${GREEN}----------------------------------------------------------------------${NC}"
echo -e "📌 ${BOLD}설명${NC}: git add로 변경 파일을 스테이징하고, 온도(--temperature)와 토큰 상한(--max-tokens)을 제어하여"
echo -e "         Why / What / How to Test 3대 구조화 섹션과 불릿이 완비된 PR 문서를 생성합니다."
echo -e "📝 ${BOLD}사전 준비${NC}: git add demo_calculator.py 실행"
git add demo_calculator.py

if [ "$(has_valid_api_key)" = "1" ]; then
    CMD="${PYTHON} main.py pr --staged --temperature 0.2 --max-tokens 1500 --model gemini-3-flash"
    echo -e "💻 ${BOLD}실행 명령어${NC}: ${CYAN}${CMD}${NC}"
    pause_step
    ${PYTHON} main.py pr --staged --temperature 0.2 --max-tokens 1500 --model gemini-3-flash || \
    ${PYTHON} main.py pr --staged --temperature 0.2 --max-tokens 1500
else
    CMD="${PYTHON} main.py pr --staged --dry-run --temperature 0.2 --max-tokens 1500"
    echo -e "ℹ️ (유효한 API 키 미설정 환경이므로 안전하게 --dry-run 프리뷰 모드로 시연합니다.)"
    echo -e "💻 ${BOLD}실행 명령어${NC}: ${CYAN}${CMD}${NC}"
    pause_step
    ${PYTHON} main.py pr --staged --dry-run --temperature 0.2 --max-tokens 1500
fi
echo -e "\n✔ [Step 5 완료] --- PR Title --- 및 --- PR Body --- (Why/What/How to Test 불릿 완비) 생성 확인."

# ------------------------------------------------------------------------------
# [Step 6] 시연 종료 및 1초 원상복구 (Zero-Artifact Clean-up)
# ------------------------------------------------------------------------------
echo ""
echo -e "${BOLD}${GREEN}----------------------------------------------------------------------${NC}"
echo -e "${BOLD}${GREEN}[Step 6/6] 시연 종료 및 1초 원상복구 (Clean up)${NC}"
echo -e "${BOLD}${GREEN}----------------------------------------------------------------------${NC}"
echo -e "📌 ${BOLD}설명${NC}: 시연에 사용된 임시 파일을 삭제하고 저장소를 클론 직후의 100% 무결점 상태로 복원합니다."
echo -e "💻 ${BOLD}실행 명령어${NC}: ${CYAN}git reset HEAD demo_calculator.py && rm -f demo_calculator.py && git status${NC}"
pause_step

git reset HEAD demo_calculator.py >/dev/null 2>&1 || true
rm -f demo_calculator.py
git status --short

echo ""
echo -e "${BOLD}${CYAN}======================================================================${NC}"
echo -e "${BOLD}${GREEN} 🎉 B3-2 전체 기능 시연이 성공적으로 완료되었습니다! (Git 워킹 트리 무결점 복원)${NC}"
echo -e "${BOLD}${CYAN}======================================================================${NC}"
