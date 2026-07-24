from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions

from memory.models import Memory
from memory.serializers import MemorySerializer


@extend_schema(tags=["memory"])
class MemoryListCreateView(generics.ListCreateAPIView):
    """
    GET -> list the user's remembered facts (newest first)
    POST -> manually add one (most memories are written by the agent itself via the remember_fact tool -  this exists so a user can add one directly too)

    Indexing into the shared vector collection happens automatically via a post_save signal (see retrieval/signals.py), same treatment as Note.
    """

    serializer_class = MemorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Memory.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@extend_schema(tags=["memory"])
class MemoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET -> one memory
    PATCH -> correct it (re-indexed automatically on save)
    DELETE -> forget it (vector store entry cleaned up via signal)

    This is what keeps automatic memory writing trustworthy: anything the agent saves about the user is visible and correctable here, not a silent black box.
    """

    serializer_class = MemorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Memory.objects.filter(user=self.request.user)