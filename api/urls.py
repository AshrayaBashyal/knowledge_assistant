from django.urls import include, path

urlpatterns = [
    path("accounts/", include("accounts.urls")),
    path("chat/", include("chat.urls")),
    path("documents/", include("documents.urls")),
    path("retrieval/", include("retrieval.urls")),
    path("notes/", include("notes.urls"))
]