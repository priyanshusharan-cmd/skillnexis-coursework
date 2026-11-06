"""Display banners (6 IAB sizes) and Meta feed/story creatives, from one template.  python ads/creatives.py && node ads/render.js"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
SIZES = [("display-300x250", 300, 250), ("display-336x280", 336, 280), ("display-728x90", 728, 90), ("display-160x600", 160, 600), ("display-320x50", 320, 50),
         ("display-1200x628", 1200, 628), ("meta-feed-1080x1080", 1080, 1080), ("meta-story-1080x1920", 1080, 1920)]
def banner(id_, w, h):
    s = min(w, h); wide = w / h > 2.5; tall = h / w > 2
    title = 34 if s >= 250 else 22; t = max(13, int(s * (0.10 if not wide else 0.30)))
    if w >= 1000: t = int(min(w, h) * 0.085)
    layout = "row" if wide else "column"
    return f'''<div class="b" id="{id_}" style="width:{w}px;height:{h}px;flex-direction:{layout};padding:{max(6, s // 14)}px {max(8, s // 10)}px;gap:{max(6, s // 20)}px;justify-content:{'center' if h > 1.5 * w and w > 500 else 'flex-start'};align-items:{'center' if wide else 'flex-start'}">
  <div class="brand" style="font-size:{max(10, t * .45):.0f}px">☕ Bean &amp; Bloom</div>
  <div style="flex:1;min-width:0"><div class="h" style="font-size:{t}px">{'Study Fuel ₹149' if s < 120 else 'Exam season? Study Fuel combo ₹149'}</div>
  {'' if s < 120 else f'<div class="sub" style="font-size:{max(11, t * .42):.0f}px">Coffee + banana bread · weekdays 3–7 pm · 2 min from campus</div>'}</div>
  <div class="cta" style="font-size:{max(10, t * .42):.0f}px;padding:{max(4, t * .3):.0f}px {max(8, t * .6):.0f}px">{'Visit today' if s >= 90 else 'Visit'}</div>
  {'<svg class="cup" viewBox="0 0 100 110" style="width:' + str(int(s * (.38 if s < 500 else .5) * (1.6 if h > 1.5 * w and w > 500 else 1))) + 'px;right:' + str(int(s * -.06)) + 'px;bottom:' + str(int(s * -.06)) + 'px"><path d="M14 28h62l-7 72a7 7 0 0 1-7 6H28a7 7 0 0 1-7-6z" fill="#E8A0A6"/><ellipse cx="45" cy="28" rx="31" ry="6" fill="#FFF7EC"/><path d="M76 40h7a12 12 0 0 1 0 24h-9" stroke="#E8A0A6" stroke-width="6" fill="none"/></svg>' if not wide and s >= 250 else ''}
</div>'''
css = """*{box-sizing:border-box;margin:0}body{background:#ccc;padding:30px;display:flex;flex-wrap:wrap;gap:30px;align-items:flex-start;font-family:Inter,sans-serif}
.b{background:#3B2416;color:#FFF7EC;display:flex;position:relative;overflow:hidden;border-radius:2px} .brand{font-weight:800;color:#E8A0A6;white-space:nowrap;z-index:1}
.h{font-family:'Inter Display',Inter;font-weight:800;line-height:1.05;z-index:1;position:relative} .sub{margin-top:.5em;opacity:.9;line-height:1.3;max-width:62%;position:relative;z-index:1}
.cta{background:#E8A0A6;color:#3B2416;font-weight:800;border-radius:999px;white-space:nowrap;z-index:1;position:relative} .cup{position:absolute;z-index:0;opacity:.95}"""
open(os.path.join(HERE, "creatives.html"), "w").write(f"<!doctype html><html><head><meta charset='utf-8'><style>{css}</style></head><body>{''.join(banner(*x) for x in SIZES)}</body></html>")
print(len(SIZES), "creatives")
