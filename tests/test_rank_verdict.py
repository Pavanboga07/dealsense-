"""Fixture tests for rank.py, verdict.py, and search.multi_search dedupe.

Uses hand-made fixtures shaped like SerpApi shopping_results.
Run: python3 tests/test_rank_verdict.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import rank, search, verdict


def raw(title, price, source, rating=None, reviews=0, link=""):
    item = {"title": title, "extracted_price": price,
            "price": f"₹{price:,}" if price is not None else "",
            "source": source, "rating": rating, "reviews": reviews,
            "product_link": link or f"https://x/{title[:5]}"}
    return search.normalize(item)


ITEMS = [
    raw("RTX 4060 Laptop A", 74990, "  Flipkart ", 4.2, 1200),
    raw("RTX 4060 Laptop B", 72990, "UnknownSeller", 3.2, 45),
    raw("RTX 4060 Laptop C", 76990, "Amazon.in", 4.6, 800),
    raw("RTX 4060 Laptop D", 95000, "Croma", 4.8, 300),   # over budget
    raw("RTX 4060 Laptop E", None, "eBay", 4.0, 10),     # no price -> dropped
]


def check(name, cond):
    print(f"  {name}: {'ok' if cond else 'FAIL'}")
    assert cond, name


def test_rank():
    ranked = rank.rank(ITEMS, budget=80000)
    check("drops no-price", len(ranked) == 4)
    check("cheapest in-budget first", ranked[0]["title"] == "RTX 4060 Laptop B")
    check("merchant cleaned", ranked[1]["merchant"] == "Flipkart")
    check("low rating flagged", ranked[0]["low_rating"] is True)
    check("over-budget trails", ranked[-1]["title"] == "RTX 4060 Laptop D")
    check("over-budget flagged", ranked[-1]["over_budget"] is True)
    check("review counts parsed", ranked[1]["review_count"] == 1200)


def test_rank_no_budget():
    ranked = rank.rank(ITEMS)
    check("no budget: pure price order", ranked[0]["title"] == "RTX 4060 Laptop B")
    check("no budget: none over", all(not i["over_budget"] for i in ranked))


def test_verdict():
    ranked = rank.rank(ITEMS, budget=80000)
    v = verdict.write_verdict(ranked, 80000, "rtx 4060 laptop")
    check("names winner", "RTX 4060 Laptop B" in v)
    check("trade-off note", "cheaper but rated" in v or "Trade-offs" in v)
    check("budget line", "within your ₹80,000 budget" in v)
    print("  verdict:", v[:160], "...")


def test_verdict_empty():
    v = verdict.write_verdict([], 80000, "laptop")
    check("honest empty", "No live results" in v)


def test_dedupe():
    # stub shopping_search to return the same item twice across queries
    calls = {"n": 0}

    def fake_search(query, gl="in", hl="en", num=20):
        calls["n"] += 1
        return [{"title": "Same Laptop", "extracted_price": 50000,
                 "price": "₹50,000", "source": "Flipkart",
                 "product_link": "https://x/same"}]

    orig = search.shopping_search
    search.shopping_search = fake_search
    try:
        merged = search.multi_search(["q1", "q2"])
    finally:
        search.shopping_search = orig
    check("dedupes across queries", len(merged) == 1 and calls["n"] == 2)


if __name__ == "__main__":
    test_rank()
    test_rank_no_budget()
    test_verdict()
    test_verdict_empty()
    test_dedupe()
    print("rank/verdict tests passed")
