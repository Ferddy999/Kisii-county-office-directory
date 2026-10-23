from django.contrib.auth import views as auth_views
from django.urls import path

from . import account_views, legal_views, views
from .auth import RoleLoginView, login_verify

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("directory/", views.directory, name="directory"),
    path("login/", RoleLoginView.as_view(), name="login"),
    path("login/verify/", login_verify, name="login_verify"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("settings/", account_views.account_settings, name="account_settings"),
    path("settings/password/", account_views.ChangePasswordView.as_view(), name="password_change"),
    path("settings/handover/", account_views.handover, name="handover"),
    path("terms/", legal_views.terms, name="terms"),
    path("terms/accept/", legal_views.accept_terms, name="accept_terms"),
    path("privacy/", legal_views.privacy, name="privacy"),
    path("cookies/", legal_views.cookie_settings, name="cookie_settings"),
    path("password-reset/", auth_views.PasswordResetView.as_view(), name="password_reset"),
    path("password-reset/sent/", auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),
]
