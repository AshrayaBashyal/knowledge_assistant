import json
from collections.abc import Iterator

from django.http import StreamingHttpResponse
from drf_spectacular.utils import OpenApiResponse, extend_schema
from langchain_core.messages import HumanMessage, SystemMessage
from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView

from chat.serializers import ChatMessageInputSerializer
from llm.providers import get_chat_model

SYSTEM_PROMPT = "You are a helpful knowledge assistant. Answer clearly and concisely."


def _sse_event(event: str, data: dict) -> str:
    """Formats one Server-Sent Event frame. SSE requires a blank line
    (\\n\\n) to terminate each frame so the client knows where it ends."""

    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


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