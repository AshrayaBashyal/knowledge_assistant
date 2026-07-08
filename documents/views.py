from django.http import FileResponse
from django.shortcuts import get_object_or_404
from documents.models import Document
from documents.serializers import DocumentSerializer, DocumentUploadSerializer
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, generics, parsers
from rest_framework.request import Request
from rest_framework.views import APIView

@extend_schema(
    tags=["documents"],
    # Forces Swagger to map the successful return value to DocumentSerializer
    responses={201: DocumentSerializer}
    )
class DocumentListCreateView(generics.ListCreateAPIView):
    """
    GET -> list the user's uploaded documents
    POST -> upload a new one (multipart/form-data, field name "file")
    """
 
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
 
    def get_queryset(self):
        return Document.objects.filter(user=self.request.user)
 
    def get_serializer_class(self):
        if self.request.method == "POST":
            return DocumentUploadSerializer
        return DocumentSerializer
 
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@extend_schema(tags=["documents"])
class DocumentDetailView(generics.RetrieveDestroyAPIView):
    """
    GET <id>/  -> metadata for one document
    DELETE <id>/  -> removes the DB row and the file on disk
    """
 
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
 
    def get_queryset(self):
        return Document.objects.filter(user=self.request.user)
 
    def perform_destroy(self, instance: Document):
        instance.file.delete(save=False)  # remove from storage, not just the DB row
        instance.delete()


class DocumentDownloadView(APIView):
    """
    GET -> download user's document
 
    Streams the raw file to its owner. This exists instead of exposing
    Django's public MEDIA_URL directly, because these files are private
    per-user data - a public static URL would let anyone with a guessed
    link read someone else's document.
    """
 
    permission_classes = [permissions.IsAuthenticated]
 
    @extend_schema(tags=["documents"], responses={200: bytes})
    def get(self, request: Request, pk: int) -> FileResponse:
        document = get_object_or_404(Document, pk=pk, user=request.user)
        return FileResponse(
            document.file.open("rb"),
            as_attachment=True,
            filename=document.original_filename,
        )