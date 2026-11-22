from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import User
from apps.analytics.models import ApiMetric, ToolInvocation
from apps.analytics.views import AdminMetricsView
from apps.retrieval.models import ContentIndex


class AdminMetricsViewTests(TestCase):
    def test_metrics_use_valid_index_status_and_count_all_http_classes(self):
        admin = User.objects.create_user(
            email="metrics-admin@example.com",
            password="test-password",
            is_staff=True,
        )
        content_type = ContentType.objects.get_for_model(User)
        ContentIndex.objects.create(
            content_type=content_type,
            object_id=admin.pk,
            status=ContentIndex.Status.INDEXED,
            chunk_count=7,
        )
        ContentIndex.objects.create(
            content_type=content_type,
            object_id=admin.pk + 100,
            status=ContentIndex.Status.FAILED,
            chunk_count=3,
        )
        ApiMetric.objects.bulk_create(
            [
                ApiMetric(path="/api/test/", method="GET", status_code=200, duration_ms=10),
                ApiMetric(path="/api/test/", method="GET", status_code=302, duration_ms=20),
                ApiMetric(path="/api/test/", method="GET", status_code=404, duration_ms=30),
                ApiMetric(path="/api/test/", method="GET", status_code=500, duration_ms=40),
            ]
        )
        ToolInvocation.objects.create(user=admin, tool="calculator", duration_ms=12)
        ToolInvocation.objects.create(user=admin, tool="calculator", duration_ms=8)

        request = APIRequestFactory().get("/api/admin/metrics/")
        force_authenticate(request, user=admin)
        response = AdminMetricsView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["kpis"]["total_indexed_chunks"], 7)
        self.assertEqual(response.data["kpis"]["total_indexed_items"], 1)
        self.assertEqual(
            response.data["status_distribution"],
            {"2xx": 1, "3xx": 1, "4xx": 1, "5xx": 1},
        )
        self.assertEqual(response.data["kpis"]["error_rate_percent"], 50.0)
        self.assertEqual(
            response.data["tool_distribution"],
            [{"tool": "calculator", "count": 2}],
        )
