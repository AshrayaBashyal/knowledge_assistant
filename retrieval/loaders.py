from pathlib import Path

from langchain_core.documents import Document as LCDocument

from documents.models import Document
from notes.models import Note


def load_content_text(obj) -> list[LCDocument]:
    """
    Converts the content's text into one or more LangChain Documents.

    Heads up: this is the only spot in `retrieval` where we explicitly check the concrete model type (using isinstance instead of duck typing). Unlike the naming helpers in content.py, the actual text extraction logic is completely different here. A Document points to an actual file on disk with specific parsing rules (like page-by-page loading for PDFs), while a Note is just a text field already sitting in memory. Since the underlying mechanics are fundamentally different, it makes sense to use explicit code branches.

    PDFs are loaded page-by-page via LangChain's PyPDFLoader, so each resulting chunk can later cite a page number. Markdown/TXT don't have an equivalent page boundary, so they're loaded as a single Document and rely on chunk_index (added during splitting) for citations instead.
    """

    if isinstance(obj, Document):
        if obj.file_type == Document.FileType.PDF:
            from langchain_community.document_loaders import PyPDFLoader
 
            return PyPDFLoader(obj.file.path).load()
 
        text = Path(obj.file.path).read_text(encoding="utf-8", errors="ignore")
        return [LCDocument(page_content=text, metadata={})]

    if isinstance(obj, Note):
        return [LCDocument(page_content=obj.content, metadata={})]
 
    raise TypeError(f"Don't know how to load content for {type(obj)}")





# since langchain_comunity import is heavy we can just use pypdf only instead:

# -- IMPLEMENTATION READY CODE JUST REPLACE IF NEEDED --

# def load_document_text(document: Document) -> list[LCDocument]:
#     """
#     Returns the document's content as one or more LangChain Documents.

#     PDFs are loaded page-by-page via pypdf to avoid heavy community imports, 
#     ensuring each resulting chunk can later cite a page number. Markdown/TXT 
#     are loaded as a single Document.
#     """
#     path = document.file.path

#     if document.file_type == Document.FileType.PDF:
#         import pypdf

#         docs = []
#         reader = pypdf.PdfReader(path)
        
#         for page_num, page in enumerate(reader.pages):
#             text = page.extract_text() or ""
#             # Matches the exact metadata schema used by LangChain's PyPDFLoader
#             metadata = {"source": path, "page": page_num}
#             docs.append(LCDocument(page_content=text, metadata=metadata))
            
#         return docs

#     text = Path(path).read_text(encoding="utf-8", errors="ignore")
#     return [LCDocument(page_content=text, metadata={"source": path})]