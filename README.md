# B3-2: 내가 고친 코드 설명을 AI가 대신 써주는 도우미 (AI Git Helper)

> **코디세이 AI 올인원 2기 실전 미션 B3-2**  
> **수석 아키텍트**: 우광택 (@yerihanview)  
> **방법론**: 린 에이전틱 3자 분업 (수석 아키텍트 - 참모 토토 - 에디터 챗GPT)

---

## 1. 프로젝트 개요 및 과제 목표

개발자가 작업한 코드 변경사항(`git status`, `git diff`)을 정밀하게 수집·정제한 뒤, 대규모 언어 모델(OpenAI API)을 연동하여 **Conventional Commits 규격의 명확한 커밋 메시지**와 **Why / What / How to Test 구조화 PR 템플릿**을 원클릭으로 자동 생성하는 안전한 고성능 Python CLI 도구입니다.

### 핵심 해결 과제
1. **커밋/PR 작성 피로도 해소**: 변경 내역 기반 맥락 파악 및 일관된 시맨틱 커밋 메시지 생성.
2. **원천적 정보 유출 차단 (Safe-Mode)**: 프롬프트 전달 전 민감 정보(API Key, 토큰, 비밀번호 등)의 자동 마스킹. 기본 ON이며 `--safe-mode` / `--no-safe-mode`로 명시 제어.
3. **토큰 폭증 및 비용 방어**: 초대형 diff 발생 시 지능적인 500라인 상한 및 절단(Truncate) 처리.
4. **무의존성 포터블 아키텍처**: 외부 서드파티 패키지 설치 없이 Python 3.10+ 표준 라이브러리만으로 즉시 구동.
5. **엄격한 공식 루브릭 준수**: 커밋 제목 72자 제한, PR 제목 80자 제한(단어 경계 보존 절단), Why/What/How to Test **섹션별 최소 1개 불릿 강제**, temperature/max_tokens 제어 완비.

> 📖 **[탑다운 종합 기술 아키텍처 해설서 (전체 도식 완전 수록)](docs/TECHNICAL_GUIDE.md)**  
> 시스템 개요부터 Git diff 파이프라인, Safe-Mode 보안, LLM 통신, 프롬프트 엔지니어링, 에러 핸들링까지 6대 핵심 영역을 탑다운 방식으로 해설합니다.

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
├── docs/                   # 전체 도식(20종) 및 탑다운 기술 아키텍처 해설서
│   ├── TECHNICAL_GUIDE.md  # 20종 도식 기반 탑다운 종합 기술 해설서
│   └── *.png               # 개념 인포그래픽 14종 + 시스템 실측 도식 6종
├── tests/
│   ├── verify_code.py      # 공식 요구사항 25대 전수 기계 채점기 (100점 테스트 스위트)
│   ├── verify.py           # 하위 호환 프록시 어댑터 (verify_code.py 호출)
│   └── test_result.txt     # 기계 채점 실행 결과 보고서 (자동 생성)
└── src/
    ├── __init__.py         # 패키지 네임스페이스
    ├── git_manager.py      # [DoD-1] Git 명령어 실행, 저장소 검증 및 status/diff 안전 수집
    ├── ai_client.py        # [DoD-2, 3] Safe-Mode 마스킹, diff 절단, OpenAI HTTP 통신, 파라미터 제어, 원인별 예외
    ├── formatter.py        # [DoD-3] 커밋 메시지(72자 제한) 및 PR 템플릿(80자 제한, 섹션별 불릿 강제) 규격화
    └── main.py             # [DoD-4] argparse 기반 CLI (서브커맨드 + 플래그, safe-mode, temperature, max-tokens)
```

### 모듈별 상세 역할 및 인터페이스 계약

| 모듈 파일 | 주요 클래스 / 함수 | 핵심 책임 |
| :--- | :--- | :--- |
| `src/git_manager.py` | `GitManager` | `subprocess.run`을 통한 Git 작업 트리 상태 검증, `is_git_repo()`, `get_status()`, `get_diff(staged=True/False)` 제공. |
| `src/ai_client.py` | `AIClient`, `AIClientError` 계열 | `mask_sensitive_data()` 정규식 다층 필터링, `truncate_diff()` 500라인 상한 제어, `prepare_input()` Safe-Mode 일괄 적용, `temperature`, `max_tokens` 주입, 표준 `urllib.request` 기반 **지수 백오프(1s→2s) 3회 재시도**, 401/403·429·5xx·네트워크 오류의 원인별 예외(`AuthenticationError`·`RateLimitError`·`ServerError`·`NetworkError`). |
| `src/formatter.py` | `OutputFormatter` | AI 응답의 여백 정제, Conventional Commits 헤더 및 72자 상한 검증, PR 제목 80자 **단어 경계 보존 절단**, 빈 제목 거부, Why/What/How to Test **섹션별 불릿 1개 이상 강제**. |
| `src/main.py` | `parse_args()`, `run_cli()` | `commit`/`pr` 서브커맨드와 `--pr` 플래그 동시 지원, `--safe-mode`/`--no-safe-mode`, `--staged`, `--dry-run`, `--model`, `--temperature`, `--max-tokens` 파싱 및 의미론적 프로세스 종료 코드(Exit Code 0/1) 반환. |

---

## 3. 핵심 보안 & 아키텍처 원칙 (Safe-Mode)

외부 AI API를 호출하는 개발 도구의 특성상, **데이터 안전성과 실행 무결성**을 최우선 가치로 설계했습니다. Safe-Mode는 기본 활성화이며, 명시적 CLI 스위치로만 끌 수 있습니다.

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
[Safe-Mode 3단계: Bounded API Retry]     ──▶ 429/5xx 에러에 대해 1초→2초 지수 백오프로 최대 3회 재시도
       │
       ▼
[Safe-Mode 4단계: Dry-Run 프리뷰 모드]   ──▶ 과금 및 외부 통신 0건으로 마스킹 파라미터 사전 검증
```

* **`--safe-mode`(기본)**: 마스킹 + 500라인 절단을 모두 적용합니다.
* **`--no-safe-mode`**: 마스킹과 절단을 끄고 원문 diff를 전송합니다. 신뢰할 수 있는 입력에서만 사용하도록 실행 시 stderr에 경고를 출력합니다.
* **`--dry-run`**: API를 호출하지 않고, 마스킹·절단이 끝난 입력과 파라미터만 미리 보여줍니다. 실제 PR 초안이나 커밋 메시지를 생성하지는 않습니다.
* **한계 고지**: 정규식 마스킹은 알려진 패턴을 지우는 방어선이며 모든 유출을 수학적으로 보장하지 않습니다. 이름에 `token`·`secret`이 들어간 코드 식별자의 대입문까지 마스킹하는 과잉 마스킹이 발생할 수 있는데, 이는 안전 측으로 틀리는(fail-safe) 방향입니다.

---

## 4. 기술 스택

* **Language**: Python 3.10+ (Type Hinting 100% 준수)
* **Standard Libraries Only**: `argparse`, `urllib.request`, `subprocess`, `re`, `json`, `os`, `sys`, `time`, `unittest`
* **Zero Dependency**: `requirements.txt` 설치 없이 기본 파이썬 환경에서 즉시 구동 가능

---

## 5. 환경 설정 및 API 키 보안

보안 표준에 따라 실제 API Key는 리포지토리에 절대 포함되지 않으며, `.gitignore`에 등록되어 커밋이 원천 차단됩니다.  
B3-2는 **의존성 0개의 순수 파이썬 내장 `.env` 파일 로더**를 탑재하여, 프로젝트 루트의 `.env` 파일에 기록된 키와 Base URL을 자동으로 감지합니다. 터미널마다 일일이 `export` 명령어를 입력할 필요가 없습니다.

### 5-1. 방법 1: 코디세이 Public API 연동 (추천: 무료 토큰 제공)
코디세이 올인원 수강생에게 제공되는 무료 Public API 키를 사용하면 개인 사비 지출 없이 즉시 실측 테스트가 가능합니다:
```bash
# 1. 설정 템플릿 복사
cp .env.example .env

# 2. .env 파일에 코디세이 키 및 엔드포인트 설정
OPENAI_API_KEY=sk-cody-live-your-key-here
OPENAI_BASE_URL=https://copa.codyssey.kr/v1
```

### 5-2. 방법 2: OpenAI 공식 API 연동
```bash
cp .env.example .env
OPENAI_API_KEY=sk-your-openai-api-key-here
```

### 5-3. 방법 3: 터미널 환경변수 직접 주입 (선택사항)
```bash
export OPENAI_API_KEY="your-api-key-here"
export OPENAI_BASE_URL="https://copa.codyssey.kr/v1"  # 코디세이 API 사용 시
```

> 💡 **참고**: API 키가 없어도 `--dry-run` 플래그를 사용하면 외부 통신 및 과금 0건으로 전체 마스킹·절단·파라미터 파이프라인을 100% 검증할 수 있습니다.

---

## 6. CLI 옵션 레퍼런스

### 6-1. 진입점 및 호출 방식 (모듈 실행·설치형 CLI·루트 래퍼 3대 다중 호환)

표준 패키지 모듈 실행(`python -m git_agent`), 설치형 전역 CLI(`git-agent`), 그리고 공식 미션지 호환용 루트 `main.py` 어디서든 동일하게 실행 가능합니다:

```bash
# 1. 패키지 모듈 실행 (Python 표준 CLI)
python -m git_agent commit [OPTIONS]
python -m git_agent pr     [OPTIONS]

# 2. 설치형 전역 CLI (pip install -e . 실행 후)
git-agent commit [OPTIONS]
git-agent pr     [OPTIONS]
cg commit        [OPTIONS]    # 단축 명령어

# 3. 루트 진입점 (공식 미션지 규격 하위 호환)
python main.py commit [OPTIONS]
python main.py pr     [OPTIONS]
python main.py --pr   [OPTIONS]
python main.py        [OPTIONS]   # 기본값: commit
```

#### 공식 미션지 준수: 최종 출력 구획화 (Delimiters)
출력 결과는 사용자가 명확히 구분하여 검토할 수 있도록 공식 미션지 예시 그대로 구획 구분선과 헤더가 표시됩니다:
* 커밋 메시지: `--- Commit Message ---` ~ `----------------------`
* PR 설명: `--- PR Title ---` 및 `--- PR Body ---` ~ `---------------`

#### 미추적 파일(Untracked Files) 지능형 감지
`git diff`에 잡히지 않는 새로 생성된 파일(`??`)이 있을 경우, "변경 사항이 없다"고 끝내지 않고 미추적 파일 목록을 출력하며 `git add <file>`을 실행하도록 친절히 안내합니다.

```bash
# 실전 예시 (패키지 모듈 실행 python -m git_agent 또는 git-agent 콘솔 명령)
python -m git_agent commit --staged
python -m git_agent pr --staged --temperature 0.7 --max-tokens 1500
python -m git_agent pr --dry-run               # 마스킹된 입력 미리보기 (API 호출 없음)
python -m git_agent commit --no-safe-mode      # 신뢰된 입력에서만 사용
# (하위 호환 지원: python main.py commit 실행도 100% 동일하게 동작)
```

### 6-2. 지원 옵션

| 인자 | 형태 | 기본값 | 설명 |
| :--- | :--- | :--- | :--- |
| `commit` \| `pr` | 위치 인자(선택) | `commit` | 출력 종류를 고르는 서브커맨드. 생략하면 커밋 메시지. |
| `--pr` | boolean 플래그 | `False` | `pr` 서브커맨드와 동일. 기존 호출 방식과의 하위 호환용. |
| `--safe-mode` | boolean 플래그 | `True` | 민감정보 마스킹 + 500라인 절단을 켭니다(기본값이므로 생략 가능). |
| `--no-safe-mode` | boolean 플래그 | `False` | Safe-Mode를 끕니다. `--safe-mode`와 동시 사용 불가(상호 배타). |
| `--staged` | boolean 플래그 | `False` | `git add`된 스테이징 영역의 변경사항을 대상으로 분석합니다 (기본: Unstaged 변경사항). |
| `--dry-run` | boolean 플래그 | `False` | **실제 API를 호출하지 않고**, 마스킹·절단이 끝난 입력과 파라미터를 미리보기로 출력합니다. |
| `--api-base URL` | 문자열 | `OPENAI_BASE_URL` 환경변수 또는 `https://api.openai.com/v1` | 커스텀 API Base URL을 지정합니다 (예: `https://copa.codyssey.kr/v1`). |
| `--model MODEL` | 문자열 | `gpt-4o-mini` | 사용할 AI 모델명을 지정합니다 (OpenAI: `gpt-4o-mini`, `gpt-4o` / 코디세이: `gemini-3-flash`, `gpt-5.4-mini` 등). |
| `--temperature N` | 부동소수점 | `0.2` | AI 생성 창의성 조절 (0.0 ~ 2.0). |
| `--max-tokens N` | 정수 | `1000` | 생성될 최대 토큰 수 제한(프롬프트 길이는 줄이지 않음). |

### 6-3. 오류는 원인별로 갈라서 안내합니다

| 상황 | 예외 | 사용자가 보는 안내 (요지) | 재시도 |
| :--- | :--- | :--- | :--- |
| API Key 누락 | `ValueError` | `OPENAI_API_KEY`를 설정하라는 안내, 종료 코드 1 | 없음 |
| HTTP 401 | `AuthenticationError` | 키가 없거나·틀리거나·폐기됨. 키 확인 후 재시도 | 없음(즉시 종료) |
| HTTP 403 | `AuthenticationError` | 이 키로 해당 모델 사용 권한 없음. 권한/모델 변경 | 없음 |
| HTTP 429 | `RateLimitError` | 속도·할당량 초과. 대기·요청 빈도 축소·결제/한도 확인 | 1초 → 2초 백오프 후 최대 3회 |
| HTTP 5xx | `ServerError` | 제공자 측 서버 오류. 잠시 후 재시도 | 1초 → 2초 백오프 후 최대 3회 |
| 연결 실패/타임아웃 | `NetworkError` | 네트워크·VPN/프록시·방화벽 확인 | 1초 → 2초 백오프 후 최대 3회 |
| 그 외 4xx | `AIClientError` | 요청 자체가 거부됨 + 제공자 메시지 요약 | 없음 |
| AI 출력 형식 위반 | `ValueError` | 커밋 헤더·제목 길이·PR 불릿 조건 위반 사유를 그대로 출력 | 없음 |

---

## 7. 파라미터 비교: temperature와 max_tokens

`temperature`는 **어떤 후보를 뽑을지(확률 분포의 날카로움)** 를, `max_tokens`는 **생성 길이의 상한**을 바꿉니다. 둘 다 프롬프트 내용은 바꾸지 않습니다.

### 7-1. 이 저장소에서 실제로 측정한 값 (로컬 실측)

측정 환경: Python 3.12.16, 2026-11-07 측정, 대표 diff 120줄 + status 2줄 기준. `OPENAI_API_KEY`가 없는 빌드 환경이므로 **모델 호출 없이, 우리 코드가 만들어내는 요청 본문까지**를 측정했습니다.

| 측정 항목 | temp=0.2 | temp=0.7 | temp=0.2 / max_tokens=300 |
| :--- | :--- | :--- | :--- |
| 요청 `temperature` 필드 | `0.2` | `0.7` | `0.2` |
| 요청 `max_tokens` 필드 | `1000` | `1000` | `300` |
| 프롬프트 길이 | 5,871자 | 5,871자 | 5,871자 |
| 프롬프트 토큰 추정(문자÷4) | 약 1,467 | 약 1,467 | 약 1,467 |
| HTTP 페이로드 크기 | 6,572 bytes | 6,572 bytes | 6,571 bytes |

측정에서 확인된 사실:

1. `temperature`를 0.2 → 0.7로 바꿔도 **프롬프트와 페이로드가 동일**합니다. 달라지는 것은 요청 JSON의 `temperature` 값 하나뿐입니다.
2. `max_tokens`를 1000 → 300으로 낮춰도 **프롬프트는 줄지 않습니다**(약 1,467 토큰이 그대로 전송됨). `max_tokens`는 응답(완성) 길이의 상한일 뿐, 입력 비용을 깎는 수단이 아닙니다.
3. 600줄 diff는 Safe-Mode에서 **501줄(500줄 + `[truncated: 100 lines omitted]`)** 로 잘립니다. 입력 비용을 실제로 줄이는 장치는 `max_tokens`가 아니라 이 절단(truncate)입니다.

### 7-2. 0.2와 0.7이 만드는 출력 차이 (해석 — 실측 아님)

아래는 API의 샘플링 동작에 근거한 해석이며, 이 저장소의 실측 수치가 아닙니다. 키가 있는 환경에서 7-3 절차로 확인할 수 있습니다.

| 관점 | `--temperature 0.2` (기본) | `--temperature 0.7` |
| :--- | :--- | :--- |
| 성격 | 결정론적 요약. 같은 diff에 거의 같은 문장 | 표현이 매번 달라지는 창의적 설명 |
| 커밋 메시지 | 타입/스코프가 안정적, 반복 실행 시 결과 편차 작음 | 어조·부연이 늘고, 가끔 제목이 길어져 72자 검증에 걸릴 확률 상승 |
| PR 본문 | `### Why`/`### What`/`### How to Test` 형식 준수율 높음 | 섹션은 지키되 불릿 대신 문단이 섞이거나 불릿이 빠질 확률 상승 → `format_pr()`의 불릿 검증에서 `ValueError`(종료 코드 1) |
| 추천 용도 | 실제 커밋·PR 초안, CI/자동화 | 데모에서 "AI가 설명을 쓴다"는 느낌을 보여줄 때 |

`temperature`가 높을수록 형식 위반 확률이 올라가지만, 이 도구는 형식을 **사후 검증**하므로 위반된 출력이 그대로 나가지 않습니다(불릿 0개 → 거부, 섹션 누락 → `- Not provided` 보완).

### 7-3. max_tokens 예산 감각

| 출력 종류 | 대략 소요(완성 토큰) | 권장 `--max-tokens` | 너무 작게 줄이면 |
| :--- | :--- | :--- | :--- |
| 커밋 메시지(제목+본문) | 100 ~ 300 | `1000`(기본) 충분 | 본문이 문장 중간에 끊김 |
| PR 설명(제목+3섹션 불릿) | 400 ~ 800 | `1200 ~ 1500` | `How to Test`가 잘려 불릿 검증 실패 또는 섹션 누락 보완 |

### 7-4. 실측 절차 (API 키가 있는 환경에서 그대로 실행)

```bash
export OPENAI_API_KEY="sk-..."

# 1) temperature 0.2 vs 0.7을 각 3회씩 생성해 흔들림을 비교
for t in 0.2 0.7; do
  for i in 1 2 3; do
    python src/main.py pr --temperature "$t" --max-tokens 1500 > "/tmp/pr_${t}_${i}.md"
  done
done

# 2) max_tokens 상한의 영향(잘림 여부) 확인
python src/main.py pr --max-tokens 300 > /tmp/pr_300.md

# 3) 기록할 지표: 제목 길이(≤80), 섹션별 불릿 개수(≥1), 전체 길이, 3회 반복 결과의 동일성
```

---

## 8. 독립 기계 채점기 (`verify_code.py`) 100점 채점 스위트

공식 요구사항을 100% 전수 검증하기 위해, 외부 의존성 없이 모의(Mock) 환경에서 즉시 실행되는 **25대 독립 테스트 스위트**를 제공합니다.

### 25대 기계 검증 항목
1. **Git 수집 검증**: `GitManager` 인터페이스 완비 및 정상 Git 저장소 판별 기능 모의 검증.
2. **Safe-Mode 마스킹 검증**: `OPENAI_API_KEY` 및 민감 토큰 정규식 마스킹 정상 치환.
3. **Diff 절단 검증**: 500라인 초과 diff의 안전한 상한 절단 동작.
4. **Conventional Commits 헤더 검증**: 시맨틱 커밋 헤더(`feat:`, `fix:` 등) 포맷 무결성.
5. **커밋 제목 길이 검증**: 커밋 제목 72자 상한 제한 검증.
6. **PR 제목 및 섹션 검증**: PR 제목 80자 상한, Why/What/How to Test 섹션 존재 및 누락 시 불릿 보완.
7. **CLI 파라미터 검증**: `--temperature`, `--max-tokens`, `--model` 파싱 및 바인딩.
8. **Safe-Mode Dry-Run 검증**: `--dry-run` 플래그의 파라미터 미리보기 및 API 미호출 격리.
9. **Git 변경 없음 경계 검증**: 변경사항이 없을 때 안전한 안내 및 정상 종료 (Exit Code 0).
10. **API 페이로드 무결성 검증**: HTTP 요청 바디에 모델명, 온도, 토큰 상한 정확한 주입 확인.
11. **PR 불릿 0개 거부**: 섹션은 있으나 불릿이 0개인 "빈 껍데기"를 `ValueError`로 거부, `*` 불릿·중첩 불릿은 허용.
12. **PR 제목 단어 경계 절단·빈 제목 거부**: 80자 초과 시 단어 중간이 잘리지 않고, 제목이 없으면 거부.
13. **`--safe-mode` 기본값·효과**: 기본 ON, `--no-safe-mode`로 마스킹·절단 해제, 두 플래그 상호 배타.
14. **HTTP 401 분기**: 인증 실패 안내(키 확인) 즉시 종료, 재시도 없음.
15. **HTTP 429 분기**: 3회 재시도 + 실제 백오프 대기(1초→2초) + 할당량 초과 안내.
16. **HTTP 5xx 분기**: 백오프 후 성공 시 복구, 지속 실패 시 서버 오류 안내.
17. **네트워크 오류 분기**: 연결 실패를 `NetworkError`로 구분하고 점검 항목 안내.
18. **서브커맨드 파싱**: `commit`/`pr` 위치 인자와 `--pr` 플래그의 호환, 잘못된 서브커맨드 거부.
19. **`pr` 서브커맨드 E2E**: `python main.py pr` 경로가 포맷팅된 PR 텍스트를 출력.
20. **인증 실패 종료 코드**: 401 안내 메시지 출력과 종료 코드 1.
21. **`--no-safe-mode` 프롬프트**: Safe-Mode 해제 시 원문이 그대로 전송되고, 기본 모드에서는 마스킹됨.
22. **최종 출력 구획화 검증**: 공식 미션지 필수 항목인 `--- Commit Message ---`, `--- PR Title ---`, `--- PR Body ---` 구분선 헤더 출력 검증.
23. **미추적 파일(Untracked) 안내**: diff가 비어 있어도 신규 미추적 파일(`??`) 감지 시 `git add` 유도 안내 출력 검증.
24. **루트 진입점(`main.py`) 래퍼 검증**: 루트 `python main.py` 실행 시 `git_agent.cli.run_cli`로의 온전한 바인딩 및 구동 검증.
25. **표준 패키지 레이아웃 및 `pyproject.toml` 검증**: `src/git_agent` 네임스페이스 격리, `python -m git_agent` 모듈 실행 및 `[project.scripts]` 콘솔 엔트리포인트 무결성 검증.

### 원클릭 채점 실행
```bash
python tests/verify_code.py
# (하위 호환 지원: python tests/verify.py 실행도 동일하게 지원)
```
> 채점 결과는 콘솔에 출력됨과 동시에 `tests/test_result.txt` 파일에 자동 보존됩니다.

---

## 🚀 9. 동료평가 시연 시나리오 (단계별 복붙 발표 가이드)

동료평가 발표 시 터미널에서 아래 6단계를 하나씩 복사·붙여넣기하며 B3-2의 전체 기능이 개발자의 실제 작업 라이프사이클 속에서 자연스럽게 흘러가는 모습을 시연하고 설명하실 수 있습니다.  
(엔터(Enter)를 누를 때마다 단계별 설명과 함께 순차 진행되는 대화형 스크립트를 원하실 경우 루트의 `bash demo.sh`를 실행하셔도 동일한 6단계 시연이 완벽히 지원됩니다.)

> 💡 **참고**: 내부 검증 기준인 `tests/verify_code.py` 25대 항목 전수 검증은 시연 대본과 무관한 내부 채점 스위트이므로 제8장을 참조하시기 바랍니다.

---

## 🚀 9. 동료평가 시연 시나리오 (8단계 복붙 발표 가이드)

동료평가 발표 시 터미널에서 아래 8단계를 하나씩 복사·붙여넣기하며 B3-2의 전수 핵심 기능이 개발자의 실제 작업 라이프사이클 속에서 자연스럽게 흘러가는 모습을 시연하고 설명하실 수 있습니다.  
모든 시연 파일은 **`demo/` 디렉토리 내부에서만 격리 생성 및 삭제**되므로 루트 워킹 트리가 항상 100% 무결점으로 깨끗하게 유지됩니다.  
(엔터(Enter)를 누를 때마다 단계별 설명과 함께 순차 진행되는 대화형 스크립트를 원하실 경우 루트의 `bash demo.sh`를 실행하시면 동일한 8단계 대화형 시연이 완벽히 지원됩니다.)

> 💡 **참고**: B3-2는 `src/git_agent` 표준 패키지로 설계되어 `python -m git_agent`로 품격 있게 시연합니다. (루트의 `python main.py`도 100% 하위 호환됩니다.)

---

### [Step 0] 사전 환경 확인 및 패키지 설정 (선택 사항)
코디세이 무료 Public API 키 또는 OpenAI 키가 `.env` 파일에 설정되어 있으면 실제 AI 커밋/PR 생성이 호출되며, 키가 없는 환경이라도 `--dry-run` 플래그를 통해 과금 0원에 모든 보안·포맷 기능을 100% 검증하실 수 있습니다.
```bash
# 1. 패키지 편집 가능 설치 (어디서나 git-agent 및 python -m git_agent 사용 가능)
pip install -e .

# 2. 코디세이 무료 API 키 설정 예시 (.gitignore에 의해 커밋 제외됨)
cat << 'EOF' > .env
OPENAI_API_KEY=sk-cody-live-your-key-here
OPENAI_BASE_URL=https://copa.codyssey.kr/v1
EOF
```

---

### [Step 1] 변경 사항 없음 (Empty Diff) 정상 방어 시연
- 📌 **발표 설명 멘트**: "작업 트리에 아무런 변경 사항이 없을 때, 예외 에러로 뻗지 않고 친절한 안내를 출력하며 정상 종료(Exit Code 0)합니다."
- 💻 **실행 명령어**:
```bash
python -m git_agent commit
```
- 🔍 **확인 포인트**: `"No changes in the selected diff. Stage new files with git add first."` 안내가 출력되고 에러 없이 정상 종료(0)됨을 확인합니다.

---

### [Step 2] 신규 파일 생성 및 미추적 파일(Untracked File) 지능형 감지 시연
- 📌 **발표 설명 멘트**: "새 파일을 만들고 `git add`를 깜빡했을 때, `git diff`는 비어있지만 미추적 파일(`??`)을 지능적으로 감지하여 `git add`를 유도합니다."
- 💻 **실행 명령어**:
```bash
touch demo/untracked_sample.py
python -m git_agent commit
rm -f demo/untracked_sample.py
```
- 🔍 **확인 포인트**: `No changes in the selected diff, but untracked files were detected: ? demo/untracked_sample.py. Please stage new files with 'git add <file>' first.` 안내가 출력됨을 확인합니다.

---

### [Step 3] Safe-Mode vs --no-safe-mode 민감정보 마스킹 대조 시연 (과금 0원 Dry-Run)
- 📌 **발표 설명 멘트**: "시연용 유틸리티 코드(`demo/calculator.py`)에 실수로 하드코딩된 API 키를 포함시킵니다. 기본 Safe-Mode에 의해 `[MASKED]`로 안전 치환되는 모습과, `--no-safe-mode` 적용 시 평문이 노출되는 차이를 대조하여 B3-2의 보안 유효성을 입증합니다."
- 💻 **실행 명령어**:
```bash
cat << 'EOF' > demo/calculator.py
"""시연용 수학 유틸리티 모듈"""

def add(a: int, b: int) -> int:
    """두 정수의 합을 계산합니다."""
    return a + b

# 실수로 하드코딩된 민감정보 (Safe-Mode 마스킹 시연용)
AWS_SECRET_KEY = "AKIA1234567890EXAMPLE"
GITHUB_TOKEN = "ghp_1234567890abcdef1234567890abcdef12"
EOF

# 신규 파일 스테이징
git add demo/calculator.py

# 3-1. 기본 Safe-Mode (보안 활성화): [MASKED] 치환 확인
python -m git_agent commit --staged --dry-run

# 3-2. --no-safe-mode (보안 비활성화 대조): 원본 평문 노출 경고 확인
python -m git_agent commit --staged --dry-run --no-safe-mode
```
- 🔍 **확인 포인트**: 
  - 기본 모드에서는 `AWS_SECRET_KEY`와 `GITHUB_TOKEN`이 `[MASKED]`로 안전하게 치환되어 원천 차단됩니다.
  - `--no-safe-mode`에서는 `WARNING: Safe-Mode is off...` 경고와 함께 원본 평문이 노출되어, Safe-Mode의 보안 보호 효과가 육안으로 대조 증명됩니다.

---

### [Step 4] 대용량 Diff 토큰 폭증 및 비용 방어 시연 (500줄 초과 절삭)
- 📌 **발표 설명 멘트**: "700줄 대용량 파일 생성 시, 프롬프트 토큰 폭증과 무분별한 API 과금을 막기 위해 diff가 500줄 상한에서 자동 절삭(Truncated)됨을 검증합니다."
- 💻 **실행 명령어**:
```bash
python -c "
with open('demo/token_overflow.txt', 'w', encoding='utf-8') as f:
    for i in range(1, 701):
        f.write(f'line_{i}: metric_data_sample_value_for_testing\n')
"
git add demo/token_overflow.txt

# 500줄 절단 미리보기 확인
python -m git_agent commit --staged --dry-run | tail -n 8

# 시연용 대용량 파일 정리
git reset HEAD demo/token_overflow.txt >/dev/null 2>&1
rm -f demo/token_overflow.txt
```
- 🔍 **확인 포인트**: 출력 끝부분에 `[truncated: ... lines omitted]` 안내가 출력되며 500줄에서 정확히 절삭되어 API 토큰/비용 폭증이 차단됨을 확인합니다.

---

### [Step 5] 미스테이징(Unstaged) vs 스테이징(Staged) 타겟팅 분리 실증
- 📌 **발표 설명 멘트**: "`demo/calculator.py`를 정상 코드로 정리한 뒤, 작업 트리(Unstaged)의 변경사항과 `git add`된 스테이징 영역(Index)이 `--staged` 옵션에 의해 정확히 분리 타겟팅되는지 확인합니다."
- 💻 **실행 명령어**:
```bash
# 정상 코드로 수정
cat << 'EOF' > demo/calculator.py
"""시연용 수학 유틸리티 모듈"""

def add(a: int, b: int) -> int:
    """두 정수의 합을 계산합니다."""
    return a + b

def multiply(a: int, b: int) -> int:
    """두 정수의 곱을 계산합니다."""
    return a * b
EOF

# 5-1. 작업 트리(Unstaged) 변경사항 타겟팅
python -m git_agent commit --dry-run | grep -E "(\+def|A  demo)"

# 5-2. git add 후 스테이징(Staged) 영역 타겟팅
git add demo/calculator.py
python -m git_agent commit --staged --dry-run | grep -E "(\+def|A  demo)"
```
- 🔍 **확인 포인트**: 기본 실행 시에는 작업 트리의 미스테이징 diff만 읽고, `--staged`를 지정하면 스테이징된 변경사항만을 정확히 타겟팅함을 확인합니다.

---

### [Step 6] 하이퍼파라미터 제어 실증 (--temperature, --max-tokens)
- 📌 **발표 설명 멘트**: "모델의 결정론성을 조절하는 temperature와 비용 상한인 max-tokens 파라미터가 CLI 옵션을 통해 실제 API 호출 페이로드로 완벽하게 주입됨을 검증합니다."
- 💻 **실행 명령어**:
```bash
# 결정론적 커밋 설정 (temp=0.0 / max_tokens=300)
python -m git_agent commit --staged --dry-run --temperature 0.0 --max-tokens 300 | head -n 4

# 창의적/대용량 PR 설정 (temp=0.8 / max_tokens=1500)
python -m git_agent commit --staged --dry-run --temperature 0.8 --max-tokens 1500 | head -n 4
```
- 🔍 **확인 포인트**: `Parameters: model=gpt-4o-mini, temp=0.0, max_tokens=300` 및 `temp=0.8, max_tokens=1500`으로 파라미터가 정확히 바인딩됨을 확인합니다.

---

### [Step 7] 공식 루브릭 커밋 메시지 자동 생성 시연 (Conventional Commits 72자)
- 📌 **발표 설명 멘트**: "공식 루브릭 규격인 Conventional Commits (`<type>(<scope>): <subject>`) 형식 및 헤더 72자 이하 제한을 준수하는 시맨틱 커밋 메시지를 생성합니다."
- 💻 **실행 명령어**:
```bash
# API 키 설정 시 실전 AI 호출 (최소 토큰 gemini-3-flash 권장)
python -m git_agent commit --staged --temperature 0.2 --model gemini-3-flash

# (참고: API 키 미설정 환경일 경우: python -m git_agent commit --staged --dry-run --temperature 0.2)
```
- 🔍 **확인 포인트**: `--- Commit Message ---` 구획선 안에 `feat(demo): add math utility functions for addition and multiplication`과 같은 시맨틱 커밋 헤더와 본문이 명확히 출력됨을 확인합니다.

---

### [Step 8] 공식 루브릭 PR 설명서 자동 생성 시연 (Why / What / How to Test 불릿 완비)
- 📌 **발표 설명 멘트**: "스테이징된 기능 변경사항에 대해 Why / What / How to Test 3대 필수 섹션과 각 섹션별 필수 불릿('- ')이 완비된 GitHub PR 설명서 초안을 자동 생성합니다."
- 💻 **실행 명령어**:
```bash
# PR 초안 생성 (3대 섹션 및 불릿 강제)
python -m git_agent pr --staged --temperature 0.2 --max-tokens 1500 --model gemini-3-flash

# (참고: API 키 미설정 환경일 경우: python -m git_agent pr --staged --dry-run --temperature 0.2 --max-tokens 1500)
```
- 🔍 **확인 포인트**: `--- PR Title ---` (80자 이하) 및 `--- PR Body ---` 구획선과 함께 `### Why`, `### What`, `### How to Test` 각 섹션별 최소 1개 이상의 불릿(`- `)이 완벽하게 지켜진 PR 문서가 출력됨을 확인합니다.

---

### [원상복구] 시연 종료 및 1초 클린업 (Clean up)
- 📌 **발표 설명 멘트**: "`demo/` 디렉토리 내부의 임시 파일을 삭제하고 저장소를 클론 직후의 100% 무결점 상태로 즉시 복원합니다."
- 💻 **실행 명령어**:
```bash
git reset HEAD demo/ >/dev/null 2>&1
rm -f demo/calculator.py
git status
```
- 🔍 **확인 포인트**: `nothing to commit, working tree clean` 상태로 깨끗하게 원상복구됨을 확인합니다.

---

### 💡 팁: 원클릭 대화형 엔터 시연 러너 (`demo.sh`)
명령어를 일일이 복사·붙여넣기하지 않고, 화면의 안내와 명령어를 보면서 **[엔터]를 누를 때마다 위 8단계가 하나씩 실행**되는 대화형 스크립트를 제공합니다:
```bash
bash demo.sh
```
- 각 단계별로 실행 명령어와 발표 포인트가 색상 배너로 표시되고, `[엔터]`를 누르면 실제 실행됩니다.
- 모든 파일이 `demo/` 디렉토리 안에서 격리 처리되며, 시연 도중 `Ctrl+C`로 중단하더라도 트랩 핸들러에 의해 임시 파일이 자동 정리되어 Git 워킹 트리가 항상 깨끗하게 유지됩니다.
- API 키가 감지되면 실제 생성을 호출하고, 미설정 시 안전하게 `--dry-run` 모드로 자동 시연합니다.

