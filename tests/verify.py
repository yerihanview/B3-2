"""
B3-2 미션 독립 기계 채점기 (DoD Verification Suite)
작성자: 참모 토토 / 검증 대상: 챗GPT 구현체
실행: python tests/verify.py
"""
import io
import os
import sys
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

# 프로젝트 루트를 sys.path에 추가 (어디서 실행해도 src import 가능)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


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
    header = "=" * 60 + "\n🚀 B3-2 DoD 원클릭 기계 채점기 가동 중...\n" + "=" * 60 + "\n"
    print(header, end="")

    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    suite.addTests(loader.loadTestsFromTestCase(TestDoD1_GitManager))
    suite.addTests(loader.loadTestsFromTestCase(TestDoD2_SafeMode))
    suite.addTests(loader.loadTestsFromTestCase(TestDoD3_Formatter))
    suite.addTests(loader.loadTestsFromTestCase(TestDoD4_CLI))

    # 콘솔 출력과 파일 저장을 위한 버퍼 분기
    buffer = io.StringIO()
    runner = unittest.TextTestRunner(stream=buffer, verbosity=2)
    result = runner.run(suite)
    test_output = buffer.getvalue()
    print(test_output, end="")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_lines = [
        f"=== B3-2 DoD 기계 채점 결과 보고서 ===",
        f"실행 일시: {timestamp}",
        f"총 테스트 수: {result.testsRun}개",
        f"성공: {result.testsRun - len(result.failures) - len(result.errors)}개",
        f"실패: {len(result.failures)}개 / 오류: {len(result.errors)}개",
        "",
        "--- 상세 실행 로그 ---",
        test_output,
    ]

    if result.wasSuccessful():
        footer = "=" * 60 + "\n🎉 [100/100 PASS] 모든 5대 DoD 기계 검증을 완벽히 통과했습니다!\n" + "=" * 60 + "\n"
        print(footer, end="")
        report_lines.append(footer)
        exit_code = 0
    else:
        footer = "=" * 60 + "\n❌ [FAIL] 실패한 항목이 있습니다.\n" + "=" * 60 + "\n"
        print(footer, end="")
        report_lines.append(footer)
        exit_code = 1

    # 결과 파일 저장: tests/test_result.txt
    result_path = os.path.join(os.path.dirname(__file__), "test_result.txt")
    with open(result_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    print(f"📄 채점 결과가 '{result_path}' 파일에 기록되었습니다.\n")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
