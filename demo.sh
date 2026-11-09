#!/usr/bin/env bash
# ==============================================================================
# B3-2 AI Git Helper - 전수 기능 단계별 대화형 시연 러너 (Interactive Demo Runner)
# 엔터(Enter)를 누를 때마다 전체 핵심 과제가 하나의 자연스러운 개발 흐름으로 시연됩니다.
# 모든 시연 파일은 demo/ 디렉토리 내부에서만 격리 생성·삭제되어 루트가 항상 깨끗합니다.
# ==============================================================================

set -e

# 색상 정의
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# 파이썬 실행 바이너리 및 모듈 경로 설정
if command -v python3 >/dev/null 2>&1; then
    PYTHON="python3"
else
    PYTHON="python"
fi

export PYTHONPATH="src:${PYTHONPATH:-}"

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
    git reset HEAD demo/calculator.py demo/token_overflow.txt demo/untracked_sample.py >/dev/null 2>&1 || true
    rm -f demo/calculator.py demo/token_overflow.txt demo/untracked_sample.py
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

mkdir -p demo

echo -e "${BOLD}${CYAN}======================================================================${NC}"
echo -e "${BOLD}${CYAN} 🚀 B3-2 AI Git Helper - 전수 기능 인터랙티브 시연 (Interactive Demo)${NC}"
echo -e "${BOLD}${CYAN}======================================================================${NC}"
echo -e "개발자의 일상적인 기능 개발 라이프사이클을 따라 B3-2의 전수 핵심 기능이 순차 진행됩니다."
echo -e "모든 임시 파일은 ${BOLD}demo/${NC} 디렉토리 내부에서 격리되어 루트 워킹 트리가 항상 깨끗합니다."
echo -e "각 단계의 설명과 복붙 명령어를 확인하신 후 [엔터]를 눌러주세요.\n"

# ------------------------------------------------------------------------------
# [Step 1] 변경 사항 없음 (Empty Diff) 정상 방어
# ------------------------------------------------------------------------------
echo -e "${BOLD}${GREEN}----------------------------------------------------------------------${NC}"
echo -e "${BOLD}${GREEN}[Step 1/8] 변경 사항 없음 (Empty Diff) 정상 방어 시연${NC}"
echo -e "${BOLD}${GREEN}----------------------------------------------------------------------${NC}"
echo -e "📌 ${BOLD}설명${NC}: 작업 트리에 아무 변경 사항이 없을 때, 에러 없이 친절한 안내를 출력하고 정상 종료(0)합니다."
echo -e "💻 ${BOLD}실행 명령어${NC}: ${CYAN}${PYTHON} -m git_agent commit${NC}"
pause_step

${PYTHON} -m git_agent commit
echo -e "\n✔ [Step 1 완료] 빈 변경사항에 대한 예외 처리 및 정상 종료(Exit Code 0) 확인."

# ------------------------------------------------------------------------------
# [Step 2] 신규 파일 생성 및 미추적 파일(Untracked File) 지능형 감지
# ------------------------------------------------------------------------------
echo ""
echo -e "${BOLD}${GREEN}----------------------------------------------------------------------${NC}"
echo -e "${BOLD}${GREEN}[Step 2/8] 신규 파일 생성 및 미추적 파일(Untracked) 감지 시연${NC}"
echo -e "${BOLD}${GREEN}----------------------------------------------------------------------${NC}"
echo -e "📌 ${BOLD}설명${NC}: 새 파일을 만들고 git add를 깜빡했을 때, diff는 비어있지만 미추적 파일을 감지해 git add를 유도합니다."
echo -e "📝 ${BOLD}사전 준비${NC}: touch demo/untracked_sample.py 실행"
touch demo/untracked_sample.py
echo -e "💻 ${BOLD}실행 명령어${NC}: ${CYAN}${PYTHON} -m git_agent commit${NC}"
pause_step

${PYTHON} -m git_agent commit || true
rm -f demo/untracked_sample.py
echo -e "\n✔ [Step 2 완료] 미추적 파일 지능형 감지 및 git add 안내 출력 확인."

# ------------------------------------------------------------------------------
# [Step 3] Safe-Mode vs No Safe-Mode 민감정보 자동 마스킹 대조 검증
# ------------------------------------------------------------------------------
echo ""
echo -e "${BOLD}${GREEN}----------------------------------------------------------------------${NC}"
echo -e "${BOLD}${GREEN}[Step 3/8] Safe-Mode vs --no-safe-mode 민감정보 마스킹 대조 시연${NC}"
echo -e "${BOLD}${GREEN}----------------------------------------------------------------------${NC}"
echo -e "📌 ${BOLD}설명${NC}: 현실적 수학 유틸리티 코드(demo/calculator.py)에 실수로 하드코딩된 API 키를 삽입합니다."
echo -e "         기본 Safe-Mode 활성화 시 [MASKED]로 안전 치환되는 모습과,"
echo -e "         --no-safe-mode 적용 시 원본 평문이 노출되는 차이를 대조하여 보안 유효성을 입증합니다."
echo -e "📝 ${BOLD}사전 준비${NC}: demo/calculator.py 생성 및 git add 스테이징"
cat << 'EOF' > demo/calculator.py
"""시연용 수학 유틸리티 모듈"""

def add(a: int, b: int) -> int:
    """두 정수의 합을 계산합니다."""
    return a + b

# 실수로 하드코딩된 민감정보 (Safe-Mode 마스킹 시연용)
AWS_SECRET_KEY = "AKIA1234567890EXAMPLE"
GITHUB_TOKEN = "ghp_1234567890abcdef1234567890abcdef12"
EOF

git add demo/calculator.py

echo -e "\n[3-1] 기본 Safe-Mode (보안 활성화): [MASKED] 치환 확인"
echo -e "💻 ${BOLD}실행 명령어${NC}: ${CYAN}${PYTHON} -m git_agent commit --staged --dry-run${NC}"
pause_step
${PYTHON} -m git_agent commit --staged --dry-run

echo -e "\n[3-2] --no-safe-mode (보안 비활성화 대조): 원본 평문 노출 경고 확인"
echo -e "💻 ${BOLD}실행 명령어${NC}: ${CYAN}${PYTHON} -m git_agent commit --staged --dry-run --no-safe-mode${NC}"
pause_step
${PYTHON} -m git_agent commit --staged --dry-run --no-safe-mode || true

echo -e "\n✔ [Step 3 완료] Safe-Mode 활성화 시 [MASKED] 완벽 치환 및 No Safe-Mode와의 명확한 대조 확인."

# ------------------------------------------------------------------------------
# [Step 4] 대용량 Diff 토큰 폭증 및 비용 방어 (500줄 초과 절삭)
# ------------------------------------------------------------------------------
echo ""
echo -e "${BOLD}${GREEN}----------------------------------------------------------------------${NC}"
echo -e "${BOLD}${GREEN}[Step 4/8] 500줄 초과 Diff 토큰 폭증 및 비용 방어 시연${NC}"
echo -e "${BOLD}${GREEN}----------------------------------------------------------------------${NC}"
echo -e "📌 ${BOLD}설명${NC}: 700줄 대용량 파일 생성 시, 프롬프트 토큰 폭증과 무분별한 API 과금을 막기 위해"
echo -e "         diff가 500줄 상한에서 자동 절삭(Truncated)됨을 검증합니다."
echo -e "📝 ${BOLD}사전 준비${NC}: demo/token_overflow.txt (700줄) 생성 및 git add"
${PYTHON} -c "
with open('demo/token_overflow.txt', 'w', encoding='utf-8') as f:
    for i in range(1, 701):
        f.write(f'line_{i}: metric_data_sample_value_for_testing\n')
"
git add demo/token_overflow.txt
echo -e "💻 ${BOLD}실행 명령어${NC}: ${CYAN}${PYTHON} -m git_agent commit --staged --dry-run${NC}"
pause_step

${PYTHON} -m git_agent commit --staged --dry-run
git reset HEAD demo/token_overflow.txt >/dev/null 2>&1 || true
rm -f demo/token_overflow.txt
echo -e "\n✔ [Step 4 완료] 500줄 초과 시 [truncated: ... lines omitted] 절삭을 통한 토큰/비용 방어 확인."

# ------------------------------------------------------------------------------
# [Step 5] 미스테이징(Unstaged) vs 스테이징(Staged) 타겟팅 분리 실증
# ------------------------------------------------------------------------------
echo ""
echo -e "${BOLD}${GREEN}----------------------------------------------------------------------${NC}"
echo -e "${BOLD}${GREEN}[Step 5/8] 미스테이징(Unstaged) vs 스테이징(Staged) 타겟팅 분리 실증${NC}"
echo -e "${BOLD}${GREEN}----------------------------------------------------------------------${NC}"
echo -e "📌 ${BOLD}설명${NC}: demo/calculator.py를 정상 유틸리티 코드로 정리한 뒤, 아직 git add를 하지 않은"
echo -e "         작업 트리(Working Tree)의 변경사항과 git add된 스테이징 영역이 정확히 분리 감지되는지 확인합니다."
echo -e "📝 ${BOLD}사전 준비${NC}: demo/calculator.py 정상화"
cat << 'EOF' > demo/calculator.py
"""시연용 수학 유틸리티 모듈"""

def add(a: int, b: int) -> int:
    """두 정수의 합을 계산합니다."""
    return a + b

def multiply(a: int, b: int) -> int:
    """두 정수의 곱을 계산합니다."""
    return a * b
EOF

echo -e "\n[5-1] 작업 트리(Unstaged) 변경사항 타겟팅:"
echo -e "💻 ${BOLD}실행 명령어${NC}: ${CYAN}${PYTHON} -m git_agent commit --dry-run${NC}"
pause_step
${PYTHON} -m git_agent commit --dry-run | grep -E "(\+def|A  demo)" || true

echo -e "\n[5-2] git add 후 스테이징(Staged) 영역 타겟팅:"
git add demo/calculator.py
echo -e "💻 ${BOLD}실행 명령어${NC}: ${CYAN}${PYTHON} -m git_agent commit --staged --dry-run${NC}"
pause_step
${PYTHON} -m git_agent commit --staged --dry-run | grep -E "(\+def|A  demo)" || true

echo -e "\n✔ [Step 5 완료] --staged 옵션에 따른 Working Tree vs Index 변경사항 타겟팅 분리 검증."

# ------------------------------------------------------------------------------
# [Step 6] 하이퍼파라미터 제어 실증 (--temperature, --max-tokens)
# ------------------------------------------------------------------------------
echo ""
echo -e "${BOLD}${GREEN}----------------------------------------------------------------------${NC}"
echo -e "${BOLD}${GREEN}[Step 6/8] 하이퍼파라미터 제어 실증 (--temperature, --max-tokens)${NC}"
echo -e "${BOLD}${GREEN}----------------------------------------------------------------------${NC}"
echo -e "📌 ${BOLD}설명${NC}: 모델의 다양성을 제어하는 temperature와 비용 상한인 max-tokens 파라미터가"
echo -e "         CLI 옵션을 통해 API 호출 페이로드로 완벽하게 주입됨을 검증합니다."
echo -e "💻 ${BOLD}실행 명령어 (결정론적 설정)${NC}: ${CYAN}${PYTHON} -m git_agent commit --staged --dry-run --temperature 0.0 --max-tokens 300${NC}"
pause_step
${PYTHON} -m git_agent commit --staged --dry-run --temperature 0.0 --max-tokens 300 | head -n 4

echo -e "\n💻 ${BOLD}실행 명령어 (창의적/대용량 설정)${NC}: ${CYAN}${PYTHON} -m git_agent commit --staged --dry-run --temperature 0.8 --max-tokens 1500${NC}"
pause_step
${PYTHON} -m git_agent commit --staged --dry-run --temperature 0.8 --max-tokens 1500 | head -n 4

echo -e "\n✔ [Step 6 완료] temp=0.0/300 및 temp=0.8/1500 파라미터 정상 주입 확인."

# ------------------------------------------------------------------------------
# [Step 7] 공식 루브릭 커밋 메시지 자동 생성 (Conventional Commits 72자)
# ------------------------------------------------------------------------------
echo ""
echo -e "${BOLD}${GREEN}----------------------------------------------------------------------${NC}"
echo -e "${BOLD}${GREEN}[Step 7/8] 공식 루브릭 시맨틱 커밋 메시지 생성 시연${NC}"
echo -e "${BOLD}${GREEN}----------------------------------------------------------------------${NC}"
echo -e "📌 ${BOLD}설명${NC}: 공식 루브릭 규격인 Conventional Commits (<type>(<scope>): <subject>) 형식 및"
echo -e "         헤더 72자 이하 제한을 준수하는 시맨틱 커밋 메시지를 생성합니다."

if [ "$(has_valid_api_key)" = "1" ]; then
    CMD="${PYTHON} -m git_agent commit --staged --temperature 0.2 --model gemini-3-flash"
    echo -e "💻 ${BOLD}실행 명령어${NC}: ${CYAN}${CMD}${NC}"
    pause_step
    ${PYTHON} -m git_agent commit --staged --temperature 0.2 --model gemini-3-flash || \
    ${PYTHON} -m git_agent commit --staged --temperature 0.2
else
    CMD="${PYTHON} -m git_agent commit --staged --dry-run --temperature 0.2"
    echo -e "ℹ️ (유효한 API 키 미설정 환경이므로 안전하게 --dry-run 프리뷰 모드로 시연합니다.)"
    echo -e "💻 ${BOLD}실행 명령어${NC}: ${CYAN}${CMD}${NC}"
    pause_step
    ${PYTHON} -m git_agent commit --staged --dry-run --temperature 0.2
fi
echo -e "\n✔ [Step 7 완료] --- Commit Message --- 구획선 및 Conventional Commits 헤더 출력 확인."

# ------------------------------------------------------------------------------
# [Step 8] 공식 루브릭 PR 설명서 자동 생성 (Why / What / How to Test)
# ------------------------------------------------------------------------------
echo ""
echo -e "${BOLD}${GREEN}----------------------------------------------------------------------${NC}"
echo -e "${BOLD}${GREEN}[Step 8/8] 공식 루브릭 PR 설명서 자동 생성 시연${NC}"
echo -e "${BOLD}${GREEN}----------------------------------------------------------------------${NC}"
echo -e "📌 ${BOLD}설명${NC}: 스테이징된 기능 변경사항에 대해 Why / What / How to Test 3대 필수 섹션과"
echo -e "         각 섹션별 필수 불릿('- ')이 완비된 GitHub PR 설명서 초안을 자동 생성합니다."

if [ "$(has_valid_api_key)" = "1" ]; then
    CMD="${PYTHON} -m git_agent pr --staged --temperature 0.2 --max-tokens 1500 --model gemini-3-flash"
    echo -e "💻 ${BOLD}실행 명령어${NC}: ${CYAN}${CMD}${NC}"
    pause_step
    ${PYTHON} -m git_agent pr --staged --temperature 0.2 --max-tokens 1500 --model gemini-3-flash || \
    ${PYTHON} -m git_agent pr --staged --temperature 0.2 --max-tokens 1500
else
    CMD="${PYTHON} -m git_agent pr --staged --dry-run --temperature 0.2 --max-tokens 1500"
    echo -e "ℹ️ (유효한 API 키 미설정 환경이므로 안전하게 --dry-run 프리뷰 모드로 시연합니다.)"
    echo -e "💻 ${BOLD}실행 명령어${NC}: ${CYAN}${CMD}${NC}"
    pause_step
    ${PYTHON} -m git_agent pr --staged --dry-run --temperature 0.2 --max-tokens 1500
fi
echo -e "\n✔ [Step 8 완료] --- PR Title --- 및 --- PR Body --- (Why/What/How to Test 불릿 완비) 생성 확인."

# ------------------------------------------------------------------------------
# 시연 종료 및 1초 원상복구 (Zero-Artifact Clean-up)
# ------------------------------------------------------------------------------
echo ""
echo -e "${BOLD}${CYAN}----------------------------------------------------------------------${NC}"
echo -e "${BOLD}${CYAN}[원상복구] 시연 종료 및 1초 클린업 (Clean up)${NC}"
echo -e "${BOLD}${CYAN}----------------------------------------------------------------------${NC}"
echo -e "📌 ${BOLD}설명${NC}: 시연에 사용된 demo/ 내부의 임시 파일을 삭제하고 저장소를 100% 무결점 상태로 복원합니다."
echo -e "💻 ${BOLD}실행 명령어${NC}: ${CYAN}git reset HEAD demo/ >/dev/null 2>&1 && rm -f demo/calculator.py && git status${NC}"
pause_step

git reset HEAD demo/calculator.py >/dev/null 2>&1 || true
rm -f demo/calculator.py
git status --short

echo ""
echo -e "${BOLD}${CYAN}======================================================================${NC}"
echo -e "${BOLD}${GREEN} 🎉 B3-2 전수 기능 시연이 성공적으로 완료되었습니다! (Git 워킹 트리 100% 무결점 복원)${NC}"
echo -e "${BOLD}${CYAN}======================================================================${NC}"
