"""Ranking: explainable, cheapest-first with quality guardrails.

Rules, in order:
1. Drop items with no usable price.
2. Clean merchant names (whitespace, casing).
3. Flag (not hide) low ratings (< 3.5 stars) and over-budget items.
4. Sort: in-budget items first by price; near-equal prices (within ₹500)
   break ties toward more reviews; over-budget items trail at the end.
"""

import re

LOW_RATING = 3.5
_PRICE_BUCKET = 500  # rupees; prices within one bucket count as "equal"


def _price(item: dict) -> float:
    p = item.get("price")
    return float(p) if isinstance(p, (int, float)) else float("inf")


def _review_count(item: dict) -> int:
    r = item.get("reviews")
    if isinstance(r, int):
        return r
    if isinstance(r, str):
        m = re.search(r"\d+", r.replace(",", ""))
        return int(m.group(0)) if m else 0
    return 0


def clean_merchant(name: str) -> str:
    """Normalize merchant names: collapse whitespace, strip trailing dots."""
    return re.sub(r"\s+", " ", (name or "").strip()).rstrip(".")


def annotate(items: list[dict], budget: int | None) -> list[dict]:
    """Add guardrail flags to each item, in place. Returns the items."""
    for item in items:
        item["merchant"] = clean_merchant(item.get("merchant", ""))
        item["review_count"] = _review_count(item)
        rating = item.get("rating")
        item["low_rating"] = isinstance(rating, (int, float)) and rating < LOW_RATING
        price = _price(item)
        item["over_budget"] = budget is not None and price > budget
    return items


def rank(items: list[dict], budget: int | None = None) -> list[dict]:
    """Rank items per the rules above. Budget may be None (no cap)."""
    usable = [i for i in items if _price(i) != float("inf")]
    annotate(usable, budget)

    def key(item: dict):
        price = _price(item)
        bucket = round(price / _PRICE_BUCKET)
        # reviews only break ties within a price bucket, capped so a
        # viral-but-pricier item can't leapfrog a genuinely cheaper one
        tiebreak = -min(item["review_count"], 10_000)
        return (1 if item["over_budget"] else 0, bucket, tiebreak, price)

    return sorted(usable, key=key)
