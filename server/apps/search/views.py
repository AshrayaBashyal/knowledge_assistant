from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.chat.models import Message
from apps.documents.models import Document
from apps.notes.models import Note
from apps.search.ranking_algorithm import rank_by_bm25
from apps.search.serializers import SearchResultSerializer

RESULTS_PER_SOURCE = 10


class WorkspaceSearchView(APIView):
    """
    GET /api/search/?q=<query>

    Full-text search across the user's own documents, notes, and chat
    messages, ranked by a manually-implemented BM25 (search/ranking.py)
    rather than Postgres's SearchRank/SearchVector - the query itself is
    plain Django filtering (fetch the user's own rows), but relevance
    scoring is entirely our own code, not the database's.

    This is deliberately not semantic/embedding-based search: Workspace
    Search is a keyword lookup tool for the user to find their own
    content quickly, not a retrieval-quality concern - that's what
    search_my_knowledge (the agent tool, Milestone 6) is for. Embedding
    every chat message just to support this would mean an embedding call
    on every single turn, forever, for a feature used occasionally.

    Two caveats worth naming plainly:
    - Each source's BM25 corpus (documents, notes, messages) is scored
      independently - BM25 is inherently corpus-relative (a term's
      rarity is only meaningful relative to a specific document set), so
      combining and sorting the three scored lists together afterward is
      an approximation, not a rigorously unified relevance score. Same
      caveat the previous Postgres-based version had.
    - BM25 needs the whole candidate corpus's statistics (average
      document length, how many documents contain each term) computed
      up front, so this fetches every one of the user's rows per source
      rather than letting the database filter first - fine at the scale
      a personal knowledge assistant's per-user data actually reaches,
      but a real cost that a database-side ranked index doesn't have.
    """

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["search"],
        parameters=[
            OpenApiParameter(
                "q", str, description="Search query", required=True
            )
        ],
        responses={200: SearchResultSerializer(many=True)},
    )
    def get(self, request: Request) -> Response:
        query_text = request.query_params.get("q", "").strip()
        if not query_text:
            return Response({"results": []})

        results = []

        documents = list(Document.objects.filter(user=request.user))
        doc_ranked = rank_by_bm25(
            query_text, [(str(d.id), d.original_filename) for d in documents]
        )
        documents_by_id = {str(d.id): d for d in documents}
        for doc_id, score in doc_ranked[:RESULTS_PER_SOURCE]:
            if score <= 0:
                break  # results are sorted best-first, so nothing after this matches either
            doc = documents_by_id[doc_id]
            results.append(
                {
                    "type": "document",
                    "id": doc.id,
                    "title": doc.original_filename,
                    "snippet": doc.original_filename,
                    "rank": score,
                }
            )

        notes = list(Note.objects.filter(user=request.user))
        note_ranked = rank_by_bm25(
            query_text, [(str(n.id), f"{n.title} {n.content}") for n in notes]
        )
        notes_by_id = {str(n.id): n for n in notes}
        for note_id, score in note_ranked[:RESULTS_PER_SOURCE]:
            if score <= 0:
                break
            note = notes_by_id[note_id]
            results.append(
                {
                    "type": "note",
                    "id": note.id,
                    "title": note.title,
                    "snippet": note.content[:200],
                    "rank": score,
                }
            )

        messages = list(Message.objects.filter(conversation__user=request.user))
        message_ranked = rank_by_bm25(
            query_text, [(str(m.id), m.content) for m in messages]
        )
        messages_by_id = {str(m.id): m for m in messages}
        for message_id, score in message_ranked[:RESULTS_PER_SOURCE]:
            if score <= 0:
                break
            message = messages_by_id[message_id]
            results.append(
                {
                    "type": "message",
                    "id": message.id,
                    "conversation_id": message.conversation_id,
                    "title": f"{message.role} message",
                    "snippet": message.content[:200],
                    "rank": score,
                }
            )

        results.sort(key=lambda r: r["rank"], reverse=True)

        serializer = SearchResultSerializer(results, many=True)
        return Response({"results": serializer.data})
