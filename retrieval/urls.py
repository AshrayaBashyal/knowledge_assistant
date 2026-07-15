from django.urls import path

from retrieval.views import DocumentIndexView

app_name = "retrieval"

urlpatterns = [
    path("documents/<int:pk>/index/", DocumentIndexView.as_view(), name="document-index"),
]