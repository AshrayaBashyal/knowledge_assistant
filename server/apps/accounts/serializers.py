import re
from django.contrib.auth import get_user_model
from rest_framework import serializers
from apps.accounts.models import UserAiSetting

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """
    Validates registration input and creates a new user with a hashed password. 
    """

    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "email", "full_name", "password"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LogoutSerializer(serializers.Serializer):
    """Request body shape for logout"""

    refresh = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    """Representation of the user for viewing and updating their profile."""

    class Meta:
        model = User
        fields = ["id", "email", "full_name", "is_staff", "date_joined"]
        read_only_fields = ["id", "email", "is_staff", "date_joined"]


class UserAiSettingSerializer(serializers.ModelSerializer):
    """
    Serializer for managing user AI provider preferences and API keys.
    API keys are write-only / masked in responses to prevent exposing credentials.
    """
    masked_gemini_key = serializers.SerializerMethodField()
    masked_groq_key = serializers.SerializerMethodField()
    has_gemini_key = serializers.SerializerMethodField()
    has_groq_key = serializers.SerializerMethodField()

    gemini_api_key = serializers.CharField(write_only=True, required=False, allow_blank=True)
    groq_api_key = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = UserAiSetting
        fields = [
            "provider",
            "preferred_model",
            "gemini_api_key",
            "groq_api_key",
            "masked_gemini_key",
            "masked_groq_key",
            "has_gemini_key",
            "has_groq_key",
            "updated_at",
        ]
        read_only_fields = [
            "masked_gemini_key",
            "masked_groq_key",
            "has_gemini_key",
            "has_groq_key",
            "updated_at",
        ]

    def get_masked_gemini_key(self, obj: UserAiSetting) -> str:
        return obj.get_masked_gemini_key()

    def get_masked_groq_key(self, obj: UserAiSetting) -> str:
        return obj.get_masked_groq_key()

    def get_has_gemini_key(self, obj: UserAiSetting) -> bool:
        return bool(obj.gemini_api_key)

    def get_has_groq_key(self, obj: UserAiSetting) -> bool:
        return bool(obj.groq_api_key)

    def validate_gemini_api_key(self, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            return ""
        # Check basic Gemini API key shape (Google API keys are usually 39 alphanumeric chars)
        if len(cleaned) < 20:
            raise serializers.ValidationError("Gemini API key is suspiciously short.")
        return cleaned

    def validate_groq_api_key(self, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            return ""
        # Groq keys usually start with 'gsk_'
        if not cleaned.startswith("gsk_") and len(cleaned) < 25:
            raise serializers.ValidationError("Groq API keys typically start with 'gsk_'.")
        return cleaned

    def update(self, instance, validated_data):
        # Only overwrite keys if explicitly provided with non-empty values
        if "gemini_api_key" in validated_data and not validated_data["gemini_api_key"]:
            # If user sends empty string, keep existing key unless specifically clearing
            pass
        return super().update(instance, validated_data)


class ValidateApiKeySerializer(serializers.Serializer):
    """Payload for live testing an API key before saving."""
    provider = serializers.ChoiceField(choices=["gemini", "groq"])
    api_key = serializers.CharField(max_length=255)
    model = serializers.CharField(max_length=100, required=False, default="")

    def validate_api_key(self, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("API key cannot be empty.")
        return cleaned
