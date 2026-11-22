from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import User, UserAiSetting
from apps.accounts.views import ValidateApiKeyView


class ValidateSavedApiKeyTests(TestCase):
    def test_uses_saved_key_when_test_request_omits_key(self):
        user = User.objects.create_user(
            email="ai-settings@example.com",
            password="test-password",
        )
        UserAiSetting.objects.create(
            user=user,
            provider=UserAiSetting.Provider.GEMINI,
            gemini_api_key="test-gemini-api-key",
        )
        request = APIRequestFactory().post(
            "/api/accounts/ai-settings/validate/",
            {"provider": "gemini", "api_key": "", "model": "gemini-3.5-flash-lite"},
            format="json",
        )
        force_authenticate(request, user=user)

        with patch("langchain_google_genai.ChatGoogleGenerativeAI") as chat_model:
            response = ValidateApiKeyView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        chat_model.assert_called_once()
        self.assertEqual(
            chat_model.call_args.kwargs["google_api_key"],
            "test-gemini-api-key",
        )
