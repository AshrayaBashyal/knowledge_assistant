from django.urls import path
from apps.analytics.views import AdminMetricsView, AdminLogsView

app_name = "analytics"

urlpatterns = [
    path("admin/metrics/", AdminMetricsView.as_view(), name="admin-metrics"),
    path("admin/logs/", AdminLogsView.as_view(), name="admin-logs"),
]
