from rest_framework import serializers
 
from retrieval.models import DocumentIndex
 
 
class DocumentIndexSerializer(serializers.ModelSerializer):
    document_id = serializers.IntegerField(source="document.id", read_only=True)
 
    class Meta:
        model = DocumentIndex
        fields = ["document_id", "status", "chunk_count", "error", "indexed_at"]
        read_only_fields = fields