from django.conf import settings
from django.db import models


def document_upload_path(instance: "Document", filename: str) -> str:
    """
    Keeps each user's files under their own folder on disk. 
    Django auto-suffixes the filename on collision.
    """

    return f"document/{instance.user_id}/{filename}"


class Document(models.Model):
    """A single uploaded file (PDF, Markdown, or TXT)."""

    class FileType(models.TextChoices):
        PDF = "pdf", "PDF"
        MARKDOWN = "markdown", "Markdown"
        TXT = "txt", "Text"

    # Maps accepted file extensions to FileType constants. Used by serializers for validation.
    EXTENSION_MAP = {
        ".pdf": FileType.PDF,
        ".md": FileType.MARKDOWN,
        ".txt": FileType.TXT,
    }

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    file = models.FileField(upload_to=document_upload_path)
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=16, choices=FileType.choices)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self) -> str:
        return self.original_filename
