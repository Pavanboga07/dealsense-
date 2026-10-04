"""Live product search via SerpApi.

Uses the official SerpApi Python client against the Google Shopping engine.
Every call hits SerpApi live -- no caching, no stale data (hackathon rule).

Robustness: transient failures (rate limits, network blips) are retried
with exponential backoff; quota/auth errors fail fast with a clear message.
"""

import time

from .config import serpapi_key

_MAX_RETRIES = 3
_BACKOFF_BASE = 2  # seconds; waits 2s, 4s, 8s


def _is_transient(error: str) -> bool:
    e = error.lower()
    return any(k in e for k in ("rate", "limit", "timeout", "temporar",
                                "503", "502", "504", "429"))


def shopping_search(query: str, gl: str = "in", hl: str = "en",
                    num: int = 20) -> list[dict]:
    """Return raw shopping results for a product query, live from SerpApi.

    Retries transient errors with backoff. Raises RuntimeError with a
    human-readable message on permanent failure (bad key, quota exhausted).
    Returns [] when the query simply has no results.
    """
    try:
        from serpapi import GoogleSearch
    except ImportError as exc:
        raise RuntimeError(
            "The 'serpapi' package (google-search-results) is not installed. "
            "Run: pip install -r requirements.txt"
        ) from exc
    params = {
        "engine": "google_shopping",
        "q": query,
        "gl": gl,
        "hl": hl,
        "num": num,
        "api_key": serpapi_key(),
    }
    last_error = ""
    for attempt in range(_MAX_RETRIES):
        try:
            results = GoogleSearch(params).get_dict()
        except Exception as exc:  # network-level failure
            last_error = str(exc)
            if attempt < _MAX_RETRIES - 1:
                time.sleep(_BACKOFF_BASE * 2 ** attempt)
                continue
            raise RuntimeError(
                f"Could not reach SerpApi after {_MAX_RETRIES} tries: {last_error}"
            ) from exc
        if "error" in results:
            last_error = str(results["error"])
            if _is_transient(last_error) and attempt < _MAX_RETRIES - 1:
                time.sleep(_BACKOFF_BASE * 2 ** attempt)
                continue
            raise RuntimeError(
                f"SerpApi rejected the request: {last_error}. "
                "Check your API key and remaining credits at serpapi.com/manage-api-key"
            )
        return results.get("shopping_results", []) or []
    raise RuntimeError(f"SerpApi request failed: {last_error}")


def _dedupe_key(item: dict) -> tuple:
    raw = item.get("raw", {})
    link = raw.get("product_link") or raw.get("link") or ""
    if link:
        return ("link", link)
    return ("sig", (item.get("title", "").lower(),
                    item.get("merchant", "").lower(),
                    item.get("price")))


def multi_search(queries: list[str], gl: str = "in") -> list[dict]:
    """Run one live search per query, merge, normalize, and dedupe.

    Returns a flat list of normalized items. Empty list means no results
    across all queries -- the agent reports that honestly.
    """
    merged: list[dict] = []
    seen: set = set()
    for q in queries:
        try:
            raw = shopping_search(q, gl=gl)
        except RuntimeError:
            raise
        for r in raw:
            item = normalize(r)
            key = _dedupe_key(item)
            if key not in seen:
                seen.add(key)
                merged.append(item)
    return merged


def normalize(item: dict) -> dict:
    """Pick the fields we rank on out of a raw shopping result."""
    price = item.get("extracted_price")
    return {
        "title": item.get("title", ""),
        "price": price,
        "price_str": item.get("price", ""),
        "merchant": item.get("source", ""),
        "link": item.get("link", "") or item.get("product_link", ""),
        "rating": item.get("rating"),
        "reviews": item.get("reviews"),
        "thumbnail": item.get("thumbnail", ""),
        "raw": item,
    }
