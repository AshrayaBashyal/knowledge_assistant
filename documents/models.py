from django.conf import settings
from django.db import models

class Document(models.Model):
    class FileType(models.TextChoices):
        PDF = "pdf", "PDF"
        MARKDOWN = "markdown", "Markdown"
        TXT = "txt", "Text"

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
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=16, choices=FileType.choices)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self) -> str:
        return self.original_filename
