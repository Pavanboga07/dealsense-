"""DealSense web UI.

Run:  python -m src.web
Then open http://localhost:5000 in a browser.
"""

from flask import Flask, request, render_template_string

from .agent import DealSenseAgent

app = Flask(__name__)

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>DealSense — live market intelligence</title>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  body { font-family: system-ui, -apple-system, sans-serif; background: #0f1115;
         color: #e8eaf0; margin: 0; padding: 2rem 1rem; }
  .wrap { max-width: 760px; margin: 0 auto; }
  h1 { font-size: 1.8rem; margin: 0 0 .2rem; }
  h1 span { color: #7dd87d; }
  p.sub { color: #9aa0b0; margin-top: 0; }
  form { display: flex; gap: .5rem; margin: 1.5rem 0; }
  input[type=text] { flex: 1; padding: .8rem 1rem; font-size: 1rem;
    border: 1px solid #2a2f3a; border-radius: 10px; background: #171b23; color: inherit; }
  button { padding: .8rem 1.4rem; font-size: 1rem; border: 0; border-radius: 10px;
    background: #7dd87d; color: #0f1115; font-weight: 700; cursor: pointer; }
  button:hover { background: #93e493; }
  .verdict { background: #171b23; border: 1px solid #2a2f3a; border-left: 4px solid #7dd87d;
    border-radius: 10px; padding: 1rem 1.2rem; margin: 1rem 0; }
  .card { background: #171b23; border: 1px solid #2a2f3a; border-radius: 10px;
    padding: 1rem 1.2rem; margin: .7rem 0; display: flex; gap: 1rem; align-items: center; }
  .price { font-size: 1.3rem; font-weight: 800; color: #7dd87d; white-space: nowrap; }
  .meta { color: #9aa0b0; font-size: .9rem; }
  .title { font-weight: 600; margin-bottom: .25rem; }
  .warn { color: #f0b429; font-size: .85rem; }
  .err { background: #2a1518; border: 1px solid #5a2b30; border-radius: 10px;
    padding: 1rem 1.2rem; color: #f2b8bd; }
  .foot { color: #6b7280; font-size: .8rem; margin-top: 2rem; text-align: center; }
  a { color: #7dd87d; }
</style>
</head>
<body>
<div class="wrap">
  <h1>Deal<span>Sense</span></h1>
  <p class="sub">Live market intelligence for Indian shoppers. Prices fetched seconds ago via SerpApi.</p>
  <form method="post" action="/search">
    <input type="text" name="q" placeholder="e.g. RTX 4060 laptop under 80000" value="{{ q|e }}" required>
    <button type="submit">Find deals</button>
  </form>
  {% if error %}
    <div class="err">{{ error }}</div>
  {% endif %}
  {% if result %}
    <div class="verdict"><strong>Verdict:</strong> {{ result.verdict }}</div>
    {% for p in result.picks %}
    <div class="card">
      <div class="price">{{ p.price_str }}</div>
      <div>
        <div class="title">{{ p.title }}</div>
        <div class="meta">{{ p.merchant }}{% if p.rating %} &middot; {{ p.rating }}&#9733;{% endif %}{% if p.reviews %} ({{ p.reviews }} reviews){% endif %}</div>
        {% if p.flags %}<div class="warn">{{ p.flags|join(', ') }}</div>{% endif %}
        {% if p.link %}<div class="meta"><a href="{{ p.link }}" target="_blank" rel="noopener">Buy link &rarr;</a></div>{% endif %}
      </div>
    </div>
    {% endfor %}
    <div class="foot">{{ result.count }} live results &middot; fetched just now, prices can change quickly</div>
  {% endif %}
  <div class="foot">DealSense &middot; SerpApi India Hackathon 2026 &middot; Track 4</div>
</div>
</body>
</html>
"""


@app.get("/")
def index():
    return render_template_string(PAGE, q="", result=None, error=None)


@app.post("/search")
def search():
    q = request.form.get("q", "").strip()
    if not q:
        return render_template_string(PAGE, q=q, result=None, error="Type a product query first.")
    try:
        result = DealSenseAgent().run(q)
    except RuntimeError as e:
        return render_template_string(PAGE, q=q, result=None, error=str(e))
    if not result["picks"]:
        return render_template_string(
            PAGE, q=q, result=None,
            error="No live results for that query. Try a broader product name.",
        )
    return render_template_string(PAGE, q=q, result=result, error=None)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
