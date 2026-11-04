"""tokens.json -> tokens.css (CSS variables), the WCAG contrast report, and the style-guide page.
    python design/build.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
T = json.load(open(os.path.join(HERE, "tokens.json")))
# WCAG 2.2: 4.5:1 for normal text (AA), 3:1 for large text (>= 24 px, or >= 18.66 px bold) and UI components/graphics
NEED = {"body": 4.5, "caption": 4.5, "label": 4.5, "large": 3.0, "ui": 3.0, "decorative": 1.0}  # decorative dividers: exempt (1.4.11)


def lum(hex_):
    c = [int(hex_[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def ratio(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def css():
    out = [":root {"]
    for k, f in T["type"]["families"].items():
        out.append(f"  --font-{k}: '{f}', system-ui, sans-serif;")
    for k, v in T["type"]["scale"].items():
        out.append(f"  --{k}: {v['weight']} {v['size']}px/{v['line']}px var(--font-{v['family']});")
    for i, v in enumerate(T["space"]):
        out.append(f"  --s{i}: {v}px;")
    for k, v in T["radius"].items():
        out.append(f"  --r-{k}: {v}px;")
    out.append("}")
    for theme, t in T["themes"].items():
        out.append(f".theme-{theme} {{")
        out += [f"  --{k}: {v};" for k, v in t["color"].items()]
        out.append("}")
    for k in T["type"]["scale"]:
        out.append(f".t-{k} {{ font: var(--{k}); margin: 0; }}")
    return "\n".join(out) + "\n"


def contrast():
    rows, fails = [], 0
    for theme, t in T["themes"].items():
        for fg, bg, use in t["pairs"]:
            r = ratio(t["color"][fg], t["color"][bg])
            ok = r >= NEED[use]
            fails += not ok
            aaa = " (AAA)" if use in ("body", "caption", "label") and r >= 7 else ""
            rows.append((t["name"], fg, bg, use, r, ok, aaa))
    return rows, fails


def main():
    open(os.path.join(HERE, "tokens.css"), "w").write(css())
    rows, fails = contrast()
    md = ["| App | Text / element | On | Used for | Ratio | WCAG 2.2 AA |", "|---|---|---|---|---:|---|"]
    md += [f"| {a} | `{f}` | `{b}` | {u} | {r:.2f}:1 | {'pass' + x if ok else '**FAIL**'} |" for a, f, b, u, r, ok, x in rows]
    md += ["", f"{len(rows) - fails}/{len(rows)} pairs pass. Normal text needs 4.5:1, large text and UI parts (borders, icons, focus rings) 3:1.",
           "`line` (1.3:1) is only used for decorative dividers between list rows, which WCAG 1.4.11 exempts; anything that identifies a "
           "control (input borders, checkboxes, outline buttons) uses `ink-500` or `brand-600`, checked above at >= 3:1."]
    open(os.path.join(HERE, "..", "contrast-report.md"), "w").write("# Colour contrast (computed from tokens.json)\n\n" + "\n".join(md) + "\n")
    print("\n".join(md))
    sg = style_guide(rows)
    open(os.path.join(HERE, "style-guide.html"), "w").write(sg)
    return fails


def style_guide(rows):
    h = T["themes"]["haat"]["color"]
    sw = "".join(f'<div class="sw"><div class="chip" style="background:{v}"></div><b>{k}</b><span>{v}</span></div>' for k, v in h.items())
    ty = "".join(f'<div class="ty"><span class="meta">{k} · {v["size"]}/{v["line"]} · {v["weight"]} · {T["type"]["families"][v["family"]]}</span>'
                 f'<p class="t-{k}">Fresh mangoes, delivered today</p></div>' for k, v in reversed(list(T["type"]["scale"].items())))
    sp = "".join(f'<div class="sp"><div style="width:{v}px"></div><span>s{i} · {v}px</span></div>' for i, v in enumerate(T["space"]) if v)
    cr = "".join(f'<tr><td><span class="pair" style="color:{T["themes"]["haat"]["color"][f]};background:{T["themes"]["haat"]["color"][b]}">Aa</span></td>'
                 f'<td>{f} on {b}</td><td>{u}</td><td>{r:.2f}:1</td><td class="{"ok" if ok else "bad"}">{"AA" + x if ok else "fail"}</td></tr>'
                 for a, f, b, u, r, ok, x in rows if a.startswith("Haat"))
    return f"""<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="tokens.css"><style>
body{{margin:0;background:var(--canvas);color:var(--ink-900);font:var(--body)}} .page{{width:1200px;padding:56px;box-sizing:border-box}}
h2{{font:var(--headline);margin:48px 0 16px}} .sw{{display:inline-flex;flex-direction:column;width:132px;margin:0 12px 16px 0;font:var(--caption)}}
.chip{{height:72px;border-radius:var(--r-md);border:1px solid var(--line);margin-bottom:8px}} .sw span{{color:var(--ink-500)}}
.ty{{display:grid;grid-template-columns:320px 1fr;align-items:baseline;border-bottom:1px solid var(--line);padding:12px 0}} .meta{{font:var(--caption);color:var(--ink-500)}}
.sp{{display:flex;align-items:center;gap:16px;margin:6px 0;font:var(--caption)}} .sp div{{height:16px;background:var(--brand-500);border-radius:4px}}
table{{border-collapse:collapse;font:var(--label)}} td{{padding:8px 16px;border-bottom:1px solid var(--line)}} .pair{{display:inline-block;padding:4px 12px;border-radius:6px;font:var(--title);border:1px solid var(--line)}}
.ok{{color:var(--leaf-700)}} .bad{{color:var(--danger-700)}} .comp{{display:flex;gap:16px;align-items:center;flex-wrap:wrap}}
.btn{{font:var(--label);border:0;border-radius:var(--r-md);padding:14px 24px;min-height:48px}} .p{{background:var(--brand-600);color:#fff}} .s{{background:var(--brand-100);color:var(--brand-600)}}
.g{{background:transparent;color:var(--brand-600);outline:2px solid var(--brand-600)}} .f{{background:var(--brand-600);color:#fff;box-shadow:0 0 0 3px var(--surface),0 0 0 5px var(--brand-500)}}
.inp{{font:var(--body);padding:12px 16px;border:1px solid var(--ink-500);border-radius:var(--r-md);width:260px;background:#fff}} .tag{{font:var(--caption);background:var(--leaf-100);color:var(--leaf-700);padding:4px 10px;border-radius:999px}}
</style></head><body class="theme-haat"><div class="page">
<p class="t-caption" style="color:var(--brand-600);letter-spacing:.08em">HAAT DESIGN SYSTEM · v1</p><h1 class="t-hero">Style guide</h1>
<p style="max-width:720px;color:var(--ink-700)">One source of truth (<code>tokens.json</code>) generates the CSS variables used by every screen, this page, and the
contrast report. Type uses a 1.25 (major third) scale on a 16 px base with a 4 px line-height grid; spacing is a 4/8 px scale.</p>
<h2>Colour</h2>{sw}<h2>Typography: Inter Display (headings) + Inter (text)</h2>{ty}
<h2>Spacing</h2>{sp}<h2>Components</h2><div class="comp"><button class="btn p">Add to cart</button><button class="btn s">Save for later</button>
<button class="btn g">View all</button><button class="btn f">Focused</button><input class="inp" placeholder="Search mangoes, atta, oil…"><span class="tag">In stock</span></div>
<p class="t-caption" style="color:var(--ink-500);margin-top:12px">Touch targets ≥ 48 px. Focus ring: 2 px brand-500 with a 3 px white gap (≥ 3:1 against both surfaces). Inputs use a 4.5:1 border so the field edge is visible.</p>
<h2>Contrast checks (WCAG 2.2)</h2><table>{cr}</table></div></body></html>"""


if __name__ == "__main__":
    raise SystemExit(1 if main() else 0)
