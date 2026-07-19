from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from documents.models import Document
from notes.models import Note
from retrieval.content import get_source_type
from retrieval.indexing import index_content
from retrieval.models import ContentIndex
from retrieval.vectorstore import get_vector_store


@receiver(post_save, sender=Note)
def auto_index_note(sender, instance: Note, **kwargs):
    """
    Notes index automatically on every create/edit - unlike documents,
    which use an explicit endpoint (see retrieval/views.py). Embedding a
    short text field is cheap enough that requiring a separate manual
    step here would just be friction with no real benefit.
    """
    index_content(instance)


def _cleanup_index(sender, instance, **kwargs):
    """
    Deleting a Document or Note doesn't automatically clean up its
    ContentIndex row or vector store entries - a GenericForeignKey's
    object_id is just an integer, not a real FK constraint, so Django
    can't cascade-delete it the way a OneToOneField would have. This is
    what replaces that lost cascade behavior.
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