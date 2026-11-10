import logging
from celery import shared_task
from django.contrib.contenttypes.models import ContentType

logger = logging.getLogger("tasks.retrieval")


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def index_content_task(self, content_type_id: int, object_id: int) -> None:
    """
    Celery task wrapper around retrieval.indexing.index_content.
    Includes automatic retries for transient cloud API network or rate limit hiccups.
    """
    from apps.retrieval.services.indexing import index_content

    try:
        content_type = ContentType.objects.get(id=content_type_id)
        obj = content_type.get_object_for_this_type(id=object_id)
        index_content(obj)
    except Exception as exc:
        logger.warning(
            "index_content_task retry triggered: %s (attempt %s/3)",
            exc,
            self.request.retries + 1,
        )
        raise self.retry(exc=exc)
