from django.urls import path

from search.views import WorkspaceSearchView

app_name = "search"

urlpatterns = [
    path("", WorkspaceSearchView.as_view(), name="workspace-search"),
]