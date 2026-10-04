"""DealSense agent: plan -> search -> compare -> recommend.

1. PLAN: parse the query into product + budget + region (src/plan.py).
2. SEARCH: one live SerpApi call per refined query, merged and deduped.
3. COMPARE: rank with budget/quality guardrails (src/rank.py).
4. RECOMMEND: template-based verdict with trade-off notes (src/verdict.py).
"""

from . import plan as plan_mod
from . import rank, search, verdict


class DealSenseAgent:
    def __init__(self, gl: str = "in"):
        self.gl = gl

    def run(self, query: str) -> dict:
        # 1. PLAN
        plan = plan_mod.parse_query(query)

        # 2. SEARCH -- live SerpApi calls, one per refined query
        items = search.multi_search(plan["refined_queries"], gl=plan["region"])

        # 3. COMPARE
        ranked = rank.rank(items, budget=plan["budget"])

        # 4. RECOMMEND
        text = verdict.write_verdict(ranked, plan["budget"], plan["product"])

        return {
            "query": query,
            "plan": plan,
            "count": len(ranked),
            "picks": ranked[:5],
            "verdict": text,
        }
