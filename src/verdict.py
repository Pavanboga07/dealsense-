"""Verdict writer: template-based recommendation, no external API.

Picks a winner from the ranked list and writes an honest short verdict
with trade-off notes, e.g. "cheapest but 3.2 stars; ₹2k more gets 4.6 stars".
"""


def _fmt_price(item: dict) -> str:
    return item.get("price_str") or f"₹{item.get('price'):,.0f}"


def _fmt_rating(item: dict) -> str:
    r = item.get("rating")
    if not isinstance(r, (int, float)):
        return "unrated"
    return f"{r}★"


def write_verdict(picks: list[dict], budget: int | None, product: str) -> str:
    """Write the recommendation text for a ranked pick list."""
    if not picks:
        return (
            "No live results for this query. The search came back empty -- "
            "try a broader product name (e.g. just 'laptop' instead of a "
            "full model number)."
        )

    winner = picks[0]
    lines = [
        f"Best pick: {winner['title'][:70]} at {_fmt_price(winner)} "
        f"from {winner['merchant'] or 'unknown merchant'} "
        f"({_fmt_rating(winner)}, {winner.get('review_count', 0):,} reviews)."
    ]

    # Trade-offs vs the next couple of picks
    notes = []
    for alt in picks[1:3]:
        delta = (alt.get("price") or 0) - (winner.get("price") or 0)
        wr, ar = winner.get("rating"), alt.get("rating")
        if delta < 0 and isinstance(ar, (int, float)) and ar < 3.5:
            notes.append(
                f"{alt['title'][:50]} is ₹{-delta:,.0f} cheaper but rated "
                f"only {ar}★ -- the winner is the safer buy."
            )
        elif delta > 0 and isinstance(ar, (int, float)) and isinstance(wr, (int, float)) and ar > wr + 0.5:
            notes.append(
                f"Spending ₹{delta:,.0f} more gets {alt['title'][:50]} "
                f"at {ar}★ ({alt.get('review_count', 0):,} reviews)."
            )
    if notes:
        lines.append("Trade-offs: " + " ".join(notes))

    if winner.get("low_rating"):
        lines.append(
            "Caution: even the top pick is rated below 3.5★ -- check recent "
            "reviews before buying."
        )
    if budget is not None:
        if winner.get("over_budget"):
            over = (winner.get("price") or 0) - budget
            lines.append(
                f"Heads up: the top pick is ₹{over:,.0f} over your "
                f"₹{budget:,} budget."
            )
        else:
            lines.append(f"All top picks are within your ₹{budget:,} budget.")

    lines.append("Prices were fetched live just now and can change quickly.")
    return " ".join(lines)
