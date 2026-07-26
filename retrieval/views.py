from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from documents.models import Document
from notes.models import Note
# from retrieval.indexing import index_content
from retrieval.models import ContentIndex
from retrieval.serializers import ContentIndexSerializer
from tasks.retrieval_tasks import index_content_task

class _BaseIndexView(APIView):
    """
    Shared logic for triggering (re-)indexing of one content object.
    Subclasses just declare which model to look the object up in -
    everything else (ownership check, calling index_content, response
    shape) is identical regardless of content type.

    POST enqueues a Celery task and returns immediately (202) rather than
    running indexing inline - chunk/embed/store now happens on a worker
    process. GET lets the client poll for the result afterward.
    """

    permission_classes = [permissions.IsAuthenticated]
    model = None

    def _get_object(self, request, pk):
        return get_object_or_404(self.model, pk=pk, user=request.user)

    @extend_schema(
        tags=["retrieval"],
        request=None,
        responses={202: ContentIndexSerializer},
    )
    def post(self, request: Request, pk: int) -> Response:
        obj = self._get_object(request, pk)
        content_type = ContentType.objects.get_for_model(obj)

        index, _ = ContentIndex.objects.get_or_create(
            content_type=content_type, object_id=obj.pk
        )
        index.status = ContentIndex.Status.PENDING
        index.save(update_fields=["status"])

        index_content_task.delay(content_type.id, obj.pk)

        serializer = ContentIndexSerializer(index)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    @extend_schema(tags=["retrieval"], responses={200: ContentIndexSerializer})
    def get(self, request: Request, pk: int) -> Response:
        obj = self._get_object(request, pk)
        content_type = ContentType.objects.get_for_model(obj)
        index = get_object_or_404(
            ContentIndex, content_type=content_type, object_id=obj.pk
        )
        return Response(ContentIndexSerializer(index).data) 
    


class DocumentIndexView(_BaseIndexView):
    """
    POST /api/retrieval/documents/<id>/index/ - chunk/embed/store a document - enqueue indexing (202)
    GET  /api/retrieval/documents/<id>/index/  - check current status
    """

    model = Document


class NoteIndexView(_BaseIndexView):
    """
    POST /api/retrieval/notes/<id>/index/  - Manual re-index of a note. Notes normally index automatically on save (in retrieval/signals.py) - this exists as a retry path, e.g. after a brief embedding failure, without needing to touch the note's content again just to re-trigger indexing.

    GET  /api/retrieval/notes/<id>/index/  - check current status
    """

    model = Note