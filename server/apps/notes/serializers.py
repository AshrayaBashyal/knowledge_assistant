from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType

from apps.notes.models import Note
from apps.retrieval.models import ContentIndex


class NoteSerializer(serializers.ModelSerializer):
    index_status = serializers.SerializerMethodField()
    index_error = serializers.SerializerMethodField()

    class Meta:
        model = Note
        fields = [
            "id",
            "title",
            "content",
            "created_at",
            "updated_at",
            "index_status",
            "index_error",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_index_status(self, obj):
        if hasattr(obj, "index_status"):
            return obj.index_status
        return self._get_index(obj, "status")

    def get_index_error(self, obj):
        if hasattr(obj, "index_error"):
            return obj.index_error
        return self._get_index(obj, "error")

    @staticmethod
    def _get_index(obj, field):
        content_type = ContentType.objects.get_for_model(Note)
        return (
            ContentIndex.objects.filter(content_type=content_type, object_id=obj.pk)
            .values_list(field, flat=True)
            .first()
        )