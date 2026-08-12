from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.chat.models import Message
from apps.documents.models import Document
from apps.notes.models import Note
from apps.search.levenshtein_algorithm import find_closest_word
from apps.search.ranking_algorithm import rank_by_bm25, tokenize
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

    If BM25 finds nothing at all, this falls back to a manual
    Levenshtein-distance fuzzy match (search/fuzzy.py) against the
    user's own vocabulary - a typo shouldn't just return a silent empty
    result when the word the user meant is sitting right there in one
    of their own documents.

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
    - BM25 needs the whole candidate corpus's statistics computed up
      front, so this fetches every one of the user's rows per source
      rather than letting the database filter first - fine at the scale
      a personal knowledge assistant's per-user data actually reaches,
      but a real cost a database-side ranked index doesn't have.
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

        documents = list(Document.objects.filter(user=request.user))
        notes = list(Note.objects.filter(user=request.user))
        messages = list(Message.objects.filter(conversation__user=request.user))

        results = self._search(query_text, documents, notes, messages)
        corrected_query = None

        if not results:
            corrected_query = self._try_fuzzy_correction(
                query_text, documents, notes, messages
            )
            if corrected_query:
                results = self._search(corrected_query, documents, notes, messages)
                if not results:
                    corrected_query = None  # the "correction" didn't actually help

        serializer = SearchResultSerializer(results, many=True)
        response_data = {"results": serializer.data}
        if corrected_query:
            response_data["corrected_query"] = corrected_query
        return Response(response_data)

    def _search(self, query_text, documents, notes, messages) -> list[dict]:
        """Runs BM25 ranking across all three sources for one query
        string and returns the merged, sorted result list. Pulled out as
        its own method so both the original query and a fuzzy-corrected
        retry (see get()) share identical ranking logic rather than
        duplicating this per call site."""
        results = []

        doc_ranked = rank_by_bm25(
            query_text, [(str(d.id), d.original_filename) for d in documents]
        )
        documents_by_id = {str(d.id): d for d in documents}
        for doc_id, score in doc_ranked[:RESULTS_PER_SOURCE]:
            if score <= 0:
                break  # sorted best-first, so nothing after this matches either
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
        return results

    def _try_fuzzy_correction(self, query_text, documents, notes, messages) -> str | None:
        """
        Builds a vocabulary from the user's own content (already fetched
        for the BM25 pass - no extra DB queries) and tries to find a
        close match for each query word via Levenshtein distance. Returns
        a corrected query string only if at least one word was actually
        changed - if every query word is already the closest match to
        itself, "correcting" would just return the original query.
        """
        vocabulary = set()
        for doc in documents:
            vocabulary.update(tokenize(doc.original_filename))
        for note in notes:
            vocabulary.update(tokenize(note.title))
            vocabulary.update(tokenize(note.content))
        for message in messages:
            vocabulary.update(tokenize(message.content))

        if not vocabulary:
            return None

        query_terms = tokenize(query_text)
        corrected_terms = []
        changed = False

        for term in query_terms:
            match = find_closest_word(term, vocabulary)
            if match and match != term:
                changed = True
                corrected_terms.append(match)
            else:
                corrected_terms.append(term)

        return " ".join(corrected_terms) if changed else None