import os

from langchain_core.documents import Document as LCDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter

from documents.models import Document


CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1000))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 200))


def split_into_chunks(document: Document, raw_docs: list[LCDocument]) -> list[LCDocument]:
    """
    Splits loaded page/whole-file text into overlapping chunks small
    enough to embed meaningfully. Each chunk is tagged with metadata
    (document_id, document_title, chunk_index) needed later to show
    source citations back to the user.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )
    chunks = splitter.split_documents(raw_docs)

    for index, chunk in enumerate(chunks):
        chunk.metadata.update(    # chunks Inherits 'source' and 'page' metadata from the LCDocument
            {
                "document_id": document.id,
                "document_title": document.original_filename,
                "chunk_index": index,
            }
        )
    return chunks