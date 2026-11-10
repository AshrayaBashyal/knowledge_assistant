from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from ai.llm.providers import get_chat_model
from apps.retrieval.services.loaders import load_content_text

MAX_SOURCE_CHARS = 6000


class FlashcardItem(BaseModel):
    """
    Schema for one generated flashcard.
    """
    question: str = Field(description="A question testing understanding of one concept from the source")
    answer: str = Field(description="A concise, correct answer to the question")
    difficulty: Literal["easy", "medium", "hard"] = Field(description="How difficult this question is")
    category: str = Field(description="A short topic label for this card, e.g. 'syntax', 'history', 'definitions'")


class FlashcardBatch(BaseModel):
    """The full structured response shape: a list of flashcards."""
    flashcards: list[FlashcardItem]


def generate_flashcards(obj, count: int) -> list[FlashcardItem]:
    """
    Generates up to `count` flashcards from a Document or Note's content.
    Reuses the user's configured model/API key if set.
    """
    raw_docs = load_content_text(obj)
    text = "\n\n".join(doc.page_content for doc in raw_docs)[:MAX_SOURCE_CHARS]

    if not text.strip():
        return []

    user = getattr(obj, "user", None)
    model = get_chat_model(user=user, streaming=False).with_structured_output(FlashcardBatch)

    messages = [
        SystemMessage(
            content=(
                "You create study flashcards from source material. Generate "
                f"exactly {count} flashcards covering the most important "
                "concepts in the source. Each flashcard needs a clear "
                "question, a concise answer, a difficulty (easy/medium/"
                "hard), and a short category label."
            )
        ),
        HumanMessage(content=f"Source material:\n\n{text}"),
    ]

    result: FlashcardBatch = model.invoke(messages)
    return result.flashcards[:count]
