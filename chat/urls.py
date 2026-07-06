from django.urls import path

from chat.views import ChatStreamView, ConversationDetailView, ConversationListCreateView

app_name = "chat"

urlpatterns = [
    path("stream/", ChatStreamView.as_view(), name="stream"),
    path("conversations/", ConversationListCreateView.as_view(), name="conversation-list"),
    path("conversations/<int:pk>/", ConversationDetailView.as_view(), name="conversation-detail"),
]