import json
from collections.abc import Iterator

from django.conf import settings
from django.http import StreamingHttpResponse
from drf_spectacular.utils import OpenApiResponse, extend_schema
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from rest_framework import generics, permissions
from rest_framework.request import Request
from rest_framework.views import APIView

from chat.models import Conversation, Message
from chat.serializers import (
    ChatMessageInputSerializer,
    ConversationDetailSerializer,
    ConversationSerializer,
)
from llm.providers import get_chat_model

SYSTEM_PROMPT = "You are a helpful knowledge assistant. Answer clearly and concisely."


class ConversationListCreateView(generics.ListCreateAPIView):
    """ 
    List user's conversations (newest first) or create an empty conversation.

    Note: Empty creation is rarely needed since /stream/ auto-creates conversations.
    - mainly for "new chat" button before the user has typed anything.
    """
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ConversationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Handles retrieval (with messages), renaming (title only), and deletion.

    GET: Retrieve conversation and all its messages.
    PATCH: Rename conversation (title only).
    DELETE: Delete conversation.
    """
 
    permission_classes = [permissions.IsAuthenticated]
 
    def get_queryset(self):
        return Conversation.objects.filter(user=self.request.user)
 
    def get_serializer_class(self):
        if self.request.method == "GET":
            return ConversationDetailSerializer
        return ConversationSerializer


def _sse_event(event: str, data: dict) -> str:          # event_id: ??
    """Formats one Server-Sent Event frame. SSE requires a blank line
    (\\n\\n) to terminate each frame so the client knows where it ends."""

    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _load_history(conversation: Conversation) -> list[Message]:
    """
    Returns up to CHAT_HISTORY_MAX_MESSAGES most recent messages, oldest
    first, so they can be replayed to the model in chronological order.
    """

    limit = settings.CHAT_HISTORY_MAX_MESSAGES
    recent = list(conversation.messages.order_by("-created_at")[:limit])
    recent.reverse()
    return recent
 

def _to_langchain_messages(history: list[Message]) -> list:
    """Maps our stored Message rows onto LangChain's message types, so the
    model sees the same HumanMessage/AIMessage objects whether they came
    from the database or from the current request."""
    
    mapped = []
    for msg in history:
        if msg.role == Message.Role.USER:
            mapped.append(HumanMessage(content=msg.content))
        else:
            mapped.append(AIMessage(content=msg.content))
    return mapped


def _stream_chat_response(message: str) -> Iterator[str]:
    """
    Generator that yields SSE frames as the model streams tokens.

    event: token -> {"content": "<partial text>"}   (one per chunk)
    event: done  -> {}                               (stream finished)
    event: error -> {"detail": "..."}                (provider/network error)
    """

    model = get_chat_model()
    messages = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=message)]

    try:
        for chunk in model.stream(messages):
            if chunk.content:
                yield _sse_event("token", {"content": chunk.content})
        yield _sse_event("done", {})
    except Exception as exc:  
        yield _sse_event("error", {"detail": str(exc)})


class ChatStreamView(APIView):
    """
    Streams the assistant's reply via Server-Sent Events.
    Currently stateless with no conversational memory, but session history will be added later. See _stream_chat_response for event shapes.
    """

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["chat"],
        request=ChatMessageInputSerializer,
        responses={
            200: OpenApiResponse(
                description="text/event-stream of token/done/error frames"
            )
        },
    )
    def post(self, request: Request) -> StreamingHttpResponse:
        serializer = ChatMessageInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        response = StreamingHttpResponse(
            _stream_chat_response(serializer.validated_data["message"]),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache" # Ensure the client gets real-time updates by preventing browser and proxy caching.
        response["X-Accel-Buffering"] = "no"  # disable Nginx/proxy buffering the SSE stream so events deliver instantly, if any
        return response