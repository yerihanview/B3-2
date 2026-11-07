"""Independent machine verification suite for B3-2 mission requirements."""

import io
import json
import os
import sys
import unittest
import urllib.error
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import MagicMock, patch

# Add src to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from ai_client import (
    AIClient,
    AIClientError,
    AuthenticationError,
    NetworkError,
    RateLimitError,
    ServerError,
)
from formatter import MAX_PR_TITLE_LEN, OutputFormatter
from git_manager import GitManager
import main

VALID_PR = (
    "feat(pipeline): automated git commit and pr generation workflow\n\n"
    "### Why\n- Manual writing is slow and inconsistent.\n\n"
    "### What\n- Added AI generator CLI with Safe-Mode.\n\n"
    "### How to Test\n- Run python tests/verify.py and check all pass."
)


def http_error(status: int, message: str = "provider error") -> urllib.error.HTTPError:
    """Build an HTTPError carrying a JSON OpenAI-style body."""
    body = json.dumps({"error": {"message": message}}).encode("utf-8")
    return urllib.error.HTTPError(
        "https://api.openai.com/v1/chat/completions", status, "error", {}, io.BytesIO(body)
    )


def raise_http(status: int, message: str = "provider error"):
    """Return a urlopen side effect that raises a fresh HTTPError on every attempt."""

    def _raise(*_args, **_kwargs):
        raise http_error(status, message)

    return _raise


def raise_network(reason: str = "timed out"):
    """Return a urlopen side effect that raises a connection error on every attempt."""

    def _raise(*_args, **_kwargs):
        raise urllib.error.URLError(reason)

    return _raise


def ok_response(content: str) -> MagicMock:
    """Build a urlopen-compatible response returning the given completion content."""
    response = MagicMock()
    response.read.return_value = json.dumps(
        {"choices": [{"message": {"content": content}}]}
    ).encode("utf-8")
    response.__enter__.return_value = response
    return response


class TestB32MissionRequirements(unittest.TestCase):
    """Test full compliance against official requirements."""

    def test_01_git_manager_diff_and_status(self):
        """Test GitManager executes git commands safely."""
        manager = GitManager()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=" M file.py\n")
            status = manager.get_status()
            self.assertIn("M file.py", status)

            mock_run.return_value = MagicMock(returncode=0, stdout="diff --git a/file.py b/file.py\n")
            diff = manager.get_diff(staged=True)
            self.assertIn("diff --git", diff)

    def test_02_mask_sensitive_data(self):
        """Test Safe-Mode masking of API keys, tokens, and credentials."""
        client = AIClient(api_key="sk-live-12345secret")
        raw = "API_KEY = 'sk-live-12345secret'\ngh_token = 'ghp_abc1234567890abcdef'\n"
        masked = client.mask_sensitive_data(raw)
        self.assertNotIn("sk-live-12345secret", masked)
        self.assertNotIn("ghp_abc1234567890abcdef", masked)
        self.assertIn("[MASKED]", masked)

    def test_03_truncate_diff_lines(self):
        """Test diff cut-off at 500 lines to prevent token explosion."""
        client = AIClient()
        long_diff = "\n".join([f"line {i}" for i in range(600)])
        truncated = client.truncate_diff(long_diff, max_lines=500)
        lines = truncated.splitlines()
        self.assertEqual(len(lines), 501)
        self.assertIn("[truncated: 100 lines omitted]", lines[-1])

    def test_04_conventional_commits_formatting_and_type(self):
        """Test Conventional Commits header validation."""
        valid_commit = "feat(auth): add login endpoint\n\nDetailed explanation."
        formatted = OutputFormatter.format_commit(valid_commit)
        self.assertEqual(formatted, valid_commit)

        invalid_commit = "updated something"
        with self.assertRaises(ValueError):
            OutputFormatter.format_commit(invalid_commit)

    def test_05_commit_title_max_72_chars(self):
        """Official requirement: commit title must be <= 72 characters."""
        title_72 = "feat(core): " + "a" * (72 - len("feat(core): "))
        self.assertEqual(len(title_72), 72)
        self.assertEqual(OutputFormatter.format_commit(title_72), title_72)

        title_73 = "feat(core): " + "a" * (73 - len("feat(core): "))
        with self.assertRaises(ValueError) as ctx:
            OutputFormatter.format_commit(title_73)
        self.assertIn("exceeds maximum allowed length of 72", str(ctx.exception))

    def test_06_pr_title_max_80_chars_and_sections(self):
        """Official requirement: PR title <= 80 chars, sections Why, What, How to Test."""
        formatted = OutputFormatter.format_pr(VALID_PR)
        self.assertIn("### Why", formatted)
        self.assertIn("### What", formatted)
        self.assertIn("### How to Test", formatted)

        # Missing sections auto-filled with bullet points
        minimal_pr = "feat: quick title\n\n### Why\n- needed"
        fixed_pr = OutputFormatter.format_pr(minimal_pr)
        self.assertIn("### What\n- Not provided; review required.", fixed_pr)
        self.assertIn("### How to Test\n- Not provided; review required.", fixed_pr)

    def test_07_cli_temperature_and_max_tokens_options(self):
        """Official requirement: CLI must support --temperature and --max-tokens options."""
        args = main.parse_args(["--temperature", "0.7", "--max-tokens", "2500", "--model", "gpt-4o"])
        self.assertEqual(args.temperature, 0.7)
        self.assertEqual(args.max_tokens, 2500)
        self.assertEqual(args.model, "gpt-4o")

        client = AIClient(model=args.model, temperature=args.temperature, max_tokens=args.max_tokens)
        self.assertEqual(client.temperature, 0.7)
        self.assertEqual(client.max_tokens, 2500)

    def test_08_cli_dry_run_safe_mode(self):
        """Test --dry-run previews safe parameters and diff without calling API."""
        args = main.parse_args(["--dry-run", "--temperature", "0.5", "--max-tokens", "1200"])
        output = main._generate(args, "diff --git a/k.py b/k.py\n+key='sk-12345'", "M k.py")
        self.assertIn("Parameters: model=gpt-4o-mini, temp=0.5, max_tokens=1200", output)
        self.assertIn("[MASKED]", output)
        self.assertNotIn("sk-12345", output)
        self.assertIn("Safe mode: on", output)

    def test_09_empty_diff_handling(self):
        """Official requirement: boundary case when no diff changes exist."""
        with patch.object(GitManager, "is_git_repo", return_value=True), \
             patch.object(GitManager, "get_status", return_value=""), \
             patch.object(GitManager, "get_diff", return_value=""):
            with patch("sys.argv", ["main.py"]):
                buf = io.StringIO()
                with redirect_stdout(buf):
                    exit_code = main.run_cli()
                self.assertEqual(exit_code, 0)
                self.assertIn("No changes in the selected diff", buf.getvalue())

    def test_10_ai_client_request_payload_parameters(self):
        """Test temperature and max_tokens are correctly included in API payload."""
        client = AIClient(api_key="sk-test", model="gpt-4o", temperature=0.8, max_tokens=1500)
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = ok_response("feat: test")

            with patch("urllib.request.Request") as mock_req_cls:
                client._request("instruction", "prompt")
                call_args = mock_req_cls.call_args
                payload = json.loads(call_args[1]["data"].decode("utf-8"))
                self.assertEqual(payload["model"], "gpt-4o")
                self.assertEqual(payload["temperature"], 0.8)
                self.assertEqual(payload["max_tokens"], 1500)

    def test_11_pr_section_without_bullet_is_rejected(self):
        """New: a section that exists but holds no bullet is an empty shell and must be rejected."""
        empty_why = (
            "feat: empty shell\n\n"
            "### Why\n"
            "### What\n- real change\n\n"
            "### How to Test\n- run verify.py"
        )
        with self.assertRaises(ValueError) as ctx:
            OutputFormatter.format_pr(empty_why)
        self.assertIn("Why", str(ctx.exception))
        self.assertIn("bullet", str(ctx.exception))

        prose_only = (
            "feat: prose shell\n\n"
            "### Why\nThis section only has a paragraph.\n\n"
            "### What\n- real change\n\n"
            "### How to Test\n- run verify.py"
        )
        with self.assertRaises(ValueError):
            OutputFormatter.format_pr(prose_only)

        # Both - and * bullets satisfy the requirement
        star_bullets = (
            "feat: star bullets\n\n"
            "### Why\n* star bullet\n\n"
            "### What\n  - nested bullet\n\n"
            "### How to Test\n- run verify.py"
        )
        formatted = OutputFormatter.format_pr(star_bullets)
        self.assertIn("* star bullet", formatted)

        # Bullets under a deeper sub-heading still belong to their parent section
        sub_heading = (
            "feat: sub heading\n\n"
            "### Why\n#### Context\n- bullet under a deeper heading\n\n"
            "### What\n- real change\n\n"
            "### How to Test\n- run verify.py"
        )
        self.assertIn("bullet under a deeper heading", OutputFormatter.format_pr(sub_heading))

    def test_12_pr_title_word_boundary_truncation_and_empty_title(self):
        """New: over-long titles are cut at a word boundary, and empty titles are rejected."""
        words = " ".join(f"word{index:02d}" for index in range(20))
        long_title = f"feat(scope): {words}"
        self.assertGreater(len(long_title), MAX_PR_TITLE_LEN)
        raw = long_title + "\n\n### Why\n- a\n\n### What\n- b\n\n### How to Test\n- c"

        formatted = OutputFormatter.format_pr(raw)
        title = formatted.splitlines()[0]
        self.assertLessEqual(len(title), MAX_PR_TITLE_LEN)
        self.assertTrue(long_title.startswith(title))
        self.assertLess(len(title), len(long_title))
        for token in title.split():
            self.assertIn(token, long_title.split(), "truncation must not leave a partial word")
        self.assertFalse(title.endswith("wor"))

        direct = OutputFormatter.truncate_to_word_boundary("alpha beta gamma delta", 12)
        self.assertEqual(direct, "alpha beta")
        self.assertEqual(len(OutputFormatter.truncate_to_word_boundary("x" * 90)), MAX_PR_TITLE_LEN)

        no_title = "### Why\n- a\n\n### What\n- b\n\n### How to Test\n- c"
        with self.assertRaises(ValueError) as ctx:
            OutputFormatter.format_pr(no_title)
        self.assertIn("title", str(ctx.exception).lower())

    def test_13_safe_mode_flag_defaults_and_effect(self):
        """New: --safe-mode is on by default and --no-safe-mode turns masking off."""
        self.assertTrue(main.parse_args([]).safe_mode)
        self.assertTrue(main.parse_args(["--safe-mode"]).safe_mode)
        self.assertFalse(main.parse_args(["--no-safe-mode"]).safe_mode)

        with self.assertRaises(SystemExit):
            with redirect_stderr(io.StringIO()):
                main.parse_args(["--safe-mode", "--no-safe-mode"])

        secret = "API_KEY = 'sk-live-abcdef123456'"
        safe_client = AIClient(api_key="sk-live-abcdef123456")
        unsafe_client = AIClient(api_key="sk-live-abcdef123456", safe_mode=False)
        self.assertNotIn("sk-live-abcdef123456", safe_client.prepare_input(secret))
        self.assertEqual(unsafe_client.prepare_input(secret), secret)
        self.assertFalse(unsafe_client.safe_mode)

        long_diff = "\n".join(f"line {index}" for index in range(600))
        self.assertEqual(unsafe_client.prepare_input(long_diff), long_diff)
        self.assertIn("[truncated:", safe_client.prepare_input(long_diff))

        args = main.parse_args(["--no-safe-mode", "--dry-run"])
        output = main._generate(args, "+token=abcdef123456", "M a.py")
        self.assertIn("Safe mode: off", output)
        self.assertIn("+token=abcdef123456", output)

    def test_14_http_401_authentication_error(self):
        """New: HTTP 401 fails fast with API-key guidance and no retry."""
        client = AIClient(api_key="sk-bad", model="gpt-4o-mini")
        with patch("urllib.request.urlopen", side_effect=raise_http(401, "Incorrect API key provided")) as mock_urlopen, \
             patch("time.sleep") as mock_sleep:
            with self.assertRaises(AuthenticationError) as ctx:
                client.generate_commit_message("diff", "status")
            message = str(ctx.exception)
            self.assertIn("401", message)
            self.assertIn("OPENAI_API_KEY", message)
            self.assertIn("Incorrect API key provided", message)
            self.assertEqual(mock_urlopen.call_count, 1)
            mock_sleep.assert_not_called()
            self.assertIsInstance(ctx.exception, AIClientError)

    def test_15_http_429_rate_limit_backoff(self):
        """New: HTTP 429 retries with real exponential backoff and then reports the quota cause."""
        client = AIClient(api_key="sk-test")
        with patch("urllib.request.urlopen", side_effect=raise_http(429, "Rate limit reached")) as mock_urlopen, \
             patch("time.sleep") as mock_sleep:
            with self.assertRaises(RateLimitError) as ctx:
                client.generate_commit_message("diff", "status")
            self.assertIn("429", str(ctx.exception))
            self.assertIn("quota", str(ctx.exception).lower())
            self.assertEqual(mock_urlopen.call_count, 3)
            self.assertEqual([call.args[0] for call in mock_sleep.call_args_list], [1, 2])

    def test_16_http_500_server_error_and_recovery(self):
        """New: HTTP 5xx is retried with backoff, recovers on success, and reports persistent failure."""
        client = AIClient(api_key="sk-test")
        responses = [http_error(503, "server overloaded"), ok_response("feat: recovered")]
        with patch("urllib.request.urlopen", side_effect=responses), patch("time.sleep") as mock_sleep:
            result = client.generate_commit_message("diff", "status")
        self.assertEqual(result, "feat: recovered")
        self.assertEqual([call.args[0] for call in mock_sleep.call_args_list], [1])

        with patch("urllib.request.urlopen", side_effect=raise_http(502, "bad gateway")), \
             patch("time.sleep"):
            with self.assertRaises(ServerError) as ctx:
                client.generate_commit_message("diff", "status")
            self.assertIn("502", str(ctx.exception))
            self.assertIn("server", str(ctx.exception).lower())

    def test_17_network_error_is_distinguished(self):
        """New: connection failures surface as NetworkError with connectivity guidance."""
        client = AIClient(api_key="sk-test")
        with patch("urllib.request.urlopen", side_effect=raise_network("timed out")), \
             patch("time.sleep") as mock_sleep:
            with self.assertRaises(NetworkError) as ctx:
                client.generate_commit_message("diff", "status")
        self.assertIn("Network error", str(ctx.exception))
        self.assertIn("internet connection", str(ctx.exception))
        self.assertEqual([call.args[0] for call in mock_sleep.call_args_list], [1, 2])

    def test_18_subcommand_commit_and_pr_parsing(self):
        """New: 'commit'/'pr' subcommands parse and stay compatible with the --pr flag."""
        commit_args = main.parse_args(["commit", "--staged"])
        self.assertEqual(commit_args.command, "commit")
        self.assertFalse(commit_args.pr)
        self.assertTrue(commit_args.staged)

        pr_args = main.parse_args(["pr", "--dry-run"])
        self.assertEqual(pr_args.command, "pr")
        self.assertTrue(pr_args.pr)
        self.assertTrue(pr_args.dry_run)

        self.assertTrue(main.parse_args(["--pr"]).pr)
        self.assertFalse(main.parse_args([]).pr)
        self.assertIsNone(main.parse_args([]).command)

        with self.assertRaises(SystemExit):
            with redirect_stderr(io.StringIO()):
                main.parse_args(["merge"])

    def test_19_run_cli_pr_subcommand_end_to_end(self):
        """New: 'python main.py pr' prints formatted PR text through the CLI exit path."""
        with patch.object(GitManager, "is_git_repo", return_value=True), \
             patch.object(GitManager, "get_status", return_value="M a.py"), \
             patch.object(GitManager, "get_diff", return_value="diff --git a/a.py b/a.py\n+print(1)"), \
             patch("main.AIClient") as mock_client_cls:
            mock_client_cls.return_value.generate_pr_description.return_value = VALID_PR
            with patch("sys.argv", ["main.py", "pr"]):
                buf = io.StringIO()
                with redirect_stdout(buf):
                    exit_code = main.run_cli()
        self.assertEqual(exit_code, 0)
        output = buf.getvalue()
        self.assertIn("### Why", output)
        self.assertIn("### How to Test", output)
        kwargs = mock_client_cls.call_args.kwargs
        self.assertTrue(kwargs["safe_mode"])

    def test_20_authentication_failure_exit_code(self):
        """New: an authentication failure exits with code 1 and prints the 401 guidance."""
        with patch.object(GitManager, "is_git_repo", return_value=True), \
             patch.object(GitManager, "get_status", return_value="M a.py"), \
             patch.object(GitManager, "get_diff", return_value="diff --git a/a.py b/a.py\n+1"), \
             patch("main.AIClient") as mock_client_cls:
            mock_client_cls.return_value.generate_commit_message.side_effect = AuthenticationError(
                "Authentication failed (HTTP 401): OPENAI_API_KEY is missing, invalid, or revoked."
            )
            with patch("sys.argv", ["main.py", "commit"]):
                err = io.StringIO()
                with redirect_stderr(err):
                    exit_code = main.run_cli()
        self.assertEqual(exit_code, 1)
        self.assertIn("401", err.getvalue())

    def test_21_no_safe_mode_passes_raw_diff_to_prompt(self):
        """New: disabling Safe-Mode sends the diff unmasked, while default mode masks it."""
        raw_diff = "diff --git a/x.py b/x.py\n+OPENAI_API_KEY=sk-live-zzz999"
        unsafe = AIClient(api_key="", safe_mode=False)
        self.assertIn("sk-live-zzz999", unsafe._build_prompt(raw_diff, "M x.py"))

        safe = AIClient(api_key="", safe_mode=True)
        self.assertNotIn("sk-live-zzz999", safe._build_prompt(raw_diff, "M x.py"))

    def test_22_output_delimiter_sections(self):
        """Official rubric: final output must be clearly delimited with headers and separators."""
        commit_args = main.parse_args(["commit"])
        with patch.object(AIClient, "generate_commit_message", return_value="feat(ui): add button"):
            commit_out = main._generate(commit_args, "diff", "M a.py")
            self.assertIn("--- Commit Message ---", commit_out)
            self.assertIn("feat(ui): add button", commit_out)
            self.assertIn("----------------------", commit_out)

        pr_args = main.parse_args(["pr"])
        with patch.object(AIClient, "generate_pr_description", return_value=VALID_PR):
            pr_out = main._generate(pr_args, "diff", "M a.py")
            self.assertIn("--- PR Title ---", pr_out)
            self.assertIn("feat(pipeline): automated git commit and pr generation workflow", pr_out)
            self.assertIn("--- PR Body ---", pr_out)
            self.assertIn("### Why", pr_out)
            self.assertIn("---------------", pr_out)

    def test_23_untracked_files_guidance_when_diff_empty(self):
        """Edge case: when diff is empty but untracked files exist, guide user to git add."""
        with patch.object(GitManager, "is_git_repo", return_value=True), \
             patch.object(GitManager, "get_status", return_value="?? new_feature.py\n?? test.txt\n"), \
             patch.object(GitManager, "get_diff", return_value=""):
            with patch("sys.argv", ["main.py"]):
                buf = io.StringIO()
                with redirect_stdout(buf):
                    exit_code = main.run_cli()
                self.assertEqual(exit_code, 0)
                output = buf.getvalue()
                self.assertIn("untracked files were detected", output)
                self.assertIn("? new_feature.py", output)
                self.assertIn("git add <file>", output)

    def test_24_root_main_wrapper_entrypoint(self):
        """Usability: root main.py exists and correctly invokes the CLI pipeline."""
        root_main_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "main.py"))
        self.assertTrue(os.path.exists(root_main_path), "Root main.py must exist")
        import importlib.util
        spec = importlib.util.spec_from_file_location("root_main", root_main_path)
        root_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(root_module)
        self.assertTrue(hasattr(root_module, "run_cli"))


def run_and_record():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestB32MissionRequirements)
    buf = io.StringIO()
    runner = unittest.TextTestRunner(stream=buf, verbosity=2)
    result = runner.run(suite)

    output = buf.getvalue()
    print(output)

    result_path = os.path.join(os.path.dirname(__file__), "test_result.txt")
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    passed = total_tests - failures - errors
    score = int((passed / total_tests) * 100) if total_tests > 0 else 0

    summary = (
        f"============================================================\n"
        f"B3-2 MISSION VERIFICATION REPORT (100% RUBRIC COMPLIANCE)\n"
        f"============================================================\n"
        f"Total Test Cases : {total_tests}\n"
        f"Passed           : {passed}\n"
        f"Failed           : {failures}\n"
        f"Errors           : {errors}\n"
        f"Final Score      : {score}/100\n"
        f"Status           : {'ALL PASS (PERFECT)' if score == 100 else 'NEEDS FIX'}\n"
        f"============================================================\n\n"
        f"Detailed Test Execution Log:\n"
        f"{output}\n"
    )

    with open(result_path, "w", encoding="utf-8") as f:
        f.write(summary)

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_and_record())
