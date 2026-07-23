from rest_framework import serializers

from flashcards.models import Flashcard, FlashcardSet


class FlashcardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flashcard
        fields = ["id", "question", "answer", "difficulty", "category"]
        read_only_fields = ["id"]


class FlashcardSetSerializer(serializers.ModelSerializer):
    """List shape - no cards, just the set metadata."""

    class Meta:
        model = FlashcardSet
        fields = ["id", "source_title", "created_at"]
        read_only_fields = fields


class FlashcardSetDetailSerializer(FlashcardSetSerializer):
    """Detail shape - includes the full generated card list."""

    flashcards = FlashcardSerializer(many=True, read_only=True)

    class Meta(FlashcardSetSerializer.Meta):
        fields = FlashcardSetSerializer.Meta.fields + ["flashcards"]


class GenerateFlashcardsInputSerializer(serializers.Serializer):
    source_type = serializers.ChoiceField(choices=["document", "note"])
    source_id = serializers.IntegerField()
    count = serializers.IntegerField(default=10, min_value=1, max_value=30)