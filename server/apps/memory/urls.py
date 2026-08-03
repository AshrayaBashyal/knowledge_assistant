from django.urls import path

from apps.memory.views import MemoryDetailView, MemoryListCreateView

app_name = "memory"

urlpatterns = [
    path("", MemoryListCreateView.as_view(), name="memory-list"),
    path("<int:pk>/", MemoryDetailView.as_view(), name="memory-detail"),
]