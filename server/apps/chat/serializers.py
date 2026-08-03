from rest_framework import serializers
from apps.chat.models import Conversation, Message


class ChatMessageInputSerializer(serializers.Serializer):
    """
    Input payload for the LLM chat endpoint.
    Omitting optional `conversation_id` auto-creates a new conversation (see ChatStreamView).
    """

    message = serializers.CharField(allow_blank=False, trim_whitespace=True)
    conversation_id = serializers.IntegerField(required=False, allow_null=True)
 

class MessageSerializer(serializers.ModelSerializer):
    """Exposes message details."""

    class Meta:
        model = Message
        fields = ["id", "role", "content", "created_at"]
        read_only_fields = ["id", "role", "content", "created_at"]
 

class ConversationSerializer(serializers.ModelSerializer):
    """Used for listing conversations, creating one manually, and renaming its title."""
 
    class Meta:
        model = Conversation
        fields = ["id", "title", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ConversationDetailSerializer(ConversationSerializer):
    """Adds the full message list - only used for the single-conversation
    GET, not the list view, to avoid pulling every message for every
    conversation when someone just wants the sidebar list."""
 
    messages = MessageSerializer(many=True, read_only=True)
 
    class Meta(ConversationSerializer.Meta):
        fields = ConversationSerializer.Meta.fields + ["messages"]
