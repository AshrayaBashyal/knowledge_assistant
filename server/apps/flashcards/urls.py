from django.urls import path

from apps.flashcards.views import (
    FlashcardDetailView,
    FlashcardSetDetailView,
    FlashcardSetListView,
    GenerateFlashcardsView,
)

app_name = "flashcards"

urlpatterns = [
    path("generate/", GenerateFlashcardsView.as_view(), name="generate"),
    path("sets/", FlashcardSetListView.as_view(), name="set-list"),
    path("sets/<int:pk>/", FlashcardSetDetailView.as_view(), name="set-detail"),
    path("<int:pk>/", FlashcardDetailView.as_view(), name="card-detail"),
]