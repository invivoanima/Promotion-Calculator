from datetime import date

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

from .models import KoreanHistoryQualification, Notice, Profile, ScoreRecord, Suggestion


class RegisterForm(forms.Form):
    username = forms.RegexField(
        label="아이디",
        regex=r"^[A-Za-z0-9_]+$",
        min_length=4,
        max_length=20,
        error_messages={
            "invalid": "아이디는 영문, 숫자, 밑줄(_)만 사용할 수 있습니다.",
            "min_length": "아이디는 4자 이상 입력해주세요.",
            "max_length": "아이디는 20자 이하로 입력해주세요.",
        },
        help_text="영문, 숫자, 밑줄(_)을 사용해 4~20자로 입력해주세요.",
    )
    display_name = forms.CharField(label="표시 이름", max_length=40)
    password1 = forms.CharField(label="비밀번호", widget=forms.PasswordInput)
    password2 = forms.CharField(label="비밀번호 확인", widget=forms.PasswordInput)
    agree_terms = forms.BooleanField(label="이용약관에 동의합니다")
    agree_privacy = forms.BooleanField(label="개인정보 수집 및 이용에 동의합니다")

    def clean_username(self):
        username = self.cleaned_data["username"].strip().lower()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("이미 사용 중인 아이디입니다.")
        return username

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get("password1")
        password2 = cleaned.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error("password2", "비밀번호가 서로 일치하지 않습니다.")
        if password1:
            validate_password(password1)
        return cleaned

    def save(self):
        username = self.cleaned_data["username"]
        user = User.objects.create_user(
            username=username,
            password=self.cleaned_data["password1"],
        )
        Profile.objects.create(
            user=user,
            display_name=self.cleaned_data["display_name"],
        )
        return user


class LoginForm(forms.Form):
    username = forms.CharField(label="아이디")
    password = forms.CharField(label="비밀번호", widget=forms.PasswordInput)

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        identifier = cleaned.get("username", "").strip()
        password = cleaned.get("password")
        if identifier and password:
            matched = User.objects.filter(username__iexact=identifier).first()
            username = matched.username if matched else identifier
            self.user_cache = authenticate(self.request, username=username, password=password)
            if self.user_cache is None:
                raise forms.ValidationError("아이디 또는 비밀번호를 확인해주세요.")
        return cleaned

    def get_user(self):
        return self.user_cache


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["display_name"]
        labels = {"display_name": "표시 이름"}


class ScoreRecordInputForm(forms.Form):
    label = forms.CharField(required=False)
    institution = forms.CharField(required=False)
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    event_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    year = forms.IntegerField(required=False)
    variant = forms.ChoiceField(required=False, choices=[])
    value = forms.DecimalField(required=False)
    extra_value = forms.DecimalField(required=False)
    memo = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))
    evidence_available = forms.BooleanField(required=False)

    dynamic_field_names = (
        "label",
        "institution",
        "start_date",
        "end_date",
        "event_date",
        "year",
        "variant",
        "value",
        "extra_value",
    )

    def __init__(self, item, *args, record=None, **kwargs):
        self.item = item
        self.record = record
        initial = kwargs.setdefault("initial", {})
        if record:
            initial.update(
                {
                    "label": record.label,
                    "institution": record.institution,
                    "start_date": record.start_date,
                    "end_date": record.end_date,
                    "event_date": record.event_date,
                    "memo": record.memo,
                    "evidence_available": record.evidence_available,
                    **(record.input_data or {}),
                }
            )
        super().__init__(*args, **kwargs)

        configured_fields = item.get("fields", {})
        for name in self.dynamic_field_names:
            if name not in configured_fields:
                self.fields.pop(name)
                continue
            config = configured_fields[name]
            form_field = self.fields[name]
            form_field.label = config["label"]
            form_field.required = config.get("required", False)
            form_field.help_text = config.get("help_text", "")
            if name == "variant":
                form_field.choices = [("", "선택해주세요")] + config.get("choices", [])
            widget_attrs = form_field.widget.attrs
            for attribute in ("min", "max", "step"):
                if attribute in config:
                    widget_attrs[attribute] = config[attribute]

        self.fields["memo"].label = "메모"
        self.fields["evidence_available"].label = "증빙자료를 보유하고 있어요"

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_date")
        end = cleaned.get("end_date")
        if start and end and end < start:
            self.add_error("end_date", "종료일은 시작일보다 빠를 수 없습니다.")
        if self.item.get("code") == "training_job":
            completion_date = cleaned.get("event_date")
            hours = cleaned.get("extra_value")
            if completion_date and not (
                date(2016, 1, 1) <= completion_date <= date(2026, 2, 28)
            ):
                self.add_error(
                    "event_date",
                    "2026년 평정에서는 2016.1.1.부터 2026.2.28.까지 수료한 연수만 인정됩니다.",
                )
            if hours is not None and hours < 60:
                self.add_error("extra_value", "60시간 이상 직무연수만 인정됩니다.")
        return cleaned

    def apply_to_record(self, record):
        record.label = self.cleaned_data.get("label", "") or ""
        record.institution = self.cleaned_data.get("institution", "") or ""
        record.start_date = self.cleaned_data.get("start_date")
        record.end_date = self.cleaned_data.get("end_date")
        record.event_date = self.cleaned_data.get("event_date")
        record.memo = self.cleaned_data.get("memo", "") or ""
        record.evidence_available = bool(self.cleaned_data.get("evidence_available"))
        record.input_data = {
            name: str(self.cleaned_data[name])
            for name in ("year", "variant", "value", "extra_value")
            if self.cleaned_data.get(name) not in (None, "")
        }
        record.status = ScoreRecord.Status.RECORDED
        return record


class KoreanHistoryForm(forms.ModelForm):
    class Meta:
        model = KoreanHistoryQualification
        exclude = ["user", "updated_at"]
        widgets = {
            "passed_at": forms.DateInput(attrs={"type": "date"}),
            "completed_at": forms.DateInput(attrs={"type": "date"}),
            "memo": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "method": "충족 방법",
            "test_grade": "한국사능력검정 등급",
            "passed_at": "합격일",
            "certificate_number": "인증번호",
            "training_name": "연수명",
            "training_institution": "연수기관",
            "training_hours": "이수시간",
            "completed_at": "수료일",
            "completed_after_appointment": "교사 임용 후 이수했어요",
            "employment_type": "이수 당시 근무 형태",
            "memo": "메모",
            "evidence_available": "증빙자료를 보유하고 있어요",
        }

    def clean(self):
        cleaned = super().clean()
        method = cleaned.get("method")
        if method == KoreanHistoryQualification.Method.TEST and not cleaned.get("test_grade"):
            self.add_error("test_grade", "등급을 입력해주세요.")
        if method == KoreanHistoryQualification.Method.TRAINING:
            if not cleaned.get("training_hours"):
                self.add_error("training_hours", "이수시간을 입력해주세요.")
            if not cleaned.get("employment_type"):
                self.add_error("employment_type", "근무 형태를 선택해주세요.")
        return cleaned


class SuggestionForm(forms.ModelForm):
    class Meta:
        model = Suggestion
        fields = ["category", "title", "content", "file"]
        labels = {
            "category": "유형",
            "title": "제목",
            "content": "내용",
            "file": "첨부파일",
        }
        widgets = {
            "content": forms.Textarea(attrs={"rows": 8}),
        }
        help_texts = {
            "file": "JPG, JPEG, PNG, WEBP, PDF만 가능하며 최대 100MB입니다.",
        }


class NoticeForm(forms.ModelForm):
    class Meta:
        model = Notice
        fields = ["category", "title", "content", "is_published", "is_pinned"]
        labels = {
            "category": "유형",
            "title": "제목",
            "content": "내용",
            "is_published": "공개하기",
            "is_pinned": "상단 고정",
        }
        widgets = {
            "content": forms.Textarea(attrs={"rows": 12}),
        }
