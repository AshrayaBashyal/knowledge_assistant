from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
 
from documents.models import Document
from flashcards.generator import generate_flashcards
from flashcards.models import Flashcard, FlashcardSet
from flashcards.serializers import (
    FlashcardSerializer,
    FlashcardSetDetailSerializer,
    FlashcardSetSerializer,
    GenerateFlashcardsInputSerializer,
)
from notes.models import Note
from retrieval.content import get_title


SOURCE_MODEL = {"document": Document, "note": Note}


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
    

class GenerateFlashcardsView(APIView):
    """
    POST /api/flashcards/generate/
    body: {"source_type": "document"|"note", "source_id": <int>, "count": <int, optional, default 10, max 30>}
 
    Generates flashcards from a document or note's content and persists them as a new FlashcardSet. Runs synchronously -  Celery task later makes it not blocking
    """
 
    permission_classes = [permissions.IsAuthenticated]
 
    @extend_schema(
        tags=["flashcards"],
        request=GenerateFlashcardsInputSerializer,
        responses={201: FlashcardSetDetailSerializer},
    )
    def post(self, request: Request) -> Response:
        serializer = GenerateFlashcardsInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
 
        model_class = SOURCE_MODELS[data["source_type"]]
        obj = get_object_or_404(model_class, pk=data["source_id"], user=request.user)
 
        items = generate_flashcards(obj, count=data["count"])
 
        flashcard_set = FlashcardSet.objects.create(
            user=request.user,
            content_type=ContentType.objects.get_for_model(obj),
            object_id=obj.pk,
            source_title=get_title(obj),
        )
        Flashcard.objects.bulk_create(
            Flashcard(
                flashcard_set=flashcard_set,
                question=item.question,
                answer=item.answer,
                difficulty=item.difficulty,
                category=item.category,
            )
            for item in items
        )
 
        result_serializer = FlashcardSetDetailSerializer(flashcard_set)
        return Response(result_serializer.data, status=status.HTTP_201_CREATED)
