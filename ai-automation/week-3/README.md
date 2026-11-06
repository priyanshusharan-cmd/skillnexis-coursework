# Week 3: Workflow automation & chatbots

Everything here is built on one running example, the learner support for "Code in Small Steps" (the free Python
course from the content-creator track). The four tasks and the mini project fit together:
* the sign-up workflow welcomes new learners;
* the FAQ bot and the knowledge base answer them;
* the support system escalates what the bot can't handle and reports daily.

| Task | Folder | Result |
|---|---|---|
| 5-step automation connecting 3 apps (Zapier/Make) | [`workflow/`](workflow/) | An importable **n8n** workflow: Google Sheets → validate → branch → Gmail → Slack, plus a status write-back. A local run proves the logic with real SMTP and webhook calls |
| FAQ chatbot with 10+ intents (Dialogflow/Botpress) | [`faq-bot/`](faq-bot/) | 12 intents and 144 training phrases. **85 % accuracy on 48 held-out messages.** Exports a **Dialogflow ES agent ZIP** (import and restore) and Botpress intents |
| Google Sheets workflow that processes form submissions | [`sheets/`](sheets/) | `Code.gs` Apps Script with an installable onFormSubmit trigger. It validates, de-duplicates, enriches, emails and logs. Tested in Node against mocks of the Apps Script services, replaying 8 submissions; all checks pass |
| AI document classifier for uploaded PDFs | [`pdf-classifier/`](pdf-classifier/) | **92.2 % accuracy** on the 7,600-article AG News test set. A FastAPI upload service plus a folder sorter; mixed-topic and image-only PDFs go to review or rejection |
| **Mini project:** support system: chatbot + knowledge base + email escalation + Sheets log + daily summary | [`support-system/`](support-system/) | A FastAPI chat service with a 10-article KB, 4 escalation rules, logging to Google Sheets (or SQLite), and a daily HTML summary report (cron or the GitHub Actions workflow included) |

## 1 · The 5-step, 3-app workflow (`workflow/`)
Free tools: Zapier's free plan only allows 2-step Zaps, so this uses **n8n**, which is free and open source
(self-host with `npx n8n` or `docker run n8nio/n8n`). The same design also fits **Make**'s free plan.

[`n8n-course-signup.json`](workflow/n8n-course-signup.json) has 5 steps:
1. **Google Sheets trigger:** a new form response row.
2. **Code:** validate and normalise (email format, name casing, choose a track).
3. **IF:** is it valid?
4. **Gmail:** send a personalised welcome email.
5. **Slack:** post to #signups. Invalid rows go instead to **5b**, which writes `INVALID: reason` back to the Sheet.

**To use it:** in n8n, go to Workflows → Import from file, connect your Google, Gmail and Slack credentials (all free),
and paste your Sheet URL.

**Local proof** ([`run_local.py`](workflow/run_local.py)) runs the identical logic with stand-ins:
* a CSV file for the Sheet;
* a **real SMTP send** to a local mail server for Gmail;
* a **real HTTP POST** of Slack's incoming-webhook JSON to a local receiver for Slack.

Result ([`run-log.json`](workflow/run-log.json)): 4 rows processed, 2 emails received, 2 Slack messages, 2 rows marked
invalid ("invalid email", "name missing"). Set `SMTP_*` and `SLACK_WEBHOOK_URL` to hit the real services.

## 2 · FAQ chatbot (`faq-bot/`)
* **Intents:** [`intents.yaml`](faq-bot/intents.yaml) has 12, including greeting, price, certificate, installing
  Python, schedule, course length, prerequisites, error help, human agent and account issues.
* **Model:** word plus character n-gram TF-IDF into logistic regression. The character n-grams cope with typos like
  "certifcate".
* **Fallback:** a confidence threshold, tuned on held-out data, sends unclear messages to a fallback instead of
  guessing.

**Honest evaluation** ([`results.json`](faq-bot/results.json)) uses 48 messages written separately in different
wording ([`tests.yaml`](faq-bot/tests.yaml)) that the model never saw:

| Metric | Value |
|---|---|
| Held-out accuracy | **85.4 %** |
| Answered correctly (above threshold) | 83.3 % |
| Sent to fallback | 8.3 % |
| Out-of-scope messages caught | 4 of 6 |
| 5-fold CV on the training phrases | 69 % ± 4 % (pessimistic: only 9–10 phrases per intent remain in each training fold) |

**Known weaknesses:**
* "what's the stock price of tesla" matches *course_price* on the word "price";
* "how many videos per week" confuses *schedule* with *course length*.

In the mini project, the knowledge base and the escalation rules catch these.

**Platforms:** [`export_dialogflow.py`](faq-bot/export_dialogflow.py) writes `dialogflow-agent.zip`: 12 intents, a
fallback intent and the welcome event. Import it in the Dialogflow ES console (free edition) under ⚙ → Export and
Import → Restore from ZIP. The script also writes `botpress-intents.json`. `python bot.py` chats in the terminal.

## 3 · Google Sheets form workflow (`sheets/`)
[`Code.gs`](sheets/Code.gs): paste it into Extensions → Apps Script and run `setup()` once. On every form
submission, under a script lock so simultaneous submissions don't race, it:
1. validates the row (required name, email format) and normalises it (trims and lower-cases the email, title-cases
   the name);
2. **de-duplicates:** a repeat email updates the existing student and counts the submissions;
3. **enriches** the row with a cohort (the Monday of the sign-up week) and a track (from the experience answer);
4. writes to `Students` and stamps `Status` on the response row;
5. emails a welcome to new students only, and logs everything to `Log`.

`processPending()` back-fills old rows.

**Tested without a Google account:** [`test_harness.js`](sheets/test_harness.js) runs `Code.gs` **unchanged** in Node,
with in-memory mocks of SpreadsheetApp, MailApp, LockService, Utilities and ScriptApp, replaying 8 tricky submissions:
* messy casing;
* a duplicate with different casing;
* an invalid email;
* a missing name;
* two submissions at the same moment.

Result ([`results/sheets-after.md`](sheets/results/sheets-after.md)): 4 unique students, 2 duplicates updated, 2
rejected with reasons, 4 welcome emails, and every row stamped.

## 4 · PDF topic classifier (`pdf-classifier/`)
* **Data:** AG News (Zhang, Zhao & LeCun, 2015), with 120 k training articles in 4 topics. Fetch it with
  `./get_data.sh`; it isn't committed because it's 31 MB.
* **Model:** TF-IDF into a calibrated linear SVM. It trains in 18 s on a laptop.

| | |
|---|---|
| Test accuracy (7,600 articles) | **92.16 %**, macro F1 0.921 ([confusion matrix](pdf-classifier/results/confusion.png)) |
| Above the 0.6 confidence threshold | 94.4 % of articles are filed automatically, at **94.7 %** accuracy; the rest go to review |
| Sample PDFs (`make_samples.py`) | **12/12** digest PDFs filed correctly. The mixed-topic PDF → `needs-review` (its chunks disagree: Sports 40 %, the other topics 20 % each). The image-only PDF → `rejected: no text layer, run OCR` |

**Mixed documents:** long text makes whole-document probabilities overconfident. The mixed PDF scored 0.70 overall,
which would have passed the threshold, so the classifier also **votes over 60-word chunks** and sends documents whose
chunks disagree to review.

**Use:**
* `python classify.py <folder>` copies the files into `sorted/<topic>/` and writes
  [`results/classified.csv`](pdf-classifier/results/classified.csv);
* `uvicorn app:app` serves an upload page and a `POST /classify` API with size, type and unreadable-PDF checks.

## 5 · Mini project: automated customer support (`support-system/`)
```
user ─► /chat ─► intent (faq-bot model) + knowledge-base search ─► answer with cited article / FAQ answer / small talk
                                   │                                   │
                                   └─► escalation rules ─► ticket + email to support (full transcript)
every turn ─► log (Google Sheets via gspread, or SQLite)  ─►  daily_report.py ─► HTML email + Markdown report
```
**Knowledge base:** 10 articles in [`kb/`](support-system/kb/). Retrieval works in two stages:
1. pick the **article** (word and character TF-IDF, plus a small synonym map such as macbook → macOS);
2. pick the best **paragraph** inside it (BM25-style term overlap).

Answers cite their source article.

**Escalation rules, checked in this order:**
1. a frustrated user ("useless", "still doesn't help"…);
2. an explicit request for a human;
3. account or data requests (delete data, change email, refund, locked);
4. two unanswered messages in a row.

An escalation creates a ticket, emails support with the full transcript (over SMTP, or into `outbox/` when no SMTP
is set), and tells the user what happens next. Self-service account questions such as "how do I stop the emails" are
answered from the KB instead of escalated.

**Logging:** every turn is logged with 12 columns. Google Sheets is used when `GOOGLE_SERVICE_ACCOUNT_JSON` and
`SHEET_ID` are set (a free service account, with the sheet shared to it); otherwise the log goes to SQLite.

**Daily summary** (`daily_report.py`):
* conversations, messages, automatic-answer rate, and conversations resolved without a human;
* escalations with reasons, top intents and KB articles used;
* the questions it couldn't answer, as a to-do list for new KB articles.

It's sent as an HTML email. Schedule it with cron or [`.github-example/daily-report.yml`](support-system/.github-example/daily-report.yml)
on GitHub Actions (free).

**Demo run** ([`simulate.py`](support-system/simulate.py); full transcript in
[`results-simulation.txt`](support-system/results-simulation.txt), report in
[`reports/`](support-system/reports/)). It ran **12 scripted conversations** through the real API, and those
conversations are simulated, not real users:

| Metric | Value |
|---|---|
| Messages | 21 (18 questions) |
| Answered automatically | 13 (**72 %**) |
| Conversations resolved without a human | 8 of 12 |
| Escalations | 4: account deletion, repeated out-of-scope, frustrated user, human request |

## Honest notes
* **Accounts:** Zapier, Make, Dialogflow, Google Sheets, Gmail and Slack all need your accounts, and I don't sign in
  for you. Everything is delivered importable (n8n JSON, Dialogflow ZIP, Apps Script), and the logic is proven
  locally with stand-ins: a real SMTP server, a real HTTP webhook receiver, and mocks of the Apps Script APIs.
* **No LLM:** the chatbot uses a small trained classifier plus retrieval rather than an LLM, so it's free, fast and
  predictable. Its limits are measured above.

## Run
```bash
pip install scikit-learn pyyaml joblib fastapi uvicorn pypdf reportlab aiosmtpd requests gspread
cd ai-automation/week-3
(cd workflow && python run_local.py)
(cd faq-bot && python train.py && python export_dialogflow.py && python bot.py "is it free?")
(cd sheets && node test_harness.js)
(cd pdf-classifier && ./get_data.sh && python train.py && python make_samples.py && python classify.py samples/)
(cd support-system && python simulate.py && uvicorn app:app)      # chat at http://localhost:8000
```
