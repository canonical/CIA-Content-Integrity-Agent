"""
Shared URL similarity utilities for Jaccard-based URL matching.
"""
from urllib.parse import urlparse


def get_path_segments(url: str) -> set:
    """Extract path segments from a URL, splitting on '/' and '-'."""
    parsed = urlparse(url)
    path = parsed.path.strip("/")
    if not path:
        return set()
    segments = []
    for part in path.split("/"):
        segments.extend(part.split("-"))
    return set(segments)


def jaccard_similarity(set1: set, set2: set) -> float:
    """Compute Jaccard similarity between two sets."""
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0
