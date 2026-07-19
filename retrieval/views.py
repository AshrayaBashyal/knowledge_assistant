from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from documents.models import Document
from notes.models import Note
from retrieval.indexing import index_content
from retrieval.models import ContentIndex
from retrieval.serializers import ContentIndexSerializer


class _BaseIndexView(APIView):
    """
    Shared logic for triggering (re-)indexing of one content object.
    Subclasses just declare which model to look the object up in -
    everything else (ownership check, calling index_content, response
    shape) is identical regardless of content type.
    """

    permission_classes = [permissions.IsAuthenticated]
    model = None

    @extend_schema(
        tags=["retrieval"],
        request=None,
        responses={200: ContentIndexSerializer, 422: ContentIndexSerializer},
    )
    def post(self, request: Request, pk: int) -> Response:
        obj = get_object_or_404(self.model, pk=pk, user=request.user)
        index = index_content(obj)

        serializer = ContentIndexSerializer(index)
        response_status = (
            status.HTTP_200_OK
            if index.status == ContentIndex.Status.INDEXED
            else status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        return Response(serializer.data, status=response_status)


class DocumentIndexView(_BaseIndexView):
    """POST /api/retrieval/documents/<id>/index/ - chunk/embed/store a document."""

    model = Document


class NoteIndexView(_BaseIndexView):
    """
    POST /api/retrieval/notes/<id>/index/

    Manual re-index of a note. Notes normally index automatically on
    save (in retrieval/signals.py) - this exists as a retry path, e.g.
    after a brief embedding failure, without needing to touch the
    note's content again just to re-trigger indexing.
    """

    model = Note