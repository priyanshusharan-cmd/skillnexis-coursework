"""One interface for text generation, so every script runs with whatever is available (all free options):

  1. Gemini      - GEMINI_API_KEY set (free tier at aistudio.google.com); model GEMINI_MODEL (default gemini-2.0-flash)
  2. OpenAI-compatible - OPENAI_API_KEY (+ optional OPENAI_BASE_URL, OPENAI_MODEL). Works with OpenAI, Groq's free tier,
                   or a local Ollama server (OPENAI_BASE_URL=http://localhost:11434/v1, OPENAI_API_KEY=ollama)
  3. offline     - no key: a classical NLP engine (TF-IDF + TextRank sentence ranking, keyword extraction and
                   templates). No model, no network; output is extractive, and every result is labelled with the
                   engine that produced it.

Keys are read from the environment (or a .env file that is git-ignored) and never written anywhere."""
import json, math, os, re
from collections import Counter
import requests

def _load_env():
    for p in (".env", os.path.join(os.path.dirname(__file__), "..", ".env")):
        if os.path.exists(p):
            for line in open(p):
                if "=" in line and not line.lstrip().startswith("#"):
                    k, v = line.strip().split("=", 1); os.environ.setdefault(k, v.strip().strip('"'))
_load_env()

def provider():
    if os.environ.get("GEMINI_API_KEY"): return "gemini"
    if os.environ.get("OPENAI_API_KEY"): return "openai"
    return "offline"

def chat(prompt, system="You are a helpful assistant.", temperature=0.4, max_tokens=900, json_mode=False):
    """Returns (text, engine). Raises for the offline engine, which callers handle with task-specific functions."""
    p = provider()
    if p == "gemini":
        model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
        body = {"systemInstruction": {"parts": [{"text": system}]}, "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens, **({"responseMimeType": "application/json"} if json_mode else {})}}
        r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent", params={"key": os.environ["GEMINI_API_KEY"]}, json=body, timeout=60)
        r.raise_for_status(); return r.json()["candidates"][0]["content"]["parts"][0]["text"], f"gemini:{model}"
    if p == "openai":
        base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/"); model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        body = {"model": model, "temperature": temperature, "max_tokens": max_tokens, "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}]}
        if json_mode: body["response_format"] = {"type": "json_object"}
        r = requests.post(base + "/chat/completions", headers={"Authorization": "Bearer " + os.environ["OPENAI_API_KEY"]}, json=body, timeout=120)
        r.raise_for_status(); return r.json()["choices"][0]["message"]["content"], f"openai:{model}"
    raise RuntimeError("offline")

def parse_json(text):
    m = re.search(r"\{.*\}", text, re.S); return json.loads(m.group(0) if m else text)

# ---------------- offline engine ----------------
STOP = set("""a about above after again against all am an and any are as at be because been before being below between both but by can could did do does
doing down during each few for from further had has have having he her here hers herself him himself his how i if in into is it its itself just me more most
my myself no nor not now of off on once only or other our ours ourselves out over own same she should so some such than that the their theirs them
themselves then there these they this those through to too under until up very was we were what when where which while who whom why will with would
you your yours yourself yourselves also one get got like make made many much way well even really thing things lot us let may might must shall use used
using via e g ie eg etc s t re ve ll d m don doesn didn isn aren wasn weren won""".split())
def sentences(text):
    """Sentences from prose and from list items (each line/item is its own unit; list markers stripped)."""
    out = []
    for block in re.split(r"\n\s*\n|\n(?=\s*(?:[-*•]|\d+[.)])\s)", text):
        block = re.sub(r"^\s*(?:[-*•]|\d+[.)])\s+", "", block.strip()); block = re.sub(r"\s+", " ", block)
        for s in re.split(r"(?<=[.!?])\s+(?=[A-Z\"'(\[])", block):
            s = s.strip()
            if not (40 <= len(s) <= 400) or len(s.split()) < 7: continue
            if sum(ch.isalpha() or ch == " " for ch in s) / len(s) < .85 or s.count("/") > 2: continue
            ws_ = s.split()
            if sum(w[:1].isupper() for w in ws_) / len(ws_) > .6: continue                    # a Title Case heading, not a sentence
            out.append(s if s[-1] in ".!?" else s + ".")
    return out
def words(s): return [w for w in re.findall(r"[a-z][a-z0-9'+-]{2,}", s.lower()) if w not in STOP]
def keywords(text, k=10):
    """Frequency x spread keyword score; multi-word phrases kept when they recur."""
    ws = words(text); c = Counter(ws); bigr = Counter(zip(ws, ws[1:]))
    phrases = {f"{a} {b}": n for (a, b), n in bigr.items() if n >= 4}
    scored = {w: n * (1 + math.log(len(w))) for w, n in c.items() if n >= 2}
    scored.update({p: n * 2.6 * (1 + math.log(len(p))) for p, n in phrases.items()})
    out = []
    for w, _ in sorted(scored.items(), key=lambda x: -x[1]):
        if not any(w in o or o in w for o in out): out.append(w)
        if len(out) == k: break
    return out
def textrank(text, n=5):
    """TextRank over TF-IDF cosine similarity between sentences; returns the top n in original order."""
    S = sentences(text)
    if len(S) <= n:
        textrank.best = S[0] if S else ""; return S
    from sklearn.feature_extraction.text import TfidfVectorizer
    import networkx as nx
    X = TfidfVectorizer(stop_words=list(STOP)).fit_transform(S); sim = (X @ X.T).toarray()
    for i in range(len(S)): sim[i, i] = 0
    rank = nx.pagerank(nx.from_numpy_array(sim)); score = {i: rank[i] * (1.05 if i < len(S) * .1 else 1.0) for i in range(len(S))}
    mx = max(score.values()); top = []
    while len(top) < n:                                   # MMR: central, but not a near-repeat of a sentence already picked
        top.append(max((i for i in range(len(S)) if i not in top), key=lambda i: score[i] / mx - .7 * max([sim[i, j] for j in top] or [0])))
    textrank.best = S[top[0]]
    return [S[i] for i in sorted(top)]
def shorten(s, limit):
    s = re.sub(r"\s*\([^)]{0,80}\)", "", s).strip()
    if len(s) <= limit: return s
    cut = s[:limit - 1]; cut = cut[:cut.rfind(" ")] if " " in cut else cut
    return cut.rstrip(",;:") + "…"
