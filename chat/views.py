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

from agents.service import build_agent
# from llm.providers import get_chat_model
# from retrieval.retriever import retrieve_relevant_chunks

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
 

def _to_agent_input(history: list[Message]) -> list[dict]:
    """Converts stored messages into the plain {role, content} dict shape
    create_agent expects. Roles map directly since our Message.Role
    choices ("user"/"assistant") already match the agent's vocabulary."""
    return [{"role": msg.role, "content": msg.content} for msg in history]


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


def _stream_chat_response(conversation: Conversation) -> Iterator[str]:
    """
    Generator that:
      - tells the client which conversation this is (event: meta)
      -  runs the agent, which decides for itself whether to call a tool (retrieval, calculator, current_time) or just answer directly
      - announces each tool call as it happens (event: tool_call), and document sources specifically when search_my_documents was used (event: sources)
      - streams the assistant's own text token by token (event: token) - tool-call chunks and the tools node's raw output are filtered out, since neither is text meant for the user to read
      - saves the full assistant reply once streaming finishes
      - signals completion (event: done) or failure (event: error)

    Retrieval  used to run on every message regardless of whether the question actually needed it - simple, but wasteful when a document collection exists but isn't relevant to what was asked. Now, the AGENT  chooses whether retrieval (or any tool) is relevant per message, instead of a similarity search running on every single request.

    The user's message is saved by the caller before this generator starts, so it's never lost even if the model call fails.
    
    --------------------------------

    (X)- LANGGRAPH MULTI-MODE STREAMING ARCHITECTURE REFERENCE:

    We use `stream_mode=["updates", "messages"]`. This instructs LangGraph to blend two distinct data streams into a single loop. Each iteration yields a tuple: `(mode, chunk)`.

    1. `mode == "updates"` (Node Execution Completion)
       - Triggered ONLY when a graph node completes its entire step execution.
       - The `chunk` is a dictionary tracking state changes, keyed by the node name.
       - Structure:
         {
             "tools": {  # Key is the node name that executed
                 "messages": [
                     ToolMessage(content="Doc content...", name="search_my_documents", tool_call_id="id_1")
                 ]
             }
         }

    2. `mode == "messages"` (Token-by-Token LLM Generation)
       - Triggered continually as the LLM streams raw tokens for text or tool definitions.
       - The `chunk` is a 2-tuple: `(token, metadata)`
       - `token` is an AIMessageChunk object. It can contain text (.content) OR tool directions (.tool_calls).
       - `metadata` is a dict containing graph tracking context, such as which node emitted the token.
       - Structures:
         - Text Token Chunk:        (AIMessageChunk(content="Hello", tool_calls=[]), {"langgraph_node": "agent"})
         - Tool Call Request Chunk: (AIMessageChunk(content="", tool_calls=[{"name": "calculator", ...}]), {"langgraph_node": "agent"})
         - Raw Tool Output Chunk:   (AIMessageChunk(content="Execution log...", ...), {"langgraph_node": "tools"})
    """

    # Transmit the conversation ID immediately to the frontend before any AI processing latency begins.
    yield _sse_event("meta", {"conversation_id": conversation.id})
 
    # Load recent chat entries from PostgreSQL database and format it
    history = _load_history(conversation)
    agent_input = {"messages": _to_agent_input(history)}
 
    # A temporary storage array passed by reference into our tools.
    # The 'search_my_documents' tool will append its raw source document objects here during execution.
    sources_sink: list = []
    agent = build_agent(conversation.user, sources_sink)
 
    full_reply = ""
    tools_used: set[str] = set()
 
    try:
        # Loop through the combined updates and token message streams simultaneously
        for mode, chunk in agent.stream(
            agent_input, stream_mode=["updates", "messages"]
        ):
            # BRANCH A: NODE UPDATES (Detecting when tools run and extracting sources)
            if mode == "updates":
                # Check if the completed node update came from the "tools" executor node
                tool_update = chunk.get("tools")
                if not tool_update:
                    continue  # Ignore updates from non-tool nodes (e.g., the base agent node)
                
                # Scan through all the tool messages produced during this step
                for tool_message in tool_update.get("messages", []):
                    tool_name = getattr(tool_message, "name", None)
                    if not tool_name or tool_name in tools_used:
                        continue  # Skip invalid entries or tools we already broadcasted to the UI
                    
                    # Deduplicate: Track this tool so we don't alert the UI multiple times for one call
                    tools_used.add(tool_name)
                    yield _sse_event("tool_call", {"tool": tool_name})
                    
                    # If the executed tool was our document vector retriever, safely serialize and transmit the found document sources currently sitting inside our sink array.
                    if tool_name == "search_my_documents" and sources_sink:
                        yield _sse_event(
                            "sources", {"sources": _describe_sources(sources_sink)}
                        )
                continue  # Advance to the next stream iteration
 
            # BRANCH B: TEXT MESSAGES (Streaming visible text tokens to the browser chat)
            # mode == "messages": chunk is explicitly formatted as a (token, metadata) tuple
            token, metadata = chunk
            
            # FILTER 1: Skip raw text data passing straight out of the tool node itself.
            # This is backend log/database text, not copy edited answer text meant for a user.
            if metadata.get("langgraph_node") == "tools":
                continue  
                
            # FILTER 2: Skip structural tool arguments and function call setups.
            # If the model is outputting internal JSON schemas to configure a tool, keep it hidden from the UI.
            if getattr(token, "tool_calls", None):
                continue  
                
            # OUTPUT: If the token survives the filters and contains genuine message text, save it to the complete buffer string and push the raw text segment to the client UI.
            if token.content:
                full_reply += token.content
                yield _sse_event("token", {"content": token.content})
                
    except Exception as exc:  
        # Catch network timeouts, provider downtime, or code failures, and surface them cleanly to the frontend UI
        yield _sse_event("error", {"detail": str(exc)})
        return
 
    # Once the streaming loop finishes successfully, write the completely assembled response text back into PostgreSQL as a permanent ASSISTANT history log row.
    if full_reply:
        Message.objects.create(
            conversation=conversation,
            role=Message.Role.ASSISTANT,
            content=full_reply,
        )
        conversation.save(update_fields=["updated_at"])
 
    # Broadcast final termination packet to inform the frontend JavaScript client it can close the SSE connection.
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
                description="text/event-stream of meta/tool_call/sources/token/done/error frames"
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
            _stream_chat_response(conversation, data["message"]),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache" # Ensure the client gets real-time updates by preventing browser and proxy caching.
        response["X-Accel-Buffering"] = "no"  # disable Nginx/proxy buffering the SSE stream so events deliver instantly, if any
        return response
    













# Removed as it doesnt show errors properly .......... ..........
# def _to_langchain_messages(history: list[Message]) -> list:
#     """Maps our stored Message rows onto LangChain's message types, so the
#     model sees the same HumanMessage/AIMessage objects whether they came
#     from the database or from the current request."""
    
#     mapped = []
#     for msg in history:
#         if msg.role == Message.Role.USER:
#             mapped.append(HumanMessage(content=msg.content))
#         else:
#             mapped.append(AIMessage(content=msg.content))
#     return mapped


 
# moved to tools/ retrieval_tool .......... ..........
# def _build_context_message(chunks: list) -> SystemMessage:
#     """Formats retrieved chunks into a single system message, numbered so
#     the model can refer back to them (e.g. "[Source 1]") in its reply."""

#     parts = [
#         "Use the following retrieved context if it helps answer the user's question. When you use it, reference it as [Source N]."
#     ]
#     for i, chunk in enumerate(chunks, start=1):
#         title = chunk.metadata.get("document_title", "unknown")
        
#         # --- If Used 'page' metadata:
#         # page = chunk.metadata.get("page_number")   # use something like raw_page and them if rw_page, add 1. or in split_into_chunks function
#         # Build page string conditionally 
#         # page_str = f", Page {page}" if page is not None else ""
#         # parts.append(f"[Source {i}: {title}{page_str}]\n{chunk.page_content}")
        
#         parts.append(f"[Source {i}: {title}]\n{chunk.page_content}")
        
#     return SystemMessage(content="\n\n".join(parts))
