from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db.models.functions import Replace
from django.db.models import Value
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from chat.models import Message
from documents.models import Document
from notes.models import Note
from search.serializers import SearchResultSerializer

from django.conf import settings


RESULTS_PER_SOURCE = settings.RESULTS_PER_SOURCE


def _normalized_filename():
    """
    Filenames use underscores/hyphens/dots as word separators ("quarterly_budget_report.txt"), but Postgres's search parser treats a string with no spaces as one indivisible token a search for "budget" would never match that filename as store Replacing separators with spaces before tokenizing lets each word (and the extension) become its own searchable lexeme, directly against Postgres: to_tsvector('quarterly_budget_repor txt') keeps it as one token, but to_tsvector on the space version correctly splits into 'quarterli', 'budget', 'repor 'txt'.
    """
    return Replace(
        Replace(
            Replace("original_filename", Value("_"), Value(" ")),
            Value("-"),
            Value(" "),
        ),
        Value("."),
        Value(" "),
    )


class WorkspaceSearchView(APIView):
    """
    GET /api/search/?q=<query>

    Full-text search across the user's own documents, notes and chat messages, using Postgres's built-in text searc (SearchVector + SearchRank) rather than the vector store.

    This is deliberately not semantic/embedding-based search Workspace Search is a keyword lookup tool for the user to find thei own content quickly, not a retrieval-quality concern - that' what search_my_knowledge (the agent tool, Milestone 6) is for Embedding every chat message just to support this would mean a embedding call on every single turn, forever, for a feature use occasionally.

    Ranking caveat worth naming: each source's `rank` i computed independently (SearchRank isn't calibrated acros different tables/ fields), so combining and sorting them together is a approximation, not a rigorously unified relevance score. Good enough fo "find my stuff quickly"; not a research-grade ranking system.
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

        query = SearchQuery(query_text)
        results = []

        documents = (
            Document.objects.filter(user=request.user)
            .annotate(rank=SearchRank(SearchVector(_normalized_filename()), query))
            .filter(rank__gt=0)
            .order_by("-rank")[:RESULTS_PER_SOURCE]
        )
        for doc in documents:
            results.append(
                {
                    "type": "document",
                    "id": doc.id,
                    "title": doc.original_filename,
                    "snippet": doc.original_filename,
                    "rank": doc.rank,
                }
            )

        notes = (
            Note.objects.filter(user=request.user)
            .annotate(rank=SearchRank(SearchVector("title", "content"), query))
            .filter(rank__gt=0)
            .order_by("-rank")[:RESULTS_PER_SOURCE]
        )
        for note in notes:
            results.append(
                {
                    "type": "note",
                    "id": note.id,
                    "title": note.title,
                    "snippet": note.content[:200],
                    "rank": note.rank,
                }
            )

        messages = (
            Message.objects.filter(conversation__user=request.user)
            .annotate(rank=SearchRank(SearchVector("content"), query))
            .filter(rank__gt=0)
            .order_by("-rank")[:RESULTS_PER_SOURCE]
        )
        for message in messages:
            results.append(
                {
                    "type": "message",
                    "id": message.id,
                    "conversation_id": message.conversation_id,
                    "title": f"{message.role} message",
                    "snippet": message.content[:200],
                    "rank": message.rank,
                }
            )

        results.sort(key=lambda r: r["rank"], reverse=True)

        serializer = SearchResultSerializer(results, many=True)
        return Response({"results": serializer.data})