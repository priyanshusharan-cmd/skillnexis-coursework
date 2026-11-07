"""Token and cost tracking: price lookup, per-request cost, budgets and the aggregates behind the dashboard."""
import collections, datetime, os, statistics
import yaml
from . import store
PRICES = yaml.safe_load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "pricing.yaml")))
def price(provider, model):
    if provider == "ollama": return PRICES["ollama"]
    return PRICES.get(model) or PRICES.get(provider) or dict(input=0.0, output=0.0, unknown=True)
def cost(provider, model, prompt_tokens, completion_tokens):
    p = price(provider, model); return round((prompt_tokens * p["input"] + completion_tokens * p["output"]) / 1e6, 8)
def what_if(rows, model):
    """Cost of the same tokens on another model's list price (handy while running offline or on a free tier)."""
    p = PRICES[model]; return round(sum(r["prompt_tokens"] * p["input"] + r["completion_tokens"] * p["output"] for r in rows) / 1e6, 6)
def pct(v, q):
    if not v: return None
    v = sorted(v); return round(v[min(len(v) - 1, int(round(q * (len(v) - 1))))], 1)
def summary(rows):
    chats = [r for r in rows if r["endpoint"] == "chat"]; ok = [r for r in chats if r["status"] == "ok"]
    by_day = collections.defaultdict(lambda: dict(requests=0, tokens=0, cost_usd=0.0))
    for r in rows:
        d = by_day[r["ts"][:10]]; d["requests"] += 1; d["tokens"] += (r["prompt_tokens"] or 0) + (r["completion_tokens"] or 0); d["cost_usd"] += r["cost_usd"] or 0
    by_user = collections.defaultdict(lambda: dict(requests=0, tokens=0, cost_usd=0.0))
    for r in rows:
        u = by_user[r.get("user") or str(r["user_id"])]; u["requests"] += 1; u["tokens"] += (r["prompt_tokens"] or 0) + (r["completion_tokens"] or 0); u["cost_usd"] += r["cost_usd"] or 0
    return dict(
        requests=len(rows), chats=len(chats), answered=len(ok),
        status=dict(collections.Counter(r["status"] for r in rows)), guardrails=dict(collections.Counter(g for r in rows for g in (r["guardrail"] or "").split(";") if g)),
        prompt_tokens=sum(r["prompt_tokens"] or 0 for r in rows), completion_tokens=sum(r["completion_tokens"] or 0 for r in rows),
        exact_token_share=round(sum(1 for r in rows if r["exact"]) / len(rows), 3) if rows else None,
        cost_usd=round(sum(r["cost_usd"] or 0 for r in rows), 6),
        cost_if_gemini_2_5_flash=what_if(rows, "gemini-2.5-flash"),
        latency_ms=dict(p50=pct([r["latency_ms"] for r in ok], .5), p95=pct([r["latency_ms"] for r in ok], .95)),
        ttft_ms=dict(p50=pct([r["ttft_ms"] for r in ok if r["ttft_ms"] is not None], .5), p95=pct([r["ttft_ms"] for r in ok if r["ttft_ms"] is not None], .95)),
        grounded_mean=round(statistics.mean([r["grounded"] for r in ok if r["grounded"] is not None]), 3) if ok else None,
        flagged_answers=sum(1 for r in ok if r["flagged"]),
        top_sources=collections.Counter(r["top_source"] for r in ok if r["top_source"]).most_common(8),
        by_day=dict(sorted(by_day.items())), by_user=dict(by_user),
        recent=[{k: r[k] for k in ("ts", "user", "endpoint", "status", "prompt_tokens", "completion_tokens", "cost_usd", "latency_ms", "grounded", "guardrail")} for r in rows[-15:]][::-1])
