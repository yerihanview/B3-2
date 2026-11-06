# B3-2: 내가 고친 코드 설명을 AI가 대신 써주는 도우미 (AI Git Helper)

> **코디세이 AI 올인원 2기 실전 미션 B3-2**  
> **수석 아키텍트**: 우광택 (@yerihanview)  
> **방법론**: 린 에이전틱 3자 분업 (수석 아키텍트 - 참모 토토 - 에디터 챗GPT)

---

## 1. 프로젝트 개요 및 과제 목표

개발자가 작업한 코드 변경사항(`git status`, `git diff`)을 정밀하게 수집·정제한 뒤, 대규모 언어 모델(OpenAI API)을 연동하여 **Conventional Commits 규격의 명확한 커밋 메시지**와 **Why / What / How to Test 구조화 PR 템플릿**을 원클릭으로 자동 생성하는 안전한 고성능 Python CLI 도구입니다.

### 핵심 해결 과제
1. **커밋/PR 작성 피로도 해소**: 변경 내역 기반 맥락 파악 및 일관된 시맨틱 커밋 메시지 생성.
2. **원천적 정보 유출 차단 (Safe-Mode)**: 프롬프트 전달 전 민감 정보(API Key, 토큰, 비밀번호 등)의 완벽한 자동 마스킹.
3. **토큰 폭증 및 비용 방어**: 초대형 diff 발생 시 지능적인 500라인 상한 및 절단(Truncate) 처리.
4. **무의존성 포터블 아키텍처**: 외부 서드파티 패키지 설치 없이 Python 3.10+ 표준 라이브러리만으로 즉시 구동.

---

## 2. 시스템 아키텍처 및 폴더 구조

단일 책임 원칙(SRP)과 인터페이스 계약(Spec-First)에 따라 모듈을 4개 계층으로 분리하여 유지보수성과 테스트 격리성을 극대화했습니다.

```
B3-2/
├── .gitignore              # .env 및 캐시 파일의 Git 추적 원천 차단
├── .env.example            # 환경변수 설정 가이드 템플릿
├── ORDER_SHEET.md          # 토토가 사전 발행한 MBO 표준 작업 지시서
├── README.md               # 프로젝트 종합 안내서 및 동료평가자 시연 가이드
├── RETROSPECTIVE.md        # 아키텍트-에디터 입체적 개발 회고록
├── tests/
│   ├── verify.py           # DoD 5대 완료 요건 원클릭 독립 기계 채점기 (100점 테스트 스위트)
│   └── test_result.txt     # DoD 기계 채점 실행 결과 보고서 (자동 생성)
└── src/
    ├── __init__.py         # 패키지 네임스페이스
    ├── git_manager.py      # [DoD-1] Git 명령어 실행, 저장소 검증 및 status/diff 안전 수집
    ├── ai_client.py        # [DoD-2, 3] Safe-Mode 마스킹, diff 절단, OpenAI HTTP 통신
    ├── formatter.py        # [DoD-3] 커밋 메시지 및 PR 템플릿 마크다운 포맷팅
    └── main.py             # [DoD-4] argparse 기반 CLI 엔트리포인트 및 에러 오케스트레이션
```

### 모듈별 상세 역할 및 인터페이스 계약

| 모듈 파일 | 주요 클래스 / 함수 | 핵심 책임 |
| :--- | :--- | :--- |
| `src/git_manager.py` | `GitManager` | `subprocess.run`을 통한 Git 작업 트리 상태 검증, `is_git_repo()`, `get_status()`, `get_diff(staged=True/False)` 제공. |
| `src/ai_client.py` | `AIClient` | `mask_sensitive_data()` 정규식 다층 필터링, `truncate_diff()` 500라인 상한 제어, 표준 `urllib.request` 기반 지수 백오프 3회 재시도 HTTP 클라이언트. |
| `src/formatter.py` | `OutputFormatter` | AI 응답의 여백 정제, Conventional Commits 헤더 검증, Why/What/How 마크다운 섹션 규격화. |
| `src/main.py` | `parse_args()`, `run_cli()` | `--staged`, `--pr`, `--dry-run`, `--model` CLI 플래그 파싱 및 의미론적 프로세스 종료 코드(Exit Code 0/1) 반환. |

---

## 3. 핵심 보안 & 아키텍처 원칙 (Safe-Mode)

외부 AI API를 호출하는 개발 도구의 특성상, **데이터 안전성과 실행 무결성**을 최우선 가치로 설계했습니다.

```
[Git 변경사항 수집]
       │
       ▼
[Safe-Mode 1단계: 정규식 민감정보 마스킹] ──▶ API Key, 토큰, 비밀번호, Private Key 자동 제거 ([MASKED])
       │
       ▼
[Safe-Mode 2단계: Diff 상한 절단 방어]    ──▶ 최대 500라인 상한 적용 및 누락 라인 수 명시
       │
       ▼
[Safe-Mode 3단계: Bounded API Retry]     ──▶ 429/5xx 에러에 대해 최대 3회 제한적 재시도
       │
       ▼
[Safe-Mode 4단계: Dry-Run 모드 지원]     ──▶ 실제 API 호출 없이 정제된 프롬프트 데이터만 사전 점검
```

1. **다층 정규식 민감정보 마스킹**:
   - `OPENAI_API_KEY` 환경변수 자체는 물론, `sk-`, `ghp_`, `github_pat_`, `AKIA` 등 주요 클라우드 토큰 패턴을 자동 감지합니다.
   - PEM 형식의 RSA/EC Private Key 블록, `Bearer`/`Basic` 인증 헤더, URL 내 임베디드 자격증명(`https://user:pass@host`)을 사전에 `[MASKED]`로 치환합니다.
2. **토큰 폭증 방어 (Diff Budgeting)**:
   - 변경사항이 500줄을 초과할 경우 상위 500줄까지만 안전하게 절단하고, `[truncated: N lines omitted]` 안내를 삽입하여 LLM 컨텍스트 초과 및 비용 폭탄을 방지합니다.
3. **무의존성 표준 라이브러리 설계**:
   - `openai` SDK 설치 없이 순수 Python 표준 라이브러리(`urllib.request`, `json`, `re`)만으로 HTTP 통신을 구현하여, 어떤 환경에서도 `pip install` 없이 즉시 실행됩니다.

---

## 4. 주요 기술 스택

- **언어 및 런타임**: Python 3.10+ (타입 힌팅 `Final`, `str | None` 적극 활용)
- **VCS 연동**: Git CLI (`subprocess` 안전 파이프라이닝)
- **AI 백엔드**: OpenAI Chat Completions API (`gpt-4o-mini`, 모델 교체 가능)
- **테스트 프레임워크**: Python 표준 `unittest`, `unittest.mock`

---

## 5. 설치 및 환경 설정 가이드

### 1) 저장소 클론
```bash
git clone https://github.com/yerihanview/B3-2.git
cd B3-2
```

### 2) OpenAI API 키 설정
본 프로젝트는 보안을 위해 **환경변수(`OPENAI_API_KEY`)**를 통해서만 자격증명을 주입받습니다.  
코드 내에 키를 절대 하드코딩하지 마세요.

```bash
# macOS / Linux / GitHub Codespaces
export OPENAI_API_KEY="sk-your-actual-api-key"

# Windows PowerShell
$env:OPENAI_API_KEY="sk-your-actual-api-key"
```

> **API 키가 없는 경우**: 아래의 `--dry-run` 플래그를 사용하면 과금이나 API 키 없이도 모든 프롬프트 생성 로직과 정제 과정을 완벽히 검증할 수 있습니다.

---

## 6. CLI 사용법 및 옵션 레퍼런스

```bash
python src/main.py [OPTIONS]
```

### 지원 옵션

| 플래그 | 형태 | 설명 |
| :--- | :--- | :--- |
| `--staged` | boolean 플래그 | `git add`된 스테이징 영역의 변경사항을 대상으로 분석합니다 (기본: Unstaged 변경사항). |
| `--pr` | boolean 플래그 | 커밋 메시지 대신 **Why / What / How to Test** 마크다운 PR 설명을 생성합니다. |
| `--dry-run` | boolean 플래그 | **실제 API를 호출하지 않고**, 마스킹 및 500줄 절단 처리가 완료된 프롬프트 데이터를 미리보기로 출력합니다. |
| `--model MODEL` | 문자열 (기본: `gpt-4o-mini`) | 사용할 OpenAI 모델명을 지정합니다 (예: `gpt-4o`, `gpt-4o-mini`). |

---

## 7. 독립 기계 채점기 (`verify.py`) 100점 채점 스위트

구현 에디터(챗GPT)의 환각을 방지하고 코드 무결성을 입증하기 위해, 구현체와 완전히 격리된 독립 블랙박스 단위·통합 검증기 `verify.py`를 제공합니다.

### 기계 검증 항목
- **DoD-1 Git 수집 검증**: `GitManager` 인터페이스 완비 및 정상 Git 저장소 판별 기능 모의 검증.
- **DoD-2 Safe-Mode 검증**: `OPENAI_API_KEY` 및 민감 토큰 정규식 마스킹 정상 치환, 600라인 초과 diff의 500라인 절단 정상 동작.
- **DoD-3 Formatter 검증**: Conventional Commits 헤더(`feat:`, `fix:` 등) 포맷 및 PR 마크다운 섹션(Why, What, How) 조립 무결성.
- **DoD-4 CLI 인터페이스 검증**: `argparse` 파서의 `--staged`, `--pr`, `--dry-run` 플래그 독립 해석 기능.

### 원클릭 채점 실행
```bash
python tests/verify.py
```
> 채점 결과는 콘솔에 출력됨과 동시에 `tests/test_result.txt` 파일에 타임스탬프와 함께 자동 보존됩니다.

### 채점 결과
```
============================================================
🚀 B3-2 DoD 원클릭 기계 채점기 가동 중...
============================================================
test_git_manager_interface (TestDoD1_GitManager) ... ok
test_git_repo_check (TestDoD1_GitManager) ... ok
test_sensitive_masking (TestDoD2_SafeMode) ... ok
test_truncate_diff (TestDoD2_SafeMode) ... ok
test_format_commit_and_pr (TestDoD3_Formatter) ... ok
test_cli_parser (TestDoD4_CLI) ... ok

----------------------------------------------------------------------
Ran 6 tests in 0.178s

OK

============================================================
🎉 [100/100 PASS] 모든 5대 DoD 기계 검증을 완벽히 통과했습니다!
➔ 다음 단계: Step 4 리팩토링 체크리스트 및 Step 5 README 작성을 진행하세요.
============================================================
```

---

## 🚀 8. 동료평가자용 3분 퀵스타트 시연 시나리오

동료평가자께서는 아래 4단계 명령어를 터미널에 그대로 복사·붙여넣기하여 프로젝트의 모든 기능을 3분 이내에 검증하실 수 있습니다.

### [Step 1] 독립 기계 채점기 1초 100점 검증
```bash
python tests/verify.py
```
> **기대 결과**: 6개 테스트 통과, `[100/100 PASS]` 출력 및 `tests/test_result.txt` 생성.

### [Step 2] 안전한 Dry-Run 커밋 메시지 프리뷰 (API 키 불필요)
```bash
python src/main.py --dry-run
```
> **기대 결과**: 현재 저장소의 `git status` 및 `git diff`가 민감정보 마스킹된 상태로 정돈되어 출력.

### [Step 3] Staged 변경사항 기반 PR 템플릿 생성 프리뷰
```bash
python src/main.py --staged --pr --dry-run
```
> **기대 결과**: Staged 내역에 대한 마스킹된 Why/What PR 프리뷰 정상 출력.

### [Step 4] 실제 API 연동 커밋 메시지 생성 (선택 사항)
```bash
export OPENAI_API_KEY="sk-..."
python src/main.py
```
> **기대 결과**: Conventional Commits 규격의 명쾌한 커밋 메시지 자동 생성 출력.
