from rest_framework import serializers


class ChatMessageInputSerializer(serializers.Serializer):
    """
    Input payload for the LLM chat endpoint.
    Omitting optional `conversation_id` auto-creates a new conversation (see ChatStreamView).
    """
    
    message = serializers.CharField(allow_blank=False, trim_whitespace=True)
    conversation_id = serializers.IntegerField(required=False, allow_null=True)
 