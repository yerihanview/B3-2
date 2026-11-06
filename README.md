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
5. **엄격한 공식 루브릭 준수**: 커밋 제목 72자 제한, PR 제목 80자 제한, Why/What/How to Test 불릿 구조, temperature/max_tokens 제어 완비.

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
│   ├── verify.py           # 공식 요구사항 10대 전수 기계 채점기 (100점 테스트 스위트)
│   └── test_result.txt     # 기계 채점 실행 결과 보고서 (자동 생성)
└── src/
    ├── __init__.py         # 패키지 네임스페이스
    ├── git_manager.py      # [DoD-1] Git 명령어 실행, 저장소 검증 및 status/diff 안전 수집
    ├── ai_client.py        # [DoD-2, 3] Safe-Mode 마스킹, diff 절단, OpenAI HTTP 통신 및 파라미터 제어
    ├── formatter.py        # [DoD-3] 커밋 메시지(72자 제한) 및 PR 템플릿(80자 제한, 불릿) 규격화
    └── main.py             # [DoD-4] argparse 기반 CLI 엔트리포인트 (temperature, max-tokens 지원)
```

### 모듈별 상세 역할 및 인터페이스 계약

| 모듈 파일 | 주요 클래스 / 함수 | 핵심 책임 |
| :--- | :--- | :--- |
| `src/git_manager.py` | `GitManager` | `subprocess.run`을 통한 Git 작업 트리 상태 검증, `is_git_repo()`, `get_status()`, `get_diff(staged=True/False)` 제공. |
| `src/ai_client.py` | `AIClient` | `mask_sensitive_data()` 정규식 다층 필터링, `truncate_diff()` 500라인 상한 제어, `temperature`, `max_tokens` 주입, 표준 `urllib.request` 기반 지수 백오프 3회 재시도 HTTP 클라이언트. |
| `src/formatter.py` | `OutputFormatter` | AI 응답의 여백 정제, Conventional Commits 헤더 및 72자 상한 검증, PR 제목 80자 검증, Why/What/How to Test 불릿 섹션 규격화. |
| `src/main.py` | `parse_args()`, `run_cli()` | `--staged`, `--pr`, `--dry-run`, `--model`, `--temperature`, `--max-tokens` CLI 플래그 파싱 및 의미론적 프로세스 종료 코드(Exit Code 0/1) 반환. |

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
[Safe-Mode 4단계: Dry-Run 프리뷰 모드]   ──▶ 과금 및 외부 통신 0건으로 마스킹 파라미터 사전 검증
```

---

## 4. 기술 스택

* **Language**: Python 3.10+ (Type Hinting 100% 준수)
* **Standard Libraries Only**: `argparse`, `urllib.request`, `subprocess`, `re`, `json`, `os`, `sys`, `unittest`
* **Zero Dependency**: `requirements.txt` 설치 없이 기본 파이썬 환경에서 즉시 구동 가능

---

## 5. 환경 설정 및 API 키 보안

보안 표준에 따라 실제 API Key는 리포지토리에 절대 포함되지 않습니다.

```bash
# 1. 예시 설정 파일 확인
cat .env.example

# 2. 로컬 환경변수 등록 (선택사항, --dry-run 구동 시에는 불필요)
export OPENAI_API_KEY="your-api-key-here"
```

---

## 6. CLI 옵션 레퍼런스

```bash
python src/main.py [OPTIONS]
```

### 지원 옵션

| 플래그 | 형태 | 기본값 | 설명 |
| :--- | :--- | :--- | :--- |
| `--staged` | boolean 플래그 | `False` | `git add`된 스테이징 영역의 변경사항을 대상으로 분석합니다 (기본: Unstaged 변경사항). |
| `--pr` | boolean 플래그 | `False` | 커밋 메시지 대신 **Why / What / How to Test** 마크다운 PR 설명을 생성합니다. |
| `--dry-run` | boolean 플래그 | `False` | **실제 API를 호출하지 않고**, 마스킹 및 500줄 절단 처리가 완료된 프롬프트 데이터를 미리보기로 출력합니다. |
| `--model MODEL` | 문자열 | `gpt-4o-mini` | 사용할 OpenAI 모델명을 지정합니다 (예: `gpt-4o`, `gpt-4o-mini`). |
| `--temperature N` | 부동소수점 | `0.2` | AI 생성 창의성 조절 (0.0 ~ 2.0). |
| `--max-tokens N` | 정수 | `1000` | 생성될 최대 토큰 수 제한. |

---

## 7. 독립 기계 채점기 (`verify.py`) 100점 채점 스위트

공식 요구사항을 100% 전수 검증하기 위해, 외부 의존성 없이 모의(Mock) 환경에서 즉시 실행되는 10대 독립 테스트 스위트를 제공합니다.

### 10대 기계 검증 항목
1. **Git 수집 검증**: `GitManager` 인터페이스 완비 및 정상 Git 저장소 판별 기능 모의 검증.
2. **Safe-Mode 마스킹 검증**: `OPENAI_API_KEY` 및 민감 토큰 정규식 마스킹 정상 치환.
3. **Diff 절단 검증**: 500라인 초과 diff의 안전한 상한 절단 동작.
4. **Conventional Commits 헤더 검증**: 시맨틱 커밋 헤더(`feat:`, `fix:` 등) 포맷 무결성.
5. **커밋 제목 길이 검증**: 커밋 제목 72자 상한 제한 검증.
6. **PR 제목 및 섹션 검증**: PR 제목 80자 상한, Why/What/How to Test 불릿 섹션 검증.
7. **CLI 파라미터 검증**: `--temperature`, `--max-tokens`, `--model` 파싱 및 바인딩.
8. **Safe-Mode Dry-Run 검증**: `--dry-run` 플래그의 파라미터 미리보기 및 API 미호출 격리.
9. **Git 변경 없음 경계 검증**: 변경사항이 없을 때 안전한 안내 및 정상 종료 (Exit Code 0).
10. **API 페이로드 무결성 검증**: HTTP 요청 바디에 모델명, 온도, 토큰 상한 정확한 주입 확인.

### 원클릭 채점 실행
```bash
python tests/verify.py
```
> 채점 결과는 콘솔에 출력됨과 동시에 `tests/test_result.txt` 파일에 타임스탬프와 함께 자동 보존됩니다.

---

## 🚀 8. 동료평가자용 3분 퀵스타트 시연 시나리오

동료평가자께서는 아래 4단계 명령어를 터미널에 그대로 복사·붙여넣기하여 프로젝트의 모든 기능을 3분 이내에 검증하실 수 있습니다.

### [Step 1] 독립 기계 채점기 1초 100점 검증 (10대 항목 전수 All Pass)
```bash
python tests/verify.py
```
> **기대 결과**: 10개 테스트 전수 통과, `[100/100 PASS]` 출력 및 `tests/test_result.txt` 보존.

### [Step 2] Happy Path 기본 동작 시연 (파라미터 제어 및 Dry-Run 프리뷰)
```bash
python src/main.py --dry-run --temperature 0.7 --max-tokens 1500
```
> **기대 결과**: 주입된 파라미터와 마스킹된 Git diff 상태가 깔끔하게 출력됨 (API 과금 0원).

### [Step 3] Staged 변경사항 기반 Why/What/How to Test PR 템플릿 프리뷰
```bash
python src/main.py --staged --pr --dry-run
```
> **기대 결과**: Staged 내역에 대한 마스킹된 Why, What, How to Test 구조화 PR 프리뷰 정상 출력.

### [Step 4] 결과물 및 로그 확인
```bash
cat tests/test_result.txt
```
> **기대 결과**: 10개 테스트 통과 보고서 전문 열람.
