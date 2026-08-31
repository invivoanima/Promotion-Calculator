# 승진점수 계산기

전라남도 초등교사가 교감 자격연수와 교감 승진을 준비하며 예상 점수를 계산하고 개인 기록을 보관하는 Django 웹 애플리케이션입니다.

공식 평정 시스템이 아니라 대략적인 점수 확인과 포트폴리오 관리를 위한 도구입니다. 실제 제출 전에는 반드시 해당 연도의 교육청 자료와 담당 기관 확인을 거쳐야 합니다.

## 현재 구현 범위

- 이메일 기반 회원가입·로그인과 개인 기록 저장
- 비로그인 사용자의 브라우저 localStorage 기반 점수 계산(서버·계정 기록에는 저장하지 않음)
- 첫 로그인 시 내 지역 선택, 계정별 대표 지역 1개 유지
- 전라남도 2026년 기준 경력평정, 근무성적평정, 연수성적평정, 공통가산점, 선택가산점
- 항목별 독립 입력과 학교·기관·기간별 복수 기록
- 항목명, 설명, 간단 계산식, 입력값, 계산 점수, 메모·증빙 보유 여부
- 1급 정교사 자격연수 현재 평정점과 9점까지의 보완 범위 표시
- 한국사능력검정·관련 연수를 점수가 아닌 별도 자격요건으로 관리
- 항목별 기록 모아보기와 점수 변화 기록
- 현재 규정 요약과 전남 공식 매뉴얼 열람
- 전국 지역 선택 화면 제공(현재 전남만 활성화)

지역 간 비교·백분위 기능은 아직 포함하지 않았습니다. 추후 구현 시 계정의 대표 지역 데이터만 비교 집단에 반영하도록 데이터 구조를 분리했습니다.

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

전체 설정 예시는 [`.env.example`](.env.example)에 있습니다. 이 프로젝트가 `.env` 파일을 자동으로 읽지는 않으므로 배포 서비스의 환경변수 설정 화면이나 운영체제 환경변수로 값을 주입하세요.

기본 비밀번호 재설정 메일은 개발용 콘솔 출력 방식입니다. 운영 환경에서는 `DJANGO_EMAIL_BACKEND`와 SMTP 관련 환경변수를 설정해야 합니다. 정적 파일 수집과 HTTPS 설정도 배포 환경에 맞게 추가하세요.

HSTS 관련 옵션은 HTTPS 구성이 완전히 확인된 뒤에만 활성화하세요. 특히 `DJANGO_SECURE_HSTS_PRELOAD=1`은 브라우저 사전등록 정책을 이해하고 되돌리기 어려운 영향을 검토한 경우에만 사용해야 합니다.

개인 기록은 기본적으로 프로젝트 루트의 `db.sqlite3`에 저장되지만 Git에는 포함되지 않습니다. 운영에서는 `DJANGO_DB_PATH`로 소스 코드 밖의 영구 저장 경로를 지정하고, 데이터베이스 백업과 접근 권한 정책을 별도로 마련하는 것을 권장합니다.

## 규정 자료

현재 화면과 간소화 계산식은 `2026. 승진후보자 평정업무 처리요령`을 바탕으로 구성했습니다. 원문은 앱의 **평정업무 자료** 메뉴에서 열 수 있습니다.
