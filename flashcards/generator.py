from pydantic import BaseModel, Field
from typing import Literal


class FlashcardItem(BaseModel):
    """
    Schema for one generated flashcard. Passed to the model via with_structured_output - the model is constrained to return data matching this shape, rather than free text we'd have to parse ourselves with regex/string-splitting and hope it stays consistent.
    """
 
    question: str = Field(description="A question testing understanding of one concept from the source")
    answer: str = Field(description="A concise, correct answer to the question")
    difficulty: Literal["easy", "medium", "hard"] = Field(description="How difficult this question is")
    category: str = Field(description="A short topic label for this card, e.g. 'syntax', 'history', 'definitions'")


class FlashcardBatch(BaseModel):
    """The full structured response shape: a list of flashcards."""
 
    flashcards: list[FlashcardItem]