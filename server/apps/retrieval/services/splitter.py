from django.conf import settings

from langchain_core.documents import Document as LCDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter

from apps.retrieval.services.content import get_source_type, get_title


CHUNK_SIZE = settings.CHUNK_SIZE
CHUNK_OVERLAP = settings.CHUNK_OVERLAP 


def split_into_chunks(obj, raw_docs: list[LCDocument]) -> list[LCDocument]:
    """
    Splits loaded page/whole-file text into overlapping chunks small enough to embed meaningfully. Each chunk is tagged with metadata (source_type, source_id, title, chunk_index) needed later to show source citations back to the user and for reconstructing vector-store ids on delete/re-index.

    Generic over `obj` (Document or Note) via content.py's helpers,
    rather than needing its own isinstance branch - splitting doesn't
    care what kind of content it's chunking, only loaders.py does.
    """

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )
    chunks = splitter.split_documents(raw_docs)

    source_type = get_source_type(obj)
    title = get_title(obj)

    for index, chunk in enumerate(chunks):
        chunk.metadata.update(    # chunks Inherits 'source' and 'page' metadata from the PDF loader
            {
                "source_type": source_type,
                "object_id": obj.pk,
                "title": title,
                "chunk_index": index,
            }
        )
    return chunks