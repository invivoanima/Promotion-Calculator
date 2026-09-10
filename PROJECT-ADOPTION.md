# 승진점수 계산기 공통 표준 적용표

적용 표준: PROJECT-GOVERNANCE-1.0 / 조사일: 2026-09-09 KST

**상태: 1차 앱 구현 및 자동 테스트 완료. 운영 설정·공개 법률 문서 확정·운영 적용은 미완료.** 첨부 문서는 평가 기준으로 사용했고, 2026-09-10 사용자의 구현 요청에 따라 코드 작업 범위를 확대했다.

## 1. 프로젝트와 작업 범위

| 항목 | 확인 결과 |
|---|---|
| 프로젝트 / project_slug | 승진점수 계산기 / `promotion-calculator` 제안(운영 디렉터리 이름은 운영자 확인 필요) |
| 담당자 / 확인일 | 저장소 조사: Codex / 2026-09-09. 운영 책임자 미확정 |
| 도메인 / 운영자 / 문의 | 도메인·법적 운영자 미확정. 로그인 회원 건의 `/suggestions/`; 비회원·탈퇴 후 연락처 없음 |
| 요청 범위 | 조사·문서·앱 1차 구현·자동 테스트. 운영 DB migration, 서버 설정, 로그 활성화, 공개 문서 최종 확정은 제외 |
| 서버 체인 / 실제 Caddy / 실행 | 저장소에 실제 Caddy 설정·서비스 실행 정의·운영 샘플 로그 없음. Cloudflare → Caddy → Waitress는 표준의 환경이며 이 프로젝트의 확인된 배포 사실이 아님 |
| 프레임워크 / DB | requirements: Django 5.2.17, Waitress 3.0.2. 로컬 SQLite 파일과 테이블 이름만 읽기 전용 확인. 운영 DB는 `DJANGO_DB_PATH`로 변경 가능; 실제 경로 미확정 |
| 개발·운영 | DEBUG 기반 일부 설정은 있으나 명시적 development/production 구분 없음. settings는 `.env` 로드; README의 ‘자동 로드하지 않음’과 불일치 |
| 법역 / 사업 / 연령 | 한국 교사 대상 도구. 적용 법역·사업자 지위·정보주체 규모·회원 연령 정책은 운영자 확인 필요. 교사 대상이라는 설명이 연령 제한 구현을 뜻하지 않음 |
| 약관 / 방침 / 가입 동의 | 활성 URL·템플릿·폼·모델에서 공개 문서, 동의 체크, 동의 버전·시각 저장을 찾지 못함. 별도 운영 사이트의 존재는 미확인 |

### 증거 색인

경로는 프로젝트 루트 기준이다. 실제 이용자 값은 읽거나 복사하지 않았다.

- E1: `promocalc/settings.py`, `promocalc/urls.py`, `requirements.txt`, `.env.example`, `README.md`: 활성 앱·배포 후보·실행 안내.
- E2: `calc/urls.py`, `calc/views.py`의 `register_view`, `login_view`, `logout_view`, `region_select`, `score_item`, `delete_score_record`, `korean_history`, `account_settings`, `delete_account`.
- E3: `calc/models.py`, `calc/forms.py`, `calc/migrations/`: 필드·CASCADE/SET_NULL·입력 검증.
- E4: `calc/views.py`의 `suggestion_*`, `staff_*`, `staff_required`; `calc/admin.py`: 소유권·관리 권한·변경 경로.
- E5: `calc/middleware.py`, `calc/management/commands/prune_access_logs.py`: GET HTML DB 기록, 오류 무시, 수동 90일 정리.
- E6: `calc/templates/calc/new/base.html`, `register.html`, `account_settings.html`, `staff/*.html`, `calc/static/calc/app.js`, `app.css`: 표시 내용·조회 UI·브라우저 저장.
- E7: `calc/tests.py`, `calc/test_features.py`: 기존 회귀 테스트. 이번 실행은 의존성 누락으로 시작 실패.
- E8: 로컬 `db.sqlite3`의 sqlite_master 테이블 목록만 읽기 전용 조회: `calc_accesslog`, `django_admin_log`, 계정·점수·건의 테이블 존재. 행 수·개인정보·실제 로그 원문 미열람. 운영 증거 아님.
- `static/` 아래 과거 Django 코드·템플릿은 활성 INSTALLED_APPS가 아니므로 현재 서비스 근거로 혼합하지 않음.

## 2. 처리 정보와 외부 서비스

아래 ‘계약 필요성’과 ‘정당한 이익’은 검토 후보이며 현재 확정된 법적 근거가 아니다. DB는 설정된 SQLite, 파일은 설정된 MEDIA_ROOT를 의미한다. 운영 백업과 서버 관리자의 실제 접근 범위는 미확정이다.

| 유형 | 실제 항목 / 목적·근거 | 경로 / 저장·열람 주체 / 공개 | 기간·기산점·파기 | 외부 전달 / 근거 |
|---|---|---|---|---|
| 계정 | 필수 이메일(username에도 저장), 표시 이름, 비밀번호 해시; 회원 ID·가입/로그인 시각·지역·권한. 인증·개인 기록 서비스, 계약 필요성 검토 | 가입·로그인·지역/계정 폼 → User/Profile/세션 DB. 본인·권한 있는 Django 관리자. staff 대시보드에 최근 username(신규 회원은 이메일) 표시. 일반 공개 회원 목록 없음 | 탈퇴 시 User/Profile CASCADE. DB 백업·세션 정리 주기 미확정. 동의 기록 없음 | 재설정 메일 전달 가능, 업체 미확정 / E1–4,6 |
| 작성물: 개인 점수 | 기관·학교 입력, 경력 기간·일자, 항목·수치·점수, 메모, 증빙 보유 여부·상태·지역 포트폴리오. 계산·기록 보관, 계약 필요성 검토 | ScoreRecord/ItemStatus/RegionPortfolio 및 기존 Common/Area 모델 DB. 본인 및 모델 권한 관리자. 공개 전환 없음 | 개별 기록 삭제·탈퇴; ScoreChange는 개별 기록 삭제 뒤에도 남고 탈퇴 시 CASCADE. 자동 기간 없음 | 외부 API 코드 없음 / E2,3 |
| 작성물: 자격·변화 기록 | 한국사 인증번호·등급·합격일, 연수기관/시간·근무 형태·메모·증빙 여부; 이전/새 점수·총점·시각. 자격 확인·변화 안내 | KoreanHistoryQualification/ScoreChange DB. 본인·모델 권한 관리자; 비공개 | 탈퇴 CASCADE. 별도 보유 기한 미정; 인증번호 필요성 재검토 | 외부 API 코드 없음 / E2,3 |
| 비회원 계산 | 위 입력의 일부, `guest_payload`(메모 포함). 일시 계산, 계약 체결 전 요청 처리 필요성 검토 | 브라우저 localStorage → POST → 서버 메모리 계산 → 응답. 계정 점수 DB에는 저장하지 않음. 브라우저 사용자·처리 서버 | localStorage는 초기화·브라우저 데이터 삭제까지, 자동 만료 없음. 서버 영구 저장 코드 없음; 프록시·오류/메일 로그의 본문 포함 여부 미확인 | 서비스 서버로 실제 전송; 외부 업체 경유 미확정 / E2,6 |
| 반응 | 좋아요 등 없음 | 생성·저장·공개 없음 | 비해당 | 비해당 / E2,3 |
| 신고 | 회원·게시물 위반 신고 없음. ‘오류 신고’는 건의 category=error | 아래 문의 흐름으로 처리; 별도 제재 판단 기능 아님 | 별도 신고 보존 비해당 | E3,4 |
| 문의·첨부 | 필수 유형/제목/내용, 선택 JPG/JPEG/PNG/WEBP/PDF 최대 100MB, 회원·지역·source_path·상태·관리자 메모·접수/완료 시각. 응대, 계약 필요성 검토 | `/suggestions/` → Suggestion DB, 파일 `media/suggestion/`. 본인·모든 staff 및 Django 모델 권한 관리자. 일반 공개 없음 | 탈퇴 시 DB CASCADE. 첨부 삭제 훅·교체 파일 정리 없음: 파일 잔존 우려. 완료 후 자동 파기 없음. 메모는 변경 이력이 아닌 덮어쓰기 | 실제 호스팅·백업 미확정 / E3,4 |
| 공지·자료 | 공지 제목/본문·게시/고정/일자; Manual 파일·uploader 텍스트, 번들 교육청 PDF. 안내 제공 | DB/MEDIA_ROOT 또는 정적 파일. 공개 공지만 익명 열람; 초안 관리자. 파일의 운영 제공 방식 미확정 | 공지 편집·Django admin 삭제 가능. 버전 보존·파일 정리 정책 없음 | 외부 조회 API 없음 / E3,4,6 |
| Caddy 접속 | 실제 항목·목적·근거 미확정 | 실제 파일·운영 열람자·공개 여부 미확인 | 회전·기산점·백업·파기 모두 운영 확인 | Cloudflare 경유 미확정 / E1 |
| 기존 앱 접속 통계 | user FK/인증 여부·route_name·지역·기기 분류·HTTP 상태·생성 시각. 방문 집계 목적, 회원 연결의 필요성·정당한 이익 평가 없음 | GET HTML → AccessLog DB. staff 화면은 회원 구분만, Django admin은 user 필드 접근 가능. IP·UA 원문·본문 저장 안 함 | 수동 `prune_access_logs --days` 기본 90일, 현재 자동 실행 미확인. 탈퇴 시 user SET_NULL, 나머지 잔존. 익명화 완료로 단정 불가 | 외부 분석 SDK 없음 / E3–6 |
| 이용자 행동 | 공통 action/대상/결과/UUID 이벤트 미구현 | 제안: 별도 JSONL, 지정 감사 권한자; 일반 공개 없음 | 달력 3개월 후보, 법적·운영상 근거 확정 전 활성화 금지 | 외부 전송 도입 없음 / E2–5 |
| 관리자 조치 | Django admin LogEntry 테이블 존재. `/staff/` 공지·문의 변경의 별도 감사 저장 없음 | 기본 admin 이력과 앱 조치 이력을 구분. Suggestion.admin_memo, ScoreChange는 대체 감사로그 아님 | 기본 admin 행의 실제 내용·보존 기간 미확인. 행위자 삭제에 따른 이력 영향 점검 필요 | 미확정 / E3,4,8 |
| 개인정보 접근 | 이메일 목록·문의/파일·개인 점수·자격 등 관리자 조회 가능. 별도 조회 이력 없음 | `/staff/`, `/admin/`, `suggestion_file`; 기존 middleware는 staff/admin 제외. 보안 의무 검토 대상 | 적용 고시·처리자 분류 확인 후 별도 기간 확정. 행동 로그 3개월을 그대로 적용하지 않음 | 자동 제공 없음 / E4,5,6 |

| 외부 서비스 | 사용 여부·기능 | 전송 정보 | 위탁·제공 역할 | 국외 이전 확인 | 방침 반영 |
|---|---|---|---|---|---|
| Cloudflare | 코드로 확정 불가 | 경유 시 요청/IP/헤더 등 실제 설정 확인 | 계약·제품별 미확정 | 처리 위치·계약 확인 필요 | ‘없음’ 선언 금지 |
| 호스팅·메일 | 호스팅 미확정; 비밀번호 재설정 지원, 기본 console backend | 메일 사용 시 수신 이메일·재설정 링크. 콘솔은 링크/토큰을 실행 출력에 남길 수 있음 | 실제 SMTP·호스팅 업체 확인 필요 | 미확정 | 업체·업무·위치 확인 뒤 반영 |
| 외부 API | 활성 계산은 서버 내 계산; 외부 검색/조회 API 없음 | 확인된 API 전송 없음 | 코드 범위 비해당 | 코드 범위 비해당 | 운영 삽입 서비스는 별도 확인 |
| 광고·분석·결제 | 외부 광고/분석/결제 코드 없음. 자체 접속 통계 있음 | 자체 AccessLog만 확인 | 외부 서비스 코드 범위 비해당 | 운영 구성 미확정 | 자체 통계는 자동 수집 항목에 포함 |

## 3. 문서 완전성

공개 약관·방침이 저장소에서 확인되지 않으므로 아래 ‘적용 결과’는 **작성 요구 또는 초안 위치**다. 현재 조항이 존재하거나 준수 완료했다는 뜻이 아니다. 문안은 `docs/governance/LEGAL-DRAFT.md` 참조.

| 표준 ID | 현재 조항·근거 | 상태 | 변경 또는 비해당 이유 | 적용 결과 |
|---|---|---|---|---|
| TERMS-01 | 문서 없음; README 서비스 설명 | 구현/개정 필요 | 운영자·회원·개인 기록 정의 필요 | 초안 T01, 운영자 미확정 |
| TERMS-02 | 문서/버전/동의 없음 E2,3,6 | 구현/개정 필요 | 게시·시행·변경 통지·동의 분리 | T02 |
| TERMS-03 | 이메일 가입 E2,3 | 미확정 | 실제 연령 정책·자격 제한 결정 필요 | T03, 교사 신분 검증한다고 쓰지 않음 |
| TERMS-04 | 점수/자격/자료/건의 E2 | 구현/개정 필요 | 예상 계산·기준연도·지원지역·중단 안내 | T04 |
| TERMS-05 | 공개 약관 없음 | 구현/개정 필요 | 계정 도용·무단 접근·타인 정보 입력 제한 | T05 |
| TERMS-06 | 비공개 점수·건의 E2–4 | 구현/개정 필요 | 권리 유지·서비스 처리 범위 한정; 공개 공유 없음 | T06 |
| TERMS-07 | 오류 신고만 E3,4 | 비해당 | 게시물 위반 신고·숨김·복구 기능 없음. 오류/권리 문의는 유지 | T07, 제재 자동화 도입 안 함 |
| TERMS-08 | is_active·admin 삭제; 제재 모델 없음 | 구현/개정 필요 | 계정 제한 권한은 존재; 사유·통지·이의·복구 절차 없음 | T08, 기간제 제재는 미구현으로 명시 |
| TERMS-09 | delete_account, CASCADE/SET_NULL | 구현/개정 필요 | 개인기록/건의 DB 삭제와 파일·통계 잔존 구분 | T09, 파일 파기 선행 |
| TERMS-10 | 교육청 매뉴얼·자체 계산 | 구현/개정 필요 | 공식 평정 보증 금지·자료 기준 안내 | T10 |
| TERMS-11 | AccessLog 자동 처리 E5 | 구현/개정 필요 | 방침과 실제 수집 일치; 향후 감사로그는 도입 후 안내 | T11 |
| TERMS-12 | 회원 건의만 존재 | 미확정 | 운영자·외부 문의·분쟁·적용 법역 확정 필요 | T12 |
| PRIV-01 | 문서·책임자·시행일 없음 | 미확정 | 운영자와 실제 게시일 미정 | P01 |
| PRIV-02 | 계정/점수/자격/문의/통계 E2–5 | 구현/개정 필요 | 비회원 POST·인증번호·첨부 포함 | P02 및 2절 |
| PRIV-03 | RegisterForm/입력 폼/미들웨어 | 구현/개정 필요 | 필수·선택·자동 생성·서버 처리 경로 구분 | P03 |
| PRIV-04 | 근거 문서 없음 | 미확정 | 계약 필요성·정당한 이익 평가·법정 의무 분리 | P04 |
| PRIV-05 | 탈퇴 및 90일 수동 명령만 | 미확정 | 유형별 기산점·기간·예외·무트래픽 처리 결정 | P05 및 6절 |
| PRIV-06 | 파일/백업 파기 미구현·미확인 | 구현/개정 필요 | DB 삭제를 전체 파기로 설명할 수 없음 | P06 |
| PRIV-07 | 외부 자동 제공 코드 없음 | 구현/개정 필요 | 적법 요청 확인·최소 제공·이력·보존 절차 필요 | P07 |
| PRIV-08 | 외부 검색 API 없음 E2 | 비해당 | 비회원 POST는 자체 서버 처리이며 외부 검색 API 아님 | P08 |
| PRIV-09 | SMTP 설정 가능·호스팅 미정 | 미확정 | 실제 위탁 업체 확인 필요 | P09 |
| PRIV-10 | 실제 프록시/처리 위치 미정 | 미확정 | 국외 이전 없음으로 단정 금지 | P10 |
| PRIV-11 | 개인 기록/문의 비공개, 공지 공개 | 구현/개정 필요 | 관리자 열람 범위와 외부 공개 구분 | P11 |
| PRIV-12 | 인증번호·자유 텍스트/파일; 연령 확인 없음 | 미확정 | 인증번호를 법정 고유식별정보로 임의 분류하지 않음. 자유 입력의 민감정보 위험·연령 방침 검토 | P12 |
| PRIV-13 | 세션/CSRF·localStorage·AccessLog | 구현/개정 필요 | 자체 통계 포함, 브라우저 삭제 방법·기능 영향 | P13 |
| PRIV-14 | 계정 수정·탈퇴·회원 건의만 | 구현/개정 필요 | 탈퇴 후 연락 경로·열람/정정/삭제/처리정지 절차 | P14 |
| PRIV-15 | 비밀번호 해시·CSRF·소유권 필터 | 구현/개정 필요 | HTTPS 설정 조건부, staff 일괄권한·감사/파일 파기 결함 | P15 |
| PRIV-16 | 책임자/개정 이력 없음 | 미확정 | 연락처·권리구제·버전 아카이브 필요 | P16 |

결제·환불·구독·광고·이용자 간 거래: 저장소상 비해당, 기능 도입 제안하지 않음. 비교·백분위도 README상 미구현이며 base 템플릿의 ‘비교·백분위에 사용’ 문구는 실제 기능보다 앞서 있어 정정 제안.

## 4. 메뉴·권한·UI

현재 `/staff/`는 `login_required` + `is_staff`; 기능별 permission 검사 없음. 기본 Django 인증 backend가 비활성 사용자를 제한하지만 별도의 활성 관리자·기능 권한 정책과 열린 세션 회수 테스트가 필요하다. `/admin/`에는 모델 권한이 있으나 마지막 최고관리자 보호 및 권한 상승 방지의 프로젝트별 제약은 없다.

| 공통 메뉴·권한 | 현재 경로·권한 | 제안 역할별 허용 | 표준과 차이 / 검증 |
|---|---|---|---|
| 대시보드 | `/staff/`, 모든 staff | 최고/운영/편집 모두 최소 통계; 개인정보는 별도 권한 | 최근 이메일 노출 제거 또는 권한 분리. 기존 테스트는 점수 원문만 검사 |
| 신고 관리 | 없음 | 비해당, 숨김 | 오류 건의와 위반 신고를 혼동하지 않음 |
| 작성물 관리 | `/admin/calc/scorerecord/` 등 모델 권한 | 개인 기록은 기본 운영/편집 열람 금지; 필요 최소 개인정보 담당자만 | 공개 콘텐츠 관리 메뉴로 전용하지 않음; 지원 조회는 회원 상세에서 제한 |
| 회원 관리 | `/admin/auth/user/`, Profile 등 | 최고 권한 관리; 운영은 별도 개인정보 권한 시 제한 조회 | 마지막 최고 보호·역할 상승 차단 필요 |
| 작품/대상 관리 | `/admin/calc/manual/`; catalog는 코드 | ‘평정 자료 관리’로 매핑, 편집/최고 | 도메인 명칭만 변경 허용. 계산 규정 서버 편집 도구는 추가하지 않음 |
| 공지 관리 | `/staff/notices/`, staff | 편집 초안 생성/수정; 운영 게시/종료; 최고 전체 | is_published 기본 True, 초안/게시/종료 구분·게시 권한 필요 |
| 문의 관리 | `/staff/suggestions/`, staff; 파일도 staff면 허용 | 지정 문의 담당 운영/최고만; 편집자 금지 | 공통 메뉴 ‘문의 관리’ 사용, 설명에 건의 포함. 접수/확인 중/완료 및 재개 유지·이력 추가 |
| 역할 관리 | `/admin/auth/group/`, `/admin/auth/user/` | 최고만, 마지막 최고 보호 | 편집 가능한 user_permissions/groups/is_superuser로 상승하지 못하도록 통합 검증 |
| 운영 기록 | 기본 admin LogEntry; 전용 화면 없음 | 최고/지정 감사 담당 읽기 | `/manage/operations/` 제안. staff 조치 추가, 편집·일괄 삭제 제외 |
| 이용자 행동 로그 / view_user_action_logs | 없음 | 최고/지정 감사 담당; 일반 운영·편집은 기본 불허 | `/manage/user-actions/`, `calc.view_user_action_logs` 그대로 |
| 실제 IP / view_user_action_network | 없음 | 최고 또는 명시적 네트워크 담당에게만; 위 조회 권한도 필요 | `calc.view_user_action_network`; 전체 응답 마스킹 및 POST 검색 |
| 기존 접속 통계 | `/staff/access-logs/`, staff | 유지 여부 D01 결정 후 별도 통계 권한 | 행동 감사 화면으로 이름만 바꾸지 않음 |

전용 관리 기본 `/manage/` 신설 제안. `/staff/` 북마크는 GET 리다이렉트 매핑으로 유지하고 POST는 과도기 동일 권한 서비스에 연결(POST를 GET으로 바꿔 작업 유실시키지 않음). `/admin/`은 최고관리자용 모델 관리 진입으로 제한하는 안을 검토한다. 기존 경로를 영구 유지하기로 정하면 D02에 확정해야 한다.

현재 일반 사이드바·모바일 접기·사이트 복귀 링크는 있으나 관리 전용 메뉴 순서 없음. 접속 화면은 날짜 필터·무제한 기간·최근 100건 잘라내기이고 페이지 이동 없음. 공통 행동 UI의 24시간·7일·50건, 필터/열 순서·실IP·커서·no-store·수집 상태·상세는 모두 미구현. 템플릿의 빈 상태가 수집 장애와 행동 부재를 구분하지 못한다. 모바일 시각·키보드·초점 검증 미실시. 정확한 목록·상세 설계는 `IMPLEMENTATION-PROPOSAL.md` 참조.

**개인정보 접근기록:** 포함 제안 대상은 대시보드 이메일, 회원/개인 점수/한국사 조회, 문의 목록·상세·첨부, Django admin 동일 조회, 향후 실IP 조회다. 현재 포함되지 않음. 다른 프로젝트의 ‘조회 이력 제외’는 적용하지 않는다. 의무 적용 범위·기간·고시 경과조치 판단은 운영자/개인정보 담당자가 확정해야 하며 미충족 위험을 열어 둔다.

## 5. 로그 이벤트 누락 검사

아래 action은 전부 **제안**, 현행 공통 행동 JSONL 기록은 없음. S=실제 변경 성공, F=입력/처리 실패, D=권한·기능 거부, N=변경 없음. 각 경로는 S/F/D/N 중 가능한 분기를 명시적으로 테스트하고 불가능한 분기는 이유를 남긴다. 성공 이벤트는 업무 트랜잭션 커밋 후, 식별자는 삭제·로그아웃 전에 값으로 복사한다. 테스트 열의 ID는 실행 결과가 아닌 필요한 검증이다.

| 기능·실제 경로 | action | 대상 ID 확보 시점 | 결과 분기 | 제안 기록 위치 / 테스트 |
|---|---|---|---|---|
| 가입 `/register/` | account.signup | User 저장 후 | S/F, 이미 로그인 N | RegisterForm 저장 서비스·view / TEST-04,05,12 |
| 로그인 `/login/` | auth.login | 인증 성공 User; 실패 null | S/F, 이미 로그인 N | auth.login 뒤, 폼 실패 / TEST-04,06 |
| 로그아웃 `/logout/` POST | auth.logout | auth.logout 전 User | S/비인증 N | logout_view / TEST-04 |
| 탈퇴 `/account/delete/` | account.delete | 삭제 전 User | S/F(확인문구)/D | delete_account 트랜잭션 / TEST-04,05 |
| 표시 이름 `/account/` | profile.update | Profile PK | S/F/D/N 동일 값 | account_settings / TEST-03,06 |
| 대표 지역 `/regions/` POST | profile.update | Profile PK; metadata 변경 필드명만 | S/F/N; 지역 입력 오류 | region_select / TEST-03 |
| 포트폴리오 생성 `_portfolio_for` | portfolio.create | get_or_create의 created=True PK | S; 기존 객체는 생성 이벤트 없음 | helper를 명시적 생성 서비스로 이동 / TEST-03,05 |
| 조회 지역 변경 `/regions/` | portfolio.view_region_change | 기존 portfolio PK 또는 null(비회원) | S/F/N 세션 변경 | region_select; 세션 ID 기록 금지 / TEST-06 |
| 점수 생성 `/score/<item>/` | score_record.create | save 후 PK | S/F/D | score_item; 지원하는 모든 ITEM_BY_CODE에 매개변수 테스트 / TEST-03,05 |
| 점수 수정 `/score/<item>/<id>/edit/` | score_record.update | 소유권 검증 후 PK | S/F/D/N 동일 값 | score_item / TEST-03,05 |
| 점수 삭제 `/score/record/<id>/delete/` | score_record.delete | delete 전 PK | S/D; 없는 대상은 not_found | delete_score_record / TEST-04,05 |
| 해당 없음 등 상태 설정 `/score/<item>/` | item_status.create/update | get_or_create 결과와 PK | S/F/D/N 동일 상태 | toggle_not_applicable 분기 / TEST-03 |
| 상태 해제 `/score/<item>/` | item_status.delete | 조회 후 삭제 전 PK | S/D/N 대상 없음 | clear_item_status 분기 / TEST-03,04 |
| 점수 저장 중 상태 자동 제거 | item_status.delete | 기존 상태 PK를 미리 확보 | 실제 삭제만 S | 점수 저장 서비스, 동일 request_id / TEST-03,05 |
| 한국사 `/qualification/korean-history/` | korean_history.create/update | 생성 결과·PK | S/F/D/N | GET의 get_or_create도 현재 변경임. POST 생성으로 이동 제안 / TEST-03,06 |
| Profile 자동 생성/지역 이관 | profile.create/update | get_or_create·이관 전후 | 실제 변경만 S | `_profile_for`, context_processor의 조회 부작용 분리 / TEST-03,05 |
| 문의 `/suggestions/`, `/suggestion/` | suggestion.create | 저장 후 PK | S/F/D; 중복도 현재 새 건 | suggestion_list / TEST-03,06; report.create로 오기하지 않음 |
| 공개 설정·반응·위반 신고 | 비해당 | 없음 | 없음 | 회원 공개 설정/반응/위반 신고 기능 없음; 문의는 위 행 |
| 비밀번호 재설정 요청 `/password-reset/` | auth.password_reset_request | null (이메일로 회원 추정 금지) | 외부 응답 계정 존재 비공개; 처리 F/S | Django 기본 view 확장 / TEST-04,06 |
| 비밀번호 재설정 완료 `/reset/<uidb64>/<token>/` | account.password_reset | 검증된 대상 ID | S/F/D | form_valid 이후; route 이름만, token/uid 경로 원문 금지 / TEST-04,06 |
| 비회원 `/try/`, `/try/<category>/` | 조회·재계산은 변경 이벤트 비해당 | 없음 | 계산 결과만 응답 | 매 hydration POST를 행동 변경으로 기록하지 않음 / TEST-06 |
| 비회원 `/try/item/<item>/`, edit/delete, `/try/reset/` | guest_score_record.create/update/delete, guest_calculation.reset 후보 | null; 클라이언트 key를 신뢰 ID로 수집하지 않음 | S/F/D/N | 브라우저 변경이며 수집 도입 필요성은 D04 미확정; 서버 응답은 브라우저 저장 성공을 보증 못 함 |
| 공지 생성·편집·공개/중지·고정/해제 `/staff/notices/...` | 운영 기록 notice.create/update/publish/unpublish/pin/unpin | Notice PK | S/F/D/N | 운영 감사 서비스 / TEST-01,03,05 |
| 문의 상태·메모 `/staff/suggestions/<id>/` | 운영 기록 suggestion.status_change/memo_update | Suggestion PK | S/F/D/N | 상태·행위자·시각, 메모 원문은 업무 DB에만 / TEST-01,03,05 |
| `/admin/` 생성·수정·삭제·일괄 처리 | 운영 기록 `<model>.create/update/delete` 및 권한 변경 | 저장 후/삭제 전 PK | S/F/D/N | ModelAdmin·공유 서비스; 기본 LogEntry 중복/연쇄삭제 검토 / TEST-01,04,05 |

ScoreChange는 결과 점수 변화의 서비스 데이터이며 위 이벤트를 대신하지 않는다. 없는 대상·타인 대상의 거부 이벤트가 실제 존재 여부를 응답으로 누설하지 않도록 고정 reason_code 사용. 미들웨어는 CSRF/라우팅 단계의 거부 문맥만 지원하고 HTTP 상태만으로 업무 성공을 생성하지 않는다.

## 6. 저장·IP·기간 결정

| 항목 | 현재 | 제안·결정 상태 |
|---|---|---|
| 경로 | AccessLog DB뿐 | 운영 `C:\caddy\logs\AuditLog\promotion-calculator\`, 개발 `<project_root>\.runtime\user-actions\`; 디렉터리는 아직 만들지 않음 |
| 환경 변수 | 감사 설정 없음 | `PROMOCALC_ENV`(미지정 development), `USER_ACTION_LOG_ENABLED`, `USER_ACTION_LOG_DIR`, `USER_ACTION_LOG_RETENTION_MONTHS`, `USER_ACTION_LOG_MAX_QUERY_DAYS=7`, `USER_ACTION_LOG_PAGE_SIZE=50`. 운영 production 명시·근거 확정 후 활성화 |
| 파일 / 스키마 | 없음 | `user-actions-YYYY-MM-DD.jsonl`, 파일 경계 KST 자정 제안, timestamp UTC / schema_version=1. 상세 계약은 구현 제안서 |
| IP 신뢰 | 앱 IP 수집 없음 | 실제 프록시·원본 차단 증빙 전 null/unknown. 사용자 CF/XFF 헤더를 곧바로 신뢰하지 않음 |
| request_id | 없음 | 서버 생성 UUID, 응답 X-Request-ID, Caddy 응답 헤더 연결. user_id 헤더 금지 |
| 행동 기간 | 없음 | 달력 3개월 후보; 목적·필요성·영향 평가와 적용법 검토 후 확정. 90일과 다름 |
| 경계 처리 | DB 정리는 now-90일 | KST 기준 달력 월 빼기, 해당 월 마지막 날로 clamp. 경계 파일은 미만 timestamp만 제거하고 보존 행을 잠금·임시파일·원자 치환으로 보존. 기준 이상은 유지 |
| 트리거·지연 | 수동 명령만 | 별도 일일 정리 + 기동 시 확인 + dry-run. 성공 스케줄 기준 추가 지연 24시간 이내 후보; 실패 시 초과 가능하므로 경보·복구 담당 필요. 운영 예약 작업 미적용 |
| 용량 회전 | 없음 | 일별 이름 유지. 임의 용량 삭제 금지. 예상 최대 크기·디스크 경보치 측정 후 확정; 분할이 필요하면 파일명·reader 편차 검토. 동시 writer 잠금 필요 |
| 백업·보존 예외 | 미확인 | 백업 사본별 만료·삭제 증거 관리. 적법 보존 사유/대상/담당/종료일을 분리, 정리 대상에서 통제된 제외 |
| 관리자 조회 이력 | 없음 | 별도 접근기록 설계·적용 의무 확인 후 기간 확정; 행동 로그 기간 재사용 안 함 |
| 오류·재시작 | AccessLog 오류를 무시 | 로그 쓰기 실패는 별도 오류/상태, 성공한 업무를 실패로 응답하지 않음. 재시작 후 상태 지속·손상 마지막 줄 감지 |

유형별 기간 최종 확정표는 아직 미완성이다: 계정/점수는 탈퇴 및 개별 삭제가 현재 기산 동작, 문의 완료 후 기간 미정, AccessLog는 수동 기본 90일일 뿐 보존 보장 없음, Caddy/Waitress/admin 이력/개인정보 접근기록/백업은 각기 운영·법적 근거 확인 필요. 현재 어떤 로그도 ‘3개월 자동 보존·자동 파기 완료’로 표시하지 않는다.

## 7. 표준 편차

미구현은 승인된 편차가 아니다. 다음 표의 ‘현행 차이’도 정당화 없이 유지하지 않는다.

| ID | 공통 기준 | 프로젝트 차이 | 필요한 이유 | 데이터·법률·운영 영향 | 대체 검증 | 확정 상태 |
|---|---|---|---|---|---|---|
| D01 | Caddy 접속, 앱 행동 JSONL | DB GET 접속 통계가 기존 대시보드 원천 | 기존 통계 연속성 검토 필요 | 추가 회원 연결 처리·중복 접속 수집; 통계 유지 시 목적/최소성/별도 기간 필요 | Caddy 집계 대체 가능성·지역/기기 필요성 검증 | 미확정. 기본 제안은 대체 후 DB 페이지뷰 신규 수집 중단; 기존 행 임의 삭제 안 함 |
| D02 | `/manage/` | `/staff/` + `/admin/` | 기존 URL 호환 | 권한 우회·이중 경로 관리 위험 | GET/POST 양쪽 동일 권한 회귀 | `/manage/`로 통합 제안; 영구 편차 미승인 |
| D03 | 신고·작성물·대상 메뉴 | 위반 신고/공개 작성물 없음, 대상은 평정 자료 | 개인 계산기 도메인 | 불필요한 공개/제재 기능 도입 방지 | URL·모델 인벤토리 | 비해당/명칭 매핑, 공통 필수 로그는 유지 |
| D04 | 인증 회원의 실제 행동 | 비회원 브라우저 데이터 변경 | 서버에 영구 기록 없는 기능 | IP 로그 신규 수집은 현재보다 수집 확대; 저장 성공도 서버에서 입증 불가 | 브라우저·서버 왕복과 저장 실패 검증 | 수집 여부 미확정, 몰래 활성화 안 함 |
| D05 | 별도 운영 감사모델 유지 | 전용 모델 없이 기본 admin LogEntry만 있음 | staff 변경까지 포함할 모델 필요 | 원문 object_repr·행위자 CASCADE 등 기존 admin 특성 검토 | 삭제/권한 변경/중복 로그 테스트 | 기존 이력 보존 + 최소 운영모델 신설 제안 |
| D06 | 앱 구현 후 검증·운영 | 1차 앱 구현과 자동 테스트 완료, 운영 미적용 | 운영 사실·운영자 정보 미확정 | 법적 적합·배포 완료 주장 불가 | 42개 자동 테스트, migration/check | 운영 적용 전 확인 필요 |

로그 원본 경로·schema v1·action 공통 계정 코드·필수 권한·24시간/7일/50건·UI 순서는 변경 제안하지 않았다.

## 8. 앱 작업과 서버 작업

| 앱 코드·문서 작업 | 현재 상태 | 검증 |
|---|---|---|
| 표준 사본·이 적용표·법률 초안·설계·서버 안내 | 문서 작성 완료, 비공개 검토용 | 개별 ID 12+16+12 누락 검사 |
| 공개 문서·동의 버전 | `/terms/`, `/privacy/`, 가입 필수 동의와 append-only 버전 기록 구현. 운영자 정보 미설정 시 초안 경고 | 신규 테스트 통과; 최종 문안·과거 버전 정책은 운영 전 검토 |
| 권한·운영 감사·파일 파기 | 기능별 Django permission, 역할 동기화 명령, 마지막 활성 최고관리자 보호, 공지/문의 운영 기록, 첨부 삭제 구현. 개인정보 조회 전용 이력은 미구현 | 신규 및 기존 테스트 통과; admin 전체 경로 감사 확대 필요 |
| JSONL 이벤트·조회·파기 도구 | schema v1 writer/reader, 서버 request_id, 주요 계정·점수·문의 이벤트, 24시간/최대 7일/50건 조회, no-store, 달력 월 정리 명령 구현. 기본 비활성 | 신규 테스트 통과; 동시 writer·상세·POST IP 검색·모든 이벤트 분기는 후속 필요 |

| 서버 설정·권한·실행 작업 | 실제 설정 확인 | 적용 상태 | 검증 |
|---|---|---|---|
| Caddy/Cloudflare/Waitress·원본 우회 | 미확인 | 미적용 | 서버 담당자 실제 설정·헤더 시험 |
| 감사 디렉터리 ACL·로그 회전·오류 출력 | 미확인 | 미적용 | 계정별 쓰기/조회/삭제 분리, 타 프로젝트 차단 |
| 정기 파기·백업·모니터링·시간 동기화 | 미확인 | 미적용 | 무트래픽·월말·실패·복구 시험 |
| 운영 환경변수·SMTP·배포 의존성 | 미확인 | 미적용 | 개발/운영 구분·console 메일 제거·고정 버전 확인 |

별도 안내: `docs/governance/SERVER-REVIEW.md`.

## 9. 검증 결과와 최종 보고

2026-09-10 실행: `.venv\Scripts\python.exe manage.py test calc --noinput` → **42개 통과**. `manage.py makemigrations --check --dry-run` → 변경 없음. `manage.py check` → 문제 없음. `check --deploy`의 개발 기본값 경고 6개는 운영 환경변수/HTTPS 확인 전 남아 있다. 운영 DB migration, 로그 활성화·삭제, 실제 회원 조치는 수행하지 않았다.

| ID | 결과·증빙 | 남은 검증 |
|---|---|---|
| TEST-01 | 부분 통과: 일반회원/권한 없는 staff 차단, 기능 permission, 마지막 최고 보호 코드 및 자동 테스트 | 역할 그룹 운영 적용·열린 세션 권한 회수 통합 시험 |
| TEST-02 | 회원 공개/운영 숨김·기간 제재는 기능 비해당. 문의 재개·공지 전환 코드 존재 | 문의 상태 이력·공지 초안/게시/종료 검증; 이 행 전체 통과 아님 |
| TEST-03 | 부분 통과: 점수 create/update/delete와 문의 create 구현 | 상태·지역·자격·noop 전 분기 |
| TEST-04 | 부분 통과: 로그인 실패 null, 로그아웃/탈퇴 전 ID 확보 구현 | 비밀번호 재설정 이벤트 |
| TEST-05 | 부분 통과: signup/점수/탈퇴 성공 on_commit, 파일 실패가 업무 응답을 변경하지 않음 | 명시적 롤백·디스크 부족 테스트 |
| TEST-06 | 기존 AccessLog는 route/기기 분류만. JSONL 미구현 | 비밀값·본문·메일·인증번호·reset token·쿼리 오염 테스트 |
| TEST-07 | 미검증: 서버 설정과 request_id 없음 | 위조 헤더·IPv4/6·Caddy 연결 |
| TEST-08 | 부분 구현: 달력 월·경계 행 보존·dry-run/apply 명령 | 동시 writer·잠금·재시작·윤년/월말 자동 테스트·운영 스케줄 |
| TEST-09 | 부분 통과: 전용 권한·기본 마스킹·no-store·필터 페이지 유지 | POST IP 검색·서명 커서·실IP 권한 테스트 |
| TEST-10 | 미충족: 수집 실패와 빈 상태 구별 없음 | 손상/미수집/상한/상태·모바일·키보드 |
| TEST-11 | 정적 불일치 확인: 공개 문서 없음, 비회원 서버 전송·첨부 잔존·이메일 표시 | 문안 확정 후 실제 삭제·보존·전송 검증 |
| TEST-12 | 미충족: 버전·동의·과거문서 없음 | 표시/동의 버전 일치, 아카이브·시행일 전환 |

사용자 화면에는 약관·방침 링크와 가입 필수 동의가 추가되며 신규 동의 버전을 저장한다. 관리자에는 기능별 권한, 운영 기록과 이용자 행동 로그 화면이 추가된다. 문의 삭제·탈퇴 시 첨부파일도 삭제한다. 과거 동의를 소급 생성하지 않으며 운영자 정보가 없으면 법률 화면에 개발 초안 경고를 표시한다.

남은 필수 확인 담당: 운영자(법적 명칭·연락처·도메인·연령·사업 형태·수집 목적), 서버 담당자(실제 체인·로그·ACL·SMTP·위탁·국외 위치·백업·스케줄), 개인정보 담당자/법률 검토자(근거·기간·고시 적용·권리구제), 구현 담당자(권한·파기·감사·조회·테스트). 개인정보 관리자 조회 이력은 면제 확정 없이 제외하지 않는다.

공통 개선 제안: 표준에 브라우저 보관/서버 일시 처리 구분, 기존 앱 접속 통계 전환, GET의 암묵적 DB 생성, 비회원 이벤트 수집 결정, Django admin 원문 object_repr와 계정삭제 이력 관계, 의존성 불일치에 따른 테스트 실패 보고 예시를 추가하면 다른 프로젝트의 오판을 줄일 수 있다. 다른 프로젝트에 자동 반영하지 않는다.
