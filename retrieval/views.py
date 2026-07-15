from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from documents.models import Document
from retrieval.indexing import index_document
from retrieval.models import DocumentIndex
from retrieval.serializers import DocumentIndexSerializer


class DocumentIndexView(APIView):
    """
    Triggers (re-)indexing of one document owned by the requesting user:
    chunk -> embed -> store. Runs synchronously and returns once finished.
    """

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["retrieval"],
        request=None,
        responses={200: DocumentIndexSerializer, 422: DocumentIndexSerializer},
    )
    def post(self, request: Request, pk: int) -> Response:
        document = get_object_or_404(Document, pk=pk, user=request.user)
        index = index_document(document)

        serializer = DocumentIndexSerializer(index)
        response_status = (
            status.HTTP_200_OK
            if index.status == DocumentIndex.Status.INDEXED
            else status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        return Response(serializer.data, status=response_status)