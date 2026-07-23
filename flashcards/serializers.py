from rest_framework import serializers

from flashcards.models import Flashcard, FlashcardSet


class FlashcardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flashcard
        fields = ["id", "question", "answer", "difficulty", "category"]
        read_only_fields = ["id"]


class FlashcardSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlashcardSet
        fields = ["id", "source_title", "created_at"]
        read_only_fields = fields


class FlashcardSetDetailSerializer(FlashcardSetSerializer):
    flashcards = FlashcardSerializer(many=True, read_only=True)

    class Meta:
        fields = FlashcardSetSerializer.Meta.fields + ["flashcards"]