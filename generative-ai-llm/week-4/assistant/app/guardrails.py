"""Guardrails on the way in and on the way out.
Input:
  * length limit (2,000 characters)
  * prompt injection / jailbreak patterns ("ignore previous instructions", "you are now", "reveal your system prompt",
    "developer mode", ...) -> blocked
  * personal data: emails, phone numbers, payment-card numbers (Luhn-checked) and API-key-looking secrets are REDACTED
    before the text is stored, logged or sent to an LLM, and the user is told
  * domain: if retrieval finds nothing relevant (best relevance below DOMAIN_MIN) the assistant declines instead of
    guessing (checked in the chat handler, since it needs the search results)
Output:
  * the same redaction, so nothing that looks like personal data or a secret leaves the service
  * the grounding check (grounding.py) adds a warning when the answer isn't supported by the sources"""
import re
MAX_CHARS, DOMAIN_MIN = 2000, .45      # DOMAIN_MIN chosen on dev questions (7 in-domain + the 16 QA questions vs 10 off-topic; eval/run_eval.py)
INJECTION = [r"ignore (?:all |any )?(?:the )?(?:previous|prior|above|earlier) (?:instructions|prompts?|rules)", r"disregard (?:the |all )?(?:previous|above|system)",
             r"(?:reveal|show|print|repeat|leak) (?:me )?(?:your |the )?(?:system|hidden|initial) (?:prompt|instructions|message)", r"\byou are now\b", r"\bact as (?:an? )?(?:unfiltered|jailbroken|dan)\b",
             r"\bdeveloper mode\b", r"\bjailbreak\b", r"\bDAN\b", r"pretend (?:you have|there are) no (?:rules|restrictions|guidelines)", r"forget (?:all )?(?:your|the) (?:rules|instructions)"]
INJ = re.compile("|".join(INJECTION), re.I)
EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"); PHONE = re.compile(r"(?<!\w)(?:\+?\d[\d\s-]{8,14}\d)(?!\w)")
CARD = re.compile(r"\b(?:\d[ -]?){13,19}\b"); SECRET = re.compile(r"\b(?:sk-[A-Za-z0-9]{16,}|AIza[0-9A-Za-z_-]{30,}|ghp_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16})\b")
def luhn(d):
    s, alt = 0, False
    for ch in reversed(d):
        n = int(ch) * (2 if alt else 1); s += n - 9 if n > 9 else n; alt = not alt
    return s % 10 == 0
def redact(text):
    found = []
    def card(m):
        d = re.sub(r"\D", "", m.group(0))
        if 13 <= len(d) <= 19 and luhn(d): found.append("payment card"); return "[REDACTED CARD]"
        return m.group(0)
    text = SECRET.sub(lambda m: found.append("secret key") or "[REDACTED KEY]", text); text = CARD.sub(card, text)
    text = EMAIL.sub(lambda m: found.append("email") or "[REDACTED EMAIL]", text)
    text = PHONE.sub(lambda m: (found.append("phone number") or "[REDACTED PHONE]") if len(re.sub(r"\D", "", m.group(0))) >= 10 else m.group(0), text)
    return text, sorted(set(found))
def check_input(text):
    """-> dict(allowed, text (redacted), reasons, redacted)"""
    if not text or not text.strip(): return dict(allowed=False, text="", reasons=["empty message"], redacted=[])
    if len(text) > MAX_CHARS: return dict(allowed=False, text="", reasons=[f"message longer than {MAX_CHARS} characters"], redacted=[])
    clean, red = redact(text)
    if INJ.search(text): return dict(allowed=False, text=clean, reasons=["prompt-injection pattern"], redacted=red)
    return dict(allowed=True, text=clean, reasons=[], redacted=red)
def check_output(text): return redact(text)
