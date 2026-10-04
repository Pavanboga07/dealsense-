"""Query understanding: plain language -> structured plan.

Dependency-light: regex and heuristics only, no paid LLM API.
Turns "cheapest RTX 4060 laptop under ₹80k in India right now" into
{"product": "RTX 4060 laptop", "budget": 80000, "region": "in",
 "refined_queries": [...]}.
"""

import re

# Words that describe intent, not the product. Stripped from the query.
_FILLER = {
    "cheapest", "cheap", "best", "buy", "find", "show", "get", "search",
    "right", "now", "me", "please", "the", "a", "an", "for", "with",
    "deal", "deals", "discount", "offer", "offers", "online", "india",
    "indian", "under", "below", "less", "than", "up", "to", "max",
    "maximum", "budget", "within", "around", "about", "price", "cost",
}

# Budget phrases to remove from the product keywords after parsing.
_BUDGET_PHRASES = [
    r"under\s+[₹rsinr\.\s]*[\d,\.]+\s*(?:k|lakh|lac|l)?",
    r"below\s+[₹rsinr\.\s]*[\d,\.]+\s*(?:k|lakh|lac|l)?",
    r"(?:max|maximum|upto|up\s*to)\s+[₹rsinr\.\s]*[\d,\.]+\s*(?:k|lakh|lac|l)?",
    r"within\s+[₹rsinr\.\s]*[\d,\.]+\s*(?:k|lakh|lac|l)?",
    r"[₹]\s*[\d,\.]+\s*(?:k|lakh|lac|l)?",
    r"\brs\.?\s*[\d,\.]+\s*(?:k|lakh|lac|l)?",
    r"\binr\s*[\d,\.]+\s*(?:k|lakh|lac|l)?",
    r"\b\d[\d,\.]*\s*(?:k|lakh|lac)\b",
]

_NUMBER = r"[\d]+(?:,[\d]+)*(?:\.[\d]+)?"


def _to_int(num: str) -> int | None:
    try:
        return int(float(num.replace(",", "")))
    except ValueError:
        return None


def parse_budget(text: str) -> int | None:
    """Extract a budget cap in rupees from free text.

    Handles: "under ₹80k", "below Rs 50000", "max ₹1.5 lakh", "₹50,000",
    "80k", "1 lakh". Returns None when no budget is mentioned.
    """
    t = text.lower()

    # lakh / lac first (1 lakh = 100000)
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:lakh|lac)\b", t)
    if m:
        return int(float(m.group(1)) * 100000)

    # k suffix (80k = 80000)
    m = re.search(r"[₹]?\s*(\d+(?:\.\d+)?)\s*k\b", t)
    if m:
        return int(float(m.group(1)) * 1000)

    # plain number near a budget keyword or currency symbol
    for pattern in (
        rf"(?:under|below|max|maximum|upto|up\s*to|within|budget)\s+[₹]?\s*({_NUMBER})",
        rf"[₹]\s*({_NUMBER})",
        rf"\brs\.?\s*({_NUMBER})",
        rf"\binr\s*({_NUMBER})",
    ):
        m = re.search(pattern, t)
        if m:
            return _to_int(m.group(1))

    return None


def parse_region(text: str) -> str:
    """Return the SerpApi `gl` param. Defaults to India ("in").

    Detects explicit non-India mentions; otherwise India, since this
    project targets the SerpApi India Hackathon.
    """
    t = text.lower()
    for country, gl in (("usa", "us"), ("united states", "us"), ("uk", "uk"),
                        ("united kingdom", "uk"), ("uae", "ae"), ("dubai", "ae")):
        if country in t:
            return gl
    return "in"


def extract_product(text: str) -> str:
    """Strip budget phrases, filler words, and region mentions.

    Keeps the product description: "RTX 4060 laptop" from
    "cheapest RTX 4060 laptop under ₹80k in India right now".
    """
    t = text.lower()
    for phrase in _BUDGET_PHRASES:
        t = re.sub(phrase, " ", t)
    t = re.sub(r"\bin\s+india\b", " ", t)
    words = [w for w in re.findall(r"[a-z0-9+.\-]+", t) if w not in _FILLER]
    return " ".join(words).strip()


def refined_queries(product: str, region: str = "in") -> list[str]:
    """Generate 2-3 SerpApi shopping queries from the product keywords."""
    queries = [product]
    if region == "in":
        queries.append(f"{product} buy online India")
    queries.append(f"{product} price")
    # dedupe while preserving order
    seen, out = set(), []
    for q in queries:
        if q not in seen:
            seen.add(q)
            out.append(q)
    return out


def parse_query(text: str) -> dict:
    """Full pipeline: text -> plan dict used by the agent."""
    product = extract_product(text)
    region = parse_region(text)
    budget = parse_budget(text)
    return {
        "product": product,
        "budget": budget,
        "region": region,
        "refined_queries": refined_queries(product, region),
        "original": text,
    }
