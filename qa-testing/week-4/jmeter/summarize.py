"""Summarise a JMeter CSV results file (.jtl) per request and overall.

usage: python summarize.py results.jtl --title "Stress: 100 users" [--out summary.md]
       [--max-error-pct 1] [--max-p95-ms 500]
Exits with status 1 when a threshold is broken, so CI fails the build.
"""
import argparse
import csv
import json
import math
from collections import defaultdict


def pct(sorted_vals, p):
    if not sorted_vals:
        return 0
    k = max(0, math.ceil(p / 100 * len(sorted_vals)) - 1)
    return sorted_vals[k]


def stats(rows):
    el = sorted(int(r["elapsed"]) for r in rows)
    ts = [int(r["timeStamp"]) for r in rows]
    span = (max(ts) - min(ts)) / 1000 if len(ts) > 1 else 1
    errors = sum(r["success"] != "true" for r in rows)
    return {
        "samples": len(rows),
        "error_pct": round(100 * errors / len(rows), 2) if rows else 0,
        "avg_ms": round(sum(el) / len(el), 1) if el else 0,
        "p50_ms": pct(el, 50), "p90_ms": pct(el, 90), "p95_ms": pct(el, 95), "p99_ms": pct(el, 99),
        "max_ms": el[-1] if el else 0,
        "throughput_rps": round(len(rows) / span, 1) if span else 0,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jtl")
    ap.add_argument("--title", default="JMeter run")
    ap.add_argument("--out")
    ap.add_argument("--json")
    ap.add_argument("--max-error-pct", type=float, default=1.0)
    ap.add_argument("--max-p95-ms", type=float, default=500.0)
    a = ap.parse_args()

    with open(a.jtl, newline="") as f:
        rows = list(csv.DictReader(f))
    by_label = defaultdict(list)
    for r in rows:
        by_label[r["label"]].append(r)
    overall = stats(rows)
    per = {k: stats(v) for k, v in sorted(by_label.items())}
    codes = defaultdict(int)
    for r in rows:
        if r["success"] != "true":
            codes[f'{r["label"]} -> {r["responseCode"]} {r.get("failureMessage", "")[:80]}'.strip()] += 1

    lines = [f"### {a.title}", "", "| Request | Samples | Error % | Avg ms | p90 | p95 | p99 | Max | Req/s |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for name, s in [*per.items(), ("**All requests**", overall)]:
        lines.append(f'| {name} | {s["samples"]} | {s["error_pct"]} | {s["avg_ms"]} | {s["p90_ms"]} | {s["p95_ms"]} | {s["p99_ms"]} | {s["max_ms"]} | {s["throughput_rps"]} |')
    ok_err = overall["error_pct"] <= a.max_error_pct
    ok_p95 = overall["p95_ms"] <= a.max_p95_ms
    lines += ["", f'- Error rate {overall["error_pct"]}% (limit {a.max_error_pct}%): {"PASS" if ok_err else "FAIL"}',
              f'- p95 {overall["p95_ms"]} ms (limit {a.max_p95_ms:g} ms): {"PASS" if ok_p95 else "FAIL"}']
    if codes:
        lines += ["", "Failures:"] + [f"- {k}: {v}" for k, v in sorted(codes.items(), key=lambda x: -x[1])[:10]]
    text = "\n".join(lines) + "\n"
    print(text)
    if a.out:
        open(a.out, "w").write(text)
    if a.json:
        json.dump({"title": a.title, "overall": overall, "per_request": per, "failures": codes}, open(a.json, "w"), indent=2)
    raise SystemExit(0 if ok_err and ok_p95 else 1)


if __name__ == "__main__":
    main()
