from pathlib import Path
from langchain_core.documents import Document as LCDocument

from apps.documents.models import Document
from apps.notes.models import Note


def load_content_text(obj) -> list[LCDocument]:
    """
    Converts the content's text into one or more LangChain Documents.

    - PDFs are loaded page-by-page using pypdf directly from the file stream.
      This supports both local storage and remote cloud storage (Cloudinary, Supabase S3)
      without requiring absolute local filesystem paths (obj.file.path).
    - Markdown / Text files are read from the file stream.
    - Notes, Memories, and other text models are duck-typed on `.content`.
    """
    if isinstance(obj, Document):
        if obj.file_type == Document.FileType.PDF:
            import pypdf

            docs = []
            with obj.file.open("rb") as f:
                reader = pypdf.PdfReader(f)
                for page_num, page in enumerate(reader.pages):
                    text = page.extract_text() or ""
                    metadata = {
                        "source": obj.original_filename,
                        "page": page_num,
                    }
                    docs.append(LCDocument(page_content=text, metadata=metadata))
            return docs

        with obj.file.open("rb") as f:
            raw_bytes = f.read()
            text = raw_bytes.decode("utf-8", errors="ignore")
            return [
                LCDocument(
                    page_content=text,
                    metadata={"source": obj.original_filename},
                )
            ]

    if hasattr(obj, "content"):
        return [LCDocument(page_content=obj.content, metadata={})]

    raise TypeError(f"Don't know how to load content for {type(obj)}")
