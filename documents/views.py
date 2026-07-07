from rest_framework import permissions, generics
from documents.models import Document
from documents.serializers import DocumentSerializer, DocumentUploadSerializer
from drf_spectacular.utils import extend_schema

@extend_schema(tags=["documents"])
class DocumentListCreateView(generics.ListCreateAPIView):
    """
    GET -> list the user's uploaded documents
    POST -> upload a new one (multipart/form-data, field name "file")
    """
 
    permission_classes = [permissions.IsAuthenticated]
 
    def get_queryset(self):
        return Document.objects.filter(user=self.request.user)
 
    def get_serializer_class(self):
        if self.request.method == "POST":
            return DocumentUploadSerializer
        return DocumentSerializer
 
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)