from django.conf import settings
from django.db import models


class Conversation(models.Model):
    """
    A user's chat session. 
    
    Kept as a separate model from Message so that renaming or deleting 
    a conversation is a cheap, single-row operation. This also allows 
    conversations to exist with zero messages.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversations",
    )
    title = models.CharField(max_length=255, default="New Conversation", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"{self.title} (user={self.user_id})"


class Message(models.Model):
    """A single turn in a conversation. """

    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"

    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(max_length=16, choices=Role.choices)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        preview = self.content[:40]
        return f"[{self.role}] {preview}"