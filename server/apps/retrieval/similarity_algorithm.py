"""
Manual vector similarity ranking - replaces reliance on Chroma's
internal ANN search ranking. Chroma is still used as storage (it holds
the vectors), but the actual "which stored vectors are closest to this
query" computation happens here, by hand, not inside the library.
"""

import heapq
import math


def cosine_similarity(vector_a: list[float], vector_b: list[float]) -> float:
    """
    cos(theta) = (A . B) / (|A| * |B|)

    Returns a value in [-1, 1] - 1 means identical direction (most
    similar), 0 means orthogonal (unrelated), -1 means opposite.
    Embedding vectors from a real model are essentially never negative
    (most sentence embedding models produce vectors that cluster in a
    fairly narrow cone), so in practice scores here land in roughly
    [0, 1], but the formula itself doesn't assume that.
    """
    if len(vector_a) != len(vector_b):
        raise ValueError(
            f"Vector dimension mismatch: {len(vector_a)} vs {len(vector_b)}"
        )

    dot_product = 0.0
    magnitude_a_sq = 0.0
    magnitude_b_sq = 0.0

    for a, b in zip(vector_a, vector_b):
        dot_product += a * b
        magnitude_a_sq += a * a
        magnitude_b_sq += b * b

    magnitude_a = math.sqrt(magnitude_a_sq)
    magnitude_b = math.sqrt(magnitude_b_sq)

    if magnitude_a == 0.0 or magnitude_b == 0.0:
        # A zero vector has no direction, so "similarity" to anything is
        # undefined - treat as no similarity rather than raising, since
        # this can legitimately happen with a degenerate embedding.
        return 0.0

    return dot_product / (magnitude_a * magnitude_b)


def top_k_by_similarity(
    query_vector: list[float],
    candidates: list[tuple[str, list[float]]],
    k: int,
) -> list[tuple[str, float]]:
    """
    Returns the k candidate ids with the highest cosine similarity to
    query_vector, sorted best-first.

    `candidates` is a list of (id, vector) pairs. Uses a size-k min-heap
    (heapq) rather than sorting the full candidate list and slicing the
    top k: sorting everything is O(n log n); maintaining a k-sized heap
    while scanning is O(n log k). For a workspace with far more stored
    chunks than k (the usual case - k is typically 3-6, n grows with
    every document/note/memory), this is the difference between "sort
    everything to throw most of it away" and "only ever hold k items in
    memory at once."
    """
    if k <= 0:
        return []

    heap: list[tuple[float, str]] = []  # (similarity, id) min-heap

    for candidate_id, vector in candidates:
        score = cosine_similarity(query_vector, vector)

        if len(heap) < k:
            heapq.heappush(heap, (score, candidate_id))
        elif score > heap[0][0]:
            # This candidate beats the current worst of our top-k -
            # evict the worst, insert this one. heapreplace does both
            # in one O(log k) operation instead of a separate pop+push.
            heapq.heapreplace(heap, (score, candidate_id))
        # else: score isn't good enough to make the top-k, skip it -
        # this is exactly what avoids ever sorting the full candidate set.

    # heap is in ascending order (min-heap) - reverse for best-first
    heap.sort(key=lambda item: item[0], reverse=True)
    return [(candidate_id, score) for score, candidate_id in heap]