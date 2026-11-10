from django.conf import settings
from django.db import connection
from django.db.models import Q, Value
from django.db.models.functions import Replace
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.chat.models import Message
from apps.documents.models import Document
from apps.notes.models import Note
from apps.search.serializers import SearchResultSerializer

RESULTS_PER_SOURCE = getattr(settings, "RESULTS_PER_SOURCE", 10)


def _normalized_filename():
    """
    Splits underscores/hyphens/dots into spaces so words inside filenames
    (like "quarterly_budget_report.pdf") become individual searchable tokens.
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

    Full-text workspace search across the user's documents, notes, and chat messages.
    Uses database-native indexing (PostgreSQL SearchVector + SearchRank on Neon/production)
    with seamless fallback for typos/partial matches, and standard indexed queries on SQLite.
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

        is_postgres = connection.vendor == "postgresql"

        if is_postgres:
            results = self._search_postgres(request.user, query_text)
            # If strict full-text search found nothing (e.g. typos or partial words),
            # fall back to partial substring matching so the user gets relevant results.
            if not results:
                results = self._search_fallback(request.user, query_text)
        else:
            results = self._search_fallback(request.user, query_text)

        results.sort(key=lambda r: r.get("rank", 0), reverse=True)
        serializer = SearchResultSerializer(results, many=True)
        return Response({"results": serializer.data})

    def _search_postgres(self, user, query_text: str) -> list[dict]:
        """PostgreSQL full-text search with SearchVector & SearchRank."""
        from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector

        results = []
        try:
            query = SearchQuery(query_text)

            documents = (
                Document.objects.filter(user=user)
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
                        "rank": float(doc.rank),
                    }
                )

            notes = (
                Note.objects.filter(user=user)
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
                        "rank": float(note.rank),
                    }
                )

            messages = (
                Message.objects.filter(conversation__user=user)
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
                        "rank": float(message.rank),
                    }
                )
        except Exception:
            return []

        return results

    def _search_fallback(self, user, query_text: str) -> list[dict]:
        """Fast database partial/case-insensitive substring search."""
        terms = [t for t in query_text.split() if t]
        if not terms:
            return []

        results = []

        doc_q = Q()
        for term in terms:
            doc_q |= Q(original_filename__icontains=term)
        for doc in Document.objects.filter(Q(user=user) & doc_q)[:RESULTS_PER_SOURCE]:
            results.append(
                {
                    "type": "document",
                    "id": doc.id,
                    "title": doc.original_filename,
                    "snippet": doc.original_filename,
                    "rank": 0.5,
                }
            )

        note_q = Q()
        for term in terms:
            note_q |= Q(title__icontains=term) | Q(content__icontains=term)
        for note in Note.objects.filter(Q(user=user) & note_q)[:RESULTS_PER_SOURCE]:
            results.append(
                {
                    "type": "note",
                    "id": note.id,
                    "title": note.title,
                    "snippet": note.content[:200],
                    "rank": 0.5,
                }
            )

        msg_q = Q()
        for term in terms:
            msg_q |= Q(content__icontains=term)
        for message in Message.objects.filter(
            Q(conversation__user=user) & msg_q
        )[:RESULTS_PER_SOURCE]:
            results.append(
                {
                    "type": "message",
                    "id": message.id,
                    "conversation_id": message.conversation_id,
                    "title": f"{message.role} message",
                    "snippet": message.content[:200],
                    "rank": 0.5,
                }
            )

        return results
