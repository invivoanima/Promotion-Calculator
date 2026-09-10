from django.conf import settings
from django.core.checks import Error, register


@register("deploy")
def legal_deployment_check(app_configs, **kwargs):
    if getattr(settings, "APP_ENV", "development") != "production":
        return []
    missing = [name for name in ("LEGAL_OPERATOR_NAME", "LEGAL_CONTACT") if not getattr(settings, name, "")]
    if missing:
        return [Error(
            "운영 공개 문서의 운영자 정보가 설정되지 않았습니다.",
            hint="다음 환경변수를 설정하세요: " + ", ".join(missing),
            id="calc.E001",
        )]
    return []
