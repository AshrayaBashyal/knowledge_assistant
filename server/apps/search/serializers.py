from rest_framework import serializers


class SearchResultSerializer(serializers.Serializer):
    """
    One unified shape for a search hit regardless of where it came from. `conversation_id` is only populated for message results (it's how the frontend would link back to "open this conversation").
    """

    type = serializers.ChoiceField(choices=["document", "note", "message"])
    id = serializers.IntegerField()
    title = serializers.CharField()
    snippet = serializers.CharField()
    rank = serializers.FloatField()
    conversation_id = serializers.IntegerField(required=False, allow_null=True)