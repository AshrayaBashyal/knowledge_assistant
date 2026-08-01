import logging
import time

from celery import shared_task
from django.contrib.contenttypes.models import ContentType

logger = logging.getLogger("flashcards.generation")


@shared_task
def generate_flashcards_task(
    flashcard_set_id: int, content_type_id: int, object_id: int, count: int
) -> None:
    """
    Celery task wrapper around flashcards.generator.generate_flashcards.

    The FlashcardSet row already exists (created synchronously with status=pending, in flashcards/views.py) before this task runs - the task's job is to fill in its cards and flip its status once done, not to create the set itself, so the API response from POST /generate/ has something to return immediately.
    """
    from flashcards.generator import generate_flashcards
    from flashcards.models import Flashcard, FlashcardSet

    flashcard_set = FlashcardSet.objects.get(id=flashcard_set_id)
    content_type = ContentType.objects.get(id=content_type_id)
    obj = content_type.get_object_for_this_type(id=object_id)

    started_at = time.monotonic()

    try:
        items = generate_flashcards(obj, count=count)
        Flashcard.objects.bulk_create(
            Flashcard(
                flashcard_set=flashcard_set,
                question=item.question,
                answer=item.answer,
                difficulty=item.difficulty,
                category=item.category,
            )
            for item in items
        )
        flashcard_set.status = FlashcardSet.Status.COMPLETED

        logger.info(
            "flashcards_generated",
            extra={
                "flashcard_set_id": flashcard_set_id,
                "user_id": flashcard_set.user_id,
                "card_count": len(items),
                "duration_ms": round((time.monotonic() - started_at) * 1000, 2),
            },
        )

    except Exception as exc:
        flashcard_set.status = FlashcardSet.Status.FAILED
        flashcard_set.error = str(exc)

        logger.exception(
            "flashcard_generation_failed",
            extra={
                "flashcard_set_id": flashcard_set_id,
                "user_id": flashcard_set.user_id,
                "duration_ms": round((time.monotonic() - started_at) * 1000, 2),
            },
        )
        
    finally:
        flashcard_set.save() 