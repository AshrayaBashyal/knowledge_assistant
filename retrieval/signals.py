from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from documents.models import Document
from memory.models import Memory
from notes.models import Note
from retrieval.content import get_source_type
# from retrieval.indexing import index_content
from retrieval.models import ContentIndex
from retrieval.vectorstore import get_vector_store
from tasks.retrieval_tasks import index_content_task


@receiver(post_save, sender=Note)
def auto_index_note(sender, instance: Note, **kwargs):
    """
    Notes index automatically on every create/edit - unlike documents, which use an explicit endpoint (in retrieval/views.py). Embedding a short text field is cheap enough that requiring a separate manual step here would just be friction with no real benefit.

    Enqueued as a Celery task rather than run inline, so saving a note no longer blocks the HTTP response on an embedding call.

    The ContentIndex row is created here, synchronously, with status PENDING, before the task is even enqueued - not left for the task to create when it eventually runs. Without this, a client polling /api/retrieval/notes/<id>/index/ right after saving would get a 404 (no row exists yet) until the worker happens to pick the task up, which is a confusing gap for something that should read as "queued" from the very first moment.
    """

    content_type = ContentType.objects.get_for_model(instance)
    ContentIndex.objects.get_or_create(content_type=content_type, object_id=instance.pk)
    index_content_task.delay(content_type.id, instance.pk)


@receiver(post_save, sender=Memory)
def auto_index_memory(sender, instance: Memory, **kwargs):
    """Same reasoning as auto_index_note - a memory fact is even shorter
    than a note, so there's no cost worth deferring indexing for."""

    content_type = ContentType.objects.get_for_model(instance)
    ContentIndex.objects.get_or_create(content_type=content_type, object_id=instance.pk)
    index_content_task.delay(content_type.id, instance.pk)


def _cleanup_index(sender, instance, **kwargs):
    """
    Deleting a Document or Note doesn't automatically clean up its ContentIndex row or vector store entries - a GenericForeignKey's object_id is just an integer, not a real FK constraint, so Django can't cascade-delete it the way a OneToOneField would have. This is what replaces that lost cascade behavior.

    Runs synchronously, not as a Celery task, unlike indexing - deleting by known ids from the vector store is cheap and local (no model inference call, unlike embedding), and running it immediately avoids a window where deleted content briefly stays searchable because its async cleanup task hasn't run yet.
    """
    content_type = ContentType.objects.get_for_model(sender)
    try:
        index = ContentIndex.objects.get(content_type=content_type, object_id=instance.pk)
    except ContentIndex.DoesNotExist:
        return

    if index.chunk_count > 0:
        source_type = get_source_type(instance)
        ids = [f"{source_type}{instance.pk}-chunk{i}" for i in range(index.chunk_count)]
        get_vector_store(instance.user_id).delete(ids=ids)

    index.delete()


@receiver(post_delete, sender=Document)
def cleanup_document_index(sender, instance, **kwargs):
    _cleanup_index(sender, instance, **kwargs)


@receiver(post_delete, sender=Note)
def cleanup_note_index(sender, instance, **kwargs):
    _cleanup_index(sender, instance, **kwargs)


@receiver(post_delete, sender=Memory)
def cleanup_memory_index(sender, instance, **kwargs):
    _cleanup_index(sender, instance, **kwargs)