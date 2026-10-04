# DealSense

A live market-intelligence shopping agent. Ask in plain language —
*"cheapest RTX 4060 laptop under ₹80k in India right now"* — and DealSense
searches live across merchants with SerpApi, compares prices, weighs
reviews, and returns a ranked recommendation with live buy links.

Built for the **SerpApi India Hackathon 2026**, Track 4 (Commerce & Market
Intelligence). Solo entry.

## How it works

```
You ──► DealSense agent ──► SerpApi (Google Shopping, live) ──► compare ──► ranked picks
                              ▲ no cached / stale data, ever
```

1. **Plan** — the agent parses your query into product keywords, budget
   cap, and region using dependency-light heuristics (`src/plan.py`).
2. **Search** — live calls to SerpApi's Google Shopping engine, one per
   refined query (`"<product>"`, `"<product> buy online India"`,
   `"<product> price"`); results are merged and deduped across calls.
   Search data is a core dependency, per hackathon rules.
3. **Compare** — normalize prices across merchants, filter/flag by budget,
   flag low ratings (< 3.5★), weigh review counts (`src/rank.py`).
4. **Recommend** — template-based verdict picking a winner with trade-off
   notes (`src/verdict.py`).

## Setup

```bash
git clone https://github.com/Pavanboga07/dealsense-.git
cd dealsense-
pip install -r requirements.txt
cp .env.example .env        # then put your SerpApi key in .env
```

Get a free SerpApi key at https://serpapi.com (every valid hackathon
submission also earns 1,000 SerpApi credits).

## Run

```bash
python -m src.cli "RTX 4060 laptop under 80000 in India"
```

Or the web UI:

```bash
python -m src.web
# open http://localhost:5000
```

Example queries the parser handles:

- `"cheapest noise cancelling headphones under ₹20k"`
- `"4k monitor below Rs 30000 in India"`
- `"mechanical keyboard max 1.5 lakh"` (yes, really)
- `"running shoes"` (no budget — pure price ranking)

## Architecture

```
src/
  plan.py     query -> {product, budget, region, refined_queries}
  search.py   live SerpApi Google Shopping calls; retry+backoff; dedupe
  rank.py     budget guardrails, rating flags, merchant cleanup, ranking
  verdict.py  template-based recommendation with trade-off notes
  agent.py    wires plan -> search -> rank -> verdict
  cli.py      rich table + verdict output
tests/        fixture-based tests (no API key needed)
```

## Project status

**Scaffold (Oct 4):** repo layout, live SerpApi search wrapper, config,
CLI entry, agent skeleton.
**Build (Oct 4, pre-reset):** query understanding, refined multi-query
search with retry/backoff and dedupe, ranking guardrails, template
verdict writer, fixture tests — all passing without a live API key.
**Post-reset:** live end-to-end verification with a real SerpApi key,
review-sentiment enrichment, demo video.

## Disclosures

- Started after Sept 1, 2026 (hackathon rule).
- Built with AI coding assistance (disclosed on the submission form).
- All search data is fetched live from SerpApi at query time.
