from django.conf import settings
from django.db import models


class ApiMetric(models.Model):
    """
    Lightweight model recording API request metrics and tool invocations
    for admin dashboard metrics, latency charts, and error rates.
    """
    path = models.CharField(max_length=255, db_index=True)
    method = models.CharField(max_length=10)
    status_code = models.PositiveIntegerField(db_index=True)
    duration_ms = models.FloatField()
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="api_metrics",
    )
    tool_called = models.CharField(max_length=100, blank=True, default="", db_index=True)
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["created_at", "status_code"]),
        ]

    def __str__(self) -> str:
        return f"{self.method} {self.path} - {self.status_code} ({self.duration_ms}ms)"


class ToolInvocation(models.Model):
    """One tool execution completed during a streamed chat turn."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tool_invocations",
    )
    tool = models.CharField(max_length=100, db_index=True)
    duration_ms = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [models.Index(fields=["created_at", "tool"])]

    def __str__(self) -> str:
        return f"{self.tool} ({self.duration_ms}ms)"
