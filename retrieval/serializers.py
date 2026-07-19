from rest_framework import serializers

from retrieval.models import ContentIndex


class ContentIndexSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentIndex
        fields = ["object_id", "status", "chunk_count", "error", "indexed_at"]
        read_only_fields = fields