"""Scripted execution of the test cases marked "manual" in test-cases.csv
(TC-008 to TC-010, TC-014 to TC-016, TC-023 to TC-025, TC-038, TC-054, TC-058).
TC-057 (mobile layout) is covered by selenium/test_regression_def1.py.

usage: python scripted-checks.py http://127.0.0.1:4300   (shop must be running)
"""
import json
import re
import sys
import urllib.error
import urllib.parse as up
import urllib.request as ur

B = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://127.0.0.1:4300"
LOGIN = {"username": "standard_user", "password": "demo-pass-123"}


class NoRedirect(ur.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def call(path, data=None, cookie=None, headers=None):
    h = dict(headers or {})
    if cookie:
        h["Cookie"] = cookie
    try:
        r = ur.build_opener(NoRedirect).open(ur.Request(B + path, data=data, headers=h))
    except urllib.error.HTTPError as e:
        r = e
    return r.status, dict(r.headers), r.read().decode()


def form(d):
    return up.urlencode(d).encode()


results = {}
_, h, _ = call("/login", form(LOGIN))
cookie_hdr = h.get("Set-Cookie", "")
ck = cookie_hdr.split(";")[0]
results["TC-008 cookie HttpOnly + SameSite"] = "HttpOnly" in cookie_hdr and "SameSite=Lax" in cookie_hdr
results["TC-009 password masked"] = 'name="password" type="password"' in call("/")[2]
_, h, _ = call("/login", form({**LOGIN, "username": "STANDARD_USER"}))
results["TC-010 username case-sensitive"] = "do%20not%20match" in h.get("Location", "")
results["TC-014 search case-insensitive"] = "Desk Lamp" in call("/inventory?q=LAMP", cookie=ck)[2]
results["TC-015 empty search lists all"] = call("/inventory?q=", cookie=ck)[2].count('class="item-name"') == 5
results["TC-016 partial match"] = "Notebook Set" in call("/inventory?q=note", cookie=ck)[2]
call("/cart/add", form({"productId": 5}), cookie=ck)
for tc, qty in [("TC-023 qty 0 rejected", "0"), ("TC-025 qty 2.5 rejected", "2.5")]:
    _, h, _ = call("/cart/update", form({"productId": 5, "qty": qty}), cookie=ck)
    results[tc] = "1%20to%2010" in h.get("Location", "")
call("/cart/update", form({"productId": 5, "qty": 10}), cookie=ck)
results["TC-024 qty 10 accepted, total 95.00"] = "₹95.00" in call("/cart", cookie=ck)[2]
J = {"Content-Type": "application/json"}
tok = json.loads(call("/api/login", json.dumps(LOGIN).encode(), headers=J)[2])["token"]
A = {**J, "Authorization": "Bearer " + tok}
before = json.loads(call("/api/products/4")[2])["stock"]
call("/api/cart", json.dumps({"productId": 4, "qty": 2}).encode(), headers=A)
call("/api/orders", json.dumps({"firstName": "P", "lastName": "R", "email": "p@e.co", "postalCode": "560019"}).encode(), headers=A)
results["TC-038 stock drops by ordered qty"] = before - json.loads(call("/api/products/4")[2])["stock"] == 2
st, _, body = call("/api/login", b"not json", headers=J)
results["TC-054 malformed JSON is 400"] = st == 400 and "Body must be JSON" in body
page = call("/checkout", cookie=ck)[2]
ids = re.findall(r'<input id="([^"]+)"', page)
results["TC-058 every input labelled"] = bool(ids) and all(re.search(r"<label>[^<]+<input id=\"" + i, page) for i in ids)

for name, ok in results.items():
    print(("PASS " if ok else "FAIL ") + name)
sys.exit(0 if all(results.values()) else 1)
