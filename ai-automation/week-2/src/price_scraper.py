"""Task 2: e-commerce price scraper. Built for books.toscrape.com, a sandbox shop made for scraping practice, but the
CSS selectors are a config dict so another shop needs only new selectors (check its robots.txt and terms first).
* polite: honours robots.txt, identifies itself, waits between requests, retries with back-off
* follows pagination ("next" link) up to --max-pages
* normalises prices (currency symbol, thousands separators) and availability
* keeps a price history in SQLite and flags price drops and watch-list targets on every run
    python src/price_scraper.py https://books.toscrape.com/catalogue/page-1.html --max-pages 50
    python src/price_scraper.py data/books_snapshot/page-1.html          # offline snapshot (used for the results here)"""
import argparse, csv, datetime, os, re, sqlite3, sys, time, urllib.robotparser
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
UA = "skillnexis-coursework-bot/1.0 (+https://github.com/priyanshusharan-cmd/skillnexis-coursework)"
SITE = dict(item="article.product_pod", title="h3 a", title_attr="title", link="h3 a", price=".price_color", stock=".availability", rating="p.star-rating", next="li.next a")
RATING = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
def get(url, delay):
    if not url.startswith("http"): return open(url, encoding="utf-8").read()
    for k in range(3):
        try:
            time.sleep(delay); r = requests.get(url, headers={"User-Agent": UA}, timeout=20); r.raise_for_status(); r.encoding = r.apparent_encoding; return r.text
        except requests.RequestException as e:
            if k == 2: raise
            time.sleep(2 ** (k + 1))
def allowed(url):
    if not url.startswith("http"): return True
    rp = urllib.robotparser.RobotFileParser(); rp.set_url(f"{urlparse(url).scheme}://{urlparse(url).netloc}/robots.txt")
    try: rp.read()
    except Exception: return True                    # no robots.txt reachable: treat as allowed, but stay polite
    return rp.can_fetch(UA, url)
def price(text):
    m = re.search(r"([£$€₹])?\s*([\d.,]+)", text.replace("\xa0", " "))
    num = m.group(2).replace(",", "") if m else ""
    return (m.group(1) or "", float(num)) if num else ("", None)
def parse(html, base):
    soup = BeautifulSoup(html, "lxml"); rows = []
    for it in soup.select(SITE["item"]):
        a = it.select_one(SITE["title"]); cur, p = price(it.select_one(SITE["price"]).get_text())
        st = it.select_one(SITE["stock"]); rt = it.select_one(SITE["rating"])
        rows.append(dict(title=a.get(SITE["title_attr"]) or a.get_text(strip=True), price=p, currency=cur, in_stock="in stock" in (st.get_text(" ", strip=True).lower() if st else ""),
                         rating=next((RATING[c] for c in (rt.get("class") if rt else []) if c in RATING), None), url=urljoin(base, it.select_one(SITE["link"])["href"])))
    nx = soup.select_one(SITE["next"]); return rows, (urljoin(base, nx["href"]) if nx else None)
def crawl(start, max_pages, delay):
    url, out, pages = start, [], 0
    if not allowed(start): sys.exit(f"robots.txt disallows {start}")
    while url and pages < max_pages:
        rows, nxt = parse(get(url, delay if pages else 0), url); out += rows; pages += 1; print(f"page {pages}: {len(rows)} items  {url}", flush=True)
        if not nxt and not url.startswith("http"):                                  # snapshot folder: walk page-N.html files
            cand = re.sub(r"page-(\d+)", lambda m: f"page-{int(m.group(1)) + 1}", url); nxt = cand if cand != url and os.path.exists(cand) else None
        url = nxt
    return out
def history(rows, db="outputs/prices.sqlite", watch=None):
    con = sqlite3.connect(db); con.execute("create table if not exists price(url text, title text, price real, currency text, in_stock int, seen text)")
    now = datetime.datetime.now().isoformat(timespec="seconds"); alerts = []
    for r in rows:
        prev = con.execute("select price from price where url=? order by seen desc limit 1", (r["url"],)).fetchone()
        if prev and r["price"] is not None and r["price"] < prev[0]: alerts.append(f"PRICE DROP {r['title']}: {r['currency']}{prev[0]:.2f} -> {r['currency']}{r['price']:.2f}")
        if watch and r["title"] in watch and r["price"] is not None and r["price"] <= watch[r["title"]]: alerts.append(f"TARGET HIT {r['title']}: {r['currency']}{r['price']:.2f} <= {watch[r['title']]:.2f}")
        con.execute("insert into price values (?,?,?,?,?,?)", (r["url"], r["title"], r["price"], r["currency"], int(r["in_stock"]), now))
    con.commit(); n = con.execute("select count(distinct seen) from price").fetchone()[0]; con.close(); return alerts, n
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("start"); ap.add_argument("--max-pages", type=int, default=50); ap.add_argument("--delay", type=float, default=1.0)
    ap.add_argument("--watch", default="data/watchlist.csv"); o = ap.parse_args(); os.makedirs("outputs", exist_ok=True)
    rows = crawl(o.start, o.max_pages, o.delay)
    with open("outputs/prices.csv", "w", newline="") as f: w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    watch = {r["title"]: float(r["target_price"]) for r in csv.DictReader(open(o.watch))} if os.path.exists(o.watch) else {}
    alerts, runs = history(rows, watch=watch)
    ps = sorted(r["price"] for r in rows if r["price"] is not None); cur = rows[0]["currency"]
    print(f"\n{len(rows)} products · min {cur}{ps[0]:.2f} · median {cur}{ps[len(ps) // 2]:.2f} · max {cur}{ps[-1]:.2f} · in stock {sum(r['in_stock'] for r in rows)}/{len(rows)} · runs in history: {runs}")
    for a in alerts: print(a)
    print("saved outputs/prices.csv and outputs/prices.sqlite")
