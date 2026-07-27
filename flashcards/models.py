
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
 
 
class FlashcardSet(models.Model):
    """
    One batch of flashcards generated from a single Document or Note.
    Uses a GenericForeignKey (same pattern as retrieval.ContentIndex)
    since the source can be either type.
 
    Unlike ContentIndex, deleting the source does NOT cascade-delete a
    FlashcardSet -- a ContentIndex is meaningless without its content still
    existing, but generated flashcards are a standalone study artifact a
    user would reasonably want to keep even after removing the source
    document. `source_title` is cached at generation time precisely so
    the set still displays sensibly if the source is later deleted.

    `status`/`error` exist because generation now runs on a Celery
    worker: the set row is created immediately so POST /generate/
    has something to return right away, and this field is how the
    client finds out whether generation actually finished.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="flashcard_sets"
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    source = GenericForeignKey("content_type", "object_id")
    source_title = models.CharField(max_length=255)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        ordering = ["-created_at"]
 
    def __str__(self) -> str:
        return f"Flashcards from {self.source_title}"
    

class Flashcard(models.Model):
    class Difficulty(models.TextChoices):
        EASY = "easy", "Easy"
        MEDIUM = "medium", "Medium"
        HARD = "hard", "Hard"

    flashcard_set = models.ForeignKey(
        FlashcardSet, on_delete=models.CASCADE, related_name="flashcards"
    )
    question = models.TextField()
    answer = models.TextField()
    difficulty = models.CharField(
        max_length=16, choices=Difficulty.choices, default=Difficulty.MEDIUM
    )
    category = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return self.question[:50]