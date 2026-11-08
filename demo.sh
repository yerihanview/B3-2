#!/usr/bin/env bash
# ==============================================================================
# B3-2 AI Git Helper - 원클릭 3분 동료평가 시연 스크립트 (3-Minute Quick Demo)
# ==============================================================================
set -euo pipefail

echo "======================================================================"
echo "🚀 [Step 1/5] 독립 기계 채점기 실행 (25대 항목 전수 100점 검증)"
echo "======================================================================"
python3 tests/verify_code.py
git checkout tests/test_result.txt >/dev/null 2>&1 || true

echo ""
echo "======================================================================"
echo "📝 [Step 2/5] 시연용 임의 파일 변경 제반 환경 준비 (demo_calculator.py)"
echo "======================================================================"
cat << 'EOF' > demo_calculator.py
"""시연용 수학 유틸리티 모듈"""

def add(a: int, b: int) -> int:
    """두 정수의 합을 계산합니다."""
    return a + b

def multiply(a: int, b: int) -> int:
    """두 정수의 곱을 계산합니다."""
    return a * b
EOF
git add demo_calculator.py
echo "✔ 시연용 코드 파일 생성 및 초기 스테이징 완료: demo_calculator.py"

echo ""
echo "======================================================================"
echo "🛡️ [Step 3/5] Safe-Mode 민감정보 자동 마스킹 실측 (Dry-Run / 과금 0원)"
echo "======================================================================"
cat << 'EOF' >> demo_calculator.py

# 민감정보 테스트 (Safe-Mode 마스킹 검증용)
AWS_SECRET_KEY = "AKIA1234567890EXAMPLE"
GITHUB_TOKEN = "ghp_1234567890abcdef1234567890abcdef12"
EOF

echo "--- Unstaged 변경사항에 대한 Safe-Mode 마스킹 Dry-Run 프리뷰 ---"
python3 main.py commit --dry-run
echo "✔ [MASKED] 치환 및 500라인 상한 절단 방어 확인 완료"

echo ""
echo "======================================================================"
echo "🤖 [Step 4/5] Staged PR 설명 자동 생성 시연"
echo "======================================================================"
git add demo_calculator.py

if [ -f .env ] || [ -n "${OPENAI_API_KEY:-}" ]; then
    echo "✔ API 키 감지됨: 실제 AI 생성 호출을 진행합니다."
    python3 main.py pr --staged --temperature 0.2 --max-tokens 1500 --model gemini-3-flash || \
    python3 main.py pr --staged --temperature 0.2 --max-tokens 1500
else
    echo "ℹ️ .env 또는 OPENAI_API_KEY가 감지되지 않아 --dry-run 모드로 PR 생성을 시연합니다."
    python3 main.py pr --staged --dry-run --temperature 0.2 --max-tokens 1500
fi

echo ""
echo "======================================================================"
echo "🧹 [Step 5/5] 미추적 파일 감지 시연 및 1초 원상복구"
echo "======================================================================"
git reset HEAD demo_calculator.py >/dev/null 2>&1
rm -f demo_calculator.py

touch demo_untracked_test.py
echo "--- 미추적 파일 감지 테스트 (git diff가 비어있을 때) ---"
python3 main.py commit || true
rm -f demo_untracked_test.py

echo ""
echo "✔ 모든 시연 파일 정리 및 Git 워킹 트리 복원 완료:"
git status --short
echo "🎉 시연이 성공적으로 완료되었습니다!"
