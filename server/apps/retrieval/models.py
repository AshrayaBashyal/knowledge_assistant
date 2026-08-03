from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class ContentIndex(models.Model):
    """
    Tracks the indexing state of one piece of content - a Document OR a
    Note. 
    Uses a GenericForeignKey (content_type + object_id) instead of a separate index model per content type, so a single retrieval call can rank documents and notes together by relevance, rather than the agent having to guess which of several separate tools to call.

    Trade-off worth naming: a GenericForeignKey's object_id is just an integer, not a real FK constraint - Django can't cascade-delete this row automatically the way a normal ForeignKey would. That's why retrieval/signals.py exists: it's what replaces the cascade behavior a OneToOneField would have given us for free.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        INDEXED = "indexed", "Indexed"
        FAILED = "failed", "Failed"

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.PENDING
    )
    chunk_count = models.PositiveIntegerField(default=0)
    error = models.TextField(blank=True)
    indexed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["content_type", "object_id"], name="unique_content_index"
            )
        ]

    def __str__(self) -> str:
        return f"Index for {self.content_type.model} {self.object_id} ({self.status})"