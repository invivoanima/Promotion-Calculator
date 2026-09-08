from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views


app_name = "calc"

urlpatterns = [
    path("", views.welcome, name="welcome"),
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("notices/", views.notice_list, name="notices"),
    path("notices/<int:notice_id>/", views.notice_detail, name="notice_detail"),
    path("suggestions/", views.suggestion_list, name="suggestions"),
    path("suggestions/<int:suggestion_id>/", views.suggestion_detail, name="suggestion_detail"),
    path("suggestions/<int:suggestion_id>/file/", views.suggestion_file, name="suggestion_file"),
    path("suggestion/", views.suggestion_list, name="suggestion"),
    path("regions/", views.region_select, name="region_select"),
    path("try/", views.guest_score_index, name="guest_score_index"),
    path("try/reset/", views.guest_score_reset, name="guest_score_reset"),
    path(
        "try/item/<str:item_code>/",
        views.guest_score_item,
        name="guest_score_item",
    ),
    path(
        "try/item/<str:item_code>/<str:record_key>/edit/",
        views.guest_score_item,
        name="guest_edit_score_record",
    ),
    path(
        "try/item/<str:item_code>/<str:record_key>/delete/",
        views.guest_delete_score_record,
        name="guest_delete_score_record",
    ),
    path(
        "try/<str:category_code>/",
        views.guest_score_index,
        name="guest_score_category",
    ),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("main/", views.dashboard, name="main"),
    path("scores/", views.score_index, name="score_index"),
    path("scores/<str:category_code>/", views.score_index, name="score_index_category"),
    path("score/<str:item_code>/", views.score_item, name="score_item"),
    path("score/<str:item_code>/<int:record_id>/edit/", views.score_item, name="edit_score_record"),
    path("score/record/<int:record_id>/delete/", views.delete_score_record, name="delete_score_record"),
    path("qualification/korean-history/", views.korean_history, name="korean_history"),
    path("records/", views.records_overview, name="records"),
    path("records/changes/", views.score_changes, name="score_changes"),
    path("resources/", views.resources, name="resources"),
    path("account/", views.account_settings, name="account_settings"),
    path("account/delete/", views.delete_account, name="delete_account"),
    path("staff/", views.staff_dashboard, name="staff_dashboard"),
    path("staff/suggestions/", views.staff_suggestions, name="staff_suggestions"),
    path(
        "staff/suggestions/<int:suggestion_id>/",
        views.staff_suggestion_detail,
        name="staff_suggestion_detail",
    ),
    path("staff/notices/", views.staff_notices, name="staff_notices"),
    path("staff/notices/new/", views.staff_notice_create, name="staff_notice_create"),
    path(
        "staff/notices/<int:notice_id>/edit/",
        views.staff_notice_edit,
        name="staff_notice_edit",
    ),
    path(
        "staff/notices/<int:notice_id>/toggle/",
        views.staff_notice_toggle,
        name="staff_notice_toggle",
    ),
    path("staff/access-logs/", views.staff_access_logs, name="staff_access_logs"),
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="calc/new/password_reset_form.html",
            email_template_name="calc/new/password_reset_email.txt",
            success_url=reverse_lazy("calc:password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(template_name="calc/new/password_reset_done.html"),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="calc/new/password_reset_confirm.html",
            success_url=reverse_lazy("calc:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(template_name="calc/new/password_reset_complete.html"),
        name="password_reset_complete",
    ),
    path("common/", views.legacy_common, name="common"),
    path("area/", views.legacy_area, name="area"),
    path("area/<str:areaname>/common/", views.legacy_area, name="ac"),
    path("area/<str:areaname>/diff/", views.legacy_area, name="ad"),
    path("area/<str:areaname>/refdata/", views.resources, name="refdata"),
]
