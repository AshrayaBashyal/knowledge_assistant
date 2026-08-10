"""
Manual near-duplicate detection for remembered facts, using Jaccard
similarity over word-shingle sets. Closes a real gap flagged (and left
unsolved) back when the Memory app was first built: nothing previously
stopped the agent from saving "user is vegetarian" three times across
three different conversations.
"""

SHINGLE_SIZE = 2  # 2-word shingles - "user is vegetarian" -> {"user is", "is vegetarian"}
DEFAULT_THRESHOLD = 0.6


def _shingles(text: str, size: int = SHINGLE_SIZE) -> set[str]:
    """
    Breaks text into overlapping word n-grams ("shingles"). Single-word
    sets would call "user is vegetarian" and "vegetarian users unite"
    50%+ similar (they share 2 of 4 unique words) despite being
    unrelated claims; 2-word shingles require matching *phrases*, not
    just a bag of individual words, which is a meaningfully stricter and
    more accurate notion of "these two facts are saying the same thing."
    """
    words = text.lower().split()
    if len(words) < size:
        return {" ".join(words)} if words else set()
    return {" ".join(words[i : i + size]) for i in range(len(words) - size + 1)}


def jaccard_similarity(text_a: str, text_b: str) -> float:
    """
    J(A, B) = |A intersect B| / |A union B|

    1.0 means the two texts have identical shingle sets (near-certainly
    the same fact reworded), 0.0 means they share no phrases at all.
    """
    shingles_a = _shingles(text_a)
    shingles_b = _shingles(text_b)

    if not shingles_a and not shingles_b:
        return 1.0  # two empty strings are trivially "identical"
    if not shingles_a or not shingles_b:
        return 0.0

    intersection = shingles_a & shingles_b
    union = shingles_a | shingles_b
    return len(intersection) / len(union)


def find_near_duplicate(
    new_fact: str, existing_facts: list[tuple[int, str]], threshold: float = DEFAULT_THRESHOLD
):
    """
    Returns (id, similarity) for the most similar existing fact if it's
    at or above `threshold`, else None. `existing_facts` is a list of
    (id, content) pairs - the caller decides what "existing" means
    (e.g. scoped to one user).
    """
    best_match = None
    best_score = 0.0

    for fact_id, existing_text in existing_facts:
        score = jaccard_similarity(new_fact, existing_text)
        if score > best_score:
            best_score = score
            best_match = fact_id

    if best_match is not None and best_score >= threshold:
        return best_match, best_score
    return None