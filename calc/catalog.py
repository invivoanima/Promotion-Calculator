"""UI and scoring metadata for the current elementary-teacher calculator."""

from decimal import Decimal


CURRENT_RULE_YEAR = 2026


REGIONS = [
    {"code": "seoul", "name": "서울특별시", "implemented": False},
    {"code": "busan", "name": "부산광역시", "implemented": False},
    {"code": "daegu", "name": "대구광역시", "implemented": False},
    {"code": "incheon", "name": "인천광역시", "implemented": False},
    {"code": "gwangju", "name": "광주광역시", "implemented": False},
    {"code": "daejeon", "name": "대전광역시", "implemented": False},
    {"code": "ulsan", "name": "울산광역시", "implemented": False},
    {"code": "sejong", "name": "세종특별자치시", "implemented": False},
    {"code": "gyeonggi", "name": "경기도", "implemented": False},
    {"code": "gangwon", "name": "강원특별자치도", "implemented": False},
    {"code": "chungbuk", "name": "충청북도", "implemented": False},
    {"code": "chungnam", "name": "충청남도", "implemented": False},
    {"code": "jeonbuk", "name": "전북특별자치도", "implemented": False},
    {"code": "jeonnam", "name": "전라남도", "implemented": True},
    {"code": "gyeongbuk", "name": "경상북도", "implemented": False},
    {"code": "gyeongnam", "name": "경상남도", "implemented": False},
    {"code": "jeju", "name": "제주특별자치도", "implemented": False},
]

REGION_BY_CODE = {region["code"]: region for region in REGIONS}
IMPLEMENTED_REGION_CODES = {
    region["code"] for region in REGIONS if region["implemented"]
}

CATEGORIES = [
    {
        "code": "career",
        "name": "경력평정",
        "short_name": "경력",
        "max_score": Decimal("70"),
        "description": "학교와 기간별 경력을 가·나·다 경력으로 나누어 기록합니다.",
    },
    {
        "code": "work",
        "name": "근무성적평정",
        "short_name": "근무성적",
        "max_score": Decimal("100"),
        "description": "선택한 3개 평정연도의 점수를 최근 연도 순으로 반영합니다.",
    },
    {
        "code": "training",
        "name": "연수성적평정",
        "short_name": "연수성적",
        "max_score": Decimal("30"),
        "description": "자격연수, 직무연수, 연구실적을 서로 분리하여 입력합니다.",
    },
    {
        "code": "common_bonus",
        "name": "공통가산점",
        "short_name": "공통가산점",
        "max_score": Decimal("3.3"),
        "description": "공통가산점 네 항목을 각각 입력합니다.",
    },
    {
        "code": "regional_bonus",
        "name": "전남 선택가산점",
        "short_name": "선택가산점",
        "max_score": Decimal("9.5"),
        "description": "전남 초등교사에게 적용되는 선택가산점을 기록합니다.",
    },
]

CATEGORY_BY_CODE = {category["code"]: category for category in CATEGORIES}


def field(label, *, required=False, help_text="", input_type="text", **extra):
    return {
        "label": label,
        "required": required,
        "help_text": help_text,
        "input_type": input_type,
        **extra,
    }


ITEMS = [
    {
        "code": "career_history",
        "category": "career",
        "name": "경력평정",
        "max_score": Decimal("70"),
        "scope": "national",
        "formula": "각 기록의 인정 월수 × 경력별 월 점수 + 남은 일수 × 경력별 일 점수. 최근 15년 기본경력(최대 64점) + 그 이전 5년 초과경력(최대 6점) = 최대 70점",
        "description": "학교·기관별 근무기간을 추가하고 해당 기간의 기본·초과 경력과 가·나·다 등급을 선택합니다.",
        "fields": {
            "institution": field("학교·기관명", required=True),
            "start_date": field("시작일", required=True, input_type="date"),
            "end_date": field("종료일", required=True, input_type="date"),
            "variant": field(
                "경력 구분",
                required=True,
                input_type="select",
                help_text=(
                    "기본·초과: 평정기준일부터 거꾸로 최근 15년은 기본경력, 그 이전 5년은 초과경력입니다.\n"
                    "가경력: 정규 교사 경력과 인정되는 임용 전 군 경력 등.\n"
                    "나경력: 임용권자가 임용한 전임 기간제·임시교원·강사 경력.\n"
                    "다경력: 초등교사의 일반 경력에는 통상 사용하지 않으므로 교육청 확인이 있을 때만 선택하세요."
                ),
                choices=[
                    ("base_ga", "기본경력 · 가경력"),
                    ("base_na", "기본경력 · 나경력"),
                    ("base_da", "기본경력 · 다경력"),
                    ("excess_ga", "초과경력 · 가경력"),
                    ("excess_na", "초과경력 · 나경력"),
                    ("excess_da", "초과경력 · 다경력"),
                ],
            ),
        },
        "notes": [
            "초등교사 기준 정규 교사 경력은 주로 가경력, 전임 기간제·임시교원·강사 경력은 나경력으로 구분합니다.",
            "다경력은 초등교사의 일반 경력에는 통상 사용하지 않으므로 소속 교육청의 확인이 있을 때만 선택하세요.",
            "휴직 등 별도 인정비율이 필요한 기간은 실제 인정되는 기간만 나누어 입력하세요.",
            "이 계산기는 경력 기간을 월·일 단위로 간소화하여 계산합니다.",
        ],
    },
    {
        "code": "work_performance",
        "category": "work",
        "name": "근무성적평정",
        "max_score": Decimal("100"),
        "scope": "national",
        "formula": "최근 5개 평정연도 중 합산점이 높은 3개 연도를 선택한 뒤, 선택 연도 중 최근순으로 34% + 33% + 33% 반영",
        "description": "2026년 기준 최근 5개 평정연도(2021~2025학년도)의 합산점을 입력합니다. 그중 점수가 높은 3개 연도를 자동으로 선택합니다.",
        "fields": {
            "year": field("평정연도", required=True, input_type="number", min=2000, max=2100, step=1),
            "value": field("합산점", required=True, input_type="number", min=0, max=100, step="0.001"),
        },
        "notes": [
            "근무성적평정점과 다면평가 합산점은 사용자가 확인한 값을 직접 입력합니다.",
            "최근 5개 평정연도 중 유리한 3개 연도를 사용하며, 선택된 연도 안에서 최근순으로 34%, 33%, 33%를 적용합니다.",
        ],
    },
    {
        "code": "training_qualification",
        "category": "training",
        "name": "자격연수성적",
        "max_score": Decimal("9"),
        "scope": "national",
        "formula": "9 - (100 - 1급 정교사 자격연수성적) × 0.025",
        "description": "현재 1급 정교사 자격연수성적을 입력합니다.",
        "fields": {
            "label": field("연수명", help_text="예: 1급 정교사 자격연수"),
            "institution": field("연수기관"),
            "event_date": field("수료일", input_type="date"),
            "value": field("자격연수성적", required=True, input_type="number", min=0, max=100, step="0.01"),
        },
        "notes": [
            "입력한 1급 정교사 자격연수성적과 9점 만점까지 부족한 점수를 함께 표시합니다.",
            "전남 보직교사 추가경력에 따른 보완 가능 점수는 별도 항목에서 직접 입력합니다.",
        ],
    },
    {
        "code": "training_job",
        "category": "training",
        "name": "직무연수성적",
        "max_score": Decimal("18"),
        "scope": "national",
        "formula": "최고 원점수의 환산성적 × 6 ÷ 100 + 인정 연수 횟수 × 6점(최대 2회)",
        "description": "최근 10년 2개월 이내에 수료한 60시간 이상 직무연수를 등록합니다. 가장 높은 환산성적 한 건과 최대 2회의 이수실적을 반영합니다.",
        "fields": {
            "label": field("연수명", required=True),
            "institution": field("연수기관"),
            "event_date": field(
                "수료일",
                required=True,
                input_type="date",
                min="2016-01-01",
                max="2026-02-28",
                help_text="2026년 평정 기준 인정 기간: 2016.1.1. ~ 2026.2.28.",
            ),
            "value": field("연수성적", required=True, input_type="number", min=0, max=100, step="0.01"),
            "extra_value": field(
                "이수시간",
                required=True,
                input_type="number",
                min=60,
                max=1000,
                step=1,
                help_text="60시간 이상 직무연수만 인정됩니다.",
            ),
        },
        "notes": [
            "해당 직위에서 최근 10년 2개월 이내에 수료한 60시간 이상의 직무연수만 인정됩니다.",
            "동일·유사 과정 여부와 인정기관 여부는 사용자가 확인해야 합니다.",
            "한국사 자격요건에 사용한 연수라도 자동으로 가져오지 않으며 이 화면에서 별도로 입력합니다.",
        ],
    },
    {
        "code": "training_research",
        "category": "training",
        "name": "연구실적",
        "max_score": Decimal("3"),
        "scope": "national",
        "formula": "연구대회 입상점 또는 학위취득점 합계(최대 3점)",
        "description": "연구대회 입상실적과 학위취득실적을 각각 등록합니다.",
        "fields": {
            "label": field("실적명", required=True),
            "institution": field("주관기관·대학"),
            "event_date": field("취득·입상일", input_type="date"),
            "variant": field(
                "실적 구분",
                required=True,
                input_type="select",
                help_text="아래 점수표에서 연구대회 규모·등급·공동연구 인원 또는 학위 구분에 해당하는 점수를 확인해 선택하세요.",
                choices=[
                    ("score_3", "직무 관련 박사학위 · 3점"),
                    ("score_1_5", "직무 관련 석사 또는 그 밖의 박사 · 1.5점"),
                    ("score_1", "그 밖의 석사 · 1점"),
                    ("research_1_5", "연구대회 입상 · 1.500점"),
                    ("research_1_25", "연구대회 입상 · 1.250점"),
                    ("research_1_05", "연구대회 입상 · 1.050점"),
                    ("research_1", "연구대회 입상 · 1.000점"),
                    ("research_0_875", "연구대회 입상 · 0.875점"),
                    ("research_0_75", "연구대회 입상 · 0.750점"),
                    ("research_0_7", "연구대회 입상 · 0.700점"),
                    ("research_0_625", "연구대회 입상 · 0.625점"),
                    ("research_0_525", "연구대회 입상 · 0.525점"),
                    ("research_0_5", "연구대회 입상 · 0.500점"),
                    ("research_0_45", "연구대회 입상 · 0.450점"),
                    ("research_0_375", "연구대회 입상 · 0.375점"),
                    ("research_0_35", "연구대회 입상 · 0.350점"),
                    ("research_0_3", "연구대회 입상 · 0.300점"),
                    ("research_0_25", "연구대회 입상 · 0.250점"),
                    ("research_0_225", "연구대회 입상 · 0.225점"),
                    ("research_0_15", "연구대회 입상 · 0.150점"),
                ],
            ),
        },
        "notes": [
            "연구대회 입상실적이 한 학년도에 2회 이상이면 가장 높은 점수의 1회만 반영합니다.",
            "연구계획 수립연도와 입상연도가 다르면 입상연도를 기준으로 합니다.",
            "실제 인정 여부와 공동연구 인원은 표창장 사본 또는 수상 확인원을 기준으로 확인하세요.",
        ],
    },
    {
        "code": "common_research_school",
        "category": "common_bonus",
        "name": "연구학교 근무경력",
        "max_score": Decimal("1"),
        "scope": "regional",
        "formula": "월 0.018점 + 일 0.0006점(최대 1점)",
        "description": "교육부장관 지정 연구학교·시험학교 근무기간을 기록합니다.",
        "fields": {
            "institution": field("연구학교명", required=True),
            "start_date": field("시작일", required=True, input_type="date"),
            "end_date": field("종료일", required=True, input_type="date"),
        },
        "notes": ["동일 기간의 연구학교 근무경력은 중복하여 입력하지 않습니다."],
    },
    {
        "code": "common_foreign_institution",
        "category": "common_bonus",
        "name": "재외국민교육기관 파견 근무경력",
        "max_score": Decimal("0.5"),
        "scope": "regional",
        "formula": "월 0.015점 + 일 0.0005점(최대 0.5점)",
        "description": "재외국민교육기관 파견 근무기간을 기관별로 기록합니다.",
        "fields": {
            "institution": field("기관명", required=True),
            "start_date": field("시작일", required=True, input_type="date"),
            "end_date": field("종료일", required=True, input_type="date"),
        },
        "notes": [],
    },
    {
        "code": "common_training_credit",
        "category": "common_bonus",
        "name": "연수이수 학점 실적",
        "max_score": Decimal("0.8"),
        "scope": "regional",
        "formula": "15시간당 1학점, 1학점당 0.02점·연도별 최대 0.08점",
        "description": "학점화 대상 직무연수의 인정 학점을 연도별로 입력합니다.",
        "fields": {
            "label": field("연수명", required=True),
            "institution": field("연수기관"),
            "year": field("인정 연도", required=True, input_type="number", min=1998, max=2100, step=1),
            "value": field(
                "인정 학점",
                required=True,
                input_type="number",
                min=0,
                max=100,
                step="0.1",
                help_text="15시간당 1학점으로 계산합니다.",
            ),
        },
        "notes": ["연수성적평정이나 다른 국가기술자격에 사용한 실적은 중복 사용하지 않습니다."],
    },
    {
        "code": "common_school_violence",
        "category": "common_bonus",
        "name": "학교폭력 예방 및 대응 관련 실적",
        "max_score": Decimal("1"),
        "scope": "regional",
        "formula": "학년도별 0.1점(최대 1점)",
        "description": "학교폭력 예방 및 대응 실적을 학년도별로 기록합니다.",
        "fields": {
            "institution": field("학교명", required=True),
            "year": field("학년도", required=True, input_type="number", min=2013, max=2100, step=1),
        },
        "notes": ["해당 학년도 중 6개월 이상 근무한 교사 실적만 입력하세요."],
    },
    {
        "code": "jeonnam_island_remote",
        "category": "regional_bonus",
        "name": "1. 도서·벽지학교 근무경력",
        "max_score": Decimal("3"),
        "scope": "regional",
        "formula": "도서·벽지와 가·나·다·라 급지별 월·일 점수 합계(최대 3점)",
        "description": "학교와 기간별로 도서·벽지 구분과 급지를 선택합니다.",
        "fields": {
            "institution": field("학교명", required=True),
            "start_date": field("시작일", required=True, input_type="date"),
            "end_date": field("종료일", required=True, input_type="date"),
            "variant": field(
                "학교 구분·급지",
                required=True,
                input_type="select",
                choices=[
                    ("island_ga", "도서학교 · 가급지"),
                    ("island_na", "도서학교 · 나급지"),
                    ("island_da", "도서학교 · 다급지"),
                    ("island_ra", "도서학교 · 라급지"),
                    ("remote_ga", "벽지학교 · 가급지"),
                    ("remote_na", "벽지학교 · 나급지"),
                    ("remote_da", "벽지학교 · 다급지"),
                    ("remote_ra", "벽지학교 · 라급지"),
                ],
            ),
        },
        "notes": ["가·나·다·라 급지는 해당 학교가 지정된 당시의 공식 일람을 확인하세요."],
    },
    {
        "code": "jeonnam_rural",
        "category": "regional_bonus",
        "name": "2. 농어촌교육진흥학교 근무경력",
        "max_score": Decimal("1"),
        "scope": "regional",
        "formula": "급지별 기본경력 최대 0.85점 + 추가경력 최대 0.15점",
        "description": "학교·기간별 급지 또는 추가경력 구분을 선택합니다.",
        "fields": {
            "institution": field("학교명", required=True),
            "start_date": field("시작일", required=True, input_type="date"),
            "end_date": field("종료일", required=True, input_type="date"),
            "variant": field(
                "인정 구분",
                required=True,
                input_type="select",
                choices=[
                    ("rural_1", "1급지 기본경력"),
                    ("rural_2", "2급지 기본경력"),
                    ("rural_3", "3급지 기본경력"),
                    ("rural_add", "2014.3.1. 이후 추가경력"),
                ],
            ),
        },
        "notes": ["같은 기간의 도서·벽지 근무경력과 농어촌 근무경력은 중복 인정되지 않습니다."],
    },
    {
        "code": "jeonnam_leadership",
        "category": "regional_bonus",
        "name": "3. 보직교사·장학사·교육연구사 근무경력",
        "max_score": Decimal("1.25"),
        "scope": "regional",
        "formula": "기본경력 월 0.012점 + 보완경력 월 0.003점",
        "description": "보직교사 등 근무경력을 학교·기간별로 입력합니다.",
        "fields": {
            "institution": field("학교·기관명", required=True),
            "start_date": field("시작일", required=True, input_type="date"),
            "end_date": field("종료일", required=True, input_type="date"),
            "variant": field(
                "경력 구분",
                required=True,
                input_type="select",
                choices=[
                    ("leadership_base", "기본경력"),
                    ("leadership_supplement", "1급 정교사 자격연수성적 보완경력"),
                ],
            ),
        },
        "notes": [
            "보완경력은 기본경력 1점 도달 이후부터 적용합니다.",
            "보완 가능 범위는 자격연수성적의 9점 만점 부족분을 확인하여 입력하세요.",
        ],
    },
    {
        "code": "jeonnam_designated_research",
        "category": "regional_bonus",
        "name": "4. 교육감·교육장 지정 연구학교 근무경력",
        "max_score": Decimal("1.25"),
        "scope": "regional",
        "formula": "교육감 지정 월 0.0167점, 교육장 지정 월 0.0139점",
        "description": "연구학교 지정 주체와 근무기간을 기록합니다.",
        "fields": {
            "institution": field("연구학교명", required=True),
            "start_date": field("시작일", required=True, input_type="date"),
            "end_date": field("종료일", required=True, input_type="date"),
            "variant": field(
                "지정 구분",
                required=True,
                input_type="select",
                choices=[
                    ("superintendent", "교육감 지정"),
                    ("district", "교육장 지정"),
                ],
            ),
        },
        "notes": ["교육부 지정 연구학교 경력과 같은 기간은 중복 인정되지 않습니다."],
    },
    {
        "code": "jeonnam_deleted_5",
        "category": "regional_bonus",
        "name": "5. 국가기술자격 소지자",
        "max_score": Decimal("0"),
        "scope": "regional",
        "formula": "삭제 항목",
        "description": "2018.9.1. 삭제되었으며 관련 내용은 6번 기타 교육활동 항목으로 이동했습니다.",
        "input_disabled": True,
        "notes": ["입력·계산 대상이 아니며 변경 이력만 표시합니다."],
    },
    {
        "code": "jeonnam_professional_activity",
        "category": "regional_bonus",
        "name": "6. 기타 교육활동 및 전문성 신장 경력·실적",
        "max_score": Decimal("1"),
        "scope": "regional",
        "formula": "세부 경력·실적 합계(한 세부목 최대 0.5점, 전체 최대 1점)",
        "description": "각 세부 실적은 이 점수칸에서 직접 등록합니다.",
        "fields": {
            "label": field("경력·실적명"),
            "institution": field("학교·기관"),
            "start_date": field("시작일", input_type="date"),
            "end_date": field("종료일", input_type="date"),
            "event_date": field("실적일", input_type="date"),
            "variant": field(
                "세부 항목",
                required=True,
                input_type="select",
                choices=[
                    ("regular", "가~라·아: 일반 교육활동 경력"),
                    ("student_teacher", "마: 교육실습학생 담당교사"),
                    ("youth", "바: 청소년단체 담당교사"),
                    ("class_award", "자: 학급경영 우수교사 · 0.25점"),
                    ("it_certificate", "차: 정보활용능력인증서 · 0.25점"),
                    ("competition_gold", "타: 전국대회 금상 · 0.25점"),
                    ("competition_silver", "타: 전국대회 은상 · 0.1875점"),
                    ("competition_bronze", "타: 전국대회 동상 · 0.125점"),
                    ("hospital", "파: 한센병 환자자녀 수용학교·학급담임"),
                    ("special_school", "하: 특수학교 근무경력"),
                    ("special_class", "하: 특수학급 근무경력"),
                    ("integrated_class", "하: 통합교육학급 근무경력"),
                    ("certificate_1", "거: 국가기술자격 1급 · 0.3점"),
                    ("certificate_2", "거: 국가기술자격 2급 · 0.2점"),
                    ("certificate_3", "거: 국가기술자격 3급 · 0.1점"),
                    ("school_power", "더: 학교교육력 증진 유공 · 연 0.036점"),
                    ("good_lesson_extra", "러: 좋은수업 실천연구 추가 · 1회 0.02점"),
                    ("leadership_extra", "머: 보직교사 추가 경력점"),
                ],
            ),
            "value": field("횟수·연수", input_type="number", min=0, max=100, step=1, help_text="기간형 항목은 비워두고, 횟수·연수형 항목만 입력하세요."),
        },
        "notes": ["연구학교나 좋은수업 기록을 다른 항목에서 자동으로 가져오지 않습니다."],
    },
    {
        "code": "jeonnam_good_lesson",
        "category": "regional_bonus",
        "name": "7. 좋은수업 실천연구 실적",
        "max_score": Decimal("1.5"),
        "scope": "regional",
        "formula": "학교 공개 1회 0.06점, 시·군·도 공개 1회 0.08점(최대 1.5점)",
        "description": "수업 공개 실적을 건별로 직접 입력합니다.",
        "fields": {
            "label": field("교과·수업명"),
            "institution": field("학교·주관기관", required=True),
            "event_date": field("수업 공개일", required=True, input_type="date"),
            "variant": field(
                "공개 규모",
                required=True,
                input_type="select",
                choices=[
                    ("school", "단위학교 교내 공개 · 0.06점"),
                    ("regional", "시·군·도 단위 공개 · 0.08점"),
                ],
            ),
        },
        "notes": [
            "1인 연 2회까지의 실적을 기준으로 확인하세요.",
            "1.5점 도달 이후 추가 실적은 6번 항목에서 별도로 입력합니다.",
        ],
    },
    {
        "code": "jeonnam_residence",
        "category": "regional_bonus",
        "name": "8. 전라남도 거주 경력",
        "max_score": Decimal("0.5"),
        "scope": "regional",
        "formula": "단독거주 월 0.0016점, 전가족 거주 월 0.0025점(최대 0.5점)",
        "description": "거주 형태가 달라진 기간은 나누어 입력합니다.",
        "fields": {
            "label": field("거주지 설명", help_text="상세 주소 대신 시·군 정도만 기록하는 것을 권장합니다."),
            "start_date": field("시작일", required=True, input_type="date"),
            "end_date": field("종료일", required=True, input_type="date"),
            "variant": field(
                "거주 형태",
                required=True,
                input_type="select",
                choices=[
                    ("solo", "본인 단독거주"),
                    ("family", "전가족 거주"),
                ],
            ),
        },
        "notes": ["주민등록번호나 전체 주소는 저장하지 않습니다."],
    },
    {
        "code": "jeonnam_homeroom",
        "category": "regional_bonus",
        "name": "9. 학급 담임 경력",
        "max_score": Decimal("0"),
        "scope": "regional",
        "formula": "초등 해당 없음",
        "description": "초등은 적용되지 않습니다. 중등 담임경력 관련 내용은 6번 너목으로 분류되었던 이력이 있습니다.",
        "input_disabled": True,
        "notes": ["입력·계산 대상이 아닙니다."],
    },
    {
        "code": "jeonnam_remote_replacement",
        "category": "regional_bonus",
        "name": "10. 도서·벽지학교 근무경력 대체 가산점",
        "max_score": Decimal("0"),
        "scope": "regional",
        "formula": "초등 해당 없음",
        "description": "중등교사의 특기·적성교육 지도실적과 일반고 담임경력을 위한 항목입니다.",
        "input_disabled": True,
        "notes": ["초등교사의 실제 도서·벽지 근무경력은 1번에서 입력합니다."],
    },
]

ITEM_BY_CODE = {item["code"]: item for item in ITEMS}

for category in CATEGORIES:
    category["items"] = [item for item in ITEMS if item["category"] == category["code"]]


def get_item(item_code):
    return ITEM_BY_CODE.get(item_code)


def get_category(category_code):
    return CATEGORY_BY_CODE.get(category_code)
