from drf_spectacular.utils import extend_schema
from django.contrib.contenttypes.models import ContentType
from django.db.models import OuterRef, Subquery
from rest_framework import generics, permissions

from apps.notes.models import Note
from apps.notes.serializers import NoteSerializer
from apps.retrieval.models import ContentIndex


@extend_schema(tags=["notes"])
class NoteListCreateView(generics.ListCreateAPIView):
    """
    GET - list the user's notes (newest first)
    POST - create a note

    Indexing happens automatically via a post_save signal (see
    retrieval/signals.py) - this view has no idea retrieval exists, the
    same way documents/views.py doesn't either. Notes just don't need an
    explicit index-trigger endpoint the way document upload does, since
    embedding a short text field is cheap enough to do inline.
    """

    serializer_class = NoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        content_type = ContentType.objects.get_for_model(Note)
        indexes = ContentIndex.objects.filter(
            content_type=content_type, object_id=OuterRef("pk")
        )
        return Note.objects.filter(user=self.request.user).annotate(
            index_status=Subquery(indexes.values("status")[:1]),
            index_error=Subquery(indexes.values("error")[:1]),
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@extend_schema(tags=["notes"])
class NoteDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET - one note
    PATCH - edit (re-indexed automatically on save)
    DELETE - delete (vector store entries cleaned up via signal, see retrieval/signals.py)
    """

    serializer_class = NoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        content_type = ContentType.objects.get_for_model(Note)
        indexes = ContentIndex.objects.filter(
            content_type=content_type, object_id=OuterRef("pk")
        )
        return Note.objects.filter(user=self.request.user).annotate(
            index_status=Subquery(indexes.values("status")[:1]),
            index_error=Subquery(indexes.values("error")[:1]),
        )

    def perform_update(self, serializer):
        serializer.save()
        serializer.instance = self.get_queryset().get(pk=serializer.instance.pk)