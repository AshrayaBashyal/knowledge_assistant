from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.views import LogoutView, MeView, RegisterView, RateLimitedLoginView

app_name = "accounts"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", RateLimitedLoginView.as_view(), name="login"),
    path("login/refresh/", TokenRefreshView.as_view(), name="login-refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
]