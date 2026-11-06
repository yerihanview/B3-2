"""
B3-2 미션 독립 기계 채점기 (DoD Verification Suite)
작성자: 참모 토토 / 검증 대상: 챗GPT 구현체
실행: python verify.py
"""
import sys
import unittest
from unittest.mock import MagicMock, patch

class TestDoD1_GitManager(unittest.TestCase):
    def test_git_manager_interface(self):
        from src.git_manager import GitManager
        gm = GitManager()
        self.assertTrue(hasattr(gm, "is_git_repo"))
        self.assertTrue(hasattr(gm, "get_status"))
        self.assertTrue(hasattr(gm, "get_diff"))

    @patch("subprocess.run")
    def test_git_repo_check(self, mock_run):
        from src.git_manager import GitManager
        mock_run.return_value = MagicMock(returncode=0, stdout="true")
        gm = GitManager()
        self.assertTrue(gm.is_git_repo())

class TestDoD2_SafeMode(unittest.TestCase):
    def test_sensitive_masking(self):
        from src.ai_client import AIClient
        client = AIClient(api_key="mock-key")
        sensitive = "OPENAI_API_KEY=sk-proj-1234567890abcdef12345678"
        masked = client.mask_sensitive_data(sensitive)
        self.assertNotIn("sk-proj-1234567890abcdef12345678", masked)
        self.assertIn("[MASKED", masked)

    def test_truncate_diff(self):
        from src.ai_client import AIClient
        client = AIClient(api_key="mock-key")
        long_diff = "\n".join([f"+ line {i}" for i in range(600)])
        truncated = client.truncate_diff(long_diff, max_lines=500)
        lines = truncated.splitlines()
        self.assertLessEqual(len(lines), 510)
        self.assertTrue(any("truncated" in l.lower() or "생략" in l for l in lines))

class TestDoD3_Formatter(unittest.TestCase):
    def test_format_commit_and_pr(self):
        from src.formatter import OutputFormatter
        commit = OutputFormatter.format_commit("feat: add safe mode\n\n- masked secrets")
        self.assertTrue(commit.startswith("feat:") or commit.startswith("fix:"))
        
        pr = OutputFormatter.format_pr("### Why\nFixed leaks\n### What\nMasked keys")
        self.assertIn("Why", pr)
        self.assertIn("What", pr)

class TestDoD4_CLI(unittest.TestCase):
    def test_cli_parser(self):
        from src.main import parse_args
        args = parse_args(["--staged", "--pr", "--dry-run"])
        self.assertTrue(args.staged)
        self.assertTrue(args.pr)
        self.assertTrue(args.dry_run)

def main():
    print("=" * 60)
    print("🚀 B3-2 DoD 원클릭 기계 채점기 가동 중...")
    print("=" * 60)
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    suite.addTests(loader.loadTestsFromTestCase(TestDoD1_GitManager))
    suite.addTests(loader.loadTestsFromTestCase(TestDoD2_SafeMode))
    suite.addTests(loader.loadTestsFromTestCase(TestDoD3_Formatter))
    suite.addTests(loader.loadTestsFromTestCase(TestDoD4_CLI))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    if result.wasSuccessful():
        print("\n" + "=" * 60)
        print("🎉 [100/100 PASS] 모든 5대 DoD 기계 검증을 완벽히 통과했습니다!")
        print("➔ 다음 단계: Step 4 리팩토링 체크리스트 및 Step 5 README 작성을 진행하세요.")
        print("=" * 60)
        return 0
    else:
        print("\n" + "=" * 60)
        print("❌ [FAIL] 실패한 항목이 있습니다. 에러 로그를 챗GPT에 전달해 자가수복(상한 3회)을 지시하세요.")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
