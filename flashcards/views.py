from rest_framework import generics, permissions, status

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from documents.models import Document
from notes.models import Note

from flashcards.serializers import FlashcardSerializer, FlashcardSetSerializer, FlashcardSetDetailSerializer, GenerateFlashcardsInputSerializer
from flashcards.models import Flashcard, FlashcardSet


class FlashcardSetListView(generics.ListAPIView):

    serializer_class = [FlashcardSetSerializer]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FlashcardSet.objects.filter(user=self.request.user)
    

class FlashcardSetDetailView(generics.RetrieveDestroyAPIView):
 
    serializer_class = FlashcardSetDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
 
    def get_queryset(self):
        return FlashcardSet.objects.filter(user=self.request.user)
    

