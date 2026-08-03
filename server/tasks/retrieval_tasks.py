from celery import shared_task
from django.contrib.contenttypes.models import ContentType


@shared_task
def index_content_task(content_type_id: int, object_id: int) -> None:
    """
    Celery task wrapper around retrieval.indexing.index_content.

    Takes content_type_id + object_id (plain, serializable values), not a model instance - Celery tasks are queued as JSON messages, and an ORM instance can't survive that trip; even if it could, it might be stale by the time a worker actually picks the task up.

    The indexing logic itself is unchanged - only how it's invoked changed. Import is inside the function, not at module level, to avoid importing the whole retrieval/documents/notes/memory chain at Celery app startup before Django's app registry is settled.
    """
    from apps.retrieval.services.indexing import index_content

    content_type = ContentType.objects.get(id=content_type_id)
    obj = content_type.get_object_for_this_type(id=object_id)
    index_content(obj)