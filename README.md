# 승진점수 계산기

전국 17개 시·도 초등교사가 교감 승진 관련 예상 점수를 계산하고 개인 기록을 보관하는 Django 웹 애플리케이션입니다.

공식 평정 시스템이 아니라 대략적인 점수 확인과 포트폴리오 관리를 위한 도구입니다. 실제 제출 전에는 반드시 해당 연도의 교육청 자료와 담당 기관 확인을 거쳐야 합니다.

## 현재 구현 범위

- 아이디 기반 회원가입·로그인과 개인 기록 저장
- 비로그인 사용자의 브라우저 localStorage 기반 점수 계산(서버·계정 기록에는 저장하지 않음)
- 첫 로그인 시 내 지역 선택, 계정별 대표 지역 1개 유지
- 전라남도 2026년 기준 경력평정, 근무성적평정, 연수성적평정, 공통가산점, 선택가산점
- 나머지 16개 지역은 경력·근무성적·연수·공통가산점의 9개 입력 항목과 기본 계산 제공 (선택가산점 제외, 교육청별 원문 대조 전)
- 모든 점수 영역을 지역·연도별 독립 계산 모듈에서 처리하며 미등록 지역·연도는 계산 차단
- 항목별 독립 입력과 학교·기관·기간별 복수 기록
- 항목명, 설명, 간단 계산식, 입력값, 계산 점수, 메모·증빙 보유 여부
- 1급 정교사 자격연수 현재 평정점과 9점까지의 보완 범위 표시
- 한국사능력검정·관련 연수를 점수가 아닌 별도 자격요건으로 관리
- 항목별 기록 모아보기와 점수 변화 기록
- 현재 규정 요약과 전남 공식 매뉴얼 열람
- 전국 지역 선택, 회원·비회원 입력, 지역별 계산 근거와 검증 상태 표시

지역 간 비교·백분위 기능은 아직 포함하지 않았습니다. 추후 구현 시 계정의 대표 지역 데이터만 비교 집단에 반영하도록 데이터 구조를 분리했습니다.

공통가산점도 지역별 모듈에 포함됩니다. '공통'이라는 분류를 이유로 다른 지역의 계산 규칙을 적용하지 않습니다. 17개 지역의 2026년 모듈을 등록했으며 서로 다른 지역 모듈을 가져오는 별칭·상속 구조를 사용하지 않습니다.

**입력 기능 제공과 교육청 원문 검증은 구분됩니다.** 전남 외 16개 지역은 2026.2.28.에 적용되는 법령을 바탕으로 만든 기본 계산입니다. 연수 학점은 지역별 확정 상한 대신 법령 한도(학년도별 0.12점·총 1점)를 사용한다고 화면에 표시합니다. 각 교육청의 인정기간·경과조치·자격연수 대상자 선발 기준은 원문 확인이 필요합니다. 새 모듈의 자격연수는 교감 승진후보자명부 기준(교감 자격연수, 계수 0.05)이며 전남의 기존 대상자 선발 계산과 구분됩니다. 기존 전남 PDF 대조에서 발견한 미반영 조건도 별도 수정 대상입니다.

계산 모듈 구조와 지역 추가 방법은 [지역별 계산 구조](docs/architecture/regional-scoring.md)를 참고하세요.

## 로컬 실행

Python 3.11 이상을 권장합니다.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

일반 브라우저에서는 `http://127.0.0.1:8000/`을 엽니다. HTTP 주소를 자동으로 HTTPS로 바꾸는 브라우저나 Codex 앱 내 브라우저에서는 `http://127.0.0.1.nip.io:8000/`을 사용하세요.

테스트는 다음 명령으로 실행합니다.

```powershell
python manage.py test calc
python manage.py check
python manage.py makemigrations --check
```

## 배포 설정

운영 환경에서는 최소한 다음 환경변수를 설정해야 합니다.

```text
DJANGO_SECRET_KEY=충분히 긴 임의의 비밀키
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=example.com,www.example.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://example.com,https://www.example.com
```

전체 설정 예시는 [`.env.example`](.env.example)에 있습니다. 프로젝트 루트의 `.env`도 읽지만 Git에 포함되지 않으며, 운영에서는 배포 서비스나 운영체제의 보호된 환경변수 저장소를 사용하세요.

정적 파일 수집과 HTTPS 설정도 배포 환경에 맞게 추가하세요.

HSTS 관련 옵션은 HTTPS 구성이 완전히 확인된 뒤에만 활성화하세요. 특히 `DJANGO_SECURE_HSTS_PRELOAD=1`은 브라우저 사전등록 정책을 이해하고 되돌리기 어려운 영향을 검토한 경우에만 사용해야 합니다.

개인 기록은 기본적으로 프로젝트 루트의 `db.sqlite3`에 저장되지만 Git에는 포함되지 않습니다. 운영에서는 `DJANGO_DB_PATH`로 소스 코드 밖의 영구 저장 경로를 지정하고, 데이터베이스 백업과 접근 권한 정책을 별도로 마련하는 것을 권장합니다.

## 약관·관리자·감사로그

운영 전 `LEGAL_OPERATOR_NAME`과 `LEGAL_CONTACT`를 설정하고 이용약관·개인정보처리방침의 실제 운영 사실을 검토하세요. 값이 없으면 법률 화면은 개발용 초안 경고를 표시하며 production 배포 점검이 실패합니다. 신규 가입은 약관·개인정보 동의 버전과 시각을 별도 기록합니다.

마이그레이션 뒤 관리자 역할은 먼저 미리보고 적용합니다.

```powershell
python manage.py setup_governance_roles
python manage.py setup_governance_roles --apply
```

이용자 행동 로그는 기본적으로 꺼져 있습니다. 실제 저장 경로의 접근권한, 프록시 신뢰, 달력 기준 3개월 보존 근거와 정기 실행을 확인한 뒤 `USER_ACTION_LOG_ENABLED=1`로 활성화하세요. 파기 명령도 기본은 미리보기입니다.

```powershell
python manage.py prune_user_action_logs
python manage.py prune_user_action_logs --apply
```

운영 기록과 이용자 행동 로그는 각각 `/manage/operations/`, `/manage/user-actions/`에서 별도 권한으로 조회합니다. 앱 설정과 서버 적용의 상세 점검표는 `docs/governance/SERVER-REVIEW.md`를 따릅니다.

## 규정 자료

전남 원문은 앱의 **평정업무 자료** 메뉴에서 열 수 있습니다. 나머지 지역은 해당 화면에 기본 계산의 법령 출처와 원문 검증 미완료 상태를 표시합니다. [지역별 적용·검증 현황](docs/reviews/2026-regional-baseline-status.md)을 참고하세요.
