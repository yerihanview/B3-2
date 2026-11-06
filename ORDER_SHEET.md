# B3-2 Lean MBO Order Sheet (작업 지시서)

> **수석 아키텍트**: 우광택 (@yerihanview)  
> **발행 주체**: 참모 토토  
> **수행 에디터**: 챗GPT (또는 기타 AI 코더)  
> **과제명**: 내가 고친 코드 설명을 AI가 대신 써주는 도우미 만들기

---

## 1. Objective (핵심 목적)
Git 변경사항(`git status`, `git diff`)을 수집하여 OpenAI API를 통해 Conventional Commits 커밋 메시지와 Why/What/How to Test PR 템플릿을 자동 생성하는 안전하고 견고한 Python CLI 도구를 구현한다.

---

## 2. Definition of Done (DoD 5대 기계 채점 요건)
1. **[DoD-1] Git 데이터 수집**: `git status`, `git diff`(staged/unstaged)를 서브프로세스로 안전하게 수집하며, Git 저장소가 아닐 경우 명확한 에러를 반환한다.
2. **[DoD-2] Safe-Mode 보안**: API Key/토큰/비밀번호 정규식 마스킹 및 500줄 초과 diff 절단 처리가 작동한다.
3. **[DoD-3] AI 프롬프트 & 서식**: Conventional Commits 규격 커밋 메시지와 Why/What/How PR 템플릿을 생성한다.
4. **[DoD-4] CLI 인터페이스**: `--staged`, `--pr`, `--dry-run`, `--model` 플래그를 지원한다.
5. **[DoD-5] 기계 검증 통과**: 독립 채점기 `python tests/verify.py`를 100점(Exit Code 0)으로 통과한다.

---

## 3. Never-Do List (절대 금지 규율)
- [ ] 전역 변수(Global variables) 사용 절대 금지.
- [ ] 빈 `except: pass`로 예외를 삼키는 행위 절대 금지.
- [ ] 한 함수의 길이는 30라인 이하로 단일 책임 유지.
- [ ] 매직 넘버 금지 (`MAX_DIFF_LINES = 500` 등 상수로 정의).
- [ ] 모든 함수에 Type Hinting과 Docstring 의무 적용.
- [ ] `tests/verify.py`에 정의된 인터페이스 시그니처를 임의로 변경하지 말 것.

---

## 4. 인터페이스 시그니처 계약 (`SPEC.md`)
- `src/git_manager.py`: `GitManager` (`is_git_repo`, `get_status`, `get_diff`)
- `src/ai_client.py`: `AIClient` (`mask_sensitive_data`, `truncate_diff`, `generate_commit_message`, `generate_pr_description`)
- `src/formatter.py`: `OutputFormatter` (`format_commit`, `format_pr`)
- `src/main.py`: `parse_args`, `run_cli`

---

## 5. 자가수복(Self-Healing) 상한
- `python tests/verify.py` 실행 실패 시 오류 트레이스백을 기반으로 자가수복을 시도하되, **최대 3회**로 제한한다.
- 3회 초과 시 코딩을 즉시 멈추고 수석 아키텍트에게 구조적 병목을 보고한다.
