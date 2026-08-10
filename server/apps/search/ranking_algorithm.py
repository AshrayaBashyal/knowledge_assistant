"""
Manual BM25 ranking - replaces reliance on Postgres's SearchRank/
SearchVector for Workspace Search's relevance scoring. Postgres full-
text search (to_tsvector/to_tsquery) is no longer used at all for
ranking; this module tokenizes and scores candidate rows in Python
instead.

BM25 (Okapi BM25) is TF-IDF's more careful sibling: it adds document-
length normalization (a term hitting once in a 5-word note should count
for more than the same term hitting once in a 500-word document) and
term-frequency saturation (the 10th occurrence of a word matters much
less than the 2nd - repeating a word doesn't linearly keep improving
relevance).
"""

import math
import re

# Standard BM25 tuning constants (the values used in Okapi BM25 itself
# and most reference implementations) - k1 controls how quickly term-
# frequency saturates, b controls how strongly document length is
# penalized (0 = no length normalization, 1 = full normalization).
K1 = 1.5
B = 0.75

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    """Lowercase, alphanumeric-only tokenization. No stemming (e.g.
    "running" stays "running", doesn't reduce to "run") - keeping this
    simple rather than pulling in a stemming library is a deliberate
    scope choice, not an oversight; it means exact word matches only."""
    return _TOKEN_PATTERN.findall(text.lower())


def _idf(term: str, term_doc_counts: dict[str, int], total_docs: int) -> float:
    """
    IDF(t) = ln( (N - n(t) + 0.5) / (n(t) + 0.5) + 1 )

    N = total documents in the corpus, n(t) = how many of them contain
    term t. A term appearing in almost every document (low information
    value, e.g. "the") gets a low/near-zero IDF; a rare term gets a high
    one. The "+1" inside the log (the BM25+ convention) keeps IDF from
    ever going negative for very common terms, unlike classic BM25.
    """
    doc_count = term_doc_counts.get(term, 0)
    return math.log((total_docs - doc_count + 0.5) / (doc_count + 0.5) + 1)


def rank_by_bm25(
    query: str, documents: list[tuple[str, str]]
) -> list[tuple[str, float]]:
    """
    Ranks `documents` (a list of (id, text) pairs) by BM25 relevance to
    `query`. Returns (id, score) pairs sorted best-first; a score of 0.0
    means no query terms matched at all.

    The whole corpus (avgdl, IDF) is computed from `documents` itself -
    BM25 is inherently corpus-relative (a term's rarity only means
    something relative to a specific set of documents), which is why
    this takes the full candidate list rather than scoring one document
    against a query in isolation.
    """
    query_terms = tokenize(query)
    if not query_terms or not documents:
        return []

    tokenized_docs = [(doc_id, tokenize(text)) for doc_id, text in documents]
    doc_lengths = {doc_id: len(tokens) for doc_id, tokens in tokenized_docs}
    total_docs = len(tokenized_docs)
    avg_doc_length = sum(doc_lengths.values()) / total_docs if total_docs else 0

    # How many documents contain each query term at least once - the
    # n(t) in the IDF formula above.
    term_doc_counts: dict[str, int] = {}
    for term in set(query_terms):
        term_doc_counts[term] = sum(
            1 for _doc_id, tokens in tokenized_docs if term in tokens
        )

    scored = []
    for doc_id, tokens in tokenized_docs:
        doc_length = doc_lengths[doc_id]
        score = 0.0

        for term in query_terms:
            term_frequency = tokens.count(term)
            if term_frequency == 0:
                continue

            idf = _idf(term, term_doc_counts, total_docs)
            length_norm = 1 - B + B * (doc_length / avg_doc_length if avg_doc_length else 0)
            numerator = term_frequency * (K1 + 1)
            denominator = term_frequency + K1 * length_norm

            score += idf * (numerator / denominator)

        scored.append((doc_id, score))

    scored.sort(key=lambda item: item[1], reverse=True)
    return scored