# Software QA Tester — Week 3: Automation & API Testing

System under test: **Demo Shop** (`demo-shop/server.js`), a small store with login, product search, cart, checkout and a REST API. It runs locally with no dependencies, so every test here can be re-run offline.

| Brief item | What was done |
| --- | --- |
| **Set up Selenium WebDriver and automate login on a demo site** | Selenium 4 with pytest (`selenium/`). Login is automated on the Demo Shop (valid, wrong password, locked user, logout). `test_saucedemo.py` automates login on the public practice site saucedemo.com. |
| **5 automated test scripts for form validations** | `selenium/test_form_validation.py`: required username, required password, all checkout fields required, invalid email (4 values), PIN code boundaries (5 and 7 digits, a letter, only spaces). |
| **Locating elements – IDs, CSS, XPath** | `selenium/pages.py` is a Page Object Model and uses all three, e.g. `By.ID("username")`, `By.CSS_SELECTOR("#login-form button[type='submit']")` and an XPath that finds the "Add to cart" button in the row whose product name matches. |
| **Test REST APIs with Postman, validate status codes and body** | `postman/demo-shop.postman_collection.json`: 15 requests across 5 API groups (login, product list/search/detail, cart add/update/delete, orders, auth). 33 assertions on status codes, JSON body, headers and response time. Covers GET, POST, PUT and DELETE. |
| **Postman collection with environment variables** | `postman/local.postman_environment.json` holds `baseUrl`, `username` and `password`. Requests chain through variables: login stores `{{token}}`, the product list stores `{{productId}}`, the order stores `{{orderId}}`. |
| **Mini project: automate 10 scenarios (login, search, add to cart, checkout) + 5 APIs, export the collection** | `selenium/test_scenarios.py`: 10 end-to-end scenarios (S01–S10). The exported collection is the JSON in `postman/` and imports directly into Postman. |

## Results

| Suite | Result | Evidence |
| --- | --- | --- |
| Selenium (headless Firefox 159, geckodriver 0.37) | **21 passed**, 2 skipped (the saucedemo.com tests need internet, see below) | `results/selenium-junit.xml` |
| Postman collection via Newman 6.2 | **15 requests, 33 of 33 assertions passed** | `results/newman.json`, `results/newman-junit.xml` |

**Do the tests actually catch bugs?** I checked by planting two defects in the shop: the PIN rule was loosened to accept 5 digits, and one price was changed. `test_v05` (PIN boundary) and `test_s07` (cart total) both failed. Then I reverted the changes. A failing test also saves a screenshot to `results/screenshots/` for the bug report.

## Run it

```sh
# Selenium (Python 3.10+)
pip install selenium pytest
cd selenium
python -m pytest -v                       # Firefox; or BROWSER=chrome python -m pytest -v
SAUCEDEMO=1 python -m pytest -v test_saucedemo.py   # public site, needs internet

# Postman / Newman
npm install
npm run shop          # terminal 1: Demo Shop on http://127.0.0.1:4300
npm run api           # terminal 2: runs the collection, writes results/
```

The Selenium suite starts its own copy of the shop on a free port, so `npm run shop` is only needed for Newman or for importing the collection into the Postman app. Selenium Manager downloads the matching browser driver automatically. Set `GECKODRIVER`/`CHROMEDRIVER` and `FIREFOX_BIN` to use specific binaries.

## Test scenarios

| ID | Scenario | Expected |
| --- | --- | --- |
| S01 | Log in as `standard_user` | Products page with 5 items |
| S02 | Wrong password | "Username and password do not match", stays on login |
| S03 | Locked user | "This user has been locked out" |
| S04 | Log out, then open `/inventory` | Back to login with "Please log in first" |
| S05 | Search "lamp" | Only "Desk Lamp", count shows 1 |
| S06 | Search "telescope" | Empty list and a no-results message |
| S07 | Add backpack + notebooks | Badge 2, cart total ₹39.49 |
| S08 | Change bottle qty to 3 | Total ₹46.50, badge 3 |
| S09 | Remove mouse | "Your cart is empty.", badge 0 |
| S10 | Checkout with valid details | "Order placed", badge back to 0 |

## Limits

- The two saucedemo.com tests were written but not run in this environment, because it has no general internet access. Run them with `SAUCEDEMO=1`.
- Only Firefox was run here. The suite also supports Chrome (`BROWSER=chrome`).
- Newman runs the same collection the Postman app would, but no Postman-app screenshots are included.
