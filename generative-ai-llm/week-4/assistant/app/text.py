"""Small text helpers shared by retrieval, grounding checks and usage accounting."""
import re
WORD = re.compile(r"[a-z0-9_]+")
STOP = set("""the a an of to in is are was were be been being and or for on with what how does do did i can could would should
by it its this that these those as from which when why who whom use used using about you your me my we our they them their
there here not no yes if then than so such into over under also any all some more most other only just very will shall may
might must has have had at""".split())
def words(t): return WORD.findall(t.lower())
def stem(w):
    """A deliberately light stemmer so 'retries'/'retry' and 'attempts'/'attempt' match."""
    for suf, rep in (("ies", "y"), ("sses", "ss"), ("ing", ""), ("ed", ""), ("es", ""), ("s", "")):
        if w.endswith(suf) and len(w) - len(suf) >= 3 and not w.endswith("ss" if suf == "s" else "\0"): return w[: len(w) - len(suf)] + rep
    return w
def content_words(t): return [stem(w) for w in words(t) if w not in STOP and len(w) > 1]
def sentences(t):
    t = re.sub(r"\s+", " ", t).strip()
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(\[])", t) if s.strip()]
def numbers(t): return set(re.findall(r"(?<![\w.])\d+(?:\.\d+)?(?![\w.])", t))
def estimate_tokens(text):
    """Offline token estimate when the provider doesn't report usage: about 0.75 words per token for English prose
    (OpenAI's rule of thumb), counting punctuation and symbols too, since code-heavy text is token-dense."""
    if not text: return 0
    w = len(re.findall(r"\w+", text)); sym = len(re.findall(r"[^\w\s]", text))
    return max(1, round(w / .75 + sym * .5))
