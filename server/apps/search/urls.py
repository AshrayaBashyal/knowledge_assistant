from django.urls import path

from apps.search.views import WorkspaceSearchView

app_name = "search"

urlpatterns = [
    path("", WorkspaceSearchView.as_view(), name="workspace-search"),
]