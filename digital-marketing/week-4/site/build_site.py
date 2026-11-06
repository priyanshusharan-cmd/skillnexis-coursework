"""Hisaab marketing site: SEO-optimised home page + one pillar blog article, sitemap, robots, structured data.
Target keywords (from docs/strategy.md): "split expenses app india", "split bills with friends upi", "how to split hostel expenses".
    python site/build_site.py
"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = "https://hisaab.example"
CSS = """:root{--brand:#0F766E;--dark:#0B3B37;--tint:#D5F5EF;--ink:#101828;--ink2:#344054;--ink3:#5D6B82;--line:#E4E7EC;--owe:#B42318;--owed:#067647}
*{box-sizing:border-box}body{margin:0;font:400 17px/1.65 Inter,system-ui,sans-serif;color:var(--ink);background:#fff}a{color:var(--brand)}
.w{max-width:1100px;margin:auto;padding:0 20px}header.nav{display:flex;justify-content:space-between;align-items:center;padding:18px 20px;max-width:1100px;margin:auto}
.logo{font:800 22px 'Inter Display',Inter;color:var(--dark);text-decoration:none}.nav a.l{margin-left:20px;color:var(--ink2);text-decoration:none;font-weight:600;font-size:15px}
.btn{display:inline-block;background:var(--brand);color:#fff;text-decoration:none;font-weight:700;padding:14px 22px;border-radius:12px;border:0;font-size:16px;cursor:pointer}
.btn.sec{background:var(--tint);color:var(--dark)}h1{font:800 clamp(36px,5.5vw,60px)/1.05 'Inter Display',Inter;letter-spacing:-.02em;margin:0 0 18px}
h2{font:800 clamp(28px,3.5vw,38px)/1.15 'Inter Display',Inter;margin:0 0 14px}h3{font:700 21px 'Inter Display',Inter;margin:0 0 8px}p{color:var(--ink2)}
.hero{display:grid;grid-template-columns:1.1fr .9fr;gap:40px;align-items:center;padding:40px 20px 72px}.hero img{width:100%;height:auto;border-radius:28px}
.sec{padding:64px 0}.alt{background:#F5F8F7}.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:24px}.card{background:#fff;border:1px solid var(--line);border-radius:20px;padding:24px}
.num{font:800 40px 'Inter Display',Inter;color:var(--brand)}table{width:100%;border-collapse:collapse;background:#fff;border-radius:16px;overflow:hidden}th,td{padding:12px 14px;border-bottom:1px solid var(--line);text-align:left}th{background:var(--tint);color:var(--dark)}
details{border-bottom:1px solid var(--line);padding:14px 0}summary{font-weight:700;cursor:pointer}form.wl{display:flex;gap:10px;flex-wrap:wrap;margin-top:18px}form.wl input{flex:1;min-width:220px;height:50px;border:1.5px solid var(--ink3);border-radius:12px;padding:0 14px;font:inherit}
footer{border-top:1px solid var(--line);padding:28px 20px 48px;color:var(--ink3);font-size:14px;max-width:1100px;margin:auto}
article{max-width:720px;margin:auto;padding:24px 20px 64px}article h2{font-size:28px;margin-top:40px}article img{width:100%;height:auto;border-radius:20px}
@media(max-width:780px){.hero,.grid3{grid-template-columns:1fr}.nav a.l{display:none}}"""
GA = """<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('consent','default',{analytics_storage:'denied',ad_storage:'denied',ad_user_data:'denied',ad_personalization:'denied'});gtag('js',new Date());gtag('config','G-XXXXXXXXXX');</script><script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>"""

def head(title, desc, path, extra=""):
    return f"""<!doctype html><html lang="en-IN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><meta name="description" content="{desc}"><link rel="canonical" href="{BASE}{path}">
<meta property="og:type" content="website"><meta property="og:title" content="{title}"><meta property="og:description" content="{desc}"><meta property="og:url" content="{BASE}{path}"><meta property="og:image" content="{BASE}/og.png">
<meta name="twitter:card" content="summary_large_image"><meta name="theme-color" content="#0F766E">{extra}{GA}<style>{CSS}</style></head><body>
<header class="nav"><a class="logo" href="/">Hisaab</a><nav aria-label="Main"><a class="l" href="/#how">How it works</a><a class="l" href="/#compare">Compare</a><a class="l" href="/blog/split-hostel-expenses.html">Guide</a><a class="btn" style="margin-left:20px;padding:10px 16px" href="/#waitlist">Join the waitlist</a></nav></header>"""

FAQ = [("Is Hisaab free?", "Yes. Adding expenses, splitting and settling are free with no daily limits. We don't charge for payments because Hisaab never handles the money; you pay through your own UPI app."),
       ("Does Hisaab hold my money or see my UPI PIN?", "No. Settling opens your UPI app with the amount filled in. The payment goes bank to bank, and your PIN is entered only in your UPI app."),
       ("Can my friends use it without installing the app?", "Yes. Share a WhatsApp link; friends can view the group, add expenses and pay from the browser."),
       ("How is it different from Google Pay's split?", "Google Pay splits one bill at a time. Hisaab keeps a running balance across every expense in a group: a whole semester of room costs or a whole trip."),
       ("Can I split unequally?", "Yes: equally, by exact amounts, by shares, or by percentage. Untick anyone who wasn't there.")]
schema_home = [{"@context": "https://schema.org", "@type": "SoftwareApplication", "name": "Hisaab", "operatingSystem": "Android, iOS, Web", "applicationCategory": "FinanceApplication",
                "offers": {"@type": "Offer", "price": "0", "priceCurrency": "INR"}, "description": "Split shared expenses with roommates and trip friends and settle in one tap with UPI."},
               {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]},
               {"@context": "https://schema.org", "@type": "Organization", "name": "Hisaab", "url": BASE, "logo": BASE + "/logo.png"}]
home = head("Hisaab: split expenses with friends and settle with UPI | Free app for India",
            "Split hostel, flat and trip expenses with friends. Hisaab keeps a running balance with everyone and settles in one tap with any UPI app. Free, no daily limits.", "/",
            f'<script type="application/ld+json">{json.dumps(schema_home)}</script>') + f"""
<main><section class="hero"><div><p style="font-weight:700;color:var(--brand);letter-spacing:.08em;text-transform:uppercase;font-size:13px;margin:0 0 10px">Free expense-splitting app for India</p>
<h1>Split expenses with friends. Settle with UPI in one tap.</h1><p style="font-size:19px">Hostel room, flat or Goa trip: add a shared expense in seconds, see one balance with every friend, and pay what you owe with any UPI app. No spreadsheets, no awkward reminders.</p>
<form class="wl" id="waitlist" aria-label="Join the waitlist"><label for="em" style="position:absolute;left:-9999px">Email</label><input id="em" type="email" required placeholder="Your email" autocomplete="email"><button class="btn" type="submit">Join the waitlist</button></form>
<p style="font-size:14px;color:var(--ink3)">Launching on Android first. We'll email you once, at launch.</p></div>
<img src="../../../ui-ux/week-4/exports/screens/05-home.png" alt="Hisaab home screen showing an overall balance of plus 854 rupees and three groups" width="390" height="844" style="max-width:340px;justify-self:center;box-shadow:0 30px 60px rgba(11,59,55,.25)"></section>
<section class="sec alt" id="how"><div class="w"><h2>How splitting expenses with Hisaab works</h2><div class="grid3">
<div class="card"><div class="num">1</div><h3>Add an expense in 10 seconds</h3><p>Type the amount, pick who paid and who was there. Split equally, by shares or exact amounts.</p></div>
<div class="card"><div class="num">2</div><h3>See one number per friend</h3><p>Hisaab keeps a running balance across every expense in the group, and simplifies who pays whom.</p></div>
<div class="card"><div class="num">3</div><h3>Settle up with UPI</h3><p>Tap Settle up: your UPI app opens with the amount filled in. Paid bank to bank, balance updated.</p></div></div></div></section>
<section class="sec" id="compare"><div class="w"><h2>Hisaab vs other ways to split bills</h2><table><thead><tr><th>Feature</th><th>Hisaab</th><th>Google Pay split</th><th>Splitwise (free)</th><th>Notes app</th></tr></thead><tbody>
<tr><td>Running balance across many expenses</td><td>✅</td><td>❌ one bill at a time</td><td>✅</td><td>Manual</td></tr><tr><td>Unequal splits</td><td>✅</td><td>Partial</td><td>✅</td><td>Manual</td></tr>
<tr><td>Settle with any UPI app inside the flow</td><td>✅</td><td>✅ creator only</td><td>❌</td><td>❌</td></tr><tr><td>Friends without the app</td><td>✅ WhatsApp link</td><td>GPay users</td><td>Invite needed</td><td>✅</td></tr>
<tr><td>Daily limit on new expenses</td><td>None</td><td>None</td><td>Reported on free plan</td><td>None</td></tr></tbody></table><p style="font-size:14px;color:var(--ink3)">Comparison based on public product information as of Nov 2026.</p></div></section>
<section class="sec alt"><div class="w"><h2>Frequently asked questions</h2>{''.join(f'<details><summary>{q}</summary><p>{a}</p></details>' for q, a in FAQ)}</div></section></main>
<footer>© 2026 Hisaab (a concept startup for a course project) · <a href="/blog/split-hostel-expenses.html">How to split hostel expenses</a> · <a href="/privacy">Privacy</a></footer>
<script>document.getElementById('waitlist').addEventListener('submit',e=>{{e.preventDefault();gtag('event','sign_up',{{method:'waitlist'}});e.target.innerHTML='<p style="font-weight:700;color:var(--owed)">You\\'re on the list! We\\'ll email you at launch.</p>';}});</script></body></html>"""
art_schema = {"@context": "https://schema.org", "@type": "Article", "headline": "How to split hostel expenses with roommates (without fights)", "datePublished": "2026-11-06",
              "author": {"@type": "Organization", "name": "Hisaab"}, "image": BASE + "/og.png", "mainEntityOfPage": BASE + "/blog/split-hostel-expenses.html"}
article = head("How to split hostel expenses with roommates (without fights) | Hisaab",
               "A practical guide to splitting rent, Wi-Fi, food and trips with hostel roommates: 5 fair methods, a simple monthly routine, and how to settle with UPI.", "/blog/split-hostel-expenses.html",
               f'<script type="application/ld+json">{json.dumps(art_schema)}</script>') + """
<main><article><p style="color:var(--ink3);font-size:14px">Guide · 6 min read · Updated 6 Nov 2026</p><h1 style="font-size:44px">How to split hostel expenses with roommates (without fights)</h1>
<p>Shared rooms run on small, frequent payments: a late-night food order, the Wi-Fi recharge, a cab to the station. Paying is easy with UPI; <strong>keeping track is what causes arguments</strong>. Here is a simple system that works for any hostel or PG room.</p>
<h2>1. Agree on what is shared</h2><p>Write down, together, which costs are split: Wi-Fi, room supplies, shared food orders, cleaning. Personal things (your own snacks, your phone recharge) stay personal. Ten minutes on day one saves a month of "but I never ate that".</p>
<h2>2. Pick the fairest split for each kind of cost</h2><table><thead><tr><th>Cost</th><th>Fair method</th></tr></thead><tbody><tr><td>Wi-Fi, room supplies</td><td>Equal split</td></tr><tr><td>Group food orders</td><td>Only people who ate; equal among them</td></tr>
<tr><td>Cab rides</td><td>Equal among riders, or by distance if drop-offs differ</td></tr><tr><td>Trips</td><td>By shares (someone skipping a day pays fewer shares)</td></tr><tr><td>Electricity with an AC user</td><td>By percentage agreed upfront</td></tr></tbody></table>
<h2>3. Record it the moment you pay</h2><p>Memory fails by the weekend. Add the expense when you pay, with a short name ("Maggi run, 11 pm") so everyone recognises it later.</p>
<h2>4. Keep one running balance, not a list of debts</h2><p>If Diya owes you ₹120 and you owe her ₹80, the only number that matters is ₹40. A running balance per person, simplified across the group, turns ten small payments into two or three.</p>
<h2>5. Settle monthly, on a fixed day</h2><p>Pick a day, say the 1st, when everyone clears their balance by UPI. A fixed day makes asking feel like routine, not nagging.</p>
<h2>Doing it with an app</h2><p>You can run this system on a shared spreadsheet. Or use an app that keeps the balances for you: <a href="/">Hisaab</a> lets you add an expense in seconds, split it any of the ways above, and settle with any UPI app.</p>
<img src="../../../../ui-ux/week-4/exports/screens/11-balances-simplify.png" alt="Hisaab balances screen showing 5 payments simplified to 3" width="390" height="844" style="max-width:300px;display:block;margin:24px auto">
<h2>Quick checklist</h2><ul><li>Agree what's shared on day one</li><li>Choose a split method per cost type</li><li>Record expenses when you pay</li><li>Track one balance per person</li><li>Settle on a fixed day each month</li></ul>
<p><a class="btn" href="/#waitlist">Join the Hisaab waitlist</a></p></article></main><footer>© 2026 Hisaab (concept startup) · <a href="/">Home</a></footer></body></html>"""
open(os.path.join(HERE, "index.html"), "w").write(home)
open(os.path.join(HERE, "blog", "split-hostel-expenses.html"), "w").write(article)
open(os.path.join(HERE, "sitemap.xml"), "w").write(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n<url><loc>{BASE}/</loc><lastmod>2026-11-06</lastmod></url>\n<url><loc>{BASE}/blog/split-hostel-expenses.html</loc><lastmod>2026-11-06</lastmod></url>\n</urlset>\n')
open(os.path.join(HERE, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n")
print("site ok")
