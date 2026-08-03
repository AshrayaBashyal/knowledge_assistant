from django.urls import path

from apps.notes.views import NoteDetailView, NoteListCreateView

app_name = "notes"

urlpatterns = [
    path("", NoteListCreateView.as_view(), name="note-list"),
    path("<int:pk>/", NoteDetailView.as_view(), name="note-detail"),
]