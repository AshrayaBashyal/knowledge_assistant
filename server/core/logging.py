import functools
import json
import logging
import time

# Every attribute a plain LogRecord has by default - used to separate "real" log record internals from the extra structured fields a caller passed in via logger.info(..., extra={...}).
_RESERVED_RECORD_KEYS = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__.keys())


class JSONFormatter(logging.Formatter):
    """
    Formats each log record as one line of JSON. This is what makes
    logging "structured" rather than free-text: any extra fields passed
    via `logger.info("message", extra={"tool": "calculator", ...})`
    appear as real JSON fields, so logs can be grepped/parsed/shipped to
    a log aggregator without regex, instead of scanning formatted
    strings like "tool=calculator duration=12ms" by hand.
    """

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        for key, value in record.__dict__.items():
            if key not in _RESERVED_RECORD_KEYS and key != "message":
                payload[key] = value

        return json.dumps(payload, default=str)


def log_call(logger_name: str):
    """
    Decorator that logs one structured entry per call to the wrapped
    function: its name, duration in ms, and whether it raised.

    Used to instrument tool calls (calculator, retrieval, memory, web
    search) without duplicating timing/try-except boilerplate in every
    one of them - each tool just gets one line added, and the actual
    tool logic stays unchanged.

    Applied *underneath* @tool (i.e. written above it, since decorators
    apply bottom-up), not the other way around - LangChain's @tool needs
    to introspect the final callable's signature and docstring, and
    functools.wraps preserves both (Python's inspect.signature() follows
    the __wrapped__ attribute wraps() sets), so @tool still sees the
    original function's shape correctly.
    """

    def decorator(func):
        logger = logging.getLogger(logger_name)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.monotonic()
            try:
                result = func(*args, **kwargs)
                duration_ms = round((time.monotonic() - start) * 1000, 2)
                logger.info(
                    "tool_call",
                    extra={
                        "tool": func.__name__,
                        "duration_ms": duration_ms,
                        "outcome": "ok",
                    },
                )
                return result
            except Exception:
                duration_ms = round((time.monotonic() - start) * 1000, 2)
                logger.exception(
                    "tool_call_failed",
                    extra={
                        "tool": func.__name__,
                        "duration_ms": duration_ms,
                        "outcome": "error",
                    },
                )
                raise

        return wrapper

    return decorator