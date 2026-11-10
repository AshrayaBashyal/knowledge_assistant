import json
import logging
from datetime import timedelta
from pathlib import Path
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, Sum, Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.analytics.models import ApiMetric
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
        seven_days_ago = now - timedelta(days=7)

        # 1. High level KPIs
        total_users = User.objects.count()
        total_docs = Document.objects.count()
        total_notes = Note.objects.count()
        total_flashcard_sets = FlashcardSet.objects.count()
        total_flashcards = Flashcard.objects.count()
        total_memories = Memory.objects.count()
        total_conversations = Conversation.objects.count()
        total_messages = Message.objects.count()

        # Content index stats
        index_stats = ContentIndex.objects.aggregate(
            total_chunks=Sum("chunk_count"),
            completed_count=Count("id", filter=Q(status=ContentIndex.Status.COMPLETED) if hasattr(ContentIndex, 'Status') else Q()),
        )
        total_chunks = index_stats.get("total_chunks") or 0

        # API Request & Latency metrics from ApiMetric
        metrics_qs = ApiMetric.objects.all()
        total_requests = metrics_qs.count()
        avg_latency = metrics_qs.aggregate(avg=Avg("duration_ms"))["avg"] or 0
        error_count = metrics_qs.filter(status_code__gte=400).count()
        error_rate = round((error_count / total_requests * 100), 2) if total_requests > 0 else 0.0

        # 2. Activity Chart (Last 7 Days)
        activity_days = []
        for i in range(6, -1, -1):
            day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            date_label = day_start.strftime("%b %d")

            day_requests = ApiMetric.objects.filter(created_at__gte=day_start, created_at__lt=day_end).count()
            day_messages = Message.objects.filter(created_at__gte=day_start, created_at__lt=day_end).count()
            day_docs = Document.objects.filter(created_at__gte=day_start, created_at__lt=day_end).count()

            activity_days.append({
                "date": date_label,
                "requests": day_requests,
                "messages": day_messages,
                "documents": day_docs,
            })

        # 3. Tool Usage Breakdown
        tool_counts_qs = (
            ApiMetric.objects.exclude(tool_called="")
            .values("tool_called")
            .annotate(count=Count("id"))
            .order_by("-count")[:8]
        )
        tool_distribution = [
            {"tool": item["tool_called"], "count": item["count"]}
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

        # 5. Status code distribution (2xx, 4xx, 5xx)
        success_2xx = metrics_qs.filter(status_code__gte=200, status_code__lt=300).count()
        client_err_4xx = metrics_qs.filter(status_code__gte=400, status_code__lt=500).count()
        server_err_5xx = metrics_qs.filter(status_code__gte=500).count()

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
                "total_api_requests": total_requests,
                "avg_latency_ms": round(avg_latency, 1),
                "error_rate_percent": error_rate,
                "vector_db": "Pinecone" if settings.PINECONE_API_KEY else "ChromaDB",
                "embedding_provider": getattr(settings, "EMBEDDING_PROVIDER", "gemini"),
            },
            "activity_chart": activity_days,
            "tool_distribution": tool_distribution,
            "latency_breakdown": latency_breakdown,
            "status_distribution": {
                "2xx": success_2xx,
                "4xx": client_err_4xx,
                "5xx": server_err_5xx,
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
