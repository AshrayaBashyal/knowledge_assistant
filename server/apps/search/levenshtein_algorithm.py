"""
Manual Levenshtein (edit) distance - used as a fuzzy-matching fallback
for Workspace Search. BM25 (search/ranking.py) requires exact word
matches; if it finds nothing at all for a query, that's often just a
typo ("buget" instead of "budget"), not genuinely irrelevant content.
This module finds the closest word actually present in the user's own
content and retries the search with it, rather than returning a
silent, unexplained empty result.
"""


def levenshtein_distance(a: str, b: str) -> int:
    """
    Minimum number of single-character insertions, deletions, or
    substitutions needed to turn `a` into `b`.

    Classic dynamic-programming formulation: dp[i][j] holds the edit
    distance between the first i characters of a and the first j
    characters of b. Only the previous row is ever needed to compute the
    current one, so this keeps O(min(len(a), len(b))) space rather than
    the full O(len(a) * len(b)) table most textbook versions use.
    """
    if a == b:
        return 0

    len_a, len_b = len(a), len(b)
    if len_a == 0:
        return len_b
    if len_b == 0:
        return len_a

    # Iterate over the shorter string for the row we keep in memory,
    # so the space bound above actually holds regardless of which
    # argument is longer.
    if len_a > len_b:
        a, b = b, a
        len_a, len_b = len_b, len_a

    previous_row = list(range(len_a + 1))

    for j in range(1, len_b + 1):
        current_row = [j] + [0] * len_a
        for i in range(1, len_a + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            current_row[i] = min(
                previous_row[i] + 1,  # deletion
                current_row[i - 1] + 1,  # insertion
                previous_row[i - 1] + cost,  # substitution
            )
        previous_row = current_row

    return previous_row[len_a]


def find_closest_word(
    word: str, vocabulary: set[str], max_distance: int = 2
) -> str | None:
    """
    Returns the vocabulary word with the smallest edit distance to
    `word`, if that distance is at or within max_distance - else None.
    max_distance=2 catches typical typos (one substitution + one
    transposition-like slip) without matching genuinely different words.
    """
    best_word = None
    best_distance = max_distance + 1

    for candidate in vocabulary:
        distance = levenshtein_distance(word, candidate)
        if distance < best_distance:
            best_distance = distance
            best_word = candidate

    if best_word is not None and best_distance <= max_distance:
        return best_word
    return None