from rest_framework import serializers

from memory.models import Memory


class MemorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Memory
        fields = ["id", "content", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]