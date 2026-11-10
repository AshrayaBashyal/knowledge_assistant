from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    """
    Custom manager required because we removed the `username` field.
    Django's default UserManager assumes `username` exists, so we must
    tell it how to create users/superusers using `email` instead.
    """

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model using email as the unique identifier instead of
    username. AbstractBaseUser gives us password hashing + session-independent
    auth; PermissionsMixin adds is_superuser/groups/permissions so the
    Django admin still works normally.
    """

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self) -> str:
        return self.email


class UserAiSetting(models.Model):
    """
    Stores user-provided API keys (BYOK) and model preferences.
    Keys are sanitized on save and masked on read.
    """
    class Provider(models.TextChoices):
        DEFAULT = "default", "Default (System)"
        GEMINI = "gemini", "Google Gemini"
        GROQ = "groq", "Groq"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="ai_settings")
    provider = models.CharField(max_length=20, choices=Provider.choices, default=Provider.DEFAULT)
    gemini_api_key = models.CharField(max_length=255, blank=True, default="")
    groq_api_key = models.CharField(max_length=255, blank=True, default="")
    preferred_model = models.CharField(max_length=100, blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.user.email} - {self.provider}"

    def get_masked_gemini_key(self) -> str:
        if not self.gemini_api_key:
            return ""
        if len(self.gemini_api_key) <= 8:
            return "********"
        return f"{self.gemini_api_key[:6]}...{self.gemini_api_key[-4:]}"

    def get_masked_groq_key(self) -> str:
        if not self.groq_api_key:
            return ""
        if len(self.groq_api_key) <= 8:
            return "********"
        return f"{self.groq_api_key[:6]}...{self.groq_api_key[-4:]}"
