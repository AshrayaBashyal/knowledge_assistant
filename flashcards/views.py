from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions

from flashcards.models import Flashcard, FlashcardSet
from flashcards.serializers import (
    FlashcardSerializer,
    FlashcardSetDetailSerializer,
    FlashcardSetSerializer,
    GenerateFlashcardsInputSerializer,
)


@extend_schema(tags=["flashcards"])
class FlashcardSetListView(generics.ListAPIView):
    """list the user's flashcard sets (newest first)."""

    serializer_class = FlashcardSetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FlashcardSet.objects.filter(user=self.request.user)


@extend_schema(tags=["flashcards"])
class FlashcardSetDetailView(generics.RetrieveDestroyAPIView):
    """
    GET -> one set with all its cards
    DELETE -> delete the whole set (cards cascade)
    """

    serializer_class = FlashcardSetDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FlashcardSet.objects.filter(user=self.request.user)


@extend_schema(tags=["flashcards"])
class FlashcardDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET -> one card
    PATCH -> edit a card (question/answer/difficulty/category)
    DELETE -> delete a single card from its set
    """

    serializer_class = FlashcardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Flashcard.objects.filter(flashcard_set__user=self.request.user)