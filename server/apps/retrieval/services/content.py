from django.contrib.contenttypes.models import ContentType


def get_source_type(obj) -> str:
    """
    Stable tag for what kind of content this is ("document", "note",
    ...), derived from Django's ContentType registry (the model's actual
    lowercased class name) rather than a hand-maintained string per
    isinstance check - it can't drift out of sync with the model itself.
    """
    return ContentType.objects.get_for_model(obj).model


def get_title(obj) -> str:
    """
    Human-readable label used in citations. Duck-typed rather than
    isinstance-based so this file doesn't need to import Document/Note at
    all - add a branch here only if a future content type exposes neither
    attribute.
    """
    if hasattr(obj, "original_filename"):
        return obj.original_filename
    return getattr(obj, "title", str(obj))