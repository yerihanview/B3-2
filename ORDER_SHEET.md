# B3-2 Lean MBO Order Sheet (작업 지시서) v3.0

> **수석 아키텍트**: 우광택 (@yerihanview)  
> **발행 주체**: 참모 토토  
> **수행 에디터**: 챗GPT (또는 기타 AI 코더)  
> **과제명**: 내가 고친 코드 설명을 AI가 대신 써주는 도우미 만들기 (B3-2)  
> **개정일**: 2026.11.07 (v3.0 전면 동기화: 24대 RTM 및 공식 미션지 전수 매핑)

---

## 1. Objective (핵심 목적)
Git 변경사항(`git status`, `git diff`)을 수집하여 OpenAI API를 통해 Conventional Commits 커밋 메시지와 Why/What/How to Test PR 템플릿을 자동 생성하는 안전하고 견고한 Python CLI 도구를 구현한다.

---

## 2. Definition of Done (DoD 6대 기계 채점 요건 & 24대 RTM)

### [DoD-1] Git 데이터 수집 및 상태 감지 (`src/git_manager.py`)
- [x] **[RTM #01] Git 명령어 안전 실행**: `subprocess.run(shell=False)` 기반으로 `git status`, `git diff`(staged/unstaged) 수집.
- [x] **[RTM #09] Diff 부재 시 정상 종료**: 변경사항이 없을 때 명확한 안내 후 Exit Code 0으로 정상 종료.
- [x] **[RTM #23] 미추적 파일(Untracked) 지능형 감지**: diff가 비어 있어도 신규 미추적 파일(`??`)이 존재하면 파일 목록을 출력하고 `git add <file>`을 안내.

### [DoD-2] 엔터프라이즈 보안 Safe-Mode (`src/ai_client.py`)
- [x] **[RTM #02] 민감정보 자동 마스킹**: API Key, GitHub 토큰, JWT, 비밀번호 정규식 탐지 및 `[MASKED]` 치환.
- [x] **[RTM #03] 대형 Diff 500라인 상한 절단**: 500줄 초과 diff 발생 시 501번째 줄에 `[truncated: N lines omitted]` 삽입 및 토큰 폭증 방어.
- [x] **[RTM #13] Safe-Mode CLI 플래그 기본 ON**: `--safe-mode`(기본 활성)와 `--no-safe-mode`(비활성) 상호 배타 플래그 지원.
- [x] **[RTM #21] No-Safe-Mode 원본 diff 전송**: 보안 모드 해제 시 원본 diff 전송 및 stderr 경고 출력.
- [x] **[RTM #08] Safe-Mode Dry-Run 프리뷰**: `--dry-run` 플래그로 API 호출 0건, 마스킹/절단 파라미터 사전 검증.

### [DoD-3] AI 통신, 복원력(Resilience) 및 파라미터 제어 (`src/ai_client.py`)
- [x] **[RTM #07] 하이퍼파라미터 바인딩**: CLI `--temperature`, `--max-tokens`, `--model` 파싱 및 AIClient 적용.
- [x] **[RTM #10] HTTP 페이로드 무결성**: OpenAI API 요청 JSON에 모델명, temperature, max_tokens 정확한 반영.
- [x] **[RTM #14] HTTP 401 즉시 종료(Fail-Fast)**: 인증 실패 시 재시도 없이 `AuthenticationError` 발생 및 Exit Code 1 종료.
- [x] **[RTM #15] HTTP 429 지수 백오프**: RateLimit 발생 시 1초→2초 지수 백오프 3회 재시도 및 할당량(Quota) 초과 원인 안내.
- [x] **[RTM #16] HTTP 5xx 서버 에러 백오프 & 복구**: 502/503 에러 지수 백오프 재시도 및 성공 시 정상 복구.
- [x] **[RTM #17] 네트워크 단절 예외 격리**: 소켓 타임아웃 및 DNS 실패 시 `NetworkError` 분리 및 인터넷 연결 점검 안내.
- [x] **[RTM #20] 인증 실패 프로세스 종료 코드**: 인증 에러 시 Exit Code 1 반환.

### [DoD-4] 엄격한 서식 규격화 및 사후 검증 (`src/formatter.py`)
- [x] **[RTM #04] Conventional Commits 헤더 포맷**: `feat:`, `fix:`, `docs:` 등 시맨틱 타입/스코프 검증.
- [x] **[RTM #05] 커밋 제목 72자 상한 제한**: 커밋 첫 줄 제목 72자 초과 시 `ValueError` 거부.
- [x] **[RTM #06] PR 3대 섹션 강제**: `### Why`, `### What`, `### How to Test` 섹션 필수 존재 및 누락 시 자동 보완.
- [x] **[RTM #11] PR 섹션 불릿 0개 '빈 껍데기' 거부**: 섹션 내 `- ` 또는 `* ` 불릿이 0개인 줄글/빈 섹션은 `ValueError`로 거부.
- [x] **[RTM #12] PR 제목 80자 단어 경계 절단**: 80자 초과 시 단어 중간을 자르지 않고 직전 공백에서 안전 절단, 빈 제목 거부.

### [DoD-5] CLI 진입점 및 공식 미션지 구획화 (`src/main.py`, `main.py`)
- [x] **[RTM #18] 서브커맨드 호환성**: `commit`, `pr` 위치 인자와 `--pr` 플래그 동시 지원.
- [x] **[RTM #19] PR 서브커맨드 E2E 실행**: `python main.py pr` 경로가 완전한 PR 텍스트 출력.
- [x] **[RTM #22] 최종 출력 구획화 (Delimiters)**:
  - 커밋 메시지: `--- Commit Message ---` ~ `----------------------`
  - PR 초안: `--- PR Title ---` 및 `--- PR Body ---` ~ `---------------`
  - 드라이런: `--- Dry Run Preview ---` ~ `-----------------------`
- [x] **[RTM #24] 루트 `main.py` 래퍼 지원**: 프로젝트 루트에서 `python main.py` 및 패키지 `python src/main.py` 100% 호환.

### [DoD-6] 기계 검증 통과 (`tests/verify.py`)
- [x] 독립 채점기 `python tests/verify.py`의 **24대 검증 항목 전수 100점(Exit Code 0)** 통과.
- [x] 실행 결과 리포트 `tests/test_result.txt` 자동 생성 및 보존.

---

## 3. Never-Do List (절대 금지 규율)
- [ ] 가변 전역 변수(Global mutable state) 사용 절대 금지.
- [ ] 빈 `except: pass`로 예외를 삼키는 행위(Bare except) 절대 금지.
- [ ] 단일 책임 원칙(SRP) 준수 및 3단계 초과 중첩(Deep Nesting) 금지.
- [ ] 매직 넘버 금지 (`MAX_DIFF_LINES = 500`, `MAX_COMMIT_TITLE_LEN = 72`, `MAX_PR_TITLE_LEN = 80`).
- [ ] 모든 함수에 Type Hinting과 Docstring 의무 적용.
- [ ] `tests/verify.py`에 정의된 24대 인터페이스 시그니처를 임의로 변경하지 말 것.

---

## 4. 인터페이스 시그니처 계약 (`SPEC.md`)
- `src/git_manager.py`: `GitManager` (`is_git_repo`, `get_status`, `get_diff`)
- `src/ai_client.py`: `AIClient` (`mask_sensitive_data`, `truncate_diff`, `prepare_input`, `generate_commit_message`, `generate_pr_description`, `temperature`, `max_tokens`, `safe_mode`), `AIClientError` 계열 (`AuthenticationError`, `RateLimitError`, `ServerError`, `NetworkError`)
- `src/formatter.py`: `OutputFormatter` (`format_commit`, `format_pr`, `truncate_to_word_boundary`)
- `src/main.py` & `main.py`: `parse_args`, `_generate`, `run_cli`

---

## 5. RTM 추적성 매트릭스 요약 (24/24 All Pass)

| 검증 ID | 검증 항목 | 담당 모듈 | 공식 미션지 근거 |
| :---: | :--- | :--- | :--- |
| **#01** | Git 상태/diff 수집 | `GitManager` | DoD-1 (diff/status 수집) |
| **#02** | 민감정보 정규식 마스킹 | `AIClient` | DoD-2 (Safe-Mode) |
| **#03** | 대형 diff 500줄 절단 | `AIClient` | DoD-2 (Safe-Mode 500줄 상한) |
| **#04** | Conventional Commits 포맷 | `OutputFormatter` | DoD-3 (커밋 메시지 규칙) |
| **#05** | 커밋 제목 72자 상한 | `OutputFormatter` | DoD-3 (제목 길이 72자) |
| **#06** | PR 3대 섹션 필수 존재 | `OutputFormatter` | DoD-3 (Why/What/How to Test) |
| **#07** | CLI 파라미터 제어 | `AIClient`, `main.py` | DoD-4 (CLI 인터페이스) |
| **#08** | Safe-Mode Dry-Run | `AIClient`, `main.py` | DoD-2 (Dry-Run 프리뷰) |
| **#09** | Diff 부재 시 정상 종료 | `GitManager`, `main.py` | 예외/경계 조건 |
| **#10** | HTTP 페이로드 무결성 | `AIClient` | DoD-4 (API 파라미터 전달) |
| **#11** | PR 섹션 불릿 강제 | `OutputFormatter` | DoD-3 (섹션별 불릿 필수) |
| **#12** | PR 제목 80자 단어 경계 절단 | `OutputFormatter` | DoD-3 (제목 80자 단어 보존) |
| **#13** | Safe-Mode 기본 활성 | `main.py` | DoD-2 (기본 Safe-Mode) |
| **#14** | 401 인증 실패 Fail-Fast | `AIClient` | 에러 처리 (API Key 오류) |
| **#15** | 429 지수 백오프 재시도 | `AIClient` | 에러 처리 (RateLimit 백오프) |
| **#16** | 5xx 서버 에러 복구 | `AIClient` | 에러 처리 (서버 에러 백오프) |
| **#17** | 네트워크 단절 예외 | `AIClient` | 에러 처리 (네트워크 오류) |
| **#18** | 서브커맨드 호환성 | `main.py` | CLI 인터페이스 (`commit`, `pr`) |
| **#19** | PR 서브커맨드 E2E | `main.py` | E2E 파이프라인 |
| **#20** | 인증 실패 종료 코드 1 | `main.py` | 프로세스 무결성 |
| **#21** | No-Safe-Mode 원본 전송 | `AIClient` | Security 제어 |
| **#22** | 최종 출력 구획화 (Delimiters) | `main.py` | 공식 미션지 L85/157/170 (헤더/구분선) |
| **#23** | 미추적 파일(`??`) 감지 안내 | `GitManager`, `main.py` | Git 미추적 파일 예외 안내 |
| **#24** | 루트 `main.py` 진입점 지원 | `main.py` | 공식 미션지 실행 예시 호환 |
