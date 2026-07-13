import json
from collections.abc import Iterator

from django.conf import settings
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
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
from retrieval.retriever import retrieve_relevant_chunks

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


def _describe_sources(chunks: list) -> list[dict]:
    """Turns retrieved LangChain Documents into a small JSON-friendly
    shape for the `sources` SSE event, so the frontend can show which
    documents/chunks informed the answer."""

    return [
        {
            "document_title": chunk.metadata.get("document_title", "unknown"),
            "chunk_index": chunk.metadata.get("chunk_index"),
            # "page_number": chunk.metadata.get("page")    # -page may start from index 0
        }
        for chunk in chunks
    ]


def _build_context_message(chunks: list) -> SystemMessage:
    """Formats retrieved chunks into a single system message, numbered so
    the model can refer back to them (e.g. "[Source 1]") in its reply."""

    parts = [
        "Use the following retrieved context if it helps answer the user's question. When you use it, reference it as [Source N]."
    ]
    for i, chunk in enumerate(chunks, start=1):
        title = chunk.metadata.get("document_title", "unknown")
        
        # --- If Used 'page' metadata:
        # page = chunk.metadata.get("page_number")   # use something like raw_page and them if rw_page, add 1. or in split_into_chunks function
        # Build page string conditionally 
        # page_str = f", Page {page}" if page is not None else ""
        # parts.append(f"[Source {i}: {title}{page_str}]\n{chunk.page_content}")
        
        parts.append(f"[Source {i}: {title}]\n{chunk.page_content}")
        
    return SystemMessage(content="\n\n".join(parts))


def _stream_chat_response(conversation: Conversation, latest_message: str) -> Iterator[str]:
    """
    Generator that:
      - tells the client which conversation this is (event: meta)
      - streams the model's reply token by token (event: token)
      - saves the full assistant reply once streaming finishes
      - signals completion (event: done) or failure (event: error)

    Retrieval runs on every message for now, regardless of whether the question actually needs it - simple, but wasteful when a document collection exists but isn't relevant to what was asked. Later (Agent) will replace this with the model deciding whether to retrieve, using retrieval as a tool instead of an always-on step.
 
    The user's message is saved by the caller before this generator
    starts, so it's never lost even if the model call fails.
    """

    yield _sse_event("meta", {"conversation_id": conversation.id})
 
    chunks = retrieve_relevant_chunks(
        conversation.user, latest_message, k=settings.RETRIEVAL_TOP_K
    )
    if chunks:
        yield _sse_event("sources", {"sources": _describe_sources(chunks)})
 
    history = _to_langchain_messages(_load_history(conversation))
    system_messages = [SystemMessage(content=SYSTEM_PROMPT)]
    if chunks:
        system_messages.append(_build_context_message(chunks))
    messages = [*system_messages, *history]
 
    model = get_chat_model()
    full_reply = ""
 
    try:
        for chunk in model.stream(messages):
            if chunk.content:
                full_reply += chunk.content
                yield _sse_event("token", {"content": chunk.content})
    except Exception as exc:  
        yield _sse_event("error", {"detail": str(exc)})
        return
 
    if full_reply:
        Message.objects.create(
            conversation=conversation,
            role=Message.Role.ASSISTANT,
            content=full_reply,
        )
        conversation.save(update_fields=["updated_at"])
 
    yield _sse_event("done", {})


class ChatStreamView(APIView):
    """
    Streams the assistant's reply via Server-Sent Events.

    If conversation_id is omitted, a new conversation is created on the
    fly and its id is sent back as the first SSE frame (event: meta) so
    the frontend can remember it for the next message. See _stream_chat_response for event shapes.
    """

    permission_classes = [permissions.IsAuthenticated]
 
    @extend_schema(
        tags=["chat"],
        request=ChatMessageInputSerializer,
        responses={
            200: OpenApiResponse(
                description="text/event-stream of meta/token/done/error frames"
            )
        },
    )
    def post(self, request: Request) -> StreamingHttpResponse:
        serializer = ChatMessageInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
 
        conversation_id = data.get("conversation_id")
        if conversation_id is not None:
            conversation = get_object_or_404(
                Conversation, id=conversation_id, user=request.user
            )
        else:
            conversation = Conversation.objects.create(user=request.user)
 
        # Saved before streaming starts, so the user's message is never
        # lost even if the model call fails partway through.
        Message.objects.create(
            conversation=conversation,
            role=Message.Role.USER,
            content=data["message"],
        )
 
        response = StreamingHttpResponse(
            _stream_chat_response(conversation),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache" # Ensure the client gets real-time updates by preventing browser and proxy caching.
        response["X-Accel-Buffering"] = "no"  # disable Nginx/proxy buffering the SSE stream so events deliver instantly, if any
        return response