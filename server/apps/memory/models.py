from django.conf import settings
from django.db import models


class Memory(models.Model):
    """
    One remembered fact/preference about a user, e.g. "prefers concise answers" or "is vegetarian". Deliberately minimal - just a user and a text field - since a memory fact is normally a single short statement, not a document with its own title/structure.

    Rows are usually created by the agent itself (in tools/memory_tool. build_remember_tool), not typed directly by the user - but the user can still view/edit/delete them via this app's endpoints, which is what keeps automatic memory writing trustworthy rather than opaque.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memories"
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "memories"

    def __str__(self) -> str:
        # Used by retrieval/content.py's get_title() as a fallback label for citations, since Memory has no separate title field.
        return self.content[:50]