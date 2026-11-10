from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.views import (
    LogoutView,
    MeView,
    RegisterView,
    RateLimitedLoginView,
    UserAiSettingView,
    ValidateApiKeyView,
)

app_name = "accounts"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", RateLimitedLoginView.as_view(), name="login"),
    path("login/refresh/", TokenRefreshView.as_view(), name="login-refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
    path("ai-settings/", UserAiSettingView.as_view(), name="ai-settings"),
    path("ai-settings/validate/", ValidateApiKeyView.as_view(), name="ai-settings-validate"),
]
