from django.db import models


class DocumentIndex(models.Model):
    """
    Tracks the indexing state of one Document.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        INDEXED = "indexed", "Indexed"
        FAILED = "failed", "Failed"

    document = models.OneToOneField(
        "documents.Document", on_delete=models.CASCADE, related_name="index"
    )
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.PENDING
    )
    chunk_count = models.PositiveIntegerField(default=0)
    error = models.TextField(blank=True)
    indexed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Index for document {self.document_id} ({self.status})"