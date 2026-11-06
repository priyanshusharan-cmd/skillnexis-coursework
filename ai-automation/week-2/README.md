# Week 2: AI APIs & web scraping

All four tasks plus the mini project are working Python tools, with tests (`pytest tests`: 6 passing). Everything is
free:
* no paid service is required;
* API keys are optional and read from the environment or a git-ignored `.env` file.

| Task | Script | Result here |
|---|---|---|
| Summarise any article URL with an AI API | [`src/summarize.py`](src/summarize.py) | [`outputs/summary-style-guide-for-python-code.md`](outputs/summary-style-guide-for-python-code.md) (PEP 8, 5,700 words), [`outputs/summary-httpx.md`](outputs/summary-httpx.md) (a live HTML page) |
| Web scraper that extracts product prices from an e-commerce site | [`src/price_scraper.py`](src/price_scraper.py) | 60 products from the books.toscrape.com sandbox shop → [`outputs/prices.csv`](outputs/prices.csv) plus a price history in `outputs/prices.sqlite`, with a watch-list alert |
| Personalised emails to a contact list from a spreadsheet | [`src/mail_merge.py`](src/mail_merge.py) + [`data/templates/progress.j2`](data/templates/progress.j2) | 4 emails rendered ([`outputs/emails/`](outputs/emails/)) and **delivered over real SMTP** to a local mail server. 3 bad rows were rejected: an invalid address, a duplicate and an unsubscribed contact |
| Data pipeline that cleans, transforms and exports CSV | [`src/pipeline.py`](src/pipeline.py) | 4,622 real order lines → 4 clean tables plus a data-quality report ([`outputs/pipeline/report.md`](outputs/pipeline/report.md)). Every reconciliation check passes |
| **Mini project:** AI content repurposer (URL → scrape → AI → X thread, LinkedIn post, Instagram caption → formatted document) | [`src/repurpose.py`](src/repurpose.py) | [`outputs/repurposed-style-guide-for-python-code.docx`](outputs/repurposed-style-guide-for-python-code.docx) (+ `.md`, `.json`), [`outputs/repurposed-httpx.docx`](outputs/repurposed-httpx.docx) |

## The AI layer (`src/llm.py`), and which engine produced these results
Every AI step goes through one function that picks the best available **free** engine:

| Priority | Engine | How to enable |
|---|---|---|
| 1 | **Google Gemini** (the brief's suggested API) | `GEMINI_API_KEY=…`, a free key from aistudio.google.com with no card needed |
| 2 | **Any OpenAI-compatible API**: OpenAI, Groq's free tier, or a **local Ollama** model | `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL` (for Ollama: `http://localhost:11434/v1`, key `ollama`) |
| 3 | **Offline engine**, no key and no network: TF-IDF + TextRank sentence ranking with MMR for variety, keyword extraction, and post templates | default |

> **Honest note: the committed outputs were made by the offline engine.** This workspace can't reach Google's or
> OpenAI's APIs, and no key was available. The offline engine is *extractive*: its "summary" and posts are built from
> the article's own most central sentences, so the wording is less natural than an LLM's. Every output is labelled
> with its engine. To get LLM-written versions, add a free Gemini key to `.env` and rerun the same commands; the
> prompts (JSON output, faithfulness rules, platform formats) are already in the scripts.

## Task notes
**1 · Summariser.** It extracts the main content first:
* **HTML:** trafilatura removes the navigation, sidebars and footers.
* **Markdown:** front matter, code fences and link syntax are stripped.
* **reStructuredText:** Python PEPs, including directives and roles.

It then asks the AI for JSON with a TL;DR, key points and who should read it, and writes Markdown. Tested on PEP 8
(public domain) and the live PyPI page of `httpx`.

**2 · Price scraper.** It runs against books.toscrape.com, a sandbox shop built for scraping practice.
* **Polite:** it checks robots.txt, sends an identifying User-Agent, waits 1 s between pages, and retries with
  back-off.
* **Prices:** normalised from strings like `£1,051.77`, `$ 2,499.00` or `₹999`.
* **Pagination:** follows the "next" link.
* **History:** every run is stored in SQLite, and the script flags **price drops** against the previous run and
  **watch-list targets** (`data/watchlist.csv`).
* **Other shops:** the selectors live in one `SITE` dict, so another shop needs only new selectors (check its terms
  first).

*Limitation:* this workspace can't reach the live site, so the results come from a 3-page snapshot of it
(`data/books_snapshot/`, 60 products). The same command with the live URL crawls all 50 pages. The unit test covers
the full live markup: star rating, the next link and absolute URLs.

**3 · Mail merge.**
* **Template:** one Jinja2 template whose subject and body change with each person's progress (finished / past
  halfway / just started), plus an optional P.S. for people with a company.
* **Hygiene first:** emails are trimmed and lower-cased, validated, de-duplicated, and unsubscribed contacts are
  removed.
* **Dry run by default:** writes `.eml` files to review first. `--send` delivers over SMTP with a pause between
  messages and a `List-Unsubscribe` header, and logs each result to `outputs/mail_log.csv`.
* **Tested for real:** sent to a local `aiosmtpd` server, which received all 4 messages.
* **Your own email:** a free Gmail App Password works (`SMTP_HOST=smtp.gmail.com`, port 587).
* The contacts in `data/contacts.xlsx` are fictitious, at example.com addresses.

**4 · CSV pipeline.** Extract → validate schema → clean → transform → validate output → export.
* **The data:** the real Chipotle orders file from the public DAT8 course (`data/raw/chipotle.tsv`).
* **Messy cases fixed:**
  * prices stored as text (`"$2.39 "`);
  * bracketed, nested option lists;
  * 60 repeated lines, merged so that **no revenue is lost**;
  * item-name variants.
* **Unsafe guesses avoided:** bare names like "Burrito" are labelled *protein not recorded* rather than guessed.
* **Outputs:** clean lines, orders, items and options tables.
* **Asserted checks:** order totals = line totals = the raw file's total ($34,500.16); all unit prices positive.

**Mini project · Repurposer.** One command turns a URL into:
* a summary;
* a **6-post X thread**;
* a **LinkedIn post**: hook first, ✅ takeaways, a closing question, 3 hashtags;
* an **Instagram caption**: emoji takeaways, a save-this call to action, up to 30 hashtags.

The result is saved as a formatted **Word document** (tables, headings, a checks section) plus Markdown and JSON.
**Platform limits are enforced after generation, whatever engine wrote the text:**
* 280 characters per post, counting links as 23 like X does;
* LinkedIn under 3,000 characters, with the hook measured against the ~210 characters shown before "see more";
* Instagram under 2,200 characters and 30 hashtags.

## Run it
```bash
pip install requests beautifulsoup4 lxml trafilatura pandas openpyxl jinja2 python-docx scikit-learn networkx tabulate aiosmtpd pytest
cd ai-automation/week-2
# optional: echo "GEMINI_API_KEY=your-free-key" > .env
python src/summarize.py https://pypi.org/project/httpx/
python src/repurpose.py https://raw.githubusercontent.com/python/peps/main/peps/pep-0008.rst
python src/price_scraper.py https://books.toscrape.com/catalogue/page-1.html --max-pages 50
python src/mail_merge.py data/contacts.xlsx data/templates/progress.j2            # add --send with SMTP_* set
python src/pipeline.py
pytest tests
```
