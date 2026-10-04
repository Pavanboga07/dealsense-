"""CLI entry: python -m src.cli "your query" """

import sys

from rich.console import Console
from rich.table import Table

from .agent import DealSenseAgent

console = Console()


def main() -> None:
    if len(sys.argv) < 2:
        console.print('Usage: python -m src.cli "RTX 4060 laptop under 80000 in India"')
        sys.exit(1)
    query = " ".join(sys.argv[1:])

    try:
        result = DealSenseAgent().run(query)
    except RuntimeError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        sys.exit(1)

    if result["count"] == 0:
        console.print(f"[yellow]{result['verdict']}[/yellow]")
        return

    table = Table(title=f"DealSense: {result['query']} ({result['count']} live results)")
    table.add_column("Title", style="cyan", max_width=50)
    table.add_column("Price", style="green")
    table.add_column("Merchant")
    table.add_column("Rating")
    for pick in result["picks"]:
        rating = pick.get("rating")
        rating_str = f"{rating}★" if isinstance(rating, (int, float)) else "-"
        if pick.get("low_rating"):
            rating_str += " ⚠"
        table.add_row(
            pick["title"][:60],
            pick["price_str"] or f"₹{pick['price']:,.0f}",
            pick["merchant"],
            rating_str,
        )
    console.print(table)
    console.print()
    console.print(f"[bold]Verdict:[/bold] {result['verdict']}")


if __name__ == "__main__":
    main()
