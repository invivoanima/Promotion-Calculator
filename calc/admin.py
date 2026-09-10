from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from . import models

# Register your models here.

admin.site.register(models.Profile)
admin.site.register(models.Manual)
admin.site.register(models.Common_Career)
admin.site.register(models.Common_WorkPerformance)
admin.site.register(models.Common_Training)
admin.site.register(models.Area_Common)
admin.site.register(models.Notice)
admin.site.register(models.Suggestion)

admin.site.register(models.Area_Diff_Jeonnam)
admin.site.register(models.RegionPortfolio)
admin.site.register(models.ScoreRecord)
admin.site.register(models.ItemStatus)
admin.site.register(models.KoreanHistoryQualification)
admin.site.register(models.ScoreChange)
admin.site.register(models.AccessLog)


@admin.register(models.LegalConsent)
class LegalConsentAdmin(admin.ModelAdmin):
    list_display = ("user_id", "terms_version", "privacy_version", "agreed_at")
    readonly_fields = ("user", "terms_version", "privacy_version", "agreed_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(models.OperationLog)
class OperationLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "actor_id_snapshot", "action", "object_type", "object_id")
    readonly_fields = tuple(field.name for field in models.OperationLog._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ProtectedUserChangeForm(UserChangeForm):
    def clean(self):
        cleaned = super().clean()
        if self.instance.pk and self.instance.is_active and self.instance.is_superuser:
            other_active = User.objects.filter(is_active=True, is_superuser=True).exclude(pk=self.instance.pk).exists()
            if not other_active and (not cleaned.get("is_active") or not cleaned.get("is_superuser")):
                raise ValidationError("마지막 활성 최고관리자는 비활성화하거나 최고관리자 권한을 해제할 수 없습니다.")
        return cleaned


class ProtectedUserAdmin(UserAdmin):
    form = ProtectedUserChangeForm

    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_active and obj.is_superuser:
            return User.objects.filter(is_active=True, is_superuser=True).exclude(pk=obj.pk).exists()
        return super().has_delete_permission(request, obj)


admin.site.unregister(User)
admin.site.register(User, ProtectedUserAdmin)
