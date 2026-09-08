from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone

from .catalog import REGIONS


REGION_CHOICES = [(region["code"], region["name"]) for region in REGIONS]
MAX_SUGGESTION_FILE_SIZE = 100 * 1024 * 1024


def validate_suggestion_file(uploaded_file):
    """Validate suggestion attachments without trusting the filename or MIME header."""
    if not uploaded_file:
        return
    if uploaded_file.size > MAX_SUGGESTION_FILE_SIZE:
        raise ValidationError("첨부파일은 100MB 이하만 업로드할 수 있습니다.")

    filename = (getattr(uploaded_file, "name", "") or "").lower()
    extension = filename.rsplit(".", 1)[-1] if "." in filename else ""
    signatures = {
        "jpg": lambda data: data.startswith(b"\xff\xd8\xff"),
        "jpeg": lambda data: data.startswith(b"\xff\xd8\xff"),
        "png": lambda data: data.startswith(b"\x89PNG\r\n\x1a\n"),
        "webp": lambda data: len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP",
        "pdf": lambda data: data.startswith(b"%PDF-") ,
    }
    signature_check = signatures.get(extension)
    if signature_check is None:
        raise ValidationError("JPG, JPEG, PNG, WEBP, PDF 파일만 첨부할 수 있습니다.")

    try:
        original_position = uploaded_file.tell()
        uploaded_file.seek(0)
        header = uploaded_file.read(32)
    except (AttributeError, OSError):
        raise ValidationError("첨부파일을 확인할 수 없습니다. 파일을 다시 선택해주세요.")
    finally:
        try:
            uploaded_file.seek(original_position)
        except (AttributeError, OSError, UnboundLocalError):
            pass
    if not signature_check(header):
        raise ValidationError("파일 형식과 확장자가 일치하지 않습니다. JPG, JPEG, PNG, WEBP, PDF만 첨부할 수 있습니다.")

class Profile(models.Model) :
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    area = models.TextField(default="", blank=True)
    display_name = models.CharField(max_length=40, blank=True)
    primary_region = models.CharField(
        max_length=30,
        choices=REGION_CHOICES,
        blank=True,
        default="",
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    point_cc = models.DecimalField(max_digits=100, decimal_places=8, default=0, blank=True, null=True)
    point_cw = models.DecimalField(max_digits=100, decimal_places=8, default=0, blank=True, null=True)
    point_ct = models.DecimalField(max_digits=100, decimal_places=8, default=0, blank=True, null=True)
    point_ac = models.DecimalField(max_digits=100, decimal_places=8, default=0, blank=True, null=True)
    point_ad = models.DecimalField(max_digits=100, decimal_places=8, default=0, blank=True, null=True)
    total = models.DecimalField(max_digits=100, decimal_places=8, default=0, blank=True, null=True)

    def __str__(self) : 
        return f'{self.user}({self.area}) - {self.point_cc}/{self.point_cw}/{self.point_ct}/{self.point_ac}/{self.point_ad} - 총 {self.total}'

    @property
    def region(self):
        return self.primary_region or self.area


class Notice(models.Model) :
    class Category(models.TextChoices):
        NOTICE = "notice", "공지"
        UPDATE = "update", "업데이트"
        MAINTENANCE = "maintenance", "점검"
        IMPORTANT = "important", "중요"

    title = models.TextField()
    content = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.NOTICE,
    )
    is_published = models.BooleanField(default=True)
    is_pinned = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-is_pinned", "-date"]

    def save(self, *args, **kwargs):
        publication_field_changed = False
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()
            publication_field_changed = True
        elif not self.is_published:
            publication_field_changed = self.published_at is not None
            self.published_at = None
        if publication_field_changed and kwargs.get("update_fields") is not None:
            kwargs["update_fields"] = set(kwargs["update_fields"]) | {"published_at"}
        super().save(*args, **kwargs)

    def __str__(self) : 
        return f'{self.title} - {self.date}'



class Manual(models.Model) :
    area = models.TextField()
    upload_date = models.DateTimeField(auto_now_add=True)
    manual = models.FileField(upload_to="manuals/")
    uploader = models.TextField()


class Suggestion(models.Model) :
    class Category(models.TextChoices):
        ERROR = "error", "오류 신고"
        FEATURE = "feature", "기능 제안"
        DATA = "data", "자료 수정"
        OTHER = "other", "기타"

    class Status(models.TextChoices):
        RECEIVED = "received", "접수"
        REVIEWING = "reviewing", "확인 중"
        COMPLETED = "completed", "처리 완료"

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.OTHER,
    )
    title = models.CharField(max_length=200, default="기존 건의")
    content = models.TextField(default='')
    file = models.FileField(
        upload_to='suggestion/',
        null=True,
        blank=True,
        validators=[validate_suggestion_file],
    )
    source_path = models.CharField(max_length=255, blank=True, default="")
    region = models.CharField(max_length=30, blank=True, default="")
    admin_memo = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.RECEIVED,
    )
    date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) : 
        return f'{self.user} - {self.content}, {self.date}'


class AccessLog(models.Model):
    class DeviceType(models.TextChoices):
        DESKTOP = "desktop", "데스크톱"
        MOBILE = "mobile", "모바일"
        TABLET = "tablet", "태블릿"
        OTHER = "other", "기타"

    user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="access_logs",
    )
    is_authenticated = models.BooleanField(default=False)
    route_name = models.CharField(max_length=150, blank=True, default="")
    region = models.CharField(max_length=30, blank=True, default="")
    device_type = models.CharField(
        max_length=12,
        choices=DeviceType.choices,
        default=DeviceType.OTHER,
    )
    status_code = models.PositiveSmallIntegerField(default=200)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["route_name", "created_at"]),
            models.Index(fields=["status_code", "created_at"]),
        ]


class Common_Career(models.Model) :
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    career_year = models.IntegerField(default=0, blank=True, null=True)
    career_month = models.IntegerField(default=0, blank=True, null=True)
    career_memo = models.TextField(default=0, blank=True, null=True)

    def __str__(self) : 
        return f'{self.user}'

class Common_WorkPerformance(models.Model) :
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    wp_late_1 = models.IntegerField(default=0, blank=True, null=True)
    wp_late_2 = models.IntegerField(default=0, blank=True, null=True)
    wp_late_3 = models.IntegerField(default=0, blank=True, null=True)
    wp_late_4 = models.IntegerField(default=0, blank=True, null=True)
    wp_late_5 = models.IntegerField(default=0, blank=True, null=True)
    wp_memo = models.TextField(default=0, blank=True, null=True)

    def __str__(self) : 
        return f'{self.user}'

class Common_Training(models.Model) :
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    grade1teacher_result = models.IntegerField(default=0)
    grade1teacher_memo = models.TextField(default='', blank=True, null=True)
    training_first = models.IntegerField(default=0)
    training_second = models.IntegerField(default=0)
    training_memo = models.TextField(default='', blank=True, null=True)
    research_contest_point = models.IntegerField(default=0)
    degree_point = models.IntegerField(default=0)
    research_memo = models.TextField(default='', blank=True, null=True)

    def __str__(self) : 
        return f'{self.user}'





class Area_Common(models.Model) :
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    area = models.TextField()
    research_school_year = models.IntegerField(default=0)
    research_school_month = models.IntegerField(default=0)
    research_school_memo = models.TextField(default='')
    foreign_school_year = models.IntegerField(default=0)
    foreign_school_month = models.IntegerField(default=0)
    foreign_school_memo = models.TextField(default='')
    lecture1_point = models.IntegerField(default=0)
    lecture2_point = models.IntegerField(default=0)
    lecture3_point = models.IntegerField(default=0)
    lecture4_point = models.IntegerField(default=0)
    lecture5_point = models.IntegerField(default=0)
    lecture6_point = models.IntegerField(default=0)
    lecture7_point = models.IntegerField(default=0)
    lecture8_point = models.IntegerField(default=0)
    lecture9_point = models.IntegerField(default=0)
    lecture10_point = models.IntegerField(default=0)
    lecture_memo = models.TextField(default='')
    violence_count = models.IntegerField(default=0)
    violence_memo = models.TextField(default='')

    def __str__(self) : 
        return f'{self.user}({self.area})'



class Area_Diff_Jeonnam(models.Model) :
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    island_ga_year = models.IntegerField(default=0)
    island_ga_month = models.IntegerField(default=0)
    island_na_year = models.IntegerField(default=0)
    island_na_month = models.IntegerField(default=0)
    island_da_year = models.IntegerField(default=0)
    island_da_month = models.IntegerField(default=0)
    island_ra_year = models.IntegerField(default=0)
    island_ra_month = models.IntegerField(default=0)
    mountain_ga_year = models.IntegerField(default=0)
    mountain_ga_month = models.IntegerField(default=0)
    mountain_na_year = models.IntegerField(default=0)
    mountain_na_month = models.IntegerField(default=0)
    mountain_da_year = models.IntegerField(default=0)
    mountain_da_month = models.IntegerField(default=0)
    mountain_ra_year = models.IntegerField(default=0)
    mountain_ra_month = models.IntegerField(default=0)
    outside_school_memo = models.TextField(default='')

    rural_1_year = models.IntegerField(default=0)
    rural_1_month = models.IntegerField(default=0)
    rural_2_year = models.IntegerField(default=0)
    rural_2_month = models.IntegerField(default=0)
    rural_3_year = models.IntegerField(default=0)
    rural_3_month = models.IntegerField(default=0)
    rural_add_month = models.IntegerField(default=0)
    rural_memo = models.TextField(default='')

    high_teacher_year = models.IntegerField(default=0)
    high_teacher_add_year = models.IntegerField(default=0)
    high_teacher_memo = models.TextField(default='')

    research_school_area_year = models.IntegerField(default=0)
    research_school_area_month = models.IntegerField(default=0)
    research_school_area2_year = models.IntegerField(default=0)
    research_school_area2_month = models.IntegerField(default=0)
    research_school_area_memo = models.TextField(default='')

    double_class_year = models.IntegerField(default=0)
    double_class_month = models.IntegerField(default=0)
    cyber_year = models.IntegerField(default=0)
    cyber_month = models.IntegerField(default=0)
    genius_year = models.IntegerField(default=0)
    genius_month = models.IntegerField(default=0)
    intern_month = models.IntegerField(default=0)
    intern_day = models.IntegerField(default=0)
    scout_month = models.IntegerField(default=0)
    competition_gold_point = models.IntegerField(default=0)
    competition_silver_point = models.IntegerField(default=0)
    competition_bronze_point = models.IntegerField(default=0)
    cert_1_point = models.IntegerField(default=0)
    cert_2_point = models.IntegerField(default=0)
    cert_3_point = models.IntegerField(default=0)
    edupower_count = models.IntegerField(default=0)
    openclass_add_count = models.IntegerField(default=0)
    high_teacher_add_plus_count = models.IntegerField(default=0)
    etc_memo = models.TextField(default='')

    openclass_count = models.IntegerField(default=0)
    openclass_memo = models.TextField(default='')

    living_solo_month = models.IntegerField(default=0)
    living_solo_day = models.IntegerField(default=0)
    living_family_month = models.IntegerField(default=0)
    living_family_day = models.IntegerField(default=0)
    living_memo = models.TextField(default='')

    def __str__(self) : 
        return f'{self.user}'


class RegionPortfolio(models.Model):
    """A user's saved calculation for one region.

    A user may keep reference calculations for multiple regions, while
    ``Profile.primary_region`` remains the only comparison cohort.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="region_portfolios")
    region = models.CharField(max_length=30, choices=REGION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "region"],
                name="unique_user_region_portfolio",
            )
        ]
        ordering = ["region"]

    def __str__(self):
        return f"{self.user} - {self.get_region_display()}"


class ScoreRecord(models.Model):
    class Scope(models.TextChoices):
        NATIONAL = "national", "전국 공통"
        REGIONAL = "regional", "지역별"

    class Category(models.TextChoices):
        CAREER = "career", "경력평정"
        WORK = "work", "근무성적평정"
        TRAINING = "training", "연수성적평정"
        COMMON_BONUS = "common_bonus", "공통가산점"
        REGIONAL_BONUS = "regional_bonus", "선택가산점"

    class Status(models.TextChoices):
        RECORDED = "recorded", "기록 있음"
        NOT_APPLICABLE = "not_applicable", "해당 없음"
        NEEDS_REVIEW = "needs_review", "확인 필요"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="score_records")
    portfolio = models.ForeignKey(
        RegionPortfolio,
        on_delete=models.CASCADE,
        related_name="score_records",
        null=True,
        blank=True,
    )
    scope = models.CharField(max_length=12, choices=Scope.choices)
    category = models.CharField(max_length=30, choices=Category.choices)
    item_code = models.CharField(max_length=80)
    label = models.CharField(max_length=160, blank=True)
    institution = models.CharField(max_length=160, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    event_date = models.DateField(null=True, blank=True)
    input_data = models.JSONField(default=dict, blank=True)
    memo = models.TextField(blank=True)
    evidence_available = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.RECORDED,
    )
    calculated_score = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-event_date", "-end_date", "-updated_at"]
        indexes = [
            models.Index(fields=["user", "category", "item_code"]),
            models.Index(fields=["portfolio", "item_code"]),
        ]

    def clean(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "종료일은 시작일보다 빠를 수 없습니다."})
        if self.scope == self.Scope.REGIONAL:
            if not self.portfolio_id:
                raise ValidationError("지역별 기록에는 지역 계산 자료가 필요합니다.")
            if self.portfolio and self.portfolio.user_id != self.user_id:
                raise ValidationError("다른 사용자의 지역 계산 자료에는 저장할 수 없습니다.")
        elif self.portfolio_id:
            raise ValidationError("전국 공통 기록에는 지역 계산 자료를 지정하지 않습니다.")

    def __str__(self):
        return f"{self.user} - {self.item_code} - {self.calculated_score}"


class ItemStatus(models.Model):
    """Explicit completion state for items that legitimately have no records."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="item_statuses")
    portfolio = models.ForeignKey(
        RegionPortfolio,
        on_delete=models.CASCADE,
        related_name="item_statuses",
        null=True,
        blank=True,
    )
    item_code = models.CharField(max_length=80)
    status = models.CharField(
        max_length=20,
        choices=ScoreRecord.Status.choices,
        default=ScoreRecord.Status.NOT_APPLICABLE,
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "portfolio", "item_code"],
                name="unique_item_status_per_portfolio",
            )
        ]


class KoreanHistoryQualification(models.Model):
    class Method(models.TextChoices):
        NONE = "", "선택 안 함"
        TEST = "test", "한국사능력검정"
        TRAINING = "training", "한국사 관련 연수"

    class EmploymentType(models.TextChoices):
        PUBLIC_REGULAR = "public_regular", "국공립 정규교원"
        PRIVATE_REGULAR = "private_regular", "사립학교 정규교원"
        TEMPORARY = "temporary", "기간제교사"
        OTHER = "other", "기타·확인 필요"

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="korean_history_qualification",
    )
    method = models.CharField(max_length=20, choices=Method.choices, blank=True, default="")
    test_grade = models.PositiveSmallIntegerField(null=True, blank=True)
    passed_at = models.DateField(null=True, blank=True)
    certificate_number = models.CharField(max_length=80, blank=True)
    training_name = models.CharField(max_length=160, blank=True)
    training_institution = models.CharField(max_length=160, blank=True)
    training_hours = models.PositiveIntegerField(null=True, blank=True)
    completed_at = models.DateField(null=True, blank=True)
    completed_after_appointment = models.BooleanField(default=False)
    employment_type = models.CharField(
        max_length=30,
        choices=EmploymentType.choices,
        blank=True,
        default="",
    )
    memo = models.TextField(blank=True)
    evidence_available = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def qualification_status(self):
        if self.method == self.Method.TEST:
            if self.test_grade and self.test_grade <= 3:
                return "satisfied"
            return "not_satisfied" if self.test_grade else "needs_review"
        if self.method == self.Method.TRAINING:
            if not self.training_hours or not self.employment_type:
                return "needs_review"
            if self.employment_type == self.EmploymentType.TEMPORARY:
                return "not_satisfied"
            if self.training_hours >= 60 and self.completed_after_appointment:
                return "satisfied"
            return "not_satisfied"
        return "needs_review"


class ScoreChange(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="score_changes")
    portfolio = models.ForeignKey(
        RegionPortfolio,
        on_delete=models.CASCADE,
        related_name="score_changes",
        null=True,
        blank=True,
    )
    item_code = models.CharField(max_length=80)
    previous_item_score = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    new_item_score = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    previous_total = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    new_total = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

