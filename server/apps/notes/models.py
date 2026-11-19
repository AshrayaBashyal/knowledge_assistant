from django.conf import settings
from django.db import models


class Note(models.Model):
    """
    A user-authored note. Unlike Document, there's no file - content is
    just a text field - so indexing is triggered automatically on every
    save (in retrieval/signals.py) rather than needing a separate manual
    action. In eager Celery mode this work runs inside the save request.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notes"
    )
    title = models.CharField(max_length=255, blank=True, default="Untitled Note")
    content = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return self.title