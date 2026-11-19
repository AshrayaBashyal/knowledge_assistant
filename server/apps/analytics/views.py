import json
import logging
import os
from datetime import timedelta
from pathlib import Path
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connection
from django.db.models import Avg, Count, Sum, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.analytics.models import ApiMetric, ToolInvocation
from apps.chat.models import Conversation, Message
from apps.documents.models import Document
from apps.flashcards.models import Flashcard, FlashcardSet
from apps.memory.models import Memory
from apps.notes.models import Note
from apps.retrieval.models import ContentIndex

User = get_user_model()
logger = logging.getLogger("apps.analytics")


@extend_schema(tags=["admin"])
class AdminMetricsView(APIView):
    """
    Returns aggregated metrics, KPI cards, activity trends, latency percentiles,
    and tool usage distribution for the Admin Dashboard.
    Restricted to staff users (is_staff=True).
    """
    permission_classes = [permissions.IsAdminUser]

    def get(self, request: Request) -> Response:
        now = timezone.now()
        # 1. High level KPIs
        total_users = User.objects.filter(is_active=True).count()
        total_docs = Document.objects.count()
        total_notes = Note.objects.count()
        total_flashcard_sets = FlashcardSet.objects.count()
        total_flashcards = Flashcard.objects.count()
        total_memories = Memory.objects.count()
        total_conversations = Conversation.objects.count()
        total_messages = Message.objects.count()

        # Content index stats
        index_stats = ContentIndex.objects.aggregate(
            total_chunks=Sum(
                "chunk_count", filter=Q(status=ContentIndex.Status.INDEXED)
            ),
            indexed_count=Count(
                "id", filter=Q(status=ContentIndex.Status.INDEXED)
            ),
        )
        total_chunks = index_stats.get("total_chunks") or 0

        # API Request & Latency metrics from ApiMetric
        metrics_qs = ApiMetric.objects.all()
        metric_summary = metrics_qs.aggregate(
            total=Count("id"),
            avg_latency=Avg("duration_ms"),
            errors=Count("id", filter=Q(status_code__gte=400)),
            success_2xx=Count(
                "id", filter=Q(status_code__gte=200, status_code__lt=300)
            ),
            redirect_3xx=Count(
                "id", filter=Q(status_code__gte=300, status_code__lt=400)
            ),
            client_err_4xx=Count(
                "id", filter=Q(status_code__gte=400, status_code__lt=500)
            ),
            server_err_5xx=Count("id", filter=Q(status_code__gte=500)),
        )
        total_requests = metric_summary["total"]
        avg_latency = metric_summary["avg_latency"] or 0
        error_count = metric_summary["errors"]
        error_rate = round((error_count / total_requests * 100), 2) if total_requests > 0 else 0.0

        # 2. Activity Chart (Last 7 Days)
        activity_start = (now - timedelta(days=6)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        request_counts = {
            item["day"]: item["count"]
            for item in metrics_qs.filter(created_at__gte=activity_start)
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(count=Count("id"))
        }
        message_counts = {
            item["day"]: item["count"]
            for item in Message.objects.filter(created_at__gte=activity_start)
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(count=Count("id"))
        }
        document_counts = {
            item["day"]: item["count"]
            for item in Document.objects.filter(uploaded_at__gte=activity_start)
            .annotate(day=TruncDate("uploaded_at"))
            .values("day")
            .annotate(count=Count("id"))
        }
        activity_days = []
        for i in range(6, -1, -1):
            day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
            day = day_start.date()
            date_label = day_start.strftime("%b %d")

            activity_days.append({
                "date": date_label,
                "requests": request_counts.get(day, 0),
                "messages": message_counts.get(day, 0),
                "documents": document_counts.get(day, 0),
            })

        # 3. Tool Usage Breakdown
        tool_counts_qs = (
            ToolInvocation.objects.values("tool")
            .annotate(count=Count("id"))
            .order_by("-count")[:8]
        )
        tool_distribution = [
            {"tool": item["tool"], "count": item["count"]}
            for item in tool_counts_qs
        ]
        # Add default tool references if empty to show schema in dashboard
        if not tool_distribution:
            tool_distribution = [
                {"tool": "search_my_knowledge", "count": 0},
                {"tool": "calculator", "count": 0},
                {"tool": "tavily_search", "count": 0},
                {"tool": "current_time", "count": 0},
            ]

        # 4. Latency by top endpoints
        endpoint_latencies = (
            ApiMetric.objects.values("path")
            .annotate(avg_ms=Avg("duration_ms"), count=Count("id"))
            .order_by("-count")[:6]
        )
        latency_breakdown = [
            {
                "path": item["path"],
                "avg_ms": round(item["avg_ms"] or 0, 1),
                "count": item["count"],
            }
            for item in endpoint_latencies
        ]

        # 5. Status code distribution
        vector_provider = settings.VECTOR_STORE_PROVIDER
        if not vector_provider:
            if settings.PINECONE_API_KEY:
                vector_provider = "pinecone"
            elif os.getenv("QDRANT_URL") and os.getenv("QDRANT_API_KEY"):
                vector_provider = "qdrant"
            else:
                vector_provider = "chroma"
        database_name = {
            "postgresql": "PostgreSQL",
            "sqlite": "SQLite",
        }.get(connection.vendor, connection.vendor)

        return Response({
            "kpis": {
                "total_users": total_users,
                "total_documents": total_docs,
                "total_notes": total_notes,
                "total_flashcard_sets": total_flashcard_sets,
                "total_flashcards": total_flashcards,
                "total_memories": total_memories,
                "total_conversations": total_conversations,
                "total_messages": total_messages,
                "total_indexed_chunks": total_chunks,
                "total_indexed_items": index_stats["indexed_count"],
                "total_api_requests": total_requests,
                "avg_latency_ms": round(avg_latency, 1),
                "error_rate_percent": error_rate,
                "vector_db": vector_provider.title() if vector_provider != "chroma" else "ChromaDB",
                "embedding_provider": settings.EMBEDDING_PROVIDER,
                "embedding_model": (
                    settings.GEMINI_EMBEDDING_MODEL
                    if settings.EMBEDDING_PROVIDER == "gemini"
                    else settings.EMBEDDING_MODEL
                ),
                "background_tasks": (
                    "Inline (blocking)"
                    if settings.CELERY_TASK_ALWAYS_EAGER
                    else "Redis queue"
                ),
                "database": database_name,
            },
            "activity_chart": activity_days,
            "tool_distribution": tool_distribution,
            "latency_breakdown": latency_breakdown,
            "status_distribution": {
                "2xx": metric_summary["success_2xx"],
                "3xx": metric_summary["redirect_3xx"],
                "4xx": metric_summary["client_err_4xx"],
                "5xx": metric_summary["server_err_5xx"],
            },
        })


@extend_schema(tags=["admin"])
class AdminLogsView(APIView):
    """
    Returns structured system and API logs with level filtering and search.
    Reads from server/logs/app.log and DB error metrics.
    Restricted to staff users (is_staff=True).
    """
    permission_classes = [permissions.IsAdminUser]

    def get(self, request: Request) -> Response:
        level_filter = request.query_params.get("level", "").upper().strip()
        search_query = request.query_params.get("search", "").lower().strip()
        limit = min(int(request.query_params.get("limit", 100)), 300)

        logs_list = []
        log_file_path = getattr(settings, "BASE_DIR", Path(".")) / "logs" / "app.log"

        if log_file_path.exists():
            try:
                # Read last lines of app.log
                with open(log_file_path, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()

                for line in reversed(lines):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        record = {
                            "timestamp": "",
                            "level": "INFO",
                            "logger": "raw",
                            "message": line,
                        }

                    rec_level = record.get("level", "INFO").upper()
                    if level_filter and rec_level != level_filter:
                        continue

                    rec_msg = str(record.get("message", "")).lower()
                    rec_logger = str(record.get("logger", "")).lower()
                    if search_query and (search_query not in rec_msg and search_query not in rec_logger):
                        continue

                    logs_list.append(record)
                    if len(logs_list) >= limit:
                        break
            except Exception as e:
                logger.error("Error reading log file: %s", e)

        # Fallback to recent ApiMetrics if logs list is empty
        if not logs_list:
            recent_metrics = ApiMetric.objects.order_by("-created_at")[:limit]
            for m in recent_metrics:
                logs_list.append({
                    "timestamp": m.created_at.isoformat(),
                    "level": "ERROR" if m.status_code >= 400 else "INFO",
                    "logger": "core.request",
                    "message": f"{m.method} {m.path} -> {m.status_code}",
                    "duration_ms": m.duration_ms,
                    "status_code": m.status_code,
                    "user_id": m.user_id,
                    "tool": m.tool_called,
                    "error": m.error_message,
                })

        return Response({
            "count": len(logs_list),
            "logs": logs_list,
        })
