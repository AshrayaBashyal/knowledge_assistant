from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import generics, permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.accounts.models import UserAiSetting
from apps.accounts.serializers import (
    LogoutSerializer,
    RegisterSerializer,
    UserSerializer,
    UserAiSettingSerializer,
    ValidateApiKeySerializer,
)


@extend_schema(tags=["accounts"])
class RateLimitedLoginView(TokenObtainPairView):
    """
    login an existing user
 
    Thin subclass of SimpleJWT's TokenObtainPairView that adds rate
    limiting (DEFAULT_THROTTLE_RATES["login"] in settings.py,) as brute-force protection, via DRF's built-in ScopedRateThrottle. Automatically keyed on IP here (not user id, unlike the chat endpoint) since ScopedRateThrottle falls back to IP whenever request.user isn't authenticated - which it never is at login time, since there's no valid token yet.
    """
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"


@extend_schema(tags=["accounts"])
class RegisterView(generics.CreateAPIView):
    """
    Register a new user account.
    
    Does NOT log them in automatically. The client must call the login 
    endpoint immediately after to obtain access and refresh tokens.
    """

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


@extend_schema(tags=["accounts"])
class MeView(generics.RetrieveUpdateAPIView):
    """Get or update the authenticated user's profile."""

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class LogoutView(APIView):
    """Log out a user by blacklisting their refresh token."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["accounts"],
        request=LogoutSerializer,
        responses={
            205: OpenApiResponse(description="Logged out"),
            400: OpenApiResponse(description="Missing or invalid refresh token"),
        },
    )
    def post(self, request: Request) -> Response:
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            token = RefreshToken(serializer.validated_data["refresh"])
            token.blacklist()
        except TokenError:
            return Response(
                {"detail": "invalid or expired refresh token"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(status=status.HTTP_205_RESET_CONTENT)


class UserAiSettingView(APIView):
    """
    Manage user-provided API keys and preferred AI models (BYOK).
    Allows setting custom Gemini or Groq API keys with masked storage.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["accounts"],
        responses={200: UserAiSettingSerializer},
    )
    def get(self, request: Request) -> Response:
        settings_obj, _ = UserAiSetting.objects.get_or_create(user=request.user)
        return Response(UserAiSettingSerializer(settings_obj).data)

    @extend_schema(
        tags=["accounts"],
        request=UserAiSettingSerializer,
        responses={200: UserAiSettingSerializer},
    )
    def post(self, request: Request) -> Response:
        settings_obj, _ = UserAiSetting.objects.get_or_create(user=request.user)

        provider = request.data.get("provider")
        preferred_model = request.data.get("preferred_model")
        gemini_key = request.data.get("gemini_api_key")
        groq_key = request.data.get("groq_api_key")
        clear_gemini = request.data.get("clear_gemini_key", False)
        clear_groq = request.data.get("clear_groq_key", False)

        if provider in ["default", "gemini", "groq"]:
            settings_obj.provider = provider

        if preferred_model is not None:
            settings_obj.preferred_model = preferred_model.strip()

        if clear_gemini:
            settings_obj.gemini_api_key = ""
        elif gemini_key:
            clean_gemini = gemini_key.strip()
            if len(clean_gemini) >= 20:
                settings_obj.gemini_api_key = clean_gemini

        if clear_groq:
            settings_obj.groq_api_key = ""
        elif groq_key:
            clean_groq = groq_key.strip()
            if len(clean_groq) >= 20:
                settings_obj.groq_api_key = clean_groq

        settings_obj.save()
        return Response(UserAiSettingSerializer(settings_obj).data)

    @extend_schema(tags=["accounts"])
    def delete(self, request: Request) -> Response:
        """Reset to system default settings and clear custom keys."""
        settings_obj, _ = UserAiSetting.objects.get_or_create(user=request.user)
        settings_obj.provider = UserAiSetting.Provider.DEFAULT
        settings_obj.gemini_api_key = ""
        settings_obj.groq_api_key = ""
        settings_obj.preferred_model = ""
        settings_obj.save()
        return Response(UserAiSettingSerializer(settings_obj).data)


class ValidateApiKeyView(APIView):
    """
    Live test an API key against Google Gemini or Groq before saving it.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["accounts"],
        request=ValidateApiKeySerializer,
    )
    def post(self, request: Request) -> Response:
        serializer = ValidateApiKeySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        provider = serializer.validated_data["provider"]
        api_key = serializer.validated_data["api_key"]
        model = serializer.validated_data.get("model")

        try:
            if provider == "gemini":
                from langchain_google_genai import ChatGoogleGenerativeAI
                test_model = model or "gemini-2.5-flash-lite"
                llm = ChatGoogleGenerativeAI(
                    model=test_model,
                    google_api_key=api_key,
                    max_output_tokens=5,
                    temperature=0.1,
                )
                llm.invoke("Hi")
            elif provider == "groq":
                from langchain_groq import ChatGroq
                test_model = model or "llama-3.1-8b-instant"
                llm = ChatGroq(
                    model=test_model,
                    api_key=api_key,
                    max_tokens=5,
                    temperature=0.1,
                )
                llm.invoke("Hi")
            else:
                return Response({"detail": f"Unknown provider {provider}"}, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                "valid": True,
                "provider": provider,
                "message": f"Successfully verified connection with {provider.title()} ({test_model})!"
            })
        except Exception as exc:
            err_msg = str(exc)
            if "API_KEY_INVALID" in err_msg or "Invalid API Key" in err_msg or "401" in err_msg or "invalid_api_key" in err_msg:
                user_friendly = "Invalid API Key: The key was rejected by the provider."
            elif "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "rate_limit_exceeded" in err_msg:
                user_friendly = "Quota Exceeded (429): Your API key has reached its rate limit or usage quota."
            elif "model_not_found" in err_msg:
                user_friendly = f"Model '{model}' is not available for this API key."
            else:
                user_friendly = f"Verification failed: {err_msg[:250]}"

            return Response({
                "valid": False,
                "provider": provider,
                "error": user_friendly,
            }, status=status.HTTP_400_BAD_REQUEST)
