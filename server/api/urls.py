from django.urls import include, path
from core.views import health_check

urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("accounts/", include("apps.accounts.urls")),
    path("chat/", include("apps.chat.urls")),
    path("documents/", include("apps.documents.urls")),
    path("flashcards/", include("apps.flashcards.urls")),
    path("memory/", include("apps.memory.urls")),
    path("notes/", include("apps.notes.urls")),
    path("retrieval/", include("apps.retrieval.urls")),
    path("search/", include("apps.search.urls")),
    path("", include("apps.analytics.urls")),
]
