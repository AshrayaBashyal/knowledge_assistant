from rest_framework import serializers
from documents.models import Document

class DocumentSerializer(serializers.ModelSerializer):
    """Read representation - used for list, retrieve, and as the response
    shape after a successful upload."""
 
    class Meta:
        model = Document
        fields = ["id", "original_filename", "file_type", "uploaded_at"]
        read_only_fields = ["id", "original_filename", "file_type", "uploaded_at"]