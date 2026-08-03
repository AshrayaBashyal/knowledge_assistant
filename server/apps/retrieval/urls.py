from django.urls import path

from apps.retrieval.views import DocumentIndexView, NoteIndexView

app_name = "retrieval"

urlpatterns = [
    path("documents/<int:pk>/index/", DocumentIndexView.as_view(), name="document-index"),
    path("notes/<int:pk>/index/", NoteIndexView.as_view(), name="note-index"),
]