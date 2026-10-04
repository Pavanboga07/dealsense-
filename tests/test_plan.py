"""Fixture-based tests for src/plan.py. Run: python3 -m pytest tests/ (or this file directly)."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import plan


def check(name, got, want):
    status = "ok" if got == want else f"FAIL (got {got!r}, want {want!r})"
    print(f"  {name}: {status}")
    assert got == want, name


def test_parse_budget():
    check("under 80k symbol", plan.parse_budget("under ₹80k"), 80000)
    check("plain number", plan.parse_budget("below Rs 50000"), 50000)
    check("lakh", plan.parse_budget("max ₹1.5 lakh"), 150000)
    check("comma number", plan.parse_budget("₹50,000"), 50000)
    check("bare k", plan.parse_budget("laptop 60k"), 60000)
    check("no budget", plan.parse_budget("RTX 4060 laptop"), None)


def test_extract_product():
    q = "cheapest RTX 4060 laptop under ₹80k in India right now"
    check("product keywords", plan.extract_product(q), "rtx 4060 laptop")
    check("no filler", plan.extract_product("best noise cancelling headphones under 20000"),
          "noise cancelling headphones")


def test_parse_query():
    p = plan.parse_query("cheapest RTX 4060 laptop under ₹80k in India right now")
    check("product", p["product"], "rtx 4060 laptop")
    check("budget", p["budget"], 80000)
    check("region", p["region"], "in")
    assert len(p["refined_queries"]) >= 2
    print(f"  refined queries: {p['refined_queries']}")


if __name__ == "__main__":
    test_parse_budget()
    test_extract_product()
    test_parse_query()
    print("plan tests passed")
